"""Rank terms by how distinctive they are inside a scope.

Term frequency is the sum of the section counts inside one scope. Document
frequency is how many sibling scopes contain the term. A term that is common
in the Fish and Game Code and rare in the other codes ranks high for that
code. The same term can rank low for the state, because the state total
includes every code.

``CODE``, ``CHAPTER``, and ``DIVISION`` are the California structure. ``STATE``
is one subdivision, such as ``US-CA``. ``FEDERAL`` is text stored with
subdivision ``US``. A scope with a single member has no contrast, so its
inverse document frequency is zero and the rank is frequency alone.
"""

import enum
import math
from heapq import heappush, heappushpop

from whoosh import index

from core import index_dir


class Surface(enum.Enum):
    """Where a note was read. A heading count never enters the body count."""

    HEADING = 'heading'
    BODY = 'body'


class Scope(enum.Enum):
    """The bucket a section's counts roll up into."""

    CODE = 'code'
    CHAPTER = 'chapter'
    DIVISION = 'division'
    ARTICLE = 'article'
    STATE = 'state'
    FEDERAL = 'federal'

    def __call__(self, key):
        """Close over this scope and one member. ``Scope.CODE('CIV').common()``."""
        return Lexicon(self, key)


class Lexicon:
    """One scope member. ``rank`` and ``common`` close over it."""

    def __init__(self, scope, key, limit=20, root=None):
        self.scope = scope
        self.key = str(key)
        self.limit = limit
        self.root = root

    def take(self, limit):
        return Lexicon(self.scope, self.key, limit, self.root)

    def rank(self):
        """Distinctive terms for this member. ``terms`` is a list and can be sliced."""
        return rank(self.scope, self.key, limit=self.limit, root=self.root)

    def common(self):
        """Shared terms for this member. ``terms`` is a list and can be sliced."""
        return common(self.scope, self.key, limit=self.limit, root=self.root)

    def needles(self):
        """The common terms split into needle forms and candidates."""
        return needle_terms(self.scope, self.key, limit=self.limit, root=self.root)

    def needle_count(self, rows):
        """Needle frequency for this scope member. Other words are not counted."""
        return ends(needle_weights(rows, scope=self.scope, key=self.key, limit=self.limit))

    def successive(self, rows):
        """Every overlapping pair in these rows, with its count and member count.

        ``pf`` is how often the pair occurs. ``df`` is how many members contain
        it. The list is not cut to the rank limit.
        """
        return successive(rows, scope=self.scope, key=self.key)

    def pairs(self, rows):
        """Adjacent words counted together for this scope member."""
        return ends(pair_weights(rows, scope=self.scope, key=self.key, limit=self.limit))

    def document(self, rows):
        """Phrases in this scope, with the members where each one appears."""
        return ends(document_phrases(rows, scope=self.scope))

    def cuts(self, rows, note=None):
        """Annotation frequency inside each cut, for this scope member."""
        return by_cut(rows, note, scope=self.scope, key=self.key, limit=self.limit)

    def hunt(self, rows, anchor):
        """Slide the scope outward from an anchor until one member is left.

        Pass the rows. A phrase search gathers those rows from ``LEGAL_TEXT``.
        Do not walk the live index from a test.
        """
        return hunt(rows, anchor, scope=self.scope, key=self.key)

    def extend(self, rows, anchor):
        """Grow an anchor by the words that precede and follow it in this scope.

        The neighbor stays only when it sits on that side in more than half
        the members that contain the anchor. The result is the whole phrase.
        Pass the rows. Do not walk the live index from a test.
        """
        return extend(rows, anchor, scope=self.scope, key=self.key)

    def frames(self, rows):
        """Words around a quantity, with the figure replaced by its classifier.

        ``rows`` are ``(member, sentence)``. ``not more than $1,000`` and
        ``not more than $10,000`` are one expression. Pass the rows.
        """
        return ends(frame_weights(rows, scope=self.scope, key=self.key, limit=self.limit))

    def shapes(self, note, rows):
        """The countable phrase for a quantity. The number is the classifier.

        A period keeps its lead, qualifier, unit, and trail. ``within 30 days``
        and ``within 95 days`` are one term. An amount is ``monetary``. A date
        is ``absolute``. A citation number stays on the mark. Pass the rows.
        """
        return ends(shape_weights(rows, note, scope=self.scope, key=self.key, limit=self.limit))

    def marks(self, note, rows):
        """Identified terms for one note inside this scope member.

        The first field of each row is the member key: a code, ``FGC 1`` for a
        chapter, division, or article, ``US-CA`` for a state, or ``US`` for
        federal text. ``af`` is the count in this member. Contrast is across
        the members present in ``rows``. Pass the rows. Do not walk the live
        index from a test.
        """
        return ends(mark_weights(rows, note, scope=self.scope, key=self.key, limit=self.limit))

    def headings(self, note, rows):
        """The same note counted on headings. A body row is left out."""
        return ends(mark_weights(
            rows, note, scope=self.scope, key=self.key, limit=self.limit, surface=Surface.HEADING,
        ))

    def terms(self, kind='rank'):
        """The term set for this member. ``rank`` is the distinctive set. ``common`` is the shared set."""
        rows = self.common() if kind == 'common' else self.rank()
        return _term_set(rows)

    def __call__(self):
        return self.terms()


