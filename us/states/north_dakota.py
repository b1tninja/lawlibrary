"""North Dakota Century Code — Legislative Council JSON API."""

import json

from publication import Publication, State
from readers import text_sections

SOURCE = 'https://ndlegis.gov/api/data/century_code.json'
BOOK = 'NDCC'

# Section ids as line leaders after JSON is decoded to plain text.
_SECTION_PATTERN = r'(?m)^(\d[\d.]*(?:-\d[\d.]*)+)\.\s+'


def _iter_nested(data):
    """Walk titles → chapters → sections from the official century_code.json."""
    titles = data.get('titles') if isinstance(data, dict) else None
    if not isinstance(titles, dict):
        return
    for title in titles.values():
        if not isinstance(title, dict):
            continue
        chapters = title.get('chapters') or {}
        for chapter in chapters.values():
            if not isinstance(chapter, dict):
                continue
            sections = chapter.get('sections') or {}
            for section in sections.values():
                if not isinstance(section, dict):
                    continue
                number = section.get('id') or section.get('section')
                text = section.get('text') or ''
                if number and text:
                    yield {
                        'SECTION_NUM': str(number),
                        'LEGAL_TEXT': text,
                        'TITLE': str(title.get('title_num') or ''),
                        'TITLE_HEADING': title.get('title_name') or '',
                        'CHAPTER': str(chapter.get('chapter_num') or ''),
                        'CHAPTER_HEADING': chapter.get('chapter_title') or '',
                        'SECTION_TITLE': section.get('title') or '',
                    }


def _iter_flat(data):
    """Accept a list of {section|id, text} objects (test fixtures)."""
    if not isinstance(data, list):
        return
    for item in data:
        if not isinstance(item, dict):
            continue
        number = item.get('id') or item.get('section')
        text = item.get('text') or ''
        if number and text:
            yield str(number), text


def _json_to_text(data):
    """Flat JSON fixtures become numbered plain text for text_sections."""
    return '\n\n'.join('%s. %s' % pair for pair in _iter_flat(data))


class NorthDakotaCode(Publication):
    code_heading = 'North Dakota Century Code'
    """Local JSON: official nested century_code shape, or a flat list fixture."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        nested = list(_iter_nested(data))
        if nested:
            for row in nested:
                row['SUBDIVISION'] = NorthDakota.code
                row['LAW_CODE'] = BOOK
                yield row
            return
        text = _json_to_text(data)
        for row in text_sections(text, _SECTION_PATTERN):
            row['SUBDIVISION'] = NorthDakota.code
            row['LAW_CODE'] = BOOK
            yield row


class NorthDakota(State):
    code = 'US-ND'
    source = SOURCE
    editions = (NorthDakotaCode,)

    def list_editions(self):
        return [SOURCE]
