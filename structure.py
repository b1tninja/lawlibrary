"""Subdivisions and the references a California section makes.

A section's plain text is a tree. ``(a)`` and ``(b)`` are siblings. ``(1)``
and ``(2)`` sit under the letter that is open. A reference such as
``Section 7280 of the Revenue and Taxation Code`` names another book.
``subdivision (b)`` names a label in the same section. ``related`` follows
those other books to a depth the caller sets.
"""

import enum
import re

from apa import Code, cite, section as one_section
from needles import cuts, pattern
from outline import Margin, Roman
import query as law_query


class Rank(enum.Enum):
    """How deep a marker sits. A larger value is nested further in."""

    HEADING = 1
    LETTER = 2
    NUMBER = 3
    CAPITAL = 4
    CLAUSE = 5


class Node:
    """One subdivision. ``label`` is empty on the preamble."""

    def __init__(self, label, rank, text):
        self.label = label
        self.rank = rank
        self.text = text
        self.children = []

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


class Link:
    """A pointer from this text to a book, a section, or a label."""

    def __init__(self, kind, text, code=None, section=None, label=None, labels=(), end=None, more=(), session=None, action=None):
        self.kind = kind
        self.text = text
        self.code = code
        self.section = section
        self.label = label
        self.labels = tuple(labels)
        self.end = None if end is None else str(end)
        self.more = tuple(str(number) for number in more)
        self.session = session
        self.action = action

    def citation(self):
        """The same pointer as a ``Citation`` chain. A session law is a ``Session``."""
        if self.session is not None:
            return self.session
        code = _book(self.code)
        if code is None:
            return None
        from places import Citation
        cited = Citation(code)
        from needles import outline
        if self.kind == 'article' and self.label and outline(code).identifies('article'):
            cited = cited.article(self.label)
        if self.kind == 'range' and self.section:
            return cited.section(self.section).commencing()
        if self.section:
            cited = cited.section(self.section)
        if self.end:
            return cited.through(self.end)
        if self.more:
            return cited.and_(*self.more)
        labels = list(self.labels)
        if self.label and self.kind != 'article' and self.label not in labels:
            labels.append(self.label)
        for label in labels:
            cited = getattr(cited, _mark_unit(label))(label)
        return cited

    def resolve(self, number):
        """The outline unit ``this chapter`` names, read from the open section."""
        if self.kind != 'internal':
            return None
        code = _book(self.code)
        if code is None or not number:
            return None
        from places import Citation
        unit = self.text.strip().split()[-1].lower()
        if unit == 'section':
            return Citation(code).section(str(number))
        import query
        from hierarchy import crumbs
        doc = query.section(code, number)
        for crumb in crumbs(doc):
            found = re.search(
                r'(?i)\b%s\s+([0-9]+(?:\.[0-9]+)*)' % re.escape(unit),
                crumb.heading or '',
            )
            if found:
                try:
                    return getattr(Citation(code), unit)(found.group(1))
                except AttributeError:
                    return None
        return None


