from string import Formatter
from localization import CATALOG, Translator


def test_catalog_complete_and_placeholders_match():
    for key, entry in CATALOG.items():
        assert set(entry) == {'it', 'en'}, key
        placeholders = lambda value: {field for _, field, _, _ in Formatter().parse(value) if field}
        assert placeholders(entry['it']) == placeholders(entry['en']), key
        assert entry['it'] and entry['en']


def test_language_round_trip_and_invalid_settings(tmp_path):
    path = tmp_path / 'preferences.json'
    translator = Translator(path)
    assert translator.language == 'it'
    translator.set_language('en')
    assert Translator(path).text('Cumulato (s)') == 'Cumulative (s)'
    path.write_text('broken')
    assert Translator(path).language == 'it'
