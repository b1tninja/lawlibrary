"""South Dakota distribution — local JSON fixture only, no network."""

import json
from pathlib import Path

from us.states.south_dakota import SouthDakota, SouthDakotaCode


def _write_fixture(tmp_path: Path):
    path = tmp_path / '17-1-1.json'
    path.write_text(
        json.dumps({
            'Statute': '17-1-1',
            'Title': 17,
            'Chapter': 1,
            'CatchLine': 'Kinds of notice.',
            'Type': 'Section',
            'Html': '<p>Notice is either actual or constructive.</p>',
        }),
        encoding='utf-8',
    )
    return path


def test_source():
    assert SouthDakota.source == 'https://sdlegislature.gov/api/Statutes/'


def test_list_editions_no_network():
    assert SouthDakota().list_editions() == [
        'https://sdlegislature.gov/api/Statutes/'
    ]


def test_accepts():
    assert SouthDakotaCode.accepts(set())


def test_sections_from_local_json(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(SouthDakotaCode().sections(path))
    assert len(rows) == 1
    assert rows[0]['SECTION_NUM'] == '17-1-1'
    assert rows[0]['TITLE'] == '17'
    assert rows[0]['CHAPTER'] == '1'
    assert rows[0]['SECTION_TITLE'] == 'Kinds of notice.'
    assert rows[0]['SUBDIVISION'] == SouthDakota.code
    assert rows[0]['LAW_CODE'] == 'SDCL'
    assert 'actual or constructive' in rows[0]['LEGAL_TEXT']
