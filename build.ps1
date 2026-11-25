$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$bundlePath = Join-Path $PSScriptRoot 'dist\TommeView'
$portableData = Join-Path $bundlePath 'data'
$dataBackup = $null
if (Test-Path -LiteralPath $portableData) {
    $dataBackup = Join-Path $PSScriptRoot ('.build-data-backups\' + [guid]::NewGuid().ToString())
    New-Item -ItemType Directory -Path $dataBackup -Force | Out-Null
    Copy-Item -LiteralPath $portableData -Destination $dataBackup -Recurse
}
$buildPython = Join-Path $PSScriptRoot '.venv-build\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $buildPython)) {
    $buildPython = (Get-Command python -CommandType Application | Select-Object -First 1).Source
}
$originalBuildPath = $env:PATH
try {
    # Do not collect unrelated ICU/OpenSSL/CRT DLLs from desktop tool runtimes.
    $pythonBase = & $buildPython -c "import sys; print(sys.base_prefix)"
    $env:PATH = "$pythonBase;$pythonBase\Scripts;$env:SystemRoot\System32;$env:SystemRoot"
    & $buildPython -m PyInstaller --clean --noconfirm TommeView.spec
} finally {
    $env:PATH = $originalBuildPath
}
if ($LASTEXITCODE -ne 0) { throw 'Build non riuscita' }
if ($dataBackup) {
    Copy-Item -LiteralPath (Join-Path $dataBackup 'data') -Destination $bundlePath -Recurse -Force
}
$italianGuide = 'README.md'
$englishGuide = 'README.en.md'
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'manual.en.md')) {
    $italianGuide = 'manuale.it.md'
    $englishGuide = 'manual.en.md'
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot $italianGuide) -Destination (Join-Path $bundlePath 'README.md') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot $englishGuide) -Destination (Join-Path $bundlePath 'README.en.md') -Force
$bundleDocs = Join-Path $bundlePath 'docs'
New-Item -ItemType Directory -Path $bundleDocs -Force | Out-Null
foreach ($docName in @('youtube-acquisition.md', 'distribution.md')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "docs\$docName") -Destination $bundleDocs -Force
}
$iphoneGuide = Join-Path $PSScriptRoot 'docs\iphone-video.md'
if (Test-Path -LiteralPath $iphoneGuide) {
    Copy-Item -LiteralPath $iphoneGuide -Destination $bundleDocs -Force
}
foreach ($noticeName in @('LICENSE', 'NOTICE', 'TRADEMARKS.md', 'CONTRIBUTING.md', 'BUILDING.md', 'SOURCE_RELEASE.md', 'LIBRARY_REPLACEMENT.md', 'THIRD_PARTY_LICENSES.md', 'SOURCE_REFERENCES.md', 'SOURCE_DELIVERY.md', 'dependency-source-inventory.json', 'ffmpeg-build-config.txt', 'licenses')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $noticeName) -Destination $bundlePath -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'download-tools.json') -Destination $bundlePath -Force
Write-Output "Pronto: $bundlePath\TommeView.exe"