class Noted:
    """One identified term inside one annotation kind.

    ``af`` is the annotation frequency in one scope member. ``df`` is how many
    members of that scope carry the annotation. This is not a token ``Weight``.
    """

    def __init__(self, note, term, af, df, idf, score, scope=None, key=None, surface=None):
        self.note = note
        self.term = term
        self.af = af
        self.df = df
        self.idf = idf
        self.score = score
        self.scope = scope
        self.key = key
        self.surface = surface if isinstance(surface, Surface) else Surface.BODY

    def __repr__(self):
        return 'Noted(%r, %r, %s)' % (self.note, self.term, self.af)


class Needle:
    """One surface word counted apart from tokens and annotations.

    ``nf`` is the needle frequency in one scope member. ``df`` is how many
    members of that scope contain the word. A term that is not a form is
    not counted here.
    """

    def __init__(self, term, nf, df, idf, score, scope=None, key=None):
        self.term = term
        self.nf = nf
        self.df = df
        self.idf = idf
        self.score = score
        self.scope = scope
        self.key = key

    def __repr__(self):
        return 'Needle(%r, %s)' % (self.term, self.nf)


class Pair:
    """Two adjacent words counted as one expression.

    ``pf`` is how often the two words occur in that order inside the scope
    member. ``expression`` is true when the phrase is already a surface word.
    """

    def __init__(self, left, right, pf, df, idf, score, scope=None, key=None, expression=False):
        self.left = left
        self.right = right
        self.pf = pf
        self.df = df
        self.idf = idf
        self.score = score
        self.scope = scope
        self.key = key
        self.expression = expression

    @property
    def phrase(self):
        return '%s %s' % (self.left, self.right)

    def __repr__(self):
        return 'Pair(%r, %s)' % (self.phrase, self.pf)


class Phrase:
    """A documented pair and the scope members that contain it.

    ``useful`` means the phrase appears in at least half the members of the
    scope. ``expression`` means it is already a surface word. A useful phrase
    that is not an expression is a candidate. The count does not add it to
    ``forms``.
    """

    def __init__(self, text, scope, members, df, n, expression):
        self.text = text
        self.scope = scope
        self.members = members
        self.df = df
        self.n = n
        self.expression = expression
        self.useful = n > 1 and df * 2 >= n

    def __repr__(self):
        return 'Phrase(%r, %s)' % (self.text, self.scope.value)


class Ends:
    """The high and low end of an ordered list.

    ``top`` is the start of the order already returned. ``bottom`` is the
    end of that same order. These are not a heading, and they are not the
    words in front of a title.
    """

    def __init__(self, rows):
        self.rows = list(rows)

    def top(self, n=1):
        if n <= 0:
            return []
        return self.rows[:n]

    def bottom(self, n=1):
        if n <= 0:
            return []
        return self.rows[-n:]

    def unique(self):
        """The first row for each term, phrase, or text."""
        seen = set()
        kept = []
        for row in self.rows:
            label = getattr(row, 'phrase', None) or getattr(row, 'text', None) or getattr(row, 'term', None)
            key = (type(row), label, getattr(row, 'note', None))
            if key in seen:
                continue
            seen.add(key)
            kept.append(row)
        return Ends(kept)

    def where(self, flag):
        """Rows on which ``flag`` is true. ``useful`` and ``expression`` are the flags."""
        return Ends([row for row in self.rows if getattr(row, flag, False)])

    def without(self, flag):
        """Rows on which ``flag`` is not true."""
        return Ends([row for row in self.rows if not getattr(row, flag, False)])

    def descending(self, field):
        """Highest ``field`` first. This is not ``Outline.order`` and not ``rank``."""
        return Ends(sorted(self.rows, key=lambda row: (-getattr(row, field, 0), _label(row))))

    def ascending(self, field):
        """Lowest ``field`` first."""
        return Ends(sorted(self.rows, key=lambda row: (getattr(row, field, 0), _label(row))))

    def __getitem__(self, item):
        return self.rows[item]

    def __iter__(self):
        return iter(self.rows)

    def __len__(self):
        return len(self.rows)

    def __eq__(self, other):
        if isinstance(other, Ends):
            return self.rows == other.rows
        return self.rows == other


def _label(row):
    return getattr(row, 'phrase', None) or getattr(row, 'text', None) or getattr(row, 'term', None) or ''


def ends(rows):
    """Close over an ordered list. ``top`` and ``bottom`` read its ends."""
    return Ends(rows)


