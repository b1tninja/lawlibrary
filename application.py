"""WSGI entry. ``application`` is the callable a server invokes.

``/`` is the plain HTML home page and ``/view`` is the script-free reader.
``/reader`` is the same library with the React client on ``#root``; the
document stays inside ``noscript`` there, so a deep link is a page before the
script runs. ``/tree``, ``/section``, ``/surfaces``, ``/annotations``, and
``/closure`` are the JSON the client reads. A GET reads the local index. A
miss is found false. The process environment and the data directory are not
served.
"""

import enum
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

class Hint(enum.Enum):
    """A path suffix that selects a representation. The section number stays the stem."""

    HTML = 'html'
    TEXT = 'txt'
    XML = 'xml'
    PDF = 'pdf'
    MARKDOWN = 'md'


def _take_hint(path):
    """Drop a known suffix from the last segment. ``1714.1.txt`` is section 1714.1."""
    if not path:
        return path, None
    stem, dot, ext = path[-1].rpartition('.')
    try:
        hint = Hint(ext.lower()) if dot and stem else None
    except ValueError:
        hint = None
    if hint is None:
        return path, None
    return path[:-1] + [stem], hint


_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / 'templates'),
    autoescape=select_autoescape(['html']),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _source_stamp():
    """Python files and templates. The development server restarts when one changes."""
    root = Path(__file__).resolve().parent
    paths = list(root.glob('*.py')) + list((root / 'templates').glob('*.html'))
    paths.append(root / 'static' / 'reader.js')
    return tuple(sorted(
        (str(path), path.stat().st_mtime_ns)
        for path in paths
        if path.is_file()
    ))


def serve(port=8765):
    """Bind 127.0.0.1. A changed source file replaces this process and keeps the port."""
    from wsgiref.simple_server import make_server
    stamp = _source_stamp()
    server = make_server('127.0.0.1', int(port), application)
    server.timeout = 0.5
    while True:
        server.handle_request()
        if _source_stamp() != stamp:
            server.server_close()
            subprocess.Popen(
                [sys.executable, '-c', 'from application import serve\nimport sys\nserve(sys.argv[1])\n', str(port)],
                cwd=str(Path(__file__).resolve().parent),
            )
            os._exit(0)


def application(environ, start_response):
    """One request. Only GET is served."""
    if environ.get('REQUEST_METHOD', 'GET') != 'GET':
        return _send(start_response, '405 Method Not Allowed', {'found': False, 'reason': 'method'})
    path = [part for part in (environ.get('PATH_INFO') or '/').split('/') if part]
    path, hint = _take_hint(path)
    query = parse_qs(environ.get('QUERY_STRING') or '')
    if not path:
        body = _tree_html('')
        if body is None:
            return _html(start_response, '404 Not Found', _page('Not found', _missing('That node is not in the index.'), index=True))
        return _html(start_response, '200 OK', _page('Law library', body, index=True))
    if path[0] == 'static' and len(path) == 2:
        return _static(start_response, path[1])
    if path[0] == 'mirror':
        return _mirror(start_response, '/'.join(path[1:]), hint)
    if path[0] == 'reader':
        return _reader(start_response, path[1:], query)
    if path[0] == 'view':
        return _view(start_response, path[1:], query, environ, hint)
    if path[0] == 'tree':
        return _tree(start_response, '/'.join(path[1:]))
    if path[0] == 'section' and len(path) >= 3:
        return _section(start_response, path[1], path[2], hint, _one(query, 'session') or None)
    if path == ['annotations']:
        return _annotations(start_response, query)
    if path == ['closure']:
        return _closure(start_response, query)
    if path == ['search']:
        return _search(start_response, query)
    if path == ['term']:
        return _term(start_response, query)
    if path[0] == 'marks' and len(path) >= 3:
        return _marks(start_response, path[1], path[2], query)
    if path == ['citing']:
        return _citing(start_response, query)
    if path == ['surfaces']:
        return _surfaces(start_response)
    if path == ['codes']:
        return _code_list(start_response)
    if path == ['sessions']:
        return _sessions(start_response)
    if path == ['outline']:
        return _outline(start_response, query)
    if path == ['cite']:
        return _cite(start_response, query)
    if path[0] == 'diagram' and len(path) == 2 and path[1] in ('codes', 'vesting', 'enactments'):
        return _diagram(start_response, path[1], query)
    return _send(start_response, '404 Not Found', {'found': False, 'reason': 'not_found'})


def _static(start_response, name):
    """One built client file. A name with a slash is a miss."""
    if name not in ('reader.js', 'reader.css', 'xml.css') or '/' in name or '\\' in name:
        return _send(start_response, '404 Not Found', {'found': False, 'reason': 'not_found'})
    path = Path(__file__).resolve().parent / 'static' / name
    if not path.is_file():
        return _send(start_response, '404 Not Found', {'found': False, 'reason': 'not_found'})
    payload = path.read_bytes()
    kind = 'text/javascript; charset=utf-8' if name.endswith('.js') else 'text/css; charset=utf-8'
    start_response('200 OK', [
        ('Content-Type', kind),
        ('Content-Length', str(len(payload))),
        ('Cache-Control', 'no-cache'),
    ])
    return [payload]


def _tree(start_response, url):
    """One node of the library. ``contents`` is that node's children as links."""
    import query
    node = query.law_tree(url)
    if node.get('found'):
        node['crumbs'] = _library_crumbs(
            node.get('url') or 'us-ca', _code_label(node.get('code')),
        )
        node['contents'] = [_child(node, child) for child in node.get('children') or []]
    status = '200 OK' if node.get('found') else '404 Not Found'
    return _send(start_response, status, node)


def _surfaces(start_response):
    """Every closed set the marks, the graph, and the filters are drawn from.

    A member is the word a file may store. The client renders a legend and a
    filter from this reply instead of keeping its own copy of the words.
    """
    from canons import Canon
    from citations import Cite, Join, Note, Quantity
    from lexical import Clause
    from marks import Layer
    from mentions import Kind, Relation
    from needles import Cut
    from places import Use
    from publication import Instrument
    from structure import Gap
    sets = {
        'layer': Layer, 'note': Note, 'canon': Canon, 'clause': Clause,
        'cite': Cite, 'join': Join, 'cut': Cut, 'kind': Kind,
        'relation': Relation, 'quantity': Quantity, 'gap': Gap, 'use': Use,
        'instrument': Instrument, 'hint': Hint,
    }
    return _send(start_response, '200 OK', {
        'found': True,
        'surfaces': {
            name: [member.value for member in members]
            for name, members in sets.items()
        },
        'units': list(_CUT_INDENT),
    })


