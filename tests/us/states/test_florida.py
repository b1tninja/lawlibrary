"""Florida distribution — local fixture only, no network."""

from pathlib import Path

from us.states.florida import Florida, FloridaChapter


def _write_fixture(tmp_path: Path):
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
    path = tmp_path / 'florida_fixture.html'
    path.write_text(html, encoding='utf-8')
    return path


def test_source():
    assert Florida.source == 'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip'


def test_list_editions_no_network():
    assert Florida().list_editions() == [
        'https://www.leg.state.fl.us/Statutes/FLLawDL2026.zip',
    ]


def test_accepts():
    assert FloridaChapter.accepts('chapter.html')
    assert not FloridaChapter.accepts(set())


def test_sections_from_local_html(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(FloridaChapter().sections(path))
    assert len(rows) >= 2
    assert all(r['SUBDIVISION'] == Florida.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1.01'
    assert 'singular includes the plural' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1.02'
    assert 'Eastern standard time' in rows[1]['LEGAL_TEXT']
