"""Connecticut General Statutes — chapter HTML at the Legislative Commissioners' Office."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://prdext2.cga.ct.gov/current/pub/titles.htm'

# Body markers like "Sec. 1-1." or "Sec. 1-1a."
_SECTION_RE = re.compile(
    r'Sec\.\s*(\d+[a-z]?-\d+[a-z]*)\.',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class ConnecticutChapter(Publication):
    """One saved chapter HTML page from the current/pub tree."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': Connecticut.code}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': Connecticut.code}


class Connecticut(State):
    code = 'US-CT'
    source = SOURCE
    editions = (ConnecticutChapter,)

    def list_editions(self):
        return [SOURCE]
