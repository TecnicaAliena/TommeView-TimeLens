"""Fill crate notice gaps from each crate's recorded source-control revision."""
import concurrent.futures
import argparse
import json
from pathlib import Path
import collect_ffmpeg_dependency_sources as collector

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'
collector.DEST = ROOT / 'release/compliance-sources/deno-upstream'

# Candidate repositories identified from the crate README or sibling project.
# The crate's own VCS revision is still used, never a moving default branch.
REPOSITORY_HINTS = {
    'aead-gcm-stream': ('https://github.com/littledivy/aead-stream', 'crate README image links to this repository'),
    'dlopen2_derive': ('https://github.com/OpenByteDev/dlopen2', 'derive crate for the locked dlopen2 package'),
    'rsqlite-vfs': ('https://github.com/Spxg/sqlite-wasm-rs', 'crate README identifies sqlite-wasm-rs; verified upstream project'),
    'zune-core': ('https://github.com/etemesi254/zune-image', 'crate README describes the shared zune family; locked zune-jpeg repository'),
}
VERSION_REVISIONS = {
    ('valuable', '0.1.0'): ('e89de8805f524aefafdbcc1fcd1b20ecfd0d22b6', 'valuable',
                          'GitHub tokio-rs/valuable git/ref/tags/v0.1.0 resolved to this commit'),
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('deno', 'ffmpeg'), default='deno')
    profile = parser.parse_args().profile
    title = 'Deno' if profile == 'deno' else 'FFmpeg'
    collector.DEST = ROOT / f'release/compliance-sources/{profile}-upstream'
    collector.DEST.mkdir(parents=True, exist_ok=True)
    crates = json.loads((REPORTS / f'{profile}-crates-inventory.json').read_text())
    repositories_by_revision = {}
    for package in crates:
        revision = package.get('vcs', {}).get('git', {}).get('sha1', '')
        repository = package.get('repository', '')
        if revision and repository.startswith('https://github.com/'):
            canonical = '/'.join(repository.split('/')[:5]).removesuffix('.git')
            repositories_by_revision.setdefault(revision, set()).add(canonical)
    wanted, unresolved = {}, []
    inferred = []
    for crate in crates:
        if crate.get('notice_paths') and crate['name'] != 'v8':
            continue
        repo = crate.get('repository', '')
        sha = crate.get('vcs', {}).get('git', {}).get('sha1', '')
        version_key = (crate['name'], crate['version'])
        if not sha and version_key in VERSION_REVISIONS:
            sha, manifest_folder, evidence = VERSION_REVISIONS[version_key]
            inferred.append({'package': crate['name'], 'version': crate['version'],
                             'repository': repo, 'revision': sha, 'evidence': evidence,
                             'manifest_folder': manifest_folder})
        candidates = repositories_by_revision.get(sha, set())
        if not repo and len(candidates) == 1:
            repo = next(iter(candidates))
            inferred.append({'package': crate['name'], 'version': crate['version'],
                             'repository': repo, 'revision': sha,
                             'evidence': 'another locked crate records the identical Git commit and this repository'})
        if not repo and sha and crate['name'] in REPOSITORY_HINTS:
            repo, evidence = REPOSITORY_HINTS[crate['name']]
            inferred.append({'package': crate['name'], 'version': crate['version'],
                             'repository': repo, 'revision': sha, 'evidence': evidence})
        if repo.startswith('https://github.com/') and sha:
            wanted.setdefault((repo, sha), []).append(crate['name'] + '-' + crate['version'])
        else:
            unresolved.append({'package': crate['name'], 'version': crate['version'], 'repository': repo, 'sha': sha})
    rows, blocks = [], [title + ' UPSTREAM SOURCE NOTICE SUPPLEMENT\nSource-superset; package-to-repository mapping in the companion inventory.\n']
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result, notices in pool.map(collector.collect, wanted):
            result['packages'] = wanted[(result['repository'], result['revision'])]
            rows.append(result)
            print(result['repository'], result['status'], result.get('error', ''), flush=True)
            blocks.append(f'\n{"=" * 72}\n{result["repository"]}\nRevision: {result["revision"]}\nPackages: {", ".join(result["packages"])}\n')
            blocks.extend(f'\n{path}\n{text}\n' for path, text in notices)
    (REPORTS / f'{profile}-upstream-inventory.json').write_text(json.dumps({'repositories': rows, 'unresolved': unresolved, 'inferred_from_same_revision': inferred}, indent=2), encoding='utf-8')
    (REPORTS / f'{title}-UPSTREAM-SOURCE-NOTICES.txt').write_text(''.join(blocks), encoding='utf-8')
    print(f'{len(rows)} upstream repositories; {len(unresolved)} unresolved mappings', flush=True)
