"""CAML, the markup California publishes its statutes in.

The Legislative Counsel writes every section and every bill as CAML: an XML
document in the namespace ``http://lc.ca.gov/legalservices/schemas/caml.1#``,
whose bill documents name a schema ``xca.1.xsd`` that is not published. There
is no DTD and no XSD to read, so the grammar here is the one the corpus
shows — every LAW_SECTION LOB in ``pubinfo_2025.zip``, 162,431 documents, each
one well formed, each one rooted at ``caml:Content``. ``docs/caml.md`` records
the survey and the counts.

CAML borrows tags from XHTML, and that is what makes reading it as HTML look
safe. It is not. Two of its elements mean something no HTML reader knows:

* A ``span`` is empty 599,451 times and carries words 190 times. An empty span
  is not a wrapper — it is a character, or a rule drawn on a form. The space
  after a subdivision label is ``<span class="EnSpace"/>``, and an HTML reader
  drops it, so ``(a) No franchisor`` is stored as ``(a)No franchisor``.
* ``caml:Fraction`` holds a numerator and a denominator. Flattened as HTML,
  ``33<caml:Fraction>1/3</caml:Fraction> percent`` becomes ``3313 percent`` —
  a voting threshold of a third read as three thousand percent.

So a CAML document is parsed as CAML: ``parse`` gives the tree, ``words``
gives the reading. Nothing here opens a zip or the index.
"""

import enum
import xml.etree.ElementTree as ET

NAMESPACE = 'http://lc.ca.gov/legalservices/schemas/caml.1#'

XHTML = 'http://www.w3.org/1999/xhtml'


class Element(enum.Enum):
    """A CAML element. The value is the tag the file writes.

    These are every tag the corpus uses. The ones in the ``caml:`` namespace
    are California's own; the rest are borrowed from XHTML and keep their
    shape, not always their meaning — see ``SPAN``.
    """

    DOCUMENT = 'caml:Content'
    FRACTION = 'caml:Fraction'
    NUMERATOR = 'caml:Numerator'
    DENOMINATOR = 'caml:Denominator'
    FIELD = 'caml:LabelledField'
    INSERT = 'caml:TipIn'
    PARAGRAPH = 'p'
    HEADING = 'h1'
    BREAK = 'br'
    SPAN = 'span'
    ITALIC = 'i'
    BOLD = 'b'
    UNDERLINE = 'u'
    SUBSCRIPT = 'sub'
    SUPERSCRIPT = 'sup'
    TABLE = 'table'
    HEAD = 'thead'
    BODY = 'tbody'
    ROW = 'tr'
    CELL = 'td'
    HEADER = 'th'
    COLUMNS = 'colgroup'
    COLUMN = 'col'

    # A measure. Bills are CAML too, rooted at caml:MeasureDoc, and they carry
    # a vocabulary the codes never use: who wrote it, what it does, and the
    # flags the Constitution and the Joint Rules attach to it.
    MEASURE = 'caml:MeasureDoc'
    DESCRIPTION = 'caml:Description'
    IDENTIFIER = 'caml:Id'
    VERSION = 'caml:VersionNum'
    HISTORY = 'caml:History'
    ACTION = 'caml:Action'
    ACTION_TEXT = 'caml:ActionText'
    ACTION_DATE = 'caml:ActionDate'
    ACTION_LINE = 'caml:ActionLine'
    DOC_NAME = 'caml:DocName'
    FRAGMENT = 'caml:Fragment'
    LEGISLATIVE_INFO = 'caml:LegislativeInfo'
    SESSION_YEAR = 'caml:SessionYear'
    SESSION_NUM = 'caml:SessionNum'
    MEASURE_NUM = 'caml:MeasureNum'
    MEASURE_TYPE = 'caml:MeasureType'
    MEASURE_STATE = 'caml:MeasureState'
    MEASURE_CLASS = 'caml:MeasureClass'
    CHAPTER_NUM = 'caml:ChapterNum'
    CHAPTER_YEAR = 'caml:ChapterYear'
    CHAPTER_TYPE = 'caml:ChapterType'
    CHAPTER_SESSION_NUM = 'caml:ChapterSessionNum'
    AUTHORS = 'caml:Authors'
    AUTHOR_TEXT = 'caml:AuthorText'
    LEGISLATOR = 'caml:Legislator'
    HOUSE = 'caml:House'
    NAME = 'caml:Name'
    CONTRIBUTION = 'caml:Contribution'
    COMMITTEE = 'caml:Committee'
    MEMBERS = 'caml:Members'
    SUBJECT = 'caml:Subject'
    GENERAL_SUBJECT = 'caml:GeneralSubject'
    TITLE = 'caml:Title'
    LAW_TITLE = 'caml:LawTitle'
    RELATING_CLAUSE = 'caml:RelatingClause'
    DIGEST_KEY = 'caml:DigestKey'
    DIGEST_TEXT = 'caml:DigestText'
    PREAMBLE = 'caml:Preamble'
    WHEREAS = 'caml:Whereas'
    RESOLVED = 'caml:Resolved'
    RESOLUTION = 'caml:Resolution'
    BILL = 'caml:Bill'
    BILL_SECTION = 'caml:BillSection'
    ACT = 'caml:Act'
    LAW_SECTION = 'caml:LawSection'
    LAW_SECTION_VERSION = 'caml:LawSectionVersion'
    LAW_HEADING = 'caml:LawHeading'
    LAW_HEADING_TEXT = 'caml:LawHeadingText'
    LAW_HEADING_VERSION = 'caml:LawHeadingVersion'
    NUM = 'caml:Num'
    NUM_SPAN = 'caml:NumSpan'
    BUDGET_BILL = 'caml:BudgetBill'
    BUDGET_ITEM = 'caml:BudgetItem'
    BUDGET_HEADING = 'caml:BudgetHeading'
    BUDGET_HEADING_TEXT = 'caml:BudgetHeadingText'
    CORRECTION = 'caml:Correction'
    POSITIONING = 'caml:Positioning'
    ELECTION = 'caml:Election'
    GROUP = 'caml:GRP'
    # What the Constitution and the Joint Rules attach to a measure.
    MEASURE_INDICATORS = 'caml:MeasureIndicators'
    APPROPRIATION = 'caml:Appropriation'
    FISCAL_COMMITTEE = 'caml:FiscalCommittee'
    LOCAL_PROGRAM = 'caml:LocalProgram'
    URGENCY = 'caml:Urgency'
    TAX_LEVY = 'caml:TaxLevy'
    VOTE_REQUIRED = 'caml:VoteRequired'
    IMMEDIATE_EFFECT = 'caml:ImmediateEffect'
    IMMEDIATE_EFFECT_FLAGS = 'caml:ImmediateEffectFlags'
    PROP_25_TRAILER_BILL = 'caml:Prop25TrailerBill'
    USUAL_CURRENT_EXPENSES = 'caml:UsualCurrentExpenses'
    JOINT_RULE_11 = 'caml:JR11'


