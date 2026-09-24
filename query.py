"""Structured statute queries over the local California Whoosh index.

Jason and MCP call this module. It does not download publications, and it
does not fetch Sacramento ordinances.
"""

import os
import re

from whoosh import index
from whoosh.query import And, Term

from indexer import WHOOSH_INDEX_BASEDIR, Indexer
from us.ca.counties.sacramento.cities.sacramento import Sacramento

HEADING_LEVELS = (
    ('division', 'DIVISION_HEADING'),
    ('title', 'TITLE_HEADING'),
    ('part', 'PART_HEADING'),
    ('chapter', 'CHAPTER_HEADING'),
    ('article', 'ARTICLE_HEADING'),
)

ACTS = {
    'davis-stirling': ('CIV', '4000', '6150'),
    'cid-manager': ('BPC', '11500', '11506'),
    'mutual-benefit': ('CORP', '7110', '8910'),
}

TEXT_SPAN_LIMIT = 30

_SECTION_NUM = re.compile(r'^\[?(?P<body>\d+(?:\.\d+)*)(?P<letter>[a-zA-Z]?)\]?\.?$')

_ORDINANCE = re.compile(
    r'(?is)'
    r'(?:sacramento\b.*\b(?:ordinance|municipal|city\s+code|county\s+code|mmc)\b)'
    r'|(?:\b(?:ordinance|municipal\s+code)\b.*\bsacramento\b)'
)

_ACT_NAME = re.compile(
    r'(?i)^\s*(?P<name>davis-stirling|cid-manager|mutual-benefit)\s*$'
)

_CODE_TOKEN = r'[A-Za-z][A-Za-z .]{0,60}?'

_SPAN = re.compile(
    rf'''(?ix)
    ^\s*
    (?P<code>{_CODE_TOKEN})
    \s+
    (?:sections?\s+|§§\s*|§\s*)?
    (?P<start>\d[\d.]*(?:[a-z])?)
    \s*(?:[-–—]|\bto\b)\s*
    (?P<end>\d[\d.]*(?:[a-z])?)
    \s*$
    '''
)

_SECTION = re.compile(
    rf'''(?ix)
    ^\s*
    (?P<code>{_CODE_TOKEN})
    \s+
    (?:section\s+|§\s*)?
    (?P<section>\d[\d.]*(?:[a-z])?)
    (?P<sub>(?:\([a-z0-9]+\))*)?
    \s*$
    '''
)


def section_key(number):
    """Sort key so 5375.5 sits between 5375 and 5376."""
    text = str(number or '').strip()
    matched = _SECTION_NUM.match(text)
    if not matched:
        return ((1 << 30,), '', text)
    parts = tuple(int(piece) for piece in matched.group('body').split('.'))
    letter = (matched.group('letter') or '').lower()
    return (parts, letter, text)


def _in_span(number, start, end):
    key = section_key(number)
    return section_key(start) <= key <= section_key(end)


def _miss(expression, reason):
    return {
        'found': False,
        'reason': reason,
        'expression': expression if expression is not None else '',
    }


def _indexer():
    return Indexer()


def _index_ready(idxer=None):
    idxer = idxer or _indexer()
    return index.exists_in(idxer.idx_path)


def _resolve_known_code(idxer, token):
    resolved = idxer._resolve_code(token)
    codes = idxer._read_codes()
    if resolved in codes:
        return resolved
    return None


def _session_value(idxer, session):
    if session is None:
        years = idxer.sessions()
        return years[-1] if years else None
    if session == 'all':
        return 'all'
    return str(session)


def _path_from_doc(doc):
    path = []
    for level, field in HEADING_LEVELS:
        heading = (doc.get(field) or '').strip()
        if heading:
            path.append({'level': level, 'heading': heading})
    return path


def _section_payload(doc, subdivision=None):
    code = doc.get('LAW_CODE')
    number = doc.get('SECTION_NUM')
    return {
        'found': True,
        'citation': doc.get('CITATION') or '%s %s' % (code, number),
        'code': code,
        'section': number,
        'subdivision': subdivision,
        'title': doc.get('SECTION_TITLE') or '',
        'path': _path_from_doc(doc),
        'text': doc.get('LEGAL_TEXT') or doc.get('text') or '',
        'session': doc.get('SESSION'),
        'active': bool(doc.get('ACTIVE_FLG', True)),
    }