_ONE = re.compile(
    r'\((?:[a-z]{1,2}|[A-Z]|_[a-z]_|[ivx]+|\d+)\)'
    r'|(?:IX|VIII|VII|VI|IV|III|II|V|I)\.'
)
_OF_THE = re.compile(
    r'(?i)Sections?\s+(?P<body>\d+(?:\.\d+)*(?:\([A-Za-z0-9]+\))*(?:\s*(?:;\s*(?:and/or|and|or)|;|,\s*(?:and/or|and|or)|,|and/or|and|or|to|through)\s*\d+(?:\.\d+)*)*)'
    r'\s*(?:of\s+the\s+|,\s+)'
)
_TITLES = tuple(sorted(Code, key=lambda code: len(code.title), reverse=True))
_UNKNOWN_TITLE = re.compile(r'[A-Za-z][A-Za-z ]*?Code')
_STACK = re.compile(
    r'(?i)\b(?:subdivision|subsection|paragraph|subparagraph|clause)s?\s+'
    r'(?P<marks>\([A-Za-z0-9]+\)(?:\([A-Za-z0-9]+\))+)'
    r'(?:\s+of\s+Sections?\s+(?P<section>\d+(?:\.\d+)*))?'
)
_NEST = re.compile(
    r'(?i)\bparagraph\s+\((?P<inner>[A-Za-z0-9]+)\)\s+of\s+'
    r'subdivision\s+\((?P<outer>[A-Za-z0-9]+)\)'
    r'(?:\s+of\s+Sections?\s+(?P<section>\d+(?:\.\d+)*))?'
)
_LABELS = re.compile(
    r'(?i)\b(?:%s)\s+'
    r'\([A-Za-z0-9]+\)(?:\s*(?:;\s*(?:and/or|and|or)|;|,\s*(?:and|or)?|and|or)\s*\([A-Za-z0-9]+\))*'
    r'(?:\s+of\s+Sections?\s+(?P<section>\d+(?:\.\d+)*))?'
    % '|'.join('%ss?' % word for word in cuts())
)
_COMMENCING = re.compile(r'(?i)\bcommencing with Section\s+(?P<num>\d+(?:\.\d+)*)')
_SESSION = re.compile(
    r'(?i)(?:Section\s+(?P<act>\d+(?:\.\d+)*)\s+of\s+)?'
    r'Chapter\s+(?P<chapter>\d+)\s+of\s+the\s+Statutes\s+of\s+(?P<year>\d{4})'
)
_CREDIT = re.compile(
    r'(?i)(?:(?P<action>repealed and added|repealed conditionally|enacted|repealed|added|amended)\s+by\s+)?'
    r'\bStats?\.?\s+(?P<year>\d{4}),\s+Ch\.?\s+(?P<chapter>\d+)'
    r'(?:,\s+Sec\.?\s+(?P<act>\d+(?:\.\d+)*))?'
)
_ARTICLE = re.compile(
    r'(?i)Sections?\s+(?P<body>\d+(?:\.\d+)*(?:\s*(?:;|,|and|or|to)\s*\d+(?:\.\d+)*)*)'
    r'\s+of\s+Article\s+(?P<roman>[IVXLCDM]+)'
    r'(?:\s*(?P<suffix>[A-D])(?![A-Za-z]))?'
)
_BARE = re.compile(
    r'(?i)\bSections?\s+(?P<body>\d+(?:\.\d+)*(?:\s*(?:;\s*(?:and/or|and|or)|;|,\s*(?:and/or|and|or)|,|and/or|and|or)\s*\d+(?:\.\d+)*)*)'
    r'(?!\s+of\s+the\b)'
)
_THIS = pattern(internal=True, prefix=r'\bthis ', suffix=r'\b')


def _mark_unit(label):
    """The closure unit for a parenthetical. A number is a paragraph."""
    rank = _rank('(%s)' % str(label).strip('()'))
    if rank is Rank.NUMBER:
        return 'paragraph'
    if rank is Rank.CLAUSE:
        return 'clause'
    if rank is Rank.CAPITAL:
        return 'subparagraph'
    return 'subdivision'


def _section_marks(body):
    """Section numbers, keeping a parenthetical that was written on the number."""
    found = []
    for match in re.finditer(
        r'(?P<num>\d+(?:\.\d+)*)(?P<marks>(?:\([A-Za-z0-9]+\))*)',
        body or '',
    ):
        labels = re.findall(r'\(([^)]+)\)', match.group('marks') or '')
        found.append((match.group('num'), labels))
    return found


def _rank(label):
    inner = label.strip('().')
    if label.endswith('.') and Roman.read(inner) is not None:
        return Rank.HEADING
    if inner.isdigit():
        return Rank.NUMBER
    if len(inner) > 1 and inner.islower() and Roman.read(inner) is not None:
        return Rank.CLAUSE
    if inner.isupper():
        return Rank.CAPITAL
    return Rank.LETTER