def _section(start_response, code, number, hint=None, session=None):
    import query
    body = query.section(code, number, session=session or None)
    if hint is Hint.HTML:
        page = _section_html(code, number) if body.get('found', True) else None
        if page is None:
            return _html(start_response, '404 Not Found', _page('Not found', _missing('That section is not in the index.')))
        return _html(start_response, '200 OK', _page('Law library', page))
    if hint in (Hint.TEXT, Hint.XML, Hint.PDF, Hint.MARKDOWN):
        if not body.get('found', True):
            return _bytes(start_response, '404 Not Found', b'', _hint_type(hint))
        return _bytes(start_response, '200 OK', _represent(body, hint), _hint_type(hint))
    if body.get('found', True) and body.get('text') is not None:
        steps = [step for step in body.get('path') or [] if step.get('heading')]
        crumbs = _section_crumbs(
            body.get('code') or code, number, steps, body.get('units'),
        )
        contents = _parent_contents(
            crumbs, '/view/section/%s/%s' % (body.get('code') or code, number),
        )
        sides = _sides(contents) or query.beside(code, number)
        body['contents'] = contents
        body['previous'] = sides.get('previous')
        body['next'] = sides.get('next')
        body['pieces'] = _pieces(body.get('text') or '')
        body['links'] = _cited(body.get('text') or '', body.get('code') or code)
        body['nodes'] = _nodes(body.get('text') or '', body.get('code') or code)
        body['credit'] = _pieces((body.get('history') or '').strip())
        body['crumbs'] = crumbs
        body['formats'] = _formats(body.get('code') or code, number)
    status = '200 OK' if body.get('found', True) else '404 Not Found'
    return _send(start_response, status, body)


def _sides(contents):
    """The sections on either side, read from the heading already opened.

    ``query.beside`` searches that same heading. When the rung above this
    section lists sections, the ordered list is already in hand, so the walk
    is not repeated. A rung that lists articles instead is None.
    """
    rows = [row for row in contents or [] if row.get('unit') == 'section']
    if len(rows) != len(contents or []) or not rows:
        return None
    place = next((index for index, row in enumerate(rows) if row.get('current')), None)
    if place is None:
        return None
    return {
        'previous': rows[place - 1]['short'] if place else None,
        'next': rows[place + 1]['short'] if place + 1 < len(rows) else None,
    }


def _marks(start_response, code, number, query):
    """Every reading a parser records on this section, cut by cut.

    A span is a layer, a kind, and two offsets into that cut's words. Spans
    overlap and nest, so the client draws them as layers and not as one flat
    slice. ``layer`` narrows the reply to one surface.
    """
    import marks as surface
    import query as law
    body = law.section(code, number, session=_one(query, 'session') or None)
    if not body.get('found', True):
        return _send(start_response, '404 Not Found', body)
    only = [word for word in (_one(query, 'layer') or '').split(',') if word]
    try:
        wanted = [surface.Layer(word) for word in only] or None
    except ValueError:
        return _send(start_response, '404 Not Found', {
            'found': False, 'reason': 'unknown_layer', 'expression': _one(query, 'layer'),
        })
    token = body.get('code') or code
    steps = [step for step in body.get('path') or [] if step.get('heading')]
    inside = _inside(_section_crumbs(token, number, steps, body.get('units')), token)
    drawn = {}
    tally = {}
    for path, _unit, node in _walk_cuts(body.get('text') or '', token):
        spans = surface.layers(_shown(node), code=token, only=wanted)
        drawn[path] = [_span(span, inside) for span in spans]
        for layer, kinds in surface.counts(spans).items():
            held = tally.setdefault(layer, {})
            for kind, many in kinds.items():
                held[kind] = held.get(kind, 0) + many
    return _send(start_response, '200 OK', {
        'found': True,
        'code': token,
        'section': body.get('section') or number,
        'citation': body.get('citation') or '',
        'spans': drawn,
        'counts': tally,
    })


def _inside(crumbs, code):
    """Where ``this chapter`` points, read from the ladder this section sits in."""
    found = {}
    for crumb in crumbs or []:
        unit = crumb.get('unit') or ''
        if unit in ('division', 'title', 'part', 'chapter', 'article', 'code'):
            found[unit] = {'href': crumb.get('href') or '', 'label': crumb.get('label') or ''}
    if 'code' in found:
        found['code']['label'] = _code_label(code)
    return found


_THIS = re.compile(r'(?i)^this\s+(?P<unit>division|title|part|chapter|article|code|section)\b')


def _span(span, inside):
    """One span the client can draw and open."""
    row = {
        'layer': span.layer.value,
        'kind': span.kind,
        'start': span.start,
        'end': span.end,
        'text': span.text,
        'target': span.target,
        'reading': span.reading,
        'detail': dict(span.detail or {}),
        'href': '',
    }
    if span.layer.value == 'note':
        row['href'] = _piece_href(span.kind, span.target)
        named = _THIS.match(span.text.strip())
        if not row['href'] and named is not None:
            step = inside.get(named.group('unit').lower())
            if step:
                row['href'] = step['href']
                row['detail']['resolved'] = step['label']
    return row


def _citing(start_response, query):
    """The sections that name this one. A stored citation edge points here."""
    from indexer import Indexer
    citation = (_one(query, 'citation') or '').strip()
    if not citation:
        return _send(start_response, '404 Not Found', {
            'found': False, 'reason': 'not_in_index', 'expression': '',
        })
    try:
        limit = max(1, min(int(_one(query, 'limit') or '40'), 200))
    except ValueError:
        limit = 40
    rows = []
    seen = set()
    edges = Indexer().reference_edges(citation, limit=min(400, limit * 8))
    for prior, receiver, kind in edges:
        if receiver == citation:
            other, names = prior, True
        elif prior == citation:
            other, names = receiver, False
        else:
            continue
        if other == citation or other in seen or len(rows) >= limit:
            continue
        seen.add(other)
        rows.append({
            'citation': other,
            'kind': kind,
            'href': _piece_href('citation', other),
            'names': names,
        })
    return _send(start_response, '200 OK', {
        'found': True,
        'citation': citation,
        'rows': rows,
    })


