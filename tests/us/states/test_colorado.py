"""Colorado distribution — local zip fixture only, no network."""

import zipfile
from pathlib import Path

from us.states.colorado import Colorado, ColoradoRevisedStatutes


def _write_fixture(tmp_path: Path):
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1-1-101. Short title. This title shall be known as the Colorado Revised Statutes.</p>
<p>Source: L. 92: Entire article R&amp;RE.</p>
<p>Editor's note: Former section relocated.</p>
<p>Annotator's note. Case law construing this section is omitted here.</p>
<p>Section 1-1-102. Construction. The provisions of this code shall be liberally construed.</p>
<p>Source: L. 92: Entire article R&amp;RE.</p>
</body></html>
"""
    path = tmp_path / 'colorado_fixture.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('title01.htm', html)
    return path


def test_source():
    assert Colorado.source == 'https://olls.info/crs/crs2026-htm.zip'


def test_list_editions_no_network():
    assert Colorado().list_editions() == ['https://olls.info/crs/crs2026-htm.zip']


def test_accepts_empty_dat_names():
    assert ColoradoRevisedStatutes.accepts(set())
    assert not ColoradoRevisedStatutes.accepts({'LAW_SECTION_TBL'})


def test_sections_from_local_zip(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(ColoradoRevisedStatutes().sections(path))
    assert len(rows) >= 2
    assert all(r['SUBDIVISION'] == Colorado.code for r in rows)
    assert rows[0]['SECTION_NUM'] == '1-1-101'
    assert 'Colorado Revised Statutes' in rows[0]['LEGAL_TEXT']
    assert 'Source:' not in rows[0]['LEGAL_TEXT']
    assert 'Annotator' not in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '1-1-102'
    assert 'liberally' in rows[1]['LEGAL_TEXT']
    assert 'Source:' not in rows[1]['LEGAL_TEXT']
