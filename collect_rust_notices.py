"""Collect checksum-pinned Cargo sources/notices from Deno's release lockfile.

All lockfile registry entries are collected (source superset, not runtime SBOM).
Nothing downloaded is executed. Existing archives must pass the lockfile hash.
"""
import concurrent.futures
import hashlib
import json
import re
import tarfile
import tomllib
import urllib.request
from pathlib import Path
from notice_files import is_notice_file

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources/deno-crates'
REPORTS = ROOT / 'release/compliance-audit'


def collect(package):
    name, version = package['name'], package['version']
    filename = f'{name}-{version}.crate'
    url = f'https://static.crates.io/crates/{name}/{filename}'
    path = DEST / filename
    result = {**package, 'archive': filename, 'url': url}
    try:
        if not path.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'TommeView-license-audit/1.0'})
            with urllib.request.urlopen(request, timeout=60) as source:
                data = source.read()
            if hashlib.sha256(data).hexdigest() != package['checksum']:
                raise ValueError('Cargo checksum mismatch')
            path.write_bytes(data)
        with path.open('rb') as source:
            if hashlib.file_digest(source, 'sha256').hexdigest() != package['checksum']:
                raise ValueError('Cached archive checksum mismatch')
        notices = []
        with tarfile.open(path, 'r|*') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                base = Path(member.name).name
                if member.name == f'{name}-{version}/Cargo.toml':
                    meta = tomllib.loads(archive.extractfile(member).read().decode())['package']
                    result['license'] = meta.get('license', '')
                    result['license_file'] = meta.get('license-file', '')
                    result['repository'] = meta.get('repository', '')
                    result['authors'] = meta.get('authors', [])
                elif base == '.cargo_vcs_info.json':
                    result['vcs'] = json.loads(archive.extractfile(member).read())
                elif is_notice_file(member.name):
                    raw = archive.extractfile(member).read()
                    notices.append((member.name, raw.decode('utf-8', errors='replace')))
        result['notice_paths'] = [p for p, _ in notices]
        result['status'] = 'downloaded and Cargo checksum verified'
        result['bytes'] = path.stat().st_size
        return result, notices
    except Exception as error:
        result.update(status='failed', error=str(error))
        return result, []


def collect_packages(packages, title='DENO', stem='deno'):
    DEST.mkdir(parents=True, exist_ok=True)
    packages = [p for p in packages if p.get('source', '').startswith('registry+')]
    rows, blocks = [], [title + ' CARGO SOURCE-SUPERSET NOTICES\nAll lockfile registry packages, including non-Windows/build/test dependencies. Not a runtime SBOM.\n']
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for index, (result, notices) in enumerate(pool.map(collect, packages), 1):
            rows.append(result)
            blocks.append(f'\n{"=" * 72}\n{result["name"]} {result["version"]}\nLicense: {result.get("license", "unresolved")}\nSource: {result["url"]}\n')
            blocks.extend(f'\n{path}\n{text}\n' for path, text in notices)
            if result['status'] == 'failed' or index % 50 == 0:
                print(f'{index}/{len(packages)} {result["name"]}: {result["status"]} {result.get("error", "")}', flush=True)
    (REPORTS / f'{stem}-crates-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    (REPORTS / f'{title}-CARGO-SOURCE-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
    failures = [r for r in rows if r['status'] == 'failed']
    print(f'Finished: {len(rows)} packages, {len(failures)} failures', flush=True)
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(collect_packages(json.loads((REPORTS / 'deno-cargo-lock.json').read_text()), title='Deno'))