def _formats(code, number):
    """The same section in each representation a ``Hint`` names."""
    return [
        {'hint': hint.value, 'href': '/section/%s/%s.%s' % (code, number, hint.value)}
        for hint in Hint
    ]


def _occurrence(hit):
    """One search hit the client can open."""
    code = hit.get('code') or ''
    number = hit.get('section') or ''
    href = '/view/section/%s/%s' % (code, number) if code and number else ''
    return {
        'citation': hit.get('citation') or '',
        'code': code,
        'section': number,
        'snippet': hit.get('snippet') or hit.get('text') or '',
        'path': hit.get('path') or [],
        'href': href,
    }


def _search(start_response, query):
    """Whoosh full text. ``q`` is words, a phrase, or a citation. A span is a filter."""
    import query as law
    phrase = _one(query, 'q')
    if not phrase:
        return _send(start_response, '404 Not Found', {'found': False, 'reason': 'not_in_index', 'expression': ''})
    try:
        limit = max(1, min(int(_one(query, 'limit') or '10'), 50))
    except ValueError:
        limit = 10
    code = _one(query, 'code') or None
    start = _one(query, 'start') or None
    end = _one(query, 'end') or None
    session = _one(query, 'session') or None
    hits = law.search(phrase, code=code, start=start, end=end, limit=limit, session=session)
    return _send(start_response, '200 OK', {
        'found': True,
        'q': phrase,
        'hits': [_occurrence(hit) for hit in hits],
    })


def _indexed_frequency(term):
    """How many stored sections contain the analyzed token. A phrase stays unset."""
    from indexer import Indexer, _ANALYZER
    from whoosh import index as whoosh_index
    tokens = [token.text for token in _ANALYZER(term or '')]
    if len(tokens) != 1:
        return None
    idxer = Indexer()
    if not whoosh_index.exists_in(idxer.idx_path):
        return None
    ix = whoosh_index.open_dir(idxer.idx_path)
    with ix.searcher() as searcher:
        return searcher.doc_frequency('LEGAL_TEXT', tokens[0])


def _term(start_response, query):
    """A hover lookup. The term, its neighbors in the hits, and where else it occurs.

    ``q`` is the word or phrase. ``note`` and ``target`` select a stored
    annotation. ``code``, ``start``, and ``end`` are the same filters as search.
    """
    import query as law
    from indexer import Indexer
    from weight import glance
    phrase = _one(query, 'q')
    note = _one(query, 'note')
    target = _one(query, 'target')
    term = phrase or target
    if not term:
        return _send(start_response, '404 Not Found', {'found': False, 'reason': 'not_in_index', 'term': ''})
    try:
        limit = max(1, min(int(_one(query, 'limit') or '24'), 50))
    except ValueError:
        limit = 24
    code = _one(query, 'code') or None
    kind = 'annotation' if note else ('phrase' if ' ' in term.strip() else 'term')
    if note:
        rows = Indexer().annotations(note=note, code=code, target=target or phrase or None, limit=limit)
        occurrences = [
            _occurrence({'citation': row['citation'], 'code': row['code'], 'section': (row['citation'] or '').split(' ')[-1], 'snippet': row['text']})
            for row in rows
        ]
        glanced = glance(target or phrase, ((row['code'], row['text']) for row in rows))
    else:
        hits = law.search(
            phrase, code=code,
            start=_one(query, 'start') or None,
            end=_one(query, 'end') or None,
            limit=limit,
            session=_one(query, 'session') or None,
        )
        occurrences = [_occurrence(hit) for hit in hits]
        glanced = glance(phrase, ((hit.get('code'), hit.get('snippet') or '') for hit in hits))
    body = {
        'found': True,
        'term': term,
        'kind': kind,
        'frequency': {
            'pf': glanced.get('pf') or 0,
            'df': glanced.get('df') or 0,
            'indexed': None if note else _indexed_frequency(phrase),
        },
        'neighbors': glanced.get('neighbors') or [],
        'occurrences': occurrences,
    }
    if not occurrences and not glanced.get('found'):
        body['found'] = False
        body['reason'] = 'not_in_index'
        return _send(start_response, '404 Not Found', body)
    return _send(start_response, '200 OK', body)


def _code_list(start_response):
    """The books in the Legislature's order."""
    from indexer import Indexer
    rows = Indexer().list_codes()
    return _send(start_response, '200 OK', {'found': True, 'codes': rows})


def _sessions(start_response):
    """Publication years stored on the index."""
    from indexer import Indexer
    years = Indexer().sessions()
    return _send(start_response, '200 OK', {'found': True, 'sessions': years})


def _outline(start_response, query):
    """Headings between two section numbers. The text of each section stays out."""
    import query as law
    code = _one(query, 'code')
    start = _one(query, 'start')
    end = _one(query, 'end')
    session = _one(query, 'session') or None
    body = law.outline(code, start, end, session=session)
    status = '200 OK' if body.get('found') else '404 Not Found'
    return _send(start_response, status, body)


def _cite(start_response, query):
    """One expression: a section, a span, a named act, or a session credit."""
    import query as law
    expression = _one(query, 'q')
    session = _one(query, 'session') or None
    body = law.cite(expression, session=session)
    status = '200 OK' if body.get('found') else '404 Not Found'
    return _send(start_response, status, body)


def _diagram(start_response, kind, query):
    """A stored graph. ``chart`` is the flowchart. The client draws ``edges``."""
    from indexer import Indexer
    from structure import _chart
    code = _one(query, 'code') or None
    idxer = Indexer()
    if kind == 'codes':
        edges, label = idxer.code_edges(), 'cites'
    elif kind == 'enactments':
        edges, label = idxer.enactment_edges(code=code), 'enacted'
    else:
        edges, label = idxer.vesting_edges(code=code, kind='vesting'), 'vested'
    return _send(start_response, '200 OK', {
        'found': True,
        'kind': kind,
        'code': code or '',
        'chart': _chart(edges, label),
        'edges': [_edge(kind, row, label) for row in edges],
    })


