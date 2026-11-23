"""Extract renderer license notices from verified official source archives."""
import hashlib
import json
import tarfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ROOT / 'release/compliance-sources'
DEST = ROOT / 'licenses'


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def collect():
    inventory = {row['file']: row for row in json.loads((SOURCES / 'inventory.json').read_text())}
    evidence = []
    specs = [
        ('mesa-11.2.2.tar.xz', {'mesa-11.2.2/docs/license.html'}, 'Mesa-11.2.2-NOTICES.txt'),
        ('llvm-3.6.2.src.tar.xz', {'llvm-3.6.2.src/LICENSE.TXT',
                                 'llvm-3.6.2.src/lib/Support/COPYRIGHT.regex',
                                 'llvm-3.6.2.src/lib/Target/ARM/LICENSE.TXT',
                                 'llvm-3.6.2.src/lib/Support/MD5.cpp'}, 'LLVM-3.6.2-NOTICES.txt'),
    ]
    for filename, wanted, output in specs:
        source = SOURCES / filename
        with source.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != inventory[filename]['sha256']:
                raise ValueError('Archive hash mismatch: ' + filename)
        blocks, found = [], set()
        with tarfile.open(source, 'r|*') as archive:
            for member in archive:
                if not member.isfile() or member.name not in wanted:
                    continue
                raw = archive.extractfile(member).read()
                text = raw.decode('utf-8')
                if member.name.endswith('.html'):
                    parser = TextOnly()
                    parser.feed(text)
                    text = ''.join(parser.parts)
                elif member.name.endswith('MD5.cpp'):
                    if not text.startswith('/*') or '*/' not in text:
                        raise ValueError('Unexpected MD5 source header')
                    text = text[:text.index('*/') + 2]
                blocks.append(f'\n=== {member.name} ===\n{text}\n')
                found.add(member.name)
        if found != wanted:
            raise ValueError(f'Missing notice: {wanted - found}')
        target = DEST / output
        target.write_text(''.join(blocks), encoding='utf-8')
        evidence.append({'file': output, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                         'source_url': inventory[filename]['url'], 'source_sha256': inventory[filename]['sha256'],
                         'source_paths': sorted(found),
                         'transformation': 'HTML tags removed for Mesa; MD5 leading comment only; other notice text unchanged'})
    (DEST / 'renderer-notice-provenance.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    collect()
