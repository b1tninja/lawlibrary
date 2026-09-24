"""New York distribution — local fixture only, no network."""

import json
import os

from us.new_york import NewYork, NewYorkLaws

FIXTURE = os.path.join(os.path.dirname(__file__), 'new_york_fixture.json')


def _write_fixture():
    payload = {
        'section': '1.01',
        'text': 'Short title. This chapter shall be known as the Penal Law.',
    }
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh)
    return FIXTURE


def test_source():
    assert NewYork.source == 'https://legislation.nysenate.gov/api/3/laws'


def test_list_editions_no_network():
    assert NewYork().list_editions() == ['https://legislation.nysenate.gov/api/3/laws']


def test_accepts():
    assert NewYorkLaws.accepts(set())


def test_sections_from_local_json():
    path = _write_fixture()
    try:
        rows = list(NewYorkLaws().sections(path))
        assert len(rows) == 1
        assert rows[0]['SECTION_NUM'] == '1.01'
        assert 'Penal Law' in rows[0]['LEGAL_TEXT']
    finally:
        os.remove(path)