def _edge(kind, row, label):
    """One stored edge. A fourth field is how many citations that pair holds."""
    source, target, edge_label = row[0], row[1], row[2]
    return {
        'source': source,
        'target': target,
        'label': edge_label or label,
        'weight': row[3] if len(row) > 3 else 1,
        'source_href': _node_href(kind, source),
        'target_href': _node_href(kind, target),
    }


def _node_href(kind, name):
    """A graph node that names a book or a section becomes a library link."""
    text = (name or '').strip()
    if kind == 'codes':
        return '/view/tree/us-ca/%s' % text.lower() if re.fullmatch(r'[A-Z]{2,}', text) else ''
    return _piece_href('citation', text)


def _closure(start_response, query):
    """The citation the React client closed over. Each filter is one query field."""
    from places import ask
    sent = {name: _one(query, name) for name in (
        'use', 'code', 'division', 'title', 'part', 'chapter', 'article',
        'section', 'subdivision', 'through', 'session', 'hops', 'only', 'same',
        'q', 'limit',
    )}
    body = ask(sent)
    _address(body)
    status = '200 OK' if body.get('found') else '404 Not Found'
    return _send(start_response, status, body)


def _address(body):
    """An href on each row a closure returned, so a node opens the next section."""
    for row in body.get('nodes') or []:
        row['href'] = _piece_href('citation', row.get('id') or '')
    for edge in body.get('edges') or []:
        edge['source_href'] = _piece_href('citation', edge.get('source') or '')
        edge['target_href'] = _piece_href('citation', edge.get('target') or '')
    for link in body.get('links') or []:
        token, number = link.get('code') or '', link.get('section') or ''
        link['href'] = '/view/section/%s/%s' % (token, number) if token and number else ''
    for gap in body.get('gaps') or []:
        token, number = gap.get('code') or '', gap.get('section') or ''
        gap['href'] = '/view/section/%s/%s' % (token, number) if token and number else ''
    for hit in body.get('hits') or []:
        token, number = hit.get('code') or '', hit.get('section') or ''
        hit['href'] = '/view/section/%s/%s' % (token, number) if token and number else ''
    return body


def _annotations(start_response, query):
    from indexer import Indexer
    note = _one(query, 'note')
    code = _one(query, 'code')
    target = _one(query, 'target')
    limit = _one(query, 'limit') or '24'
    try:
        capped = max(1, min(int(limit), 100))
    except ValueError:
        capped = 24
    rows = Indexer().annotations(note=note, code=code, target=target, limit=capped)
    return _send(start_response, '200 OK', {'found': True, 'annotations': rows})


def _one(query, name):
    values = query.get(name) or []
    return values[0] if values else ''


def _view(start_response, path, query, environ=None, hint=None):
    if path and path[0] == 'section' and len(path) >= 3 and hint in (Hint.TEXT, Hint.XML, Hint.PDF, Hint.MARKDOWN):
        return _section(start_response, path[1], path[2], hint)
    if not path:
        body = _tree_html('')
    elif path[0] == 'tree':
        body = _tree_html('/'.join(path[1:]))
    elif path[0] == 'section' and len(path) >= 3:
        body = _section_html(path[1], path[2])
    elif path == ['random']:
        picked = _pick_section()
        body = _section_html(picked[0], picked[1], again='/view/random') if picked else None
        if body is None:
            return _html(start_response, '404 Not Found', _page('Not found', _missing('That section is not in the index.')))
        return _html(start_response, '200 OK', _page('Law library', body), cache='no-store')
    elif path == ['open']:
        body = _section_html(_one(query, 'code'), _one(query, 'section'))
    elif path[0] == 'diagram' and len(path) >= 2 and path[1] in ('codes', 'vesting', 'enactments'):
        body = _diagram_html(path[1], _one(query, 'code'))
    else:
        return _html(start_response, '404 Not Found', _page('Not found', _missing('That page is not in the library.')))
    if body is None:
        return _html(start_response, '404 Not Found', _page('Not found', _missing('That node is not in the index.')))
    return _html(start_response, '200 OK', _page('Law library', body))


_READER_VIEWS = (
    'tree', 'section', 'search', 'cite', 'outline', 'diagram', 'closure',
    'annotations', 'graph',
)


def _reader(start_response, path, query):
    """The React reader. ``#root`` is the mount and ``noscript`` keeps the document.

    Every place the client can open is a path here, so a deep link is a page
    before the script runs. The script-free twin of that page is ``/view``.
    """
    if path and path[0] not in _READER_VIEWS:
        return _html(start_response, '404 Not Found', _render(
            'reader.html',
            title='Not found',
            main=Markup(_missing('That view is not in the reader.')),
        ))
    document = _render(
        'reader.html',
        title=_reader_title(path, query),
        main=Markup(_unscripted(_reader_document(path, query))),
    )
    return _html(start_response, '200 OK', document)


_NOSCRIPT = re.compile(r'(?is)<noscript>.*?</noscript>')
_MERMAID = re.compile(r'(?is)<pre class="mermaid">.*?</pre>')


def _unscripted(body):
    """The same words with nothing a script would have drawn.

    The flat page hides its flowchart inside a ``noscript`` block. Nested, that
    block would close the one this page opens, and the rest of the document
    would escape it, so both the block and the flowchart are dropped here.
    """
    return _MERMAID.sub('', _NOSCRIPT.sub('', body or ''))


def _reader_title(path, query):
    """The place, so a tab and a bookmark name the section and not the app."""
    if not path:
        return 'Law library'
    if path[0] == 'section' and len(path) >= 3:
        return '%s %s' % (path[1].upper(), path[2])
    if path[0] == 'tree':
        return ' '.join(part.upper() for part in path[1:3]) or 'Library'
    if path[0] == 'diagram' and len(path) >= 2:
        return path[1].title()
    asked = _one(query, 'q')
    return ('%s %s' % (path[0].title(), asked)).strip()


