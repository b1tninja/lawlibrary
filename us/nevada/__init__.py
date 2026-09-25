"""Nevada Revised Statutes — official NRS HTML distribution."""

import os
import re

import html2text

from publication import Publication, State


SOURCE = 'https://www.leg.state.nv.us/nrs/'

# Markers like "NRS 1.010" or "NRS 62A.010" in chapter HTML.
_SECTION_RE = re.compile(
    r'NRS\s+(\d+[A-Za-z]?(?:\.\d+)+)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class NevadaRevisedStatutes(Publication):
    """One saved NRS chapter HTML page."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': 'US-NV'}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': 'US-NV'}


class Nevada(State):
    code = 'US-NV'
    source = SOURCE
    editions = (NevadaRevisedStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return NevadaRevisedStatutes()
