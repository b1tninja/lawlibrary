"""Vermont Statutes Online — legislature HTML.

The site labels this an unofficial copy.
"""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://legislature.vermont.gov/statutes'

_SECTION_RE = re.compile(
    r'(?:§|Section)\s*(\d+[a-z]?(?:-\d+)*)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class VermontStatutes(Publication):
    """One saved HTML page from the Vermont legislature statutes site."""

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
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text, 'SUBDIVISION': 'US-VT'}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body, 'SUBDIVISION': 'US-VT'}


class Vermont(State):
    code = 'US-VT'
    """HTML browse of the Vermont Statutes; print annotated edition is official."""

    source = SOURCE
    editions = (VermontStatutes,)

    def list_editions(self):
        return [SOURCE]