def _marks(text):
    """Labels that open a subdivision, including a run on one line.

    A label at the start of a line opens a node. So does the next label
    when nothing but whitespace sits between them, as in ``(e)(1)(A)``.
    A colon introduces a list, and a later ``(2)`` or ``or (3)`` continues
    it when prose sits between the items. A citation such as
    ``clause (i), (ii), or (iii)`` is not a list of nodes.
    """
    covered = [(match.start(), match.end()) for match in _LABELS.finditer(text)]
    raw = [
        match for match in _ONE.finditer(text)
        if not any(begin <= match.start() < end for begin, end in covered)
    ]
    chosen = []
    for match in raw:
        start = match.start()
        line = text.rfind('\n', 0, start) + 1
        at_line = text[line:start].strip() == ''
        stacked = bool(chosen) and text[chosen[-1].end():start].strip() == ''
        after_colon = text[:start].rstrip().endswith(':')
        continued = False
        if chosen:
            gap = text[chosen[-1].end():start]
            continued = bool(re.search(r'[A-Za-z]', gap)) and bool(
                re.search(r'(?i)(?:,|\bor\b|\band\b)\s*$', gap)
            )
        if at_line or stacked or after_colon or continued:
            chosen.append(match)
    return chosen


def split_nodes(text):
    """The preamble and each labeled subdivision."""
    root = Node('', None, '')
    root.margin = Margin(-1, -1)
    matches = _marks(text or '')
    if not matches:
        root.text = (text or '').strip()
        return root
    root.text = text[:matches[0].start()].strip()
    stack = [root]
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        label = match.group(0)
        rank = _rank(label)
        line = text.rfind('\n', 0, match.start()) + 1
        margin = Margin.read(text[line:match.start()])
        body = text[match.end():end].strip()
        node = Node(label, rank, body)
        node.margin = margin
        while len(stack) > 1 and stack[-1].margin > margin:
            stack.pop()
        if not margin > stack[-1].margin:
            while len(stack) > 1 and stack[-1].rank is not None and stack[-1].rank.value >= rank.value:
                stack.pop()
        stack[-1].children.append(node)
        stack.append(node)
    return root


def _book(value):
    """The ``Code`` member for a token or a member already in hand."""
    if isinstance(value, Code):
        return value
    if not value:
        return None
    try:
        return Code.get(value)
    except KeyError:
        return None


def _named_statutes(text):
    """``Section N of the {title}``. The longest printed title wins.

    ``Code of Civil Procedure`` stays that book. A shorter match would stop
    at the first word ``Code``. A title that is not one of the 29 codes is
    still consumed, so it is not read as a section of the open book.
    """
    found = []
    for match in _OF_THE.finditer(text or ''):
        rest = text[match.end():]
        folded = rest.lower()
        code = None
        length = 0
        for candidate in _TITLES:
            if folded.startswith(candidate.title.lower()):
                code = candidate
                length = len(candidate.title)
                break
        if length == 0:
            if not re.search(r'(?i)of\s+the\s+$', match.group(0)):
                continue
            unknown = _UNKNOWN_TITLE.match(rest)
            if unknown is None:
                continue
            length = unknown.end()
        end = match.end() + length
        found.append((match.start(), end, match.group('body'), code, text[match.start():end]))
    return found


