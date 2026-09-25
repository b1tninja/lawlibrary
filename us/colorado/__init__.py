"""Colorado Revised Statutes — OLLS HTML zip.

Distribution: https://olls.info/crs/crs2026-htm.zip (HTML titles). The HTML
edition includes Source / Editor's note / Annotator / Cross references blocks;
those are stripped. Unannotated SGML is by request, not a public URL.
"""

import io
import os
import re
import zipfile

import html2text

from publication import Publication, State

SOURCE = 'https://olls.info/crs/crs2026-htm.zip'

# CRS cites like "1-1-101." or "Section 1-1-101" (html2text may wrap in **).
_SECTION_RE = re.compile(
    r'(?:\*{0,2})(?:Section|Sec\.|§)?\s*(\d+-\d+-\d+(?:\.\d+)?)(?:\*{0,2})\s*\.?',
    re.IGNORECASE,
)
_ANNOT_RE = re.compile(
    r'(?:\*{0,2})(?:Source\s*:|Editor\'s note\s*:|Annotator\'s note\s*[.:]|'
    r'Annotators? note\s*[.:]|Cross references\s*:)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


def _strip_annotations(text):
    match = _ANNOT_RE.search(text)
    if match:
        return text[: match.start()].strip()
    return text.strip()


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Colorado.code,
    }


class ColoradoRevisedStatutes(Publication):
    """CRS HTML archive (one or more .htm files inside a zip)."""

    @classmethod
    def accepts(cls, names):
        # HTML zips have no California .dat tables.
        return isinstance(names, (set, frozenset)) and not names

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
                    yield _row(stem, _strip_annotations(text))
                    continue
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    body = _strip_annotations(text[start:end])
                    if body:
                        yield _row(match.group(1), body)


class Colorado(State):
    code = 'US-CO'
    source = SOURCE
    editions = (ColoradoRevisedStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return ColoradoRevisedStatutes()
