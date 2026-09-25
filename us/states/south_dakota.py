"""South Dakota Codified Laws — legislature Statutes JSON API."""

import json
import os

from publication import Publication, State


SOURCE = 'https://sdlegislature.gov/Statutes'


class SouthDakotaCode(Publication):
    """One saved API JSON object with text and section fields."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        text = data['text']
        section = data.get('section') or data.get('SECTION_NUM')
        if not section:
            section = os.path.splitext(os.path.basename(path))[0]
        yield {'SECTION_NUM': str(section), 'LEGAL_TEXT': text, 'SUBDIVISION': 'US-SD'}


class SouthDakota(State):
    code = 'US-SD'
    source = SOURCE
    editions = (SouthDakotaCode,)

    def list_editions(self):
        return [SOURCE]