class Weight:
    """One term's rank inside one scope member."""

    def __init__(self, scope, key, term, tf, df, idf, score):
        self.scope = scope
        self.key = key
        self.term = term
        self.tf = tf
        self.df = df
        self.idf = idf
        self.score = score

    def __repr__(self):
        return 'Weight(%s, %r, %r, %.3f)' % (self.scope.value, self.key, self.term, self.score)


_places = None


def _term_set(rows):
    return frozenset(item.term for item in rows)


def tf_weight(count):
    """Saturating term frequency. A second occurrence counts less than the first."""
    if count <= 0:
        return 0.0
    return 1.0 + math.log(count)


def af_weight(count):
    """Saturating annotation frequency. Parallel to term frequency.

    The count is how many times the note marked the term, not how many times
    the token occurs in the text.
    """
    return tf_weight(count)


def nf_weight(count):
    """Saturating needle frequency. Parallel to term frequency and annotation frequency.

    The count is how many times a surface word from ``forms`` was recorded.
    """
    return tf_weight(count)


def pf_weight(count):
    """Saturating pair frequency. How often two words were seen in that order."""
    return tf_weight(count)


def idf_weight(df, n):
    """Inverse document frequency across the members of one scope.

    One member gives no contrast, so the weight is zero.
    """
    if n <= 1 or df <= 0:
        return 0.0
    return math.log((n + 1) / (df + 1)) + 1.0


def _key(scope, fields):
    code = fields.get('LAW_CODE') or ''
    sub = fields.get('SUBDIVISION') or ''
    if scope is Scope.CODE:
        return code or None
    if scope is Scope.CHAPTER:
        chapter = fields.get('CHAPTER') or ''
        if not code or not chapter:
            return None
        return '%s %s' % (code, chapter)
    if scope is Scope.DIVISION:
        division = fields.get('DIVISION') or ''
        if not code or not division:
            return None
        return '%s %s' % (code, division)
    if scope is Scope.ARTICLE:
        article = fields.get('ARTICLE') or ''
        if not code or not article:
            return None
        return '%s %s' % (code, article)
    if scope is Scope.STATE:
        if sub.startswith('US-'):
            return sub
        return None
    if scope is Scope.FEDERAL:
        if sub == 'US':
            return 'US'
        return None
    return None


def _load(path):
    global _places
    if _places is not None and _places.get('path') == path:
        return _places
    ix = index.open_dir(path)
    with ix.searcher() as searcher:
        placed = []
        members = {scope: set() for scope in Scope}
        for docnum in range(searcher.doc_count()):
            fields = searcher.stored_fields(docnum)
            row = {}
            for scope in Scope:
                key = _key(scope, fields)
                row[scope] = key
                if key:
                    members[scope].add(key)
            placed.append(row)
    _places = {'path': path, 'rows': placed, 'members': members}
    return _places


def _keep(term):
    word = term.decode('utf-8') if isinstance(term, bytes) else term
    if len(word) < 3 or word.isdigit():
        return None
    return word


def rollup(hits):
    """Add one term's section counts into every scope those sections belong to.

    ``hits`` is ``(keys, weight)``. ``keys`` maps a scope to the member that
    contains the section. Term frequency at a wider scope is the sum. Document
    frequency is how many members at that scope received a count. The postings
    are read once.
    """
    totals = {scope: {} for scope in Scope}
    for keys, weight in hits:
        if weight <= 0:
            continue
        for scope, key in keys.items():
            if not key:
                continue
            bucket = totals[scope]
            bucket[key] = bucket.get(key, 0) + weight
    return totals


_tallies = None


def _tally(path):
    """One lexicon walk. Later ranks reuse it for every scope and member."""
    global _tallies
    if _tallies is not None and _tallies.get('path') == path:
        return _tallies
    loaded = _load(path)
    rows = loaded['rows']
    ix = index.open_dir(path)
    stored = {scope: {} for scope in Scope}
    with ix.searcher() as searcher:
        reader = searcher.reader()
        for raw in reader.lexicon('LEGAL_TEXT'):
            term = _keep(raw)
            if term is None:
                continue
            postings = reader.postings('LEGAL_TEXT', raw)
            hits = []
            while postings.is_active():
                docnum = postings.id()
                keys = rows[docnum] if docnum < len(rows) else None
                if keys:
                    hits.append((keys, postings.weight()))
                postings.next()
            if not hits:
                continue
            for scope, members in rollup(hits).items():
                n = len(loaded['members'][scope])
                scope_store = stored[scope]
                df = len(members)
                idf = idf_weight(df, n)
                for key, tf in members.items():
                    scored = tf_weight(tf) * idf if idf else tf_weight(tf)
                    scope_store.setdefault(key, {})[term] = Weight(
                        scope, key, term, tf, df, idf, scored,
                    )
    _tallies = {'path': path, 'stored': stored}
    return _tallies


