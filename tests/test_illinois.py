"""Illinois distribution — local fixture only, no network."""

import os

from states.illinois import Illinois, IllinoisCompiledStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'illinois_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>(5 ILCS 5/1) (from Ch. 1, par. 301)</p>
<p>Sec. 1. Whenever Congress has adopted a proposal to amend the Constitution,
a joint resolution proposing ratification shall be considered.</p>
<p>(5 ILCS 5/2)</p>
<p>Sec. 2. Short title. This Act may be cited as the Federal Constitutional
Amendment Act.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Illinois.source == 'https://www.ilga.gov/ftp/ILCS/'


def test_list_editions_no_network():
    assert Illinois().list_editions() == ['https://www.ilga.gov/ftp/ILCS/']


def test_accepts():
    assert IllinoisCompiledStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(IllinoisCompiledStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '5 ILCS 5/1'
        assert 'Constitution' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '5 ILCS 5/2'
        assert 'Short title' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
