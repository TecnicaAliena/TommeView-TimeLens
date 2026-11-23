"""Collect registry sources required by the pinned FFmpeg dependency lockfiles."""
import json
import tomllib
from pathlib import Path
import collect_rust_notices as collector

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'


if __name__ == '__main__':
    rows = json.loads((REPORTS / 'ffmpeg-dependencies-inventory.json').read_text())
    packages = {}
    for row in rows:
        for lock in row.get('cargo_lockfiles', []):
            for package in tomllib.loads(lock['text'])['package']:
                packages[(package['name'], package['version'], package.get('source', ''))] = package
    records = list(packages.values())
    (REPORTS / 'ffmpeg-cargo-lock.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(f'{len(records)} unique Rust lock entries; git sources: {[p for p in records if p.get("source", "").startswith("git+")]}', flush=True)
    collector.DEST = ROOT / 'release/compliance-sources/ffmpeg-crates'
    raise SystemExit(collector.collect_packages(records, title='FFmpeg', stem='ffmpeg'))
