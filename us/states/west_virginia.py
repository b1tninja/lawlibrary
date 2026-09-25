"""West Virginia Code — HTML per section at the legislature host."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://code.wvlegislature.gov/'

# Markers like "§61-2-1" or "Section 61-2-1".
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+[A-Za-z]?-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class WestVirginiaCode(Publication):
    """One saved West Virginia Code HTML page."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': 'US-WV'}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': 'US-WV'}


class WestVirginia(State):
    code = 'US-WV'
    source = SOURCE
    editions = (WestVirginiaCode,)

    def list_editions(self):
        return [SOURCE]
