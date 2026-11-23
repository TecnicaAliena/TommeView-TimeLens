"""Rehash collected source archives; this is integrity evidence, not legal clearance."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'


def verify():
    output = []
    for group in ('deno-crates', 'ffmpeg-crates', 'ffmpeg-dependencies', 'git-fallbacks'):
        manifest = 'git-fallbacks.json' if group == 'git-fallbacks' else group + '-inventory.json'
        rows = json.loads((REPORTS / manifest).read_text(encoding='utf-8'))
        checked, failures, uncollected = 0, [], []
        for row in rows:
            expected = row.get('checksum') or row.get('sha256')
            name = row.get('archive') or row.get('file')
            if not expected or not name:
                uncollected.append(row.get('repository', row.get('name')))
                continue
            path = (SOURCES / group / name).resolve()
            if not path.is_relative_to((SOURCES / group).resolve()):
                raise ValueError(f'Archive outside group: {name}')
            try:
                with path.open('rb') as source:
                    actual = hashlib.file_digest(source, 'sha256').hexdigest()
                if actual != expected:
                    raise ValueError('SHA256 mismatch')
                checked += 1
            except (OSError, ValueError) as exc:
                failures.append({'file': name, 'error': str(exc)})
        output.append({'group': group, 'verified_archives': checked,
                       'integrity_failures': failures, 'uncollected_in_original_manifest': uncollected})
    (REPORTS / 'local-integrity-verification.json').write_text(
        json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))
    return not any(group['integrity_failures'] for group in output)


if __name__ == '__main__':
    raise SystemExit(0 if verify() else 1)
