"""A reference that keeps the unit it was opened inside.

``division(4).part(1)`` is a closure: the part call remembers the division.
The same names are functions, and they close over the place entered with
``book``. ``read`` and ``find`` look the citation up. They do not carry a
copy of the section. The unit names come from the word registry, plus a bill line.
"""

import contextvars
import enum
import re

from needles import consider, cuts


def _units():
    names = []
    for cls in consider():
        if cls.internal:
            names.extend(cls.forms)
    names.extend(cuts())
    names.append('line')
    names.append('page')
    return tuple(dict.fromkeys(names))


_UNITS = frozenset(_units())
_MARKS = frozenset(cuts()) | {'line'}
_here = contextvars.ContextVar('place', default=None)


class Place:
    """One unit and the place that contains it."""

    def __init__(self, unit, number, parent, commencing=None, title=None):
        self.unit = unit
        self.number = number
        self.parent = parent
        self.commencing = commencing
        self.title = title

    def __getattr__(self, name):
        if name not in _UNITS:
            raise AttributeError(name)

        def bound(number=None, commencing=None):
            return Place(name, number, self, commencing)

        return bound

    def __enter__(self):
        self._token = _here.set(self)
        return self

    def __exit__(self, *exc):
        _here.reset(self._token)
        return False

    def _phrase(self):
        if self.unit == 'section':
            text = 'Section %s' % self.number
        elif self.unit in _MARKS:
            text = '%s (%s)' % (self.unit, self.number)
        else:
            text = '%s %s' % (self.unit[:1].upper() + self.unit[1:], self.number)
        if self.commencing:
            text += ' (commencing with Section %s)' % self.commencing
        return text

    def _code(self):
        here = self
        while here is not None:
            if here.unit == 'code':
                return here.number
            here = here.parent
        return None

    def _chain(self):
        chain = []
        here = self
        while here is not None and here.unit != 'code':
            chain.append(here)
            here = here.parent
        chain.reverse()
        return chain

    def _section(self):
        for place in self._chain():
            if place.unit == 'section' and place.number is not None:
                return str(place.number)
        return None

    def _covers(self, hit):
        """True when the hit sits inside every unit this place has open."""
        blob = ' '.join((item.get('heading') or '') for item in (hit.get('path') or []))
        for place in self._chain():
            if place.number is None:
                continue
            if place.unit == 'section':
                if str(hit.get('section')) != str(place.number):
                    return False
                continue
            if place.unit in _MARKS:
                continue
            if not re.search(
                r'(?i)\b%s %s\b' % (re.escape(str(place.unit)), re.escape(str(place.number))),
                blob,
            ):
                return False
        return True

    def read(self, session=None):
        """The stored section for this place. A place with no section is a miss.

        ``session`` is the publication year this place was opened in. A year
        that is not indexed stays a miss. It is not filled from another year.
        """
        import query
        code = self._code()
        number = self._section()
        if not code or not number:
            return {'found': False, 'reason': 'not_in_index', 'citation': self.reference()}
        return query.section(code, number, session=session)

    def find(self, phrase, limit=10):
        """Sections inside this place whose text matches ``phrase``.

        The words stay in the index. The result is the citation and a snippet.
        """
        import query
        code = self._code()
        if not code or not phrase:
            return []
        hits = query.search(phrase, code=code, limit=max(limit * 8, limit))
        kept = [hit for hit in hits if self._covers(hit)]
        return kept[:limit]

    def through(self, *, page=None, line=None):
        """The other end of a bill span: through page 15, line 11."""
        if page is None and line is None:
            raise TypeError('name the end page or line')
        nxt = Place(self.unit, self.number, self.parent, self.commencing, self.title)
        nxt.span_page = page
        nxt.span_line = line
        return nxt

    def reference(self):
        """The units from this one out to the code."""
        chain = self._chain()
        if any(place.unit == 'page' for place in chain):
            return _bill_sheet(
                chain,
                getattr(self, 'span_page', None),
                getattr(self, 'span_line', None),
            )
        bits = []
        here = self
        while here is not None and here.unit != 'code':
            bits.append(here._phrase())
            here = here.parent
        if here is not None and here.unit == 'code':
            bits.append('the %s' % (here.title or here.number))
        return ' of '.join(bits)


