"""Delaware Code — HTML and title PDFs at delcode.delaware.gov.

PDF bytes are not parsed; list_editions may name a title PDF URL as a sample
edition offered at the host. Parsing covers saved chapter HTML only.
"""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://delcode.delaware.gov/'
SAMPLE_TITLE_PDF = 'https://delcode.delaware.gov/title1/title1.pdf'

# Section heads like "§ 101." or "§ 101A." after html2text.
_SECTION_RE = re.compile(r'§\s*(\d+[A-Za-z]*)\.')


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class DelawareChapter(Publication):
    """One saved chapter HTML page from the Delaware Code Online."""

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


class Delaware(State):
    code = 'US-DE'
    source = SOURCE
    editions = (DelawareChapter,)

    def list_editions(self):
        return [SAMPLE_TITLE_PDF]