def find_links(text, here=None):
    """References in one string. ``here`` is the open book, a ``Code`` member."""
    book = _book(here)
    found = []
    named = _named_statutes(text or '')
    for _start, _end, body, code, phrase in named:
        marks = list(_section_marks(body))
        if len(marks) >= 2 and re.search(r'(?i)\b(?:to|through)\b', body):
            found.append(Link('statute', phrase, code, marks[0][0], end=marks[-1][0]))
        elif len(marks) >= 2:
            found.append(Link(
                'statute', phrase, code, marks[0][0],
                more=tuple(number for number, _labels in marks[1:]),
            ))
        else:
            for number, labels in marks:
                found.append(Link(
                    'statute', phrase, code, number,
                    label=labels[0] if labels else None,
                    labels=labels,
                ))
    taken = [(start, end) for start, end, _body, _code, _phrase in named]
    for match in _ARTICLE.finditer(text or ''):
        token = match.group('roman')
        suffix = match.group('suffix')
        roman = Roman.read(token)
        if roman is None and suffix is None and len(token) > 1 and token[-1] in 'ABCD':
            roman = Roman.read(token[:-1])
            suffix = token[-1]
        if roman is None:
            continue
        label = roman.text.upper()
        if suffix:
            label = '%s %s' % (label, suffix.upper())
        for number in re.findall(r'\d+(?:\.\d+)*', match.group('body')):
            found.append(Link('article', match.group(0), Code.CONSTITUTION, number, label))
        taken.append((match.start(), match.end()))
    for match in _BARE.finditer(text or ''):
        if any(match.start() >= begin and match.end() <= end for begin, end in taken):
            continue
        if any(
            match.start() >= begin and match.end() <= end
            for begin, end in ((item.start(), item.end()) for item in _COMMENCING.finditer(text or ''))
        ):
            continue
        if book:
            for number in re.findall(r'\d+(?:\.\d+)*', match.group('body')):
                found.append(Link('statute', match.group(0), book, number))
    for match in _COMMENCING.finditer(text or ''):
        found.append(Link('range', match.group(0), book, match.group('num')))
    for match in _NEST.finditer(text or ''):
        if any(match.start() >= begin and match.end() <= end for begin, end in taken):
            continue
        found.append(Link(
            'subdivision', match.group(0), book,
            section=match.group('section'),
            label=match.group('outer'),
            labels=(match.group('outer'), match.group('inner')),
        ))
        taken.append((match.start(), match.end()))
    for match in _STACK.finditer(text or ''):
        if any(match.start() >= begin and match.end() <= end for begin, end in taken):
            continue
        labels = re.findall(r'\(([A-Za-z0-9]+)\)', match.group('marks'))
        found.append(Link(
            'subdivision', match.group(0), book,
            section=match.group('section'),
            label=labels[0] if labels else None,
            labels=tuple(labels),
        ))
        taken.append((match.start(), match.end()))
    for match in _LABELS.finditer(text or ''):
        if any(match.start() < end and match.end() > begin for begin, end in taken):
            continue
        labels = re.findall(r'\(([A-Za-z0-9]+)\)', match.group(0))
        named = match.group('section')
        for label in labels:
            found.append(Link('subdivision', match.group(0), book, section=named, label=label))
    for match in _THIS.finditer(text or ''):
        found.append(Link('internal', match.group(0), book))
    for match in _SESSION.finditer(text or ''):
        from needles import Session
        law = Session.year(match.group('year')).chapter(match.group('chapter'))
        if match.group('act'):
            law = law.section(match.group('act'))
        found.append(Link('session', match.group(0), session=law))
        taken.append((match.start(), match.end()))
    for match in _CREDIT.finditer(text or ''):
        if any(match.start() < end and match.end() > begin for begin, end in taken):
            continue
        from needles import Action, Session
        law = Session.year(match.group('year')).chapter(match.group('chapter'))
        if match.group('act'):
            law = law.section(match.group('act'))
        named = (match.group('action') or '').casefold()
        action = Action(named) if named else None
        found.append(Link('session', match.group(0), session=law, action=action))
    return found


def _mermaid_id(token):
    return re.sub(r'[^A-Za-z0-9]', '', token) or 'n'


def markdown(title, chart):
    """A Markdown page. The diagram is a fenced mermaid flowchart, which Cursor chat and the Markdown preview both draw."""
    body = (chart or '').strip() or 'flowchart TD'
    heading = (title or '').strip() or 'Diagram'
    return '# %s\n\n```mermaid\n%s\n```\n' % (heading, body)


def _chart(edges, label, nodes=()):
    """A flowchart. A pair uses ``label``. A triple carries its own label. ``nodes`` are offices with no edge."""
    lines = ['flowchart TD']
    seen = set()

    def node(name):
        ident = _mermaid_id(name)
        if ident not in seen:
            lines.append('  %s["%s"]' % (ident, (name or '').replace('"', "'")))
            seen.add(ident)
        return ident

    for name in nodes:
        if name:
            node(name)
    drawn = set()
    for row in edges:
        if len(row) >= 3:
            source, target, edge_label = row[0], row[1], row[2]
        else:
            source, target, edge_label = row[0], row[1], label
        key = (source, target, edge_label)
        if not source or not target or key in drawn:
            continue
        drawn.add(key)
        lines.append('  %s -->|%s| %s' % (node(source), edge_label, node(target)))
    return '\n'.join(lines)


