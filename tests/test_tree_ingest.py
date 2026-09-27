"""The publisher's tree is stored on each section at ingestion.

LAW_TOC_TBL is the table the official site draws. A row repeats every
ancestor's number on the row, so the filled fields are the path down to it,
not what it is; the unit a row *is* is the field it fills that its parent
does not. Nearly every code opens with headings that have no number at all.

These pubinfo zips are built to shape, in the layout the Legislature uses.
No statute is quoted.
"""

import zipfile
from types import SimpleNamespace

from us.states.ca import California, iter_laws, own_unit, toc_headings, toc_trail

from indexer import Indexer


def _row(cols):
    return '\t'.join('NULL' if col is None else '`%s`' % col for col in cols)


def _toc(code, div, title, part, chap, art, heading, seq, level, pos, path, holds):
    return _row([code, div, title, part, chap, art, heading, 'Y', 'u', '2020-01-01 00:00:00',
                 seq, level, pos, path, holds, None, None, None, None])


def _pubinfo(path):
    """A code with three shapes the fixed ladder gets wrong.

    Division 1 > Chapter 2 > Article 3 is the shape the old walk handled.
    Division 2 > Part 1 > Title 3 nests a title under a part, as the Civil
    Code does, so a title row has a part filled too. PRELIMINARY PROVISIONS
    has no unit at all and holds a section, as the front of nearly every
    code does.
    """
    toc = [
        _toc('CIV', '1.', None, None, None, None, 'Division 1. Persons', '1', '1', '1', '1', 'N'),
        _toc('CIV', '1.', None, None, '2.', None, 'Chapter 2. Hiring', '2', '2', '1', '1.2', 'N'),
        _toc('CIV', '1.', None, None, '2.', '3.', 'Article 3. Hiring of Real Property', '3', '3', '1', '1.2.3', 'Y'),
        _toc('CIV', '2.', None, None, None, None, 'Division 2. Property', '4', '1', '2', '2', 'N'),
        _toc('CIV', '2.', None, '1.', None, None, 'Part 1. Property in General', '5', '2', '1', '2.1', 'N'),
        _toc('CIV', '2.', '3.', '1.', None, None, 'Title 3. General Definitions', '6', '3', '1', '2.1.1', 'Y'),
        _toc('CIV', None, None, None, None, None, 'PRELIMINARY PROVISIONS', '7', '1', '3', '3', 'Y'),
    ]
    sections = [
        _row(['1', 'CIV', '1.2.3', '1940', '1', 'Landlord duty', None, None, None, 'u', '2020-01-01 00:00:00', 'ver1', '1']),
        _row(['2', 'CIV', '2.1.1', '748', '1', 'Definitions', None, None, None, 'u', '2020-01-01 00:00:00', 'ver2', '2']),
        _row(['3', 'CIV', '3', '2', '1', 'Application', None, None, None, 'u', '2020-01-01 00:00:00', 'ver3', '3']),
    ]
    law = [
        _row(['pk1', 'CIV', '1940.', '1872', '1', '1', None, 'ver1', '1.', None, None, '2.', '3.',
              'Enacted 1872.', 'LAW_SECTION_TBL_pk1.lob', 'Y', 'u', '2020-01-01 00:00:00']),
        _row(['pk2', 'CIV', '748.', '1872', '1', '1', None, 'ver2', '2.', '3.', '1.', None, None,
              'Enacted 1872.', 'LAW_SECTION_TBL_pk2.lob', 'Y', 'u', '2020-01-01 00:00:00']),
        _row(['pk3', 'CIV', '2.', '1872', '1', '1', None, 'ver3', None, None, None, None, None,
              'Enacted 1872.', 'LAW_SECTION_TBL_pk3.lob', 'Y', 'u', '2020-01-01 00:00:00']),
    ]
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('CODES_TBL.dat', _row(['CIV', 'Civil Code']) + '\n')
        zf.writestr('LAW_TOC_TBL.dat', '\n'.join(toc) + '\n')
        zf.writestr('LAW_TOC_SECTIONS_TBL.dat', '\n'.join(sections) + '\n')
        zf.writestr('LAW_SECTION_TBL.dat', '\n'.join(law) + '\n')
        zf.writestr('LAW_SECTION_TBL_pk1.lob', '<p>The landlord shall keep the dwelling habitable.</p>')
        zf.writestr('LAW_SECTION_TBL_pk2.lob', '<p>Words used in this title have these meanings.</p>')
        zf.writestr('LAW_SECTION_TBL_pk3.lob', '<p>This code takes effect at noon.</p>')


