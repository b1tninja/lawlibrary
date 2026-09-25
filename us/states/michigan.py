"""Michigan Compiled Laws — legislature chapter XML directory.

Chapter XML files under https://www.legislature.mi.gov/documents/mcl/
(UTF-16; section body is BodyText on MCLSectionInfo). Not one zip.
"""

import xml.etree.ElementTree as ET

import html2text

from publication import Publication, State
from readers import parent_map

SOURCE = 'https://www.legislature.mi.gov/documents/mcl/'

# Short book token for the Compiled Laws (not the ISO subdivision).
LAW_CODE = 'MCL'

# DivisionType words that match a LawSchema level. A closer ancestor wins.
_LEVELS = {
    'DIVISION': 'DIVISION',
    'TITLE': 'TITLE',
    'PART': 'PART',
    'CHAPTER': 'CHAPTER',
    'ARTICLE': 'ARTICLE',
}

_HTML = html2text.HTML2Text(bodywidth=0)
_HTML.ignore_links = True


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _plain(html):
    if not html or not str(html).strip():
        return ''
    text = str(html).strip()
    if '<' not in text:
        return text
    return _HTML.handle(text).strip()


def _child_text(el, name):
    for child in el:
        if _local(child.tag) == name:
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    return ''


def _put_level(fields, key, number, heading):
    if key in fields:
        return
    if number:
        fields[key] = number
    if heading:
        fields['%s_HEADING' % key] = heading


def _outline(el, parents):
    """Chapter and division labels that contain this section."""
    fields = {}
    catch = _child_text(el, 'CatchLine')
    if catch:
        fields['SECTION_TITLE'] = catch
    cur = parents.get(el)
    while cur is not None:
        tag = _local(cur.tag)
        if tag == 'MCLDivisionInfo':
            kind = (_child_text(cur, 'DivisionType') or '').strip().upper()
            key = _LEVELS.get(kind)
            if key:
                _put_level(
                    fields,
                    key,
                    _child_text(cur, 'DivisionNumber'),
                    _child_text(cur, 'DivisionTitle'),
                )
        elif tag in ('MCLChapterInfo', 'Chapter'):
            _put_level(
                fields,
                'CHAPTER',
                _child_text(cur, 'Name') or cur.get('number') or '',
                _child_text(cur, 'Title') or cur.get('title') or '',
            )
        cur = parents.get(cur)
    return fields


def _parse_root(path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        with open(path, 'rb') as fh:
            raw = fh.read()
        text = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8')
        return ET.fromstring(text)


class MichiganCompiledLaws(Publication):
    code_heading = 'Michigan Compiled Laws'
    """One local MCL chapter XML file; section body is BodyText."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        root = _parse_root(path)
        parents = parent_map(root)
        for el in root.iter():
            tag = _local(el.tag)
            # Official: MCLSectionInfo. Fixture: Section.
            if tag not in ('MCLSectionInfo', 'Section'):
                continue
            section_num = _child_text(el, 'MCLNumber') or _child_text(el, 'SectionNumber')
            body = _child_text(el, 'BodyText')
            if tag == 'MCLSectionInfo':
                # Official chapter XML: statute words live only in BodyText.
                legal_text = _plain(body)
            else:
                # Fixture <Section><BodyText>… or bare section text.
                legal_text = _plain(body) if body else _plain(''.join(el.itertext()))
            if not section_num or not legal_text:
                continue
            row = {
                'PK': '%s:%s' % (LAW_CODE, section_num),
                'LAW_CODE': LAW_CODE,
                'SECTION_NUM': section_num,
                'LEGAL_TEXT': legal_text,
                'SUBDIVISION': Michigan.code,
            }
            row.update(_outline(el, parents))
            yield row


class Michigan(State):
    code = 'US-MI'
    source = SOURCE
    editions = (MichiganCompiledLaws,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return MichiganCompiledLaws()
