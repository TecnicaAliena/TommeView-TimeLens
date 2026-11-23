"""Recognize source notice documents without mistaking code files for licenses."""
import re
from pathlib import PurePosixPath


def is_notice_file(name):
    path = PurePosixPath(name)
    if path.suffix.lower() in {'.cc', '.h', '.rs', '.c', '.cpp', '.py', '.js', '.sh'}:
        return False
    if re.match(r'(?i)^(licen[sc]e|unlicen[sc]e|copying|copyright|notice|authors)([._-]|$)', path.name):
        return True
    return any(part.lower() in {'licenses', 'licences'} for part in path.parts[:-1]) and path.suffix.lower() in {'', '.txt', '.md'}
