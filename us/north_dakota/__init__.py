"""North Dakota Century Code — Legislative Council JSON API."""

import json

from publication import Publication, State


SOURCE = 'https://ndlegis.gov/api/data/century_code.json'


class NorthDakotaCode(Publication):
    """A local JSON list of objects with section and text fields."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            items = json.load(fh)
        for item in items:
            yield {
                'SECTION_NUM': str(item['section']),
                'LEGAL_TEXT': item['text'],
            }


class NorthDakota(State):
    code = 'US-ND'
    source = SOURCE
    editions = (NorthDakotaCode,)

    def list_editions(self):
        return [SOURCE]
