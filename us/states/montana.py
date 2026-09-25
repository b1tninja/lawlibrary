"""Montana Code Annotated — mca.legmt.gov HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://mca.legmt.gov/bills/mca/'

# MCA cites like "1-1-101" or "§ 45-5-102".
_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class MontanaCodeAnnotated(Publication):
    """One saved MCA HTML page."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': Montana.code}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': Montana.code}


class Montana(State):
    code = 'US-MT'
    source = SOURCE
    editions = (MontanaCodeAnnotated,)

    def list_editions(self):
        return [SOURCE]
