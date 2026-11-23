"""Preserve published MIT and CC0 declarations where a crate lacks a notice file.

The Cargo package checksum, package manifest and original leading source headers
are retained. This is notice assembly, not proof of the release's linked graph.
"""
import hashlib
import json
import tarfile
from pathlib import Path

from assemble_declared_apache_notices import leading_notice

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'
TEXTS = {
    'MIT': ('MIT.txt', 'c3b1b78bc8bd3ea13aa4bc9778442d16560270afa235006d816e5e88cef24db4'),
    'CC0-1.0': ('CC0-1.0.txt', 'a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499'),
}


def validate_texts():
    for identifier, (name, expected) in TEXTS.items():
        actual = hashlib.sha256((ROOT / 'licenses' / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Official {identifier} license text changed')


def assemble():
    validate_texts()
    gaps = json.loads((REPORTS / 'remaining-notice-review.json').read_text())
    inventories = {profile: json.loads((REPORTS / f'{profile}-crates-inventory.json').read_text())
                   for profile in ('deno', 'ffmpeg')}
    decisions, remaining = [], []
    blocks = ['MIT AND CC0 DECLARATIONS AND COPYRIGHT NOTICES\n'
              'Source-package superset, not an actual binary component list.\n'
              'Full license texts: MIT.txt and CC0-1.0.txt.\n']
    for gap in gaps:
        identifier = gap['declared_license']
        if identifier not in TEXTS:
            remaining.append(gap)
            continue
        crate = next(item for item in inventories[gap['profile']]
                     if item['name'] + '-' + item['version'] == gap['package'])
        source = SOURCES / f'{gap["profile"]}-crates' / crate['archive']
        with source.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != crate['checksum']:
                raise ValueError('Crate checksum mismatch: ' + crate['archive'])
        headers, notices = [], []
        with tarfile.open(source, 'r|*') as archive:
            for member in archive:
                if not member.isfile():
                    continue
                base = Path(member.name).name.lower()
                if base == 'notice' or base.startswith('notice.'):
                    notices.append(member.name)
                if member.size <= 1024 * 1024 and Path(member.name).suffix.lower() in {'.rs', '.c', '.h', '.cpp'}:
                    text = archive.extractfile(member).read().decode('utf-8', errors='strict')
                    if header := leading_notice(text):
                        headers.append({'source_path': member.name, 'text': header})
        if notices:
            raise ValueError('Standalone NOTICE must be included by the notice collector')
        decisions.append({**gap, 'selected_license': identifier, 'source_url': crate['url'],
                          'source_sha256': crate['checksum'], 'original_authors': crate.get('authors', []),
                          'source_headers': headers, 'standalone_NOTICE_in_published_crate': False,
                          'license_text_sha256': TEXTS[identifier][1],
                          'basis': 'published Cargo package SPDX license declaration; original authors and headers retained'})
        blocks.append(f'\n=== {gap["profile"]}/{gap["package"]} ===\nSource: {crate["url"]}\n'
                      f'Upstream declaration and selected license: {identifier}\n'
                      f'Authors as published: {json.dumps(crate.get("authors", []), ensure_ascii=False)}\n')
        for header in headers:
            blocks.append(f'\n{header["source_path"]}\n{header["text"]}\n')
    (REPORTS / 'declared-permissive-decisions.json').write_text(json.dumps(decisions, indent=2), encoding='utf-8')
    (REPORTS / 'MIT-CC0-DECLARED-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
    (REPORTS / 'remaining-notice-review.json').write_text(json.dumps(remaining, indent=2), encoding='utf-8')
    print(f'{len(decisions)} MIT/CC0 declarations supplemented; {len(remaining)} entries remain')


if __name__ == '__main__':
    assemble()
