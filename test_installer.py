"""Verify setup, installed executable, upgrade and uninstall on Windows."""
import hashlib
import argparse
import json
import os
import shutil
import subprocess
import time
import uuid
import winreg
from pathlib import Path

from model import Markers, SessionStore
from player import default_session_dir
from app_info import APP_VERSION

ROOT = Path(__file__).resolve().parent
UNINSTALL_KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{EE5761C8-27B1-44B7-8F10-3B77A1B52F7A}_is1'
SUPPORTED_EXTENSIONS = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg', '.mts', '.m2ts')


def registration():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, UNINSTALL_KEY) as key:
            return {name: winreg.QueryValueEx(key, name)[0]
                    for name in ('Publisher', 'DisplayVersion', 'InstallLocation')}
    except FileNotFoundError:
        return None


def registry_default(path):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
        return winreg.QueryValueEx(key, '')[0]


def registry_default_optional(path):
    try:
        return registry_default(path)
    except FileNotFoundError:
        return None


def registry_value_exists(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            winreg.QueryValueEx(key, name)
        return True
    except FileNotFoundError:
        return False


def run_process(executable, *args, env=None):
    result = subprocess.run([str(executable), *args], timeout=90,
                            creationflags=subprocess.CREATE_NO_WINDOW, env=env)
    if result.returncode != 0:
        raise RuntimeError(f'{Path(executable).name}: codice {result.returncode}')


def main():
    global UNINSTALL_KEY
    parser = argparse.ArgumentParser()
    parser.add_argument('--validation', action='store_true')
    options = parser.parse_args()
    shell_prog_id = 'TommeView.Validation.Video' if options.validation else 'TommeView.Video'
    shell_application = 'TommeView.Validation.exe' if options.validation else 'TommeView.exe'
    shell_verb = 'TommeViewValidation' if options.validation else 'TommeView'
    if options.validation:
        UNINSTALL_KEY = UNINSTALL_KEY.replace('EE5761C8-27B1-44B7-8F10-3B77A1B52F7A', 'E0B2A21C-B50E-4597-A902-D0003EE2692A')
    if registration() is not None:
        raise RuntimeError('TommeView e gia installato: il test non modifica installazioni esistenti.')
    token = uuid.uuid4().hex[:12]
    output = ROOT / 'test-output' / ('installer-' + token)
    target = output / 'application'
    output.mkdir(parents=True)
    setup = ROOT / 'release' / 'TommeViewSetup.exe'
    if options.validation:
        setup = ROOT / 'release' / ('validation-' + APP_VERSION) / 'TommeViewSetup.exe'
    previous_associations = {
        extension: registry_default_optional(rf'Software\Classes\{extension}')
        for extension in SUPPORTED_EXTENSIONS
    }
    args = ('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS',
            '/TASKS=openwith,contextmenu,fileassoc', f'/DIR={target}')
    store = SessionStore(default_session_dir())
    video = output / ('persistence-' + token + '.mp4')
    sentinel = store.path(video)
    if sentinel.exists():
        raise RuntimeError('La sessione di prova esiste gia')
    sentinel_created = False
    uninstalled = False
    upgraded_previous = False
    upgraded_1_1 = False
    try:
        previous_setup = ROOT / 'release' / 'TommeViewSetup-1.0.0.exe'
        if options.validation:
            previous_setup = ROOT / 'release' / 'validation-1.0' / 'TommeViewSetup.exe'
        if previous_setup.exists():
            run_process(previous_setup, *args, f'/LOG={output / "install-1.0.log"}')
            assert registration()['DisplayVersion'] == '1.0.0'
            legacy = Markers()
            legacy.add(5, 1234)
            store.save(video, legacy)
            sentinel_created = True
            payload = json.loads(sentinel.read_text())
            payload['version'] = 1
            payload.pop('rotation', None)
            sentinel.write_text(json.dumps(payload), encoding='utf-8')
            previous_digest = hashlib.sha256(sentinel.read_bytes()).hexdigest()
        intermediate_setup = ROOT / 'release' / 'validation-1.1' / 'TommeViewSetup.exe'
        if options.validation and previous_setup.exists() and intermediate_setup.exists() and APP_VERSION != '1.1.0':
            run_process(intermediate_setup, *args, f'/LOG={output / "install-1.1.log"}')
            assert registration()['DisplayVersion'] == '1.1.0'
            assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == previous_digest
            legacy.rotation = 270
            store.save(video, legacy)
            previous_digest = hashlib.sha256(sentinel.read_bytes()).hexdigest()
            upgraded_1_1 = True
        run_process(setup, *args, f'/LOG={output / "install.log"}')
        if previous_setup.exists():
            assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == previous_digest
            assert store.load(video).items == legacy.items
            assert store.load(video).rotation == legacy.rotation
            upgraded_previous = True
        metadata = registration()
        assert metadata['Publisher'] == 'Marco Tommesani', metadata
        assert metadata['DisplayVersion'] == APP_VERSION, metadata
        assert Path(metadata['InstallLocation']).resolve() == target.resolve(), metadata
        assert (target / 'TommeView.exe').is_file()
        assert not (target / 'demo').exists(), 'Demo must not be distributed'
        for name in ('LGPL-3.0.txt', 'GPL-3.0.txt', 'LGPL-2.1.txt', 'Python-LICENSE.txt'):
            assert (target / 'licenses' / name).stat().st_size > 1000
        assert (target / 'SOURCE_REFERENCES.md').is_file()
        for source in (ROOT / 'licenses').iterdir():
            if source.is_file():
                assert (target / 'licenses' / source.name).read_bytes() == source.read_bytes()
        assert (target / 'SOURCE_REFERENCES.md').read_bytes() == (ROOT / 'SOURCE_REFERENCES.md').read_bytes()
        assert not (target / 'docs/public-launch-plan.md').exists()
        assert not list((target / '_internal/PySide6').rglob('*VirtualKeyboard*'))
        assert not (target / '_internal/PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll').exists()
        assert not (target / 'data').exists(), 'Il setup non deve contenere dati personali'
        open_command = registry_default(
            rf'Software\Classes\Applications\{shell_application}\shell\open\command')
        assert str(target / 'TommeView.exe').lower() in open_command.lower()
        for extension in SUPPORTED_EXTENSIONS:
            assert registry_value_exists(
                rf'Software\Classes\{extension}\OpenWithProgids', shell_prog_id)
            assert registry_default(rf'Software\Classes\{extension}') == shell_prog_id
            context_command = registry_default(
                rf'Software\Classes\SystemFileAssociations\{extension}\shell\{shell_verb}\command')
            assert str(target / 'TommeView.exe').lower() in context_command.lower()
        run_process(target / 'TommeView.exe', '--self-test',
                    env={**os.environ, 'TOMMEVIEW_TEST_VIDEO': str(ROOT / 'demo/demo.avi')})
        smoke = json.loads((target / 'test-output' / 'smoke-report.json').read_text())
        assert smoke['result'] == 'PASS'
        shutil.copytree(target / 'test-output', output / 'installed-app-test')
        markers = Markers()
        markers.add(3, 1234)
        markers.add(3, 5678)
        store.save(video, markers)
        sentinel_created = True
        digest = hashlib.sha256(sentinel.read_bytes()).hexdigest()
        legacy_vendor = target / '_internal/tools/download/ffmpeg/ffmpeg-n8.1.2-51-g7ba069f4f1-win64-lgpl-8.1'
        (legacy_vendor / 'bin').mkdir(parents=True, exist_ok=True)
        (legacy_vendor / 'doc').mkdir(exist_ok=True)
        obsolete = [legacy_vendor / 'bin' / name for name in ('ffmpeg.exe', 'ffprobe.exe', 'ffplay.exe')]
        obsolete.append(legacy_vendor / 'doc/ffmpeg-all.html')
        obsolete.extend(target / '_internal/PySide6' / name for name in (
            'Qt6VirtualKeyboard.dll', 'plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll',
            'Qt6Pdf.dll', 'plugins/imageformats/qpdf.dll'))
        for path in obsolete:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'old vendor fixture')
        user_file = legacy_vendor / 'doc/user-note.html'
        user_file.write_bytes(b'preserve unknown files')
        demo_target = target / 'demo/demo.avi'
        demo_target.parent.mkdir(exist_ok=True)
        shutil.copyfile(ROOT / 'demo/demo.avi', demo_target)
        run_process(setup, *args, f'/LOG={output / "upgrade.log"}')
        assert not demo_target.exists(), 'Original demo must be removed on upgrade'
        demo_target.write_bytes(b'user replacement video')
        run_process(setup, *args, f'/LOG={output / "upgrade-custom-demo.log"}')
        assert demo_target.read_bytes() == b'user replacement video'
        assert all(not path.exists() for path in obsolete)
        assert user_file.read_bytes() == b'preserve unknown files'
        assert not list((target / '_internal/tools/download/ffmpeg-shared').glob('ffplay.exe'))
        assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == digest
        assert registration()['DisplayVersion'] == APP_VERSION
        run_process(target / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                    f'/LOG={output / "uninstall.log"}')
        for _ in range(40):
            if not (target / 'TommeView.exe').exists() and registration() is None:
                break
            time.sleep(.1)
        assert not (target / 'TommeView.exe').exists()
        assert registration() is None
        assert not registry_value_exists(
            rf'Software\Classes\Applications\{shell_application}', 'FriendlyAppName')
        for extension in SUPPORTED_EXTENSIONS:
            assert not registry_value_exists(
                rf'Software\Classes\{extension}\OpenWithProgids', shell_prog_id)
            assert registry_default_optional(
                rf'Software\Classes\{extension}') == previous_associations[extension]
            try:
                registry_default(
                    rf'Software\Classes\SystemFileAssociations\{extension}\shell\{shell_verb}\command')
            except FileNotFoundError:
                pass
            else:
                raise AssertionError(f'context menu not removed for {extension}')
        uninstalled = True
        assert demo_target.read_bytes() == b'user replacement video'
        assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == digest
        assert store.load(video).items == markers.items
        report = {'result': 'PASS', 'publisher': metadata['Publisher'], 'version': metadata['DisplayVersion'],
                  'upgrade_from_1_0_verified': upgraded_previous,
                  'upgrade_from_1_1_verified': upgraded_1_1,
                  'checks': ['silent per-user installation', 'publisher registration', 'no bundled personal sessions',
                             'no bundled demo; original demo removed on upgrade; user replacement preserved',
                             'license texts and source references installed; internal launch plan excluded',
                             'unused Qt Virtual Keyboard and PDF files absent and removed on upgrade',
                             'Open with registration for supported video formats',
                             'per-format context menu registration and removal',
                             'optional default associations and previous-value restoration',
                             'installed executable playback and controls', 'upgrade preserves user sessions',
                             'upgrade removes obsolete static FFmpeg tools and preserves unknown files',
                             'uninstall removes executable and registration', 'uninstall preserves user sessions'],
                  'evidence': str(output)}
        (ROOT / 'test-output' / 'installer-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
    finally:
        if not uninstalled and (target / 'unins000.exe').exists():
            installed = registration()
            if installed and Path(installed['InstallLocation']).resolve() == target.resolve():
                run_process(target / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART')
        if sentinel_created and sentinel.is_file() and sentinel.resolve().is_relative_to(store.folder.resolve()):
            sentinel.unlink()


if __name__ == '__main__':
    main()
