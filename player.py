import argparse
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('QT_MEDIA_BACKEND', 'ffmpeg')

from PySide6.QtCore import QEvent, QRect, QSize, QStandardPaths, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QImage, QPainter, QPen, QTransform
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QMainWindow, QMenu, QMessageBox,
    QPushButton, QSizePolicy, QSlider, QSplitter, QStyle, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget, QInputDialog)

from model import COLORS, RATES, Markers, SessionStore, export_csv, seconds
from app_info import APP_NAME, APP_VERSION, APP_AUTHOR
from localization import RESOURCES, Translator
from acquisition_ui import AcquisitionDialog

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent


def default_session_dir():
    return Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)) / APP_NAME / 'sessions'

STYLE = '''
QWidget { background: #171a1e; color: #e8edf1; font-family: "Segoe UI"; font-size: 13px; }
QMainWindow { background: #111316; }
QToolButton, QPushButton, QComboBox { background: #282d33; border: 1px solid #3b424a; border-radius: 4px; padding: 6px; }
QToolButton:hover, QPushButton:hover { background: #39434a; border-color: #53cfb6; }
QToolButton:disabled, QPushButton:disabled { color: #626a71; }
QToolButton:checked { background: #28594f; }
QToolTip { color: #fff; background: #30383f; border: 1px solid #65717b; padding: 5px; }
QTableWidget { background: #1b1f24; alternate-background-color: #20252b; border: 0; gridline-color: #323940; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: #30534e; color: white; }
QHeaderView::section { background: #272d33; color: #aebbc5; border: 0; padding: 8px 5px; }
QComboBox QAbstractItemView { background: #282d33; selection-background-color: #30534e; }
QSlider::groove:horizontal { height: 5px; background: #414b54; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #4bd6bd; }
QSlider::handle:horizontal { background: #f1f6f8; width: 13px; margin: -5px 0; border-radius: 6px; }
QSplitter::handle { background: #383f46; width: 1px; }
QMenu { background: #282d33; border: 1px solid #59636c; padding: 4px; }
QMenu::item { padding: 8px 24px; }
QMenu::item:selected { background: #30534e; }
QStatusBar { color: #a5b1ba; background: #20252a; }
'''


class VideoSurface(QWidget):
    clicked = Signal()
    doubleClicked = Signal()

    def __init__(self):
        super().__init__()
        self.image = QImage()
        self.rotation = 0
        self.native_rotation = 0
        self.native_mirrored = False
        self.empty_text = 'Nessun video aperto'
        self.ms = 0
        self.rate = 100
        self.flash_flags = []
        self.video_only = False
        self.setMinimumSize(320, 180)
        self.flash_timer = QTimer(self)
        self.flash_timer.setSingleShot(True)
        self.flash_timer.timeout.connect(self.clear_flash)

    def flash(self, flags):
        self.flash_flags = list(dict.fromkeys(flags))
        self.flash_timer.start(500)
        self.update()

    def clear_flash(self):
        self.flash_flags = []
        self.flash_timer.stop()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#080a0c'))
        if not self.image.isNull():
            p.save()
            angle = (self.rotation + self.native_rotation) % 360
            available = self.size().transposed() if angle in (90, 270) else self.size()
            size = self.image.size().scaled(available, Qt.AspectRatioMode.KeepAspectRatio)
            p.translate(self.width() / 2, self.height() / 2)
            p.rotate(angle)
            if self.native_mirrored:
                p.scale(-1, 1)
            dest = QRect(-size.width() // 2, -size.height() // 2, size.width(), size.height())
            p.drawImage(dest, self.image)
            p.restore()
        else:
            p.setPen(QColor('#84929d'))
            p.setFont(QFont('Segoe UI', 20))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.empty_text)
        if not self.video_only:
            p.setFont(QFont('Consolas', 23, QFont.Weight.Bold))
            time_text = seconds(self.ms) + ' s'
            width = p.fontMetrics().horizontalAdvance(time_text) + 24
            box = QRect(16, self.height() - 58, width, 42)
            p.fillRect(box, QColor(0, 0, 0, 195))
            p.setPen(QColor('#ffffff'))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, time_text)
            p.setFont(QFont('Segoe UI', 12, QFont.Weight.Bold))
            rate_box = QRect(self.width() - 105, self.height() - 52, 89, 32)
            p.fillRect(rate_box, QColor(0, 0, 0, 195))
            p.setPen(QColor('#4bd6bd'))
            p.drawText(rate_box, Qt.AlignmentFlag.AlignCenter, f'{self.rate}%')
        if self.flash_flags:
            # Multiple markers crossed in one decoded frame remain visible together.
            for index, flag in enumerate(self.flash_flags):
                col, row = index % 5, index // 5
                rect = QRect(16 + col * 64, 16 + row * 78, 60, 72)
                p.fillRect(rect, QColor(0, 0, 0, 195))
                p.setPen(QColor(COLORS[flag]))
                p.setFont(QFont('Segoe UI', 42, QFont.Weight.Bold))
                p.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(flag))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()


