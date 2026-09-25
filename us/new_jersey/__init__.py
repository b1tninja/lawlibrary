"""New Jersey Statutes — official STATUTES-TEXT.zip distribution."""

import os
import re
import zipfile

from publication import Publication, State

SOURCE = 'https://pub.njleg.gov/statutes/STATUTES-TEXT.zip'

# Line-start cites: 1:1-1. / 2A:4-30.124 / 1:1-2a.
_SECTION_RE = re.compile(
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

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        text = _read_text(path)
        matches = list(_SECTION_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {
                'SECTION_NUM': stem,
                'LEGAL_TEXT': text,
                'SUBDIVISION': NewJersey.code,
            }
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {
                'SECTION_NUM': match.group(1),
                'LEGAL_TEXT': body,
                'SUBDIVISION': NewJersey.code,
            }


class NewJersey(State):
    code = 'US-NJ'
    source = SOURCE
    editions = (NewJerseyStatutes,)

    def list_editions(self):
        return [SOURCE]
