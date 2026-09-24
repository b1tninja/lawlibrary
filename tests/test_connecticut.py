"""Connecticut distribution — local fixture only, no network."""

import os

from states.connecticut import Connecticut, ConnecticutChapter

FIXTURE = os.path.join(os.path.dirname(__file__), 'connecticut_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p><span class="catchln" id="sec_1-1">Sec. 1-1. Words and phrases.</span> Words shall be construed according to common usage.</p>
<p><span class="catchln" id="sec_1-2">Sec. 1-2. Legal notices.</span> Notices shall be published as the law requires.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Connecticut.source == 'https://prdext2.cga.ct.gov/current/pub/titles.htm'


def test_list_editions_no_network():
    assert Connecticut().list_editions() == [
        'https://prdext2.cga.ct.gov/current/pub/titles.htm',
    ]


def test_accepts():
    assert ConnecticutChapter.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(ConnecticutChapter().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1-1'
        assert 'common usage' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-2'
        assert 'published' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
