"""Louisiana distribution — local fixture only, no network."""

import os

from states.louisiana import Louisiana, LouisianaStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'louisiana_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>R.S. 14:30 First degree murder. First degree murder is the killing of a human being.</p>
<p>R.S. 14:67 Theft. Theft is the misappropriation or taking of anything of value.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Louisiana.source == 'https://legis.la.gov/legis/LawsContents.aspx'


def test_list_editions_no_network():
    editions = Louisiana().list_editions()
    assert editions == ['https://legis.la.gov/legis/LawsContents.aspx']


def test_accepts():
    assert LouisianaStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(LouisianaStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '14:30'
        assert 'First degree murder' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '14:67'
        assert 'Theft' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
