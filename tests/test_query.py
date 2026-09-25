"""Query interface for Jason: parser, ordering, and indexed lookups."""

import pytest
from whoosh import index

from indexer import WHOOSH_INDEX_BASEDIR, Indexer
from indexer import _code_rank
from query import (
    ACTS,
    act,
    cite,
    heading_key,
    index_present,
    outline,
    parse_citation,
    parse_law_url,
    place,
    search,
    section,
    section_key,
)


def _index_has_civ_4000():
    if not index.exists_in(WHOOSH_INDEX_BASEDIR):
        return False
    hits = Indexer().get_section('CIV', '4000')
    return bool(hits) and bool(hits[0].get('text'))


def _index_has_civ_1940():
    if not index.exists_in(WHOOSH_INDEX_BASEDIR):
        return False
    hits = Indexer().get_section('CIV', '1940')
    return bool(hits) and bool(hits[0].get('text'))


INDEX_READY = _index_has_civ_4000()
INDEX_HAS_1940 = _index_has_civ_1940()


def test_a_heading_follows_the_statute_not_the_alphabet():
    ordered = sorted(['10', '2', '1.5', '1', 'IX', 'IV', 'I'], key=heading_key)
    assert ordered == ['1', '1.5', '2', '10', 'I', 'IV', 'IX']
    constitution = sorted(
        ['SEC. 20', 'SEC. 2', 'SEC. 10', 'Section 4', 'SECTION 1', '[SEC. 24.]'],
        key=heading_key,
    )
    assert constitution == ['SECTION 1', 'SEC. 2', 'Section 4', 'SEC. 10', 'SEC. 20', '[SEC. 24.]']
    assert _code_rank('CONS') < _code_rank('BPC') < _code_rank('CIV') < _code_rank('CCP')
    assert _code_rank('CIV') < _code_rank('ZZZ')


def test_section_key_orders_decimal_and_letter():
    assert section_key('5375') < section_key('5375.5') < section_key('5376')
    assert section_key('5375') < section_key('5375a')
    assert section_key('5375.5') < section_key('5375.5a')
    ordered = sorted(['5376', '5375.5', '5375', '5375a'], key=section_key)
    assert ordered == ['5375', '5375a', '5375.5', '5376']


def test_parse_citation_forms():
    assert parse_citation('CIV 5806') == {
        'kind': 'section',
        'code': 'CIV',
        'section': '5806',
        'subdivision': None,
        'expression': 'CIV 5806',
    }
    assert parse_citation('Civil Code section 5806')['section'] == '5806'
    assert parse_citation('Civil Code section 5806')['code'].lower().startswith('civil')

    dotted = parse_citation('Civ. Code § 5806(a)')
    assert dotted['kind'] == 'section'
    assert dotted['section'] == '5806'
    assert dotted['subdivision'] == '(a)'

    nested = parse_citation('Civ. Code § 5800(a)(4)')
    assert nested['section'] == '5800'
    assert nested['subdivision'] == '(a)(4)'

    bpc = parse_citation('BPC 11500(d)')
    assert bpc['code'] == 'BPC'
    assert bpc['section'] == '11500'
    assert bpc['subdivision'] == '(d)'

    span = parse_citation('CIV 4000-6150')
    assert span == {
        'kind': 'span',
        'code': 'CIV',
        'start': '4000',
        'end': '6150',
        'expression': 'CIV 4000-6150',
    }

    long_span = parse_citation('Business and Professions Code §§ 11500-11506')
    assert long_span['kind'] == 'span'
    assert long_span['start'] == '11500'
    assert long_span['end'] == '11506'

    named = parse_citation('davis-stirling')
    assert named == {
        'kind': 'act',
        'name': 'davis-stirling',
        'expression': 'davis-stirling',
    }


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
@pytest.mark.skipif(
    index.exists_in(WHOOSH_INDEX_BASEDIR) and not INDEX_HAS_1940,
    reason='index missing section text (stale or untagged region fields)',
)
def test_civil_code_title_resolves():
    from indexer import Indexer
    assert Indexer()._resolve_code('Civil Code') == 'CIV'
    assert Indexer()._resolve_code('Civ. Code') == 'CIV'
    result = cite('Civil Code section 1940')
    assert result['found'] is True
    assert result['code'] == 'CIV'
    assert result['section'] == '1940'
    assert result.get('text')