def rank(scope, key, limit=20, root=None):
    """The highest scoring terms for one member of ``scope``.

    ``key`` is a code token (``FGC``), a code and chapter (``FGC 1``), a
    code and division (``FGC 1``), a code and article, a state (``US-CA``),
    or ``US`` for federal text. A missing member is a miss. The lexicon is
    walked once for the index; each later member reads that tally.
    """
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    path = str(root or index_dir())
    if not index.exists_in(path):
        return {'found': False, 'reason': 'not_indexed', 'scope': scope, 'key': key, 'terms': []}
    loaded = _load(path)
    if key not in loaded['members'][scope]:
        return {'found': False, 'reason': 'unknown_scope', 'scope': scope, 'key': key, 'terms': []}
    weights = _tally(path)['stored'][scope].get(key) or {}
    best = []
    for term, weight in weights.items():
        scored = weight.score
        if len(best) < limit:
            heappush(best, (scored, term, weight))
        elif scored > best[0][0]:
            heappushpop(best, (scored, term, weight))
    ordered = [item[2] for item in sorted(best, key=lambda item: (-item[0], item[1]))]
    return {'found': True, 'reason': None, 'scope': scope, 'key': key, 'terms': ordered}


def _by_common(weights, limit):
    """Highest document frequency first. That is the inverse of the rank score."""
    best = []
    for weight in weights:
        mark = (weight.df, weight.tf)
        if len(best) < limit:
            heappush(best, (mark, weight.term, weight))
        elif mark > best[0][0]:
            heappushpop(best, (mark, weight.term, weight))
    return [item[2] for item in sorted(best, key=lambda item: (-item[0][0], -item[0][1], item[1]))]


def common(scope, key, limit=20, root=None):
    """Terms that appear in the most members of ``scope``.

    ``rank`` surfaces a term that is frequent here and rare elsewhere.
    This list surfaces a term that is shared. A shared term is where a
    needle form usually sits. A missing member is a miss.
    """
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    path = str(root or index_dir())
    if not index.exists_in(path):
        return {'found': False, 'reason': 'not_indexed', 'scope': scope, 'key': key, 'terms': []}
    loaded = _load(path)
    if key not in loaded['members'][scope]:
        return {'found': False, 'reason': 'unknown_scope', 'scope': scope, 'key': key, 'terms': []}
    weights = _tally(path)['stored'][scope].get(key) or {}
    return {
        'found': True, 'reason': None, 'scope': scope, 'key': key,
        'terms': _by_common(weights.values(), limit),
    }


def mark_term(note, text, target):
    """The term a stored annotation contributes.

    A case note's term is the printed word. ``uppercase`` and ``title`` name
    the kind, not the term. Every other note uses its target, including a
    digit string such as a dollar amount. The token lexicon drops those.
    """
    kind = getattr(note, 'value', note) or ''
    if kind == 'case':
        word = (text or '').strip()
        return word.casefold() if word else None
    value = (target if target is not None else '').strip()
    return value.casefold() if value else None


def shape_term(note, text):
    """The phrase a quantity contributes. A citation number is not a quantity."""
    from citations import Absolute, Duration, Monetary
    kind = getattr(note, 'value', note) or ''
    raw = (text or '').strip()
    readers = {'period': Duration, 'amount': Monetary, 'date': Absolute}
    reader = readers.get(kind)
    if reader is None or not raw:
        return None
    found = reader.parse(raw)
    return found.shape() if found else None


class Growth:
    """An anchor and the words that precede and follow it across a scope.

    ``before`` and ``after`` are the words that co-occur on that side. ``phrase``
    is those words with the anchor between them.
    """

    def __init__(self, before, anchor, after, phrase, support, members, distance=None):
        self.before = before
        self.anchor = anchor
        self.after = after
        self.phrase = phrase
        self.support = support
        self.members = members
        self.distance = distance

    def __repr__(self):
        return 'Growth(%r)' % (self.phrase,)


def _anchor_hits(rows, anchor):
    from citations import measure_tokens
    tokens = tuple(anchor.split()) if isinstance(anchor, str) else tuple(anchor)
    hits = []
    if not tokens:
        return tokens, hits
    for row in rows:
        words = row[1]
        if isinstance(words, str):
            words = measure_tokens(words)
        else:
            words = [word.casefold() for word in words]
        width = len(tokens)
        for index in range(len(words) - width + 1):
            if tuple(words[index:index + width]) == tokens:
                hits.append((str(row[0]), words, index))
    return tokens, hits


def _edge_word(hits, place):
    """The word on one side of every hit in a member. A split member does not vote."""
    grouped = {}
    for member, words, index in hits:
        at = place(words, index)
        grouped.setdefault(member, []).append(at)
    votes = {}
    for member, edges in grouped.items():
        if any(edge is None for edge in edges) or len(set(edges)) != 1:
            continue
        votes.setdefault(edges[0], set()).add(member)
    return votes


