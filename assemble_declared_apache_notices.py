"""Preserve published Apache declarations and original source copyright headers.

This supplements standalone notice collection. It is not a binary dependency
audit or blanket clearance of redistribution obligations.
"""
import hashlib
import json
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'
APACHE_SHA256 = 'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30'


def leading_notice(text):
    if text.startswith('/*') and '*/' in text:
        header = text[:text.index('*/') + 2]
    else:
        lines = []
        for line in text.splitlines(keepends=True):
            if line.startswith('//') or not line.strip():
                lines.append(line)
            else:
                break
        header = ''.join(lines)
    return header if re.search(r'(?i)copyright|licensed under|SPDX-License-Identifier', header) else ''


def assemble():
    license_text = ROOT / 'licenses/Apache-2.0.txt'
    if hashlib.sha256(license_text.read_bytes()).hexdigest() != APACHE_SHA256:
        raise ValueError('Official Apache license text changed')
    gaps = json.loads((REPORTS / 'cargo-notice-gaps.json').read_text())
    inventories = {p: json.loads((REPORTS / f'{p}-crates-inventory.json').read_text()) for p in ('deno', 'ffmpeg')}
    decisions, remaining, blocks = [], [], ['APACHE-2.0 DECLARATIONS AND COPYRIGHT NOTICES\n'
                                          'Source-package superset, not an actual binary component list.\n'
                                          'Full license: Apache-2.0.txt\n']
    for gap in gaps:
        if gap['declared_license'] not in ('Apache-2.0', 'MIT OR Apache-2.0', 'MIT/Apache-2.0'):
            remaining.append(gap)
            continue
        crate = next(c for c in inventories[gap['profile']] if c['name'] + '-' + c['version'] == gap['package'])
        path = SOURCES / (gap['profile'] + '-crates') / crate['archive']
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != crate['checksum']:
                raise ValueError('Crate checksum mismatch')
        headers, notice_files = [], []
        with tarfile.open(path, 'r|*') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                base = Path(member.name).name.lower()
                if base == 'notice' or base.startswith('notice.'):
                    notice_files.append(member.name)
                if member.size <= 1024 * 1024 and Path(member.name).suffix in ('.rs', '.c', '.h', '.cpp'):
                    text = archive.extractfile(member).read().decode('utf-8', errors='strict')
                    header = leading_notice(text)
                    if header:
                        headers.append({'source_path': member.name, 'text': header})
        if notice_files:
            raise ValueError('Standalone NOTICE must be included by the notice collector')
        if gap['declared_license'] == 'MIT/Apache-2.0' and not any('at your option' in h['text'] and 'Apache' in h['text'] for h in headers):
            raise ValueError('Legacy slash expression lacks explicit source option')
        decision = {**gap, 'selected_license': 'Apache-2.0', 'source_url': crate['url'],
                    'source_sha256': crate['checksum'], 'original_authors': crate.get('authors', []),
                    'source_headers': headers, 'standalone_NOTICE_in_published_crate': False,
                    'license_text_sha256': APACHE_SHA256,
                    'basis': 'published Cargo package license declaration; explicit choice for OR; original headers retained'}
        decisions.append(decision)
        blocks.append(f'\n=== {gap["profile"]}/{gap["package"]} ===\nSource: {crate["url"]}\n'
                      f'Upstream declaration: {gap["declared_license"]}\nSelected: Apache-2.0\n'
                      f'Authors as published: {json.dumps(crate.get("authors", []), ensure_ascii=False)}\n')
        for header in headers:
            blocks.append(f'\n{header["source_path"]}\n{header["text"]}\n')
    (REPORTS / 'declared-apache-decisions.json').write_text(json.dumps(decisions, indent=2), encoding='utf-8')
    (REPORTS / 'Apache-DECLARED-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
    (REPORTS / 'remaining-notice-review.json').write_text(json.dumps(remaining, indent=2), encoding='utf-8')
    print(f'{len(decisions)} Apache declarations supplemented; {len(remaining)} other entries remain for review')


if __name__ == '__main__':
    assemble()
