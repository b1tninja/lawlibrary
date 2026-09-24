"""North Carolina distribution — local fixture only, no network."""

import os

from states.north_carolina import NorthCarolina, NorthCarolinaChapter

FIXTURE = os.path.join(os.path.dirname(__file__), 'north_carolina_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>§ 14-1. Felonies and misdemeanors defined. A felony is a crime punishable by death or imprisonment.</p>
<p>§ 14-2. Punishment for felony. Every person convicted of a felony shall be punished as provided by law.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert NorthCarolina.source == 'https://www.ncleg.gov/Laws/GeneralStatutesTOC'


def test_list_editions_no_network():
    assert NorthCarolina().list_editions() == [
        'https://www.ncleg.gov/Laws/GeneralStatutesTOC'
    ]


def test_accepts():
    assert NorthCarolinaChapter.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(NorthCarolinaChapter().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '14-1'
        assert 'Felonies' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '14-2'
        assert 'Punishment' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
