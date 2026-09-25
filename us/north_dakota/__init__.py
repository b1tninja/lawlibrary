"""North Dakota Century Code — Legislative Council JSON API."""

import json
import os

from publication import Publication, State

SOURCE = 'https://ndlegis.gov/api/data/century_code.json'


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
                    yield str(number), text


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


class NorthDakotaCode(Publication):
    """Local JSON: official nested century_code shape, or a flat list fixture."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        rows = list(_iter_nested(data)) or list(_iter_flat(data))
        if not rows:
            stem = os.path.splitext(os.path.basename(path))[0]
            yield {
                'SECTION_NUM': stem,
                'LEGAL_TEXT': '',
                'SUBDIVISION': NorthDakota.code,
            }
            return
        for number, text in rows:
            yield {
                'SECTION_NUM': number,
                'LEGAL_TEXT': text,
                'SUBDIVISION': NorthDakota.code,
            }


class NorthDakota(State):
    code = 'US-ND'
    source = SOURCE
    editions = (NorthDakotaCode,)

    def list_editions(self):
        return [SOURCE]
