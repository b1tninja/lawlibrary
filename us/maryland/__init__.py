"""Maryland Code — General Assembly HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://mgaleg.maryland.gov/mgawebsite/laws/statutes'

# § 1-101, Section 2-201, Art. 1 § 3
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+[A-Za-z]?-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class MarylandStatutes(Publication):
    """One saved Maryland statutes HTML page."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        text = _html_to_text(html)
        matches = list(_SECTION_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body}


class Maryland(State):
    code = 'US-MD'
    source = SOURCE
    editions = (MarylandStatutes,)

    def list_editions(self):
        return [SOURCE]
