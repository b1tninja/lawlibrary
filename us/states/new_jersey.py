"""New Jersey Statutes — official STATUTES-TEXT.zip distribution."""

import os
import zipfile

from publication import Publication, State
from readers import text_sections

SOURCE = 'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'
BOOK = 'NJSA'

# Line-start cites: 1:1-1. / 2A:4-30.124 / 1:1-2a.
_SECTION_PATTERN = (
    r'(?m)^(\d+[A-Za-z]?:\d+[A-Za-z]?-\d+(?:\.\d+)*[A-Za-z]?)\.?\s+'
)


def _read_text(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if os.path.splitext(info.filename)[1].lower() != '.txt':
                    continue
                with zf.open(info) as fh:
                    return fh.read().decode('utf-8', errors='replace')
        return ''
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


class NewJerseyStatutes(Publication):
    """Plain-text dump inside STATUTES-TEXT.zip (STATUTES.TXT)."""

    code_heading = 'New Jersey Statutes'

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        text = _read_text(path)
        for row in text_sections(text, _SECTION_PATTERN):
            row['SUBDIVISION'] = NewJersey.code
            row['LAW_CODE'] = BOOK
            yield row


class NewJersey(State):
    code = 'US-NJ'
    source = SOURCE
    editions = (NewJerseyStatutes,)

    def list_editions(self):
        return [SOURCE]
