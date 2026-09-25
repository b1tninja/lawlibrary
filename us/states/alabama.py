"""Alabama Code of Alabama — Alison HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://alison.legislature.state.al.us/code-of-alabama'

# Section markers like "Section 13A-1-1" or "§ 1-1-1" in Alison HTML.
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+[A-Za-z]?-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class AlabamaCode(Publication):
    """One saved Alison HTML page (or chapter dump)."""

    @classmethod
    def accepts(cls, names):
        # Not a California-style .dat zip; any empty or unrelated name set is fine.
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        text = _html_to_text(html)
        matches = list(_SECTION_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': Alabama.code}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': Alabama.code}


class Alabama(State):
    code = 'US-AL'
    source = SOURCE
    editions = (AlabamaCode,)

    def list_editions(self):
        return [SOURCE]
