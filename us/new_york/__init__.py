"""New York Consolidated Laws — NYS Senate legislation API."""

import json
import os

from publication import Publication, State

SOURCE = 'https://legislation.nysenate.gov/api/3/laws'
# Free key from legislation.nysenate.gov; required as ?key= on every request.
API_KEY_NOTE = SOURCE + ' (API key required)'


def _section_num(obj, fallback):
    for key in ('locationId', 'section', 'SECTION_NUM', 'lawId'):
        value = obj.get(key)
        if value:
            return str(value)
    return fallback


def _text_of(obj):
    text = obj.get('text') or obj.get('LEGAL_TEXT') or ''
    return text if isinstance(text, str) else ''


def _yield_docs(obj, fallback):
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _yield_docs(item, '%s-%s' % (fallback, i))
        return
    if not isinstance(obj, dict):
        return
    text = _text_of(obj)
    if text.strip():
        yield {
            'SECTION_NUM': _section_num(obj, fallback),
            'LEGAL_TEXT': text,
            'SUBDIVISION': NewYork.code,
        }
        return
    # OpenLegislation wrappers: result / documents / items / documents tree.
    for key in ('result', 'documents', 'items'):
        if key in obj:
            yield from _yield_docs(obj[key], fallback)
            return
    for child in obj.values():
        if isinstance(child, (dict, list)):
            yield from _yield_docs(child, fallback)


class NewYorkLaws(Publication):
    """One saved API JSON object (local fixture). Does not call the live API."""

    @classmethod
    def accepts(cls, names):
        return True

    def sections(self, path):
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        stem = os.path.splitext(os.path.basename(path))[0]
        rows = list(_yield_docs(data, stem))
        if rows:
            yield from rows
            return
        yield {
            'SECTION_NUM': stem,
            'LEGAL_TEXT': '',
            'SUBDIVISION': NewYork.code,
        }


class NewYork(State):
    code = 'US-NY'
    source = SOURCE
    editions = (NewYorkLaws,)

    def list_editions(self):
        # Key is free from the Senate; this project does not invent or store one.
        return [API_KEY_NOTE]