def _reader_document(path, query):
    """The words of that place without a script, for ``noscript`` and a crawler."""
    if not path:
        return _tree_html('') or _missing('That node is not in the index.')
    if path[0] == 'tree':
        return _tree_html('/'.join(path[1:])) or _missing('That node is not in the index.')
    if path[0] == 'section' and len(path) >= 3:
        return _section_html(path[1], path[2]) or _missing('That section is not in the index.')
    if path[0] == 'diagram' and len(path) >= 2 and path[1] in ('codes', 'vesting', 'enactments'):
        return _diagram_html(path[1], _one(query, 'code')) or _missing('That diagram is not stored.')
    return _tree_html('') or _missing('That node is not in the index.')


def _mirror(start_response, url, hint=None):
    """One HTML file per node. wget --mirror follows the links and saves the tree."""
    import query
    node = query.law_tree(url)
    if not node.get('found'):
        document = _render('mirror.html', title='Not found', parent='/mirror', text='', history='', children=[], previous='', following='')
        return _html(start_response, '404 Not Found', document)
    if node.get('section'):
        if hint in (Hint.TEXT, Hint.XML, Hint.PDF, Hint.MARKDOWN):
            import query
            body = query.section(node.get('code') or '', node.get('section') or '')
            if not body.get('found', True):
                return _bytes(start_response, '404 Not Found', b'', _hint_type(hint))
            return _bytes(start_response, '200 OK', _represent(body, hint), _hint_type(hint))
        return _html(start_response, '200 OK', _mirror_section(node))
    children = [
        {'href': '/mirror/' + child['url'], 'label': child.get('heading') or child.get('value') or child['url']}
        for child in node.get('children') or []
    ]
    document = _render(
        'mirror.html',
        title=node.get('url') or 'mirror',
        parent=_mirror_parent(node.get('url') or ''),
        text='',
        history='',
        children=children,
        previous='',
        following='',
    )
    return _html(start_response, '200 OK', document)


def _mirror_section(node):
    import query
    code = node.get('code') or ''
    number = node.get('section') or ''
    body = query.section(code, number)
    sides = query.beside(code, number)
    previous = _mirror_section_href(node, sides.get('previous')) if sides.get('previous') else ''
    following = _mirror_section_href(node, sides.get('next')) if sides.get('next') else ''
    return _render(
        'mirror.html',
        title=body.get('citation') or '%s %s' % (code, number),
        parent=_mirror_parent(node.get('url') or ''),
        text=body.get('text') or '',
        history=(body.get('history') or '').strip(),
        children=[],
        previous=previous,
        following=following,
        path=[step.get('heading') or '' for step in body.get('path') or [] if step.get('heading')],
    )


def _mirror_section_href(node, number):
    region = (node.get('region') or 'US-CA').lower()
    code = (node.get('code') or '').lower()
    return '/mirror/%s/%s/section/%s' % (region, code, number)


def _mirror_parent(url):
    parts = [part for part in (url or '').split('/') if part]
    units = {'division', 'title', 'part', 'chapter', 'article', 'section', 'subdivision'}
    if len(parts) >= 3 and parts[-2] in units:
        parts = parts[:-2]
    elif parts:
        parts = parts[:-1]
    if not parts:
        return ''
    return '/mirror/' + '/'.join(parts)


def _code_label(token):
    wanted = (token or '').upper()
    for row in _codes():
        if (row.get('token') or '').upper() == wanted:
            return row.get('label') or wanted
    return wanted


def _library_crumbs(url, code_label=''):
    """Library, then each heading, down to the open node. The last crumb is current."""
    parts = [part for part in (url or 'us-ca').split('/') if part]
    names = {
        'division': 'Division', 'title': 'Title', 'part': 'Part',
        'chapter': 'Chapter', 'article': 'Article', 'section': '§',
        'subdivision': 'Subdivision',
    }
    units = set(names)
    trail = [{'href': '/', 'label': 'Library', 'unit': 'library'}]
    walked = []
    if not parts:
        return trail
    if parts[0].lower() in ('us', 'us-ca'):
        trail.append({'href': '/view/tree/us', 'label': 'United States', 'unit': 'country'})
    if parts[0].lower() == 'us' and len(parts) == 1:
        return trail
    walked.append(parts[0])
    region = 'California' if parts[0].lower() == 'us-ca' else parts[0].upper()
    trail.append({'href': '/view/tree/' + '/'.join(walked), 'label': region, 'unit': 'region'})
    if len(parts) > 1:
        walked.append(parts[1])
        trail.append({
            'href': '/view/tree/' + '/'.join(walked),
            'label': code_label or parts[1].upper(),
            'unit': 'code',
        })
    index = 2
    while index + 1 < len(parts) and parts[index] in units:
        unit, value = parts[index], parts[index + 1]
        walked.extend((unit, value))
        if unit == 'section':
            href = '/view/section/%s/%s' % (parts[1].upper(), value)
        else:
            href = '/view/tree/' + '/'.join(walked)
        trail.append({'href': href, 'label': '%s %s' % (names[unit], value), 'unit': unit})
        index += 2
    return trail


_HEADING_UNIT = re.compile(
    r'(?i)^(?P<unit>division|title|part|chapter|article)\s+(?P<number>[0-9]+(?:\.[0-9]+)*)'
)


def _section_crumbs(code, number, steps, units=None):
    """The ladder above this section, and the heading that names each rung.

    The href is the unit and the number the index stored, so every rung of the
    trail is a node the tree can open. A caption says which unit it belongs to
    (``TITLE 5. HIRING`` is title 5), which is not always the field it was
    stored on; a rung with no caption keeps its unit and number.
    """
    rungs = list(units or [])
    if not rungs:
        for step in steps or []:
            matched = _HEADING_UNIT.match((step.get('heading') or '').strip())
            if matched is not None:
                rungs.append({
                    'level': matched.group('unit').lower(),
                    'value': matched.group('number'),
                    'heading': step.get('heading') or '',
                })
    parts = ['us-ca', (code or '').lower()]
    for rung in rungs:
        parts.extend((rung['level'], rung['value']))
    parts.extend(('section', str(number)))
    trail = _library_crumbs('/'.join(parts), _code_label(code))
    captions = _captions(steps)
    for crumb in trail:
        unit = crumb.get('unit')
        if unit in ('division', 'title', 'part', 'chapter', 'article'):
            crumb['label'] = captions.get((unit, crumb['label']), crumb['label'])
            crumb['pieces'] = _pieces(crumb['label'], heading=True)
    return trail


