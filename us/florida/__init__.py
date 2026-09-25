"""Florida Statutes — Division of Law Revision download zip.

source points at FLLawDL2026.zip (a Windows statutes browser). This edition
parses saved chapter HTML from the statutes site; it does not unpack the
browser zip.
"""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip'

# Section numbers like "1.01" ahead of a catchline word.
_SECTION_RE = re.compile(r'(?<![\d.])(\d+\.\d+)\s+(?=[A-Za-z])')


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Florida.code,
    }


class FloridaChapter(Publication):
    """One saved chapter HTML page from the Florida Statutes site."""

    @classmethod
    def accepts(cls, names):
        # The official zip is a Windows browser, not chapter HTML.
        if isinstance(names, (set, frozenset)):
            return False
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        text = _html_to_text(html)
        matches = list(_SECTION_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield _row(stem, text)
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield _row(match.group(1), body)


class Florida(State):
    code = 'US-FL'
    source = SOURCE
    editions = (FloridaChapter,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return FloridaChapter()