def _bill_sheet(chain, span_page, span_line):
    """Page 12, line 5, and a span through page 15, line 11."""
    page = next((place.number for place in chain if place.unit == 'page'), None)
    line = next((place.number for place in chain if place.unit == 'line'), None)
    bits = []
    if page is not None:
        bits.append('Page %s' % page)
    if line is not None:
        bits.append('line %s' % line)
    text = ', '.join(bits)
    end = []
    if span_page is not None:
        end.append('page %s' % span_page)
    if span_line is not None:
        end.append('line %s' % span_line)
    if end:
        text += ' through %s' % ', '.join(end)
    return text


def _sibling_phrase(labels):
    """subdivisions (a) and (b), using the rank of the first label."""
    from structure import _mark_unit
    unit = _mark_unit(labels[0])
    marks = ['(%s)' % label for label in labels]
    if len(marks) == 2:
        body = '%s and %s' % tuple(marks)
    else:
        body = '%s, and %s' % (', '.join(marks[:-1]), marks[-1])
    return '%ss %s' % (unit, body)


def book(code):
    """The code the following units belong to."""
    return Place('code', getattr(code, 'value', code), None, title=getattr(code, 'title', None))


class Citation:
    """A code, closed over by each unit call.

    ``Citation(Code.CIVIL).section(4600).subdivision('b')`` prints the
    California citation. ``text`` is the stored plain text of that
    subdivision. ``refs`` is that section as a node. ``follow`` opens the
    next statute. ``md`` is the Markdown page and ``chart`` is the flowchart.
    The sentence is not kept on the object.
    """

    def __init__(self, code):
        from apa import Code
        if not isinstance(code, Code):
            raise TypeError('code must be a Code')
        self.code = code
        self.place = book(code)
        self.span_end = None
        self.span_more = ()
        self.et_seq = False
        self.hops_depth = 1
        self.only_codes = None
        self.same_book = False
        self.siblings = ()
        self.session_year = None
        self._refs = None
        self._text = None
        self._sentences = None

    @classmethod
    def _from(cls, code, place):
        cited = cls.__new__(cls)
        cited.code = code
        cited.place = place
        cited.span_end = None
        cited.span_more = ()
        cited.et_seq = False
        cited.hops_depth = 1
        cited.only_codes = None
        cited.same_book = False
        cited.siblings = ()
        cited.session_year = None
        cited._refs = None
        cited._text = None
        cited._sentences = None
        return cited

    def _copy(self):
        cited = Citation._from(self.code, self.place)
        cited.span_end = self.span_end
        cited.span_more = self.span_more
        cited.et_seq = self.et_seq
        cited.hops_depth = self.hops_depth
        cited.only_codes = self.only_codes
        cited.same_book = self.same_book
        cited.siblings = self.siblings
        cited.session_year = self.session_year
        return cited

    def through(self, end=None, *, page=None, line=None):
        """A section range takes ``end``. A bill span takes ``page`` and ``line``."""
        if page is not None or line is not None:
            cited = self._copy()
            cited.place = self.place.through(page=page, line=line)
            return cited
        cited = Citation._from(self.code, self.place)
        cited.span_end = str(end)
        cited.session_year = self.session_year
        return cited

    def and_(self, *numbers):
        """A series: this section and each further number."""
        cited = Citation._from(self.code, self.place)
        cited.span_more = tuple(str(number) for number in numbers)
        cited.session_year = self.session_year
        return cited

    def commencing(self):
        """An open end. Prints as commencing with Section, not et seq."""
        cited = Citation._from(self.code, self.place)
        cited.et_seq = True
        cited.session_year = self.session_year
        return cited

    def session(self, year):
        """Close this citation over one publication year.

        Later unit calls and ``text`` keep that year. A year that is not
        indexed is a miss. The current code is a separate citation, not a
        substitute for this one.
        """
        cited = self._copy()
        cited.session_year = None if year in (None, '') else str(year)
        cited._refs = None
        return cited

    def hops(self, depth):
        """How many citation hops to follow. None follows until a section repeats."""
        cited = self._copy()
        cited.hops_depth = depth
        return cited

    def only(self, *codes):
        """Follow citations only into these books."""
        cited = self._copy()
        cited.only_codes = codes
        return cited

    def same(self):
        """Follow citations only inside this code."""
        cited = self._copy()
        cited.same_book = True
        return cited

    @property
    def refs(self):
        """This section as a reference node. ``follow`` opens statutes it names."""
        from structure import Refs
        number = self.place._section()
        if self.same_book:
            allowed = {self.code}
        elif self.only_codes:
            allowed = set(self.only_codes)
        else:
            allowed = None
        if self._refs is None:
            self._refs = Refs(
                self.code, number or '', depth=self.hops_depth, allowed=allowed,
                session=self.session_year,
            )
        return self._refs

    @property
    def chart(self):
        return self.refs.chart

    @property
    def md(self):
        return self.refs.md

    def _walk(self):
        return self.refs.tree

    def diagram(self):
        """The Mermaid flowchart of this section and the statutes it cites."""
        return self.chart

    def page(self):
        """That flowchart as a Markdown page. Chat draws the mermaid fence."""
        return self.md

    def tree(self):
        """The same walk as nested nodes. The visited set is built inside the walk."""
        return self._walk()

    def __call__(self, *labels):
        """Stack one label, or name sibling labels in one call.

        ``section('4600')('a')(1)`` is subdivision (a), paragraph (1).
        ``section('4600')('a', 'b')`` is subdivisions (a) and (b).
        """
        if not labels:
            raise TypeError('a label is required')
        if len(labels) == 1:
            from structure import _mark_unit
            label = str(labels[0]).strip('()')
            cited = self._copy()
            cited.place = getattr(self.place, _mark_unit(label))(label)
            return cited
        cited = self._copy()
        cited.siblings = tuple(str(label).strip('()') for label in labels)
        cited.session_year = self.session_year
        return cited

    def __getattr__(self, name):
        if name not in _UNITS:
            raise AttributeError(name)

        def bound(number=None, commencing=None):
            cited = Citation._from(self.code, getattr(self.place, name)(number, commencing))
            cited.session_year = self.session_year
            cited.hops_depth = self.hops_depth
            cited.only_codes = self.only_codes
            cited.same_book = self.same_book
            return cited

        return bound

    def __str__(self):
        return self.reference()

    def reference(self):
        """The California form: Civil Code section 4600, subdivision (b)."""
        if any(place.unit == 'page' for place in self.place._chain()):
            return self.place.reference()
        number = self.place._section()
        if not number:
            return self.place.reference()
        from apa import cite, section, series, span
        from government import Article, ArticleMark
        chain = self.place._chain()
        article_place = next(
            (place for place in chain if place.unit == 'article' and place.number is not None),
            None,
        )
        from needles import outline
        article = None
        if article_place is not None and outline(self.code).identifies('article'):
            label = ' '.join(str(article_place.number).upper().split())
            try:
                article = Article(label)
            except ValueError:
                article = ArticleMark(label)
        if self.span_end:
            return cite(self.code, span(number, self.span_end), article=article).reference()
        if self.span_more:
            return cite(self.code, series(number, *self.span_more), article=article).reference()
        marks = [
            place for place in chain
            if place.unit in _MARKS and place.number is not None
        ]
        first = marks[0].number if marks else None
        if self.et_seq:
            body = section(number, first)
            body.open = True
            return cite(self.code, body, article=article).reference()
        text = cite(self.code, section(number, first), article=article).reference()
        for mark in marks[1:]:
            text += ', %s (%s)' % (mark.unit, str(mark.number).strip('()'))
        if self.siblings:
            text += ', %s' % _sibling_phrase(self.siblings)
        return text

    @property
    def text(self):
        """The stored plain text. A missing section or label is empty."""
        if self._text is not None:
            return self._text
        doc = self.place.read(session=self.session_year)
        body = doc.get('text') or ''
        if not doc.get('found'):
            self._text = ''
            return self._text
        marks = [
            place for place in self.place._chain()
            if place.unit in _MARKS and place.number is not None
        ]
        if not marks:
            self._text = body
            return self._text
        from structure import split_nodes
        node = split_nodes(body)
        for mark in marks:
            label = '(%s)' % str(mark.number).strip('()')
            node = next((child for child in node.children if child.label == label), None)
            if node is None:
                self._text = ''
                return self._text
        self._text = node.text
        return self._text

    @property
    def subdivisions(self):
        """The labels in ``text``, in walk order. A section with no labels is empty."""
        from structure import split_nodes
        body = self.text
        if not body:
            return []
        return [node.label for node in split_nodes(body).walk() if node.label]

    @property
    def sentences(self):
        """Each sentence of ``text``, with its rule, conditions, exceptions, and limits."""
        from analysis import parse_sentence, split_sentences
        if getattr(self, '_sentences', None) is None:
            self._sentences = [parse_sentence(sentence) for sentence in split_sentences(self.text)]
        return self._sentences

    def words(self):
        """The tokens in ``text``, split on whitespace. The list can be sliced.

        ``words`` on a needle class is the word classes, not these tokens.
        """
        return self.text.split()

    def containing(self, phrase):
        """The stored sentence that contains ``phrase``. A miss is empty."""
        text = self.text
        if not text or not phrase:
            return ''
        from analysis import split_sentences
        needle = str(phrase).casefold()
        for sentence in split_sentences(text):
            if needle in sentence.casefold():
                return sentence
        return ''


