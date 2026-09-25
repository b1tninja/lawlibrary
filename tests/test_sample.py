from apa import Code
from corpus import connect, cfr_corpus_path
from indexer import Indexer
from sample import Draw, sample, sources


def _index(tmp_path):
    idxer = Indexer(tmp_path / 'idx')
    laws = [
        {
            'PK': '2025:civ1940',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '1940',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'This code governs a hiring of real property.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
        {
            'PK': '2025:civ1941',
            'LAW_CODE': 'CIV',
            'SECTION_NUM': '1941',
            'CODE_HEADING': 'Civil Code - CIV',
            'LEGAL_TEXT': 'The lessor of a building shall keep it fit.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
        {
            'PK': '2025:bpc10050',
            'LAW_CODE': 'BPC',
            'SECTION_NUM': '10050',
            'CODE_HEADING': 'Business and Professions Code - BPC',
            'LEGAL_TEXT': 'There is in the Business and Transportation Agency a Department of Real Estate.',
            'ACTIVE_FLG': True,
            'SESSION': '2025',
            'SUBDIVISION': 'US-CA',
        },
    ]
    idxer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), laws)
    return idxer


def test_a_draw_closes_over_the_book():
    """The book, the count, the seed, and the pattern stay on the draw."""
    closed = Draw(Code.CIVIL).take(5).seed(7).matching('subdivision')
    assert closed.book == 'CIV'
    assert closed.count == 5
    assert closed._seed == 7
    assert closed.pattern == 'subdivision'
    assert Draw('').citations()[:2] == []


def test_sources_list_the_indexed_code_and_a_rule_pointer(tmp_path):
    rows = sources(indexer=_index(tmp_path), root=tmp_path)
    books = {row['book'] for row in rows if row['kind'] == 'statute'}
    assert books == {'CIV', 'BPC'}
    rules = [row for row in rows if row['kind'] == 'rule']
    assert rules
    assert rules[0]['present'] is False
    assert rules[0]['url']


def test_the_same_seed_returns_the_same_sections(tmp_path):
    idxer = _index(tmp_path)
    first = sample(Code.CIVIL, n=1, seed=7, indexer=idxer)
    second = sample('Civil Code', n=1, seed=7, indexer=idxer)
    assert first['found'] is True
    assert first['book'] == 'CIV'
    assert first['sections'][0]['citation'] == second['sections'][0]['citation']
    assert 'This code' in first['sections'][0]['text'] or 'lessor' in first['sections'][0]['text']


def test_a_pattern_keeps_sections_that_contain_the_words(tmp_path):
    drawn = sample('CIV', n=2, seed=1, pattern='this code', indexer=_index(tmp_path))
    assert drawn['found'] is True
    assert len(drawn['sections']) == 1
    assert drawn['sections'][0]['section'] == '1940'


def test_a_regulation_file_can_be_sampled(tmp_path):
    path = cfr_corpus_path('24', root=tmp_path)
    db = connect(path)
    db.execute(
        'INSERT INTO section (pk, law_code, section_num, legal_text, citation, session) VALUES (?, ?, ?, ?, ?, ?)',
        ('24-1.1', '24', '1.1', 'This part applies to the following programs.', '24 CFR 1.1', '2026'),
    )
    db.commit()
    db.close()
    drawn = sample('24', n=1, seed=3, root=tmp_path)
    assert drawn['kind'] == 'regulation'
    assert drawn['sections'][0]['text'].startswith('This part')


def test_a_court_rule_is_a_pointer_until_it_is_indexed():
    drawn = sample('SacramentoSuperiorCourt', kind='rule')
    assert drawn['found'] is False
    assert drawn['reason'] == 'not_indexed'
    assert drawn['url'].startswith('https://')
