"""North Dakota distribution — local fixture only, no network."""

import json
import os

from states.north_dakota import NorthDakota, NorthDakotaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'north_dakota_fixture.json')


def _write_fixture():
    payload = [
        {
            'section': '12.1-01-01',
            'text': 'Title. This title shall be known as the North Dakota Criminal Code.',
        },
        {
            'section': '12.1-01-02',
            'text': 'General purposes. The general purposes of this title are to forbid conduct.',
        },
    ]
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh)
    return FIXTURE


def test_source():
    assert NorthDakota.source == 'https://ndlegis.gov/api/data/century_code.json'


def test_list_editions_no_network():
    assert NorthDakota().list_editions() == [
        'https://ndlegis.gov/api/data/century_code.json'
    ]


def test_accepts():
    assert NorthDakotaCode.accepts(set())


def test_sections_from_local_json():
    path = _write_fixture()
    try:
        rows = list(NorthDakotaCode().sections(path))
        assert len(rows) == 2
        assert rows[0]['SECTION_NUM'] == '12.1-01-01'
        assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '12.1-01-02'
        assert 'General purposes' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
