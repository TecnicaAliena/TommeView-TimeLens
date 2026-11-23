"""Resolve the Windows yt-dlp release requirements to exact PyPI source archives."""
import concurrent.futures
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path
from packaging.requirements import Requirement
from packaging.markers import default_environment

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources/ytdlp-dependencies'
REPORT = ROOT / 'release/compliance-audit/ytdlp-dependencies-inventory.json'


def collect(pair):
    name, version = pair
    result = {'name': name, 'version': version}
    try:
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=60) as response:
            metadata = json.load(response)
        source = next(f for f in metadata['urls'] if f['packagetype'] == 'sdist')
        target = DEST / source['filename']
        if not target.exists():
            with urllib.request.urlopen(source['url'], timeout=90) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != source['digests']['sha256']:
                raise ValueError('PyPI source checksum mismatch')
            target.write_bytes(data)
        with target.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        if digest != source['digests']['sha256']:
            raise ValueError('Cached source checksum mismatch')
        result.update(file=target.name, url=source['url'], sha256=digest,
                      license=metadata['info'].get('license'),
                      project_urls=metadata['info'].get('project_urls'),
                      status='downloaded; PyPI source checksum verified')
    except Exception as error:
        result.update(status='failed', error=str(error))
    return result


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    environment = {**default_environment(), 'sys_platform': 'win32', 'os_name': 'nt',
                   'platform_system': 'Windows', 'platform_machine': 'AMD64',
                   'python_version': '3.10', 'python_full_version': '3.10.11',
                   'implementation_name': 'cpython', 'platform_python_implementation': 'CPython'}
    wanted = set()
    archive = ROOT / 'release/compliance-sources/yt-dlp-3a08beaf031ab68f966401ead017ac81fe8486cf.tar.gz'
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.endswith(('bundle/requirements/curl-cffi.txt', 'bundle/requirements/win-x64-pyinstaller.txt')):
                continue
            for line in tar.extractfile(member).read().decode().splitlines():
                if not line or not line[0].isalpha():
                    continue
                requirement = Requirement(line.rstrip(' \\'))
                if requirement.marker and not requirement.marker.evaluate(environment):
                    continue
                if requirement.url:
                    continue  # Custom PyInstaller build needs separate recipe review.
                version = next(s.version for s in requirement.specifier if s.operator == '==')
                wanted.add((requirement.name, version))
    # Own application bootloader and upstream base of yt-dlp's custom bootloader.
    wanted.update({('pyinstaller', '6.22.2'), ('pyinstaller', '6.22.0')})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(collect, sorted(wanted)))
    REPORT.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    for row in rows:
        print(row['name'], row['version'], row['status'], row.get('error', ''), flush=True)
