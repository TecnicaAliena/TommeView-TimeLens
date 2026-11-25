# Building TommeView from source

## Requirements

- Windows 10/11 x64
- Python 3.11
- PowerShell
- Inno Setup 6 for the optional installer

Create an isolated build environment, install the Python dependencies and fetch
the pinned acquisition tools:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requirements.txt pytest pyinstaller Pillow
powershell -ExecutionPolicy Bypass -File prepare-download-tools.ps1
```

Run TommeView from source with:

```powershell
.\.venv-build\Scripts\python.exe player.py --demo
```

Run the focused checks and source smoke test:

```powershell
.\.venv-build\Scripts\python.exe -m pytest test_model.py test_acquisition.py test_localization.py test_download_payload.py test_qt_payload.py test_ytdlp_update.py -q
.\.venv-build\Scripts\python.exe smoke_test.py
```

Build the executable and installer:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
powershell -ExecutionPolicy Bypass -File build-installer.ps1 -SkipBuild -Compiler 'C:\path\to\ISCC.exe'
```

The build writes to ignored `dist/`, `build/` and `release/` directories. Read
[distribution notes](docs/distribution.md) before redistributing a build: GPL
applies to TommeView's original source, while bundled third-party components
retain their own licenses and notice/source obligations.
