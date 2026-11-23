param([string]$Compiler = (Join-Path $PSScriptRoot 'tools\inno\ISCC.exe'), [switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $SkipBuild) { & (Join-Path $PSScriptRoot 'build.ps1') }
if (-not (Test-Path -LiteralPath $Compiler)) { throw 'Compilatore Inno Setup non trovato. Specificare -Compiler con il percorso di ISCC.exe.' }
& $Compiler (Join-Path $PSScriptRoot 'installer\TommeView.iss')
if ($LASTEXITCODE -ne 0) { throw 'Creazione installer fallita' }
Get-Item (Join-Path $PSScriptRoot 'release\TommeViewSetup.exe') | Select-Object FullName, Length
