"""Illinois Compiled Statutes — ilga.gov FTP HTML tree.

Directory of section HTML at https://www.ilga.gov/ftp/ILCS/ (not one zip).
The FTP readme says the print at the Secretary of State is the official copy.
"""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://www.ilga.gov/ftp/ILCS/'

# ILCS cites like "(5 ILCS 5/1)" or "Sec. 1." in section HTML dumps.
_ILCS_RE = re.compile(
    r'\((\d+)\s+ILCS\s+(\d+)/([\d.]+)\)',
    re.IGNORECASE,
)
_SEC_RE = re.compile(
    r'(?:Section|Sec\.)\s*([\d.]+)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Illinois.code,
    }


class IllinoisCompiledStatutes(Publication):
    """One saved ILCS section HTML file from the FTP tree."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        text = _html_to_text(html)
        ilcs = list(_ILCS_RE.finditer(text))
        if ilcs:
            for i, match in enumerate(ilcs):
                start = match.start()
                end = ilcs[i + 1].start() if i + 1 < len(ilcs) else len(text)
                body = text[start:end].strip()
                num = '%s ILCS %s/%s' % match.groups()
                yield _row(num, body)
            return
        matches = list(_SEC_RE.finditer(text))
        if not matches:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield _row(stem, text)
            return
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            yield _row(match.group(1), body)


class Illinois(State):
    code = 'US-IL'
    source = SOURCE
    editions = (IllinoisCompiledStatutes,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return IllinoisCompiledStatutes()
