import pytest
from qt_payload import reviewed_qt_entries, EXCLUDED_QT_FILES


def test_exclude_unused_modules_and_plugins():
    entries = [(f'PySide6/plugins/{name}', '/source', 'BINARY')
               for name in EXCLUDED_QT_FILES]
    keep = ('PySide6\\Qt6Multimedia.dll', '/source', 'BINARY')
    assert reviewed_qt_entries(entries + [keep]) == [keep]


def test_fail_on_unreviewed_module():
    with pytest.raises(RuntimeError, match='Unreviewed Qt module'):
        reviewed_qt_entries([('PySide6/Qt6Graphs.dll', '/source', 'BINARY')])


def test_preserve_external_tools():
    entries = [('tools/download/ffmpeg-shared/avcodec-62.dll', '/source', 'DATA')]
    assert reviewed_qt_entries(entries) == entries
