"""South Carolina Code of Laws — statehouse HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://www.scstatehouse.gov/code/statmast.php'

# Section markers like "Section 16-1-10" or "§ 16-1-10" in SC HTML.
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class SouthCarolinaCode(Publication):
    """One saved South Carolina HTML page (or chapter dump)."""

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


class SouthCarolina(State):
    code = 'US-SC'
    source = SOURCE
    editions = (SouthCarolinaCode,)

    def list_editions(self):
        return [SOURCE]
