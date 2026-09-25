"""Words a hunter may search for.

``Section``, ``Article``, and ``Bill`` are classes of words. A general
class applies to every law. A subclass applies only in the book or shelf
that gives the word a further meaning. Hunters ask ``consider`` instead of
keeping their own list.
"""

import enum
import re


class Cut(enum.Enum):
    """A label under a section. The value is the word in the text."""

    SUBDIVISION = 'subdivision'
    SUBSECTION = 'subsection'
    PARAGRAPH = 'paragraph'
    SUBPARAGRAPH = 'subparagraph'
    CLAUSE = 'clause'
    SUBCLAUSE = 'subclause'
    ITEM = 'item'
    SUBITEM = 'subitem'


class Breakdown:
    """The units inside a section. A book holds an instance of a subclass."""

    cuts = frozenset()

    def members(self):
        return self.cuts


class General(Breakdown):
    """Every cut. The parser uses this set for a book that does not define one."""

    cuts = frozenset(Cut)


class House(Breakdown):
    """The House order. It starts at subsection."""

    cuts = frozenset((
        Cut.SUBSECTION, Cut.PARAGRAPH, Cut.SUBPARAGRAPH, Cut.CLAUSE,
        Cut.SUBCLAUSE, Cut.ITEM, Cut.SUBITEM,
    ))


class California(Breakdown):
    """A code that defines subdivision. Subsection is not in this set."""

    cuts = frozenset((
        Cut.SUBDIVISION, Cut.PARAGRAPH, Cut.SUBPARAGRAPH, Cut.CLAUSE,
        Cut.SUBCLAUSE, Cut.ITEM, Cut.SUBITEM,
    ))


class Insurance(California):
    """Insurance Code section 10 names subdivision and subsection."""

    cuts = California.cuts | frozenset((Cut.SUBSECTION,))


def members(breakdown):
    """The cuts in one breakdown. A class is read from its instance."""
    if isinstance(breakdown, type):
        breakdown = breakdown()
    return breakdown.members()


def _cut_words(breakdown):
    return tuple(cut.value for cut in members(breakdown))


class Word:
    """One class of words. ``forms`` are the surface words."""

    forms = ()
    cuts = ()
    reading = ''
    codes = frozenset()
    shelf = None
    internal = False

    @classmethod
    def applies(cls, code=None, shelf=None):
        if not cls.forms and not cls.cuts:
            return False
        token = getattr(code, 'value', code)
        if cls.codes and token not in cls.codes:
            return False
        if cls.shelf and shelf != cls.shelf:
            return False
        return True


class Section(Word):
    """The basic unit of a bill and of an enacted statute."""

    forms = ('section',)
    breakdown = General
    cuts = _cut_words(General)
    reading = 'A section shall contain, as nearly as may be, a single proposition of enactment.'
    internal = True


class CodeSection(Section):
    """A code that defines section and subdivision for itself.

    The defining sections are BPC 15, CORP 10, EVID 7, FGC 73, FIN 9,
    GOV 10, HNC 10, HSC 10, INS 10, PUC 10, RTC 10, UIC 9, VEH 11, WAT 10,
    and WIC 10. Insurance Code section 10 also names subsection. Evidence
    Code section 7 also names paragraph. The rest of the cuts stay, so a
    federal subsection in the same code still parses. Education Code
    section 71, Elections Code section 353, Food and Agricultural Code
    section 41, Labor Code section 10, Military and Veterans Code section
    10, Public Resources Code section 10, and Streets and Highways Code
    section 10 define section only.
    """

    codes = frozenset((
        'BPC', 'CORP', 'EVID', 'FGC', 'FIN', 'GOV', 'HNC', 'HSC',
        'PUC', 'RTC', 'UIC', 'VEH', 'WAT', 'WIC',
    ))
    breakdown = California


class InsuranceSection(CodeSection):
    """Insurance Code section 10 names subdivision and subsection."""

    codes = frozenset(('INS',))
    breakdown = Insurance


class PublicUtilitiesSection(CodeSection):
    """Public Utilities Code section 10. Not every code defines these words."""

    codes = frozenset(('PUC',))
    reading = (
        'Section means a section of this code unless some other statute is named. '
        'Subdivision means a subdivision of the section in which that word occurs '
        'unless some other section is named.'
    )


class Article(Word):
    """A unit of a code, or an article of a constitution."""

    forms = ('article',)
    reading = 'An article is a heading in a code. In the constitution it identifies the section.'
    internal = True


class Bill(Word):
    """A measure. The Joint Rules give the word a wider meaning."""

    forms = ('bill',)
    reading = 'A measure introduced in a house.'


