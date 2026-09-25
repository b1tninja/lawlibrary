"""Indiana Code — local HTML (HTML zip when a real archive is available).

The Legislative Services Agency downloads page
(https://iga.in.gov/laws/ic/downloads) is a JavaScript app shell. A direct
fetch of https://iga.in.gov/laws/ic/downloads/ic-html.zip returned that same
text/html shell (691 bytes), not a zip of statute text, so there is no
confirmed bulk file URL to fetch. This edition parses local .html/.htm files,
or a local zip containing such files, saved from an official distribution when
one is available.
"""

import os
import re
import zipfile

import html2text

from publication import Publication, State

SOURCE = 'https://iga.in.gov/laws/ic/downloads'

# Indiana Code cites like "IC 1-1-1-1" or "Section 1-1-1-1".
_SECTION_RE = re.compile(
    r'(?:IC\s+|Section\s+)?(\d+-\d+-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Indiana.code,
        'LAW_CODE': 'IC',
        'PK': 'IC:%s' % section_num,
    }


def _yield_from_html(html, stem):
    text = _html_to_text(html)
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        yield _row(stem, text)
        return
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        yield _row(match.group(1), body)


class IndianaCode(Publication):
    """Local Indiana Code HTML, or a zip of HTML files."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    ext = os.path.splitext(info.filename)[1].lower()
                    if ext not in ('.html', '.htm'):
                        continue
                    with zf.open(info) as fh:
                        html = fh.read().decode('utf-8', errors='replace')
                    stem = os.path.splitext(os.path.basename(info.filename))[0]
                    yield from _yield_from_html(html, stem)
            return
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        stem = os.path.splitext(os.path.basename(path))[0]
        yield from _yield_from_html(html, stem)


class Indiana(State):
    code = 'US-IN'
    source = SOURCE
    editions = (IndianaCode,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return IndianaCode()
