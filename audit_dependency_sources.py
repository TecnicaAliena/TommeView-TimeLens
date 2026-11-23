"""Generate traceable source inventories without executing downloaded code."""
import hashlib
import json
import posixpath
import re
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'release/compliance-sources'
REPORTS = ROOT / 'release/compliance-audit'


def qt_notices():
    records, missing, notices = [], [], []
    for archive in sorted(SOURCES.glob('qt*-everywhere-src-6.10.2.tar.xz')):
        archive_rows = []
        with tarfile.open(archive, 'r|*') as tar:
            for member in tar:
                name = member.name
                if not member.isfile() or not name.endswith('/qt_attribution.json'):
                    continue
                # Some upstream attribution strings contain literal newlines.
                payload = json.loads(tar.extractfile(member).read(), strict=False)
                for item in payload if isinstance(payload, list) else [payload]:
                    archive_rows.append({**item, 'archive': archive.name, 'attribution_path': name})
        wanted = set()
        for item in archive_rows:
            refs = item.get('LicenseFile', [])
            if isinstance(refs, str):
                refs = [refs]
            item['resolved_license_paths'] = [posixpath.normpath(posixpath.join(
                posixpath.dirname(item['attribution_path']), ref)) for ref in refs]
            wanted.update(item['resolved_license_paths'])
        texts = {}
        with tarfile.open(archive, 'r|*') as tar:
            for member in tar:
                if member.isfile() and member.name in wanted:
                    texts[member.name] = tar.extractfile(member).read().decode('utf-8', errors='replace')
        for item in archive_rows:
            header = '\n'.join(f'{key}: {item.get(key, "")}' for key in
                               ('Name', 'Version', 'Copyright', 'License', 'QtUsage', 'QtParts'))
            notices.append(f'\n{"=" * 72}\n{header}\nSource: {archive.name}/{item["attribution_path"]}\n')
            for path in item['resolved_license_paths']:
                if path in texts:
                    notices.append(f'\nLicense file: {path}\n{texts[path]}\n')
                else:
                    missing.append({'attribution': item['attribution_path'], 'license_file': path})
        records.extend(archive_rows)
        print(f'Read {archive.name}: {len(archive_rows)} attributions', flush=True)
    (REPORTS / 'qt-source-attributions.json').write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding='utf-8')
    (REPORTS / 'qt-license-files-missing.json').write_text(json.dumps(missing, indent=2), encoding='utf-8')
    (REPORTS / 'Qt-SOURCE-NOTICES.txt').write_text(
        'SOURCE-SUPERSET NOTICES: includes tools, tests and non-Windows code; not a claim all are shipped.\n'
        + ''.join(notices), encoding='utf-8')
    print(f'Qt: {len(records)} source attributions, {len(missing)} unresolved license-file references')


def ffmpeg_recipes():
    archive = next(SOURCES.glob('FFmpeg-Builds-*.tar.gz'))
    config = (ROOT / 'ffmpeg-build-config.txt').read_text(encoding='utf-8')
    rows = []
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if not member.isfile() or '/scripts.d/' not in member.name or not member.name.endswith('.sh'):
                continue
            text = tar.extractfile(member).read().decode('utf-8')
            fields = dict(re.findall(r'^SCRIPT_(\w+)=[\"\']([^\"\']+)[\"\']', text, re.M))
            flags = re.findall(r'echo (--enable-[\w-]+)', text)
            rows.append({'recipe': member.name.split('/', 1)[1], 'pins': fields,
                         'enabled_flags_in_binary': [f for f in flags if f in config],
                         'recipe_sha256': hashlib.sha256(text.encode()).hexdigest(),
                         'review': 'Recipe identified; dependency closure and binary correspondence not certified'})
    (REPORTS / 'ffmpeg-recipes.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print(f'FFmpeg: {len(rows)} recipes, {sum(bool(r["enabled_flags_in_binary"]) for r in rows)} directly enabled')


def deno_dependencies():
    archive = SOURCES / 'deno_src-2.9.6.tar.gz'
    with tarfile.open(archive) as tar:
        members = [m for m in tar.getmembers() if m.isfile()]
        locks = [m for m in members if m.name.endswith('/Cargo.lock') or m.name == 'Cargo.lock']
        lock = min(locks, key=lambda m: len(m.name))
        data = tomllib.loads(tar.extractfile(lock).read().decode())
        rows = [{k: p[k] for k in ('name', 'version', 'source', 'checksum') if k in p}
                for p in data['package']]
    (REPORTS / 'deno-cargo-lock.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print(f'Deno: {len(rows)} Cargo lock entries (all targets/features, not binary SBOM)')


if __name__ == '__main__':
    REPORTS.mkdir(parents=True, exist_ok=True)
    qt_notices()
    ffmpeg_recipes()
    deno_dependencies()
