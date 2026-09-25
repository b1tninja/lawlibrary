"""Maryland distribution — local fixture only, no network."""

import os

from us.maryland import Maryland, MarylandStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'maryland_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>§ 1-101. Definitions. In this article the following words have the meanings indicated.</p>
<p>§ 1-201. Scope. This title applies to residential property in the State.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Maryland.source == 'https://mgaleg.maryland.gov/mgawebsite/laws/statutes'


def test_list_editions_no_network():
    editions = Maryland().list_editions()
    assert editions == ['https://mgaleg.maryland.gov/mgawebsite/laws/statutes']


def test_accepts():
    assert MarylandStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(MarylandStatutes().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Maryland.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '1-101'
        assert 'Definitions' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-201'
        assert 'residential' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