def _laws(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    return {law['SECTION_NUM']: law for law in iter_laws(pub)}


def test_a_row_is_the_unit_its_parent_lacks():
    parent = SimpleNamespace(DIVISION='2', TITLE=None, PART='1', CHAPTER=None, ARTICLE=None)
    title = SimpleNamespace(DIVISION='2', TITLE='3', PART='1', CHAPTER=None, ARTICLE=None)
    assert own_unit(title, parent) == 'TITLE', 'a title under a part is a title, not a part'
    assert own_unit(parent, SimpleNamespace(DIVISION='2', TITLE=None, PART=None, CHAPTER=None, ARTICLE=None)) == 'PART'
    root = SimpleNamespace(DIVISION=None, TITLE=None, PART=None, CHAPTER=None, ARTICLE=None)
    assert own_unit(root, None) is None, 'an unnumbered heading adds no field'


def test_a_title_under_a_part_is_filed_as_a_title(tmp_path):
    """The old walk put Title 3 on PART_HEADING, because part outranked title in a fixed order."""
    law = _laws(tmp_path)['748']
    assert law['TITLE_HEADING'] == 'Title 3. General Definitions'
    assert law['PART_HEADING'] == 'Part 1. Property in General'
    assert law['DIVISION_HEADING'] == 'Division 2. Property'


def test_the_trail_is_the_publishers_tree(tmp_path):
    law = _laws(tmp_path)['748']
    assert law['TOC_PATH'] == '2.1.1'
    assert law['TOC_LEVEL'] == 3
    assert law['TOC_UNIT'] == 'title'
    assert [(rung['unit'], rung['number']) for rung in law['TOC_TRAIL']] == [
        ('division', '2'), ('part', '1'), ('title', '3'),
    ]
    assert law['TOC_TRAIL'][-1]['holds'] is True
    assert law['TOC_TRAIL'][0]['holds'] is False
    assert [rung['path'] for rung in law['TOC_TRAIL']] == ['2', '2.1', '2.1.1']


def test_an_unnumbered_heading_is_a_rung(tmp_path):
    """PRELIMINARY PROVISIONS has no unit field. It holds a section all the same."""
    law = _laws(tmp_path)['2']
    assert law['TOC_PATH'] == '3'
    assert law['TOC_UNIT'] == 'unnumbered'
    assert law['TOC_TRAIL'] == [{
        'unit': 'unnumbered', 'number': '', 'heading': 'PRELIMINARY PROVISIONS',
        'position': 3, 'path': '3', 'holds': True,
    }]
    # No unit field, so the five captions stay empty rather than wrong.
    assert not any(law[field] for field in ('DIVISION_HEADING', 'TITLE_HEADING', 'PART_HEADING'))


def test_the_old_shape_still_reads(tmp_path):
    law = _laws(tmp_path)['1940']
    assert law['TOC_PATH'] == '1.2.3'
    assert [rung['unit'] for rung in law['TOC_TRAIL']] == ['division', 'chapter', 'article']
    assert law['ARTICLE_HEADING'] == 'Article 3. Hiring of Real Property'


def test_the_tree_is_stored_and_read_back(tmp_path):
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    california = California()
    indexer = Indexer(tmp_path / 'idx')
    assert california.edition(pub).index(indexer, pub, subdivision=california.code) == 3
    from whoosh import index
    from whoosh.query import Term, Prefix
    ix = index.open_dir(indexer.idx_path)
    with ix.searcher() as searcher:
        held = searcher.search(Term('SECTION_NUM', '748'), limit=1)[0]
        assert held['TOC_PATH'] == '2.1.1'
        assert held['TOC_TRAIL'][2]['heading'] == 'Title 3. General Definitions'
        # A prefix on the path names a subtree: everything under Division 2.
        under = searcher.search(Prefix('TOC_PATH', '2.'), limit=None)
        assert {hit['SECTION_NUM'] for hit in under} == {'748'}
        assert searcher.search(Term('TOC_UNIT', 'unnumbered'), limit=1)[0]['SECTION_NUM'] == '2'


def _tree(tmp_path, monkeypatch):
    """A tree read from the synthetic index, with query pointed at it."""
    import query
    pub = tmp_path / 'pubinfo_2025.zip'
    _pubinfo(pub)
    california = California()
    idxer = Indexer(tmp_path / 'idx')
    california.edition(pub).index(idxer, pub, subdivision=california.code)
    monkeypatch.setattr(query, '_indexer', lambda: Indexer(tmp_path / 'idx'))
    return query


def test_the_tree_is_drawn_as_the_publisher_nests_it(tmp_path, monkeypatch):
    """The root lists every top rung in the publisher's order, the unnumbered one included."""
    query = _tree(tmp_path, monkeypatch)
    root = query.law_tree('us-ca/civ')
    assert root['found'] is True
    assert [(child['unit'], child['value'], child['url']) for child in root['children']] == [
        ('division', '1', 'us-ca/civ/node/1'),
        ('division', '2', 'us-ca/civ/node/2'),
        ('unnumbered', '', 'us-ca/civ/node/3'),
    ]
    assert root['children'][2]['heading'] == 'PRELIMINARY PROVISIONS'
    assert root['children'][2]['holds'] is True
    assert root['trail'] == []


def test_a_node_descends_by_its_path_and_keeps_its_trail(tmp_path, monkeypatch):
    query = _tree(tmp_path, monkeypatch)
    division = query.law_tree('us-ca/civ/node/2')
    assert [(c['unit'], c['value'], c['url']) for c in division['children']] == [('part', '1', 'us-ca/civ/node/2.1')]
    assert [rung['heading'] for rung in division['trail']] == ['Division 2. Property']
    part = query.law_tree('us-ca/civ/node/2.1')
    assert [(c['unit'], c['value'], c['heading']) for c in part['children']] == [
        ('title', '3', 'Title 3. General Definitions'),
    ]
    assert [rung['unit'] for rung in part['trail']] == ['division', 'part']


def test_a_node_that_holds_sections_lists_them(tmp_path, monkeypatch):
    query = _tree(tmp_path, monkeypatch)
    title = query.law_tree('us-ca/civ/node/2.1.1')
    assert [(c['unit'], c['value'], c['heading']) for c in title['children']] == [('section', '748', 'Definitions')]
    assert title['children'][0]['url'] == 'us-ca/civ/node/2.1.1/section/748'
    preliminary = query.law_tree('us-ca/civ/node/3')
    assert [c['value'] for c in preliminary['children']] == ['2']
    assert preliminary['trail'][0]['heading'] == 'PRELIMINARY PROVISIONS'


def test_a_node_rung_is_a_crumb_with_its_own_name():
    """A node's name is not in its address; the trail the tree read supplies it."""
    from application import _library_crumbs
    rungs = [
        {'unit': 'division', 'number': '2', 'heading': 'Division 2. Property', 'path': '2'},
        {'unit': 'part', 'number': '1', 'heading': '', 'path': '2.1'},
    ]
    crumbs = _library_crumbs('us-ca/civ/node/2.1', 'Civil Code', rungs=rungs)
    tail = [(crumb['unit'], crumb['label'], crumb['href']) for crumb in crumbs[-2:]]
    assert tail == [
        ('division', 'Division 2. Property', '/view/tree/us-ca/civ/node/2'),
        ('part', 'Part 1', '/view/tree/us-ca/civ/node/2.1'),
    ]
    front = _library_crumbs('us-ca/civ/node/3', 'Civil Code', rungs=[
        {'unit': 'unnumbered', 'number': '', 'heading': 'PRELIMINARY PROVISIONS', 'path': '3'},
    ])
    assert front[-1] == {'unit': 'unnumbered', 'label': 'PRELIMINARY PROVISIONS', 'href': '/view/tree/us-ca/civ/node/3'}


def test_the_tree_route_walks_the_publishers_tree(tmp_path, monkeypatch):
    import json
    import application
    query = _tree(tmp_path, monkeypatch)
    assert query is not None
    seen = {}

    def start_response(status, headers):
        seen['status'] = status

    body = json.loads(b''.join(application.application(
        {'REQUEST_METHOD': 'GET', 'PATH_INFO': '/tree/us-ca/civ/node/2.1', 'QUERY_STRING': ''},
        start_response,
    )))
    assert seen['status'] == '200 OK'
    assert [(crumb['unit'], crumb['label']) for crumb in body['crumbs'][-2:]] == [
        ('division', 'Division 2. Property'), ('part', 'Part 1. Property in General'),
    ]
    assert [(row['unit'], row['label'], row['href']) for row in body['contents']] == [
        ('title', 'Title 3. General Definitions', '/view/tree/us-ca/civ/node/2.1.1'),
    ]


def test_a_node_address_round_trips(tmp_path, monkeypatch):
    query = _tree(tmp_path, monkeypatch)
    place = query.parse_law_url('us-ca/civ/node/2.1')
    assert place.units == (('node', '2.1'),)
    assert place.url == 'us-ca/civ/node/2.1'
    assert place.child('node', '2.1.1').url == 'us-ca/civ/node/2.1.1'
