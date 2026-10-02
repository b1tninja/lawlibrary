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
    # The publisher's tree: the Civil Code opens with headings that have no
    # number, then its divisions, each addressed by its node.
    first = body['contents'][0]
    assert first['href'].startswith('/view/tree/us-ca/civ/node/')
    assert first['unit'] == 'unnumbered' and first['label']
    assert 'division' in {row['unit'] for row in body['contents']}


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
    # What a session law did to the section is a closed set too, so the
    # reader can name it rather than printing the credit and nothing else.
    assert surfaces['action'][:2] == ['added', 'amended']
    assert 'repealed and added' in surfaces['action']
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


def test_a_heading_answers_with_the_words_its_sections_carry():
    """One pass over the rows the index wrote, not over the words again."""
    status, body = _json('/cloud', 'url=us-ca/civ/division/3/title/5/part/4/chapter/2')
    assert status == '200 OK'
    assert body['code'] == 'CIV'
    assert body['leaves']
    assert body['tree']['unit'] == 'code'
    families = {'term', 'note', 'act', 'body'}
    for leaf in body['leaves']:
        assert set(leaf['counts']) == families
        assert leaf['id'] == '%s %s' % (leaf['code'], leaf['num'])
    opened = next(leaf for leaf in body['leaves'] if leaf['id'] == 'CIV 1940')
    assert opened['counts']['term'].get('shall')
    assert opened['counts']['note'].get('citation')
    assert 'Revenue and Taxation Code' in opened['counts']['act']

    def walk(node, depth=0):
        yield node, depth
        for child in node.get('children') or []:
            yield from walk(child, depth + 1)

    units = [node['unit'] for node, _depth in walk(body['tree'])]
    assert units[0] == 'code'
    assert 'section' in units
    captions = {node['unit']: node['label'] for node, _depth in walk(body['tree'])}
    assert captions['title'].startswith('TITLE 5.')


def test_a_word_points_at_the_codes_that_use_it():
    """Every section of one heading shares a code, so the reach is the index's."""
    status, body = _json('/cloud', 'url=us-ca/civ/division/3/title/5/part/4/chapter/2')
    books = body['books']
    assert books['term|shall']
    assert len(books['term|shall']) > 1
    assert max(books['term|shall'], key=books['term|shall'].get) != 'CIV'
    assert books['note|citation']
    status, body = _json('/cloud', 'url=us-ca/nope/division/1')
    assert status == '404 Not Found'
    assert body['reason'] == 'unknown_code'
    status, body = _json('/cloud')
    assert status == '404 Not Found'


def test_a_representation_reads_the_same_ladder_the_reader_draws():
    """A caption is filed on the unit its own words name, not the stored field.

    CIV 1940 keeps ``TITLE 5. HIRING`` on the part field, and the part it
    displaced has no caption of its own. The trail settles that, so the text,
    the Markdown and the XML all name four rungs in the order the reader shows
    them.
    """
    status, body = _json('/section/CIV/1940')
    assert status == '200 OK'
    drawn = [
        (crumb['unit'], crumb['label'])
        for crumb in body['crumbs']
        if crumb['unit'] in ('division', 'title', 'part', 'chapter')
    ]
    assert [unit for unit, _label in drawn] == ['division', 'title', 'part', 'chapter']
    title = dict(drawn)['title']
    part = dict(drawn)['part']

    status, raw, _headers = _get('/section/CIV/1940.md')
    page = raw.decode('utf-8')
    assert status == '200 OK'
    rungs = [row for row in page.splitlines() if row.lstrip().startswith('- ')]
    assert [row.strip()[2:] for row in rungs[:4]] == [label for _unit, label in drawn]
    # The ladder nests, one step per rung.
    assert [len(row) - len(row.lstrip()) for row in rungs[:4]] == [0, 2, 4, 6]

    status, raw, _headers = _get('/section/CIV/1940.xml')
    document = raw.decode('utf-8')
    assert '<heading level="title">%s</heading>' % title in document
    assert '<heading level="part">%s</heading>' % part in document

    from application import _CUT_INDENT
    status, raw, _headers = _get('/section/CIV/1940.txt')
    lines = raw.decode('utf-8').splitlines()
    # Each rung steps in by its own cut, so the depth is the unit and not the
    # order the index happened to store it in.
    for unit, label in drawn:
        assert (' ' * _CUT_INDENT[unit]) + label in lines


