"""Massachusetts distribution — local fixture only, no network."""

import os

from states.massachusetts import Massachusetts, MassachusettsGeneralLaws

FIXTURE = os.path.join(os.path.dirname(__file__), 'massachusetts_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1. Short title. This chapter shall be known as the consumer protection act.</p>
<p>Section 2. Unfair practices. Unfair methods of competition and unfair or deceptive acts are unlawful.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Massachusetts.source == 'https://malegislature.gov/Laws/GeneralLaws/'


def test_list_editions_no_network():
    editions = Massachusetts().list_editions()
    assert editions == ['https://malegislature.gov/Laws/GeneralLaws/']


def test_accepts():
    assert MassachusettsGeneralLaws.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(MassachusettsGeneralLaws().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1'
        assert 'consumer protection' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '2'
        assert 'Unfair' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
