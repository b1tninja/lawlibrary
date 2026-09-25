"""Electronic Code of Federal Regulations — one parser for every title.

Parse format: the annual CFR XML on govinfo (``CFRDOC`` / ``SECTION``), which
is the official edition and keeps part and chapter. eCFR bulk XML
(``DIV8`` SECTION) still parses when that is the file on disk. PDF is the
print copy of the same title. Commercial hosts are not sources.
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


def _child_text(el, name):
    for child in el:
        if _local(child.tag).upper() == name:
            text = _plain(child)
            if text:
                return text
    return ''


def _title_from_tree(root):
    if _local(root.tag).upper() == 'CFRDOC':
        for el in root.iter():
            if _local(el.tag).upper() != 'TITLENUM':
                continue
            text = ''.join(el.itertext()).strip()
            if text.isdigit():
                return text
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


def _title_heading(root, title):
    """Printed title name when the eCFR file names it (DIV1 HEAD)."""
    for el in root.iter():
        if _local(el.tag).upper() != 'DIV1':
            continue
        if (_attr(el, 'TYPE') or '').upper() != 'TITLE':
            continue
        for child in el:
            if _local(child.tag).upper() == 'HEAD':
                text = _plain(child)
                if text:
                    return text
    if title:
        return 'Title %s' % title
    return None


def _law_code(title):
    """Whoosh token such as ``1CFR`` from the title number."""
    if not title:
        return None
    text = str(title).strip()
    if text.upper().endswith('CFR'):
        return text.upper() if text[-3:].isalpha() else text
    return '%sCFR' % text


def _title_num_for_path(law_code):
    """Numeric title for ``cfr_corpus_path`` from a ``1CFR`` token."""
    text = str(law_code or '').strip()
    if text.upper().endswith('CFR'):
        return text[:-3]
    return text


def _outline(el, parents):
    """Title, chapter, and part that contain this section."""
    fields = {}
    cur = parents.get(el)
    while cur is not None:
        kind = (_attr(cur, 'TYPE') or '').upper()
        if kind in ('TITLE', 'CHAPTER', 'PART') and kind not in fields:
            number = (_attr(cur, 'N') or '').strip()
            head = ''
            for child in cur:
                if _local(child.tag).upper() == 'HEAD':
                    head = _plain(child)
                    break
            if number:
                fields[kind] = number
            if head:
                fields['%s_HEADING' % kind] = head
        cur = parents.get(cur)
    return fields


def _annual_outline(el, parents):
    """Title, chapter, and part printed on the annual CFR XML."""
    fields = {}
    cur = parents.get(el)
    while cur is not None:
        tag = _local(cur.tag).upper()
        if tag in ('TITLE', 'CHAPTER', 'PART') and tag not in fields:
            if tag == 'TITLE':
                head = _child_text(cur, 'CFRTITLE') or _child_text(cur, 'HD')
            else:
                head = _child_text(cur, 'HD')
            number = ''
            if tag == 'PART':
                raw = _child_text(cur, 'EAR') or head
                match = re.search(r'\d+', raw)
                number = match.group(0) if match else ''
            elif tag == 'TITLE' and head:
                match = re.search(r'\d+', head)
                number = match.group(0) if match else ''
            if number:
                fields[tag] = number
            if head:
                fields['%s_HEADING' % tag] = head
        cur = parents.get(cur)
    return fields


def _annual_sections(root, parents, law_code, code_heading):
    for el in root.iter():
        if _local(el.tag).upper() != 'SECTION':
            continue
        num = _section_num(_child_text(el, 'SECTNO'))
        parts = []
        for child in el:
            if _local(child.tag).upper() == 'P':
                text = _plain(child)
                if text:
                    parts.append(text)
        text = '\n\n'.join(parts)
        if not num or not text:
            continue
        row = {
            'COUNTRY': 'US',
            'SUBDIVISION': 'US',
            'LAW_CODE': law_code,
            'SECTION_NUM': num,
            'LEGAL_TEXT': text,
        }
        subject = _child_text(el, 'SUBJECT')
        if subject:
            row['SECTION_TITLE'] = subject
        if code_heading:
            row['CODE_HEADING'] = code_heading
        row.update(_annual_outline(el, parents))
        yield row


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
    """Annual CFR XML, or eCFR bulk XML. One class; do not fork per agency."""

    instrument = Instrument.REGULATION

    @classmethod
    def accepts(cls, names):
        if isinstance(names, (set, frozenset)):
            return False
        name = os.path.basename(str(names)).lower()
        return name.endswith('.xml') and (
            'ecfr' in name or 'cfr' in name or 'title' in name
        )

    def sections(self, path):
        from readers import parent_map
        tree = ET.parse(path)
        root = tree.getroot()
        parents = parent_map(root)
        title = _title_from_tree(root) or _title_from_path(path)
        if not title:
            raise ValueError('CFR title number not found in %s' % path)
        law_code = _law_code(title)
        code_heading = _title_heading(root, title)
        if _local(root.tag).upper() == 'CFRDOC':
            if not code_heading or code_heading == 'Title %s' % title:
                for el in root.iter():
                    if _local(el.tag).upper() == 'CFRTITLE':
                        text = _plain(el)
                        if text:
                            code_heading = text
                            break
            yield from _annual_sections(root, parents, law_code, code_heading)
            return
        for el in root.iter():
            if _local(el.tag).upper() != 'DIV8':
                continue
            if (_attr(el, 'TYPE') or '').upper() != 'SECTION':
                continue
            num = _section_num(_attr(el, 'N') or '')
            text = _section_text(el)
            if not num or not text:
                continue
            row = {
                'COUNTRY': 'US',
                'SUBDIVISION': 'US',
                'LAW_CODE': law_code,
                'SECTION_NUM': num,
                'LEGAL_TEXT': text,
            }
            if code_heading:
                row['CODE_HEADING'] = code_heading
            row.update(_outline(el, parents))
            yield row

    def load(self, path, root=None):
        """Parse local title XML into ``data/codes/US/cfr/{title}.sqlite``.

        Replaces existing rows for that title so a second load does not
        duplicate. ``pk`` is ``{title}:{section}``; citation is
        ``{LAW_CODE} {section}``.
        """
        rows = list(self.sections(path))
        if not rows:
            raise ValueError('no CFR sections in %s' % path)
        law_code = rows[0]['LAW_CODE']
        title_num = _title_num_for_path(law_code)
        db_path = cfr_corpus_path(title_num, root=root)
        db = connect(db_path)
        try:
            db.execute('DELETE FROM section WHERE law_code = ?', (law_code,))
            db.executemany(
                'INSERT INTO section '
                '(pk, law_code, section_num, legal_text, citation, session) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                [
                    (
                        '%s:%s' % (law_code, row['SECTION_NUM']),
                        law_code,
                        row['SECTION_NUM'],
                        row['LEGAL_TEXT'],
                        '%s %s' % (law_code, row['SECTION_NUM']),
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
