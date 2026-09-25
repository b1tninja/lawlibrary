"""New York distribution — local JSON fixture only; no live API, no invented key."""

import json
from pathlib import Path

from us.states.new_york import API_KEY_NOTE, NewYork, NewYorkLaws


def _write_fixture(tmp_path: Path):
    # Shape of a saved OpenLegislation law-document payload (text only).
    payload = {
        'success': True,
        'responseType': 'law-document',
        'result': {
            'lawId': 'PEN',
            'locationId': '1.00',
            'title': 'Short title',
            'text': 'Short title. This chapter shall be known as the Penal Law.',
        },
    }
    path = tmp_path / 'pen_1_00.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


def test_source():
    assert NewYork.source == 'https://legislation.nysenate.gov/api/3/laws'


def test_list_editions_notes_key():
    editions = NewYork().list_editions()
    assert editions == [API_KEY_NOTE]
    assert 'API key' in editions[0]


def test_accepts():
    assert NewYorkLaws.accepts(set())


def test_sections_from_local_json(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(NewYorkLaws().sections(path))
    assert len(rows) == 1
    assert rows[0]['SUBDIVISION'] == NewYork.code
    assert rows[0]['SECTION_NUM'] == '1.00'
    assert 'Penal Law' in rows[0]['LEGAL_TEXT']
