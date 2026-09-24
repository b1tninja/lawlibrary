"""New Hampshire Revised Statutes Annotated — official RSA HTML."""

import os
import re

import html2text

from publication import Publication, State


SOURCE = 'https://gc.nh.gov/rsa/html/NHTOC.HTM'

# Markers like "Section 1:1" or "Section 21-V:3" in RSA HTML.
_SECTION_RE = re.compile(
    r'Section\s+([\dA-Za-z-]+:[\d.]+)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class NewHampshireRSA(Publication):
    """One saved RSA section or chapter HTML page."""

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


class NewHampshire(State):
    code = 'US-NH'
    source = SOURCE
    editions = (NewHampshireRSA,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return NewHampshireRSA()
