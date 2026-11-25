import hashlib
import io
import json
from urllib.error import URLError

import pytest

from ytdlp_update import LATEST, RELEASES, preferred_ytdlp, update_ytdlp

BASE = '2026.08.19'
NEW = '2026.11.23'
PAYLOAD = b'validated executable bytes'


@pytest.fixture
def locations(tmp_path):
    tools = tmp_path / 'tools'
    tools.mkdir()
    (tools / 'download-tools.json').write_text(json.dumps({
        'yt-dlp': {'url': f'{RELEASES}{BASE}/yt-dlp.exe'}
    }), encoding='utf-8')
    return tmp_path / 'cache', tools


def fake_release(tag=NEW, payload=PAYLOAD, **overrides):
    url = f'{RELEASES}{tag}/yt-dlp.exe'
    asset = {'name': 'yt-dlp.exe', 'browser_download_url': url, 'size': len(PAYLOAD),
             'digest': 'sha256:' + hashlib.sha256(PAYLOAD).hexdigest()}
    asset.update(overrides)
    responses = {LATEST: json.dumps({'tag_name': tag, 'assets': [asset]}).encode(),
                 url: payload}
    calls = []

    def opener(target):
        calls.append(target)
        return io.BytesIO(responses[target])

    return opener, calls


def test_update_publishes_verified_file_and_skips_repeat(locations):
    cache, tools = locations
    bundled = tools / 'yt-dlp.exe'
    bundled.write_bytes(b'bundled copy')
    opener, calls = fake_release()
    updated = update_ytdlp(cache, tools, opener)
    assert updated == cache / f'yt-dlp-{NEW}.exe'
    assert updated.read_bytes() == PAYLOAD
    assert preferred_ytdlp(cache, tools, bundled) == updated
    assert bundled.read_bytes() == b'bundled copy'
    assert update_ytdlp(cache, tools, opener) is None
    assert calls == [LATEST, f'{RELEASES}{NEW}/yt-dlp.exe', LATEST]
    older, older_calls = fake_release(BASE)
    assert update_ytdlp(cache, tools, older) is None
    assert older_calls == [LATEST]


@pytest.mark.parametrize('payload, asset', [
    (b'x' * len(PAYLOAD), {}),
    (b'truncated', {}),
    (PAYLOAD, {'digest': None}),
    (PAYLOAD, {'browser_download_url': 'https://example.com/yt-dlp.exe'}),
])
def test_invalid_update_preserves_previous_cache(locations, payload, asset):
    cache, tools = locations
    cache.mkdir()
    previous = cache / 'yt-dlp-2026.09.01.exe'
    previous.write_bytes(b'previous')
    opener, _ = fake_release(payload=payload, **asset)
    with pytest.raises(ValueError):
        update_ytdlp(cache, tools, opener)
    assert list(cache.iterdir()) == [previous]
    assert preferred_ytdlp(cache, tools, tools / 'yt-dlp.exe') == previous


def test_offline_falls_back_to_bundle(locations):
    cache, tools = locations
    cache.mkdir()
    (cache / f'yt-dlp-{BASE}.exe').touch()
    (cache / '.update-incomplete').mkdir()
    bundled = tools / 'yt-dlp.exe'

    def offline(_):
        raise URLError('offline')

    with pytest.raises(URLError):
        update_ytdlp(cache, tools, offline)
    assert preferred_ytdlp(cache, tools, bundled) == bundled
