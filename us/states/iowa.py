"""Iowa Code — unofficial chapter XML from LSA publications.

The official code is eight volume PDFs; this edition does not parse those
PDFs. Chapter XML under
https://www.legis.iowa.gov/docs/publications/ICC/{year}/attachments/{chapter}_slim.xml
is the machine-readable form used here (labeled unofficial by the LSA).
"""

import re
import xml.etree.ElementTree as ET

from publication import Publication, State

SOURCE = 'https://www.legis.iowa.gov/docs/publications/ICC/2026/attachments/'

# Short book token for the Iowa Code (not the ISO subdivision).
LAW_CODE = 'IC'

_ID_SECTION = re.compile(r'^sec(.+)$', re.IGNORECASE)
_CHAPTER_HEAD = re.compile(r'^(\d+[A-Za-z]?)(?:\s+|(?=[A-Z]))(.*)$')
_SKIP_CLASSES = frozenset({'history', 'historyitem', 'footnotes', 'footnote', 'toc', 'about'})


def _local(tag):
    return tag.rsplit('}', 1)[-1]


def _classes(el):
    return {c.lower() for c in (el.get('class') or '').split()}


def _identifier_from_span(el):
    """Official slim XML puts the cite in xhtml:span class='identifier'."""
    for child in el.iter():
        if _local(child.tag).lower() != 'span':
            continue
        if 'identifier' not in _classes(child):
            continue
        text = ''.join(child.itertext()).strip()
        if text:
            return text
    return ''


def _section_num(el):
    # Fixture: <identifier>1.1</identifier>
    for child in el:
        if _local(child.tag) == 'identifier':
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    number = _identifier_from_span(el)
    if number:
        return number
    section_id = el.get('id') or ''
    match = _ID_SECTION.match(section_id.strip())
    if match:
        return match.group(1)
    return ''


def _chapter(root):
    """Chapter number and heading printed once on the chapter file."""
    for el in root.iter():
        if _local(el.tag) != 'Heading':
            continue
        if 'heading' not in _classes(el) and el.get('class'):
            continue
        text = ' '.join(''.join(el.itertext()).split())
        match = _CHAPTER_HEAD.match(text)
        if match:
            return match.group(1), match.group(2).strip()
        if text:
            return '', text
    return '', ''


def _headnote(el):
    for child in el.iter():
        if 'headnote' in _classes(child):
            text = ' '.join(''.join(child.itertext()).split())
            if text:
                return text
    return ''


def _body_text(el):
    """Statute words only: skip history/footnote blocks; keep para and Text."""
    parts = []
    if el.text and el.text.strip():
        parts.append(el.text.strip())
    for child in list(el):
        tag = _local(child.tag)
        klass = _classes(child)
        if klass & _SKIP_CLASSES or tag.lower() in _SKIP_CLASSES:
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
            continue
        # Heading identifiers are the section number, not the body.
        if 'headnote' in klass or ('heading' in klass and tag.lower() == 'div'):
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
            continue
        nested = _body_text(child)
        if nested:
            parts.append(nested)
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return ' '.join(p for p in parts if p).strip()


class IowaCode(Publication):
    code_heading = 'Iowa Code'
    """One LSA chapter XML file (Section / Text when present)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        root = ET.parse(path).getroot()
        chapter, chapter_heading = _chapter(root)
        for el in root.iter():
            if _local(el.tag) != 'Section':
                continue
            section_num = _section_num(el)
            legal_text = _body_text(el)
            if not section_num or not legal_text:
                continue
            row = {
                'PK': '%s:%s' % (LAW_CODE, section_num),
                'LAW_CODE': LAW_CODE,
                'SECTION_NUM': section_num,
                'LEGAL_TEXT': legal_text,
                'SUBDIVISION': Iowa.code,
            }
            if chapter:
                row['CHAPTER'] = chapter
            if chapter_heading:
                row['CHAPTER_HEADING'] = chapter_heading
            title = _headnote(el)
            if title:
                row['SECTION_TITLE'] = title
            yield row


class Iowa(State):
    code = 'US-IA'
    source = SOURCE
    editions = (IowaCode,)

    def list_editions(self):
        return [SOURCE]

    def edition(self, path):
        return IowaCode()
