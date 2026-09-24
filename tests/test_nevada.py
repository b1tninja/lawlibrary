"""Nevada distribution — local fixture only, no network."""

import os

from states.nevada import Nevada, NevadaRevisedStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'nevada_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>NRS 1.010 Courts of justice. The courts of justice of this State are:</p>
<p>NRS 1.020 Courts of record. The following are courts of record.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Nevada.source == 'https://www.leg.state.nv.us/nrs/'


def test_list_editions_no_network():
    assert Nevada().list_editions() == ['https://www.leg.state.nv.us/nrs/']


def test_accepts():
    assert NevadaRevisedStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(Nevada().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1.010'
        assert 'courts of justice' in rows[0]['LEGAL_TEXT'].lower()
        assert rows[1]['SECTION_NUM'] == '1.020'
        assert 'courts of record' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
