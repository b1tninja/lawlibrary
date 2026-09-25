"""South Dakota Codified Laws — legislature Statutes JSON API."""

import json
import os

import html2text

from publication import Publication, State

SOURCE = 'https://sdlegislature.gov/api/Statutes/'
BOOK = 'SDCL'


def _label(value):
    if value is None:
        return ''
    return str(value).strip()


def _html_to_text(html):
    return html2text.HTML2Text(bodywidth=0).handle(html or '').strip()


class SouthDakotaCode(Publication):
    code_heading = 'South Dakota Codified Laws'
    """One saved /api/Statutes/Statute/{cite} JSON object."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        section = data.get('Statute') or data.get('section') or data.get('SECTION_NUM')
        if not section:
            section = os.path.splitext(os.path.basename(path))[0]
        raw = data.get('text') or data.get('LEGAL_TEXT') or data.get('Html') or ''
        text = _html_to_text(raw) if '<' in raw else (raw or '').strip()
        row = {
            'SECTION_NUM': str(section),
            'LEGAL_TEXT': text,
            'SUBDIVISION': SouthDakota.code,
            'LAW_CODE': BOOK,
        }
        title = _label(data.get('Title'))
        chapter = _label(data.get('Chapter'))
        article = _label(data.get('Article'))
        catch = _label(data.get('CatchLine'))
        if title:
            row['TITLE'] = title
        if chapter:
            row['CHAPTER'] = chapter
        if article:
            row['ARTICLE'] = article
        if catch:
            row['SECTION_TITLE'] = catch
        yield row


class SouthDakota(State):
    code = 'US-SD'
    source = SOURCE
    editions = (SouthDakotaCode,)

    def list_editions(self):
        return [SOURCE]
