"""The WSGI callable answers GET and leaves a miss as found false."""

import json

from application import application


def _get(path, method='GET', query=''):
    seen = {}

    def start_response(status, headers):
        seen['status'] = status
        seen['headers'] = headers

    body = b''.join(application({
        'REQUEST_METHOD': method, 'PATH_INFO': path, 'QUERY_STRING': query,
    }, start_response))
    return seen['status'], json.loads(body)


def test_the_home_page_is_html_and_a_section_route_stays_json():
    status, raw = _get_raw('/')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'text/html' in dict(raw[1]).get('Content-Type', '')
    assert 'reader.js' not in page
    assert 'name="section"' in page
    assert 'Law Library' in page
    assert 'href="/view/tree/' in page
    status, body = _get('/section/CIV/1')
    assert status == '200 OK'
    assert body['found'] is True
    assert body['code'] == 'CIV'


def test_the_mirror_is_a_tree_of_files():
    status, raw = _get_raw('/mirror')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'href="/mirror/us-ca/' in page
    assert '<script' not in page
    status, raw = _get_raw('/mirror/us-ca/civ/section/1714.1')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert '<h1>CIV 1714.1</h1>' in page
    assert 'class="history"' in page
    assert 'href="/mirror/us-ca/civ"' in page
    assert '<script' not in page
    home, home_raw = _get_raw('/')
    assert home == '200 OK'
    assert 'href="/mirror"' in home_raw[0].decode('utf-8')


def test_a_code_lists_its_headings():
    status, raw = _get_raw('/view/tree/us-ca/civ')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'No further headings' not in page
    assert '/view/tree/us-ca/civ/division/' in page
    import re
    from query import heading_key
    divisions = re.findall(r'/view/tree/us-ca/civ/division/([^"/]+)', page)
    assert divisions
    assert divisions == sorted(divisions, key=heading_key)
    assert divisions[0] == '1'
    assert 'class="crumbs"' in page
    assert 'California' in page


def test_a_suffix_selects_the_representation():
    status, body = _get('/section/CIV/1714.1')
    assert status == '200 OK'
    assert body['code'] == 'CIV'
    status, raw = _get_raw('/section/CIV/1714.1.txt')
    text = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'text/plain' in dict(raw[1]).get('Content-Type', '')
    assert text.startswith('CIV 1714.1')
    assert '<html' not in text
    from application import _plain
    shaped = _plain({
        'citation': 'CIV 813',
        'path': [
            {'level': 'division', 'heading': 'DIVISION 2. PROPERTY'},
            {'level': 'title', 'heading': 'TITLE 2. ESTATES'},
            {'level': 'chapter', 'heading': 'CHAPTER 3. Servitudes'},
        ],
        'text': 'The holder',
    })
    assert '\nDIVISION 2. PROPERTY\n' in shaped
    assert '\n  TITLE 2. ESTATES\n' in shaped
    assert '\n      CHAPTER 3. Servitudes\n' in shaped
    assert '\n        The holder\n' in shaped
    status, raw = _get_raw('/section/CIV/1714.1.xml')
    page = raw[0].decode('utf-8')
    assert page.startswith('<?xml')
    assert 'href="/static/xml.css"' in page
    assert '<section code="CIV" number="1714.1">' in page
    status, raw = _get_raw('/section/CIV/1714.1.md')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'text/markdown' in dict(raw[1]).get('Content-Type', '')
    assert page.startswith('# CIV 1714.1')
    assert '```mermaid' in page
    assert '<html' not in page
    status, raw = _get_raw('/view/section/CIV/1714.1.pdf')
    assert raw[0].startswith(b'%PDF-1.4')
    assert 'application/pdf' in dict(raw[1]).get('Content-Type', '')
    status, raw = _get_raw('/section/CIV/1714.1.html')
    assert status == '200 OK'
    assert 'text/html' in dict(raw[1]).get('Content-Type', '')
    page = raw[0].decode('utf-8')
    assert 'CIV 1714.1' in page
    assert '<ol class="cuts">' in page
    assert 'class="cut-division"' in page
    assert 'class="cut-section"' in page
    assert '<ol class="contents">' in page
    assert 'aria-current="page"' in page


def test_a_refresh_opens_another_section(monkeypatch):
    import application
    monkeypatch.setattr(application, '_pick_section', lambda: ('CIV', '1714.1'))
    status, raw = _get_raw('/view/random')
    page = raw[0].decode('utf-8')
    headers = dict(raw[1])
    assert status == '200 OK'
    assert headers.get('Cache-Control') == 'no-store'
    assert 'CIV 1714.1' in page
    assert 'href="/view/random"' in page
    assert 'Another' in page
    assert 'class="legend"' in page
    assert '.txt' in page and '.html' in page and '.xml' in page and '.pdf' in page