def _docs_for_code(idxer, code, session=None):
    if not _index_ready(idxer):
        return []
    idx = index.open_dir(idxer.idx_path)
    with idx.searcher() as searcher:
        results = searcher.search(
            Term('LAW_CODE', code),
            limit=None,
            filter=idxer._filter(True, session),
        )
        return [dict(hit) for hit in results]


def _sections_in_span(idxer, code, start, end, session=None):
    docs = _docs_for_code(idxer, code, session=session)
    matched = [doc for doc in docs if _in_span(doc.get('SECTION_NUM'), start, end)]
    matched.sort(key=lambda doc: section_key(doc.get('SECTION_NUM')))
    return matched


def _outline_nodes(docs):
    nodes = []
    if not docs:
        return nodes
    for level, field in HEADING_LEVELS:
        current = None
        for doc in docs:
            heading = (doc.get(field) or '').strip()
            number = doc.get('SECTION_NUM')
            if not heading:
                if current is not None:
                    nodes.append(current)
                    current = None
                continue
            if current is None or current['heading'] != heading:
                if current is not None:
                    nodes.append(current)
                current = {
                    'level': level,
                    'heading': heading,
                    'first': number,
                    'last': number,
                    'count': 1,
                }
            else:
                current['last'] = number
                current['count'] += 1
        if current is not None:
            nodes.append(current)
    return nodes


def place(locality='Sacramento'):
    name = (locality or '').strip()
    if name.lower() != Sacramento.name.lower():
        return _miss(locality, 'not_in_index')
    return {
        'country': 'US',
        'region': Sacramento.region(),
        'locality': Sacramento.name,
        'statutes': Sacramento.region(),
        'ordinances': 'absent',
    }


def _get_section_doc(idxer, code, number, session=None):
    section_num = str(number).rstrip('.')
    idx = index.open_dir(idxer.idx_path)
    query = And([Term('LAW_CODE', code), Term('SECTION_NUM', section_num)])
    with idx.searcher() as searcher:
        results = searcher.search(query, limit=20, filter=idxer._filter(True, session))
        if not results:
            return None
        return dict(results[0])


def section(code, number, *, subdivision=None, session=None):
    expression = '%s %s' % (code or '', number or '')
    if subdivision:
        expression = '%s%s' % (
            expression.rstrip(),
            subdivision if str(subdivision).startswith('(') else '(%s)' % subdivision,
        )
    if not (code or '').strip() or number is None or str(number).strip() == '':
        return _miss(expression.strip(), 'not_in_index')
    idxer = _indexer()
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')
    doc = _get_section_doc(idxer, resolved, number, session=session)
    if doc is None:
        return _miss(expression.strip(), 'not_in_index')
    return _section_payload(doc, subdivision=subdivision)


def outline(code, start, end, *, session=None):
    expression = '%s %s-%s' % (code or '', start or '', end or '')
    if not (code or '').strip() or start is None or end is None:
        return _miss(expression.strip(), 'not_in_index')
    idxer = _indexer()
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')
    docs = _sections_in_span(idxer, resolved, start, end, session=session)
    if not docs:
        return _miss(expression.strip(), 'not_in_index')
    chosen = _session_value(idxer, session)
    return {
        'found': True,
        'code': resolved,
        'start': str(start).rstrip('.'),
        'end': str(end).rstrip('.'),
        'session': None if chosen == 'all' else chosen,
        'nodes': _outline_nodes(docs),
    }


def range(code, start, end, *, session=None, text=False):
    expression = '%s %s-%s' % (code or '', start or '', end or '')
    idxer = _indexer()
    if not (code or '').strip() or start is None or end is None:
        return _miss(expression.strip(), 'not_in_index')
    if not _index_ready(idxer):
        return _miss(expression.strip(), 'not_in_index')
    resolved = _resolve_known_code(idxer, code)
    if resolved is None:
        return _miss(expression.strip(), 'unknown_code')

    mutual = ACTS['mutual-benefit']
    is_mutual = (
        resolved == mutual[0]
        and section_key(start) == section_key(mutual[1])
        and section_key(end) == section_key(mutual[2])
    )

    docs = _sections_in_span(idxer, resolved, start, end, session=session)
    if not docs:
        return _miss(expression.strip(), 'not_in_index')

    if text and (is_mutual or len(docs) > TEXT_SPAN_LIMIT):
        result = outline(resolved, start, end, session=session)
        if result.get('found'):
            result['reason'] = 'span_too_large'
        return result

    if text:
        chosen = _session_value(idxer, session)
        return {
            'found': True,
            'code': resolved,
            'start': str(start).rstrip('.'),
            'end': str(end).rstrip('.'),
            'session': None if chosen == 'all' else chosen,
            'sections': [_section_payload(doc) for doc in docs],
        }

    return outline(resolved, start, end, session=session)


