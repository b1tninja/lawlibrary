"""Ohio distribution — local fixture only, no network."""

import os

from us.ohio import Ohio, OhioRevisedCode

FIXTURE = os.path.join(os.path.dirname(__file__), 'ohio_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>§ 2901.01. Definitions. As used in the Revised Code, the following definitions apply.</p>
<p>§ 2901.02. Classification of offenses. Offenses include felonies and misdemeanors.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Ohio.source == 'https://codes.ohio.gov/ohio-revised-code'


def test_list_editions_no_network():
    assert Ohio().list_editions() == ['https://codes.ohio.gov/ohio-revised-code']


def test_accepts():
    assert OhioRevisedCode.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(OhioRevisedCode().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '2901.01'
        assert rows[0]['SUBDIVISION'] == 'US-OH'
        assert 'Definitions' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '2901.02'
        assert 'Classification' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
