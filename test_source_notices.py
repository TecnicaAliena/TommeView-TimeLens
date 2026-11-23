import hashlib
import io
import tarfile

import pytest

from assemble_crate_notices import read_notices
from notice_files import is_notice_file
from assemble_declared_apache_notices import leading_notice
from assemble_declared_permissive_notices import TEXTS


def test_retains_original_header_but_not_program_code():
    header = '// Copyright 2016 Example\n// Licensed under Apache-2.0\n'
    assert leading_notice(header + 'fn main() {}\n') == header
    assert leading_notice('/* Copyright Example; SPDX-License-Identifier: MIT */\nint x;') == '/* Copyright Example; SPDX-License-Identifier: MIT */'
    assert leading_notice('// Ordinary code comment\nfn main() {}') == ''


def test_permissive_notice_texts_have_pinned_hashes():
    assert set(TEXTS) == {'MIT', 'CC0-1.0'}
    assert all(len(expected) == 64 for _, expected in TEXTS.values())


@pytest.mark.parametrize('name', ['crate/UNLICENSE', 'crate/AUTHORS', 'crate/LICENSE-MIT', 'crate/LICENSES/Apache-2.0.txt'])
def test_additional_notice_names(name):
    assert is_notice_file(name)


@pytest.mark.parametrize('name', ['crate/notice.rs', 'crate/copyright.cc', 'crate/LICENSES/generate.py', 'crate/src/lib.rs'])
def test_code_is_not_a_notice_document(name):
    assert not is_notice_file(name)


def archive_fixture(tmp_path):
    path = tmp_path / 'source.tar.gz'
    content = b'Copyright Example\nPermission notice\n'
    with tarfile.open(path, 'w:gz') as archive:
        entry = tarfile.TarInfo('source/LICENSE')
        entry.size = len(content)
        archive.addfile(entry, io.BytesIO(content))
    return path, hashlib.sha256(path.read_bytes()).hexdigest(), content


def test_exact_notice_bytes_preserved(tmp_path):
    path, digest, content = archive_fixture(tmp_path)
    assert read_notices(path, digest, ['source/LICENSE']) == {'source/LICENSE': content}


def test_notice_reader_rejects_changed_source(tmp_path):
    path, _, _ = archive_fixture(tmp_path)
    with pytest.raises(ValueError, match='hash mismatch'):
        read_notices(path, '0' * 64, ['source/LICENSE'])


def test_notice_reader_rejects_missing_notice(tmp_path):
    path, digest, _ = archive_fixture(tmp_path)
    with pytest.raises(ValueError, match='notice missing'):
        read_notices(path, digest, ['source/COPYING'])
