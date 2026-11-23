"""Resolve simple literal DEPS mappings without executing Python from upstream."""
import ast
import concurrent.futures
import json
import tarfile
from pathlib import Path
import collect_ffmpeg_dependency_sources as collector

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
collector.DEST = ROOT / 'release/compliance-sources/shaderc-dependencies'


def resolve(node, variables):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return resolve(node.left, variables) + resolve(node.right, variables)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'Var' and len(node.args) == 1:
        return variables[ast.literal_eval(node.args[0])]
    raise ValueError('Unsupported DEPS expression')


if __name__ == '__main__':
    collector.DEST.mkdir(parents=True, exist_ok=True)
    source = next((ROOT / 'release/compliance-sources/ffmpeg-dependencies').glob('google_shaderc-*.tar.gz'))
    with tarfile.open(source) as archive:
        member = next(m for m in archive if m.name.endswith('/DEPS'))
        tree = ast.parse(archive.extractfile(member).read().decode())
    assignments = {n.targets[0].id: n.value for n in tree.body if isinstance(n, ast.Assign)}
    variables = ast.literal_eval(assignments['vars'])
    pins = []
    for key, value in zip(assignments['deps'].keys, assignments['deps'].values):
        path = ast.literal_eval(key)
        repo, revision = resolve(value, variables).rsplit('@', 1)
        pins.append((repo, revision))
    rows, blocks = [], ['SHADERC PINNED DEPENDENCY NOTICES\nIncludes upstream DEPS test/build entries.\n']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result, notices in pool.map(collector.collect, pins):
            rows.append(result)
            blocks.append(f'\n{result["repository"]} {result["revision"]}\n')
            blocks.extend(f'\n{path}\n{text}\n' for path, text in notices)
            print(result['repository'], result['status'], flush=True)
    (REPORTS / 'shaderc-inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    (REPORTS / 'Shaderc-SOURCE-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
