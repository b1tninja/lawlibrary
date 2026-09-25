"""Kansas distribution — local JSON fixture only, no network."""

import json
from pathlib import Path

from us.states.kansas import Kansas, KansasStatutes


def _write_fixture(tmp_path: Path):
    path = tmp_path / '21-5801.json'
    path.write_text(
        json.dumps({
            'section': '21-5801',
            'chapter': '21',
            'rest': '5801',
            'text': '21-5801. Theft. Theft is obtaining unauthorized control over property.',
            'url': '/laws/21_000_0000_chapter/',
        }),
        encoding='utf-8',
    )
    return path


def test_source():
    assert Kansas.source == 'https://kslegislature.gov/b2025_26/api/v1/statutes/'


def test_list_editions_no_network():
    assert Kansas().list_editions() == [
        'https://kslegislature.gov/b2025_26/api/v1/statutes/'
    ]


def test_accepts():
    assert KansasStatutes.accepts(set())


def test_sections_from_local_json(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(KansasStatutes().sections(path))
    assert len(rows) == 1
    assert rows[0]['SUBDIVISION'] == Kansas.code
    assert rows[0]['LAW_CODE'] == 'KSA'
    assert rows[0]['SECTION_NUM'] == '21-5801'
    assert rows[0]['CHAPTER'] == '21'
    assert 'Theft' in rows[0]['LEGAL_TEXT']