def extend(rows, anchor, scope=Scope.CODE, key=None):
    """Grow ``anchor`` by the co-occurring words before and after it.

    A pair counts only the one word on each side. A frame keeps a fixed
    window. This walks outward. A neighbor is kept when more than half the
    members that contain the anchor have that same word on that side. Six
    words is the furthest the walk goes on one side. A missing anchor is none.
    """
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    tokens, hits = _anchor_hits(rows, anchor)
    group = {member for member, _words, _index in hits}
    if not hits or (key is not None and str(key) not in group):
        return None
    before = []
    after = []

    def attached(word, seen):
        return word is not None and len(seen) * 2 > len(group)

    while len(before) < 6:
        def place(words, index, _before=tuple(before)):
            at = index - len(_before)
            if at <= 0:
                return None
            return words[at - 1]
        votes = _edge_word(hits, place)
        if not votes:
            break
        word, seen = max(votes.items(), key=lambda item: (len(item[1]), item[0]))
        if not attached(word, seen):
            break
        before.insert(0, word)
    while len(after) < 6:
        def place(words, index, _after=tuple(after), _width=len(tokens)):
            at = index + _width + len(_after)
            if at >= len(words):
                return None
            return words[at]
        votes = _edge_word(hits, place)
        if not votes:
            break
        word, seen = max(votes.items(), key=lambda item: (len(item[1]), item[0]))
        if not attached(word, seen):
            break
        after.append(word)
    phrase = ' '.join(before + list(tokens) + after)
    return Growth(tuple(before), tokens, tuple(after), phrase, len(group), len(group))


def _pair_table(rows, anchor):
    """Every overlapping successive pair, counted once. The anchor's members too."""
    from citations import measure_tokens
    tokens = tuple(anchor.split()) if isinstance(anchor, str) else tuple(anchor)
    pairs = {}
    group = set()
    if not tokens:
        return tokens, group, pairs
    width = len(tokens)
    for row in rows:
        words = row[1]
        if isinstance(words, str):
            words = measure_tokens(words)
        else:
            words = [word.casefold() for word in words]
        member = str(row[0])
        for left, right in zip(words, words[1:]):
            pairs.setdefault((left, right), set()).add(member)
        for index in range(len(words) - width + 1):
            if tuple(words[index:index + width]) == tokens:
                group.add(member)
                break
    return tokens, group, pairs


def _linked(pairs, group, edge, side):
    """The next word in the pair table that the current members still share."""
    if len(group) <= 1 or not edge:
        return None, group
    votes = {}
    for (left, right), seen in pairs.items():
        if side == 'left' and right == edge:
            word = left
        elif side == 'right' and left == edge:
            word = right
        else:
            continue
        hold = seen & group
        if hold:
            votes.setdefault(word, set()).update(hold)
    if not votes:
        return None, group
    word, seen = max(votes.items(), key=lambda item: (len(item[1]), item[0]))
    if len(seen) * 2 <= len(group):
        return None, group
    return word, seen


def hunt(rows, anchor, scope=Scope.CODE, key=None):
    """Grow an anchor from successive pairs until the scope has no contrast.

    One pass counts every overlapping pair and the members that contain it.
    The scope starts as the members that contain the anchor. The next word is
    the other half of the pair on that side, kept when more than half of the
    current members have it. The scope slides to them. The walk stops when
    one member is left, or when the next pair fails the half test. ``distance``
    is how many words were added. A missing anchor is none.
    """
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    tokens, group, pairs = _pair_table(rows, anchor)
    if not group or (key is not None and str(key) not in group):
        return None
    origin = set(group)
    before = []
    after = []
    edge = tokens[0]
    while True:
        word, seen = _linked(pairs, group, edge, 'left')
        if word is None:
            break
        before.insert(0, word)
        group = seen
        edge = word
    edge = tokens[-1]
    while True:
        word, seen = _linked(pairs, group, edge, 'right')
        if word is None:
            break
        after.append(word)
        group = seen
        edge = word
    phrase = ' '.join(before + list(tokens) + after)
    return Growth(
        tuple(before), tokens, tuple(after), phrase,
        len(group), len(origin), len(before) + len(after),
    )


def frame_weights(rows, scope=Scope.CODE, key=None, limit=20):
    """How often the same words surround a quantity. The number is not the term."""
    from citations import frames
    shaped = []
    for row in rows:
        for phrase in frames(row[1]):
            shaped.append((row[0], 'frame', phrase, phrase))
    return mark_weights(shaped, 'frame', scope=scope, key=key, limit=limit)


def shape_weights(rows, note, scope=Scope.CODE, key=None, limit=20):
    """Annotation frequency of the quantity phrase. The stored target is unchanged."""
    shaped = []
    for row in rows:
        term = shape_term(row[1], row[2])
        if term is None and len(row) > 3:
            term = shape_term(row[1], row[3])
        if term is None:
            continue
        shaped.append((row[0], row[1], row[2], term))
    return mark_weights(shaped, note, scope=scope, key=key, limit=limit)


