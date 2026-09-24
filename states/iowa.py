"""Iowa Code — LSA chapter XML (unofficial machine form of the code)."""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://www.legis.iowa.gov/law/iowaCode?year=2026'


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _text_of(el):
    parts = [t for t in el.itertext() if t and t.strip()]
    return ' '.join(p.strip() for p in parts).strip()


def _section_num(el):
    # Prefer an identifier child (slim chapter XML), then id, then stem later.
    for child in el.iter():
        if _local(child.tag) in ('identifier',) or (
            child.get('class') == 'identifier'
        ):
            value = ''.join(child.itertext()).strip()
            if value:
                return value
        attrs = child.attrib or {}
        if attrs.get('class') == 'identifier':
            value = ''.join(child.itertext()).strip()
            if value:
                return value
    sid = el.get('id') or ''
    if sid.startswith('sec'):
        return sid[3:]
    if sid:
        return sid
    return ''


class IowaCode(Publication):
    """One LSA chapter XML file (Section / Text when present)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        tree = ET.parse(path)
        root = tree.getroot()
        section_els = [el for el in root.iter() if _local(el.tag) == 'Section']
        if not section_els:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {'SECTION_NUM': stem, 'LEGAL_TEXT': _text_of(root)}
            return
        for el in section_els:
            text_els = [c for c in el if _local(c.tag) == 'Text']
            if text_els:
                body = _text_of(text_els[0])
            else:
                body = _text_of(el)
            num = _section_num(el) or os.path.splitext(os.path.basename(path))[0]
            yield {'SECTION_NUM': num, 'LEGAL_TEXT': body}


class Iowa(State):
    code = 'US-IA'
    source = SOURCE
    editions = (IowaCode,)

    def list_editions(self):
        return [SOURCE]
