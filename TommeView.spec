# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
from pathlib import Path
from PySide6.QtCore import QLibraryInfo
import PySide6
from download_payload import payload_files
from qt_payload import reviewed_qt_entries

# Python's older VC runtime must not shadow the runtime required by Qt.
qt_package = Path(PySide6.__file__).parent
vc_runtime = [(str(qt_package / name), '.') for name in
              ('VCRUNTIME140.dll', 'VCRUNTIME140_1.dll')]

metadata = []
for package in ('PySide6', 'PySide6_Addons', 'PySide6_Essentials', 'shiboken6'):
    metadata += copy_metadata(package)

download_root = Path('tools/download')
download_data = [(str(Path('tools/download') / path.relative_to(download_root)),
                  str(path.resolve()), 'DATA') for path in payload_files(download_root)]


a = Analysis(
    ['player.py'],
    pathex=[],
    binaries=vc_runtime,
    datas=metadata + [('locales.json', '.'), ('assets/icons', 'assets/icons'),
                     ('assets/tommeview.ico', 'assets'),
                     (str(Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)) / 'qtbase_it.qm'), 'translations')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'cv2', 'pytest'],
    noarchive=False,
    optimize=0,
)
# Qt Virtual Keyboard is GPL-only in the open-source distribution. Neither
# that plugin nor PDF image decoding is used by this video player.
a.binaries = reviewed_qt_entries(a.binaries)
a.datas = reviewed_qt_entries(a.datas)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TommeView',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    version='version_info.txt',
    icon='assets/tommeview.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    download_data,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TommeView',
)