def search(query, *, code=None, start=None, end=None, limit=10, session=None):
    if query is None or str(query).strip() == '':
        return []
    if _ORDINANCE.search(str(query)):
        return []
    idxer = _indexer()
    if not _index_ready(idxer):
        return []

    resolved = None
    if code is not None and str(code).strip() != '':
        resolved = _resolve_known_code(idxer, code)
        if resolved is None:
            return []

    span_filter = resolved is not None or start is not None or end is not None
    fetch_limit = max(limit * 25, 50) if span_filter else limit
    hits = idxer.search_law(query, limit=fetch_limit, session=session)

    results = []
    for hit in hits:
        hit_code = hit.get('code')
        hit_section = hit.get('section')
        if resolved is not None and hit_code != resolved:
            continue
        if start is not None and end is not None and not _in_span(hit_section, start, end):
            continue
        if start is not None and end is None and section_key(hit_section) < section_key(start):
            continue
        if end is not None and start is None and section_key(hit_section) > section_key(end):
            continue
        doc = {
            'DIVISION_HEADING': hit.get('division'),
            'TITLE_HEADING': None,
            'PART_HEADING': hit.get('part'),
            'CHAPTER_HEADING': hit.get('chapter'),
            'ARTICLE_HEADING': hit.get('article'),
        }
        results.append({
            'citation': hit.get('citation'),
            'code': hit_code,
            'section': hit_section,
            'path': _path_from_doc(doc),
            'snippet': hit.get('snippet') or '',
            'session': hit.get('session'),
        })
        if len(results) >= limit:
            break
    return results


def act(name, *, session=None):
    key = (name or '').strip().lower()
    if not key:
        return _miss(name, 'unknown_act')
    if key not in ACTS:
        return _miss(name, 'unknown_act')
    code, start, end = ACTS[key]
    return outline(code, start, end, session=session)


def parse_citation(expression):
    """Parse a citation string into a structured ask, or a miss dict."""
    text = expression if expression is not None else ''
    stripped = str(text).strip()
    if not stripped:
        return _miss(stripped, 'not_in_index')
    if _ORDINANCE.search(stripped):
        return _miss(stripped, 'ordinance_absent')

    act_match = _ACT_NAME.match(stripped)
    if act_match:
        return {
            'kind': 'act',
            'name': act_match.group('name').lower(),
            'expression': stripped,
        }

    span_match = _SPAN.match(stripped)
    if span_match:
        return {
            'kind': 'span',
            'code': span_match.group('code').strip(),
            'start': span_match.group('start').rstrip('.'),
            'end': span_match.group('end').rstrip('.'),
            'expression': stripped,
        }

    section_match = _SECTION.match(stripped)
    if section_match:
        sub = section_match.group('sub') or None
        return {
            'kind': 'section',
            'code': section_match.group('code').strip(),
            'section': section_match.group('section').rstrip('.'),
            'subdivision': sub,
            'expression': stripped,
        }

    return _miss(stripped, 'not_in_index')


def cite(expression, *, session=None):
    parsed = parse_citation(expression)
    if parsed.get('found') is False:
        return parsed
    kind = parsed['kind']
    if kind == 'act':
        return act(parsed['name'], session=session)
    if kind == 'span':
        return outline(parsed['code'], parsed['start'], parsed['end'], session=session)
    if kind == 'section':
        return section(
            parsed['code'],
            parsed['section'],
            subdivision=parsed.get('subdivision'),
            session=session,
        )
    return _miss(expression, 'not_in_index')


def index_path():
    return WHOOSH_INDEX_BASEDIR


def index_present():
    return os.path.isdir(WHOOSH_INDEX_BASEDIR) and index.exists_in(WHOOSH_INDEX_BASEDIR)
