"""The shelf: one index per edition, read as one.

Each edition is its own Whoosh directory with its own needle store, built
by its own writer; ``core.open_index`` reads them together. Nothing here
opens the live index.
"""

import json
import os

from whoosh.query import Term

from core import EDITION_MARK, Shelf, editions, index_ready, newest_edition, open_index
from indexer import Indexer


def _law(year, code, number, words):
    return {
        'PK': '%s:%s%s' % (year, code.lower(), number),
        'LAW_CODE': code, 'SECTION_NUM': number,
        'CODE_HEADING': '%s Code - %s' % (code, code),
        'LEGAL_TEXT': words, 'ACTIVE_FLG': True,
        'SESSION': year, 'SUBDIVISION': 'US-CA',
    }


def _edition(root, year, laws, mark=True):
    idxer = Indexer(str(root / year))
    count = idxer.index_pubinfo_laws(str(root / ('pubinfo_%s.zip' % year)), iter(laws))
    if mark:
        idxer.mark_edition(year, count, 'pubinfo_%s.zip' % year)
    return idxer


def _shelf(tmp_path):
    root = tmp_path / 'shelf'
    _edition(root, '2011', [
        _law('2011', 'CIV', '1', 'The penalty imposed before judgment later.'),
        _law('2011', 'CIV', '1350', 'The association shall keep the common area.'),
    ])
    _edition(root, '2025', [
        _law('2025', 'CIV', '1', 'The penalty imposed before judgment later.'),
        _law('2025', 'CIV', '4600', 'The association shall keep the common area.'),
        _law('2025', 'FGC', '1', 'The fine imposed before judgment today.'),
    ])
    return root


def test_an_edition_is_a_marked_directory_and_a_half_built_one_is_not_read(tmp_path):
    root = _shelf(tmp_path)
    _edition(root, '2023', [_law('2023', 'CIV', '1', 'Half built.')], mark=False)
    assert [part.name for part in editions(root)] == ['2011', '2025']
    assert newest_edition(root).name == '2025'
    assert index_ready(root) and not index_ready(tmp_path / 'nowhere')
    with open(root / '2025' / EDITION_MARK, encoding='utf-8') as fh:
        mark = json.load(fh)
    assert mark['session'] == '2025' and mark['sections'] == 3
    # A flat index has no editions and is read as before.
    flat = Indexer(str(tmp_path / 'flat'))
    flat.index_pubinfo_laws(str(tmp_path / 'pub.zip'), iter([_law('2025', 'CIV', '1', 'Flat.')]))
    assert editions(tmp_path / 'flat') == [] and index_ready(tmp_path / 'flat')
    assert not isinstance(open_index(tmp_path / 'flat'), Shelf)


def test_the_editions_read_as_one_index(tmp_path):
    root = _shelf(tmp_path)
    shelf = open_index(root)
    assert isinstance(shelf, Shelf) and shelf.sessions == ['2011', '2025']
    assert shelf.doc_count() == 5
    assert 'TOC_PATH' in shelf.schema.names() and shelf.storage.supports_mmap is False
    with shelf.searcher() as searcher:
        assert searcher.doc_count() == 5
        hits = searcher.search(Term('LAW_CODE', 'CIV'), limit=None)
        assert sorted((hit['SESSION'], hit['SECTION_NUM']) for hit in hits) == [
            ('2011', '1'), ('2011', '1350'), ('2025', '1'), ('2025', '4600'),
        ]
        newest = list(searcher.document_numbers(SESSION='2025'))
        assert len(newest) == 3
        assert {searcher.stored_fields(docnum)['SESSION'] for docnum in newest} == {'2025'}
        assert sorted(term.decode() for term in searcher.lexicon('SESSION')) == ['2011', '2025']
        # Postings cross the editions: "impos" is in both.
        assert searcher.doc_frequency('LEGAL_TEXT', 'impos') == 3


def test_the_generation_follows_every_edition(tmp_path):
    root = _shelf(tmp_path)
    before = open_index(root).latest_generation()
    Indexer(str(root / '2011')).index_pubinfo_laws(
        str(root / 'pubinfo_2011.zip'), iter([_law('2011', 'GOV', '1', 'Added later.')]))
    assert open_index(root).latest_generation() != before
    assert open_index(root).doc_count() == 6


def test_a_shelf_indexer_reads_the_newest_editions_store_and_codes(tmp_path):
    root = _shelf(tmp_path)
    idxer = Indexer(str(root))
    assert idxer.codes_path == os.path.join(str(root / '2025'), 'codes.json')
    assert sorted(row['code'] for row in idxer.list_codes()) == ['CIV', 'FGC']
    db = idxer._needle_db()
    try:
        citations = {row[0] for row in db.execute('SELECT DISTINCT citation FROM annotation')} | {
            row[0] for row in db.execute('SELECT DISTINCT citation FROM needle')}
    finally:
        db.close()
    assert 'CIV 4600' in citations and 'CIV 1350' not in citations
    assert idxer.sessions() == ['2011', '2025']


def test_the_lookups_walk_the_shelf(tmp_path, monkeypatch):
    import query
    root = _shelf(tmp_path)
    monkeypatch.setattr(query, '_indexer', lambda: Indexer(str(root)))
    found = query.section('CIV', '4600')
    assert found['found'] is True and found['session'] == '2025'
    older = query.section('CIV', '1350')
    assert older['found'] is False
    assert [row['session'] for row in older['indexed_in']] == ['2011']
    assert query.section('CIV', '1350', session='2011')['found'] is True
    assert query.section('CIV', '1350', session='2011')['session'] == '2011'


def test_the_ledger_counts_the_newest_edition_of_the_shelf(tmp_path):
    from ledger import open_ledger
    root = _shelf(tmp_path)
    book = open_ledger(str(root))
    assert book.session == '2025'
    assert int(book.meta['sections']) == 3
    assert book.tally(book.places('code', 'CIV'))['associ'] == 1


def test_a_packed_needle_row_is_written_and_not_parsed_again(tmp_path):
    from indexer import needle_rows
    law = _law('2025', 'CIV', '1946', 'The landlord shall give notice within 30 days.')
    packed = needle_rows(law)
    assert packed[2], 'the sentence carries at least one annotation'
    law['NEEDLES'] = packed
    idxer = Indexer(str(tmp_path / 'idx'))
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), iter([law]))
    db = idxer._needle_db()
    try:
        assert db.execute("SELECT COUNT(*) FROM annotation WHERE citation = 'CIV 1946'").fetchone()[0] == len(packed[2])
    finally:
        db.close()
