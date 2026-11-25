import csv
import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass, field, replace
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


@dataclass(frozen=True)
class PlaybackZone:
    kind: str
    start: int
    end: int
    region: tuple[float, float, float, float] | None = None
    speed: int = 10
    enter_ms: int = 200
    exit_ms: int = 200
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    start_marker: str | None = None
    end_marker: str | None = None

    def validate(self):
        if (not isinstance(self.id, str) or not self.id
                or self.kind not in ('zoom', 'speed')
                or type(self.start) is not int or type(self.end) is not int
                or not 0 <= self.start < self.end
                or type(self.speed) is not int or not 1 <= self.speed <= 1000
                or self.start_marker is not None and self.start_marker == self.end_marker
                or any(link is not None and (not isinstance(link, str) or not link)
                       for link in (self.start_marker, self.end_marker))
                or any(type(ms) is not int or not 0 <= ms <= 60_000
                       for ms in (self.enter_ms, self.exit_ms))):
            raise ValueError('zone_invalid')
        if self.kind == 'speed' and self.region is None:
            return
        if (self.kind != 'zoom' or not isinstance(self.region, tuple)
                or len(self.region) != 4
                or any(type(v) not in (int, float) or not 0 <= v <= 1 for v in self.region)
                or self.region[2] <= self.region[0] or self.region[3] <= self.region[1]):
            raise ValueError('zone_invalid')


class Markers:
    def __init__(self, items=(), rotation=0, descriptions=None, zones=()):
        self.items = list(items)
        self.rotation = rotation
        self.descriptions = dict(descriptions or {})
        self.zones = []
        for zone in zones:
            if any(other.id == zone.id for other in self.zones):
                raise ValueError('zone_invalid')
            self.set_zone(zone)

    def set_zone(self, zone):
        zone.validate()
        for link in (zone.start_marker, zone.end_marker):
            if link is not None and not any(marker.id == link for marker in self.items):
                raise ValueError('zone_invalid')
        others = [other for other in self.zones if other.id != zone.id]
        if any(other.kind == zone.kind and zone.start < other.end and other.start < zone.end
               for other in others):
            raise ValueError('zone_overlap')
        self.zones = sorted([*others, zone], key=lambda item: item.start)

    def zone_at(self, kind, ms, reverse=False):
        return next((zone for zone in self.zones if zone.kind == kind and
                     (zone.start < ms <= zone.end if reverse else zone.start <= ms < zone.end)), None)

    def reverse_position(self, origin, elapsed_ms, master_rate):
        """Integrate reverse playback across each speed boundary in wall time."""
        remaining = elapsed_ms * master_rate
        position = origin
        for zone in reversed(self.zones):
            if zone.kind != 'speed' or zone.start >= position:
                continue
            edge = min(position, zone.end)
            gap = position - edge
            if remaining <= gap:
                return position - remaining
            remaining -= gap
            cost = (edge - zone.start) * 100 / zone.speed
            if remaining <= cost:
                return edge - remaining * zone.speed / 100
            remaining -= cost
            position = zone.start
        return max(0, position - remaining)

    def add(self, flag, ms):
        marker = Marker(uuid.uuid4().hex, int(flag), max(0, int(ms)))
        self.items.append(marker)
        return marker

    def remove(self, marker_id):
        self.items = [m for m in self.items if m.id != marker_id]
        self.zones = [replace(zone,
                              start_marker=None if zone.start_marker == marker_id else zone.start_marker,
                              end_marker=None if zone.end_marker == marker_id else zone.end_marker)
                      for zone in self.zones]

    def move_marker(self, marker_id, ms, duration):
        if type(ms) is not int or not 0 <= ms <= duration:
            raise ValueError('zone_invalid')
        marker = next(item for item in self.items if item.id == marker_id)
        delta = ms - marker.ms
        items = [replace(item, ms=ms) if item.id == marker_id else item for item in self.items]
        zones = []
        for zone in self.zones:
            if marker_id in (zone.start_marker, zone.end_marker):
                zone = replace(zone, start=zone.start + (delta if zone.start_marker == marker_id else 0),
                               end=zone.end + (delta if zone.end_marker == marker_id else 0))
                if zone.end > duration:
                    raise ValueError('zone_invalid')
            zones.append(zone)
        # Validate the complete edit before mutating marker times or zone bounds.
        updated = Markers(items, self.rotation, self.descriptions, zones)
        self.items, self.zones = updated.items, updated.zones

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
        if (not isinstance(data, dict) or data.get('version') not in (1, 2, 3, 4)
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
        zones = data.get('zones', []) if data['version'] == 4 else []
        if not isinstance(zones, list):
            raise ValueError('zone_invalid')
        parsed = []
        for zone in zones:
            if not isinstance(zone, dict) or 'id' not in zone:
                raise ValueError('zone_invalid')
            values = dict(zone)
            if isinstance(values.get('region'), list):
                values['region'] = tuple(values['region'])
            parsed.append(PlaybackZone(**values))
        return data['video'], Markers(markers, rotation, descriptions, parsed)

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
        payload = {'version': 4 if markers.zones else 3,
                   'video': str(Path(video).resolve()), 'rotation': markers.rotation,
                   'descriptions': markers.descriptions,
                   'markers': [asdict(m) for m, _ in markers.rows()]}
        if markers.zones:
            payload['zones'] = [asdict(zone) for zone in markers.zones]
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
