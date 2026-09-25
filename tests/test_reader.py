"""The JSON the React client reads, and the page it mounts on.

Each route answers ``found``. A miss keeps ``reason``. The client draws the
marks, the cuts, the trail, and the graph from these replies; it keeps no copy
of the words.
"""

import json

from application import application


def _get(path, query=''):
    seen = {}

    def start_response(status, headers):
        seen['status'] = status
        seen['headers'] = headers

    body = b''.join(application({
        'REQUEST_METHOD': 'GET', 'PATH_INFO': path, 'QUERY_STRING': query,
    }, start_response))
    return seen['status'], body, dict(seen['headers'])


def _json(path, query=''):
    status, body, headers = _get(path, query)
    return status, json.loads(body)


def test_the_reader_is_a_mount_and_keeps_the_document():
    """React takes ``#root``. The same place without a script is the page."""
    status, body, headers = _get('/reader/section/CIV/1714.1')
    page = body.decode('utf-8')
    assert status == '200 OK'
    assert 'text/html' in headers.get('Content-Type', '')
    assert 'id="root"' in page
    assert '/static/reader.js' in page
    assert '/static/reader.css' in page
    assert '<noscript>' in page
    assert 'CIV 1714.1' in page.split('<noscript>')[1]
    status, body, _headers = _get('/reader')
    assert status == '200 OK'
    assert 'id="root"' in body.decode('utf-8')
    status, body, _headers = _get('/reader/nowhere')
    assert status == '404 Not Found'


def test_a_section_carries_the_trail_the_cuts_and_the_formats():
    status, body = _json('/section/CIV/1714.1')
    assert status == '200 OK'
    assert body['found'] is True
    units = [rung['level'] for rung in body['units']]
    assert 'division' in units
    trail = [crumb['unit'] for crumb in body['crumbs']]
    assert trail[0] == 'library'
    assert trail[-1] == 'section'
    assert body['crumbs'][-1]['href'] == '/view/section/CIV/1714.1'
    assert any(step['href'].startswith('/view/tree/') for step in body['crumbs'][1:-1])
    current = [row for row in body['contents'] if row.get('current')]
    assert len(current) == 1
    assert current[0]['short'] == '1714.1'
    assert body['nodes']['unit'] == 'section'
    assert [row['hint'] for row in body['formats']] == ['html', 'txt', 'xml', 'pdf', 'md']
    assert body['links'] == list({row['href']: row for row in body['links']}.values())
    assert any(piece.get('kind') for piece in body['credit'])


def test_a_heading_names_its_own_unit_in_the_trail():
    """The index stored ``TITLE 5. HIRING`` on the part field. The caption wins."""
    status, body = _json('/section/CIV/1940')
    assert status == '200 OK'
    trail = {crumb['unit']: crumb['label'] for crumb in body['crumbs']}
    assert trail['title'].startswith('TITLE 5.')
    assert trail['chapter'].startswith('CHAPTER 2.')
    hrefs = [crumb['href'] for crumb in body['crumbs'] if crumb['unit'] == 'chapter']
    assert hrefs and hrefs[0].endswith('/title/5/part/4/chapter/2')
    status, node = _json('/tree/us-ca/civ/division/3/title/5/part/4/chapter/2')
    assert node['found'] is True
    assert any(row['short'] == '1940' for row in node['contents'])


def test_a_tree_node_lists_its_children_as_links():
    status, body = _json('/tree/us-ca/civ')
    assert status == '200 OK'
    assert body['crumbs'][-1]['unit'] == 'code'
    assert body['contents']
    first = body['contents'][0]
    assert first['href'].startswith('/view/tree/us-ca/civ/division/')
    assert first['unit'] == 'division'


def test_the_closed_sets_are_served_so_the_client_keeps_no_copy():
    status, body = _json('/surfaces')
    assert status == '200 OK'
    surfaces = body['surfaces']
    assert 'citation' in surfaces['note']
    assert 'cross_reference' in surfaces['note']
    assert surfaces['cite'][:3] == ['section', 'range', 'series']
    assert surfaces['use'] == ['read', 'find', 'refs', 'gaps']
    assert 'short_title' in surfaces['gap']
    assert 'subdivision' in surfaces['cut']
    assert 'section' in body['units']


def test_a_stored_graph_is_an_edge_list_the_client_can_open():
    """The chart stays the static export. The edges are what a node click needs."""
    status, body = _json('/diagram/codes')
    assert status == '200 OK'
    assert body['chart'].startswith('flowchart')
    assert body['edges']
    edge = body['edges'][0]
    assert edge['label'] == 'cites'
    assert edge['weight'] >= 1
    assert edge['target_href'].startswith('/view/tree/us-ca/')
    status, body = _json('/diagram/enactments', 'code=WAT')
    assert body['found'] is True
    assert all(row['label'] == 'enacted' for row in body['edges'])


def test_a_walk_names_every_hop_and_every_edge():
    status, body = _json('/closure', 'code=CIV&section=1940&use=refs&hops=2')
    assert status == '200 OK'
    assert body['use'] == 'refs'
    assert body['citation'] == 'CIV 1940'
    hops = {row['id']: row['hop'] for row in body['nodes']}
    assert hops['CIV 1940'] == 0
    assert max(hops.values()) >= 1
    assert all(row['href'].startswith('/view/section/') for row in body['nodes'])
    assert {'source', 'target', 'label', 'source_href', 'target_href'} <= set(body['edges'][0])
    assert any(edge['source'] == 'CIV 1940' for edge in body['edges'])
    assert all(link['href'] or not link['section'] for link in body['links'])


