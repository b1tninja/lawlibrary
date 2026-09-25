"""Illinois distribution — local fixture only, no network."""

from pathlib import Path

from us.states.illinois import Illinois, IllinoisCompiledStatutes


def _write_fixture(tmp_path: Path):
    html = """<!DOCTYPE html>
<html><body>
<p>(5 ILCS 5/1) (from Ch. 1, par. 301)</p>
<p>Sec. 1. Whenever Congress has adopted a proposal to amend the Constitution,
a joint resolution proposing ratification shall be considered.</p>
<p>(5 ILCS 5/2)</p>
<p>Sec. 2. Short title. This Act may be cited as the Federal Constitutional
Amendment Act.</p>
</body></html>
"""
    path = tmp_path / 'illinois_fixture.html'
    path.write_text(html, encoding='utf-8')
    return path


def test_source():
    assert Illinois.source == 'https://www.ilga.gov/ftp/ILCS/'


def test_list_editions_no_network():
    assert Illinois().list_editions() == ['https://www.ilga.gov/ftp/ILCS/']


def test_accepts():
    assert IllinoisCompiledStatutes.accepts(set())


def test_sections_from_local_html(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(IllinoisCompiledStatutes().sections(path))
    assert len(rows) >= 2
    assert all(r['SUBDIVISION'] == Illinois.code for r in rows)
    assert all(r['LAW_CODE'] == 'ILCS' for r in rows)
    assert rows[0]['SECTION_NUM'] == '5 ILCS 5/1'
    assert 'Constitution' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '5 ILCS 5/2'
    assert 'Short title' in rows[1]['LEGAL_TEXT']
