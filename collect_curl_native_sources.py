"""Collect hash-pinned native curl dependencies from the upstream CMake recipe."""
import concurrent.futures
import hashlib
import json
import re
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources/curl-native'


def download(item):
    name, url, expected = item
    path = DEST / url.rsplit('/', 1)[1]
    result = {'name': name, 'url': url, 'file': path.name, 'sha256': expected}
    try:
        if not path.exists():
            with urllib.request.urlopen(url, timeout=90) as source:
                data = source.read()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('Upstream CMake checksum mismatch')
            path.write_bytes(data)
        with path.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
                raise ValueError('Cached checksum mismatch')
        result.update(status='upstream CMake checksum verified', bytes=path.stat().st_size)
    except Exception as error:
        result.update(status='failed', error=str(error))
    return result


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    with tarfile.open(ROOT / 'release/compliance-sources/curl-impersonate-2.0.0.tar.gz') as archive:
        text = archive.extractfile('curl-impersonate-2.0.0/CMakeLists.txt').read().decode()
    values = dict(re.findall(r'set\(([A-Z0-9_]+) "([^"\n]*)"\)', text))
    wanted = []
    for name in ('ZLIB', 'ZSTD', 'BROTLI', 'BORINGSSL', 'NGHTTP2', 'NGTCP2', 'NGHTTP3', 'CURL'):
        url = re.sub(r'\$\{([A-Z0-9_]+)\}', lambda m: values[m[1]], values[name + '_URL'])
        expected = values[name + '_URL_HASH'].removeprefix('SHA256=')
        wanted.append((name, url, expected))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(download, wanted))
    (ROOT / 'release/compliance-audit/curl-native-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    for row in rows:
        print(row['name'], row['status'], row.get('error', ''), flush=True)
