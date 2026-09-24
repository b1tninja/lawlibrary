"""West Virginia distribution — local fixture only, no network."""

import os

from us.west_virginia import WestVirginia, WestVirginiaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'west_virginia_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>§61-2-1. Murder defined. Murder by poison, lying in wait, or any other willful, deliberate and premeditated killing.</p>
<p>§61-2-2. Second degree murder. All other murder is murder of the second degree.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert WestVirginia.source == 'https://code.wvlegislature.gov/'


def test_list_editions_no_network():
    editions = WestVirginia().list_editions()
    assert editions == ['https://code.wvlegislature.gov/']


def test_accepts():
    assert WestVirginiaCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(WestVirginiaCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '61-2-1'
        assert 'Murder' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '61-2-2'
        assert 'second degree' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
