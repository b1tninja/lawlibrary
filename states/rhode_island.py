"""Rhode Island General Laws — legislature HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://webserver.rilegislature.gov/statutes/Statutes.html'

# Section markers like "Section 11-1-1" or "§ 11-1-1" in RI HTML.
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class RhodeIslandCode(Publication):
    """One saved Rhode Island HTML page (or chapter dump)."""

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


class RhodeIsland(State):
    code = 'US-RI'
    source = SOURCE
    editions = (RhodeIslandCode,)

    def list_editions(self):
        return [SOURCE]
