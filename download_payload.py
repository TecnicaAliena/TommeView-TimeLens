"""Explicit redistributable allowlist: never package the whole vendor archive."""
from pathlib import Path


def payload_files(root):
    root = Path(root)
    required = ['yt-dlp.exe', 'deno/deno.exe', 'ffmpeg-shared/ffmpeg.exe',
                'ffmpeg-shared/ffprobe.exe', 'download-tools.json',
                'yt-dlp-LICENSE.txt', 'yt-dlp-THIRD_PARTY_LICENSES.txt', 'deno-LICENSE.md',
                'ffmpeg-shared/LICENSE.txt']
    files = [root / name for name in required]
    for path in files:
        if not path.is_file():
            raise RuntimeError('Run prepare-download-tools.ps1: missing ' + str(path))
    libraries = sorted((root / 'ffmpeg-shared').glob('*.dll'))
    if not libraries:
        raise RuntimeError('Missing shared FFmpeg DLLs')
    files.extend(libraries)
    return files
