"""Non-modal acquisition dialog: all network and process work stays off the UI thread."""
import json
import threading
from pathlib import Path

from PySide6.QtCore import QThread, QStandardPaths, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel,
                              QLineEdit, QMessageBox, QProgressBar, QPushButton,
                              QPlainTextEdit, QVBoxLayout)

from acquisition import AcquisitionCancelled, acquire, find_tools, youtube_url
from localization import RESOURCES


class DownloadWorker(QThread):
    progress = Signal(float)
    message = Signal(str)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, url, folder, tools, parent=None):
        super().__init__(parent)
        self.url, self.folder, self.tools = url, folder, tools
        self.stop_requested = threading.Event()

    def run(self):
        try:
            path = acquire(self.url, self.folder, self.tools, self.stop_requested,
                           self.progress.emit, self.message.emit)
            self.succeeded.emit(str(path))
        except AcquisitionCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class AcquisitionDialog(QDialog):
    videoReady = Signal(str)

    def __init__(self, translator, preferences, parent=None):
        super().__init__(parent)
        self.t = translator.text
        self.preferences = Path(preferences)
        self.worker = None
        self.close_after_cancel = False
        self.result_path = None
        self.setWindowTitle(self.t('Scarica da YouTube'))
        self.resize(680, 580)
        layout = QVBoxLayout(self)
        notice = QLabel(self.t('youtube_notice'))
        notice.setWordWrap(True)
        layout.addWidget(notice)
        terms = QPushButton(self.t('youtube_terms'))
        terms.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl('https://www.youtube.com/static?template=terms')))
        layout.addWidget(terms)
        self.url = QLineEdit()
        self.url.setPlaceholderText('https://www.youtube.com/watch?v=...')
        layout.addWidget(QLabel(self.t('Link del video')))
        layout.addWidget(self.url)
        default = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MoviesLocation)) / 'TommeView' / 'Acquisizioni'
        try:
            saved = json.loads(self.preferences.read_text(encoding='utf-8'))
            folder = saved.get('folder', str(default))
            if not isinstance(folder, str):
                folder = str(default)
        except (OSError, ValueError, AttributeError):
            folder = str(default)
        self.folder = QLineEdit(folder)
        self.browse = QPushButton(self.t('Scegli cartella'))
        self.browse.clicked.connect(self.choose_folder)
        row = QHBoxLayout()
        row.addWidget(self.folder, 1)
        row.addWidget(self.browse)
        layout.addWidget(QLabel(self.t('Cartella acquisizioni')))
        layout.addLayout(row)
        self.auto_open = QCheckBox(self.t('Apri il video al termine'))
        self.auto_open.setChecked(True)
        layout.addWidget(self.auto_open)
        self.acknowledgement = QCheckBox(self.t('youtube_acknowledgement'))
        layout.addWidget(self.acknowledgement)
        self.status = QLabel(self.t('youtube_quality'))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(200)
        layout.addWidget(self.log, 1)
        row = QHBoxLayout()
        self.start_button = QPushButton(self.t('Scarica'))
        self.start_button.clicked.connect(self.start_download)
        self.start_button.setEnabled(False)
        self.acknowledgement.toggled.connect(self.update_start_button)
        self.url.textChanged.connect(lambda: self.acknowledgement.setChecked(False))
        self.cancel_button = QPushButton(self.t('Annulla download'))
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        self.open_button = QPushButton(self.t('Apri video'))
        self.open_button.clicked.connect(lambda: self.videoReady.emit(str(self.result_path)))
        self.open_button.setEnabled(False)
        self.folder_button = QPushButton(self.t('Apri cartella'))
        self.folder_button.clicked.connect(self.open_folder)
        for button in (self.start_button, self.cancel_button, self.open_button, self.folder_button):
            row.addWidget(button)
        layout.addLayout(row)

    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def update_start_button(self):
        self.start_button.setEnabled(self.acknowledgement.isChecked() and not self.busy())

    def choose_folder(self):
        path = QFileDialog.getExistingDirectory(self, self.t('Cartella acquisizioni'), self.folder.text())
        if path:
            self.folder.setText(path)

    def open_folder(self):
        folder = self.result_path.parent if self.result_path else Path(self.folder.text())
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def start_download(self):
        if self.busy() or not self.acknowledgement.isChecked():
            return
        try:
            url = youtube_url(self.url.text())
            if not self.folder.text().strip():
                raise ValueError('Cartella acquisizioni')
            folder = Path(self.folder.text()).expanduser().resolve()
            tools = find_tools(RESOURCES / 'tools/download')
            folder.mkdir(parents=True, exist_ok=True)
            self.preferences.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.preferences.with_suffix('.tmp')
            temporary.write_text(json.dumps({'folder': str(folder)}), encoding='utf-8')
            temporary.replace(self.preferences)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, self.t('Scarica da YouTube'), self.t(str(exc)))
            return
        self.result_path = None
        self.open_button.setEnabled(False)
        self.log.clear()
        self.status.setText(self.t('youtube_downloading'))
        self.progress_bar.setRange(0, 0)
        for widget in (self.start_button, self.url, self.folder, self.browse, self.acknowledgement):
            widget.setEnabled(False)
        self.cancel_button.setEnabled(True)
        if self.worker:
            self.worker.deleteLater()
        self.worker = DownloadWorker(url, folder, tools, self)
        self.worker.progress.connect(self.show_progress)
        self.worker.message.connect(self.log.appendPlainText)
        self.worker.succeeded.connect(self.download_succeeded)
        self.worker.failed.connect(self.download_failed)
        self.worker.cancelled.connect(lambda: self.status.setText(self.t('Download annullato')))
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def show_progress(self, value):
        self.progress_bar.setRange(0, 100 if value >= 0 else 0)
        if value >= 0:
            self.progress_bar.setValue(min(100, max(0, int(value))))

    def cancel_download(self):
        if self.busy():
            self.worker.stop_requested.set()
            self.cancel_button.setEnabled(False)
            self.status.setText(self.t('Annullamento in corso'))

    def download_succeeded(self, value):
        self.result_path = Path(value)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status.setText(self.t('Download completato') + '\n' + value)
        self.open_button.setEnabled(True)
        if self.auto_open.isChecked() and not self.close_after_cancel:
            self.videoReady.emit(value)

    def download_failed(self, message):
        self.status.setText(self.t('youtube_failed'))
        self.log.appendPlainText(self.t(message))

    def download_finished(self):
        for widget in (self.url, self.folder, self.browse, self.acknowledgement):
            widget.setEnabled(True)
        self.acknowledgement.setChecked(False)
        self.update_start_button()
        self.cancel_button.setEnabled(False)
        if not self.result_path:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        if self.close_after_cancel:
            self.close_after_cancel = False
            self.close()

    def reject(self):
        self.close()

    def closeEvent(self, event):
        if self.busy():
            self.close_after_cancel = True
            self.cancel_download()
            event.ignore()
        else:
            self.acknowledgement.setChecked(False)
            event.accept()
