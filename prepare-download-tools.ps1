$ErrorActionPreference = 'Stop'
$target = Join-Path $PSScriptRoot 'tools\download'
$cache = Join-Path $PSScriptRoot 'tools\download-cache'
New-Item -ItemType Directory -Force -Path $target, $cache | Out-Null
$manifest = Get-Content (Join-Path $PSScriptRoot 'download-tools.json') -Raw | ConvertFrom-Json
foreach ($name in @('yt-dlp', 'deno', 'ffmpeg')) {
    $entry = $manifest.$name
    $archive = Join-Path $cache ([IO.Path]::GetFileName($entry.url))
    if (-not (Test-Path $archive)) {
        $partial = $archive + '.partial'
        Invoke-WebRequest $entry.url -OutFile $partial -TimeoutSec 180
        if ((Get-FileHash $partial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
            throw "SHA256 mismatch: $partial. No downloaded code has been executed."
        }
        Move-Item -LiteralPath $partial -Destination $archive
    }
    if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
        throw "SHA256 mismatch: $archive. No downloaded code has been executed."
    }
    if ($name -eq 'yt-dlp') { Copy-Item $archive (Join-Path $target 'yt-dlp.exe') -Force }
    elseif ($name -eq 'ffmpeg') {
        # Extract only runtime files and notices, not ffplay, headers or HTML manuals.
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $ffmpegTarget = Join-Path $target 'ffmpeg-shared'
        New-Item -ItemType Directory -Force -Path $ffmpegTarget | Out-Null
        $zip = [IO.Compression.ZipFile]::OpenRead($archive)
        try {
            foreach ($item in $zip.Entries) {
                if ($item.FullName -match '/bin/(ffmpeg\.exe|ffprobe\.exe|[^/]+\.dll)$' -or
                    $item.FullName -match '/(LICENSE[^/]*|COPYING[^/]*|NOTICE[^/]*)$') {
                    $destination = Join-Path $ffmpegTarget $item.Name
                    [IO.Compression.ZipFileExtensions]::ExtractToFile($item, $destination, $true)
                }
            }
        } finally { $zip.Dispose() }
    }
    else { Expand-Archive -LiteralPath $archive -DestinationPath (Join-Path $target $name) -Force }
}
# Keep upstream license notices with the redistributable tools.
Invoke-WebRequest 'https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/LICENSE' -OutFile (Join-Path $target 'yt-dlp-LICENSE.txt')
Invoke-WebRequest 'https://raw.githubusercontent.com/yt-dlp/yt-dlp/2026.08.19/THIRD_PARTY_LICENSES.txt' -OutFile (Join-Path $target 'yt-dlp-THIRD_PARTY_LICENSES.txt')
Invoke-WebRequest 'https://raw.githubusercontent.com/denoland/deno/v2.9.6/LICENSE.md' -OutFile (Join-Path $target 'deno-LICENSE.md')
Copy-Item (Join-Path $PSScriptRoot 'download-tools.json') $target -Force
Write-Output "Verified download tools ready: $target"
