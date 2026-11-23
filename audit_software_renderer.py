"""Compare Qt's software OpenGL DLL with official reference builds, without execution."""
import hashlib
import json
import re
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / 'release/compliance-audit'


def describe(path):
    raw = path.read_bytes()
    binary = pefile.PE(data=raw, fast_load=True)
    sections = {section.Name.rstrip(b'\0').decode(): hashlib.sha256(section.get_data()).hexdigest()
                for section in binary.sections}
    binary.close()
    strings = [value.decode('ascii') for value in re.findall(rb'[ -~]{8,}', raw)
               if re.search(rb'(Mesa [0-9]|LLVM [0-9]|LLVM version)', value)]
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
            'sections': sections, 'version_strings': strings}


def audit():
    installed = describe(ROOT / 'dist/TommeView/_internal/PySide6/opengl32sw.dll')
    comparisons = []
    for folder, archive in (
        ('qt-mesa-reference', 'opengl32sw-64-mesa_11_2_2-signed_sha256.7z'),
        ('qt-mesa-reference-2020', 'opengl32sw-64-mesa_11_2_2-signed.7z'),
    ):
        reference = describe(REPORTS / folder / 'opengl32sw.dll')
        comparisons.append({'upstream': 'https://download.qt.io/development_releases/prebuilt/llvmpipe/windows/' + archive,
                            'reference': reference,
                            'identical_sections': installed['sections'] == reference['sections'],
                            'different_sections': sorted(name for name in installed['sections'].keys() | reference['sections'].keys()
                                                         if installed['sections'].get(name) != reference['sections'].get(name))})
    result = {'bundle': installed, 'comparisons': comparisons,
              'scope': 'PE section comparison only; not a source rebuild or verification of all vendor build inputs'}
    (REPORTS / 'software-renderer-audit.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    audit()