class Glyph(enum.Enum):
    """What a span sets. The value is the class the file writes.

    A space is a character the section is written with. A leader is the rule
    ruled across a form, and carries no word. The last two are the only ones
    that wrap anything.
    """

    EN_SPACE = 'EnSpace'
    EM_SPACE = 'EmSpace'
    THIN_SPACE = 'ThinSpace'
    NB_SPACE = 'NbSpace'
    DOTTED_LEADERS = 'DottedLeaders'
    SPACED_LEADERS = 'SpacedLeaders'
    DASHED_LEADERS = 'DashedLeaders'
    UNDERLINED_LEADERS = 'UnderlinedLeaders'
    SMALL_CAPS = 'SmallCaps'
    SPECIAL_FORMATTING = 'SpecialFormatting'


# A space is a space. En, em, thin and non-breaking are widths, and a width is
# not a word, so each one reads as the one character it stands for. Keeping the
# typographic codepoints instead would only split a search in two.
SPACES = frozenset({Glyph.EN_SPACE, Glyph.EM_SPACE, Glyph.THIN_SPACE, Glyph.NB_SPACE})

LEADERS = frozenset({
    Glyph.DOTTED_LEADERS, Glyph.SPACED_LEADERS,
    Glyph.DASHED_LEADERS, Glyph.UNDERLINED_LEADERS,
})

# A block stands on its own line. Everything else runs inside one.
BLOCKS = frozenset({
    Element.PARAGRAPH, Element.HEADING, Element.ROW,
    Element.TABLE, Element.HEAD, Element.BODY,
    # A measure's own prose. The rest of its vocabulary is a field on the
    # record, and reads where it sits.
    Element.BILL_SECTION, Element.WHEREAS, Element.RESOLVED, Element.PREAMBLE,
    Element.DIGEST_TEXT, Element.RELATING_CLAUSE, Element.ACTION_LINE,
    Element.LAW_HEADING_TEXT, Element.BUDGET_HEADING_TEXT, Element.LAW_TITLE,
})

CELLS = frozenset({Element.CELL, Element.HEADER})


class Piece:
    """One node of a CAML document.

    ``element`` is the member, or None for a tag the survey did not meet — the
    tag itself is then on ``tag``, and its words are still read, because a tag
    nobody has seen yet is not a reason to drop a sentence. ``glyph`` is set on
    a span. ``words`` is the text before the first child, and each child keeps
    the text that follows it on ``after``.
    """

    def __init__(self, tag, element=None, glyph=None, words='', after='', attrs=None, children=()):
        self.tag = tag
        self.element = element
        self.glyph = glyph
        self.words = words
        self.after = after
        self.attrs = attrs or {}
        self.children = list(children)

    def __repr__(self):
        return 'Piece(%s%s, %d children)' % (
            self.tag,
            '' if self.glyph is None else ' ' + self.glyph.value,
            len(self.children),
        )

    def walk(self):
        """This piece, then every piece under it, in reading order."""
        yield self
        for child in self.children:
            yield from child.walk()


