"""Fetch verified stable yt-dlp updates into the per-user cache."""
import hashlib
import json
import logging
import re
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


RELEASES = 'https://github.com/yt-dlp/yt-dlp/releases/download/'
LATEST = 'https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'
VERSION = r'\d{4}\.\d{2}\.\d{2}(?:\.\d{1,3})?'
MAX_ASSET_SIZE = 64 * 1024 * 1024


def version_key(version):
    return tuple(int(part) for part in version.split('.'))


def bundled_version(tools_root):
    manifest = json.loads((tools_root / 'download-tools.json').read_text(encoding='utf-8'))
    match = re.fullmatch(re.escape(RELEASES) + f'({VERSION})/yt-dlp.exe',
                         manifest['yt-dlp']['url'])
    if not match:
        raise ValueError('Invalid bundled yt-dlp version')
    return version_key(match[1])


def cached_ytdlp(cache, tools_root):
    """Select only completed cache files newer than the copy in this build."""
    minimum = bundled_version(tools_root)
    versions = []
    for path in cache.glob('yt-dlp-*.exe'):
        match = re.fullmatch(f'yt-dlp-({VERSION})\\.exe', path.name)
        if match and path.is_file():
            version = version_key(match[1])
            if version > minimum:
                versions.append((version, path))
    return max(versions, default=(minimum, None), key=lambda entry: entry[0])


def preferred_ytdlp(cache, tools_root, bundled):
    try:
        return cached_ytdlp(cache, tools_root)[1] or bundled
    except (OSError, ValueError, TypeError, KeyError):
        return bundled


class GitHubRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urlsplit(newurl)
        if (target.scheme != 'https' or target.port not in (None, 443)
                or target.username is not None or target.hostname not in {
                    'api.github.com', 'github.com', 'release-assets.githubusercontent.com',
                    'objects.githubusercontent.com'}):
            raise ValueError('Unexpected yt-dlp update redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def github_open(url):
    return build_opener(GitHubRedirects()).open(
        Request(url, headers={'User-Agent': 'TommeView yt-dlp updater'}), timeout=8)


def update_ytdlp(cache, tools_root, open_url=github_open):
    """Check once and publish a candidate only after checking its size and digest."""
    installed, _ = cached_ytdlp(cache, tools_root)
    with open_url(LATEST) as response:
        release = json.loads(response.read(2 * 1024 * 1024))
    tag = release['tag_name']
    if not re.fullmatch(VERSION, tag) or release.get('draft') or release.get('prerelease'):
        raise ValueError('Unexpected yt-dlp release')
    if version_key(tag) <= installed:
        return None
    asset = next((item for item in release['assets'] if item['name'] == 'yt-dlp.exe'), None)
    url = f'{RELEASES}{tag}/yt-dlp.exe'
    if not asset or asset['browser_download_url'] != url:
        raise ValueError('Missing official yt-dlp Windows release asset')
    digest = re.fullmatch(r'sha256:([0-9a-f]{64})', asset.get('digest') or '')
    size = asset['size']
    if not digest or type(size) is not int or not 0 < size <= MAX_ASSET_SIZE:
        raise ValueError('Missing or invalid yt-dlp release verification data')

    cache.mkdir(parents=True, exist_ok=True)
    candidate = cache / f'yt-dlp-{tag}.exe'
    with tempfile.TemporaryDirectory(prefix='.update-', dir=cache) as staging:
        temporary = Path(staging) / 'yt-dlp.exe'
        checksum = hashlib.sha256()
        received = 0
        with open_url(url) as response, temporary.open('wb') as output:
            while chunk := response.read(256 * 1024):
                received += len(chunk)
                if received > size:
                    raise ValueError('yt-dlp update exceeded its published size')
                output.write(chunk)
                checksum.update(chunk)
        if received != size or checksum.hexdigest() != digest[1]:
            raise ValueError('yt-dlp update failed verification')
        temporary.replace(candidate)
    return candidate


def check_for_update(cache, tools_root):
    try:
        update_ytdlp(cache, tools_root)
    except Exception as error:
        # Acquisition can continue with the cached or bundled executable.
        logging.getLogger(__name__).debug('yt-dlp update skipped: %s', error)