def code_chart(pairs):
    """Books connected by citation. ``pairs`` are ``(source book, cited section)``. The cited book is the first word."""
    edges = []
    for source, cited in pairs:
        book = (cited or '').split(' ', 1)[0]
        if source and book:
            edges.append((source, book))
    return _chart(edges, 'cites')


def enactment_chart(pairs):
    """A section and the Statutes chapter that enacted it. ``pairs`` are ``(citation, year chapter)``."""
    return _chart(pairs, 'enacted')


class Diagram:
    """A stored graph. The kind is closed over, then a book, then the page.

    ``Diagram.codes().page()`` is the book-to-book citation graph.
    ``Diagram.vesting().code(Code.GOVERNMENT).page()`` is that book's grants.
    ``Diagram.enactments().code(Code.WATER).chart()`` is the flowchart alone.
    ``Diagram.around('CIV 1714.1').page()`` is that section and the sections that name it.
    """

    _TITLES = {
        'codes': 'Code citations',
        'vesting': 'Vesting',
        'enactments': 'Enactments',
        'references': 'References',
    }

    def __init__(self, kind, code=None, citation=None):
        self.kind = kind
        self.book = code
        self.citation = citation

    @classmethod
    def codes(cls):
        return cls('codes')

    @classmethod
    def vesting(cls):
        return cls('vesting')

    @classmethod
    def enactments(cls):
        return cls('enactments')

    @classmethod
    def around(cls, citation):
        return cls('references', citation=citation)

    def code(self, code):
        return Diagram(self.kind, code, self.citation)

    def chart(self):
        from indexer import Indexer
        index = Indexer()
        if self.kind == 'vesting':
            return index.vesting_diagram(code=self.book)
        if self.kind == 'enactments':
            return index.enactment_diagram(code=self.book)
        if self.kind == 'references':
            return index.reference_diagram(self.citation)
        return index.code_diagram()

    def page(self):
        return markdown(self._TITLES.get(self.kind, 'Diagram'), self.chart())

    def __call__(self):
        return self.page()


def mermaid(tree):
    """A flowchart of the section and the statutes it names."""
    lines = ['flowchart TD']
    seen = set()

    def emit(node, parent=None):
        ident = _mermaid_id(node['id'])
        if ident not in seen:
            label = node['label'].replace('"', "'")
            lines.append('  %s["%s"]' % (ident, label))
            seen.add(ident)
        if parent is not None:
            lines.append('  %s --> %s' % (_mermaid_id(parent), ident))
        for child in node.get('children') or []:
            emit(child, node['id'])

    emit(tree)
    return '\n'.join(lines)


def _scope(codes, same, book):
    """Books the walk may enter. ``None`` means every book."""
    if same:
        return {book} if book else set()
    if not codes:
        return None
    allowed = set()
    for item in codes:
        found = _book(item)
        if found is not None:
            allowed.add(found)
    return allowed