def test_federal_statute_is_outside_california():
    miss = cite('Fair Housing Act')
    assert miss['found'] is False
    assert miss['reason'] == 'outside_us_ca'
    assert miss['statute'] == {'title': '42', 'chapter': '45'}
    assert miss['regulations'] == {'title': '24'}

    usc = cite('42 USC 3604')
    assert usc['reason'] == 'outside_us_ca'
    assert usc['statute'] == {'title': '42', 'chapter': '45'}
    assert usc['regulations'] == {'title': '24'}

    ada = cite('Americans with Disabilities Act')
    assert ada['reason'] == 'outside_us_ca'
    assert ada['statute'] == {'title': '42', 'chapter': '126'}
    assert ada['regulations'] == {'title': '28'}

    nfip = cite('NFIP')
    assert nfip['reason'] == 'outside_us_ca'
    assert nfip['statute'] == {'title': '42', 'chapter': '50'}
    assert nfip['regulations'] == {'title': '44'}


def test_federal_section_usc_hit_and_cfr_miss(tmp_path, monkeypatch):
    import corpus
    import query as law_query
    from corpus import connect

    usc_path = tmp_path / 'US.sqlite'
    db = connect(str(usc_path))
    db.execute(
        'INSERT INTO section '
        '(pk, law_code, section_num, legal_text, citation, session) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (
            '42:3604',
            '42',
            '3604',
            'It shall be unlawful to discriminate in the sale or rental of housing.',
            '42 USC 3604',
            None,
        ),
    )
    db.commit()
    db.close()

    cfr_path = tmp_path / 'US' / 'cfr' / '24.sqlite'
    monkeypatch.setattr(corpus, 'corpus_path', lambda *a, **k: str(usc_path))
    monkeypatch.setattr(corpus, 'cfr_corpus_path', lambda *a, **k: str(cfr_path))

    hit = law_query.federal_section('42', '3604', kind='usc')
    assert hit == {
        'found': True,
        'kind': 'usc',
        'citation': '42 USC 3604',
        'code': '42',
        'section': '3604',
        'text': 'It shall be unlawful to discriminate in the sale or rental of housing.',
    }

    miss = law_query.federal_section('24', '100.5', kind='cfr')
    assert miss['found'] is False
    assert miss['reason'] == 'not_in_index'
    assert miss['expression'] == '24 CFR 100.5'
    assert miss['corpus'] == str(cfr_path)


def test_sacramento_ordinance_is_absent():
    miss = cite('Sacramento parking ordinance')
    assert miss['found'] is False
    assert miss['reason'] == 'ordinance_absent'
    assert place()['ordinances'] == 'absent'
    assert place()['region'] == 'US-CA'
    assert place()['country'] == 'US'
    assert place()['locality'] == 'Sacramento'
    assert place()['statutes'] == 'US-CA'


def test_search_defaults_to_us_ca(tmp_path, monkeypatch):
    """Statute search scopes to US-CA; ordinance queries stay empty."""
    import query as law_query

    idx_path = tmp_path / 'idx'
    indexer = Indexer(idx_path)
    laws = [{
        'PK': '2025:pk1',
        'LAW_CODE': 'CIV',
        'SECTION_NUM': '1940',
        'SECTION_TITLE': 'Landlord duty',
        'CODE_HEADING': 'Civil Code',
        'LEGAL_TEXT': 'The landlord shall keep the dwelling habitable.',
        'ACTIVE_FLG': True,
        'SESSION': '2025',
        'SUBDIVISION': 'US-CA',
        'LOCALITY': '',
    }]
    indexer.index_pubinfo_laws(str(tmp_path / 'pub.zip'), laws)
    # codes.json needs CIV for resolve; index_pubinfo_laws wrote CODE_HEADING
    monkeypatch.setattr(law_query, '_indexer', lambda: Indexer(idx_path))

    hits = law_query.search('habitable dwelling')
    assert len(hits) == 1
    assert hits[0]['country'] == 'US'
    assert hits[0]['subdivision'] == 'US-CA'
    assert hits[0]['locality'] == ''

    assert law_query.search('Sacramento parking ordinance') == []
    assert law_query.search('habitable', subdivision='US-NY') == []


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
def test_search_opens_a_section_sign():
    hits = search('See Bus. & Prof. Code § 10050')
    if not hits:
        pytest.skip('BPC 10050 is not in this index')
    assert hits[0]['code'] == 'BPC'
    assert hits[0]['section'] == '10050'
    series = search('Bus. & Prof. Code §§ 10050, 10052')
    assert [hit['section'] for hit in series[:2]] == ['10050', '10052']


