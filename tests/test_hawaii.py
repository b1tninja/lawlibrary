"""Hawaii distribution — local fixture only, no network."""

import os

from states.hawaii import Hawaii, HawaiiChapter

FIXTURE = os.path.join(os.path.dirname(__file__), 'hawaii_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p class="RegularParagraphs"><b>§1-1 Common law of the State; exceptions.</b>
The common law of England is declared to be the common law of the State of Hawaii.</p>
<p class="RegularParagraphs"><b>§1-2 Certain laws not obligatory until published.</b>
No law shall be obligatory until published.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Hawaii.source == 'https://data.capitol.hawaii.gov/hrscurrent/'


def test_list_editions_no_network():
    assert Hawaii().list_editions() == [
        'https://data.capitol.hawaii.gov/hrscurrent/',
    ]


def test_accepts():
    assert HawaiiChapter.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(HawaiiChapter().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1-1'
        assert 'common law of England' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-2'
        assert 'obligatory until published' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