class Refs:
    """One section and the statutes it names. ``follow`` opens the next hop.

    ``Citation(code).section(number).refs`` is this node.
    ``follow`` returns the sections those statute links name. A section
    already in ``seen`` is not opened again, so the walk stays a DAG.
    A session chapter is a link and is not opened. ``md`` is the Markdown
    page. ``chart`` is the flowchart alone.
    """

    def __init__(self, code, section, depth=0, seen=None, allowed=None, session=None):
        book = _book(code) or code
        self.code = book
        self.section = '' if section is None else str(section)
        self.depth = depth
        self.seen = seen if seen is not None else set()
        self.allowed = allowed
        self.session = session
        token = getattr(book, 'value', book) or ''
        self.key = ('%s %s' % (token, self.section)).strip()
        if self.key:
            self.seen.add(self.key)
        self._tree = None
        self._links = None

    @property
    def tree(self):
        """The walk for this node. ``md`` and ``chart`` share it."""
        if self._tree is None:
            if not self.section:
                self._tree = {'found': False, 'reason': 'not_in_index', 'mermaid': '', 'links': []}
            else:
                self._tree = related(
                    self.code, self.section, depth=self.depth,
                    codes=None if self.allowed is None else tuple(self.allowed),
                    session=self.session,
                )
        return self._tree

    def links(self):
        """The pointers in this section. The list can be sliced. A missing section is empty."""
        if self._links is None:
            text = self.tree.get('text') or ''
            self._links = find_links(text, here=self.code) if text else []
        return self._links

    def follow(self):
        """The statute sections this node names and has not opened yet."""
        opened = []
        for link in self.links():
            if link.kind != 'statute' or not link.code or not link.section:
                continue
            if self.allowed is not None and link.code not in self.allowed:
                continue
            key = '%s %s' % (link.code.value, link.section)
            if key in self.seen:
                continue
            opened.append(Refs(
                link.code, link.section, depth=0, seen=self.seen,
                allowed=self.allowed, session=self.session,
            ))
        return opened

    @property
    def sessions(self):
        """Statutes chapters named here. Each value is the year, then the chapter. They are not opened."""
        rows = []
        for link in self.tree.get('links') or []:
            if link.get('kind') == 'session' and link.get('year') and link.get('chapter'):
                rows.append('%s %s' % (link['year'], link['chapter']))
        return list(dict.fromkeys(rows))

    @property
    def articles(self):
        """Constitution articles named here. Each value is the article, then the section. They are not opened."""
        rows = []
        for link in self.tree.get('links') or []:
            if link.get('kind') == 'article' and link.get('section'):
                rows.append('%s %s' % (link.get('label') or '', link['section']).strip())
        return list(dict.fromkeys(rows))

    @property
    def chart(self):
        """The flowchart of this section and ``depth`` hops."""
        return self.tree.get('mermaid') or ''

    @property
    def md(self):
        """That flowchart as a Markdown page."""
        token = getattr(self.code, 'value', self.code) or ''
        title = ('%s %s' % (token, self.section)).strip() or 'Diagram'
        return markdown(title, self.chart)

    def page(self):
        return self.md

    def __iter__(self):
        return iter(self.links())


def _follows(depth):
    """A positive depth has hops left. None or a negative depth stops only on a repeat."""
    if depth is None or depth < 0:
        return True
    return depth > 0


def _node_dict(code, number, text, depth, seen, allowed=None, session=None):
    book = _book(code)
    token = book.value if book else code
    key = '%s %s' % (token, number)
    seen.add(key)
    links = find_links(text, here=book)
    children = []
    if _follows(depth):
        for link in links:
            if link.kind != 'statute' or not link.code or not link.section:
                continue
            if allowed is not None and link.code not in allowed:
                continue
            nxt = '%s %s' % (link.code.value, link.section)
            if nxt in seen:
                continue
            seen.add(nxt)
            doc = law_query.section(link.code, link.section, session=session)
            if not doc.get('found'):
                children.append({
                    'id': nxt,
                    'label': nxt,
                    'found': False,
                    'text': '',
                    'children': [],
                })
                continue
            nxt_depth = depth if depth is None or depth < 0 else depth - 1
            children.append(_node_dict(
                link.code, link.section, doc.get('text') or '', nxt_depth, seen, allowed, session,
            ))
    parts = split_nodes(text)
    return {
        'id': key,
        'label': key,
        'found': True,
        'text': text,
        'subdivisions': [
            {'label': node.label, 'text': node.text}
            for node in parts.walk() if node.label
        ],
        'links': [
            {
                'kind': link.kind, 'text': link.text, 'code': link.code,
                'section': link.section, 'label': link.label,
                'year': None if link.session is None else link.session.year,
                'chapter': None if link.session is None else link.session.chapter,
                'action': '' if link.action is None else link.action.value,
            }
            for link in links
        ],
        'children': children,
    }


class Gap(enum.Enum):
    """A citation shape in the text that the recorded links do not cover."""

    SHORT_TITLE = 'short_title'
    UNRESOLVED = 'unresolved'
    UNLINKED = 'unlinked'