class JointBill(Bill):
    """Joint Rule 4. The wider meaning belongs to those rules."""

    reading = (
        'Bill includes a resolution ratifying a proposed amendment to the '
        'United States Constitution and a resolution calling for a constitutional convention.'
    )
    shelf = 'joint-rules'


class Act(Word):
    forms = ('act',)
    reading = 'The statute being amended, when the word sits inside the quotes.'
    internal = True


class Part(Word):
    forms = ('part',)
    internal = True


class Chapter(Word):
    forms = ('chapter',)
    internal = True


class Division(Word):
    forms = ('division',)
    internal = True


class Title(Word):
    forms = ('title',)
    internal = True


class Subtitle(Word):
    forms = ('subtitle',)
    internal = True


class Subchapter(Word):
    forms = ('subchapter',)
    internal = True


class Subpart(Word):
    forms = ('subpart',)
    internal = True


class CodeWord(Word):
    forms = ('code',)
    internal = True


class Paragraph(Word):
    forms = ('paragraph',)
    internal = True


class Constitution(Word):
    forms = ('constitution',)
    internal = True


class Modal(Word):
    """shall and may. The House guide treats may not as a denial."""

    forms = ('shall', 'may', 'may not')
    readings = {
        'shall': 'The duty is obligatory.',
        'may': 'The actor is allowed, not required.',
        'may not': 'A denial is required.',
    }
    reading = readings['shall']


class Vesting(Word):
    """An office takes the powers named in the phrase.

    A vested right of property is not this phrase. The verb is
    ``vested in`` or ``vested with``.
    """

    forms = ('vested with', 'vested in', 'succeed to')
    reading = 'The named office takes the duties, powers, and jurisdiction.'


class Enactment(Word):
    """The words that open a statute or an ordinance."""

    forms = ('do enact as follows', 'do ordain as follows', 'does ordain as follows')
    reading = 'The enacting clause. A city or district ordinance ordains. A statute enacts.'


class Noun:
    """A kind of office. Hunters enumerate these instead of repeating the titles.

    ``rules`` is the parses worth running for this class. ``of`` keeps the
    words after of. ``tail`` takes the words in front of the title. ``number``
    and ``this`` mark a unit of a code. An empty ``rules`` means the class is
    listed and not parsed. ``examples`` are citations that show a rule.
    """

    forms = ()
    reading = ''
    rules = ()
    examples = ()


class Department(Noun):
    forms = ('Department',)
    reading = 'An executive department.'
    rules = ('of',)
    examples = (('BPC', '10050', 'office', 'Department of Real Estate'),)


class OfficeNoun(Noun):
    forms = ('Office',)
    reading = 'An office created in a department or in an agency.'
    rules = ('of',)
    examples = (('HSC', '13100', 'office', 'Office of the State Fire Marshal'),)


class Commission(Noun):
    forms = ('Commission',)
    reading = 'A commission.'
    rules = ('tail',)
    examples = (('PRC', '30300', 'office', 'California Coastal Commission'),)


class Board(Noun):
    forms = ('Board',)
    reading = 'A board.'
    rules = ('of', 'tail')
    examples = (('GOV', '15700', 'office', 'Franchise Tax Board'),)


class AgencyNoun(Noun):
    forms = ('Agency',)
    reading = 'An agency. The cabinet agencies sit in state government.'
    rules = ('tail',)
    examples = (('PRC', '30300', 'office', 'Resources Agency'),)


class Bureau(Noun):
    forms = ('Bureau',)
    reading = 'A bureau.'
    rules = ('of',)


class DivisionNoun(Noun):
    """The office, as in Division of Labor Standards Enforcement.

    The unit of a code is ``Division``, the word class. This is the office.
    """

    forms = ('Division',)
    reading = 'A division of a department.'
    rules = ('of', 'number', 'this')
    examples = (
        ('LAB', '79', 'office', 'Division of Labor Standards Enforcement'),
        ('EVID', '910', 'unit', 'this division'),
        ('LAB', '124', 'unit', 'Division 4'),
    )


class Council(Noun):
    forms = ('Council',)
    reading = 'A council.'
    rules = ('tail',)
    examples = (('GOV', '12903', 'office', 'Fair Employment and Housing Council'),)


class Authority(Noun):
    forms = ('Authority',)
    reading = 'An authority.'
    rules = ('tail',)


class Conservancy(Noun):
    forms = ('Conservancy',)
    reading = 'A conservancy.'
    rules = ('tail',)


class District(Noun):
    forms = ('District',)
    reading = 'A district.'


class Committee(Noun):
    forms = ('Committee',)
    reading = 'A committee.'


class Panel(Noun):
    forms = ('Panel',)
    reading = 'A panel.'


class Administration(Noun):
    forms = ('Administration',)
    reading = 'An administration.'


class Secretary(Noun):
    forms = ('Secretary',)
    reading = 'A secretary of an agency or of state.'
    rules = ('of',)
    examples = (('PRC', '10223', 'office', 'Secretary of the Resources Agency'),)


