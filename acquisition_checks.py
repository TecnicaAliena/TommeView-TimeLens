"""Offline UI checks included in the packaged self-test."""
from pathlib import Path
import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import acquisition_ui


def run_acquisition_checks(window, output):
    original_acquire = acquisition_ui.acquire
    original_tools = acquisition_ui.find_tools
    opened = []

    def wait(predicate):
        deadline = time.monotonic() + 5
        while not predicate():
            assert time.monotonic() < deadline, 'Acquisition UI timeout'
            QApplication.processEvents()
            time.sleep(.01)
        QApplication.processEvents()

    try:
        window.show_acquisition()
        dialog = window.download_dialog
        dialog.videoReady.disconnect(window.open_video)
        dialog.videoReady.connect(opened.append)
        acquisition_ui.find_tools = lambda _: {}
        acquisition_ui.acquire = lambda *args: Path(output) / 'fixture.mkv'
        dialog.url.setText('https://youtu.be/BaW_jenozKc')
        dialog.folder.setText(str(Path(output) / 'acquisitions'))
        assert not dialog.acknowledgement.isChecked()
        assert not dialog.start_button.isEnabled()
        dialog.start_download()
        assert dialog.worker is None
        dialog.acknowledgement.setChecked(True)
        assert dialog.start_button.isEnabled()
        dialog.url.setText('https://www.youtube.com/watch?v=BaW_jenozKc')
        assert not dialog.acknowledgement.isChecked()
        assert not dialog.start_button.isEnabled()
        dialog.acknowledgement.setChecked(True)
        dialog.start_download()
        wait(lambda: not dialog.busy() and dialog.url.isEnabled())
        assert not dialog.acknowledgement.isChecked()
        assert not dialog.start_button.isEnabled()
        assert len(opened) == 1 and dialog.open_button.isEnabled()
        assert dialog.progress_bar.value() == 100
        assert dialog.preferences.exists()
        dialog.grab().save(str(Path(output) / 'acquisition-dialog.png'))

        def cancellable(url, folder, tools, cancelled, *args):
            from acquisition import AcquisitionCancelled
            assert cancelled.wait(4), 'Cancellation not delivered'
            raise AcquisitionCancelled()

        acquisition_ui.acquire = cancellable
        dialog.acknowledgement.setChecked(True)
        dialog.start_download()
        assert not dialog.start_button.isEnabled()
        assert not dialog.acknowledgement.isEnabled()
        QTimer.singleShot(50, dialog.close)
        wait(lambda: not dialog.busy() and not dialog.isVisible())
        assert not dialog.open_button.isEnabled()
        assert len(opened) == 1
        dialog.show()
        assert not dialog.acknowledgement.isChecked()
        dialog.acknowledgement.setChecked(True)
        dialog.close()
        dialog.show()
        assert not dialog.acknowledgement.isChecked()
        assert not dialog.start_button.isEnabled()
    finally:
        acquisition_ui.acquire = original_acquire
        acquisition_ui.find_tools = original_tools
        if window.download_dialog:
            window.download_dialog.videoReady.disconnect(opened.append)
            window.download_dialog.videoReady.connect(window.open_video)
            window.download_dialog.close()
        window.activateWindow()
