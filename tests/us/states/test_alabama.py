"""Alabama distribution — local fixture only, no network."""

import os

from us.states.alabama import Alabama, AlabamaCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'alabama_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 13A-1-1. Short title. This title shall be known as the Alabama Criminal Code.</p>
<p>Section 13A-1-2. Definitions. Unless otherwise provided, the following terms apply.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Alabama.source == 'https://alison.legislature.state.al.us/code-of-alabama'


def test_list_editions_no_network():
    editions = Alabama().list_editions()
    assert editions == ['https://alison.legislature.state.al.us/code-of-alabama']


def test_accepts():
    assert AlabamaCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(AlabamaCode().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Alabama.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '13A-1-1'
        assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '13A-1-2'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
