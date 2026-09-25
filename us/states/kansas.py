"""Kansas Statutes — kslegislature.gov per-section JSON API."""

import json
import os

from publication import Publication, State

SOURCE = 'https://kslegislature.gov/b2025_26/api/v1/statutes/'
BOOK = 'KSA'


class KansasStatutes(Publication):
    code_heading = 'Kansas Statutes'
    """One saved K.S.A. section JSON object from /api/v1/statutes/{section}/."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        section = data.get('section') or data.get('SECTION_NUM')
        text = data.get('text') or data.get('LEGAL_TEXT') or ''
        if not section:
            section = os.path.splitext(os.path.basename(path))[0]
        row = {
            'SECTION_NUM': str(section),
            'LEGAL_TEXT': text,
            'SUBDIVISION': Kansas.code,
            'LAW_CODE': BOOK,
        }
        chapter = data.get('chapter')
        if chapter:
            row['CHAPTER'] = str(chapter)
        yield row


class Kansas(State):
    code = 'US-KS'
    source = SOURCE
    editions = (KansasStatutes,)

    def list_editions(self):
        return [SOURCE]
