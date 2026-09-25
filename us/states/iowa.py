"""Iowa Code — unofficial chapter XML from LSA publications.

The official code is eight volume PDFs; this edition does not parse those
PDFs. Chapter XML under
https://www.legis.iowa.gov/docs/publications/ICC/{year}/attachments/{chapter}_slim.xml
is the machine-readable form used here (labeled unofficial by the LSA).
"""

import os
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://www.legis.iowa.gov/docs/publications/ICC/2026/attachments/'


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _text_of(el):
    parts = [t for t in el.itertext() if t and t.strip()]
    return ' '.join(p.strip() for p in parts).strip()


def _section_num(el):
    for child in el.iter():
        if _local(child.tag) == 'identifier' or child.get('class') == 'identifier':
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


def _row(section_num, legal_text):
    return {
        'SECTION_NUM': section_num,
        'LEGAL_TEXT': legal_text,
        'SUBDIVISION': Iowa.code,
    }


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
            yield _row(stem, _text_of(root))
            return
        for el in section_els:
            text_els = [c for c in el if _local(c.tag) == 'Text']
            if text_els:
                body = _text_of(text_els[0])
            else:
                body = _text_of(el)
            num = _section_num(el) or os.path.splitext(os.path.basename(path))[0]
            yield _row(num, body)


class Iowa(State):
    code = 'US-IA'
    source = SOURCE
    editions = (IowaCode,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return IowaCode()
