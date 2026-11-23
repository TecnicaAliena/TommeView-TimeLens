"""Integration checks against real decoded frames and Qt wheel events."""
import json
import time

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolButton

from model import RATES


def run_transport_checks(window, output, wait_until):
    def seek(ms):
        window.pause_playback()
        window.seek(ms)
        wait_until(lambda: not window.seek_pending)

    def wheel(widget, angle=120, pixels=0, modifiers=Qt.KeyboardModifier.NoModifier):
        pos = widget.rect().center()
        event = QWheelEvent(QPointF(pos), QPointF(widget.mapToGlobal(pos)), QPoint(0, pixels),
            QPoint(0, angle), Qt.MouseButton.NoButton, modifiers,
            Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(widget, event)

    window.activateWindow()
    measurements = {}
    for rate in (5, 100, 1000):
        window.rate_combo.setCurrentIndex(RATES.index(rate))
        seek(15000)
        start = window.surface.ms
        QTest.mouseClick(window.reverse_button, Qt.MouseButton.LeftButton)
        assert window.reverse_active and window.reverse_button.isChecked()
        assert window.player.playbackState() == QMediaPlayer.PlaybackState.PausedState
        wall = time.monotonic()
        QTest.qWait(2200 if rate == 5 else 750)
        elapsed = time.monotonic() - wall
        advanced = start - window.surface.ms
        measured = advanced / (elapsed * 1000)
        measurements[str(rate)] = {'media_ms': advanced, 'wall_s': round(elapsed, 3), 'measured_rate': round(measured, 3)}
        assert rate / 100 * .5 < measured < rate / 100 * 1.5, measurements
        QTest.keyClick(window, Qt.Key.Key_Space)
        assert not window.reverse_active
        wait_until(lambda: not window.seek_pending)
        paused = window.surface.ms
        QTest.qWait(120)
        assert window.surface.ms == paused
    window.rate_combo.setCurrentIndex(RATES.index(100))
    seek(7500)
    window.markers.add(8, 7000)
    window.toggle_reverse()
    wait_until(lambda: 8 in window.surface.flash_flags)
    window.pause_playback()
    wait_until(lambda: not window.seek_pending)
    QTest.keyClick(window, Qt.Key.Key_Space)
    assert window.reverse_active
    before = window.reverse_position()
    window.rate_combo.setCurrentIndex(RATES.index(200))
    assert abs(window.reverse_position() - before) < 100
    assert window.reverse_rate == 2
    QTest.mouseClick(window.play_button, Qt.MouseButton.LeftButton)
    assert not window.reverse_active and window.direction == 1
    assert window.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    for rate, delta in [(5, 5), (100, 100), (1000, 1000)]:
        window.rate_combo.setCurrentIndex(RATES.index(rate))
        seek(5000)
        start = window.surface.ms
        wheel(window.surface)
        QTest.qWait(50)
        assert window.seek_target == start + delta
        wait_until(lambda: not window.seek_pending)
        wheel(window.timeline, angle=-240)
        QTest.qWait(50)
        assert window.seek_target == start - delta
        wait_until(lambda: not window.seek_pending)
        assert window.player.playbackState() == QMediaPlayer.PlaybackState.PausedState
    window.rate_combo.setCurrentIndex(RATES.index(5))
    seek(5000)
    start = window.surface.ms
    for _ in range(24):
        wheel(window.table.viewport(), angle=5)
    QTest.qWait(80)
    assert window.seek_target == start + 5
    wait_until(lambda: not window.seek_pending)
    window.rate_combo.setCurrentIndex(RATES.index(100))
    wheel(window.surface, modifiers=Qt.KeyboardModifier.ControlModifier)
    assert RATES[window.rate_combo.currentIndex()] == 125
    wheel(window.timeline, angle=-120, modifiers=Qt.KeyboardModifier.ControlModifier)
    assert RATES[window.rate_combo.currentIndex()] == 100
    wheel(window.table.viewport(), modifiers=Qt.KeyboardModifier.ControlModifier)
    assert RATES[window.rate_combo.currentIndex()] == 125
    window.rate_combo.setCurrentIndex(RATES.index(100))
    seek(5000)
    start = window.surface.ms
    wheel(window.surface, angle=0, pixels=80)
    QTest.qWait(80)
    assert window.seek_target == start + 200
    wait_until(lambda: not window.seek_pending)

    # During either playback direction the wheel scrolls rows, never pauses/seeks.
    for i in range(70):
        window.markers.add(i % 10, 1000 + i * 200)
    window.refresh_markers()
    for reverse in (False, True):
        seek(10000)
        window.start_reverse() if reverse else window.toggle_forward()
        scroll = window.table.verticalScrollBar()
        scroll.setValue(0)
        previous_jog = window.jog_position
        wheel(window.surface, angle=-360)
        assert scroll.value() > 0
        assert window.jog_position == previous_jog
        assert window.reverse_active if reverse else window.player.isPlaying()
        wheel(window.table.viewport(), angle=-120)
        assert window.reverse_active if reverse else window.player.isPlaying()
    seek(20)
    window.start_reverse()
    wait_until(lambda: not window.reverse_active and not window.seek_pending)
    assert window.surface.ms <= 34
    wheel(window.surface, angle=-12000)
    QTest.qWait(100)
    assert window.seek_target == 0
    wheel(window.surface, angle=120000)
    QTest.qWait(100)
    assert window.seek_target == window.player.duration() - 1
    wait_until(lambda: not window.seek_pending)
    window.toggle_reverse()
    wait_until(lambda: window.surface.ms < window.player.duration() - 200)
    seek(6500)
    window.direction = 1
    window.change_language('en')
    window.resize(1000, 580)
    QTest.qWait(100)
    assert window.table.columnWidth(1) > 0
    buttons = {b.property('marker_flag'): b for b in window.findChildren(QToolButton)
               if b.property('marker_flag') is not None}
    assert buttons[0].y() == buttons[4].y() < buttons[5].y() == buttons[9].y()
    assert window.clock.geometry().right() < window.rate_combo.geometry().left()
    window.grab().save(str(output / 'transport-compact-en.png'))
    window.change_language('it')
    window.grab().save(str(output / 'transport-compact-it.png'))
    window.session_dirty = True
    window.save_session()
    (output / 'reverse-report.json').write_text(json.dumps(measurements, indent=2), encoding='utf-8')
    return ['reverse playback 5%/100%/1000%', 'reverse marker crossings and start boundary',
            'space resumes reverse; forward button changes direction', 'live reverse rate change',
            'Ctrl+wheel playback-speed changes over video, timeline and table',
            'paused wheel jog proportional to speed and delta', 'fractional and pixel wheel input',
            'wheel scrolls table during forward and reverse playback', 'jog clamps to video bounds',
            'compact sidebar and two-row tags']
