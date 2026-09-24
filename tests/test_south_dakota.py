"""South Dakota distribution — local fixture only, no network."""

import json
import os

from states.south_dakota import SouthDakota, SouthDakotaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'south_dakota_fixture.json')


def _write_fixture():
    payload = {
        'section': '22-1-1',
        'text': 'Short title. This title shall be known as the South Dakota Criminal Code.',
    }
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh)
    return FIXTURE


def test_source():
    assert SouthDakota.source == 'https://sdlegislature.gov/Statutes'


def test_list_editions_no_network():
    assert SouthDakota().list_editions() == ['https://sdlegislature.gov/Statutes']


def test_accepts():
    assert SouthDakotaCode.accepts(set())


def test_sections_from_local_json():
    path = _write_fixture()
    try:
        rows = list(SouthDakotaCode().sections(path))
        assert len(rows) == 1
        assert rows[0]['SECTION_NUM'] == '22-1-1'
        assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
    finally:
        os.remove(path)
