"""Collect pinned FFmpeg recipe sources for review, without running recipes.

Conservative recipe superset: contains disabled/platform-specific/build packages.
Archives may omit git submodules: report them, never call this full closure.
"""
import concurrent.futures
import hashlib
import json
import re
import tarfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from notice_files import is_notice_file

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources/ffmpeg-dependencies'
REPORTS = ROOT / 'release/compliance-audit'


def archive_url(repo, commit):
    parsed = urlparse(repo)
    path = parsed.path.removesuffix('.git').strip('/')
    if parsed.hostname == 'github.com':
        path = '/'.join(path.split('/')[:2]).removesuffix('.git')
        return f'https://codeload.github.com/{path}/tar.gz/{commit}'
    if parsed.hostname in ('gitlab.com', 'gitlab.freedesktop.org', 'code.videolan.org'):
        return f'https://{parsed.hostname}/{path}/-/archive/{commit}/{path.split("/")[-1]}-{commit}.tar.gz'
    if parsed.hostname and parsed.hostname.endswith('.googlesource.com'):
        return f'https://{parsed.hostname}/{path}/+archive/{commit}.tar.gz'
    if parsed.hostname == 'git.savannah.gnu.org':
        project = path.split('/')[-1]
        return f'https://git.savannah.gnu.org/cgit/{project}.git/snapshot/{project}-{commit}.tar.gz'
    return None


def collect(item):
    repo, commit = item
    url = archive_url(repo, commit)
    filename = re.sub(r'[^\w.-]', '_', urlparse(repo).path.removesuffix('.git').strip('/')) + '-' + commit + '.tar.gz'
    result = {'repository': repo, 'revision': commit, 'url': url, 'file': filename}
    if url is None:
        return {**result, 'status': 'manual-source-retrieval-required'}, []
    try:
        path = DEST / filename
        if not path.exists():
            request = urllib.request.Request(url, headers={'User-Agent': 'TommeView-source-audit/1.0'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if not data.startswith(b'\x1f\x8b'):
                raise ValueError('Response is not a gzip archive')
            path.write_bytes(data)
        with path.open('rb') as source:
            result['sha256'] = hashlib.file_digest(source, 'sha256').hexdigest()
        notices, submodules, lockfiles = [], [], []
        with tarfile.open(path, 'r|*') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                base = Path(member.name).name
                if base == '.gitmodules':
                    submodules.append({'path': member.name, 'text': archive.extractfile(member).read().decode('utf-8', errors='replace')})
                elif base == 'Cargo.lock':
                    lockfiles.append({'path': member.name, 'text': archive.extractfile(member).read().decode('utf-8', errors='replace')})
                elif is_notice_file(member.name):
                    notices.append((member.name, archive.extractfile(member).read().decode('utf-8', errors='replace')))
        result.update(status='downloaded; submodules/transitive closure not certified',
                      bytes=path.stat().st_size, submodules=submodules, cargo_lockfiles=lockfiles,
                      notice_paths=[p for p, _ in notices])
        return result, notices
    except Exception as error:
        return {**result, 'status': 'failed', 'error': str(error)}, []


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    recipes = json.loads((REPORTS / 'ffmpeg-recipes.json').read_text())
    pins = set()
    for recipe in recipes:
        fields = recipe['pins']
        for key, repo in fields.items():
            if key.startswith('REPO'):
                revision = fields.get('COMMIT' + key[4:])
                if revision and re.fullmatch(r'[\w.-]+', revision):
                    pins.add((repo, revision))
    rows, blocks = [], ['FFMPEG RECIPE SOURCE-SUPERSET NOTICES\nIncludes disabled/non-Windows/build packages. Not a runtime SBOM.\n']
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for index, (result, notices) in enumerate(pool.map(collect, sorted(pins)), 1):
            rows.append(result)
            print(f'{index}/{len(pins)} {result["repository"]}: {result["status"]} {result.get("error", "")}', flush=True)
            blocks.append(f'\n{"=" * 72}\n{result["repository"]}\nRevision: {result["revision"]}\n')
            blocks.extend(f'\n{path}\n{text}\n' for path, text in notices)
    (REPORTS / 'ffmpeg-dependencies-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    (REPORTS / 'FFmpeg-RECIPE-SOURCE-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
    print(f'Finished: {len(rows)} pinned repositories; manual/SVN and nested dependencies require review')
