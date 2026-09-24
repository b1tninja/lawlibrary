"""Texas distribution — local zip fixture only, no network."""

import zipfile
from pathlib import Path

from us.texas import Texas, TexasStatutes


def _write_fixture(tmp_path: Path):
    html = """<!DOCTYPE html>
<html><body>
<p>Sec. 1.001. PURPOSE. This code consolidates the statutes relating to property.</p>
<p>Sec. 1.002. CONSTRUCTION. The Code Construction Act applies to this code.</p>
</body></html>
"""
    path = tmp_path / 'property.zip'
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('property.htm', html)
    return path


def test_source():
    assert Texas.source == 'https://statutes.capitol.texas.gov/download'


def test_list_editions_no_network():
    assert Texas().list_editions() == ['https://statutes.capitol.texas.gov/download']


def test_accepts():
    assert TexasStatutes.accepts(set())


def test_sections_from_local_zip(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(TexasStatutes().sections(path))
    assert len(rows) == 2
    assert rows[0]['SECTION_NUM'] == '1.001'
    assert 'property' in rows[0]['LEGAL_TEXT'].lower()
    assert rows[1]['SECTION_NUM'] == '1.002'
    assert 'Construction' in rows[1]['LEGAL_TEXT']
