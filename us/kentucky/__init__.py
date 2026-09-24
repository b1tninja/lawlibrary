"""Kentucky Revised Statutes — LRC HTML distribution."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://apps.legislature.ky.gov/law/statutes/'

# KRS section numbers: 2.010, 446.080, 14A.1-010
_SECTION_RE = re.compile(
    r'(?:KRS\s+)?(\d+[A-Z]?(?:\.\d+[A-Z]?)*(?:-\d+)?\.\d+)\b',
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class KentuckyStatutes(Publication):
    """One saved KRS HTML page (chapter or statute dump)."""

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


class Kentucky(State):
    code = 'US-KY'
    source = SOURCE
    editions = (KentuckyStatutes,)

    def list_editions(self):
        return [SOURCE]
