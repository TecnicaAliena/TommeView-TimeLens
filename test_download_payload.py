from pathlib import Path
import pytest
from download_payload import payload_files
from acquisition import find_tools


def prepare(root):
    for name in ['yt-dlp.exe', 'deno/deno.exe', 'ffmpeg-shared/ffmpeg.exe',
                 'ffmpeg-shared/ffprobe.exe', 'ffmpeg-shared/avcodec-62.dll',
                 'ffmpeg-shared/LICENSE.txt', 'download-tools.json',
                 'yt-dlp-LICENSE.txt', 'yt-dlp-THIRD_PARTY_LICENSES.txt', 'deno-LICENSE.md']:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'fixture')


def test_allowlist_excludes_unused_and_old_tools(tmp_path):
    prepare(tmp_path)
    old = tmp_path / 'ffmpeg/old/bin'
    old.mkdir(parents=True)
    for name in ('ffmpeg.exe', 'ffprobe.exe', 'ffplay.exe'):
        (old / name).touch()
    (tmp_path / 'ffmpeg-shared/ffplay.exe').touch()
    (tmp_path / 'ffmpeg-shared/manual.html').touch()
    files = payload_files(tmp_path)
    assert all('ffplay' not in str(p) and p.suffix != '.html' for p in files)
    assert all('/ffmpeg/old/' not in p.as_posix() for p in files)
    assert any(p.suffix == '.dll' for p in files)
    assert find_tools(tmp_path)['ffmpeg'].parent.name == 'ffmpeg-shared'


def test_shared_libraries_and_notices_required(tmp_path):
    prepare(tmp_path)
    (tmp_path / 'ffmpeg-shared/avcodec-62.dll').unlink()
    with pytest.raises(RuntimeError, match='DLL'):
        payload_files(tmp_path)
    (tmp_path / 'ffmpeg-shared/avcodec-62.dll').touch()
    (tmp_path / 'yt-dlp-THIRD_PARTY_LICENSES.txt').unlink()
    with pytest.raises(RuntimeError, match='missing'):
        payload_files(tmp_path)


def test_file_dialogs_do_not_force_qt_widgets():
    root = Path(__file__).parent
    for name in ('player.py', 'acquisition_ui.py'):
        assert 'DontUseNativeDialog' not in (root / name).read_text(encoding='utf-8')


def test_demo_is_not_packaged_and_cleanup_uses_original_hash():
    import hashlib
    root = Path(__file__).parent
    build = (root / 'build.ps1').read_text(encoding='utf-8')
    installer = (root / 'installer/TommeView.iss').read_text(encoding='utf-8')
    assert "Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'demo')" not in build
    assert not any(line.startswith('Source:') and '\\demo\\' in line
                   for line in installer.splitlines())
    digest = hashlib.sha256((root / 'demo/demo.avi').read_bytes()).hexdigest()
    assert digest in installer
    assert 'Check: IsOriginalDemo' in installer


def test_gpl_notice_and_replacement_instructions_are_packaged():
    root = Path(__file__).parent
    build = (root / 'build.ps1').read_text(encoding='utf-8')
    installer = (root / 'installer/TommeView.iss').read_text(encoding='utf-8')
    for name in ('LICENSE', 'NOTICE', 'TRADEMARKS.md', 'LIBRARY_REPLACEMENT.md',
                 'SOURCE_DELIVERY.md', 'dependency-source-inventory.json'):
        assert (root / name).is_file()
        assert f"'{name}'" in build
        assert f'Source: "..\\dist\\TommeView\\{name}";' in installer
