"""Hawaii Revised Statutes — HTML directory at data.capitol.hawaii.gov."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://data.capitol.hawaii.gov/hrscurrent/'

# Section markers like "§1-1" or "§1-4.5" in HRS HTML.
_SECTION_RE = re.compile(r'§\s*(\d+-\d+(?:\.\d+)?)')


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class HawaiiChapter(Publication):
    """One saved HRS HTML page (chapter TOC or section)."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': Hawaii.code}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': Hawaii.code}


class Hawaii(State):
    code = 'US-HI'
    source = SOURCE
    editions = (HawaiiChapter,)

    def list_editions(self):
        return [SOURCE]
