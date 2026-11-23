import csv
import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

RATES = (5, 10, 20, 25, 33, 50, 67, 75, 100, 125, 150, 175, 200, 250, 300, 400, 500, 600, 800, 1000)
COLORS = ('#a4b5c4', '#4bd6bd', '#ffca65', '#70b7ff', '#ff8796', '#c6a0ff', '#b7d968', '#ffad70', '#70d4ef', '#ee9ed8')


def seconds(ms):
    return f'{int(ms) // 1000}.{int(ms) % 1000:03d}'


@dataclass(frozen=True)
class Marker:
    id: str
    flag: int
    ms: int


class Markers:
    def __init__(self, items=(), rotation=0, descriptions=None):
        self.items = list(items)
        self.rotation = rotation
        self.descriptions = dict(descriptions or {})

    def add(self, flag, ms):
        marker = Marker(uuid.uuid4().hex, int(flag), max(0, int(ms)))
        self.items.append(marker)
        return marker

    def remove(self, marker_id):
        self.items = [m for m in self.items if m.id != marker_id]

    def rows(self):
        previous = {}
        result = []
        for marker in sorted(self.items, key=lambda m: m.ms):
            delta = marker.ms - previous[marker.flag] if marker.flag in previous else None
            result.append((marker, delta))
            previous[marker.flag] = marker.ms
        return result

    def crossed(self, before, now):
        return [m for m, _ in self.rows() if before < m.ms <= now]

    def crossed_reverse(self, before, now):
        return [m for m, _ in reversed(self.rows()) if now <= m.ms < before]

    def cumulative_rows(self):
        first = {}
        for marker, delta in self.rows():
            first.setdefault(marker.flag, marker.ms)
            yield marker, delta, marker.ms - first[marker.flag]


class SessionStore:
    def __init__(self, folder, legacy_folders=()):
        self.folder = Path(folder)
        self.legacy_folders = [Path(p) for p in legacy_folders]

    def path(self, video):
        key = hashlib.sha256(os.path.normcase(str(Path(video).resolve())).encode()).hexdigest()[:24]
        return self.folder / (key + '.json')

    def load(self, video):
        path = self.path(video)
        if not path.exists():
            for folder in (() if (self.folder / '.legacy-import-disabled').exists() else self.legacy_folders):
                legacy = folder / path.name
                if legacy.is_file():
                    stored_video, markers = self.read_session(legacy)
                    if self.path(stored_video) != path:
                        raise ValueError('session_video_mismatch')
                    self.save(video, markers)
                    return markers
            return Markers()
        return self.read_session(path)[1]

    @staticmethod
    def read_session(path):
        data = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(data, dict) or data.get('version') not in (1, 2, 3)
                or not isinstance(data.get('markers'), list)
                or not isinstance(data.get('video'), str) or not data['video']):
            raise ValueError('invalid_session')
        rotation = data.get('rotation', 0)
        if type(rotation) is not int or rotation not in (0, 90, 180, 270):
            raise ValueError('invalid_rotation')
        markers = []
        ids = set()
        for item in data['markers']:
            marker = Marker(**item)
            if (type(marker.flag) is not int or not 0 <= marker.flag <= 9
                    or type(marker.ms) is not int or marker.ms < 0
                    or not isinstance(marker.id, str) or not marker.id or marker.id in ids):
                raise ValueError('invalid_marker')
            ids.add(marker.id)
            markers.append(marker)
        descriptions = data.get('descriptions', {})
        if (not isinstance(descriptions, dict) or any(
                key not in [str(n) for n in range(10)] or not isinstance(value, str)
                for key, value in descriptions.items())):
            raise ValueError('invalid_session')
        return data['video'], Markers(markers, rotation, descriptions)

    def import_folder(self, folder):
        imported = skipped = 0
        errors = []
        for source in sorted(Path(folder).glob('*.json')):
            try:
                video, markers = self.read_session(source)
                if self.path(video).exists():
                    skipped += 1
                    continue
                self.save(video, markers)
                imported += 1
            except (OSError, ValueError, TypeError, KeyError) as exc:
                errors.append(f'{source.name}: {exc}')
        return imported, skipped, errors

    def save(self, video, markers):
        self.folder.mkdir(parents=True, exist_ok=True)
        path = self.path(video)
        temporary = path.with_suffix('.tmp')
        payload = {'version': 3, 'video': str(Path(video).resolve()), 'rotation': markers.rotation,
                   'descriptions': markers.descriptions,
                   'markers': [asdict(m) for m, _ in markers.rows()]}
        temporary.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        os.replace(temporary, path)

    def reset_all(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        # A reset must not resurrect old portable sessions on the next launch.
        (self.folder / '.legacy-import-disabled').touch()
        for pattern in ('*.json', '*.tmp'):
            for path in self.folder.glob(pattern):
                if path.is_file() and not path.is_symlink():
                    path.unlink()


def export_csv(path, markers, translate=lambda text: text, language='it'):
    with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream, delimiter=';')
        writer.writerow([translate(s) for s in ['Flag', 'Descrizione', 'Tempo (s)', 'Intertempo (s)', 'Cumulato (s)',
                                               'Tempo (ms)', 'Intertempo (ms)', 'Cumulato (ms)']])
        def number(ms):
            return seconds(ms).replace('.', ',') if language == 'it' else seconds(ms)
        for marker, delta, cumulative in markers.cumulative_rows():
            writer.writerow([marker.flag, markers.descriptions.get(str(marker.flag), ''), number(marker.ms), '' if delta is None else number(delta),
                             number(cumulative), marker.ms, '' if delta is None else delta, cumulative])
