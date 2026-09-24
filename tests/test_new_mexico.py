"""New Mexico distribution — local fixture only, no network."""

import os

from states.new_mexico import NewMexico, NewMexicoStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'new_mexico_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 30-1-1. Short title. This chapter may be cited as the Criminal Code.</p>
<p>Section 30-1-2. Definitions. As used in the Criminal Code, the following terms apply.</p>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert NewMexico.source == 'https://nmonesource.com/'


def test_list_editions_no_network():
    assert NewMexico().list_editions() == ['https://nmonesource.com/']


def test_accepts():
    assert NewMexicoStatutes.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(NewMexico().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '30-1-1'
        assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '30-1-2'
        assert 'Definitions' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
