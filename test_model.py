import csv
import json
import pytest
from model import Markers, SessionStore, export_csv, seconds


def test_intervals_sorted_per_flag_and_recomputed_after_delete():
    markers = Markers()
    markers.add(1, 5123)
    markers.add(2, 4000)
    first = markers.add(1, 1123)
    markers.add(2, 4567)
    markers.add(1, 2123)
    assert [(m.flag, delta) for m, delta in markers.rows()] == [(1, None), (1, 1000), (2, None), (2, 567), (1, 3000)]
    markers.remove(first.id)
    assert [(m.flag, delta) for m, delta in markers.rows()] == [(1, None), (2, None), (2, 567), (1, 3000)]


def test_crossing_does_not_miss_flags_at_high_speed_or_repeat_boundary():
    markers = Markers()
    for flag, ms in [(1, 1000), (2, 1050), (3, 1090), (1, 1300)]:
        markers.add(flag, ms)
    assert [m.flag for m in markers.crossed(999, 1200)] == [1, 2, 3]
    assert not markers.crossed(1090, 1200)
    assert not markers.crossed(1300, 500)


def test_store_and_export(tmp_path):
    markers = Markers()
    markers.add(0, 1234)
    markers.add(0, 2567)
    store = SessionStore(tmp_path / 'sessions')
    video = tmp_path / 'video.mp4'
    store.save(video, markers)
    assert store.load(video).items == markers.items
    assert not list(store.folder.glob('*.tmp'))
    path = tmp_path / 'times.csv'
    export_csv(path, markers)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream, delimiter=';'))
    assert rows[2] == ['0', '', '2,567', '1,333', '1,333', '2567', '1333', '1333']
    assert seconds(6000012) == '6000.012'


def test_reverse_crossing_boundaries_and_rate_range():
    from model import RATES
    markers = Markers()
    for flag, ms in [(1, 1000), (2, 1050), (3, 1090), (1, 1300)]:
        markers.add(flag, ms)
    assert [m.flag for m in markers.crossed_reverse(1300, 1000)] == [3, 2, 1]
    assert not markers.crossed_reverse(1000, 999)
    assert not markers.crossed_reverse(1000, 1300)
    assert RATES[0] == 5 and RATES[-1] == 1000


def test_invalid_session_is_rejected_without_modification(tmp_path):
    store = SessionStore(tmp_path)
    video = tmp_path / 'video.mp4'
    path = store.path(video)
    bad = json.dumps({'version': 1, 'markers': [{'id': 'abc', 'flag': 10, 'ms': 12}]})
    path.write_text(bad)
    with pytest.raises(ValueError):
        store.load(video)
    assert path.read_text() == bad


def test_portable_session_is_migrated_without_overwriting_newer_data(tmp_path):
    video = tmp_path / 'video.mp4'
    old = SessionStore(tmp_path / 'portable' / 'data' / 'sessions')
    markers = Markers()
    markers.add(2, 1234)
    old.save(video, markers)
    original = old.path(video).read_bytes()
    installed = SessionStore(tmp_path / 'appdata' / 'TommeView' / 'sessions', [old.folder])
    assert installed.load(video).items == markers.items
    assert old.path(video).read_bytes() == original
    markers.add(2, 2345)
    installed.save(video, markers)
    assert installed.load(video).items == markers.items
    assert len(old.load(video).items) == 1


def test_import_preserves_existing_sessions_and_reports_invalid_files(tmp_path):
    old = SessionStore(tmp_path / 'old')
    video = tmp_path / 'video.mp4'
    markers = Markers()
    markers.add(1, 234)
    old.save(video, markers)
    installed = SessionStore(tmp_path / 'new')
    assert installed.import_folder(old.folder) == (1, 0, [])
    installed.save(video, Markers())
    (old.folder / 'broken.json').write_text('[]')
    imported, skipped, errors = installed.import_folder(old.folder)
    assert (imported, skipped, len(errors)) == (0, 1, 1)
    assert not installed.load(video).items
    assert (old.folder / 'broken.json').read_text() == '[]'


def test_rotation_migration_cumulative_and_reset(tmp_path):
    old = SessionStore(tmp_path / 'portable')
    video = tmp_path / 'a.mov'
    old.folder.mkdir()
    old.path(video).write_text(json.dumps({'version': 1, 'video': str(video), 'markers': []}))
    store = SessionStore(tmp_path / 'sessions', [old.folder])
    session = store.load(video)
    assert session.rotation == 0
    session.rotation = 270
    for flag, ms in [(1, 3000), (2, 800), (1, 1000), (1, 6000)]:
        session.add(flag, ms)
    store.save(video, session)
    assert store.load(video).rotation == 270
    assert [(m.flag, total) for m, _, total in session.cumulative_rows()] == [(2, 0), (1, 0), (1, 2000), (1, 5000)]
    first = next(m for m in session.items if m.ms == 1000)
    session.remove(first.id)
    assert [total for _, _, total in session.cumulative_rows()] == [0, 0, 3000]
    pending = store.path(video).with_suffix('.tmp')
    pending.write_text('unfinished save')
    store.reset_all()
    assert not pending.exists()
    assert not list(store.folder.glob('*.json'))
    assert store.load(video).rotation == 0
    assert not store.path(video).exists()
    assert old.path(video).exists()


def test_invalid_rotation_rejected(tmp_path):
    store = SessionStore(tmp_path)
    video = tmp_path / 'a.mov'
    store.path(video).write_text(json.dumps({'version': 2, 'video': str(video), 'markers': [], 'rotation': 45}))
    with pytest.raises(ValueError, match='invalid_rotation'):
        store.load(video)


def test_descriptions_are_per_video_and_multiline_csv(tmp_path):
    store = SessionStore(tmp_path / 'sessions')
    markers = Markers(descriptions={'1': 'tempo pinza\nseconda riga'})
    markers.add(1, 1234)
    store.save(tmp_path / 'one.mp4', markers)
    assert store.load(tmp_path / 'one.mp4').descriptions == markers.descriptions
    assert store.load(tmp_path / 'two.mp4').descriptions == {}
    path = tmp_path / 'descriptions.csv'
    export_csv(path, markers)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.reader(stream, delimiter=';'))
    assert rows[1][1] == 'tempo pinza\nseconda riga'
