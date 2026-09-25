"""Shared statute readers — synthetic fixtures only."""

from pathlib import Path

from readers import html_sections, text_sections, xml_sections


def test_xml_sections_skips_annotation(tmp_path: Path):
    path = tmp_path / 'sample.xml'
    path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
        <book>
          <section number="1-1">
            <para>Keep the operative words.</para>
            <annotation>Skip this annotation note.</annotation> keep the tail.
          </section>
        </book>
        """,
        encoding='utf-8',
    )
    rows = list(
        xml_sections(
            path,
            section_tag='section',
            number='number',
            skip_tags=('annotation',),
        )
    )
    assert len(rows) == 1
    assert rows[0]['SECTION_NUM'] == '1-1'
    assert 'operative words' in rows[0]['LEGAL_TEXT']
    assert 'keep the tail' in rows[0]['LEGAL_TEXT']
    assert 'annotation note' not in rows[0]['LEGAL_TEXT']


def test_html_sections_strips_tags_and_splits(tmp_path: Path):
    path = tmp_path / 'sample.html'
    path.write_text(
        '<html><body><p>Section 10 <span>Alpha</span> body.</p></body></html>',
        encoding='utf-8',
    )
    rows = list(html_sections(path, r'Section\s+(\d+)'))
    assert len(rows) == 1
    assert rows[0]['SECTION_NUM'] == '10'
    assert 'Alpha' in rows[0]['LEGAL_TEXT']
    assert 'body' in rows[0]['LEGAL_TEXT']


def test_text_sections_two_numbers():
    text = 'Section 1 First body. Section 2 Second body.'
    rows = list(text_sections(text, r'Section\s+(\d+)'))
    assert len(rows) == 2
    assert rows[0]['SECTION_NUM'] == '1'
    assert rows[0]['LEGAL_TEXT'] == 'First body.'
    assert rows[1]['SECTION_NUM'] == '2'
    assert rows[1]['LEGAL_TEXT'] == 'Second body.'
