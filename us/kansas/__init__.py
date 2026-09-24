"""Kansas Statutes — kslegislature.gov HTML statute book."""

import os
import re

import html2text

from publication import Publication, State

SOURCE = 'https://www.kslegislature.gov/b2025_26/laws/'

# K.S.A. cites like "50-6,146" or "65-1113" after Section/K.S.A./§.
_SECTION_RE = re.compile(
    r'(?:K\.?S\.?A\.?\s+|Section\s+|§\s*)?(\d+-\d+(?:,\d+)*(?:\.\d+)?)',
    re.IGNORECASE,
)
_META_RE = re.compile(
    r'<meta[^>]+name=["\']T_KSASECTEXT_S_KSANUM["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html)


class KansasStatutes(Publication):
    """One saved Kansas Statutes HTML section page."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            html = fh.read()
        text = _html_to_text(html)
        matches = list(_SECTION_RE.finditer(text))
        if matches:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                body = text[start:end].strip()
                yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body}
            return
        meta = _META_RE.search(html)
        stem = os.path.splitext(os.path.basename(path))[0]
        num = meta.group(1) if meta else stem
        yield {'SECTION_NUM': num, 'LEGAL_TEXT': text}


class Kansas(State):
    code = 'US-KS'
    source = SOURCE
    editions = (KansasStatutes,)

    def list_editions(self):
        return [SOURCE]