class Use(enum.Enum):
    """What the React client asked the closure to return. The value is the string."""

    READ = 'read'
    FIND = 'find'
    REFS = 'refs'
    GAPS = 'gaps'


_HEADINGS = ('division', 'title', 'part', 'chapter', 'article', 'section', 'subdivision')


def _flag(value):
    return str(value or '').strip().lower() in ('1', 'true', 'yes')


def _walk_edges(tree):
    """Every hop of the walk as ``source``, ``target``, and ``label``.

    One node names the next. A repeated pair is dropped, so the list stays the
    DAG the client draws. The mermaid string remains the static export.
    """
    edges = []
    seen = set()

    def walk(node):
        here = node.get('id') or ''
        for child in node.get('children') or []:
            target = child.get('id') or ''
            key = (here, target)
            if not target or key in seen:
                continue
            seen.add(key)
            edges.append({
                'source': here,
                'target': target,
                'label': 'cites',
                'found': bool(child.get('found')),
            })
            walk(child)

    walk(tree)
    return edges


def _walk_nodes(tree):
    """One row per section the walk opened, with the hop it was reached on."""
    rows = []
    seen = set()

    def walk(node, depth):
        key = node.get('id') or ''
        if not key or key in seen:
            return
        seen.add(key)
        rows.append({
            'id': key,
            'label': node.get('label') or key,
            'citation': node.get('citation') or node.get('label') or key,
            'found': bool(node.get('found')),
            'hop': depth,
        })
        for child in node.get('children') or []:
            walk(child, depth + 1)

    walk(tree, 0)
    return rows


