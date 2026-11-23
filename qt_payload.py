"""Reviewed Qt runtime modules; fail closed when collection changes."""
from pathlib import PurePosixPath

EXCLUDED_QT_FILES = {
    'qt6virtualkeyboard.dll', 'qtvirtualkeyboardplugin.dll',
    'qt6pdf.dll', 'qpdf.dll',
}
ALLOWED_QT_MODULES = {
    'qt6core.dll', 'qt6gui.dll', 'qt6multimedia.dll',
    'qt6multimediawidgets.dll', 'qt6network.dll', 'qt6opengl.dll',
    'qt6qml.dll', 'qt6qmlmeta.dll', 'qt6qmlmodels.dll',
    'qt6qmlworkerscript.dll', 'qt6quick.dll', 'qt6svg.dll',
    'qt6test.dll', 'qt6widgets.dll',
}


def reviewed_qt_entries(entries):
    """Remove unused keyboard/PDF plugins, reject unreviewed Qt DLLs."""
    result = []
    for entry in entries:
        name = PurePosixPath(entry[0].replace('\\', '/')).name.lower()
        if name in EXCLUDED_QT_FILES:
            continue
        if name.startswith('qt6') and name.endswith('.dll'):
            if name not in ALLOWED_QT_MODULES:
                raise RuntimeError(f'Unreviewed Qt module: {entry[0]}')
        result.append(entry)
    return result