def test_a_closure_reports_the_citations_the_links_missed():
    status, body = _json('/closure', 'code=CIV&section=1940&use=gaps&hops=0')
    assert status == '200 OK'
    assert body['use'] == 'gaps'
    assert isinstance(body['gaps'], list)
    for gap in body['gaps']:
        assert gap['gap'] in ('short_title', 'unresolved', 'unlinked')
        assert gap['phrase']
    status, body = _json('/closure', 'code=CIV&use=timeline')
    assert body['reason'] == 'unknown_use'


def test_the_sides_come_from_the_heading_already_opened():
    """``query.beside`` searches the same heading. The list is already in hand."""
    import query
    for number in ('1940', '1714.1'):
        status, body = _json('/section/CIV/%s' % number)
        assert status == '200 OK'
        beside = query.beside('CIV', number)
        assert body['previous'] == beside['previous']
        assert body['next'] == beside['next']


def test_the_document_inside_noscript_holds_no_nested_block():
    """A nested ``noscript`` would close the one the reader opens."""
    status, body, _headers = _get('/reader/section/CIV/1940')
    page = body.decode('utf-8')
    assert page.count('<noscript>') == 1
    assert page.count('</noscript>') == 1
    kept = page.split('<noscript>')[1].split('</noscript>')[0]
    assert 'class="mermaid"' not in kept
    assert 'CIV 1940' in kept


def _spans(body, path='0.0'):
    return body['spans'][path]


def test_every_reading_is_a_span_on_the_cut_it_sits_in():
    """Readings overlap, so the reply is spans and not one flat slice."""
    status, body = _json('/marks/CIV/1940')
    assert status == '200 OK'
    assert body['citation'] == 'CIV 1940'
    status, section = _json('/section/CIV/1940')
    paths = []

    def walk(node):
        paths.append(node['path'])
        for child in node['children']:
            walk(child)

    walk(section['nodes'])
    assert set(paths) == set(body['spans'])
    rows = _spans(body)
    layers = {row['layer'] for row in rows}
    assert {'note', 'canon', 'clause', 'needle'} <= layers
    opening = [row for row in rows if row['text'].startswith('Except')]
    assert {row['layer'] for row in opening} == {'note', 'clause', 'canon'}
    assert len({(row['start'], row['end']) for row in opening}) == 3
    assert len({row['start'] for row in opening}) == 1
    for row in rows:
        assert 0 <= row['start'] < row['end']


def test_a_citation_span_carries_the_book_the_sentence_named():
    """``Section 7280 of the Revenue and Taxation Code`` is RTC 7280."""
    status, body = _json('/marks/CIV/1940')
    assert status == '200 OK'
    cited = [
        row
        for rows in body['spans'].values()
        for row in rows
        if row['layer'] == 'note' and row['kind'] == 'citation'
    ]
    assert cited
    for row in cited:
        assert row['target'].split()[0].isalpha()
        assert row['href'] == '/view/section/%s' % row['target'].replace(' ', '/')
    assert any(row['target'] == 'RTC 7280' for row in cited)


def test_an_internal_reference_opens_the_heading_it_means():
    status, body = _json('/marks/CIV/1940')
    inside = [
        row
        for rows in body['spans'].values()
        for row in rows
        if row['text'].strip().lower() == 'this chapter'
    ]
    assert inside
    step = inside[0]
    assert step['href'].startswith('/view/tree/us-ca/civ/')
    assert step['href'].endswith('/chapter/2')
    assert step['detail']['resolved'].startswith('CHAPTER 2.')


def test_a_layer_narrows_the_reply_and_an_unknown_one_is_a_miss():
    status, body = _json('/marks/CIV/1940', 'layer=note,clause')
    assert status == '200 OK'
    kept = {row['layer'] for rows in body['spans'].values() for row in rows}
    assert kept <= {'note', 'clause'}
    assert set(body['counts']) <= {'note', 'clause'}
    status, body = _json('/marks/CIV/1940', 'layer=timeline')
    assert status == '404 Not Found'
    assert body['reason'] == 'unknown_layer'
    status, body = _json('/marks/CIV/999999999')
    assert status == '404 Not Found'
    assert body['found'] is False


def test_the_sections_that_name_this_one_are_the_stored_edges():
    status, body = _json('/citing', 'citation=RTC 7280')
    assert status == '200 OK'
    named = [row for row in body['rows'] if row['names']]
    assert any(row['citation'] == 'CIV 1940' for row in named)
    from indexer import Indexer
    stored = {
        (prior, receiver)
        for prior, receiver, _kind in Indexer().reference_edges('RTC 7280', limit=400)
    }
    for row in body['rows']:
        assert row['citation'] != 'RTC 7280'
        assert row['href'] == '/view/section/%s' % row['citation'].replace(' ', '/')
        pair = (row['citation'], 'RTC 7280') if row['names'] else ('RTC 7280', row['citation'])
        assert pair in stored, 'a row that is only a prefix of the citation'
    status, body = _json('/citing')
    assert status == '404 Not Found'


def test_the_layers_are_a_closed_set_too():
    status, body = _json('/surfaces')
    surfaces = body['surfaces']
    assert surfaces['layer'] == [
        'note', 'canon', 'clause', 'mention', 'relation', 'needle', 'abbreviation',
    ]
    assert 'mandatory' in surfaces['canon']
    assert 'short_title' in surfaces['clause']
