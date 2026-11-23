"""Assemble exact, deduplicated Cargo notices and explicit gaps, without network access.

The input is a source superset including tests and non-Windows targets. An empty
gap list would not alone prove actual runtime coverage or redistribution clearance.
"""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'


def read_notices(path, expected, wanted):
    with path.open('rb') as source:
        if hashlib.file_digest(source, 'sha256').hexdigest() != expected:
            raise ValueError(f'Source hash mismatch: {path.name}')
    result = {}
    with tarfile.open(path, 'r|*') as archive:
        for member in archive:
            if member.isfile() and member.name in wanted:
                result[member.name] = archive.extractfile(member).read()
    if set(result) != set(wanted):
        raise ValueError(f'Listed notice missing in {path.name}')
    return result


def assemble():
    texts, packages, gaps = {}, [], []
    for profile in ('deno', 'ffmpeg'):
        crates = json.loads((REPORTS / f'{profile}-crates-inventory.json').read_text())
        upstream = json.loads((REPORTS / f'{profile}-upstream-inventory.json').read_text())
        if profile == 'deno':
            verified = json.loads((REPORTS / 'crate-repository-mapping-verification.json').read_text())
            approved = {(r['package'], r['version'], r['repository'], r['revision']) for r in verified
                        if r.get('exact_match') or r.get('line_ending_only_difference')}
            for mapping in upstream.get('inferred_from_same_revision', []):
                key = tuple(mapping[k] for k in ('package', 'version', 'repository', 'revision'))
                if key not in approved:
                    raise ValueError(f'Unverified inferred repository mapping: {key}')
        supplements = {}
        for repo in upstream['repositories']:
            if not repo.get('sha256') or not repo.get('notice_paths'):
                continue
            notices = read_notices(SOURCES / f'{profile}-upstream' / repo['file'],
                                   repo['sha256'], repo['notice_paths'])
            for package in repo['packages']:
                supplements[package] = (repo, notices)
        for crate in crates:
            identity = crate['name'] + '-' + crate['version']
            notices = read_notices(SOURCES / f'{profile}-crates' / crate['archive'],
                                   crate['checksum'], crate.get('notice_paths', []))
            sources = [(crate['url'], name, raw) for name, raw in notices.items()]
            if identity in supplements:
                repo, extra = supplements[identity]
                sources.extend((repo['url'], name, raw) for name, raw in extra.items())
            refs = []
            for url, name, raw in sources:
                # Deduplicate only byte-identical texts: no copyright removal,
                # whitespace normalization or replacement with generic licenses.
                digest = hashlib.sha256(raw).hexdigest()
                texts[digest] = raw
                refs.append({'sha256': digest, 'source_url': url, 'source_path': name})
            entry = {'profile': profile, 'package': identity,
                     'declared_license': crate.get('license', ''), 'notices': refs}
            packages.append(entry)
            if not refs:
                gaps.append({'profile': profile, 'package': identity,
                             'declared_license': crate.get('license', ''),
                             'reason': 'No standalone notice in collected crate or resolved upstream supplement'})
    lines = ['CARGO DEPENDENCY SOURCE-SUPERSET NOTICES\n'
             'Includes build, test and non-Windows packages; not a runtime SBOM.\n'
             'Package and source attribution index: cargo-notice-index.json\n'
             'Each exact notice text appears once, identified by its SHA256.\n']
    for digest, raw in sorted(texts.items()):
        lines.extend([f'\n=== SHA256 {digest} ===\n', raw.decode('utf-8', errors='strict'), '\n'])
    (REPORTS / 'Cargo-DEDUPLICATED-NOTICES.txt').write_text(''.join(lines), encoding='utf-8')
    (REPORTS / 'cargo-notice-index.json').write_text(json.dumps(packages, indent=2), encoding='utf-8')
    (REPORTS / 'cargo-notice-gaps.json').write_text(json.dumps(gaps, indent=2), encoding='utf-8')
    print(f'{len(packages)} package entries; {len(texts)} byte-distinct notices; {len(gaps)} gaps')
    print(f'Notice text size: {(REPORTS / "Cargo-DEDUPLICATED-NOTICES.txt").stat().st_size} bytes')


if __name__ == '__main__':
    assemble()