class Director(Noun):
    forms = ('Director',)
    reading = 'A director of a department.'
    rules = ('of',)


class Commissioner(Noun):
    forms = ('Commissioner',)
    reading = 'A commissioner. The name usually sits in front of the title.'
    rules = ('tail',)
    examples = (('BPC', '10050', 'office', 'Real Estate Commissioner'),)


class University(Noun):
    forms = ('University',)
    reading = 'A university.'


class College(Noun):
    forms = ('College',)
    reading = 'A college.'


class Definition(Word):
    """means is exclusive. includes is not."""

    forms = ('means', 'includes')
    reading = 'Means is only the words that follow. Includes does not close the list.'


def _walk(cls):
    found = []
    for sub in cls.__subclasses__():
        found.append(sub)
        found.extend(_walk(sub))
    return found


def registered():
    """Every word class that declares a form or a cut."""
    return tuple(cls for cls in _walk(Word) if cls.forms or cls.cuts)


class Outline:
    """How one book divides, from the outside in.

    A code article sits under a chapter. It is not part of the section number.
    A constitution article identifies the section, because the same number
    is used in more than one article. A chapter of the Statutes of a year
    is a session law, not this chapter.
    """

    order = ('title', 'division', 'part', 'chapter', 'article', 'section')
    mark = 'subdivision'

    def identifies(self, unit):
        """True when the unit belongs in the citation, not only in the heading."""
        return False


class ConstitutionOutline(Outline):
    """California Constitution. The article is the heading, then the section.

    Articles are this book's organization above the section. They do not
    choose the breakdown inside a section, and this book does not get one
    of its own.
    """

    order = ('article', 'section')
    code = 'CONS'

    def identifies(self, unit):
        return unit == 'article'


class _SessionYear:
    """The year of chaptering, waiting for its chapter."""

    def __init__(self, year):
        self.year = str(year)

    def chapter(self, number):
        return Session(self.year, number)


class Occasion(enum.Enum):
    """When a session credit takes effect. The value is the history word.

    It sits against a calendar day. ``Effective January 1, 2012`` is not the
    chaptering year printed in ``Stats. 2011``.
    """

    EFFECTIVE = 'effective'
    OPERATIVE = 'operative'
    INOPERATIVE = 'inoperative'
    APPROVED = 'approved'
    APPLICABLE = 'applicable'
    SUPERSEDED = 'superseded'
    REPEALED = 'repealed'


class Action(enum.Enum):
    """What a session law did to the section. The value is the history word."""

    ADDED = 'added'
    AMENDED = 'amended'
    ENACTED = 'enacted'
    REPEALED = 'repealed'
    REPEALED_AND_ADDED = 'repealed and added'
    REPEALED_CONDITIONALLY = 'repealed conditionally'


class Shelf(enum.Enum):
    """Where a hyphenated book sits. The value is the shelf.

    ``101-336`` on the public-law shelf is one law. The same hyphen in a
    heading is a range of sections.
    """

    PUBLIC_LAW = 'public-law'
    CODE = 'code'
    STATUTES = 'statutes'


class PublicLaw:
    """A federal public law. The first number is the Congress. The second is the law.

    ``P.L. 101-336`` is Public Law 101-336, the 336th public law of the 101st
    Congress. It is not a California session chapter and not a code section.
    """

    def __init__(self, congress, number):
        self.congress = str(congress)
        self.number = str(number)
        self.shelf = Shelf.PUBLIC_LAW

    def book(self):
        """Congress and law, joined by the hyphen the slip prints."""
        return '%s-%s' % (self.congress, self.number)

    def reference(self):
        return 'Public Law %s-%s' % (self.congress, self.number)

    def target(self):
        return 'PL %s %s' % (self.congress, self.number)


class FederalCode:
    """A section of the United States Code. The title, then the section.

    ``42 U.S.C. 12101`` is Title 42, section 12101, as classified. It is not
    the public law that enacted the text.
    """

    def __init__(self, title, section):
        self.title = str(title)
        self.section = str(section)
        self.shelf = Shelf.CODE

    def book(self):
        """The title is the book. The section is a place in that book."""
        return self.title

    def reference(self):
        return '%s U.S.C. %s' % (self.title, self.section)

    def target(self):
        return 'USC %s %s' % (self.title, self.section)


class StatutesAtLarge:
    """A page of the Statutes at Large. The volume, then the page.

    ``104 Stat. 327`` is volume 104, page 327. For a title that is not
    positive law, that volume is the legal evidence of the enacted text.
    """

    def __init__(self, volume, page):
        self.volume = str(volume)
        self.page = str(page)
        self.shelf = Shelf.STATUTES

    def book(self):
        """The volume is the book. The page is a place in that volume."""
        return self.volume

    def reference(self):
        return '%s Stat. %s' % (self.volume, self.page)

    def target(self):
        return 'STAT %s %s' % (self.volume, self.page)


