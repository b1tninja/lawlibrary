"""North Dakota distribution — tiny synthetic JSON string; no committed fixture file."""

import json
from pathlib import Path

from us.states.north_dakota import NorthDakota, NorthDakotaCode

# Nested shape matches https://ndlegis.gov/api/data/century_code.json
SYNTHETIC = """{
  "last_updated": "2026-01-01T00:00:00",
  "titles": {
    "12.1": {
      "title_num": "12.1",
      "title_name": "Criminal Code",
      "chapters": {
        "01": {
          "id": "12.1-01",
          "chapter_num": "01",
          "chapter_title": "General Provisions",
          "sections": {
            "01": {
              "id": "12.1-01-01",
              "section_num": "01",
              "title": "Title",
              "text": "This title shall be known as the North Dakota Criminal Code."
            },
            "02": {
              "id": "12.1-01-02",
              "section_num": "02",
              "title": "General purposes",
              "text": "General purposes. The general purposes of this title are to forbid conduct."
            }
          }
        }
      }
    }
  }
}"""


def _write_fixture(tmp_path: Path):
    path = tmp_path / 'century_code.json'
    # Round-trip to prove it is valid JSON while keeping the string in the test.
    path.write_text(json.dumps(json.loads(SYNTHETIC)), encoding='utf-8')
    return path


def test_source():
    assert NorthDakota.source == 'https://ndlegis.gov/api/data/century_code.json'


def test_list_editions_no_network():
    assert NorthDakota().list_editions() == [
        'https://ndlegis.gov/api/data/century_code.json'
    ]


def test_accepts():
    assert NorthDakotaCode.accepts(set())


def test_sections_from_synthetic_json(tmp_path):
    path = _write_fixture(tmp_path)
    rows = list(NorthDakotaCode().sections(path))
    assert len(rows) == 2
    assert all(r['SUBDIVISION'] == NorthDakota.code for r in rows)
    assert all(r['LAW_CODE'] == 'NDCC' for r in rows)
    assert rows[0]['SECTION_NUM'] == '12.1-01-01'
    assert rows[0]['TITLE'] == '12.1'
    assert rows[0]['TITLE_HEADING'] == 'Criminal Code'
    assert rows[0]['CHAPTER_HEADING'] == 'General Provisions'
    assert 'Criminal Code' in rows[0]['LEGAL_TEXT']
    assert rows[1]['SECTION_NUM'] == '12.1-01-02'
    assert 'General purposes' in rows[1]['LEGAL_TEXT']