def _captions(steps):
    """Each heading filed under the unit its own words name.

    The key is the unit and the plain label ``Chapter 2``, which is what
    ``_library_crumbs`` writes before a caption replaces it. A heading that
    names no unit captions nothing.
    """
    names = {
        'division': 'Division', 'title': 'Title', 'part': 'Part',
        'chapter': 'Chapter', 'article': 'Article',
    }
    found = {}
    for step in steps or []:
        heading = (step.get('heading') or '').strip()
        matched = _HEADING_UNIT.match(heading)
        if matched is None:
            continue
        unit = matched.group('unit').lower()
        found[(unit, '%s %s' % (names[unit], matched.group('number')))] = heading
    return found


def _parent_contents(crumbs, current):
    """The ordered children of the heading that holds this section."""
    if len(crumbs) < 2:
        return []
    parent = crumbs[-2].get('href') or ''
    prefix = '/view/tree/'
    if not parent.startswith(prefix):
        return []
    import query
    node = query.law_tree(parent[len(prefix):])
    if not node.get('found'):
        return []
    rows = []
    for child in node.get('children') or []:
        item = _child(node, child)
        item['current'] = item['href'] == current
        rows.append(item)
    return rows


def _tree_html(url):
    import query
    node = query.law_tree(url)
    if not node.get('found'):
        return None
    if node.get('section') and node.get('code') and not (node.get('children') or []):
        return _section_html(node['code'], node['section'])
    children = [_child(node, child) for child in node.get('children') or []]
    crumbs = _library_crumbs(node.get('url') or 'us-ca', _code_label(node.get('code')))
    return _render(
        'tree.html',
        url=node.get('url') or 'us-ca',
        heading=crumbs[-1]['label'] if crumbs else 'Library',
        crumbs=crumbs,
        children=children,
        codes=_codes(),
    )


def _child(node, child):
    code = node.get('code') or ''
    if child.get('unit') == 'section' and code:
        href = '/view/section/%s/%s' % (code, child.get('value') or '')
    else:
        href = '/view/tree/' + child['url']
    heading = child.get('heading') or ''
    return {
        'href': href,
        'label': heading or child.get('value') or child.get('url'),
        'short': child.get('value') or heading,
        'unit': child.get('unit') or '',
        'pieces': _pieces(heading, heading=True) if heading else None,
    }


def _pick_section():
    """One current section. Each call may return a different code and number."""
    import random
    from whoosh import index
    import query
    if not query.index_present():
        return None
    idxer = query._indexer()
    codes = [row.get('code') for row in idxer.list_codes() if row.get('code')]
    if not codes:
        return None
    rng = random.SystemRandom()
    code = rng.choice(codes)
    session = query._session_value(idxer, None)
    chosen = None
    seen = 0
    opened = index.open_dir(idxer.idx_path)
    with opened.searcher() as searcher:
        for docnum in searcher.document_numbers(LAW_CODE=code):
            fields = searcher.stored_fields(docnum)
            if fields.get('ACTIVE_FLG') is False:
                continue
            if session not in (None, 'all') and fields.get('SESSION') not in (None, session):
                continue
            number = fields.get('SECTION_NUM')
            if not number:
                continue
            seen += 1
            if rng.randrange(seen) == 0:
                chosen = (code, number)
    return chosen


def _section_html(code, number, again=None):
    import query
    body = query.section(code, number)
    if not body.get('found', True):
        return None
    text = body.get('text') or ''
    edges, chart = _refs(code, number, body.get('chapters') or [])
    sides = query.beside(code, number)
    previous = sides.get('previous')
    following = sides.get('next')
    steps = [step for step in body.get('path') or [] if step.get('heading')]
    crumbs = _section_crumbs(code, number, steps, body.get('units'))
    current = '/view/section/%s/%s' % (code, number)
    return _render(
        'section.html',
        path=[step.get('heading') or '' for step in steps],
        crumbs=crumbs,
        contents=_parent_contents(crumbs, current),
        title=body.get('citation') or '%s %s' % (code, number),
        code=code,
        number=number,
        previous={'href': '/view/section/%s/%s' % (code, previous), 'label': previous} if previous else None,
        following={'href': '/view/section/%s/%s' % (code, following), 'label': following} if following else None,
        tree=_nodes(text, code),
        history=(body.get('history') or '').strip(),
        credit=_pieces((body.get('history') or '').strip()) if (body.get('history') or '').strip() else None,
        chart=chart,
        edges=edges,
        again=again,
    )


def _diagram_html(kind, code):
    from structure import Diagram
    diagram = getattr(Diagram, kind)()
    if kind != 'codes':
        if not code:
            return _render(
                'diagram.html',
                kind=kind,
                needs_code=True,
                example_href='/view/diagram/%s?code=GOV' % kind,
                chart='',
            )
        from apa import Code
        try:
            diagram = diagram.code(Code.get(code))
        except KeyError:
            return None
    return _render('diagram.html', kind=kind, needs_code=False, example_href='', chart=diagram.chart() or 'flowchart TD')


def _cut_units(code):
    """The word this book uses at each depth under a section."""
    from needles import Cut, breakdown
    from structure import Rank
    cuts = breakdown(code).members()
    letter = 'subsection' if Cut.SUBSECTION in cuts and Cut.SUBDIVISION not in cuts else 'subdivision'
    ladder = (letter, 'paragraph', 'subparagraph', 'clause')
    return {
        Rank.LETTER: ladder[0],
        Rank.NUMBER: ladder[1],
        Rank.CAPITAL: ladder[2],
        Rank.CLAUSE: ladder[3],
        Rank.HEADING: 'section',
    }


def _shown(node):
    """The words of one cut: its label, then its text."""
    return ('%s %s' % (node.label, node.text)).strip() if node.label else (node.text or '')


def _walk_cuts(text, code):
    """Each cut of the section, with the path that names it in the tree."""
    from structure import split_nodes
    units = _cut_units(code)
    rows = []

    def walk(node, trail):
        unit = 'section' if node.rank is None else units.get(node.rank, 'section')
        rows.append(('.'.join(trail), unit, node))
        for index, child in enumerate(node.children):
            walk(child, trail + [str(index)])

    walk(split_nodes(text), ['0'])
    return rows


