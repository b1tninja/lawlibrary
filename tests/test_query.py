"""Query interface for Jason: parser, ordering, and indexed lookups."""

import pytest
from whoosh import index

from indexer import WHOOSH_INDEX_BASEDIR, Indexer
from query import (
    ACTS,
    act,
    cite,
    outline,
    parse_citation,
    place,
    section_key,
)


def _index_has_civ_4000():
    if not index.exists_in(WHOOSH_INDEX_BASEDIR):
        return False
    hits = Indexer().get_section('CIV', '4000')
    return bool(hits)


INDEX_READY = _index_has_civ_4000()


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
def test_civil_code_title_resolves():
    from indexer import Indexer
    assert Indexer()._resolve_code('Civil Code') == 'CIV'
    assert Indexer()._resolve_code('Civ. Code') == 'CIV'
    result = cite('Civil Code section 1940')
    assert result['found'] is True
    assert result['code'] == 'CIV'
    assert result['section'] == '1940'
    assert result.get('text')


def test_sacramento_ordinance_is_absent():
    miss = cite('Sacramento parking ordinance')
    assert miss['found'] is False
    assert miss['reason'] == 'ordinance_absent'
    assert place()['ordinances'] == 'absent'
    assert place()['region'] == 'US-CA'


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
    reason='index present but CIV 4000 not indexed yet',
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
    reason='index present but CIV 4000 not indexed yet',
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


@pytest.mark.skipif(
    not index.exists_in(WHOOSH_INDEX_BASEDIR),
    reason='local Whoosh index data/idx is missing',
)
@pytest.mark.skipif(
    index.exists_in(WHOOSH_INDEX_BASEDIR) and not INDEX_READY,
    reason='index present but CIV 4000 not indexed yet',
)
def test_act_davis_stirling_span():
    result = act('davis-stirling')
    assert result['found'] is True
    assert result['code'] == 'CIV'
    assert result['start'] == '4000'
    assert result['end'] == '6150'
    assert ACTS['davis-stirling'] == ('CIV', '4000', '6150')
