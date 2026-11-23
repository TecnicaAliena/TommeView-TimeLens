"""Check the clean public source tree before it is committed or pushed."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


FORBIDDEN_PARTS = {
    '.git', '.venv', '.venv-build', '__pycache__', '.pytest_cache', 'build',
    'dist', 'release', 'test-output', 'tools', 'data', 'sessions',
    'public-repository', '.build-data-backups',
}
FORBIDDEN_NAMES = {
    'AGENTS.md', 'public-launch-plan.md', 'APPLICATION_LICENSE.txt',
}
FORBIDDEN_SUFFIXES = {'.key', '.pem', '.pfx', '.p12'}
REQUIRED = {
    'LICENSE', 'NOTICE', 'TRADEMARKS.md', 'BUILDING.md', 'CONTRIBUTING.md',
    'SOURCE_RELEASE.md', 'player.py', 'model.py', 'acquisition.py',
    'acquisition_ui.py', 'TommeView.spec', 'installer/TommeView.iss',
    'requirements.txt', 'THIRD_PARTY_LICENSES.md', 'SOURCE_REFERENCES.md',
}


def tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ['git', '-C', str(root), 'ls-files'], check=True,
        capture_output=True, text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def check(root: Path) -> None:
    files = tracked_files(root)
    names = {path.as_posix() for path in files}
    missing = REQUIRED - names
    assert not missing, f'Missing required public source files: {sorted(missing)}'
    for path in files:
        assert not (set(path.parts) & FORBIDDEN_PARTS), path
        assert path.name not in FORBIDDEN_NAMES, path
        assert path.suffix.lower() not in FORBIDDEN_SUFFIXES, path
    print(f'PASS: {len(files)} tracked public source files; forbidden paths absent')


if __name__ == '__main__':
    check(Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve())
