"""Index declared incoming dependency edges for notice gaps, without resolving Cargo.

This records target/optional/dev conditions verbatim. It deliberately does not
claim that a package is linked or excluded from an actual release binary.
"""
import json
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'


def edges(metadata, wanted, source):
    output = []
    scopes = [('all targets', metadata)] + list(metadata.get('target', {}).items())
    for target, scope in scopes:
        for kind in ('dependencies', 'build-dependencies', 'dev-dependencies'):
            for alias, value in scope.get(kind, {}).items():
                detail = value if isinstance(value, dict) else {'version': value}
                name = detail.get('package', alias)
                if name in wanted:
                    output.append({'dependency': name, 'parent_manifest': source,
                                   'target_condition': target, 'kind': kind,
                                   'optional': detail.get('optional', False),
                                   'version_requirement': detail.get('version', 'workspace/path')})
    return output


def audit():
    gaps = json.loads((REPORTS / 'cargo-notice-gaps.json').read_text())
    results = []
    for profile in ('deno', 'ffmpeg'):
        crates = json.loads((REPORTS / f'{profile}-crates-inventory.json').read_text())
        gap_ids = {g['package'] for g in gaps if g['profile'] == profile}
        wanted = {c['name'] for c in crates if c['name'] + '-' + c['version'] in gap_ids}
        incoming = []
        for crate in crates:
            with tarfile.open(SOURCES / f'{profile}-crates' / crate['archive'], 'r|*') as archive:
                for member in archive:
                    if member.isfile() and member.name == crate['name'] + '-' + crate['version'] + '/Cargo.toml':
                        incoming.extend(edges(tomllib.loads(archive.extractfile(member).read().decode()), wanted, member.name))
                        break
        results.append({'profile': profile, 'edges': incoming,
                        'no_incoming_crate_edge': sorted(wanted - {e['dependency'] for e in incoming}),
                        'scope': 'registry crate declarations only; root workspace, feature resolution and actual linker inputs not covered'})
    (REPORTS / 'crate-target-evidence.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    for row in results:
        print(row['profile'], len(row['edges']), 'declared edges')
        for edge in row['edges']:
            if edge['dependency'].startswith(('winapi-', 'testing_macros', 'objc', 'block', 'malloc')):
                print(edge['dependency'], edge['kind'], edge['target_condition'], edge['parent_manifest'])


if __name__ == '__main__':
    audit()
