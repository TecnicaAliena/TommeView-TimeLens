"""Package only manifest-listed upstream source archives, never private app sources.

Local candidate artifacts only: packaging does not clear license/source gaps or
publish a release. Archive bytes are checked both before and after packaging.
"""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'release/compliance-sources'
REPORTS = ROOT / 'release/compliance-audit'
DEST = ROOT / 'release/source-distribution'
LIMIT = 512 * 1024 * 1024
GROUPS = {
    '': SOURCES / 'inventory.json',
    'deno-crates': REPORTS / 'deno-crates-inventory.json',
    'ffmpeg-crates': REPORTS / 'ffmpeg-crates-inventory.json',
    'ffmpeg-dependencies': REPORTS / 'ffmpeg-dependencies-inventory.json',
    'git-fallbacks': REPORTS / 'git-fallbacks.json',
    'deno-upstream': REPORTS / 'deno-upstream-inventory.json',
    'ffmpeg-upstream': REPORTS / 'ffmpeg-upstream-inventory.json',
    'submodules/archives': REPORTS / 'submodules-inventory.json',
    'shaderc-dependencies': REPORTS / 'shaderc-inventory.json',
    'ytdlp-dependencies': REPORTS / 'ytdlp-dependencies-inventory.json',
    'curl-native': REPORTS / 'curl-native-inventory.json',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def selected_sources():
    selected, unresolved = {}, []
    fallbacks = json.loads((REPORTS / 'git-fallbacks.json').read_text(encoding='utf-8'))
    fallback_keys = {(row['repository'].removesuffix('.git'), row['revision']) for row in fallbacks}
    for group, manifest in GROUPS.items():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        rows = data['repositories'] if isinstance(data, dict) else data
        for row in rows:
            filename = row.get('archive') or row.get('file')
            expected = row.get('checksum') or row.get('sha256')
            if not filename or not expected:
                repository = row.get('repository', '').removesuffix('.git')
                revision = row.get('revision', '')
                if (repository, revision) in fallback_keys:
                    continue
                # These source-superset entries are not selected for the release
                # build: tests/demos, disabled x265, or upstream notice supplements
                # whose exact published .crate source archive is already selected.
                status = row.get('status', '')
                nonselected = ('excluded test/demo source' in status or
                               ('x265' in repository and revision) or
                               (group == 'deno-upstream' and 'failed' in status))
                if not nonselected:
                    unresolved.append({'group': group, 'repository': repository, 'revision': revision, 'status': status})
                continue
            if Path(filename).name != filename or not filename.endswith(('.crate', '.tar.gz', '.tar.xz', '.tar.bz2', '.zip')):
                raise ValueError('Not an allowed source archive: ' + filename)
            path = SOURCES / group / filename
            if digest(path) != expected:
                raise ValueError('Source archive hash mismatch: ' + filename)
            name = '/'.join(part for part in (group, filename) if part)
            selected[name] = {'path': name, 'sha256': expected, 'bytes': path.stat().st_size,
                              'upstream': row.get('url') or row.get('repository', ''),
                              'revision': row.get('revision', '')}
    # Exact SVN revision archived separately; only its tarball, never the clone.
    lame = SOURCES / 'lame-r6761.tar.gz'
    selected[lame.name] = {'path': lame.name, 'sha256': digest(lame), 'bytes': lame.stat().st_size,
                          'upstream': 'https://svn.code.sf.net/p/lame/svn/!svn/rvr/6761/trunk/lame/', 'revision': '6761'}
    return list(sorted(selected.values(), key=lambda row: row['path'])), unresolved


def package():
    rows, unresolved = selected_sources()
    DEST.mkdir(parents=True, exist_ok=True)
    groups, current, size = [], [], 0
    for row in rows:
        if row['bytes'] > LIMIT:
            raise ValueError('Single source exceeds part limit: ' + row['path'])
        if current and size + row['bytes'] > LIMIT:
            groups.append(current)
            current, size = [], 0
        current.append(row)
        size += row['bytes']
    if current:
        groups.append(current)
    parts = []
    for number, group in enumerate(groups, 1):
        target = DEST / f'TommeView-dependency-sources-part-{number:03d}.zip'
        temporary = target.with_suffix('.zip.part')
        if temporary.exists():
            temporary.unlink()
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_STORED) as archive:
            archive.writestr('SOURCE-INDEX.json', json.dumps(group, indent=2))
            for row in group:
                archive.write(SOURCES / row['path'], row['path'])
        with zipfile.ZipFile(temporary) as archive:
            if set(archive.namelist()) != {'SOURCE-INDEX.json', *(r['path'] for r in group)}:
                raise ValueError('Unexpected packaged file')
            for row in group:
                with archive.open(row['path']) as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != row['sha256']:
                        raise ValueError('Packaged member hash mismatch')
        temporary.replace(target)
        parts.append({'file': target.name, 'bytes': target.stat().st_size,
                      'sha256': digest(target), 'source_archives': len(group)})
        print(target.name, len(group), 'source archives verified', flush=True)
    result = {'status': 'local candidate only; not redistribution clearance',
              'download_tools_manifest_sha256': digest(ROOT / 'download-tools.json'),
              'parts': parts, 'source_archives': len(rows),
              'unresolved_selected_source_entries': unresolved,
              'selection_notes': [
                  'Exact Git fallbacks replace failed HTTP downloads at the same repository revision.',
                  'The disabled x265 and test/demo-only source-superset entries are not selected.',
                  'Failed Deno upstream notice supplements do not replace the checksum-verified published crate sources included in the parts.'
              ]}
    (DEST / 'distribution-inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'{len(rows)} source archives in {len(parts)} parts; no private application source selected')


if __name__ == '__main__':
    package()
