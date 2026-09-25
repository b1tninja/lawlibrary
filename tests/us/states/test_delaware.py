"""Delaware distribution — local fixture only, no network."""

import os

from us.states.delaware import Delaware, DelawareChapter

FIXTURE = os.path.join(os.path.dirname(__file__), 'delaware_fixture.html')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<div class="Section">
  <div class="SectionHead" id="101">§ 101. Designation and citation of Code.</div>
  <p class="subsection">The laws shall constitute the Delaware Code.</p>
</div>
<div class="Section">
  <div class="SectionHead" id="102">§ 102. Effective date of Code.</div>
  <p class="subsection">This Code shall become effective upon enactment.</p>
</div>
</body></html>
"""
    with open(FIXTURE, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return FIXTURE


def test_source():
    assert Delaware.source == 'https://delcode.delaware.gov/'


def test_list_editions_no_network():
    assert Delaware().list_editions() == [
        'https://delcode.delaware.gov/title1/title1.pdf',
    ]


def test_accepts():
    assert DelawareChapter.accepts(set())


def test_sections_from_local_html():
    path = _write_fixture()
    try:
        rows = list(DelawareChapter().sections(path))
        assert len(rows) >= 2
        assert all(r['SUBDIVISION'] == Delaware.code for r in rows)
        assert rows[0]['SECTION_NUM'] == '101'
        assert 'Delaware Code' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '102'
        assert 'effective' in rows[1]['LEGAL_TEXT'].lower()
    finally:
        os.remove(path)
