"""Shared statute file readers.

Yield plain section rows (`SECTION_NUM`, `LEGAL_TEXT`) from XML, HTML, or
plain text. Callers add jurisdiction fields such as `SUBDIVISION`.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import html2text


def _local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def _text_excluding(el, skip_tags):
    """Element text with named tags omitted; keep each skipped element's tail."""
    skip = {t.lower() for t in skip_tags}
    parts = []
    if el.text and el.text.strip():
        parts.append(el.text.strip())
    for child in list(el):
        tag = _local(child.tag).lower()
        if tag in skip:
            if child.tail and child.tail.strip():
                parts.append(child.tail.strip())
            continue
        nested = _text_excluding(child, skip_tags)
        if nested:
            parts.append(nested)
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return ' '.join(p for p in parts if p).strip()


def _section_number(el, number: str) -> str:
    value = el.get(number)
    if value and str(value).strip():
        return str(value).strip()
    for child in el:
        if _local(child.tag) == number:
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    for child in el.iter():
        if child is el:
            continue
        if _local(child.tag) == number:
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    return ''


def _named_text(el, name):
    """Attribute or direct-child text for ``name``."""
    value = el.get(name)
    if value and str(value).strip():
        return str(value).strip()
    for child in el:
        if _local(child.tag) == name:
            text = ''.join(child.itertext()).strip()
            if text:
                return text
    return ''


def xml_sections(path, *, section_tag, number, skip_tags=(), copies=()):
    """Yield dicts with SECTION_NUM and LEGAL_TEXT from an XML file.

    ``section_tag`` is matched on the element's local name. ``number`` is an
    attribute or child element. Text inside ``skip_tags`` is omitted; the
    skipped element's tail is kept. ``copies`` names attributes or direct
    children to copy onto the row under the same name.
    """
    root = ET.parse(path).getroot()
    for el in root.iter():
        if _local(el.tag) != section_tag:
            continue
        section_num = _section_number(el, number)
        legal_text = _text_excluding(el, skip_tags)
        row = {'SECTION_NUM': section_num, 'LEGAL_TEXT': legal_text}
        for name in copies:
            copied = _named_text(el, name)
            if copied:
                row[name] = copied
        yield row


def parent_map(root):
    """Child element to its parent. ElementTree does not keep that link."""
    return {child: node for node in root.iter() for child in node}


def html_sections(path, number_pattern):
    """Strip HTML to plain text, then split with ``text_sections``."""
    with open(path, encoding='utf-8', errors='replace') as fh:
        html = fh.read()
    text = html2text.HTML2Text(bodywidth=0).handle(html)
    yield from text_sections(text, number_pattern)


def text_sections(text, number_pattern):
    """Split plain text on ``number_pattern`` (one capture group for the number).

    Each match starts a section; LEGAL_TEXT is the text after the match until
    the next match (or end), stripped.
    """
    pattern = re.compile(number_pattern) if isinstance(number_pattern, str) else number_pattern
    matches = list(pattern.finditer(text or ''))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():end].strip()
        yield {'SECTION_NUM': match.group(1), 'LEGAL_TEXT': body}
