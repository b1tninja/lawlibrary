"""Colorado distribution — local zip fixture only, no network."""

import os
import zipfile

from us.colorado import Colorado, ColoradoRevisedStatutes

FIXTURE = os.path.join(os.path.dirname(__file__), 'colorado_fixture.zip')


def _write_fixture():
    html = """<!DOCTYPE html>
<html><body>
<p>Section 1-1-101. Short title. This title shall be known as the Colorado Revised Statutes.</p>
<p>Section 1-1-102. Construction. The provisions of this code shall be liberally construed.</p>
</body></html>
"""
    with zipfile.ZipFile(FIXTURE, 'w') as zf:
        zf.writestr('title01.htm', html)
    return FIXTURE


def test_source():
    assert Colorado.source == 'https://olls.info/crs/crs2026-htm.zip'


def test_list_editions_no_network():
    assert Colorado().list_editions() == ['https://olls.info/crs/crs2026-htm.zip']


def test_accepts_empty_dat_names():
    assert ColoradoRevisedStatutes.accepts(set())
    assert not ColoradoRevisedStatutes.accepts({'LAW_SECTION_TBL'})


def test_sections_from_local_zip():
    path = _write_fixture()
    try:
        rows = list(ColoradoRevisedStatutes().sections(path))
        assert len(rows) >= 2
        assert rows[0]['SECTION_NUM'] == '1-1-101'
        assert 'Colorado Revised Statutes' in rows[0]['LEGAL_TEXT']
        assert rows[1]['SECTION_NUM'] == '1-1-102'
        assert 'liberally' in rows[1]['LEGAL_TEXT']
    finally:
        os.remove(path)