_WIDE = re.compile(
    r'(?i)Sections?\s+\d+(?:\.\d+)*(?:\([A-Za-z0-9]+\))*'
    r'(?:\s*(?:,|and|to)\s*\d+(?:\.\d+)*)*'
    r'\s*(?:of\s+the\s+|,\s+)'
    r'[A-Za-z][A-Za-z ]*?Code(?:\s+of\s+(?:the\s+)?[A-Za-z][A-Za-z ]+)?'
)
def inspect(text, here=None):
    """Phrases a reader would call a citation that ``find_links`` did not keep.

    A short title is a link that stops at the first word ``Code`` while the
    sentence still names the book, as in ``Code of Civil Procedure``.
    An unresolved title names a book that is not one of the codes.
    An unlinked phrase, such as a chapter of the Statutes of a year, was
    not recorded at all.
    """
    named = _named_statutes(text or '')
    gaps = []
    for sight in _WIDE.finditer(text or ''):
        covered = [row for row in named if row[0] == sight.start()]
        phrase = sight.group(0)
        if ',' in phrase and not re.search(r'(?i)of\s+the\s+', phrase):
            rest = phrase.split(',', 1)[1].strip()
            if not any(rest.lower().startswith(code.title.lower()) for code in _TITLES):
                continue
        if not covered:
            gaps.append({'gap': Gap.UNLINKED, 'phrase': phrase})
            continue
        _start, end, _body, code, _link_phrase = covered[0]
        if end < sight.end():
            title = '' if code is None else code.title
            tail = text[end - len(title):sight.end()] if title else ''
            longer = title and any(
                len(candidate.title) > len(title) and tail.lower().startswith(candidate.title.lower())
                for candidate in _TITLES
            )
            if title and not longer:
                continue
            gaps.append({'gap': Gap.SHORT_TITLE, 'phrase': phrase})
        elif code is None:
            gaps.append({'gap': Gap.UNRESOLVED, 'phrase': phrase})
    linked = find_links(text, here=here)
    linked_text = '\n'.join(link.text for link in linked)
    for sight in _SESSION.finditer(text or ''):
        if sight.group(0) not in linked_text:
            gaps.append({'gap': Gap.UNLINKED, 'phrase': sight.group(0)})
    return gaps


def _review_nodes(node, gaps):
    if node.get('found'):
        book = _book(node['id'].split(' ', 1)[0])
        number = node['id'].split(' ', 1)[-1]
        for gap in inspect(node.get('text') or '', here=book):
            gap['code'] = book
            gap['section'] = number
            gap['citation'] = cite(book, one_section(number)).reference() if book else ''
            gaps.append(gap)
    for child in node.get('children') or []:
        _review_nodes(child, gaps)


def review(code, number, depth=1, codes=None, same=False, session=None):
    """The citation gaps in a section and the statutes it names, to ``depth`` hops.

    ``codes`` is the books the walk may enter. ``same`` stays in the open book.
    """
    tree = related(code, number, depth=depth, codes=codes, same=same, session=session)
    if not tree.get('found'):
        return tree
    gaps = []
    _review_nodes(tree, gaps)
    return {'found': True, 'citation': tree.get('citation'), 'gaps': gaps}


def related(code, number, depth=1, codes=None, same=False, session=None):
    """The section, its subdivisions, and statutes it cites, to ``depth`` hops.

    ``depth`` 0 is this section alone. A positive depth is that many hops.
    ``None`` or a negative depth follows until a section is repeated. The
    default remains 1. ``codes`` limits the hops to those books. ``same``
    follows only the open book. A citation of another book stays on the
    section. It is not opened.
    """
    doc = law_query.section(code, number, session=session)
    if not doc.get('found'):
        miss = {'found': False, 'reason': doc.get('reason'), 'mermaid': ''}
        if 'session' in doc:
            miss['session'] = doc['session']
        if 'indexed_in' in doc:
            miss['indexed_in'] = doc['indexed_in']
        return miss
    book = _book(doc.get('code') or code)
    tree = _node_dict(
        book or doc.get('code') or code,
        doc.get('section') or number,
        doc.get('text') or '',
        depth,
        set(),
        _scope(codes, same, book),
        session,
    )
    tree['citation'] = doc.get('citation')
    tree['mermaid'] = mermaid(tree)
    return tree
