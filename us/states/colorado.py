"""Colorado Revised Statutes — OLLS HTML zip.

Distribution: https://olls.info/crs/crs2026-htm.zip (HTML titles). The HTML
edition includes Source / Editor's note / Annotator / Cross references blocks;
those are stripped. Unannotated SGML is by request, not a public URL.
"""

import os
import re
import tempfile
import zipfile

from publication import Publication, State
from readers import html_sections

SOURCE = 'https://olls.info/crs/crs2026-htm.zip'

# CRS cites like "1-1-101." or "Section 1-1-101" (html2text may wrap in **).
_SECTION_PATTERN = (
    r'(?i)(?:\*{0,2})(?:Section|Sec\.|§)?\s*'
    r'(\d+-\d+-\d+(?:\.\d+)?)(?:\*{0,2})\s*\.?'
)
_ANNOT_RE = re.compile(
    r'(?:\*{0,2})(?:Source\s*:|Editor\'s note\s*:|Annotator\'s note\s*[.:]|'
    r'Annotators? note\s*[.:]|Cross references\s*:)',
    re.IGNORECASE,
)


def _strip_annotations(text):
    match = _ANNOT_RE.search(text)
    if match:
        return text[: match.start()].strip()
    return text.strip()


def _stamp(row):
    body = _strip_annotations(row['LEGAL_TEXT'])
    # Skip TOC range leaders ("3-1-101 to 3-1-137") and other empty scraps.
    if len(body) < 40:
        return None
    row = dict(row)
    row['LEGAL_TEXT'] = body
    row['SUBDIVISION'] = Colorado.code
    row['LAW_CODE'] = 'CRS'
    row['PK'] = 'CRS:%s' % row['SECTION_NUM']
    return row


def _from_html_path(path):
    for row in html_sections(path, _SECTION_PATTERN):
        stamped = _stamp(row)
        if stamped is not None:
            yield stamped


class ColoradoRevisedStatutes(Publication):
    code_heading = 'Colorado Revised Statutes'
    session = '2026'
    """CRS HTML archive, or one title/chapter .htm file with annotations stripped."""

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset)):
            # HTML zips have no California .dat tables.
            return not names
        name = str(names).lower()
        return name.endswith(('.htm', '.html', '.zip'))

    def sections(self, path):
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    ext = os.path.splitext(info.filename)[1].lower()
                    if ext not in ('.htm', '.html'):
                        continue
                    html = zf.read(info.filename)
                    with tempfile.NamedTemporaryFile(
                        suffix=ext, delete=False,
                    ) as tmp:
                        tmp.write(html)
                        tmp_path = tmp.name
                    try:
                        yield from _from_html_path(tmp_path)
                    finally:
                        os.unlink(tmp_path)
            return
        yield from _from_html_path(path)


class Colorado(State):
    code = 'US-CO'
    source = SOURCE
    editions = (ColoradoRevisedStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return ColoradoRevisedStatutes()
