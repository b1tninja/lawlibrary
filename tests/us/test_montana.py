"""Montana distribution — local fixture only, no network."""

import os

from us.montana import Montana, MontanaCodeAnnotated

FIXTURE = os.path.join(os.path.dirname(__file__), 'montana_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1-1-101. Name of code. These codes shall be known as the Montana Code Annotated.</p>
<p>Section 1-1-102. Intentions of the legislature. In the construction of a statute, the intention of the legislature is to be pursued if possible.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Montana.source == 'https://mca.legmt.gov/bills/mca/'


def test_list_editions_no_network():
    assert Montana().list_editions() == ['https://mca.legmt.gov/bills/mca/']


def test_accepts():
    assert MontanaCodeAnnotated.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(MontanaCodeAnnotated().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Montana.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '1-1-101'
        assert 'Montana Code Annotated' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-1-102'
        assert 'legislature' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
