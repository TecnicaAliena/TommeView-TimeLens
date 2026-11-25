"""Exercise actual FFmpeg decoding and desktop controls with a generated video."""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QContextMenuEvent, QFontDatabase
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QDialogButtonBox, QDoubleSpinBox, QLabel, QMenu, QPushButton,
                              QSpinBox, QToolButton)
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


def check_playback_zones(window, output):
    def drag(widget, start, end):
        QTest.mousePress(widget, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(widget, end)
        QTest.mouseRelease(widget, Qt.MouseButton.LeftButton, pos=end)

    def accept_zone():
        dialog = QApplication.activeModalWidget()
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).click()

    surface = window.surface
    timeline = window.timeline
    saved_markers = window.markers.items.copy()
    for flag, times in ((7, (2000, 5500)), (8, (2000, 3000, 4000)), (9, (16_000, 18_000))):
        for ms in times:
            window.markers.add(flag, ms)
    window.refresh_markers()

    def draw_zoom_crop():
        window.zone_buttons['zoom'].click()
        bounds = surface.full_image_transform().mapRect(surface.image.rect())
        start = QPoint(round(bounds.left() + bounds.width() * .2), round(bounds.top() + bounds.height() * .2))
        end = QPoint(round(bounds.left() + bounds.width() * .6), round(bounds.top() + bounds.height() * .6))
        drag(surface, start, end)

    window.seek(1000)
    wait_until(lambda: not window.seek_pending)
    draw_zoom_crop()
    assert timeline.draft.kind == 'zoom'
    assert timeline.draft.start == window.surface.ms
    assert timeline.draft.end - timeline.draft.start == 5000
    QTest.keyClick(window, Qt.Key.Key_8)
    assert timeline.draft and len(window.markers.items) == len(saved_markers) + 7
    seven = next(button for button in window.findChildren(QToolButton) if button.property('marker_flag') == 7)
    QTest.mouseClick(seven, Qt.MouseButton.LeftButton)
    zoom = window.markers.zones[0]
    assert (zoom.start, zoom.end) == (2000, 5500)
    assert zoom.kind == 'zoom' and zoom.enter_ms == zoom.exit_ms == 200
    window.add_marker(7)
    assert len([item for item in window.markers.items if item.flag == 7]) == 3
    assert window.markers.zones[0] == zoom
    window.seek(2500)
    wait_until(lambda: not window.seek_pending)
    window.zone_buttons['speed'].click()
    proposal = timeline.draft
    assert proposal.start == window.surface.ms and proposal.end - proposal.start == 5000
    QTest.mouseClick(window.clock, Qt.MouseButton.LeftButton)
    assert not timeline.draft and proposal in window.markers.zones

    def speed_area():
        return next(zone for zone in window.markers.zones if zone.kind == 'speed')

    rect = timeline.zone_rect(proposal)
    left_edge = QPoint(rect.left(), rect.center().y())
    QTest.mouseMove(timeline, left_edge)
    assert timeline.cursor().shape() == Qt.CursorShape.SizeHorCursor
    drag(timeline, left_edge, left_edge - QPoint(12, 0))
    stretched = speed_area()
    assert stretched.start < proposal.start and stretched.end == proposal.end
    rect = timeline.zone_rect(stretched)
    right_edge = QPoint(rect.right(), rect.center().y())
    drag(timeline, right_edge, right_edge + QPoint(12, 0))
    resized = speed_area()
    assert resized.start == stretched.start and resized.end > stretched.end
    center = timeline.zone_rect(resized).center()
    QTest.mouseMove(timeline, center)
    assert timeline.cursor().shape() == Qt.CursorShape.SizeAllCursor
    drag(timeline, center, center + QPoint(16, 0))
    speed = speed_area()
    assert speed.start > resized.start and speed.end - speed.start == resized.end - resized.start
    assert {zone.kind for zone in window.store.load(window.video_path).zones} == {'zoom', 'speed'}
    duration = timeline.duration
    timeline.duration = 600_000
    assert timeline.default_span(1000) == (1000, 31_000)
    timeline.duration = duration

    try:
        window.rate_combo.setCurrentIndex(RATES.index(50))
        window.seek(3000)
        wait_until(lambda: not window.seek_pending)
        assert abs(window.player.playbackRate() - .05) < .0001
        assert surface.zoom_region(time.monotonic()) == zoom.region
        window.grab().save(str(output / 'playback-zones.png'))
        # Use a synthetic wall-clock to assert the same transition duration
        # irrespective of the master rate or the local speed multiplier.
        with patch('player.time.monotonic', return_value=10):
            window.update_effects(6000, animate=True)
            assert abs(surface.zoom_until - 10.2) < .0001
            assert surface.zoom_region(10) == zoom.region
            assert surface.zoom_region(10.2) == (0.0, 0.0, 1.0, 1.0)
        window.seek(2300)
        wait_until(lambda: not window.seek_pending)
        window.toggle_forward()
        wait_until(lambda: abs(window.player.playbackRate() - .05) < .0001)
        window.pause_playback()
        window.seek(10_000)
        wait_until(lambda: not window.seek_pending)
        assert abs(window.player.playbackRate() - .50) < .0001
        draw_zoom_crop()
        default_zoom = timeline.draft
        assert default_zoom.start == window.surface.ms and default_zoom.end - default_zoom.start == 5000
        QTest.mouseClick(window.clock, Qt.MouseButton.LeftButton)
        assert default_zoom in window.markers.zones and not timeline.draft

        def choose_zone_action(zone, row, index):
            def choose():
                menu = QApplication.activePopupWidget()
                menu.setActiveAction(menu.actions()[index])
                QTest.keyClick(menu, Qt.Key.Key_Return)
            pos = QPoint(timeline.x_for((zone.start + zone.end) // 2), row)
            QTimer.singleShot(50, choose)
            QApplication.sendEvent(timeline, QContextMenuEvent(
                QContextMenuEvent.Reason.Mouse, pos, timeline.mapToGlobal(pos)))

        def edit_zoom_duration():
            dialog = QApplication.activeModalWidget()
            dialog.findChildren(QDoubleSpinBox)[2].setValue(.4)
            accept_zone()

        QTimer.singleShot(200, edit_zoom_duration)
        choose_zone_action(zoom, 55, 0)
        assert next(zone for zone in window.markers.zones if zone.id == zoom.id).enter_ms == 400
        with patch('player.QInputDialog.getDouble', return_value=(2.1, True)):
            window.edit_marker_time(zoom.start_marker)
        linked_zoom = next(zone for zone in window.store.load(window.video_path).zones if zone.id == zoom.id)
        assert linked_zoom.start == 2100 and linked_zoom.end == 5500

        window.zone_buttons['speed'].click()
        assert timeline.draft and timeline.draft.kind == 'speed'
        window.activateWindow()
        wait_until(lambda: QApplication.activeWindow() is window and not QApplication.activePopupWidget())
        QTest.keyClick(window, Qt.Key.Key_9)
        linked_speed = next(zone for zone in window.markers.zones if zone.kind == 'speed' and zone.start_marker)
        assert (linked_speed.start, linked_speed.end) == (16_000, 18_000)

        def edit_speed_factor():
            QApplication.activeModalWidget().findChild(QSpinBox).setValue(200)
            accept_zone()

        QTimer.singleShot(200, edit_speed_factor)
        choose_zone_action(linked_speed, 75, 0)
        window.seek(17_000)
        wait_until(lambda: not window.seek_pending)
        assert abs(window.player.playbackRate() - 1.0) < .0001
        speed = next(zone for zone in window.markers.zones if zone.kind == 'speed')
        choose_zone_action(speed, 75, 1)
        assert [zone.kind for zone in window.store.load(window.video_path).zones] == ['zoom', 'zoom', 'speed']
    finally:
        window.pause_playback()
        window.start_zone(None)
        window.markers.zones.clear()
        window.markers.items = saved_markers
        window.refresh_markers()
        window.zones_changed()
        window.rate_combo.setCurrentIndex(RATES.index(100))
    return ['current-position defaults and exactly two markers per numeric tag',
            'timeline edge resizing, center movement and cursor hints',
            'linked marker movement and adding unrelated same-label points',
            'numeric speed area with acceleration above master speed',
            'persistent overlapping zoom and slowdown',
            'live slowdown boundary, seek and master rate', 'wall-clock zoom easing',
            'timeline context menu editing and deletion']


def run():
    app = QApplication([])
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'consola.ttf', 'consolab.ttf'):
        QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR']) / 'Fonts' / name))
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    output = BASE / 'test-output'
    output.mkdir(exist_ok=True)
    run_tool_checks(output)
    session_dir = tempfile.TemporaryDirectory(prefix='smoke-session-', dir=output)
    window = PlayerWindow(Path(session_dir.name) / 'sessions')
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
        zone_checks = check_playback_zones(window, output)
        report = {'result': 'PASS', 'rates': measurements, 'markers': len(expected),
                  'checks': ['decode', 'pause via space', 'numeric flags with table focus',
                  'same-flag intervals', 'row click seek while paused', 'context menu deletion',
                  'crossing flash and 500 ms expiry', 'seek does not flash skipped flags',
                  'real playback 5%/10%/100%/1000%', 'rate keyboard limits', 'fullscreen', 'session persistence',
                  'seek to same frame', 'seek to end and replay', 'user AppData path', 'author and support dialog']}
        report['checks'].extend(release_checks)
        report['checks'].extend(transport_checks)
        report['checks'].extend(zone_checks)
        (output / 'smoke-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        window.close()
        app.processEvents()
        session_dir.cleanup()


if __name__ == '__main__':
    run()
