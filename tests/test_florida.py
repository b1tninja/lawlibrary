"""Florida distribution — local fixture only, no network."""

import os

from states.florida import Florida, FloridaChapter

FIXTURE = os.path.join(os.path.dirname(__file__), 'florida_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<div class="Section">
  <span class="SectionNumber">1.01</span>
  <span class="Catchline">Definitions.</span>
  <span class="SectionBody">In construing these statutes the singular includes the plural.</span>
</div>
<div class="Section">
  <span class="SectionNumber">1.02</span>
  <span class="Catchline">Legal time.</span>
  <span class="SectionBody">Eastern standard time is the legal time of Florida.</span>
</div>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Florida.source == 'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip'


def test_list_editions_no_network():
    assert Florida().list_editions() == [
        'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip',
    ]


def test_accepts():
    assert FloridaChapter.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(FloridaChapter().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1.01'
        assert 'singular includes the plural' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1.02'
        assert 'Eastern standard time' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
