"""Isolated YouTube acquisition; no Qt or changes to annotation storage."""
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit


class AcquisitionCancelled(Exception):
    pass


def youtube_url(value):
    """Accept a single video, never arbitrary sites, commands, or playlists."""
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except ValueError:
        raise ValueError('youtube_invalid_url') from None
    if parsed.scheme not in ('https', 'http') or parsed.username or parsed.password:
        raise ValueError('youtube_invalid_url')
    host = (parsed.hostname or '').lower()
    if port not in (None, 80, 443):
        raise ValueError('youtube_invalid_url')
    if host == 'youtu.be':
        video_id = parsed.path.strip('/')
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if parsed.path == '/watch':
            video_id = parse_qs(parsed.query).get('v', [''])[0]
        else:
            parts = parsed.path.strip('/').split('/')
            video_id = parts[1] if len(parts) == 2 and parts[0] in ('shorts', 'live', 'embed') else ''
    else:
        video_id = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
        raise ValueError('youtube_invalid_url')
    return f'https://www.youtube.com/watch?v={video_id}'


def find_tools(root):
    tools = {}
    for name in ('yt-dlp', 'deno', 'ffmpeg', 'ffprobe'):
        folder = Path(root) / 'ffmpeg-shared' if name in ('ffmpeg', 'ffprobe') else Path(root)
        matches = sorted(folder.rglob(name + '.exe'))
        if not matches:
            raise FileNotFoundError('youtube_missing_tools')
        tools[name] = matches[0].resolve()
    return tools


def download_arguments(url, folder, tools):
    return [str(tools['yt-dlp']), '--ignore-config', '--no-plugin-dirs',
            '--no-playlist', '--no-colors', '--newline', '--progress', '--no-simulate',
            '--match-filters', '!is_live',
            '--encoding', 'utf-8', '--socket-timeout', '30', '--retries', '3',
            '--no-js-runtimes', '--js-runtimes', 'deno:' + str(tools['deno']),
            '--ffmpeg-location', str(tools['ffmpeg'].parent),
            '--format', 'bv*+ba/b', '--format-sort-force', '--format-sort', 'res,fps,quality,br',
            '--merge-output-format', 'mkv', '--windows-filenames', '--no-overwrites',
            '--write-info-json', '--paths', str(folder),
            '--output', '%(title).100B [%(id)s].%(ext)s',
            '--progress-template', 'download:TV_PROGRESS:%(progress._percent_str)s',
            '--print', 'after_move:TV_FILE:%(filepath)j', '--', youtube_url(url)]


def spawn(arguments):
    """Prevent frozen Qt DLL search paths leaking into independent tools."""
    options = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                   stdin=subprocess.DEVNULL, text=True, encoding='utf-8', errors='replace')
    env = os.environ.copy()
    if os.name == 'nt':
        env = {key.upper(): value for key, value in env.items()}
        options['creationflags'] = subprocess.CREATE_NO_WINDOW
        env['PATH'] = os.pathsep.join([str(Path(arguments[0]).parent),
                                     str(Path(env['SYSTEMROOT']) / 'System32'), env['SYSTEMROOT']])
    options['env'] = env
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    frozen_windows = os.name == 'nt' and getattr(sys, 'frozen', False)
    if frozen_windows:
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    try:
        return subprocess.Popen(arguments, **options)
    finally:
        if frozen_windows:
            ctypes.windll.kernel32.SetDllDirectoryW(sys._MEIPASS)


def stop_process(process):
    if process.poll() is None:
        if os.name == 'nt':
            # Only the process tree created by this acquisition is terminated.
            subprocess.run([str(Path(os.environ['SystemRoot']) / 'System32/taskkill.exe'),
                            '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
        else:
            process.kill()
        process.wait(timeout=15)


def publish_download(source, destination, metadata):
    """Reserve a name without replacing an existing video or sidecar."""
    for number in range(10000):
        suffix = f' ({number})' if number else ''
        target = destination / (source.stem + suffix + source.suffix)
        sidecar = target.with_suffix(target.suffix + '.source.json')
        if sidecar.exists():
            continue
        try:
            # A hard link is atomic, no-overwrite, and on the same volume as staging.
            os.link(source, target)
        except FileExistsError:
            continue
        except OSError:
            # FAT/exFAT and some network shares do not support hard links.
            try:
                stream = target.open('xb')
            except FileExistsError:
                continue
            try:
                with source.open('rb') as original, stream:
                    shutil.copyfileobj(original, stream)
            except Exception:
                target.unlink()
                raise
        try:
            with sidecar.open('x', encoding='utf-8') as stream:
                json.dump(metadata, stream, ensure_ascii=False, indent=2)
        except Exception:
            target.unlink()  # Our new link only; staging still owns the original.
            raise
        source.unlink()
        return target
    raise OSError('Too many duplicate filenames')


def acquire(url, destination, tools, cancelled, progress, log, launcher=spawn):
    url = youtube_url(url)
    destination = Path(destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.tommeview-download-', dir=destination)).resolve()
    process = None
    try:
        process = launcher(download_arguments(url, staging, tools))
        lines = queue.Queue()

        def read_output():
            try:
                for line in process.stdout:
                    lines.put(line.rstrip())
            finally:
                lines.put(None)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        result = None
        errors = []
        while True:
            if cancelled.is_set():
                raise AcquisitionCancelled()
            try:
                line = lines.get(timeout=.1)
            except queue.Empty:
                continue
            if line is None:
                break
            if line.startswith('TV_PROGRESS:'):
                match = re.search(r'([\d.]+)%', line)
                progress(float(match[1]) if match else -1)
            elif line.startswith('TV_FILE:'):
                result = Path(json.loads(line[len('TV_FILE:'):])).resolve()
            else:
                errors.append(line[-2000:])
                errors = errors[-15:]
                log(line[-2000:])
        while process.poll() is None:
            if cancelled.wait(.1):
                raise AcquisitionCancelled()
        if cancelled.is_set():
            raise AcquisitionCancelled()
        if process.returncode != 0:
            raise RuntimeError('\n'.join(errors))
        if not result or not result.is_relative_to(staging) or not result.is_file():
            raise RuntimeError('youtube_missing_result')
        info_path = next(staging.glob('*.info.json'), None)
        info = json.loads(info_path.read_text(encoding='utf-8')) if info_path else {}
        metadata = {key: info.get(key) for key in ('id', 'title', 'width', 'height', 'fps')}
        metadata['source_url'] = url
        return publish_download(result, destination, metadata)
    finally:
        if process is not None:
            stop_process(process)
            if process.stdout:
                process.stdout.close()
        # Never remove the destination or existing acquisitions.
        if staging.parent == destination and staging.name.startswith('.tommeview-download-'):
            shutil.rmtree(staging)
