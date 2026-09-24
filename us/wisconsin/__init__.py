"""Wisconsin Statutes — HTML chapters at the legislature host."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://docs.legis.wisconsin.gov/statutes/statutes/'

# Markers like "1.01" or "Section 943.10" after a section label.
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+[A-Za-z]?(?:\.\d+)+)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class WisconsinStatutes(Publication):
    """One saved Wisconsin Statutes HTML page (annotations left for later)."""

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


class Wisconsin(State):
    code = 'US-WI'
    source = SOURCE
    editions = (WisconsinStatutes,)

    def list_editions(self):
        return [SOURCE]
