"""New York Consolidated Laws — NYS Senate legislation API."""

import json
import os

from publication import Publication, State


SOURCE = 'https://legislation.nysenate.gov/api/3/laws'


class NewYorkLaws(Publication):
    """One saved API JSON object with a text field (local fixture / download)."""

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
        yield {'SECTION_NUM': str(section), 'LEGAL_TEXT': text}


class NewYork(State):
    code = 'US-NY'
    source = SOURCE
    editions = (NewYorkLaws,)

    def list_editions(self):
        return [SOURCE]
