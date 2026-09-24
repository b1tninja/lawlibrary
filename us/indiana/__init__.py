"""Indiana Code — iga.in.gov HTML zip downloads."""

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


def _read_html_from_zip(path):
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            ext = os.path.splitext(info.filename)[1].lower()
            if ext in ('.html', '.htm'):
                with zf.open(info) as fh:
                    return info.filename, fh.read().decode('utf-8', errors='replace')
    raise FileNotFoundError('no .html in %s' % path)


class IndianaCode(Publication):
    """Full-code HTML zip from the Legislative Services Agency downloads page."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        name, html = _read_html_from_zip(path)
        text = _html_to_text(html)
        matches = list(_SECTION_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(name))[0]
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text}
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body}


class Indiana(State):
    code = 'US-IN'
    source = SOURCE
    editions = (IndianaCode,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        # Zip of HTML, not California .dat tables.
        return IndianaCode()