def _nodes(text, code):
    """The section as a tree. Each label takes the cut that book uses at that depth."""
    from structure import split_nodes
    units = _cut_units(code)

    def pack(node, trail):
        unit = 'section' if node.rank is None else units.get(node.rank, 'section')
        return {
            'path': '.'.join(trail),
            'unit': unit,
            'label': node.label or '',
            'pieces': _pieces(_shown(node)),
            'children': [
                pack(child, trail + [str(index)])
                for index, child in enumerate(node.children)
            ],
        }

    return pack(split_nodes(text), ['0'])


def _pieces(text, heading=False):
    """Plain slices of the section. A kind means that slice is a highlight."""
    from citations import Cite, annotate, heading_notes
    reader = heading_notes if heading else annotate
    notes = sorted(reader(text or ''), key=lambda note: (note.start, note.end))
    kept = []
    for note in notes:
        if kept and note.start == kept[-1].start and note.end > kept[-1].end:
            kept[-1] = note
            continue
        if kept and note.start < kept[-1].end:
            continue
        kept.append(note)
    notes = kept
    pieces = []
    cursor = 0
    source = text or ''
    for note in notes:
        if note.start < cursor or note.end <= note.start:
            continue
        if cursor < note.start:
            pieces.append({'text': source[cursor:note.start], 'kind': '', 'title': ''})
        kind = str(getattr(note.note, 'value', note.note))
        cite = getattr(note, 'cite', None)
        cite_value = cite.value if cite is not None else ''
        title = str(note.target or kind)
        if cite is Cite.RANGE and note.target:
            title = 'range %s' % note.target
        pieces.append({
            'text': source[note.start:note.end],
            'kind': kind,
            'title': title,
            'cite': cite_value,
            'href': _piece_href(kind, str(note.target or '')),
        })
        cursor = note.end
    if cursor < len(source) or not pieces:
        pieces.append({'text': source[cursor:], 'kind': '', 'title': ''})
    return pieces


def _ancestors(region='US-CA'):
    """Jurisdictions above the open one. Look within before looking here."""
    if (region or '').upper() == 'US-CA':
        return ('US',)
    return ()


def _piece_href(kind, target):
    """A citation link. The open jurisdiction's codes come first.

    A token that is not one of those codes is tried in each ancestor.
    ``PL 101 336`` is not a California code. The United States reads it as
    a public law on Congress.gov.
    """
    if kind not in ('citation', 'cross_reference'):
        return ''
    matched = re.match(r'^([A-Z]{2,})\s+(\d[\d.]*)', target or '')
    if matched is not None:
        token = matched.group(1)
        if any((row.get('token') or '').upper() == token for row in _codes()):
            return '/view/section/%s/%s' % (token, matched.group(2))
    if 'US' in _ancestors():
        public = re.match(r'^PL\s+(\d+)\s+(\d+)$', target or '')
        if public is not None:
            from us.plaw import locate
            return locate(public.group(1), public.group(2))
        code = re.match(r'^USC\s+(\d+[a-z]?)\s+(\d[\d.a-z]*)$', target or '', re.I)
        if code is not None:
            from us.usc import locate_section
            return locate_section(code.group(1), code.group(2))
    return ''


def _refs(code, number, chapters):
    """One hop of the citation graph, as edges a page can link without a script."""
    from apa import Code
    from places import Citation
    try:
        book = Code.get(code)
    except KeyError:
        return [], ''
    node = Citation(book).section(str(number)).hops(1).refs
    tree = node.tree
    chart = node.chart or ''
    edges = []
    seen = set()

    def add(kind, source, target, label, href):
        key = (kind, source, target)
        if not target or key in seen:
            return
        seen.add(key)
        edges.append({
            'kind': kind,
            'source': source,
            'target': target,
            'label': label or target,
            'href': href,
        })

    def walk(item):
        here = item.get('id') or ''
        for link in item.get('links') or []:
            kind = link.get('kind') or ''
            if kind == 'statute' and link.get('section') and link.get('code') is not None:
                token = getattr(link['code'], 'value', link['code'])
                target = '%s %s' % (token, link['section'])
                add(kind, here, target, link.get('text') or '', '/view/section/%s/%s' % (token, link['section']))
            elif kind == 'session' and link.get('year') and link.get('chapter'):
                action = link.get('action') or ''
                target = ' '.join(part for part in (action, link['year'], link['chapter']) if part)
                add(kind, here, target, link.get('text') or '', '')
            elif kind == 'article' and link.get('section'):
                target = '%s %s' % (link.get('label') or '', link['section']).strip()
                add(kind, here, target, link.get('text') or '', '')
        for child in item.get('children') or []:
            walk(child)

    if tree.get('found'):
        walk(tree)
    source = tree.get('id') or '%s %s' % (code, number)
    for row in chapters or []:
        action = row.get('action') or ''
        target = ' '.join(part for part in (action, row.get('year'), row.get('chapter')) if part)
        add('session', source, target, target, '')
    return edges, chart


def _cited(text, code):
    """The statutes these words name, once each, in the order they appear."""
    from structure import find_links
    links = []
    seen = set()
    for link in find_links(text, here=code):
        if link.kind != 'statute' or not link.section or link.code is None:
            continue
        token = getattr(link.code, 'value', link.code)
        label = '%s %s' % (token, link.section)
        if label in seen:
            continue
        seen.add(label)
        links.append({
            'href': '/view/section/%s/%s' % (token, link.section),
            'label': label,
        })
    return links


def _markup(text):
    """The section text with each annotation wrapped. Overlapping marks are skipped."""
    return _ENV.get_template('macros.html').module.marks(_pieces(text))


def _codes():
    import query
    if not query.index_present():
        return []
    rows = []
    for row in query._indexer().list_codes():
        token = row.get('code') or ''
        rows.append({'token': token, 'label': row.get('title') or token})
    return rows


def _missing(message):
    return _render('missing.html', message=message)


def _page(title, main, index=False):
    """The library page is the document. index is accepted and unused."""
    return _render('page.html', title=title, main=Markup(main))


def _render(name, **context):
    return _ENV.get_template(name).render(**context)


def _hint_type(hint):
    return {
        Hint.HTML: 'text/html; charset=utf-8',
        Hint.TEXT: 'text/plain; charset=utf-8',
        Hint.XML: 'application/xml; charset=utf-8',
        Hint.PDF: 'application/pdf',
        Hint.MARKDOWN: 'text/markdown; charset=utf-8',
    }[hint]


