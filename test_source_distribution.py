import json
import zipfile

import pytest

import package_dependency_sources as packer


@pytest.fixture
def manifest(tmp_path, monkeypatch):
    manifest = tmp_path / 'manifest.json'
    (tmp_path / 'git-fallbacks.json').write_text('[]', encoding='utf-8')
    monkeypatch.setattr(packer, 'GROUPS', {'': manifest})
    monkeypatch.setattr(packer, 'SOURCES', tmp_path)
    monkeypatch.setattr(packer, 'REPORTS', tmp_path)
    return manifest


def test_rejects_archive_outside_manifest_directory(manifest):
    manifest.write_text(json.dumps([{'file': '../private.tar.gz', 'sha256': '0' * 64}]))
    with pytest.raises(ValueError, match='allowed source archive'):
        packer.selected_sources()


def test_rejects_changed_archive(tmp_path, manifest):
    manifest.write_text(json.dumps([{'file': 'source.tar.gz', 'sha256': '0' * 64}]))
    (tmp_path / 'source.tar.gz').write_bytes(b'changed bytes')
    with pytest.raises(ValueError, match='hash mismatch'):
        packer.selected_sources()


def test_partial_package_is_not_a_valid_zip(tmp_path):
    partial = tmp_path / 'sources.zip.part'
    partial.write_bytes(b'partial')
    with pytest.raises(zipfile.BadZipFile):
        zipfile.ZipFile(partial).testzip()
