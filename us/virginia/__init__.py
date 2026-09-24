"""Virginia Code — LIS law library CSV and API."""

import csv

from publication import Publication, State

SOURCE = 'https://law.lis.virginia.gov/law-library/'


class VirginiaCode(Publication):
    """One title CSV with columns section,text (annotations excluded)."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8', errors='replace', newline='') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                number = (row.get('section') or '').strip()
                text = (row.get('text') or '').strip()
                if number or text:
                    yield {'SECTION_NUM': number, 'LEGAL_TEXT': text}


class Virginia(State):
    code = 'US-VA'
    source = SOURCE
    editions = (VirginiaCode,)

    def list_editions(self):
        return [SOURCE]