class Timeline(QWidget):
    seekRequested = Signal(int)

    def __init__(self):
        super().__init__()
        self.duration = 0
        self.position = 0
        self.markers = Markers()
        self.setMinimumHeight(56)
        self.setMouseTracking(True)
        self.setToolTip('Posizione video')

    def x_for(self, ms):
        return 12 + round(max(0, min(ms, self.duration)) / max(1, self.duration) * (self.width() - 24))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor('#45505b'), 4))
        p.drawLine(12, 33, self.width() - 12, 33)
        p.setPen(QPen(QColor('#4bd6bd'), 4))
        p.drawLine(12, 33, self.x_for(self.position), 33)
        p.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        for marker, _ in self.markers.rows():
            x = self.x_for(marker.ms)
            p.setPen(QPen(QColor(COLORS[marker.flag]), 2))
            p.drawLine(x, 23, x, 40)
            p.drawText(QRect(x - 8, 1, 16, 21), Qt.AlignmentFlag.AlignCenter, str(marker.flag))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#ffffff'))
        p.drawEllipse(self.x_for(self.position) - 6, 27, 12, 12)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.duration:
            self.seek_at(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.duration:
            self.seek_at(event.position().x())

    def seek_at(self, x):
        self.seekRequested.emit(round(max(0, min(1, (x - 12) / max(1, self.width() - 24))) * self.duration))


class PlayerWindow(QMainWindow):
    def __init__(self, data_dir=None):
        super().__init__()
        self.setWindowTitle('TommeView - Video e intertempi')
        self.setWindowIcon(QIcon(str(RESOURCES / 'assets/tommeview.ico')))
        self.resize(1280, 800)
        self.setMinimumSize(940, 580)
        self.setAcceptDrops(True)
        self.store = SessionStore(data_dir if data_dir is not None else default_session_dir(),
                                  () if data_dir is not None else [BASE / 'data' / 'sessions'])
        self.translator = Translator(self.store.folder.parent / 'preferences.json')
        self.t = self.translator.text
        self.session_dirty = False
        self.pending_frame = None
        self.presented_frames = 0
        self.received_frames = 0
        self.markers = Markers()
        self.video_path = None
        self.save_allowed = True
        self.previous_ms = -1
        self.seek_pending = False
        self.seek_target = 0
        self.seek_started = 0
        self.seek_reverse = False
        self.direction = 1
        self.reverse_active = False
        self.reverse_origin = 0
        self.reverse_started = 0
        self.reverse_rate = 1.0
        self.jog_position = None
        self.reverse_timer = QTimer(self)
        self.reverse_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.reverse_timer.setInterval(33)
        self.reverse_timer.timeout.connect(self.reverse_tick)
        self.jog_timer = QTimer(self)
        self.jog_timer.setSingleShot(True)
        self.jog_timer.setInterval(16)
        self.jog_timer.timeout.connect(self.flush_jog)
        self.was_maximized = False
        self.video_only = False
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.7)
        self.player.setAudioOutput(self.audio)
        self.sink = QVideoSink(self)
        self.player.setVideoSink(self.sink)
        self.build_ui()
        self.retranslate()
        self.render_timer = QTimer(self)
        self.render_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.render_timer.setInterval(16)
        self.render_timer.timeout.connect(self.present_frame)
        self.render_timer.start()
        self.sink.videoFrameChanged.connect(self.on_frame)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_state)
        self.player.errorOccurred.connect(self.on_error)
        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.seekableChanged.connect(self.timeline.setEnabled)
        self.player.playbackRateChanged.connect(self.on_rate)
        QApplication.instance().installEventFilter(self)

    def tool(self, icon, tooltip, action, parent_layout):
        button = QToolButton()
        button.setIcon(self.control_icon(icon))
        button.setToolTip(tooltip)
        button.setFixedSize(36, 34)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.clicked.connect(action)
        parent_layout.addWidget(button)
        return button

    def control_icon(self, icon):
        original = icon if isinstance(icon, QIcon) else self.style().standardIcon(icon)
        if not isinstance(icon, QIcon) and icon not in (QStyle.StandardPixmap.SP_MediaPlay, QStyle.StandardPixmap.SP_MediaPause,
                       QStyle.StandardPixmap.SP_MediaSkipBackward, QStyle.StandardPixmap.SP_MediaVolume,
                       QStyle.StandardPixmap.SP_MediaVolumeMuted, QStyle.StandardPixmap.SP_TitleBarMaxButton):
            return original
        pixmap = original.pixmap(24, 24)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor('#e8edf1'))
        painter.end()
        return QIcon(pixmap)

    def build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(12, 10, 12, 8)
        root.setSpacing(10)
        header = QHBoxLayout()
        brand = QLabel('TommeView')
        brand.setStyleSheet('font-size: 20px; font-weight: 700; color: #4bd6bd;')
        header.addWidget(brand)
        open_button = QPushButton('Apri video')
        open_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        open_button.clicked.connect(self.choose_video)
        header.addSpacing(12)
        header.addWidget(open_button)
        self.download_dialog = None
        download_button = QPushButton('Scarica da YouTube')
        download_button.clicked.connect(self.show_acquisition)
        header.addWidget(download_button)
        self.filename = QLabel('Nessun file')
        self.filename.setProperty('i18n_skip', True)
        self.filename.setMinimumWidth(0)
        self.filename.setStyleSheet('color: #9eabb5;')
        header.addWidget(self.filename, 1)
        self.rotate_ccw = self.tool(QIcon(str(RESOURCES / 'assets/icons/rotate-ccw.svg')),
            'Ruota 90 gradi in senso antiorario', lambda: self.rotate_video(-90), header)
        self.rotate_cw = self.tool(QIcon(str(RESOURCES / 'assets/icons/rotate-cw.svg')),
            'Ruota 90 gradi in senso orario', lambda: self.rotate_video(90), header)
        self.tool(QStyle.StandardPixmap.SP_FileDialogDetailedView, 'Mostra/nascondi pannello flag', self.toggle_sidebar, header)
        self.tool(QStyle.StandardPixmap.SP_TitleBarMaxButton, 'Schermo intero (F11)', self.toggle_fullscreen, header)
        self.tool(QStyle.StandardPixmap.SP_TitleBarMaxButton, 'Solo video (F10)', self.toggle_video_only, header)
        self.tool(QStyle.StandardPixmap.SP_MessageBoxInformation, 'Informazioni su TommeView', self.show_about, header)
        self.language_buttons = {}
        for language, name in [('it', 'Italiano'), ('en', 'English')]:
            button = QToolButton()
            button.setFixedSize(36, 30)
            button.setIcon(QIcon(str(RESOURCES / f'assets/icons/{language}.svg')))
            button.setIconSize(QSize(26, 18))
            button.setToolTip(name)
            button.setAccessibleName(name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, lang=language: self.change_language(lang))
            self.language_buttons[language] = button
            header.addWidget(button)
        root.addLayout(header)
        splitter = QSplitter()
        left = QWidget()
        left_layout = QVBoxLayout(left)
        self.video_layout = left_layout
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        self.surface = VideoSurface()
        self.surface.clicked.connect(self.toggle_play)
        self.surface.doubleClicked.connect(self.toggle_video_only)
        left_layout.addWidget(self.surface, 1)
        self.timeline = Timeline()
        self.timeline.seekRequested.connect(self.seek)
        left_layout.addWidget(self.timeline)
        controls = QHBoxLayout()
        self.play_button = self.tool(QStyle.StandardPixmap.SP_MediaPlay, 'Riproduci avanti / pausa', self.toggle_forward, controls)
        self.reverse_icon = QIcon(self.control_icon(QStyle.StandardPixmap.SP_MediaPlay).pixmap(24, 24)
                                  .transformed(QTransform().scale(-1, 1)))
        self.reverse_button = self.tool(self.reverse_icon, 'Riproduci indietro / pausa', self.toggle_reverse, controls)
        self.reverse_button.setCheckable(True)
        self.tool(QStyle.StandardPixmap.SP_MediaSkipBackward, 'Torna all\'inizio', lambda: self.seek(0), controls)
        self.clock = QLabel('0.000 / 0.000 s')
        self.clock.setFont(QFont('Consolas', 10))
        self.clock.setMinimumWidth(145)
        controls.addWidget(self.clock)
        controls.addStretch()
        slower = QToolButton()
        slower.setText('-')
        slower.setFixedSize(30, 34)
        slower.setToolTip('Riduci velocita (-)')
        slower.clicked.connect(lambda: self.change_rate(-1))
        controls.addWidget(slower)
        self.rate_combo = QComboBox()
        self.rate_combo.addItems([f'{rate}%' for rate in RATES])
        self.rate_combo.setCurrentIndex(RATES.index(100))
        self.rate_combo.setFixedWidth(86)
        self.rate_combo.setToolTip('Velocita di riproduzione')
        self.rate_combo.currentIndexChanged.connect(lambda i: self.player.setPlaybackRate(RATES[i] / 100))
        controls.addWidget(self.rate_combo)
        faster = QToolButton()
        faster.setText('+')
        faster.setFixedSize(30, 34)
        faster.setToolTip('Aumenta velocita (+)')
        faster.clicked.connect(lambda: self.change_rate(1))
        controls.addWidget(faster)
        self.mute_button = self.tool(QStyle.StandardPixmap.SP_MediaVolume, 'Audio attivo / muto', self.toggle_mute, controls)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)
        self.volume.setFixedWidth(65)
        self.volume.setToolTip('Volume')
        self.volume.valueChanged.connect(lambda v: self.audio.setVolume(v / 100))
        controls.addWidget(self.volume)
        left_layout.addLayout(controls)
        splitter.addWidget(left)
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(300)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(10, 0, 0, 0)
        title_row = QHBoxLayout()
        self.count_label = QLabel('Flag  |  0')
        self.count_label.setStyleSheet('font-size: 16px; font-weight: 600;')
        title_row.addWidget(self.count_label, 1)
        self.tool(QStyle.StandardPixmap.SP_DialogSaveButton, 'Esporta tempi e intertempi in CSV', self.export, title_row)
        self.clear_button = self.tool(QStyle.StandardPixmap.SP_TrashIcon,
            'Cancella tutti i punti del video', self.clear_markers, title_row)
        self.reset_button = self.tool(QIcon(str(RESOURCES / 'assets/icons/database-x.svg')),
            'Reset database', self.reset_database, title_row)
        side.addLayout(title_row)
        flags = QGridLayout()
        flags.setSpacing(3)
        for flag in range(10):
            button = QToolButton()
            button.setText(str(flag))
            button.setFixedHeight(30)
            button.setMinimumWidth(25)
            button.setStyleSheet(f'color: {COLORS[flag]}; font-weight: 700; padding: 2px;')
            button.setToolTip(self.t('Aggiungi flag {flag}', flag=flag))
            button.setProperty('marker_flag', flag)
            button.clicked.connect(lambda checked=False, n=flag: self.add_marker(n))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda point, n=flag: self.edit_description(n))
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            flags.addWidget(button, flag // 5, flag % 5)
        side.addLayout(flags)
        self.filter = QComboBox()
        self.filter.addItem('Tutte le flag', None)
        for flag in range(10):
            self.filter.addItem(f'Flag {flag}', flag)
        self.filter.currentIndexChanged.connect(self.refresh_markers)
        side.addWidget(self.filter)
        self.table = QTableWidget(0, 5)
        self.table.setStyleSheet('QTableWidget::item { padding: 3px; } '
                                'QHeaderView::section { font-size: 11px; padding: 4px 2px; }')
        self.table.verticalHeader().setDefaultSectionSize(27)
        self.table.setHorizontalHeaderLabels(['Flag', 'Descrizione', 'Tempo (s)', 'Intertempo (s)', 'Cumulato (s)'])
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 32)
        for column in (2, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setWordWrap(True)
        self.table.horizontalHeader().sectionResized.connect(lambda *_: self.table.resizeRowsToContents())
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        self.table.cellClicked.connect(self.marker_clicked)
        side.addWidget(self.table, 1)
        self.save_label = QLabel('Nessuna sessione')
        self.save_label.setWordWrap(True)
        self.save_label.setStyleSheet('color: #9eabb5; font-size: 12px;')
        side.addWidget(self.save_label)
        splitter.addWidget(self.sidebar)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([780, 476])
        root.addWidget(splitter, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage(self.t('Pronto'))

    def show_acquisition(self):
        if self.download_dialog is None:
            self.download_dialog = AcquisitionDialog(self.translator,
                self.store.folder.parent / 'acquisition-preferences.json', self)
            self.download_dialog.videoReady.connect(self.open_video)
        self.download_dialog.show()
        self.download_dialog.raise_()
        self.download_dialog.activateWindow()

    def retranslate(self):
        self.translator.activate_qt()
        self.translator.widgets(self)
        self.setWindowTitle(f'{self.video_path.name} - TommeView' if self.video_path else self.t('TommeView - Video e intertempi'))
        if not self.video_path:
            self.filename.setText(self.t('Nessun file'))
        self.surface.empty_text = self.t('Nessun video aperto')
        self.table.setHorizontalHeaderLabels([self.t(s).replace(' (s)', '\n(s)')
            for s in ['Flag', 'Descrizione', 'Tempo (s)', 'Intertempo (s)', 'Cumulato (s)']])
        for index in range(1, self.filter.count()):
            self.filter.setItemText(index, self.t('Flag {flag}', flag=index - 1))
        for button in self.findChildren(QToolButton):
            flag = button.property('marker_flag')
            if flag is not None:
                button.setToolTip(self.t('Aggiungi flag {flag}', flag=flag))
        for language, button in self.language_buttons.items():
            button.setChecked(language == self.translator.language)
        self.refresh_markers()
        self.on_state(self.player.playbackState())
        self.surface.update()

    def change_language(self, language):
        try:
            self.translator.set_language(language)
        except OSError as exc:
            QMessageBox.warning(self, self.t('Preferenze non salvate'), str(exc))
            return
        self.retranslate()

    def confirm(self, title, text):
        was_playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        was_reverse = self.reverse_active
        self.pause_playback()
        dialog = QMessageBox(QMessageBox.Icon.Warning, self.t(title), self.t(text), parent=self)
        accept = dialog.addButton(self.t('Conferma'), QMessageBox.ButtonRole.DestructiveRole)
        cancel = dialog.addButton(self.t('Annulla'), QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel)
        dialog.setEscapeButton(cancel)
        dialog.exec()
        if was_playing:
            self.player.play()
        elif was_reverse:
            self.start_reverse()
        return dialog.clickedButton() == accept

    def rotate_video(self, delta):
        if not self.video_path:
            return
        self.markers.rotation = (self.markers.rotation + delta) % 360
        self.surface.rotation = self.markers.rotation
        self.surface.update()
        self.session_dirty = True
        self.save_session()

    def clear_markers(self):
        if not self.video_path or not self.confirm('Cancella tutti i punti del video', 'confirm_clear'):
            return
        replacement = Markers(rotation=self.markers.rotation, descriptions=self.markers.descriptions)
        try:
            self.store.save(self.video_path, replacement)
        except OSError as exc:
            QMessageBox.warning(self, self.t('Operazione non riuscita'), str(exc))
            return
        self.markers = replacement
        self.save_allowed = True
        self.session_dirty = False
        self.surface.clear_flash()
        self.refresh_markers()
        self.save_label.setText(self.t('Punti cancellati'))

    def reset_database(self):
        if not self.confirm('Reset database', 'confirm_reset'):
            return
        try:
            self.store.reset_all()
        except OSError as exc:
            QMessageBox.warning(self, self.t('Operazione non riuscita'), str(exc))
            return
        self.markers = Markers()
        self.surface.rotation = 0
        self.surface.clear_flash()
        self.save_allowed = True
        self.session_dirty = False
        self.refresh_markers()
        self.save_label.setText(self.t('Database azzerato'))

    def choose_video(self):
        path, _ = QFileDialog.getOpenFileName(self, self.t('Apri video'), '',
            self.t('Video (*.mp4 *.mkv *.avi *.mov *.wmv *.webm *.m4v *.mpg *.mpeg *.mts *.m2ts);;Tutti i file (*)'))
        if path:
            self.open_video(path)

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Informazioni su TommeView')
        dialog.setMinimumWidth(440)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        title = QLabel(f'{APP_NAME} {APP_VERSION}')
        title.setStyleSheet('font-size: 24px; font-weight: 700; color: #4bd6bd;')
        layout.addWidget(title)
        layout.addWidget(QLabel(self.t('Autore: {author}', author=APP_AUTHOR)))
        support = QLabel(self.t('support'))
        support.setWordWrap(True)
        support.setMaximumWidth(440)
        support.setStyleSheet('font-size: 15px; color: #ffca65;')
        layout.addWidget(support)
        license_notice = QLabel(self.t('third_party_notice'))
        license_notice.setObjectName('thirdPartyNotice')
        license_notice.setWordWrap(True)
        license_notice.setMaximumWidth(440)
        layout.addWidget(license_notice)
        licenses_button = QPushButton(self.t('Apri licenze'))
        licenses_button.setObjectName('openLicensesButton')
        licenses_button.clicked.connect(self.open_licenses)
        layout.addWidget(licenses_button)
        location = QLabel(self.t('Annotazioni: {path}', path=self.store.folder))
        location.setTextFormat(Qt.TextFormat.PlainText)
        location.setWordWrap(True)
        location.setMaximumWidth(440)
        location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(location)
        actions = QHBoxLayout()
        open_folder = QPushButton('Apri cartella annotazioni')
        open_folder.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        open_folder.clicked.connect(self.open_session_folder)
        actions.addWidget(open_folder)
        import_button = QPushButton('Importa flag...')
        import_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        import_button.clicked.connect(self.import_sessions)
        actions.addWidget(import_button)
        layout.addLayout(actions)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.button(QDialogButtonBox.StandardButton.Close).setText(self.t('Chiudi'))
        close.rejected.connect(dialog.reject)
        layout.addWidget(close)
        self.translator.widgets(dialog)
        dialog.exec()

    def open_licenses(self):
        documents = BASE
        folder = documents / 'licenses'
        if not folder.is_dir() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            QMessageBox.warning(self, self.t('Licenze'), self.t('license_folder_unavailable'))

    def open_session_folder(self):
        try:
            self.store.folder.mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.folder)))
        except OSError as exc:
            QMessageBox.warning(self, self.t('Cartella non accessibile'), str(exc))

    def import_sessions(self):
        folder = QFileDialog.getExistingDirectory(self, self.t('Seleziona la cartella data o sessions della versione precedente'))
        if not folder:
            return
        folder = Path(folder)
        for candidate in (folder / 'data' / 'sessions', folder / 'sessions'):
            if candidate.is_dir():
                folder = candidate
                break
        reload_current = (self.video_path is not None and not self.markers.items
                          and not self.store.path(self.video_path).exists())
        imported, skipped, errors = self.store.import_folder(folder)
        if reload_current and self.store.path(self.video_path).exists():
            self.markers = self.store.load(self.video_path)
            self.surface.rotation = self.markers.rotation
            self.refresh_markers()
        message = self.t('import_report', imported=imported, skipped=skipped, errors=len(errors))
        if errors:
            message += '\n\n' + '\n'.join(name + ': ' + self.t(detail) for name, _, detail in
                                           (error.partition(': ') for error in errors[:5]))
        QMessageBox.information(self, self.t('Importazione flag'), message)

    def open_video(self, path):
        path = Path(path).resolve()
        if not path.is_file():
            QMessageBox.warning(self, self.t('File non trovato'), str(path))
            return
        if not self.save_session():
            return
        self.pause_playback()
        self.direction = 1
        self.jog_position = None
        self.jog_timer.stop()
        self.pending_frame = None
        self.player.stop()
        self.player.setSource(QUrl())
        self.video_path = path
        self.save_allowed = True
        try:
            self.markers = self.store.load(path)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            self.markers = Markers()
            self.save_allowed = False
            QMessageBox.warning(self, self.t('Sessione non leggibile'),
                self.t('session_read_error', error=self.t(str(exc))))
        self.session_dirty = False
        self.surface.rotation = self.markers.rotation
        self.surface.native_rotation = 0
        self.surface.native_mirrored = False
        self.surface.image = QImage()
        self.surface.ms = 0
        self.surface.clear_flash()
        self.previous_ms = -1
        self.seek_pending = False
        self.filename.setText(self.fontMetrics().elidedText(path.name, Qt.TextElideMode.ElideMiddle, 420))
        self.filename.setToolTip(str(path))
        self.setWindowTitle(f'{path.name} - TommeView')
        self.refresh_markers()
        self.save_label.setText(self.t('Salvataggio automatico attivo') if self.save_allowed else self.t('Sessione non leggibile: usa Esporta CSV'))
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()

    def on_frame(self, frame):
        if not frame.isValid():
            return
        self.received_frames += 1
        self.pending_frame = QVideoFrame(frame)
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState or self.seek_pending:
            self.present_frame()

    def present_frame(self):
        frame = self.pending_frame
        self.pending_frame = None
        if frame is None or not frame.isValid():
            return
        ms = max(0, frame.startTime() // 1000) if frame.startTime() >= 0 else self.player.position()
        if self.seek_pending:
            # A queued frame from before setPosition must not finish a new seek.
            frame_duration = max(100, (frame.endTime() - frame.startTime()) // 1000)
            if abs(ms - self.seek_target) > frame_duration:
                return
            if self.seek_reverse:
                crossed = self.markers.crossed_reverse(self.previous_ms, ms)
                if crossed:
                    self.surface.flash([m.flag for m in crossed])
            self.seek_pending = False
            self.seek_reverse = False
        elif self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState and ms >= self.previous_ms:
            crossed = self.markers.crossed(self.previous_ms, ms)
            if crossed:
                self.surface.flash([m.flag for m in crossed])
        image = frame.toImage()
        if image.isNull():
            return
        self.presented_frames += 1
        self.surface.image = image
        self.surface.native_rotation = frame.rotation().value
        self.surface.native_mirrored = frame.mirrored()
        self.previous_ms = ms
        self.surface.ms = ms
        self.timeline.position = ms
        self.clock.setText(f'{seconds(ms)} / {seconds(self.player.duration())} s')
        self.timeline.update()
        self.surface.update()

    def on_duration(self, duration):
        self.timeline.duration = duration
        self.timeline.update()
        self.clock.setText(f'{seconds(self.surface.ms)} / {seconds(duration)} s')

    def on_state(self, state):
        if state != QMediaPlayer.PlaybackState.PlayingState:
            self.present_frame()
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        icon = QStyle.StandardPixmap.SP_MediaPause if playing else QStyle.StandardPixmap.SP_MediaPlay
        self.play_button.setIcon(self.control_icon(icon))
        self.reverse_button.setIcon(self.control_icon(QStyle.StandardPixmap.SP_MediaPause) if self.reverse_active else self.reverse_icon)
        self.reverse_button.setChecked(self.reverse_active)
        status = 'Riproduzione inversa' if self.reverse_active else 'Riproduzione' if playing else 'In pausa'
        self.statusBar().showMessage(self.t(status))

    def on_error(self, error, message):
        self.pause_playback()
        self.statusBar().showMessage(self.t('Errore video: {error}', error=message))
        QMessageBox.warning(self, self.t('Riproduzione non riuscita'), message)

    def on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.statusBar().showMessage(self.t('Fine video'))
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.player.setPlaybackRate(RATES[self.rate_combo.currentIndex()] / 100)

    def toggle_play(self):
        if not self.video_path:
            return
        if self.reverse_active or self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause_playback()
        elif self.direction == -1:
            self.start_reverse()
        else:
            self.flush_jog()
            self.jog_position = None
            if self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                self.seek(0)
            self.player.play()

    def toggle_forward(self):
        if self.reverse_active:
            self.pause_playback()
        self.direction = 1
        self.toggle_play()

    def toggle_reverse(self):
        if self.reverse_active:
            self.pause_playback()
        else:
            self.start_reverse()

    def pause_playback(self):
        self.reverse_active = False
        self.reverse_timer.stop()
        self.player.pause()
        self.on_state(self.player.playbackState())

    def start_reverse(self):
        if not self.video_path or not self.player.isSeekable():
            self.on_state(self.player.playbackState())
            return
        self.pause_playback()
        self.flush_jog()
        self.jog_position = None
        self.direction = -1
        self.reverse_origin = self.seek_target if self.seek_pending else self.surface.ms
        if self.reverse_origin <= 0:
            self.reverse_origin = max(0, self.player.duration() - 1)
            self.seek(self.reverse_origin)
        self.reverse_started = time.monotonic()
        self.reverse_rate = self.player.playbackRate()
        self.reverse_active = True
        self.reverse_timer.start()
        self.on_state(self.player.playbackState())

    def reverse_position(self):
        return max(0, self.reverse_origin - (time.monotonic() - self.reverse_started) * 1000 * self.reverse_rate)

    def reverse_tick(self):
        if not self.reverse_active:
            return
        # Serialize decoder seeks. Wall time, not decoder throughput, sets media speed.
        if self.seek_pending and time.monotonic() - self.seek_started < 1:
            return
        target = round(self.reverse_position())
        self.seek(target, playback=True)
        if target == 0:
            self.pause_playback()

    def jog(self, steps):
        if (not steps or not self.video_path or not self.player.isSeekable() or self.reverse_active
                or self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState):
            return
        if self.jog_position is None:
            self.jog_position = float(self.seek_target if self.seek_pending else self.surface.ms)
        # One notch = 100 media milliseconds at 100%; retain fractional wheel motion.
        self.jog_position = max(0, min(self.player.duration() - 1,
            self.jog_position + steps * 100 * self.player.playbackRate()))
        if not self.jog_timer.isActive():
            self.jog_timer.start()

    def flush_jog(self):
        self.jog_timer.stop()
        if self.jog_position is not None:
            self.seek(round(self.jog_position), jog=True)

    def seek(self, ms, playback=False, jog=False):
        if not self.player.isSeekable():
            return
        if not jog and not playback:
            self.jog_position = None
            self.jog_timer.stop()
        if not playback:
            self.surface.clear_flash()
        self.pending_frame = None
        self.seek_target = max(0, min(round(ms), max(0, self.player.duration() - 1)))
        if self.reverse_active and not playback:
            self.reverse_origin = self.seek_target
            self.reverse_started = time.monotonic()
        if not self.seek_pending and (self.seek_target == self.surface.ms or self.seek_target == self.player.position()):
            return
        self.seek_started = time.monotonic()
        self.seek_reverse = playback
        self.seek_pending = True
        self.player.setPosition(self.seek_target)

    def change_rate(self, direction):
        index = max(0, min(len(RATES) - 1, self.rate_combo.currentIndex() + direction))
        self.rate_combo.setCurrentIndex(index)

    def on_rate(self, rate):
        if self.reverse_active:
            self.reverse_origin = self.reverse_position()
            self.reverse_started = time.monotonic()
        self.reverse_rate = rate
        self.surface.rate = round(rate * 100)
        self.surface.update()

    def add_marker(self, flag):
        if (not self.video_path or self.surface.image.isNull() or self.jog_timer.isActive()
                or (self.seek_pending and not self.seek_reverse)):
            return
        self.markers.add(flag, self.surface.ms)
        self.session_dirty = True
        self.surface.flash([flag])
        self.refresh_markers()
        self.save_session()

    def refresh_markers(self):
        rows = [(m, delta, cumulative) for m, delta, cumulative in self.markers.cumulative_rows()
                if self.filter.currentData() is None or m.flag == self.filter.currentData()]
        self.table.setRowCount(len(rows))
        for row, (marker, delta, cumulative) in enumerate(rows):
            for column, value in enumerate([str(marker.flag), self.markers.descriptions.get(str(marker.flag), ''), seconds(marker.ms), '--' if delta is None else seconds(delta), seconds(cumulative)]):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, marker.id)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if column == 0 else Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if column == 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                item.setForeground(QColor(COLORS[marker.flag]) if column == 0 else QColor('#e8edf1'))
                item.setFont(QFont('Segoe UI' if column == 0 else 'Consolas', 10))
                item.setToolTip(value)
                self.table.setItem(row, column, item)
        self.table.resizeRowsToContents()
        self.count_label.setText(self.t('Flag  |  {count}', count=len(self.markers.items)))
        self.timeline.markers = self.markers
        self.timeline.update()

    def marker_clicked(self, row, column):
        item = self.table.item(row, 0)
        marker = next((m for m in self.markers.items if m.id == item.data(Qt.ItemDataRole.UserRole)), None)
        if marker:
            self.seek(marker.ms)
            self.surface.flash([marker.flag])

    def context_menu(self, point):
        item = self.table.itemAt(point)
        if item is None:
            return
        marker_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        describe = menu.addAction(self.t('Modifica descrizione tag'))
        remove = menu.addAction(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon), self.t('Elimina punto'))
        selected = menu.exec(self.table.viewport().mapToGlobal(point))
        if selected == describe:
            marker = next(m for m in self.markers.items if m.id == marker_id)
            self.edit_description(marker.flag)
        elif selected == remove:
            self.delete_marker(marker_id)

    def edit_description(self, flag):
        if not self.video_path or not self.save_allowed:
            return
        value, accepted = QInputDialog.getMultiLineText(self, self.t('Modifica descrizione tag'),
            self.t('Descrizione tag {flag}', flag=flag), self.markers.descriptions.get(str(flag), ''))
        if accepted:
            self.markers.descriptions[str(flag)] = value.strip()
            self.session_dirty = True
            self.refresh_markers()
            self.save_session()

    def delete_marker(self, marker_id):
        self.markers.remove(marker_id)
        self.session_dirty = True
        self.refresh_markers()
        self.save_session()

    def save_session(self):
        if not self.video_path or not self.save_allowed or not self.session_dirty:
            return True
        try:
            self.store.save(self.video_path, self.markers)
            self.session_dirty = False
            self.save_label.setText(self.t('Flag salvate automaticamente'))
            return True
        except OSError as exc:
            self.save_label.setText(self.t('Salvataggio fallito: esporta in CSV'))
            QMessageBox.warning(self, self.t('Salvataggio fallito'), str(exc))
            return False

    def export(self):
        if not self.video_path:
            return
        path, _ = QFileDialog.getSaveFileName(self, self.t('Esporta tempi'), str(self.video_path.with_suffix('.flag.csv')), 'CSV (*.csv)')
        if path:
            try:
                export_csv(path, self.markers, self.t, self.translator.language)
                self.statusBar().showMessage(self.t('CSV esportato: {path}', path=path), 6000)
            except OSError as exc:
                QMessageBox.warning(self, self.t('Esportazione fallita'), str(exc))

    def toggle_mute(self):
        self.audio.setMuted(not self.audio.isMuted())
        icon = QStyle.StandardPixmap.SP_MediaVolumeMuted if self.audio.isMuted() else QStyle.StandardPixmap.SP_MediaVolume
        self.mute_button.setIcon(self.control_icon(icon))

    def toggle_sidebar(self):
        if self.video_only:
            return
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def toggle_video_only(self):
        if self.video_only:
            self.takeCentralWidget()
            self.setCentralWidget(self.normal_central)
            self.video_layout.insertWidget(0, self.surface, 1)
            self.normal_central.show()
            self.statusBar().setVisible(self.previous_status_visible)
            self.setWindowState(self.previous_window_state)
        else:
            self.previous_window_state = self.windowState()
            self.previous_status_visible = self.statusBar().isVisible()
            self.normal_central = self.takeCentralWidget()
            self.normal_central.hide()
            self.video_layout.removeWidget(self.surface)
            self.setCentralWidget(self.surface)
            self.surface.show()
            self.statusBar().hide()
            self.showFullScreen()
        self.video_only = not self.video_only
        self.surface.video_only = self.video_only
        self.surface.update()

    def toggle_fullscreen(self):
        if self.video_only:
            self.toggle_video_only()
            return
        if self.isFullScreen():
            self.showMaximized() if self.was_maximized else self.showNormal()
        else:
            self.was_maximized = self.isMaximized()
            self.showFullScreen()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel and obj in (self.surface, self.timeline, self.table.viewport()):
            if not QApplication.activeModalWidget() and not QApplication.activePopupWidget():
                steps = event.pixelDelta().y() / 40 if not event.pixelDelta().isNull() else event.angleDelta().y() / 120
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    if steps:
                        self.change_rate(1 if steps > 0 else -1)
                    event.accept()
                    return True
                moving = self.reverse_active or self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
                if moving:
                    if obj != self.table.viewport():
                        QApplication.sendEvent(self.table.viewport(), event)
                        return True
                    return super().eventFilter(obj, event)
                self.jog(steps)
                event.accept()
                return True
        if event.type() not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            return super().eventFilter(obj, event)
        if QApplication.activeModalWidget() or QApplication.activePopupWidget() or QApplication.activeWindow() != self:
            return super().eventFilter(obj, event)
        key = event.key()
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier):
            return False
        digit = key - Qt.Key.Key_0 if Qt.Key.Key_0 <= key <= Qt.Key.Key_9 else None
        handled = digit is not None or key in (Qt.Key.Key_Space, Qt.Key.Key_Plus, Qt.Key.Key_Minus,
            Qt.Key.Key_Equal, Qt.Key.Key_F10, Qt.Key.Key_F11, Qt.Key.Key_Escape)
        if not handled:
            return super().eventFilter(obj, event)
        event.accept()
        if event.type() == QEvent.Type.ShortcutOverride or event.isAutoRepeat():
            return True
        if digit is not None:
            self.add_marker(digit)
        elif key == Qt.Key.Key_Space:
            self.toggle_play()
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.change_rate(1)
        elif key == Qt.Key.Key_Minus:
            self.change_rate(-1)
        elif key == Qt.Key.Key_F10:
            self.toggle_video_only()
        elif key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif key == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        return True

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].isLocalFile():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.open_video(event.mimeData().urls()[0].toLocalFile())

    def closeEvent(self, event):
        if self.download_dialog and self.download_dialog.busy():
            if not getattr(self, '_closing_download', False):
                self._closing_download = True
                self.download_dialog.worker.finished.connect(self.close)
            self.download_dialog.close()
            event.ignore()
            return
        self._closing_download = False
        if self.video_only:
            self.toggle_video_only()
        if not self.save_session():
            event.ignore()
            return
        self.pause_playback()
        self.jog_timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        QApplication.instance().removeEventFilter(self)
        super().closeEvent(event)


def main():
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument('video', nargs='?')
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--self-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        try:
            from smoke_test import run
            run()
        except Exception:
            import traceback
            (BASE / 'self-test-error.log').write_text(traceback.format_exc(), encoding='utf-8')
            sys.exit(1)
        return
    app = QApplication(sys.argv[:1])
    app.setApplicationName('TommeView')
    app.setApplicationVersion(APP_VERSION)
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    window = PlayerWindow(args.data_dir)
    window.show()
    path = BASE / 'demo' / 'demo.avi' if args.demo else args.video
    if path:
        QTimer.singleShot(150, lambda: window.open_video(path))
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
