"""Rhode Island distribution — local fixture only, no network."""

import os

from us.states.rhode_island import RhodeIsland, RhodeIslandCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'rhode_island_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 11-1-1. Short title. This title shall be known as the Rhode Island Criminal Code.</p>
<p>Section 11-1-2. Definitions. Unless otherwise provided, the following terms apply.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert RhodeIsland.source == 'https://webserver.rilegislature.gov/statutes/Statutes.html'


def test_list_editions_no_network():
    editions = RhodeIsland().list_editions()
    assert editions == ['https://webserver.rilegislature.gov/statutes/Statutes.html']


def test_accepts():
    assert RhodeIslandCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(RhodeIslandCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '11-1-1'
        assert rows[0]['SUBDIVISION'] == 'US-RI'
        assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '11-1-2'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
