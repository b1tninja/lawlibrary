"""Oregon Revised Statutes — legislature ORS HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://www.oregonlegislature.gov/bills_laws/pages/ors.aspx'

# ORS markers like "Section 1.010" or "ORS 162.005" in chapter HTML.
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|ORS|§)\s*(\d+\.\d+(?:[A-Za-z]+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class OregonCode(Publication):
    """One saved ORS HTML page (or chapter dump)."""

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


class Oregon(State):
    code = 'US-OR'
    source = SOURCE
    editions = (OregonCode,)

    def list_editions(self):
        return [SOURCE]
