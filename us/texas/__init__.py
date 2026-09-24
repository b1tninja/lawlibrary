"""Texas Statutes — Legislative Council HTML downloads."""

import os
import re
import zipfile

import html2text

from publication import Publication, State

SOURCE = 'https://statutes.capitol.texas.gov/download'

_SECTION_RE = re.compile(
    r'(?:Sec\.|Section)\s*(\d+\.\d+(?:\.\d+)?)',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class TexasStatutes(Publication):
    """One code zip containing a single .htm file of statutory text."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with zipfile.ZipFile(path) as zf:
            htm_names = [
                info.filename for info in zf.infolist()
                if os.path.splitext(info.filename)[1].lower() in ('.htm', '.html')
                and not info.is_dir()
            ]
            if not htm_names:
                return
            name = htm_names[0]
            html = zf.read(name).decode('utf-8', errors='replace')
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


class Texas(State):
    code = 'US-TX'
    source = SOURCE
    editions = (TexasStatutes,)

    def list_editions(self):
        return [SOURCE]