def test_a_section_lists_each_cut():
    from application import _nodes
    tree = _nodes('(a) A duty.\n(1) A step.\n(A) A letter.\n(ii) A clause.', 'CIV')
    subdivision = tree['children'][0]
    assert subdivision['unit'] == 'subdivision'
    assert subdivision['children'][0]['unit'] == 'paragraph'
    assert subdivision['children'][0]['children'][0]['unit'] == 'subparagraph'
    assert subdivision['children'][0]['children'][0]['children'][0]['unit'] == 'clause'


def test_a_search_and_a_term_lookup_stay_misses_without_a_query():
    status, body = _get('/search')
    assert status == '404 Not Found'
    assert body['reason'] == 'not_in_index'
    status, body = _get('/term')
    assert body['found'] is False


def test_a_closure_keeps_the_filters_the_client_sent():
    """The heading, the year, and the books are one citation. An unknown use stays a miss."""
    status, body = _get('/closure', query='code=NOPE')
    assert status == '404 Not Found'
    assert body['reason'] == 'unknown_code'
    status, body = _get('/closure', query='code=CIV&use=timeline')
    assert body['reason'] == 'unknown_use'
    status, body = _get('/closure', query='code=CIV&division=1&part=2.52&section=55.51&same=1')
    assert status == '200 OK'
    assert body['use'] == 'read'
    assert body['filters']['division'] == '1'
    assert body['filters']['part'] == '2.52'
    assert body['filters']['section'] == '55.51'
    assert body['filters']['same'] is True
    assert body['section']['found'] is True
    status, body = _get('/closure', query='code=CIV&section=55.51&hops=0&same=1')
    assert body['use'] == 'refs'
    assert body['chart'].startswith('flowchart')
    assert body['edges'] == []


def test_a_missing_path_is_a_miss():
    status, body = _get('/env')
    assert status == '404 Not Found'
    assert body['found'] is False
    assert body['reason'] == 'not_found'


def test_the_reader_marks_a_sum_and_links_the_library():
    from application import _markup
    status, raw = _get_raw('/view')
    assert status == '200 OK'
    assert 'text/html' in dict(raw[1]).get('Content-Type', '')
    page = raw[0].decode('utf-8')
    assert 'href="/view/diagram/codes"' in page
    assert 'reader.js' not in page
    assert 'Law Library' in page
    assert 'htmx' not in page
    assert 'id="main"' in page
    from application import _ENV
    legend = _ENV.get_template('macros.html').module.legend()
    assert 'class="legend"' in legend
    assert 'note-session' in legend
    assert 'class="mermaid"' in page or 'mermaid' in page
    marked = _markup('The fee is $100.')
    assert 'class="note-amount"' in marked
    assert 'data-note="amount"' in marked
    assert '>$100</mark>' in marked
    from application import _piece_href
    assert _piece_href('citation', 'CIV 1714.1') == '/view/section/CIV/1714.1'
    assert _piece_href('cross_reference', 'WAT 12867') == '/view/section/WAT/12867'
    assert _piece_href('cut', 'paragraph') == ''


def _get_raw(path, **extra):
    seen = {}

    def start_response(status, headers):
        seen['status'] = status
        seen['headers'] = headers

    environ = {'REQUEST_METHOD': 'GET', 'PATH_INFO': path, 'QUERY_STRING': ''}
    environ.update(extra)
    body = b''.join(application(environ, start_response))
    return seen['status'], (body, seen['headers'])


def test_the_script_free_reader_is_a_full_page():
    status, raw = _get_raw('/view', HTTP_HX_REQUEST='true')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert page.startswith('<!DOCTYPE')
    assert 'href="/view/tree/' in page
    assert 'hx-get' not in page


def test_a_section_links_the_statutes_it_cites():
    status, raw = _get_raw('/view/section/CIV/1940')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'class="refs"' in page
    assert 'href="/view/section/RTC/7280"' in page
    assert 'class="ref-statute"' in page
    assert '<noscript>' in page


def test_a_section_shows_its_heading_and_the_next_section():
    status, raw = _get_raw('/view/open', QUERY_STRING='code=CIV&section=1714.1')
    page = raw[0].decode('utf-8')
    assert status == '200 OK'
    assert 'DIVISION 3. OBLIGATIONS' in page
    assert 'PART 3. OBLIGATIONS IMPOSED BY LAW' in page
    assert 'class="history"' in page
    assert 'Previous' in page
    assert 'Next' in page
    library, library_raw = _get_raw('/view')
    listing = library_raw[0].decode('utf-8')
    assert library == '200 OK'
    assert 'name="section"' in listing
    assert 'action="/view/open"' in listing


def test_a_post_is_not_served():
    status, body = _get('/', method='POST')
    assert status == '405 Method Not Allowed'
    assert body['reason'] == 'method'
