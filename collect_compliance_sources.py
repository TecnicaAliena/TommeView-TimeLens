"""Download pinned upstream archives for review; never execute upstream code.

This collects source evidence, not a declaration of complete compliance.
Generated archives and inventory remain in ignored release/compliance-sources.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources'
QT = 'https://download.qt.io/official_releases/qt/6.10/6.10.2/submodules/'
SOURCES = {
    'llvm-3.6.2.src.tar.xz': 'https://releases.llvm.org/3.6.2/llvm-3.6.2.src.tar.xz',
    'mesa-11.2.2.tar.xz': 'https://archive.mesa3d.org/older-versions/11.x/11.2.2/mesa-11.2.2.tar.xz',
    'Pyinstaller-Builds-5eb86b862d61adc3df0f44e6e0b815b7d74fa3f5.tar.gz': 'https://codeload.github.com/yt-dlp/Pyinstaller-Builds/tar.gz/5eb86b862d61adc3df0f44e6e0b815b7d74fa3f5',
    'Python-3.10.11.tar.xz': 'https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tar.xz',
    'Python-3.11.9.tar.xz': 'https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tar.xz',
    'curl-impersonate-2.0.0.tar.gz': 'https://codeload.github.com/lexiforest/curl-impersonate/tar.gz/v2.0.0',
    'pyinstaller-70fc17210920bce17f4ab09bbf8104b0dbd45338.tar.gz': 'https://codeload.github.com/pyinstaller/pyinstaller/tar.gz/70fc17210920bce17f4ab09bbf8104b0dbd45338',
    'deno_src-2.9.6.tar.gz': 'https://github.com/denoland/deno/releases/download/v2.9.6/deno_src.tar.gz',
    **{f'{m}-everywhere-src-6.10.2.tar.xz': QT + f'{m}-everywhere-src-6.10.2.tar.xz'
       for m in ('qtbase', 'qtdeclarative', 'qtmultimedia', 'qtsvg', 'qtimageformats', 'qttranslations', 'qtshadertools')},
    'pyside-setup-everywhere-src-6.10.2.tar.xz': 'https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.10.2-src/pyside-setup-everywhere-src-6.10.2.tar.xz',
    'FFmpeg-7ba069f4f11d126f52a740156dbab6476a8a865a.tar.gz': 'https://codeload.github.com/FFmpeg/FFmpeg/tar.gz/7ba069f4f11d126f52a740156dbab6476a8a865a',
    'FFmpeg-Builds-847e5e1cacc2945ac46528d34d754bd36051680c.tar.gz': 'https://codeload.github.com/BtbN/FFmpeg-Builds/tar.gz/847e5e1cacc2945ac46528d34d754bd36051680c',
    'ffmpeg-7.1.2.tar.xz': 'https://ffmpeg.org/releases/ffmpeg-7.1.2.tar.xz',
    'yt-dlp-3a08beaf031ab68f966401ead017ac81fe8486cf.tar.gz': 'https://codeload.github.com/yt-dlp/yt-dlp/tar.gz/3a08beaf031ab68f966401ead017ac81fe8486cf',
    'deno-e518fbd66dda5debcbdefc0beb0b3756b37b64fa.tar.gz': 'https://codeload.github.com/denoland/deno/tar.gz/e518fbd66dda5debcbdefc0beb0b3756b37b64fa',
}


def collect(item):
    name, url = item
    target = DEST / name
    try:
        if not target.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'TommeView-source-audit/1.0'})
            temporary = target.with_suffix(target.suffix + '.part')
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open('wb') as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            temporary.replace(target)
        with target.open('rb') as input_file:
            digest = hashlib.file_digest(input_file, 'sha256').hexdigest()
        print(f'Collected {name}: {target.stat().st_size}', flush=True)
        return {'file': name, 'url': url, 'bytes': target.stat().st_size,
                'sha256': digest, 'status': 'downloaded; correspondence/dependency closure not certified'}
    except Exception as error:
        print(f'FAILED {name}: {error}', flush=True)
        return {'file': name, 'url': url, 'error': str(error), 'status': 'failed'}


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(collect, SOURCES.items()))
    (DEST / 'inventory.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(any(r['status'] == 'failed' for r in records))