def test_the_markdown_is_the_section_cut_by_cut():
    """One block per cut, so a subdivision reads as a subdivision.

    A section with no cuts is one block, which is the whole of it — the page
    was empty before, because the only row it had was the one being hidden.
    """
    status, raw, _headers = _get('/section/CIV/1940.md')
    page = raw.decode('utf-8')
    assert status == '200 OK'
    blocks = [block.strip() for block in page.split('\n\n') if block.strip()]
    lettered = [block for block in blocks if block.startswith('(a)')]
    assert lettered, 'the first subdivision is its own block'
    assert any(block.startswith('(b)') for block in blocks)
    assert any(block.startswith('(1)') for block in blocks)
    # Every cut is on the page, once. The stored text runs a label into its
    # words as ``(a)Except``; a block is the label and then the words, so the
    # Markdown reads the way the reader shows it.
    status, section = _json('/section/CIV/1940')

    def walk(node, held):
        words = ''.join(piece.get('text') or '' for piece in node.get('pieces') or []).strip()
        if len(words) > 40:
            held.append(words)
        for kid in node.get('children') or []:
            walk(kid, held)
        return held

    for words in walk(section['nodes'], []):
        assert page.count(words) == 1, words[:60]

    status, raw, _headers = _get('/section/CIV/1860.md')
    lone = raw.decode('utf-8')
    assert 'If an innkeeper' in lone
    assert '## History' in lone
    # Nothing cites CIV 1860 here, so there is no chart of one node and no
    # list of references that only repeats the history line.
    assert '## Diagram' not in lone
    assert 'mermaid' not in lone
    assert '## Sections this one names' not in lone


def test_a_rung_says_what_it_is_and_how_much_it_holds():
    """A contents list of bare numbers is not a choice a reader can make.

    California's codes do not share one ladder — the Civil Code runs division,
    part, title and the Penal Code runs part, title, division — and a caption
    is filed on whichever field the publisher counted as deepest. Every Penal
    Code division has an empty DIVISION_HEADING, so its caption is read back
    from its own words.
    """
    status, body = _json('/tree/us-ca/pen')
    assert status == '200 OK'
    rows = body['contents']
    # The publisher's tree: the Penal Code opens with its preliminary
    # headings and then its parts, each with its caption and its node.
    assert rows and {row['unit'] for row in rows} == {'unnumbered', 'part'}
    for row in rows:
        if row['unit'] == 'part':
            assert row['label'].upper().startswith('PART %s.' % row['short'])
        assert row['label'] and row['pieces'], 'a caption is marked up like any other heading'
        assert row['href'].startswith('/view/tree/us-ca/pen/node/')
    # The caption carries the publisher's own span, so no second one is sent.
    assert not any(row.get('first') for row in rows)


def test_a_numbered_address_still_walks_the_unit_fields():
    """``division/1`` is a filter on the unit fields, not a node, and keeps its walk."""
    status, body = _json('/tree/us-ca/pen/division/1')
    assert status == '200 OK'
    rows = body['contents']
    assert rows
    for row in rows:
        assert row['label'] and row['short']
        assert row['sections'] > 0
        assert not row['href'].startswith('/view/tree/us-ca/pen/node/')


def test_a_lettered_rung_finds_its_own_caption():
    """``TITLE 1A`` is a rung. Reading only the digits made it ``TITLE 1``."""
    status, body = _json('/tree/us-ca/civ/division/3')
    lettered = [row for row in body['contents'] if row['short'] == '1A']
    assert lettered, 'CIV division 3 has a title 1A'
    assert lettered[0]['label'].upper().startswith('TITLE 1A.')


def test_a_bracketed_section_does_not_end_the_span():
    """A bracketed number is the section the publisher wrote out in words.

    It sorts after every plain one, so taken as the end of a span it would
    report a division as running to ``[50.]`` rather than to its last section.
    Which numbers are bracketed is an edition's business; that some are, and
    that they sort last, is the rule this holds.
    """
    import query
    from application import _widen
    assert query.section_key('[50.]') > query.section_key('86')

    row = {'sections': 0, 'first': '', 'last': ''}
    for number in ('38', '[50.]', '86'):
        _widen(row, number, query)
    assert (row['first'], row['last']) == ('38', '86')

    status, body = _json('/tree/us-ca/civ')
    assert body['found'] is True
    assert all(
        not row.get('first') or row['first'][:1].isdigit()
        for row in body['contents']
    )