def ask(query):
    """Open a citation from the filters a client sends.

    ``code`` is the book. A heading filter remembers the unit above it, the
    same way ``division(1).part('2.52')`` does. ``session`` is the publication
    year. ``hops`` is how far the citation walk goes, and ``all`` follows until
    a section repeats. ``only`` is the books the walk may enter. ``same`` stays
    in the open book. ``q`` searches inside the place. ``use`` picks read, find,
    refs, or gaps. A missing use follows the filters that were sent.
    """
    from apa import Code
    sent = {key: (value or '').strip() for key, value in (query or {}).items()}
    token = sent.get('code') or ''
    try:
        code = Code.get(token)
    except KeyError:
        return {'found': False, 'reason': 'unknown_code', 'expression': token}
    use = (sent.get('use') or '').lower()
    if not use:
        if sent.get('q'):
            use = Use.FIND.value
        elif sent.get('hops') or sent.get('only'):
            use = Use.REFS.value
        else:
            use = Use.READ.value
    try:
        chosen = Use(use)
    except ValueError:
        return {'found': False, 'reason': 'unknown_use', 'expression': use}
    cited = Citation(code)
    for unit in _HEADINGS:
        number = sent.get(unit)
        if number:
            cited = getattr(cited, unit)(number)
    if sent.get('through'):
        cited = cited.through(sent['through'])
    if sent.get('session'):
        cited = cited.session(sent['session'])
    if sent.get('hops'):
        raw = sent['hops']
        if raw.lower() == 'all':
            cited = cited.hops(None)
        else:
            try:
                cited = cited.hops(int(raw))
            except ValueError:
                return {'found': False, 'reason': 'hops', 'expression': raw}
    if sent.get('only'):
        books = []
        for item in sent['only'].split(','):
            item = item.strip()
            if not item:
                continue
            try:
                books.append(Code.get(item))
            except KeyError:
                return {'found': False, 'reason': 'unknown_code', 'expression': item}
        if books:
            cited = cited.only(*books)
    if _flag(sent.get('same')):
        cited = cited.same()
    filters = {
        'code': code.value,
        'use': chosen.value,
        'reference': cited.reference(),
    }
    for unit in _HEADINGS:
        if sent.get(unit):
            filters[unit] = sent[unit]
    for name in ('session', 'hops', 'only', 'through', 'q'):
        if sent.get(name):
            filters[name] = sent[name]
    if _flag(sent.get('same')):
        filters['same'] = True
    body = {'found': True, 'use': chosen.value, 'filters': filters}
    if chosen is Use.FIND:
        phrase = sent.get('q') or ''
        if not phrase:
            return {'found': False, 'reason': 'not_in_index', 'expression': ''}
        try:
            limit = max(1, min(int(sent.get('limit') or '10'), 50))
        except ValueError:
            limit = 10
        body['hits'] = cited.place.find(phrase, limit=limit)
        return body
    if chosen is Use.GAPS:
        from structure import review
        number = cited.place._section()
        if not number:
            return {'found': False, 'reason': 'not_in_index', 'expression': filters['reference']}
        looked = review(
            cited.code, number, depth=cited.hops_depth,
            same=cited.same_book,
            codes=None if cited.only_codes is None else tuple(cited.only_codes),
            session=cited.session_year,
        )
        if not looked.get('found'):
            return looked
        body['citation'] = looked.get('citation') or ''
        body['gaps'] = [
            {
                'gap': getattr(gap.get('gap'), 'value', gap.get('gap')),
                'phrase': gap.get('phrase') or '',
                'code': getattr(gap.get('code'), 'value', gap.get('code')) or '',
                'section': gap.get('section') or '',
                'citation': gap.get('citation') or '',
            }
            for gap in looked.get('gaps') or []
        ]
        return body
    if chosen is Use.REFS:
        number = cited.place._section()
        if not number:
            return {'found': False, 'reason': 'not_in_index', 'expression': filters['reference']}
        tree = cited.refs.tree
        if not tree.get('found'):
            return tree
        body['citation'] = tree.get('citation') or ''
        body['chart'] = tree.get('mermaid') or ''
        body['links'] = [
            {
                'kind': link.get('kind'),
                'text': link.get('text'),
                'code': getattr(link.get('code'), 'value', link.get('code')),
                'section': link.get('section'),
                'label': link.get('label'),
                'year': link.get('year'),
                'chapter': link.get('chapter'),
                'action': link.get('action') or '',
            }
            for link in tree.get('links') or []
        ]
        body['nodes'] = _walk_nodes(tree)
        body['edges'] = _walk_edges(tree)
        return body
    number = cited.place._section()
    if not number:
        return body
    opened = cited.place.read(session=cited.session_year)
    body['found'] = bool(opened.get('found'))
    if not opened.get('found'):
        body['reason'] = opened.get('reason')
        if 'indexed_in' in opened:
            body['indexed_in'] = opened['indexed_in']
    body['section'] = opened
    return body


def _bind(unit):
    def call(number=None, commencing=None):
        return Place(unit, number, _here.get(), commencing)

    call.__name__ = unit
    return call


for _unit in _UNITS:
    globals()[_unit] = _bind(_unit)