class Session:
    """Chapter of the Statutes of a year. The chapter is not a code chapter.

    ``year`` is the calendar year of chaptering. ``chapter`` is the session
    law. ``act`` is the enrolled bill's own section, when the cite names one.
    """

    order = ('year', 'chapter')

    def __init__(self, year, chapter, act=None):
        self.year = str(year)
        self.chapter = str(chapter)
        self.act = None if act is None else str(act)

    @staticmethod
    def year(year):
        return _SessionYear(year)

    def section(self, number):
        """The enrolled bill's own section, not a section of a code."""
        return Session(self.year, self.chapter, number)

    def reference(self):
        text = 'Chapter %s of the Statutes of %s' % (self.chapter, self.year)
        if self.act:
            text = 'Section %s of %s' % (self.act, text)
        return text

    def target(self):
        """Year, then chapter. The act section is not part of the identity."""
        return '%s %s' % (self.year, self.chapter)


def outline(code=None):
    """The division model for this book. Any other code uses the code outline."""
    token = getattr(code, 'value', code)
    for cls in Outline.__subclasses__():
        if getattr(cls, 'code', None) == token:
            return cls()
    return Outline()


def consider(code=None, shelf=None):
    """Classes that apply here. A subclass stands in for its base."""
    chosen = [cls for cls in registered() if cls.applies(code, shelf)]
    shadowed = set()
    for cls in chosen:
        for base in cls.__mro__[1:]:
            if base in chosen:
                shadowed.add(base)
    return tuple(cls for cls in chosen if cls not in shadowed)


def forms(code=None, shelf=None, internal=None):
    """Surface words for the classes that apply. Longer words come first."""
    words = []
    for cls in consider(code, shelf):
        if internal is True and not cls.internal:
            continue
        if internal is False and cls.internal:
            continue
        words.extend(cls.forms)
    return tuple(sorted(set(words), key=len, reverse=True))


def pattern(code=None, shelf=None, internal=None, prefix='', suffix=''):
    """One expression for the words ``consider`` would return."""
    words = forms(code, shelf, internal=internal)
    if not words:
        return re.compile(r'(?!)')
    body = '|'.join(re.escape(word) for word in words)
    return re.compile('(?i)%s(?:%s)%s' % (prefix, body, suffix))


_COMPILED = {}


def _compiled(code, shelf):
    key = (getattr(code, 'value', code), shelf)
    cached = _COMPILED.get(key)
    if cached is not None:
        return cached
    pairs = []
    for cls in consider(code, shelf):
        for form in tuple(cls.forms) + tuple(cls.cuts):
            pairs.append((cls.__name__, form, re.compile(r'(?i)\b%s\b' % re.escape(form))))
    pairs.sort(key=lambda item: len(item[1]), reverse=True)
    _COMPILED[key] = tuple(pairs)
    return _COMPILED[key]


def occurrences(text, code=None, shelf=None):
    """Needle hits that apply to this code and shelf.

    A class whose ``codes`` or ``shelf`` does not match is not searched.
    A longer form covers the span, so ``vested with`` is not also ``with``.
    """
    if not text:
        return []
    found = []
    spans = []
    for name, form, pattern in _compiled(code, shelf):
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            spans.append((match.start(), match.end()))
            found.append({
                'class': name,
                'form': form,
                'start': match.start(),
                'end': match.end(),
            })
    found.sort(key=lambda row: (row['start'], row['end']))
    return found


def nouns():
    """Office titles. A hunter builds its pattern from this, not from its own list."""
    return tuple(cls for cls in _walk(Noun) if cls.forms)


def tails():
    """Titles that often close a name. Franchise Tax Board is one."""
    words = sorted(
        {form for cls in nouns() if 'tail' in cls.rules for form in cls.forms},
        key=len, reverse=True,
    )
    return tuple(words)


def noun_pattern():
    """Department|Office|Commission and the rest, longer titles first."""
    words = sorted({form for cls in nouns() for form in cls.forms}, key=len, reverse=True)
    if not words:
        return ''
    return '|'.join(re.escape(word) for word in words)


def breakdown(code=None):
    """The units inside a section for this book. Any other book uses the general set."""
    for cls in consider(code):
        named = getattr(cls, 'breakdown', None)
        if named is not None:
            return named()
    return General()


def cuts(code=None, shelf=None):
    """Label words such as subdivision and subsection. The parser keeps every cut."""
    words = []
    for cls in consider(code, shelf):
        words.extend(cls.cuts)
    return tuple(sorted(set(words), key=len, reverse=True))
