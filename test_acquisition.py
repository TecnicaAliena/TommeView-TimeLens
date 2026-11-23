import io
import json
from pathlib import Path
import threading
import sys

import pytest

from acquisition import (AcquisitionCancelled, acquire, download_arguments,
                         find_tools, publish_download, youtube_url, spawn)


@pytest.mark.parametrize('url', [
    'https://youtu.be/BaW_jenozKc?t=2',
    'https://www.youtube.com/watch?v=BaW_jenozKc&list=ignored',
    'https://m.youtube.com/shorts/BaW_jenozKc',
    'https://youtube.com/live/BaW_jenozKc',
])
def test_video_url_normalization(url):
    assert youtube_url(url) == 'https://www.youtube.com/watch?v=BaW_jenozKc'


@pytest.mark.parametrize('url', ['file:///movie', '--exec calc',
    'https://youtube.com.evil.test/watch?v=BaW_jenozKc',
    'https://youtube.com/playlist?list=abc', 'https://user:pass@youtu.be/BaW_jenozKc',
    'https://youtu.be:bad/BaW_jenozKc', 'https://[broken', 'https://youtu.be/short'])
def test_reject_invalid_urls(url):
    with pytest.raises(ValueError, match='youtube_invalid_url'):
        youtube_url(url)


def tool_paths(tmp_path):
    return {name: tmp_path / (name + '.exe') for name in ('yt-dlp', 'deno', 'ffmpeg', 'ffprobe')}


def test_command_quality_and_isolation(tmp_path):
    args = download_arguments('https://youtu.be/BaW_jenozKc', tmp_path, tool_paths(tmp_path))
    assert args[args.index('--format') + 1] == 'bv*+ba/b'
    assert args[args.index('--format-sort') + 1].startswith('res,fps')
    assert '--format-sort-force' in args
    assert '--ignore-config' in args and '--no-plugin-dirs' in args
    assert '--no-playlist' in args and '--no-overwrites' in args
    assert '--cookies-from-browser' not in args
    assert args[-2] == '--'


def test_missing_tools(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_tools(tmp_path)


class FakeProcess:
    def __init__(self, output, code=0):
        self.stdout = io.StringIO(output)
        self.returncode = code

    def poll(self):
        return self.returncode


def fake_download(args):
    folder = Path(args[args.index('--paths') + 1])
    video = folder / 'Video [BaW_jenozKc].mkv'
    video.write_bytes(b'fixture')
    video.with_suffix('.info.json').write_text(json.dumps({'title': 'Video', 'height': 2160}))
    return FakeProcess('TV_PROGRESS: 50.0%\nTV_FILE:' + json.dumps(str(video)) + '\n')


def test_success_duplicate_metadata_and_cleanup(tmp_path):
    progress = []
    for _ in range(2):
        result = acquire('https://youtu.be/BaW_jenozKc', tmp_path, tool_paths(tmp_path),
                         threading.Event(), progress.append, lambda _: None, fake_download)
        assert result.read_bytes() == b'fixture'
        info = json.loads(result.with_suffix('.mkv.source.json').read_text())
        assert info['height'] == 2160 and info['source_url'].startswith('https://www.youtube.com/')
    assert len(list(tmp_path.glob('*.mkv'))) == 2
    assert progress == [50, 50]
    assert not list(tmp_path.glob('.tommeview-download-*'))


@pytest.mark.parametrize('cancel', [True, False])
def test_failure_cancel_preserve_existing(tmp_path, cancel):
    existing = tmp_path / 'existing.mkv'
    existing.write_bytes(b'preserve')
    event = threading.Event()
    if cancel:
        event.set()
    with pytest.raises(AcquisitionCancelled if cancel else RuntimeError):
        acquire('https://youtu.be/BaW_jenozKc', tmp_path, tool_paths(tmp_path), event,
                lambda _: None, lambda _: None, lambda _: FakeProcess('error', 1))
    assert existing.read_bytes() == b'preserve'
    assert not list(tmp_path.glob('.tommeview-download-*'))


def test_refuse_result_outside_staging(tmp_path):
    existing = tmp_path / 'existing.mkv'
    existing.write_bytes(b'preserve')
    with pytest.raises(RuntimeError, match='youtube_missing_result'):
        acquire('https://youtu.be/BaW_jenozKc', tmp_path, tool_paths(tmp_path), threading.Event(),
                lambda _: None, lambda _: None,
                lambda _: FakeProcess('TV_FILE:' + json.dumps(str(existing))))
    assert existing.read_bytes() == b'preserve'


def test_publish_without_hardlinks(tmp_path, monkeypatch):
    staging = tmp_path / 'staging'
    staging.mkdir()
    video = staging / 'video.mkv'
    video.write_bytes(b'fixture')
    def unsupported(*args):
        raise OSError('not supported')
    monkeypatch.setattr('acquisition.os.link', unsupported)
    result = publish_download(video, tmp_path, {'title': 'Video'})
    assert result.read_bytes() == b'fixture'
    assert not video.exists()


def test_cancel_real_child_process(tmp_path):
    stopped = threading.Event()
    processes = []
    timer = threading.Timer(.5, stopped.set)
    def launch(_):
        process = spawn([sys.executable, '-c', 'import time; time.sleep(30)'])
        processes.append(process)
        return process
    timer.start()
    try:
        with pytest.raises(AcquisitionCancelled):
            acquire('https://youtu.be/BaW_jenozKc', tmp_path, tool_paths(tmp_path),
                    stopped, lambda _: None, lambda _: None, launch)
    finally:
        timer.cancel()
    assert processes[0].poll() is not None
    assert not list(tmp_path.glob('.tommeview-download-*'))
