"""Exercise actual FFmpeg decoding and desktop controls with a generated video."""
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QPushButton
from player import BASE, STYLE, PlayerWindow, default_session_dir
from app_info import APP_AUTHOR
from release_checks import run_release_checks
from transport_checks import run_transport_checks
from model import RATES
from acquisition_checks import run_acquisition_checks
from acquisition_tool_checks import run_tool_checks


def wait_until(predicate, timeout=5000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        QApplication.processEvents()
        if predicate():
            return
        QTest.qWait(20)
    raise AssertionError('Timeout in attesa della condizione')


def run():
    app = QApplication([])
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'consola.ttf', 'consolab.ttf'):
        QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR']) / 'Fonts' / name))
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    output = BASE / 'test-output'
    output.mkdir(exist_ok=True)
    run_tool_checks(output)
    window = PlayerWindow(output / 'sessions')
    window.change_language('it')
    window.show()
    window.activateWindow()
    run_acquisition_checks(window, output)
    video_fixture = Path(os.environ.get('TOMMEVIEW_TEST_VIDEO', str(BASE / 'demo' / 'demo.avi')))
    if not video_fixture.is_file():
        raise RuntimeError('Set TOMMEVIEW_TEST_VIDEO to the repository demo/demo.avi for packaged tests')
    window.open_video(video_fixture)
    try:
        wait_until(lambda: not window.surface.image.isNull() and window.surface.ms >= 300)
        QTest.keyClick(window, Qt.Key.Key_Space)
        assert window.player.playbackState() == QMediaPlayer.PlaybackState.PausedState
        QTest.qWait(150)
        paused = window.surface.ms
        QTest.qWait(150)
        assert window.surface.ms == paused
        window.seek(paused)
        assert not window.seek_pending
        window.markers.items.clear()
        for flag, ms in [(1, 1000), (2, 2000), (1, 3500), (2, 4500)]:
            window.seek(ms)
            wait_until(lambda: not window.seek_pending and abs(window.surface.ms - ms) <= 34)
            QTest.keyClick(window.table, Qt.Key.Key_0 + flag)
        assert len(window.markers.items) == 4
        assert [delta for _, delta in window.markers.rows()] == [None, None, 2500, 2500]
        # A real click on a row seeks the paused decoder to the marker.
        rect = window.table.visualItemRect(window.table.item(0, 1))
        QTest.mouseClick(window.table.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
        wait_until(lambda: not window.seek_pending and abs(window.surface.ms - 1000) <= 34)
        # Trigger the actual context menu and choose its deletion action.
        QTimer.singleShot(100, lambda: app.activePopupWidget().setActiveAction(app.activePopupWidget().actions()[-1]))
        QTimer.singleShot(180, lambda: QTest.keyClick(app.activePopupWidget(), Qt.Key.Key_Return))
        window.context_menu(window.table.visualItemRect(window.table.item(0, 1)).center())
        assert len(window.markers.items) == 3
        assert [delta for _, delta in window.markers.rows()] == [None, None, 2500]
        # Restore a marker for the crossing test, then jump across it without flashing.
        window.markers.add(1, 1000)
        window.session_dirty = True
        window.refresh_markers()
        window.seek(3000)
        wait_until(lambda: not window.seek_pending)
        assert not window.surface.flash_flags
        window.seek(700)
        wait_until(lambda: not window.seek_pending)
        window.toggle_play()
        wait_until(lambda: 1 in window.surface.flash_flags)
        window.toggle_play()
        QTest.qWait(550)
        assert not window.surface.flash_flags
        # Verify both rate limits against real media time advancement.
        measurements = {}
        for rate in (5, 10, 100, 1000):
            window.rate_combo.setCurrentIndex(RATES.index(rate))
            assert round(window.player.playbackRate() * 100) == rate
            window.seek(5000)
            wait_until(lambda: not window.seek_pending)
            window.toggle_play()
            start = window.surface.ms
            wall = time.monotonic()
            QTest.qWait(2200 if rate == 5 else 1400 if rate == 10 else 650)
            elapsed = time.monotonic() - wall
            advanced = window.surface.ms - start
            window.toggle_play()
            measured = advanced / (elapsed * 1000)
            measurements[str(rate)] = {'media_ms': advanced, 'wall_s': round(elapsed, 3), 'measured_rate': round(measured, 3)}
            assert rate / 100 * .55 < measured < rate / 100 * 1.45, measurements
        for _ in range(30):
            QTest.keyClick(window, Qt.Key.Key_Minus)
        assert window.surface.rate == 5
        for _ in range(30):
            QTest.keyClick(window, Qt.Key.Key_Plus)
        assert window.surface.rate == 1000
        QTest.keyClick(window, Qt.Key.Key_F11)
        assert window.isFullScreen()
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert not window.isFullScreen()
        window.rate_combo.setCurrentIndex(RATES.index(100))
        window.seek(6500)
        wait_until(lambda: not window.seek_pending and abs(window.surface.ms - 6500) <= 34)
        QTest.qWait(100)
        window.surface.clear_flash()
        window.grab().save(str(output / 'desktop.png'))
        window.resize(1000, 580)
        QTest.qWait(100)
        window.grab().save(str(output / 'compact.png'))
        assert window.table.width() >= 290
        assert not window.surface.image.isNull()
        assert window.save_session()
        expected = window.markers.items.copy()
        assert window.store.load(window.video_path).items == sorted(expected, key=lambda m: m.ms)
        window.seek(window.player.duration())
        wait_until(lambda: not window.seek_pending)
        window.toggle_play()
        wait_until(lambda: window.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia)
        window.toggle_play()
        wait_until(lambda: window.surface.ms < 1000)
        window.toggle_play()
        assert default_session_dir() == Path(os.environ['LOCALAPPDATA']) / 'TommeView' / 'sessions'
        about_checks = []
        def inspect_about():
            dialog = app.activeModalWidget()
            labels = [label.text() for label in dialog.findChildren(QLabel)]
            about_checks.append(any(APP_AUTHOR in text for text in labels) and window.t('support') in labels)
            about_checks.append(window.t('third_party_notice') in labels)
            button = dialog.findChild(QPushButton, 'openLicensesButton')
            with patch('player.QDesktopServices.openUrl', return_value=True) as open_url:
                button.click()
                about_checks.append(open_url.call_count == 1 and Path(open_url.call_args.args[0].toLocalFile()).name == 'licenses')
            screenshot = 'about.png' if window.translator.language == 'it' else 'about-en.png'
            dialog.grab().save(str(output / screenshot))
            dialog.accept()
        for language in ('it', 'en'):
            window.change_language(language)
            QTimer.singleShot(150, inspect_about)
            window.show_about()
        window.change_language('it')
        assert about_checks == [True, True, True] * 2
        with patch('player.QDesktopServices.openUrl', return_value=False), patch('player.QMessageBox.warning') as warning:
            window.open_licenses()
            assert warning.call_count == 1
        transport_checks = run_transport_checks(window, output, wait_until)
        window.pause_playback()
        old_state = window.windowState()
        QTest.keyClick(window, Qt.Key.Key_F10)
        assert window.video_only and window.isFullScreen()
        assert window.centralWidget() is window.surface
        assert not window.sidebar.isVisible()
        window.surface.flash([1])
        assert window.surface.flash_flags == [1]
        window.grab().save(str(output / 'video-only.png'))
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert not window.video_only and window.windowState() == old_state
        def enter_description():
            dialog = app.activeModalWidget()
            dialog.setTextValue('tempo pinza\ninizio movimento')
            dialog.accept()
        QTimer.singleShot(100, enter_description)
        window.edit_description(1)
        assert window.markers.descriptions['1'] == 'tempo pinza\ninizio movimento'
        assert window.store.load(window.video_path).descriptions == window.markers.descriptions
        assert any(window.table.item(row, 1).text() == 'tempo pinza\ninizio movimento'
                   for row in range(window.table.rowCount()))
        window.grab().save(str(output / 'descriptions.png'))
        release_checks = run_release_checks(window, output, wait_until)
        report = {'result': 'PASS', 'rates': measurements, 'markers': len(expected),
                  'checks': ['decode', 'pause via space', 'numeric flags with table focus',
                  'same-flag intervals', 'row click seek while paused', 'context menu deletion',
                  'crossing flash and 500 ms expiry', 'seek does not flash skipped flags',
                  'real playback 5%/10%/100%/1000%', 'rate keyboard limits', 'fullscreen', 'session persistence',
                  'seek to same frame', 'seek to end and replay', 'user AppData path', 'author and support dialog']}
        report['checks'].extend(release_checks)
        report['checks'].extend(transport_checks)
        (output / 'smoke-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        window.close()
        app.processEvents()


if __name__ == '__main__':
    run()
