"""Resolve and collect source submodules at exact gitlink revisions.

No checkout or execution. Explicit test/demo submodules are recorded as excluded.
"""
import configparser
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import urljoin, urlparse
import collect_ffmpeg_dependency_sources as collector

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
BASE = ROOT / 'release/compliance-sources/submodules'
collector.DEST = BASE / 'archives'


def gitlinks(repo, revision):
    parsed = urlparse(repo)
    if parsed.hostname == 'github.com':
        project = '/'.join(parsed.path.strip('/').split('/')[:2]).removesuffix('.git')
        result = subprocess.run(['gh', 'api', f'repos/{project}/git/trees/{revision}?recursive=1'],
                                check=True, capture_output=True, text=True, timeout=90)
        data = json.loads(result.stdout)
        if data.get('truncated'):
            raise RuntimeError('GitHub tree truncated')
        return {r['path']: r['sha'] for r in data['tree'] if r['mode'] == '160000'}
    cache = BASE / 'trees' / hashlib.sha256(repo.encode()).hexdigest()[:16]
    if not cache.exists():
        subprocess.run(['git', 'init', '--bare', str(cache)], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(cache), 'fetch', '--filter=blob:none', '--depth=1',
                    repo, revision], check=True, capture_output=True, timeout=180)
    result = subprocess.run(['git', '-C', str(cache), 'ls-tree', '-r', 'FETCH_HEAD'],
                            check=True, capture_output=True, text=True)
    return {line.split('\t', 1)[1]: line.split()[2] for line in result.stdout.splitlines()
            if line.startswith('160000 ')}


if __name__ == '__main__':
    collector.DEST.mkdir(parents=True, exist_ok=True)
    ff = json.loads((REPORTS / 'ffmpeg-dependencies-inventory.json').read_text())
    deno = json.loads((REPORTS / 'deno-upstream-inventory.json').read_text())['repositories']
    queue = [r for r in ff if r.get('submodules') and 'AviSynth' not in r['repository']]
    queue += [r for r in deno if r['repository'].endswith('rusty_v8')]
    seen, rows, blocks = set(), [], ['PINNED SUBMODULE SOURCE NOTICES\n']
    while queue:
        parent = queue.pop(0)
        identity = (parent['repository'], parent['revision'])
        if identity in seen:
            continue
        seen.add(identity)
        try:
            links = gitlinks(*identity)
            parser = configparser.RawConfigParser()
            for config in parent.get('submodules', []):
                parser.read_string(config['text'])
            for section in parser.sections():
                path = parser.get(section, 'path')
                repo = parser.get(section, 'url')
                if repo.startswith('.'):
                    repo = urljoin(parent['repository'] + '/', repo)
                if path not in links:
                    continue
                record = {'parent': parent['repository'], 'parent_revision': parent['revision'], 'path': path}
                if any(part in path.lower().split('/') for part in ('test', 'testdata', 'tests', 'demos', 'googletest', 'benchmark', 'greatest')):
                    rows.append({**record, 'repository': repo, 'revision': links[path], 'status': 'excluded test/demo source; not required for selected library build'})
                    continue
                if not repo.startswith('https://'):
                    rows.append({**record, 'repository': repo, 'revision': links[path], 'status': 'unsupported repository scheme'})
                    continue
                result, notices = collector.collect((repo, links[path]))
                rows.append({**record, **result})
                blocks.append(f'\n{"=" * 72}\n{repo}\nRevision: {links[path]}\n')
                blocks.extend(f'\n{name}\n{text}\n' for name, text in notices)
                if result.get('submodules'):
                    queue.append(result)
                print(repo, result['status'], result.get('error', ''), flush=True)
        except Exception as error:
            rows.append({'parent': identity[0], 'revision': identity[1], 'status': 'resolution failed', 'error': str(error)})
            print(identity[0], 'resolution failed', str(error), flush=True)
        (REPORTS / 'submodules-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
        (REPORTS / 'Submodules-SOURCE-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