def _surface(row):
    """``heading`` or ``body``. A row that does not say is a body."""
    for field in row[4:]:
        value = getattr(field, 'value', field)
        if value in ('heading', 'body'):
            return Surface(value)
    return Surface.BODY


def rollup_marks(rows, surface=None):
    """Count identified terms by note and by scope member.

    ``rows`` are ``(member, note, text, target)``. A later field ``heading``
    or ``body`` is the surface. A row that does not say is a body. The member
    is a code, a code and chapter, a code and division, a code and article, a
    state, or ``US``. Annotation frequency is how many times that term was
    marked in the member on that surface. The token postings are not read.
    """
    totals = {}
    for row in rows:
        member, note, text, target = row[0], row[1], row[2], row[3]
        if surface is not None and _surface(row) is not surface:
            continue
        term = mark_term(note, text, target)
        kind = getattr(note, 'value', note) or ''
        if not term or not member or not kind:
            continue
        members = totals.setdefault(kind, {})
        bucket = members.setdefault(str(member), {})
        bucket[term] = bucket.get(term, 0) + 1
    return totals


def mark_weights(rows, note, scope=Scope.CODE, key=None, limit=20, surface=Surface.BODY):
    """Annotation frequency times inverse document frequency for one note.

    Document frequency is how many members of ``scope`` in ``rows`` carry that
    term. ``af`` is the count in ``key``. A scope with one member has no
    contrast, so the rank is annotation frequency alone. A key that is absent
    from the rows is a miss.
    """
    kind = getattr(note, 'value', note) or ''
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    if not isinstance(surface, Surface):
        surface = Surface(surface)
    members = rollup_marks(rows, surface=surface).get(kind) or {}
    if key is not None and str(key) not in members:
        return []
    n = len(members)
    here = str(key) if key is not None else None
    counts = {}
    for member, terms in members.items():
        for term, af in terms.items():
            seen, total = counts.get(term, (0, 0))
            extra = af if here is None or member == here else 0
            if here is not None and member != here and term not in (members.get(here) or {}):
                counts[term] = (seen + 1, total)
                continue
            counts[term] = (seen + 1, total + extra)
    weights = []
    focus = members.get(here, {}) if here is not None else None
    for term, (df, af) in counts.items():
        if focus is not None and term not in focus:
            continue
        if focus is not None:
            af = focus[term]
        idf = idf_weight(df, n)
        scored = af_weight(af) * idf if idf else af_weight(af)
        weights.append(Noted(kind, term, af, df, idf, scored, scope, here, surface))
    best = []
    for weight in weights:
        mark = weight.score
        if len(best) < limit:
            heappush(best, (mark, weight.term, weight))
        elif mark > best[0][0]:
            heappushpop(best, (mark, weight.term, weight))
    return [item[2] for item in sorted(best, key=lambda item: (-item[0], item[1]))]


def _cut_name(row):
    """The cut a row belongs to. A cut note's target is the cut. A fifth field assigns any other note."""
    from needles import Cut
    words = {cut.value for cut in Cut}
    named = row[4] if len(row) > 4 else None
    if named in words:
        return named
    kind = getattr(row[1], 'value', row[1])
    target = (row[3] or '').strip().casefold()
    if kind == 'cut' and target in words:
        return target
    return None


def by_cut(rows, note=None, scope=Scope.CODE, key=None, limit=20):
    """Annotation frequency aggregated by cut, inside one scope.

    Each cut is its own ``mark_weights`` list. A row with no cut is left out.
    ``note`` keeps one kind. Without it, a cut note supplies the frequency of
    the label itself. ``scope`` is code, chapter, division, article, state, or
    federal. The first field of each row is that member.
    """
    chosen = getattr(note, 'value', note) if note else None
    buckets = {}
    for row in rows:
        cut = _cut_name(row)
        if cut is None:
            continue
        kind = getattr(row[1], 'value', row[1])
        if chosen and kind != chosen:
            continue
        buckets.setdefault(cut, []).append(row[:4])
    kind = chosen or 'cut'
    return {
        cut: mark_weights(grouped, kind, scope=scope, key=key, limit=limit)
        for cut, grouped in buckets.items()
    }


def _needle_form(term, known):
    """The surface word in ``term``, or None when the term is not in the set."""
    word = (term or '').strip().casefold()
    if word in known:
        return word
    head, _, tail = word.partition(' ')
    if head == 'this' and tail in known:
        return tail
    return None


def rollup_needles(rows):
    """Count surface words by scope member.

    ``rows`` are ``(member, term)``. A term that is not a form is left out.
    ``this`` plus a form counts as that form. Token postings are not read.
    """
    from needles import forms
    known = {form.casefold() for form in forms()}
    totals = {}
    for member, term, *_rest in rows:
        form = _needle_form(term, known)
        if not form or not member:
            continue
        bucket = totals.setdefault(str(member), {})
        bucket[form] = bucket.get(form, 0) + 1
    return totals


