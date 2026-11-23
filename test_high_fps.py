"""Synthetic 240 FPS MOV benchmark; not a substitute for testing an iPhone HEVC original."""
import json
import os
import time
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import cv2
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from player import PlayerWindow
from model import RATES
from smoke_test import wait_until


def main():
    output = Path(__file__).parent / 'test-output'
    output.mkdir(exist_ok=True)
    clip = output / 'synthetic-240fps.mov'
    writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*'mp4v'), 240, (960, 540))
    assert writer.isOpened()
    for index in range(720):
        frame = np.full((540, 960, 3), (34, 26, 19), dtype=np.uint8)
        cv2.rectangle(frame, (index % 850, 170), (index % 850 + 90, 290), (90, 220, 150), -1)
        writer.write(frame)
    writer.release()
    app = QApplication([])
    window = PlayerWindow(output / 'high-fps-sessions')
    window.show()
    window.open_video(clip)
    deadline = time.monotonic() + 5
    while window.surface.image.isNull() and time.monotonic() < deadline:
        QTest.qWait(20)
    start = window.surface.ms
    received = window.received_frames
    converted = window.presented_frames
    QTest.qWait(1600)
    advanced = window.surface.ms - start
    received = window.received_frames - received
    converted = window.presented_frames - converted
    window.player.pause()
    report = {'source_fps': 240, 'source_codec': 'MPEG-4 Part 2', 'media_advanced_ms': advanced,
              'frames_received': received, 'images_converted': converted,
              'iphone_hevc_original_tested': False}
    assert advanced > 1100, report
    assert received > converted * 2, report
    assert converted <= 105, report
    reverse = {}
    for rate in (5, 100, 1000):
        window.pause_playback()
        window.rate_combo.setCurrentIndex(RATES.index(rate))
        window.seek(2700)
        wait_until(lambda: not window.seek_pending)
        start = window.surface.ms
        window.start_reverse()
        wall = time.monotonic()
        previous = start
        for _ in range(10 if rate == 1000 else 40):
            QTest.qWait(20)
            assert window.surface.ms <= previous
            previous = window.surface.ms
        measured = (start - window.surface.ms) / ((time.monotonic() - wall) * 1000)
        reverse[str(rate)] = round(measured, 3)
        assert rate / 100 * .45 < measured < rate / 100 * 1.55, reverse
        window.pause_playback()
        wait_until(lambda: not window.seek_pending)
    report['reverse_measured_rates'] = reverse
    report['result'] = 'PASS'
    (output / 'high-fps-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    window.close()


if __name__ == '__main__':
    main()
