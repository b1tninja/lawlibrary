"""Wisconsin distribution — local fixture only, no network."""

import os

from us.wisconsin import Wisconsin, WisconsinStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'wisconsin_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1.01. Construction of laws; words and phrases. In the construction of Wisconsin laws the words and phrases shall be construed according to common usage.</p>
<p>Section 1.10. State song, state dance, and state symbols. The Wisconsin state song is "On, Wisconsin".</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Wisconsin.source == 'https://docs.legis.wisconsin.gov/statutes/statutes/'


def test_list_editions_no_network():
    editions = Wisconsin().list_editions()
    assert editions == ['https://docs.legis.wisconsin.gov/statutes/statutes/']


def test_accepts():
    assert WisconsinStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(WisconsinStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1.01'
        assert 'Construction' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1.10'
        assert 'On, Wisconsin' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