class Document:
    """One parsed CAML document, and what the grammar did not cover.

    ``unknown`` names any tag or span class the corpus had not shown when this
    module was written. It is empty for every section in ``pubinfo_2025``. A
    later edition that adds one says so here instead of losing it quietly.
    """

    def __init__(self, root, unknown=()):
        self.root = root
        self.unknown = sorted(set(unknown))

    def __repr__(self):
        return 'Document(%r, unknown=%r)' % (self.root, self.unknown)

    def walk(self):
        return self.root.walk()


def _name(tag):
    """``{uri}Name`` as CAML writes it: ``caml:Name``, or the bare tag."""
    if tag.startswith('{'):
        uri, name = tag[1:].split('}', 1)
        if uri == NAMESPACE:
            return 'caml:' + name
        if uri == XHTML:
            return name
        return tag
    return tag


def parse(text):
    """One CAML document as a ``Document``.

    ``text`` is the LOB as it is stored. A document that is not well formed
    raises ``xml.etree.ElementTree.ParseError``; none of the 162,431 sections
    surveyed did.
    """
    return _document(ET.fromstring(text))


def _document(node):
    unknown = []
    root = _piece(node, unknown)
    return Document(root, unknown)


def _piece(node, unknown):
    tag = _name(node.tag)
    try:
        element = Element(tag)
    except ValueError:
        element = None
        unknown.append(tag)
    attrs = {_name(key): value for key, value in node.attrib.items()}
    glyph = None
    if element is Element.SPAN:
        word = attrs.get('class') or ''
        try:
            glyph = Glyph(word)
        except ValueError:
            if word:
                unknown.append('span.' + word)
    piece = Piece(tag, element, glyph, node.text or '', '', attrs)
    for kid in node:
        child = _piece(kid, unknown)
        child.after = kid.tail or ''
        piece.children.append(child)
    return piece


def words(piece, cell='\t', row='\n', block='\n\n'):
    """The words a CAML piece carries, read as CAML and not as HTML.

    A space span is the space it stands for. A leader is a rule and carries
    none. A fraction is its numerator over its denominator, so a third stays a
    third. A tip-in is a plate bound into the printed volume and has no words
    at all. A block ends where it ends.

    The reading is built in order, because one piece depends on what came
    before it: a fraction after a whole number is a mixed number and takes a
    space, and the same fraction after a bracket does not.
    """
    if isinstance(piece, Document):
        piece = piece.root
    held = []
    _read(piece, held, cell, row, block)
    return _trim(''.join(held))


def _read(piece, held, cell, row, block):
    element = piece.element
    if element is Element.INSERT:
        return
    if element is Element.BREAK:
        held.append('\n' + piece.after)
        return
    if element is Element.SPAN and piece.glyph is not None:
        if piece.glyph in SPACES:
            held.append(' ')
            _inside(piece, held, cell, row, block)
            held.append(piece.after)
            return
        if piece.glyph in LEADERS:
            _inside(piece, held, cell, row, block)
            held.append(piece.after)
            return
    if element is Element.FRACTION:
        held.append(_fraction(piece, _last(held)))
        held.append(piece.after)
        return
    if element in CELLS or element is Element.ROW or element in BLOCKS or element is Element.DOCUMENT:
        inner = []
        inner.append(piece.words)
        _inside(piece, inner, cell, row, block)
        body = ''.join(inner)
        if element in CELLS:
            held.append(body.strip() + cell)
        elif element is Element.ROW:
            held.append(body.rstrip(cell).rstrip() + row)
        else:
            body = body.strip()
            held.append(body + block if body else '')
        held.append(piece.after)
        return
    held.append(piece.words)
    _inside(piece, held, cell, row, block)
    held.append(piece.after)


def _inside(piece, held, cell, row, block):
    for child in piece.children:
        _read(child, held, cell, row, block)


def _last(held):
    for chunk in reversed(held):
        if chunk:
            return chunk[-1]
    return ''


def _fraction(piece, before):
    """A third is ``1/3``. After a whole number it is ``33 1/3``, a mixed one."""
    top = bottom = ''
    for child in piece.children:
        if child.element is Element.NUMERATOR:
            top = (child.words + _plain(child)).strip()
        elif child.element is Element.DENOMINATOR:
            bottom = (child.words + _plain(child)).strip()
    figure = '%s/%s' % (top, bottom) if top and bottom else top + bottom
    return (' ' + figure) if before.isdigit() else figure


def _plain(piece):
    return ''.join(child.words + _plain(child) + child.after for child in piece.children)


def _trim(text):
    lines = [line.rstrip() for line in text.split('\n')]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)


def glyphs(document):
    """How many of each glyph the document sets. A survey in one call."""
    tally = {}
    for piece in document.walk():
        if piece.glyph is not None:
            tally[piece.glyph] = tally.get(piece.glyph, 0) + 1
    return tally
