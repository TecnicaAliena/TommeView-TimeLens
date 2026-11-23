"""Fetch exact source refs where no HTTP archive endpoint was available."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'release/compliance-sources/git-fallbacks'
REPORT = ROOT / 'release/compliance-audit/git-fallbacks.json'


if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    rows = json.loads((ROOT / 'release/compliance-audit/ffmpeg-dependencies-inventory.json').read_text())
    rows += [r for r in json.loads((ROOT / 'release/compliance-audit/submodules-inventory.json').read_text())
             if r['status'] == 'failed']
    output = []
    for row in rows:
        if row['status'].startswith('downloaded') or 'x265' in row['repository']:
            continue
        record = {k: row[k] for k in ('repository', 'revision', 'file')}
        repo = DEST / (row['revision'] + '.git')
        try:
            if not repo.exists():
                subprocess.run(['git', 'init', '--bare', str(repo)], check=True, capture_output=True)
            result = subprocess.run(['git', '-C', str(repo), 'fetch', '--depth=1',
                                     row['repository'], row['revision']], timeout=120,
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stderr[-1500:])
            target = DEST / row['file']
            subprocess.run(['git', '-C', str(repo), 'archive', '--format=tar.gz',
                            '--prefix=source/', f'--output={target}', 'FETCH_HEAD'],
                           timeout=120, check=True, capture_output=True)
            with target.open('rb') as source:
                record.update(sha256=hashlib.file_digest(source, 'sha256').hexdigest(),
                              bytes=target.stat().st_size, status='exact Git revision archived')
        except Exception as error:
            record.update(status='failed', error=str(error))
        output.append(record)
        REPORT.write_text(json.dumps(output, indent=2), encoding='utf-8')
        print(row['repository'], record['status'], record.get('error', ''), flush=True)
