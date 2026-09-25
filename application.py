"""WSGI entry. ``application`` is the callable a server invokes.

``/`` is the plain HTML home page, inside ``noscript``, so a legacy browser
can open it. ``/tree``, ``/section``, ``/annotations``, and ``/view`` stay
available to link. React mounts on ``#root``. A GET reads
the local index. A miss is found false. The process environment and the data
directory are not served.
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
    if path[0] == 'view':
        return _view(start_response, path[1:], query, environ, hint)
    if path[0] == 'tree':
        return _tree(start_response, '/'.join(path[1:]))
    if path[0] == 'section' and len(path) >= 3:
        return _section(start_response, path[1], path[2], hint)
    if path == ['annotations']:
        return _annotations(start_response, query)
    if path == ['closure']:
        return _closure(start_response, query)
    if path == ['search']:
        return _search(start_response, query)
    if path == ['term']:
        return _term(start_response, query)
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
    import query
    node = query.law_tree(url)
    status = '200 OK' if node.get('found') else '404 Not Found'
    return _send(start_response, status, node)


def _section(start_response, code, number, hint=None):
    import query
    body = query.section(code, number)
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
        sides = query.beside(code, number)
        body['previous'] = sides.get('previous')
        body['next'] = sides.get('next')
        body['pieces'] = _pieces(body.get('text') or '')
        body['links'] = _cited(body.get('text') or '', code)
    status = '200 OK' if body.get('found', True) else '404 Not Found'
    return _send(start_response, status, body)


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


def _closure(start_response, query):
    """The citation the React client closed over. Each filter is one query field."""
    from places import ask
    sent = {name: _one(query, name) for name in (
        'use', 'code', 'division', 'title', 'part', 'chapter', 'article',
        'section', 'subdivision', 'through', 'session', 'hops', 'only', 'same',
        'q', 'limit',
    )}
    body = ask(sent)
    status = '200 OK' if body.get('found') else '404 Not Found'
    return _send(start_response, status, body)


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


def _section_crumbs(code, number, steps):
    parts = ['us-ca', (code or '').lower()]
    for step in steps or []:
        heading = step.get('heading') or ''
        matched = re.match(
            r'(?i)^(?:division|title|part|chapter|article)\s+([0-9]+(?:\.[0-9]+)*)',
            heading,
        )
        if step.get('level') and matched:
            parts.extend((step['level'], matched.group(1)))
    parts.extend(('section', str(number)))
    trail = _library_crumbs('/'.join(parts), _code_label(code))
    place = 3
    for step in steps or []:
        if place < len(trail) - 1 and step.get('heading'):
            trail[place]['label'] = step['heading']
            place += 1
    for crumb in trail:
        if crumb.get('unit') in ('division', 'title', 'part', 'chapter', 'article'):
            crumb['pieces'] = _pieces(crumb.get('label') or '', heading=True)
    return trail


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
    return {
        'href': href,
        'label': child.get('heading') or child.get('value') or child.get('url'),
        'unit': child.get('unit') or '',
        'pieces': _pieces(child.get('heading') or '', heading=True) if child.get('heading') else None,
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
    crumbs = _section_crumbs(code, number, steps)
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


def _nodes(text, code):
    """The section as a tree. Each label takes the cut that book uses at that depth."""
    from needles import Cut, breakdown
    from structure import Rank, split_nodes
    cuts = breakdown(code).members()
    letter = 'subsection' if Cut.SUBSECTION in cuts and Cut.SUBDIVISION not in cuts else 'subdivision'
    ladder = (letter, 'paragraph', 'subparagraph', 'clause')
    units = {
        Rank.LETTER: ladder[0],
        Rank.NUMBER: ladder[1],
        Rank.CAPITAL: ladder[2],
        Rank.CLAUSE: ladder[3],
        Rank.HEADING: 'section',
    }

    def pack(node):
        unit = 'section' if node.rank is None else units.get(node.rank, 'section')
        shown = ('%s %s' % (node.label, node.text)).strip() if node.label else (node.text or '')
        return {
            'unit': unit,
            'pieces': _pieces(shown),
            'children': [pack(child) for child in node.children],
        }

    return pack(split_nodes(text))


def _pieces(text, heading=False):
    """Plain slices of the section. A kind means that slice is a highlight."""
    from citations import Cite, annotate, heading_notes
    reader = heading_notes if heading else annotate
    notes = sorted(reader(text or ''), key=lambda note: (note.start, note.end))
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


def _piece_href(kind, target):
    """A citation that names a code and a section becomes a library link."""
    if kind not in ('citation', 'cross_reference'):
        return ''
    matched = re.match(r'^([A-Z]{2,})\s+(\d[\d.]*)', target or '')
    if matched is None:
        return ''
    return '/view/section/%s/%s' % (matched.group(1), matched.group(2))


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
    from structure import find_links
    links = []
    for link in find_links(text, here=code):
        if link.kind != 'statute' or not link.section or link.code is None:
            continue
        token = getattr(link.code, 'value', link.code)
        links.append({
            'href': '/view/section/%s/%s' % (token, link.section),
            'label': '%s %s' % (token, link.section),
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
