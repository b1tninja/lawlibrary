"""The index is read through the file, and a constraint is not a filter.

``core.open_index`` opens Whoosh without copying each segment into memory;
``core.within`` limits a search without ``filter=``, which Whoosh turns into
the set of every document the constraint matches before it looks at the
query. Both answers must be the answers ``open_dir`` and ``filter=`` gave.
"""

from whoosh import index
from whoosh.query import And, Term

from core import open_index, within
from indexer import Indexer


def _laws(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    laws = []
    for year in ('2011', '2025'):
        for code, number, words in (
            ('FGC', '1', 'The fine imposed before judgment today.'),
            ('CIV', '1', 'The penalty imposed before judgment later.'),
            ('CIV', '2', 'The landlord shall keep the dwelling habitable.'),
        ):
            laws.append({
                'PK': '%s:%s%s' % (year, code.lower(), number),
                'LAW_CODE': code, 'SECTION_NUM': number,
                'CODE_HEADING': '%s Code - %s' % (code, code),
                'LEGAL_TEXT': words, 'ACTIVE_FLG': True,
                'SESSION': year, 'SUBDIVISION': 'US-CA',
            })
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), laws)
    return idxer


def test_the_index_opens_without_a_copy_and_reads_the_same(tmp_path):
    idxer = _laws(tmp_path)
    opened = open_index(idxer.idx_path)
    assert opened.storage.supports_mmap is False
    assert opened.latest_generation() == index.open_dir(idxer.idx_path).latest_generation()
    with opened.searcher() as searcher:
        assert searcher.doc_count() == 6
        hits = searcher.search(Term('LAW_CODE', 'CIV'), limit=None)
        assert sorted(hit['SECTION_NUM'] for hit in hits) == ['1', '1', '2', '2']
        assert searcher.stored_fields(0)['LAW_CODE'] in ('FGC', 'CIV')


def test_within_is_the_filter_without_the_walk(tmp_path):
    idxer = _laws(tmp_path)
    query = And([Term('LAW_CODE', 'CIV'), Term('SECTION_NUM', '1')])
    constraint = idxer._filter(True, '2025')
    assert within(query, None) is query
    with open_index(idxer.idx_path).searcher() as searcher:
        filtered = [dict(hit) for hit in searcher.search(query, limit=None, filter=constraint)]
        limited = [dict(hit) for hit in searcher.search(within(query, constraint), limit=None)]
    assert [hit['SESSION'] for hit in filtered] == ['2025']
    assert limited == filtered
    # The constraint does not score: the query's own order stands, with a
    # limit (the top-k path skips by block quality) and without one.
    with open_index(idxer.idx_path).searcher() as searcher:
        for limit in (None, 10, 1):
            ranked = searcher.search(within(Term('LEGAL_TEXT', 'impos'), constraint), limit=limit)
            plain = searcher.search(Term('LEGAL_TEXT', 'impos'), limit=limit, filter=constraint)
            assert [(hit['LAW_CODE'], hit.score) for hit in ranked] == [(hit['LAW_CODE'], hit.score) for hit in plain]
            assert ranked and all(hit['SESSION'] == '2025' for hit in ranked)


def test_the_lookup_and_the_search_still_find_the_section(tmp_path):
    idxer = _laws(tmp_path)
    found = idxer.get_section('CIV', '2', session='2011')
    assert found and found[0]['session'] == '2011'
    assert [hit['session'] for hit in idxer.search_law('habitable dwelling')] == ['2025']
    assert idxer.search_law('habitable dwelling', session='all') and len(idxer.search_law('habitable', session='all')) == 2