def needle_weights(rows, scope=Scope.CODE, key=None, limit=20):
    """Needle frequency times inverse scope frequency.

    ``nf`` is the count in ``key``. Document frequency is how many members
    contain that form. A key absent from the rows is a miss.
    """
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    members = rollup_needles(rows)
    if key is not None and str(key) not in members:
        return []
    n = len(members)
    here = str(key) if key is not None else None
    focus = members.get(here, {}) if here is not None else None
    counts = {}
    for member, terms in members.items():
        for term, nf in terms.items():
            seen, total = counts.get(term, (0, 0))
            extra = nf if here is None or member == here else 0
            counts[term] = (seen + 1, total + extra)
    weights = []
    for term, (df, nf) in counts.items():
        if focus is not None and term not in focus:
            continue
        if focus is not None:
            nf = focus[term]
        idf = idf_weight(df, n)
        scored = nf_weight(nf) * idf if idf else nf_weight(nf)
        weights.append(Needle(term, nf, df, idf, scored, scope, here))
    best = []
    for weight in weights:
        mark = weight.score
        if len(best) < limit:
            heappush(best, (mark, weight.term, weight))
        elif mark > best[0][0]:
            heappushpop(best, (mark, weight.term, weight))
    return [item[2] for item in sorted(best, key=lambda item: (-item[0], item[1]))]


_TYPE = frozenset(('duration', 'monetary', 'absolute'))


def _fold(token):
    token = str(token)
    return token if token.startswith('{') else token.casefold()


def _placeholder(token):
    return str(token).startswith('{') or token in _TYPE


def _windows(words):
    if isinstance(words, str):
        from citations import plain_tokens
        return plain_tokens(words)
    return [_fold(token) for token in words]


def _tally(bucket, tokens, placeholders=False):
    for left, right in zip(tokens, tokens[1:]):
        marked = _placeholder(left) or _placeholder(right)
        if placeholders != marked:
            continue
        pair = (left, right)
        bucket[pair] = bucket.get(pair, 0) + 1


def rollup_pairs(rows):
    """Count adjacent word pairs by scope member.

    ``rows`` are ``(member, words)``. ``words`` is one window, a sentence or
    a section, as a string or a sequence. Order is kept. A repeated pair in
    the same window counts again. Token postings are not read. A string is
    counted twice: the printed pairs, and the pairs that contain a placeholder
    or a quantity type.
    """
    totals = {}
    for member, words, *_rest in rows:
        if not member:
            continue
        bucket = totals.setdefault(str(member), {})
        _tally(bucket, _windows(words))
        if isinstance(words, str):
            from citations import marked_tokens
            _tally(bucket, marked_tokens(words), placeholders=True)
    return totals


def glance(term, rows, limit=8):
    """Frequency and neighbors for one hovered term, from rows already in hand.

    ``rows`` are ``(member, text)``. ``df`` is how many members contain the
    term. ``pf`` is how often it occurs. A neighbor is the pair on either side,
    most frequent first. This pass does not walk the index.
    """
    from citations import plain_tokens
    tokens = [piece.casefold() for piece in str(term or '').split() if piece]
    if not tokens:
        return {'found': False, 'reason': 'not_in_index', 'term': ''}
    width = len(tokens)
    seen = {}
    neighbor = {}
    count = 0
    for member, text, *_rest in rows:
        words = plain_tokens(text or '')
        starts = [
            index for index in range(len(words) - width + 1)
            if words[index:index + width] == tokens
        ]
        if not starts:
            continue
        count += len(starts)
        seen[str(member)] = seen.get(str(member), 0) + len(starts)
        for start in starts:
            if start:
                pair = (words[start - 1], words[start])
                neighbor[pair] = neighbor.get(pair, 0) + 1
            end = start + width - 1
            if end + 1 < len(words):
                pair = (words[end], words[end + 1])
                neighbor[pair] = neighbor.get(pair, 0) + 1
    if not seen:
        return {'found': False, 'reason': 'not_in_index', 'term': ' '.join(tokens)}
    ranked = sorted(neighbor.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))[:limit]
    return {
        'found': True,
        'term': ' '.join(tokens),
        'pf': count,
        'df': len(seen),
        'neighbors': [
            {'left': left, 'right': right, 'phrase': '%s %s' % (left, right), 'pf': pf}
            for (left, right), pf in ranked
        ],
    }