def test_empty_cite_is_miss():
    miss = cite('')
    assert miss['found'] is False
    assert miss['reason'] == 'not_in_index'


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
@pytest.mark.skipif(
    index.exists_in(WHOOSH_INDEX_BASEDIR) and not INDEX_READY,
    reason='index missing section text (stale or CIV 4000 not indexed)',
)
def test_cite_civ_4000_returns_text():
    result = cite('CIV 4000')
    assert result['found'] is True
    assert result['code'] == 'CIV'
    assert result['section'] == '4000'
    assert result.get('text')


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
@pytest.mark.skipif(
    index.exists_in(WHOOSH_INDEX_BASEDIR) and not INDEX_READY,
    reason='index missing section text (stale or CIV 4000 not indexed)',
)
def test_outline_civ_5800_5810_excludes_1940():
    result = outline('CIV', '5800', '5810')
    assert result['found'] is True
    assert result['nodes']
    sections = set()
    for node in result['nodes']:
        sections.add(node['first'])
        sections.add(node['last'])
    assert '1940' not in sections
    for node in result['nodes']:
        assert section_key(node['first']) >= section_key('5800')
        assert section_key(node['last']) <= section_key('5810')


@pytest.mark.skipif(not index_present(), reason='local Whoosh index missing')
def test_section_miss_reports_other_sessions():
    years = Indexer().sessions()
    newest = years[-1]
    nowhere = section('CIV', '5200')
    assert nowhere['found'] is False
    assert nowhere['reason'] == 'not_in_index'
    assert nowhere['session'] == newest
    assert nowhere['indexed_in'] == []
    elsewhere = section('CIV', '1351', session='2025')
    assert elsewhere['found'] is False
    assert elsewhere['session'] == '2025'
    assert elsewhere['indexed_in']
    assert all(row['session'] != '2025' for row in elsewhere['indexed_in'])
    assert all(row['session'] in years for row in elsewhere['indexed_in'])
    assert all('1351' in row['citation'] for row in elsewhere['indexed_in'])
    hit = section('BPC', '11500', session='2011')
    assert hit['found'] is True
    assert 'indexed_in' not in hit
    from structure import related
    walk = related('CIV', '5200', depth=0)
    assert walk['found'] is False
    assert walk['session'] == newest
    assert walk['indexed_in'] == []
    current = section('CIV', '1350', session='2011')
    assert current['found'] is True
    assert current['history']
    assert {'year': '1985', 'chapter': '874', 'act': '14', 'action': 'repealed and added'} in current['chapters']


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
@pytest.mark.skipif(
    index.exists_in(WHOOSH_INDEX_BASEDIR) and not INDEX_READY,
    reason='index missing section text (stale or CIV 4000 not indexed)',
)
def test_act_davis_stirling_span():
    result = act('davis-stirling')
    assert result['found'] is True
    assert result['code'] == 'CIV'
    assert result['start'] == '4000'
    assert result['end'] == '6150'
    assert ACTS['davis-stirling'] == ('CIV', '4000', '6150')


def test_a_law_url_names_one_node():
    path = parse_law_url('us-ca/civ/division/1/section/1940/subdivision/b')
    assert path.region == 'US-CA'
    assert path.code == 'CIV'
    assert path.section == '1940'
    assert path.subdivision == 'b'
    assert path.url == 'us-ca/civ/division/1/section/1940/subdivision/b'
    assert parse_law_url('').url == 'us-ca'