def _represent(body, hint):
    if hint is Hint.TEXT:
        return _plain(body).encode('utf-8')
    if hint is Hint.XML:
        return _xml(body).encode('utf-8')
    if hint is Hint.MARKDOWN:
        return _markdown(body).encode('utf-8')
    return _pdf(_plain(body))


_CUT_INDENT = {
    'division': 0,
    'title': 2,
    'part': 4,
    'chapter': 6,
    'article': 8,
    'section': 10,
    'subdivision': 12,
    'subsection': 12,
    'paragraph': 14,
    'subparagraph': 14,
    'clause': 16,
    'subclause': 16,
    'item': 16,
    'subitem': 16,
}


def _plain(body):
    """The text file. Each heading steps in by its cut, then the section text."""
    lines = [body.get('citation') or '']
    depth = 0
    for step in body.get('path') or []:
        heading = (step.get('heading') or '').strip()
        if not heading:
            continue
        depth = _CUT_INDENT.get(step.get('level') or '', depth)
        lines.append((' ' * depth) + heading)
    text = (body.get('text') or '').strip()
    if text:
        pad = ' ' * (depth + 2)
        lines.append('\n'.join(pad + row for row in text.splitlines()))
    history = (body.get('history') or '').strip()
    if history:
        lines.append(history)
    return '\n\n'.join(lines) + '\n'


def _xml(body):
    def esc(value):
        return html.escape(value or '', quote=True)
    headings = ''.join(
        '<heading level="%s">%s</heading>' % (esc(step.get('level') or ''), esc(step.get('heading') or ''))
        for step in body.get('path') or []
        if step.get('heading')
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<?xml-stylesheet type="text/css" href="/static/xml.css"?>\n'
        '<section code="%s" number="%s">\n'
        '<citation>%s</citation>\n'
        '<path>%s</path>\n'
        '<text>%s</text>\n'
        '<history>%s</history>\n'
        '</section>\n'
    ) % (
        esc(body.get('code') or ''),
        esc(str(body.get('section') or '')),
        esc(body.get('citation') or ''),
        headings,
        esc(body.get('text') or ''),
        esc((body.get('history') or '').strip()),
    )


def _markdown(body):
    """The section as a Markdown page. The diagram is a fenced flowchart."""
    code = body.get('code') or ''
    number = str(body.get('section') or '')
    edges, chart = _refs(code, number, body.get('chapters') or [])
    lines = ['# %s' % (body.get('citation') or '%s %s' % (code, number)), '']
    for step in body.get('path') or []:
        heading = (step.get('heading') or '').strip()
        if heading:
            lines.append(heading)
            lines.append('')
    text = (body.get('text') or '').strip()
    if text:
        lines.append(text)
        lines.append('')
    history = (body.get('history') or '').strip()
    if history:
        lines.extend(('## History', '', history, ''))
    if edges:
        lines.extend(('## References', ''))
        for edge in edges:
            if edge.get('href'):
                lines.append('- [%s](%s)' % (edge['target'], edge['href']))
            else:
                lines.append('- %s' % edge['target'])
        lines.append('')
    if chart:
        lines.extend(('## Diagram', '', '```mermaid', chart, '```', ''))
    return '\n'.join(lines)


def _pdf(text):
    """One text page per block of lines. The words are the stored section."""
    lines = []
    for raw in text.splitlines() or ['']:
        row = raw.encode('latin-1', 'replace').decode('latin-1')
        while len(row) > 90:
            lines.append(row[:90])
            row = row[90:]
        lines.append(row)
    pages = [lines[index:index + 46] for index in range(0, len(lines), 46)] or [[]]
    objects = []
    kids = []

    def add(value):
        objects.append(value)
        return len(objects)

    font = add('<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman >>')
    for page_lines in pages:
        commands = ['BT', '/F1 11 Tf', '54 740 Td', '14 TL']
        for line in page_lines:
            safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
            commands.append('(%s) Tj T*' % safe)
        commands.append('ET')
        stream = '\n'.join(commands).encode('latin-1')
        contents = add('<< /Length %s >>\nstream\n%s\nendstream' % (len(stream), stream.decode('latin-1')))
        kids.append(add(
            '<< /Type /Page /Parent 0 0 R /MediaBox [0 0 612 792] '
            '/Resources << /Font << /F1 %s 0 R >> >> /Contents %s 0 R >>' % (font, contents)
        ))
    kids_ref = ' '.join('%s 0 R' % kid for kid in kids)
    catalog_pages = add('<< /Type /Pages /Count %s /Kids [%s] >>' % (len(kids), kids_ref))
    catalog = add('<< /Type /Catalog /Pages %s 0 R >>' % catalog_pages)
    for kid in kids:
        objects[kid - 1] = objects[kid - 1].replace('/Parent 0 0 R', '/Parent %s 0 R' % catalog_pages)
    out = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for number, value in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(('%s 0 obj\n' % number).encode('latin-1'))
        out.extend(value.encode('latin-1'))
        out.extend(b'\nendobj\n')
    startxref = len(out)
    out.extend(('xref\n0 %s\n' % (len(objects) + 1)).encode('latin-1'))
    out.extend(b'0000000000 65535 f \n')
    for offset in offsets[1:]:
        out.extend(('%010d 00000 n \n' % offset).encode('latin-1'))
    out.extend(('trailer << /Size %s /Root %s 0 R >>\nstartxref\n%s\n%%%%EOF\n' % (
        len(objects) + 1, catalog, startxref,
    )).encode('latin-1'))
    return bytes(out)


def _bytes(start_response, status, payload, content_type):
    start_response(status, [
        ('Content-Type', content_type),
        ('Content-Length', str(len(payload))),
    ])
    return [payload]


def _html(start_response, status, document, cache=None):
    payload = str(document).encode('utf-8')
    headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(payload))),
    ]
    if cache:
        headers.append(('Cache-Control', cache))
    start_response(status, headers)
    return [payload]


def _send(start_response, status, body):
    payload = json.dumps(body).encode('utf-8')
    start_response(status, [
        ('Content-Type', 'application/json; charset=utf-8'),
        ('Content-Length', str(len(payload))),
    ])
    return [payload]