def successive(rows, scope=Scope.CODE, key=None):
    """Every overlapping successive pair, with how often it occurs.

    ``pf`` is the count. ``df`` is how many members contain the pair. A key
    that is absent from the rows is an empty list. The rank limit does not apply.
    """
    from needles import forms
    known = {form.casefold() for form in forms()}
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    members = rollup_pairs(rows)
    if key is not None and str(key) not in members:
        return ends([])
    n = len(members)
    here = str(key) if key is not None else None
    totals = {}
    for member, terms in members.items():
        for pair, pf in terms.items():
            count, seen = totals.get(pair, (0, 0))
            extra = pf if here is None or member == here else 0
            totals[pair] = (count + extra, seen + 1)
    found = []
    focus = members.get(here, {}) if here is not None else None
    for (left, right), (pf, df) in totals.items():
        if focus is not None and (left, right) not in focus:
            continue
        if focus is not None:
            pf = focus[(left, right)]
        idf = idf_weight(df, n)
        scored = pf_weight(pf) * idf if idf else pf_weight(pf)
        phrase = '%s %s' % (left, right)
        found.append(Pair(
            left, right, pf, df, idf, scored, scope, here, phrase in known,
        ))
    found.sort(key=lambda item: (-item.pf, item.left, item.right))
    return ends(found)


def pair_weights(rows, scope=Scope.CODE, key=None, limit=20):
    """Pair frequency times inverse scope frequency.

    ``pf`` is the count of that ordered pair in ``key``. A pair whose phrase
    is already a form is an expression. A key absent from the rows is a miss.
    """
    from needles import forms
    known = {form.casefold() for form in forms()}
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    members = rollup_pairs(rows)
    if key is not None and str(key) not in members:
        return []
    n = len(members)
    here = str(key) if key is not None else None
    focus = members.get(here, {}) if here is not None else None
    counts = {}
    for member, terms in members.items():
        for pair, pf in terms.items():
            seen, total = counts.get(pair, (0, 0))
            extra = pf if here is None or member == here else 0
            counts[pair] = (seen + 1, total + extra)
    weights = []
    for (left, right), (df, pf) in counts.items():
        if focus is not None and (left, right) not in focus:
            continue
        if focus is not None:
            pf = focus[(left, right)]
        idf = idf_weight(df, n)
        scored = pf_weight(pf) * idf if idf else pf_weight(pf)
        phrase = '%s %s' % (left, right)
        weights.append(Pair(
            left, right, pf, df, idf, scored, scope, here, phrase in known,
        ))
    best = []
    for weight in weights:
        mark = weight.score
        if len(best) < limit:
            heappush(best, (mark, weight.phrase, weight))
        elif mark > best[0][0]:
            heappushpop(best, (mark, weight.phrase, weight))
    return [item[2] for item in sorted(best, key=lambda item: (-item[0], item[1]))]


def document_phrases(rows, scope=Scope.CODE):
    """Record each adjacent phrase and the members of ``scope`` that contain it.

    ``rows`` are ``(member, words)``. The member is the key for this scope.
    A phrase in one member is relevant there. It is useful when it is shared
    across the scope. Pass the rows. Do not walk the live index from a test.
    """
    from needles import forms
    known = {form.casefold() for form in forms()}
    if not isinstance(scope, Scope):
        scope = Scope(scope)
    totals = rollup_pairs(rows)
    seen = {}
    for member, pairs in totals.items():
        for left, right in pairs:
            text = '%s %s' % (left, right)
            seen.setdefault(text, set()).add(member)
    n = len(totals)
    recorded = [
        Phrase(text, scope, frozenset(members), len(members), n, text in known)
        for text, members in seen.items()
    ]
    return sorted(recorded, key=lambda item: (-item.df, item.text))


def useful_needles(weights, n):
    """Split identified terms into needles, candidates, quantities, and the rest.

    A needle is already a surface word, or ``this`` plus that word. A quantity
    is an amount, a period, or a date. A candidate is shared across the scope
    (``df`` at least half of ``n``) and is not a needle or a quantity. A rarer
    term stays distinctive. It is a weight, not a new word class.
    """
    from needles import forms
    known = {form.casefold() for form in forms()}
    needles = []
    candidates = []
    quantities = []
    distinctive = []
    for weight in weights:
        term = (weight.term or '').casefold()
        note = weight.note
        head, _, tail = term.partition(' ')
        internal = head == 'this' and tail in known
        if note in ('amount', 'period', 'date') or term.isdigit():
            quantities.append(weight)
        elif term in known or internal:
            needles.append(weight)
        elif n > 1 and weight.df * 2 >= n:
            candidates.append(weight)
        else:
            distinctive.append(weight)
    return {
        'needles': needles,
        'candidates': candidates,
        'quantities': quantities,
        'distinctive': distinctive,
    }


def needle_terms(scope, key, limit=20, root=None):
    """Split the common terms into needle forms and terms that are not forms yet."""
    found = common(scope, key, limit=limit, root=root)
    if not found['found']:
        found['needles'] = []
        found['candidates'] = []
        return found
    from needles import forms
    known = {form.casefold() for form in forms()}
    needles = []
    candidates = []
    for weight in found['terms']:
        if weight.term.casefold() in known:
            needles.append(weight)
        else:
            candidates.append(weight)
    found['needles'] = needles
    found['candidates'] = candidates
    return found
