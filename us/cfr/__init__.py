"""Electronic Code of Federal Regulations — one parser for every title.

Parse format: govinfo / eCFR bulk XML (DIV5 PART, DIV8 SECTION). The annual
CFR PDF and Text on govinfo remain the official legal edition; eCFR XML is
not. Commercial hosts are not sources.
"""

import os
import re
import xml.etree.ElementTree as ET

from corpus import connect, cfr_corpus_path
from publication import Instrument, Publication

BULK_ROOT = 'https://www.govinfo.gov/bulkdata/ECFR'
TITLE_URL = BULK_ROOT + '/title-{n}/ECFR-title{n}.xml'
TITLE_COUNT = 50

_SECTION_N = re.compile(r'^[§\s]+')
_TITLE_IN_NAME = re.compile(r'(?:ECFR-)?title-?(\d+)', re.IGNORECASE)


def title_url(n):
    return TITLE_URL.format(n=int(n))


def _local(tag):
    if tag is None:
        return ''
    if '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def _attr(el, name):
    for key, value in el.attrib.items():
        if _local(key).upper() == name.upper():
            return value
    return None


def _plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def _section_num(raw):
    text = (raw or '').strip()
    text = _SECTION_N.sub('', text).strip()
    return text


def _title_from_path(path):
    match = _TITLE_IN_NAME.search(os.path.basename(path))
    return match.group(1) if match else None


def _title_from_tree(root):
    for el in root.iter():
        if _local(el.tag).upper() != 'IDNO':
            continue
        if (_attr(el, 'TYPE') or '').lower() == 'title':
            text = ''.join(el.itertext()).strip()
            if text.isdigit():
                return text
    for el in root.iter():
        if _local(el.tag).upper() != 'DIV1':
            continue
        if (_attr(el, 'TYPE') or '').upper() == 'TITLE':
            n = _attr(el, 'N')
            if n and str(n).strip().isdigit():
                return str(n).strip()
    return None


def _section_text(section):
    parts = []
    for child in section:
        name = _local(child.tag).upper()
        if name in ('HEAD', 'P'):
            text = _plain(child)
            if text:
                parts.append(text)
        elif name.startswith('DIV'):
            continue
    if not parts:
        text = _plain(section)
        if text:
            parts.append(text)
    return '\n\n'.join(parts)


class CFR(Publication):
    """eCFR bulk XML for any title. One class; do not fork per agency."""

    instrument = Instrument.REGULATION

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset)):
            return False
        name = os.path.basename(str(names)).lower()
        return name.endswith('.xml') and ('ecfr' in name or 'title' in name)

    def sections(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        title = _title_from_tree(root) or _title_from_path(path)
        if not title:
            raise ValueError('CFR title number not found in %s' % path)
        for el in root.iter():
            if _local(el.tag).upper() != 'DIV8':
                continue
            if (_attr(el, 'TYPE') or '').upper() != 'SECTION':
                continue
            num = _section_num(_attr(el, 'N') or '')
            text = _section_text(el)
            if not num or not text:
                continue
            yield {
                'COUNTRY': 'US',
                'LAW_CODE': str(title),
                'SECTION_NUM': num,
                'LEGAL_TEXT': text,
            }

    def load(self, path, root=None):
        """Parse local title XML into ``data/codes/US/cfr/{title}.sqlite``.

        Replaces existing rows for that title so a second load does not
        duplicate. ``pk`` is ``{title}:{section}``; citation is
        ``{title} CFR {section}``.
        """
        rows = list(self.sections(path))
        if not rows:
            raise ValueError('no CFR sections in %s' % path)
        title = rows[0]['LAW_CODE']
        db_path = cfr_corpus_path(title, root=root)
        db = connect(db_path)
        try:
            db.execute('DELETE FROM section WHERE law_code = ?', (title,))
            db.executemany(
                'INSERT INTO section '
                '(pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [
                    (
                        '%s:%s' % (title, row['SECTION_NUM']),
                        title,
                        row['SECTION_NUM'],
                        row['LEGAL_TEXT'],
                        '%s CFR %s' % (title, row['SECTION_NUM']),
                        None,
                    )
                    for row in rows
                ],
            )
            db.commit()
        finally:
            db.close()
        return len(rows)


class CodeOfFederalRegulations:
    """Federal regulations host. Not a State; not an ISO subdivision."""

    source = BULK_ROOT
    editions = (CFR,)

    def list_editions(self):
        """Govinfo bulk URL pattern for each title; does not fetch."""
        return [title_url(n) for n in range(1, TITLE_COUNT + 1)]

    def edition(self, path):
        hint = path
        for parser in self.editions:
            if parser.accepts(hint):
                return parser()
        raise TypeError('no parser for %s' % os.path.basename(path))

    def sections(self, path):
        return self.edition(path).sections(path)
