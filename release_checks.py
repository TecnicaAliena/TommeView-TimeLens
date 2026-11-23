from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox

from localization import Translator
from model import Markers


def run_release_checks(window, output, wait_until):
    app = QApplication.instance()
    window.player.pause()
    window.markers = Markers()
    for flag, ms in [(1, 1000), (2, 2000), (1, 3000), (1, 6500)]:
        window.markers.add(flag, ms)
    window.session_dirty = True
    window.save_session()
    window.refresh_markers()
    assert window.table.item(3, 4).text() == '5.500'
    assert not window.rotate_cw.icon().isNull() and not window.rotate_ccw.icon().isNull()
    QTest.mouseClick(window.rotate_cw, Qt.MouseButton.LeftButton)
    assert window.surface.rotation == 90
    assert window.store.load(window.video_path).rotation == 90
    video = window.video_path
    window.open_video(video)
    wait_until(lambda: not window.surface.image.isNull())
    window.player.pause()
    assert window.surface.rotation == 90
    window.grab().save(str(output / 'rotation-it.png'))
    QTest.mouseClick(window.rotate_ccw, Qt.MouseButton.LeftButton)
    assert window.surface.rotation == 0
    QTest.mouseClick(window.rotate_ccw, Qt.MouseButton.LeftButton)
    assert window.surface.rotation == 270
    window.change_language('en')
    assert window.table.horizontalHeaderItem(4).text().replace('\n', ' ') == 'Cumulative (s)'
    assert 'counterclockwise' in window.rotate_ccw.toolTip()
    assert Translator(window.translator.preferences).language == 'en'
    window.grab().save(str(output / 'rotation-en.png'))

    def answer(accept, screenshot=None):
        dialog = app.activeModalWidget()
        if screenshot:
            dialog.grab().save(str(output / screenshot))
        assert dialog.defaultButton().text() == 'Cancel'
        role = QMessageBox.ButtonRole.DestructiveRole if accept else QMessageBox.ButtonRole.RejectRole
        next(b for b in dialog.buttons() if dialog.buttonRole(b) == role).click()

    before = window.store.path(video).read_bytes()
    QTimer.singleShot(100, lambda: answer(False))
    window.clear_markers()
    assert window.store.path(video).read_bytes() == before
    QTimer.singleShot(100, lambda: answer(True, 'clear-confirm-en.png'))
    window.clear_markers()
    assert not window.markers.items and not window.store.load(video).items
    assert window.store.load(video).rotation == 270
    other = output / 'other.mov'
    window.store.save(other, Markers(rotation=180))
    QTimer.singleShot(100, lambda: answer(False))
    window.reset_database()
    assert window.store.path(other).exists()
    QTimer.singleShot(100, lambda: answer(True, 'reset-confirm-en.png'))
    window.reset_database()
    assert not list(window.store.folder.glob('*.json'))
    assert window.surface.rotation == 0
    window.save_session()
    assert not list(window.store.folder.glob('*.json'))
    assert Translator(window.translator.preferences).language == 'en'
    window.change_language('it')

    # Pixel checks prove the rotation transforms the picture, not the overlays.
    old_image = window.surface.image
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(QColor('red'))
    painter = QPainter(image)
    painter.fillRect(200, 0, 200, 200, QColor('blue'))
    painter.end()
    window.surface.image = image
    window.surface.native_rotation = 0
    window.surface.rotation = 90
    shot = window.surface.grab().toImage()
    x, y = shot.width() // 2, shot.height() // 2
    assert shot.pixelColor(x, y - 30).red() > 200
    assert shot.pixelColor(x, y + 30).blue() > 200
    window.surface.rotation = 270
    shot = window.surface.grab().toImage()
    assert shot.pixelColor(x, y - 30).blue() > 200
    assert shot.pixelColor(x, y + 30).red() > 200
    window.surface.rotation = 0
    window.surface.image = old_image
    return ['rotation buttons and persistence', 'rotation pixel orientation', 'cumulative intervals',
            'live English and Italian translation', 'language persistence', 'clear markers confirmation and persistence',
            'global reset confirmation and no session resurrection']
