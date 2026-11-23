"""Compare original crate manifests with inferred repository revisions, offline."""
import hashlib
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
SOURCES = ROOT / 'release/compliance-sources'


def member_bytes(path, suffix):
    with tarfile.open(path, 'r|*') as archive:
        for member in archive:
            if member.isfile() and member.name.split('/', 1)[-1] == suffix:
                return archive.extractfile(member).read()
    raise ValueError(f'Missing manifest {suffix} in {path.name}')


def verify():
    report = json.loads((REPORTS / 'deno-upstream-inventory.json').read_text())
    crates = json.loads((REPORTS / 'deno-crates-inventory.json').read_text())
    results = []
    for mapping in report['inferred_from_same_revision']:
        crate = next(c for c in crates if c['name'] == mapping['package'] and c['version'] == mapping['version'])
        repo = next(r for r in report['repositories'] if r['repository'] == mapping['repository'] and r['revision'] == mapping['revision'])
        row = dict(mapping)
        try:
            original = member_bytes(SOURCES / 'deno-crates' / crate['archive'], 'Cargo.toml.orig')
            relative = mapping.get('manifest_folder', crate.get('vcs', {}).get('path_in_vcs', '')).strip('/')
            target = (relative + '/' if relative else '') + 'Cargo.toml'
            upstream = member_bytes(SOURCES / 'deno-upstream' / repo['file'], target)
            row.update(crate_manifest_sha256=hashlib.sha256(original).hexdigest(),
                       upstream_manifest_sha256=hashlib.sha256(upstream).hexdigest(),
                       upstream_path=target, exact_match=original == upstream,
                       line_ending_only_difference=original != upstream and original.replace(b'\r\n', b'\n') == upstream.replace(b'\r\n', b'\n'))
        except (OSError, ValueError) as error:
            row.update(exact_match=False, error=str(error))
        results.append(row)
    (REPORTS / 'crate-repository-mapping-verification.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    for row in results:
        status = 'exact original manifest match' if row['exact_match'] else (
            'manifest matches except CRLF/LF' if row.get('line_ending_only_difference') else 'REVIEW REQUIRED')
        print(row['package'], status)
    return all(r['exact_match'] or r.get('line_ending_only_difference') for r in results)


if __name__ == '__main__':
    raise SystemExit(0 if verify() else 1)
