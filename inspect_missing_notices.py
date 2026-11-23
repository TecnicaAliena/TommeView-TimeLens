"""Collect read-only evidence for unresolved notice entries; never mark them cleared."""
import hashlib
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'


def inspect():
    gaps = json.loads((REPORTS / 'cargo-notice-gaps.json').read_text())
    inventories = {profile: json.loads((REPORTS / f'{profile}-crates-inventory.json').read_text())
                   for profile in ('deno', 'ffmpeg')}
    evidence = []
    for gap in gaps:
        crate = next(c for c in inventories[gap['profile']] if c['name'] + '-' + c['version'] == gap['package'])
        path = SOURCES / (gap['profile'] + '-crates') / crate['archive']
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != crate['checksum']:
                raise ValueError('Source checksum mismatch: ' + path.name)
        documents, declarations = [], []
        with tarfile.open(path, 'r|*') as archive:
            for member in archive:
                if not member.isfile() or member.size > 1024 * 1024:
                    continue
                suffix = Path(member.name).suffix.lower()
                base = Path(member.name).name.lower()
                if suffix not in ('.rs', '.md', '.txt', '.toml', '.c', '.h', ''):
                    continue
                raw = archive.extractfile(member).read()
                try:
                    text = raw.decode('utf-8')
                except UnicodeDecodeError:
                    continue
                if base.startswith(('readme', 'authors', 'copyright', 'license', 'copying', 'notice')):
                    documents.append({'path': member.name, 'text': text})
                lines = text.splitlines()
                hits = [{'line': i + 1, 'text': line} for i, line in enumerate(lines)
                        if re.search(r'(?i)copyright|permission is hereby|licensed under|license\s*=|SPDX-License-Identifier|public domain', line)]
                if hits:
                    declarations.append({'path': member.name, 'hits': hits})
        evidence.append({**gap, 'authors': crate.get('authors', []), 'repository': crate.get('repository', ''),
                         'source_url': crate['url'], 'source_sha256': crate['checksum'],
                         'documents': documents, 'declarations': declarations,
                         'status': 'review evidence only; not notice clearance'})
    (REPORTS / 'missing-notice-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    for row in evidence:
        print(f'{row["profile"]}/{row["package"]}: {len(row["documents"])} documents, '
              f'{sum(len(d["hits"]) for d in row["declarations"])} declaration lines')


if __name__ == '__main__':
    inspect()
