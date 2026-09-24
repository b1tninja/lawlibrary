"""Colorado Revised Statutes — OLLS HTML zip."""

import io
import os
import re
import zipfile

import html2text

from publication import Publication, State

SOURCE = 'https://olls.info/crs/crs2026-htm.zip'

_SECTION_RE = re.compile(
    r'(?:Section|Sec\.|§)\s*(\d+-\d+-\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class ColoradoRevisedStatutes(Publication):
    """CRS HTML archive (one or more .htm files inside a zip)."""

    @classmethod
    def accepts(cls, names):
        # HTML zips have no California .dat tables.
        return not names

    def sections(self, path):
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                ext = os.path.splitext(info.filename)[1].lower()
                if ext not in ('.htm', '.html'):
                    continue
                with zf.open(info) as raw:
                    html = io.TextIOWrapper(raw, encoding='utf-8', errors='replace').read()
                text = _html_to_text(html)
                matches = list(_SECTION_RE.finditer(text))
                if not matches:
                    stem = os.path.splitext(os.path.basename(info.filename))[0]
                    yield {'SECTION_NUM': stem, 'LEGAL_TEXT': text}
                    continue
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    body = text[start:end].strip()
                    yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body}


class Colorado(State):
    code = 'US-CO'
    source = SOURCE
    editions = (ColoradoRevisedStatutes,)

    def list_editions(self):
        return [SOURCE]
