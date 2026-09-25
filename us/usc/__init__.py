"""United States Code — OLRC USLM XML (release-point zips).

Parse format: official USLM ``<section>`` elements from title XML in an
OLRC release-point zip (or a local title ``.xml``). The USLM user guide
names ``section`` as the primary hierarchical level in a USC title.

Title 42 is not positive law. Ingest stores prima facie Code text for
search; it is not the Statutes at Large. Prefer USLM over XHTML, PDF, or
PCC of the same title. One publication is the whole Code
(``data/codes/US.sqlite``).
"""

import os
import re
import xml.etree.ElementTree as ET
import zipfile

from corpus import connect, corpus_path
from publication import Instrument, Publication

SOURCE = 'https://uscode.house.gov/download/download.shtml'
# Current release point as of docs/special/us-code.md (PL 119-111).
TITLE_42_ZIP = (
    'https://uscode.house.gov/download/releasepoints/us/pl/119/111/'
    'xml_usc42@119-111.zip'
)
ALL_TITLES_ZIP = (
    'https://uscode.house.gov/download/releasepoints/us/pl/119/111/'
    'xml_uscAll@119-111.zip'
)

_TITLE_IN_IDENT = re.compile(r'/usc/t(\d+[a-z]?)', re.IGNORECASE)
_SECTION_IN_IDENT = re.compile(r'/s([^/]+)', re.IGNORECASE)
_TITLE_IN_NAME = re.compile(r'usc(\d+[a-z]?)', re.IGNORECASE)
_SECTION_SIGN = re.compile(r'^[§\s]+')
_RELEASE_IN_NAME = re.compile(r'@([\d-]+)')


def _local(tag):
    if tag is None:
        return ''
    if '}' in tag:
        return tag.rsplit('}', 1)[-1]
    return tag


def _attr(el, name):
    for key, value in el.attrib.items():
        if _local(key) == name or key == name:
            return value
    return None


def _plain(el):
    return re.sub(r'\s+', ' ', ''.join(el.itertext())).strip()


def _is_title_xml(name):
    """True for an OLRC USLM title file such as ``usc42.xml``."""
    base = os.path.basename(str(name)).lower()
    return base.endswith('.xml') and 'usc' in base


def _title_from_path(path):
    match = _TITLE_IN_NAME.search(os.path.basename(path))
    return match.group(1) if match else None


def _release_from_path(path):
    match = _RELEASE_IN_NAME.search(os.path.basename(path))
    return match.group(1) if match else ''


def _title_from_ident(ident):
    if not ident:
        return None
    match = _TITLE_IN_IDENT.search(ident)
    return match.group(1) if match else None


def _section_from_ident(ident):
    if not ident:
        return None
    match = _SECTION_IN_IDENT.search(ident)
    return match.group(1) if match else None


def _section_num(section):
    num_el = None
    for child in section:
        if _local(child.tag).lower() == 'num':
            num_el = child
            break
    if num_el is not None:
        value = _attr(num_el, 'value')
        if value:
            return str(value).strip()
        text = _SECTION_SIGN.sub('', _plain(num_el)).strip().rstrip('.')
        if text:
            return text
    return _section_from_ident(_attr(section, 'identifier'))


def _section_text(section):
    """Plain text of the section body; skip editorial notes and source credit."""
    parts = []
    for child in section:
        name = _local(child.tag).lower()
        if name in ('notes', 'note', 'sourcecredit', 'footnote', 'endnote'):
            continue
        text = _plain(child)
        if text:
            parts.append(text)
    if not parts:
        text = _plain(section)
        if text:
            parts.append(text)
    return '\n\n'.join(parts)


def _title_from_tree(root, fallback=None):
    ident = _attr(root, 'identifier')
    title = _title_from_ident(ident)
    if title:
        return title
    for el in root.iter():
        if _local(el.tag).lower() != 'title':
            continue
        title = _title_from_ident(_attr(el, 'identifier'))
        if title:
            return title
        for child in el:
            if _local(child.tag).lower() != 'num':
                continue
            value = _attr(child, 'value')
            if value:
                return str(value).strip()
    return fallback


def _yield_sections(root, title):
    for el in root.iter():
        if _local(el.tag).lower() != 'section':
            continue
        num = _section_num(el)
        text = _section_text(el)
        if not num or not text:
            continue
        law_code = (
            _title_from_ident(_attr(el, 'identifier'))
            or title
        )
        if not law_code:
            continue
        yield {
            'COUNTRY': 'US',
            'LAW_CODE': str(law_code),
            'SECTION_NUM': num,
            'LEGAL_TEXT': text,
        }


class UnitedStatesCode(Publication):
    """OLRC USLM title XML. Walks ``<section>``; one class for every title."""

    instrument = Instrument.STATUTE

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset, list, tuple)):
            return any(_is_title_xml(n) for n in names)
        return _is_title_xml(names)

    def sections(self, path):
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                for info in zf.infolist():
                    if info.is_dir() or not _is_title_xml(info.filename):
                        continue
                    with zf.open(info) as fh:
                        tree = ET.parse(fh)
                    title = _title_from_tree(
                        tree.getroot(),
                        _title_from_path(info.filename),
                    )
                    yield from _yield_sections(tree.getroot(), title)
            return
        tree = ET.parse(path)
        root = tree.getroot()
        title = _title_from_tree(root, _title_from_path(path))
        yield from _yield_sections(root, title)

    def load(self, path, root=None):
        """Parse local USLM title XML (or release zip) into ``US.sqlite``.

        Replaces existing rows for the titles present in the file so a
        second load does not duplicate. ``pk`` is ``{title}:{section}``;
        citation is ``{title} USC {section}``. ``session`` is the release
        id from the path when present, else empty.
        """
        rows = list(self.sections(path))
        if not rows:
            raise ValueError('no USC sections in %s' % path)
        session = _release_from_path(path)
        titles = sorted({row['LAW_CODE'] for row in rows})
        db_path = corpus_path('US', root=root)
        db = connect(db_path)
        try:
            db.executemany(
                'DELETE FROM section WHERE law_code = ?',
                [(title,) for title in titles],
            )
            db.executemany(
                'INSERT INTO section '
                '(pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [
                    (
                        '%s:%s' % (row['LAW_CODE'], row['SECTION_NUM']),
                        row['LAW_CODE'],
                        row['SECTION_NUM'],
                        row['LEGAL_TEXT'],
                        '%s USC %s' % (row['LAW_CODE'], row['SECTION_NUM']),
                        session,
                    )
                    for row in rows
                ],
            )
            db.commit()
        finally:
            db.close()
        return len(rows)
