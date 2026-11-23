@echo off
cd /d "%~dp0"
if exist "dist\TommeView\TommeView.exe" (
    start "" "dist\TommeView\TommeView.exe" %*
) else (
    python player.py %*
)
