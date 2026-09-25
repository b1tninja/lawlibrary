"""APA Style legal references for a known code.

``CitationSystem`` is the style in force. Enter it with ``with``. The
block may nest. The active system is a ``contextvars`` value, so it
follows the task that entered it.

The shape is the one on the APA Style site for a statute or regulation:
the name, then the source and a section sign, then the year, with no
italics. A code is a member. A span is one section, a range, or a series.
The year is the session. A missing session is left out rather than guessed.
"""

import contextvars
import enum
import re

from citations import Cite
from government import Article, ArticleMark
from parsers import Guide

_active = contextvars.ContextVar('citation_system', default=None)
_tokens = contextvars.ContextVar('citation_system_tokens', default=())


class CitationSystem(enum.Enum):
    """The style used to render a citation inside a ``with`` block.

    The value is the ``Guide``. California Style Manual and The Bluebook
    share the section-sign form already used in this library. Their full
    texts were not opened. APA uses the reference-list pattern.
    """

    CaliforniaStyleManual = Guide.CALIFORNIA_STYLE_MANUAL
    Bluebook = Guide.BLUEBOOK
    APA = Guide.APA
    IndigoBook = Guide.INDIGO
    ALWD = Guide.ALWD
    Universal = Guide.UNIVERSAL
    Chicago = Guide.CHICAGO

    def __enter__(self):
        token = _active.set(self.value)
        _tokens.set(_tokens.get() + (token,))
        return self

    def __exit__(self, exc_type, exc, tb):
        tokens = _tokens.get()
        token = tokens[-1]
        _tokens.set(tokens[:-1])
        _active.reset(token)
        return False


def active():
    """The ``Guide`` in force, or ``None`` outside a ``with`` block."""
    return _active.get()


class Code(enum.Enum):
    """A California code. The value is the Legislature's token.

    ``title`` is the printed name. ``shorthand`` is the source abbreviation
    in the reference. Both resolve to this member.
    """

    def __new__(cls, token, title, shorthand):
        obj = object.__new__(cls)
        obj._value_ = token
        obj.title = title
        obj.shorthand = shorthand
        return obj

    BUSINESS_AND_PROFESSIONS = ('BPC', 'Business and Professions Code', 'Bus. & Prof. Code')
    CIVIL_PROCEDURE = ('CCP', 'Code of Civil Procedure', 'Civ. Proc. Code')
    CIVIL = ('CIV', 'Civil Code', 'Civ. Code')
    COMMERCIAL = ('COM', 'Commercial Code', 'Com. Code')
    CONSTITUTION = ('CONS', 'California Constitution', 'Cal. Const.')
    CORPORATIONS = ('CORP', 'Corporations Code', 'Corp. Code')
    EDUCATION = ('EDC', 'Education Code', 'Educ. Code')
    ELECTIONS = ('ELEC', 'Elections Code', 'Elec. Code')
    EVIDENCE = ('EVID', 'Evidence Code', 'Evid. Code')
    FOOD_AND_AGRICULTURAL = ('FAC', 'Food and Agricultural Code', 'Food & Agric. Code')
    FAMILY = ('FAM', 'Family Code', 'Fam. Code')
    FISH_AND_GAME = ('FGC', 'Fish and Game Code', 'Fish & Game Code')
    FINANCIAL = ('FIN', 'Financial Code', 'Fin. Code')
    GOVERNMENT = ('GOV', 'Government Code', 'Gov. Code')
    HARBORS_AND_NAVIGATION = ('HNC', 'Harbors and Navigation Code', 'Harb. & Nav. Code')
    HEALTH_AND_SAFETY = ('HSC', 'Health and Safety Code', 'Health & Saf. Code')
    INSURANCE = ('INS', 'Insurance Code', 'Ins. Code')
    LABOR = ('LAB', 'Labor Code', 'Lab. Code')
    MILITARY_AND_VETERANS = ('MVC', 'Military and Veterans Code', 'Mil. & Vet. Code')
    PUBLIC_CONTRACT = ('PCC', 'Public Contract Code', 'Pub. Cont. Code')
    PENAL = ('PEN', 'Penal Code', 'Pen. Code')
    PUBLIC_RESOURCES = ('PRC', 'Public Resources Code', 'Pub. Res. Code')
    PROBATE = ('PROB', 'Probate Code', 'Prob. Code')
    PUBLIC_UTILITIES = ('PUC', 'Public Utilities Code', 'Pub. Util. Code')
    REVENUE_AND_TAXATION = ('RTC', 'Revenue and Taxation Code', 'Rev. & Tax. Code')
    STREETS_AND_HIGHWAYS = ('SHC', 'Streets and Highways Code', 'Sts. & Hy. Code')
    UNEMPLOYMENT_INSURANCE = ('UIC', 'Unemployment Insurance Code', 'Unemp. Ins. Code')
    VEHICLE = ('VEH', 'Vehicle Code', 'Veh. Code')
    WATER = ('WAT', 'Water Code', 'Wat. Code')
    WELFARE_AND_INSTITUTIONS = ('WIC', 'Welfare and Institutions Code', 'Welf. & Inst. Code')

    @classmethod
    def get(cls, token):
        """The member for a Legislature token such as ``BPC`` or ``CIV``."""
        key = str(token or '').strip().upper()
        for code in cls:
            if code.value == key:
                return code
        raise KeyError(key)


class Span:
    """How many sections, and which numbers. ``cite`` is ``Cite``."""

    def __init__(self, cite, numbers, subdivision=None):
        if not isinstance(cite, Cite):
            raise TypeError('cite must be a Cite')
        self.cite = cite
        self.numbers = tuple(str(number) for number in numbers)
        self.subdivision = subdivision
        self.open = False
        if cite is Cite.SECTION and len(self.numbers) != 1:
            raise ValueError('a section has one number')
        if cite is Cite.RANGE and len(self.numbers) != 2:
            raise ValueError('a range has a first and a last number')
        if cite is Cite.SERIES and len(self.numbers) < 2:
            raise ValueError('a series has at least two numbers')

    def text(self):
        sign = '§' if self.cite is Cite.SECTION else '§§'
        if self.cite is Cite.RANGE:
            body = '%s-%s' % self.numbers
        else:
            body = ', '.join(self.numbers)
        if self.subdivision and self.cite is Cite.SECTION:
            body = '%s(%s)' % (body, str(self.subdivision).strip('()'))
        return '%s %s' % (sign, body)


def section(number, subdivision=None):
    """One section. A subdivision is the label, such as ``d`` or ``(d)``."""
    return Span(Cite.SECTION, (number,), subdivision)


def span(start, end):
    """A range. The name is ``span`` because ``range`` is a Python builtin."""
    return Span(Cite.RANGE, (start, end))


def series(*numbers):
    """Two or more sections that are not a single range."""
    return Span(Cite.SERIES, numbers)


class Reference:
    """One citation and the two in-text forms. ``guide`` is the system in force."""

    def __init__(self, code, span, session=None, article=None, guide=None):
        if not isinstance(code, Code):
            raise TypeError('code must be a Code')
        if not isinstance(span, Span):
            raise TypeError('span must be a Span')
        if article is not None and not isinstance(article, (Article, ArticleMark)):
            raise TypeError('article must be an Article')
        self.code = code
        self.span = span
        self.session = None if session in (None, '') else str(session)
        self.article = article
        self.guide = guide if guide is not None else active() or Guide.CALIFORNIA_STYLE_MANUAL

    def index(self):
        """The key the local index uses: the token and the first number."""
        return '%s %s' % (self.code.value, self.span.numbers[0])

    def reference(self):
        """The entry for the guide in force.

        APA is the name, the source, the section sign, and the year.
        The California Style Manual and The Bluebook are the shorthand
        and the section sign.
        """
        if self.guide is Guide.CALIFORNIA_STYLE_MANUAL:
            from california import render
            return render(self)
        if self.guide is not Guide.APA:
            from styles import render as render_style
            return render_style(self)
        parts = [self.code.title + ',']
        if self.article is not None:
            parts.append('art. %s,' % self.article.value)
        parts.append(self.code.shorthand)
        parts.append(self.span.text())
        text = ' '.join(parts)
        if self.session:
            text = '%s (%s)' % (text, self.session)
        return text + '.'

    def parenthetical(self):
        """(Name, year) when the year is known."""
        if self.session:
            return '(%s, %s)' % (self.code.title, self.session)
        return '(%s)' % self.code.title

    def narrative(self):
        """Name (year) when the year is known."""
        if self.session:
            return '%s (%s)' % (self.code.title, self.session)
        return self.code.title


def _parse_apa(text):
    """Name, source, section sign, optional year."""
    from california import parse as parse_california

    raw = (text or '').strip().rstrip('.')
    session = None
    year = re.search(r'\((\d{4})\)$', raw)
    if year:
        session = year.group(1)
        raw = raw[:year.start()].strip()
    _name, _sep, rest = raw.partition(',')
    found = parse_california(rest.strip())
    return Reference(
        found.code, found.span, session=session, article=found.article, guide=Guide.APA,
    )


def parse(text):
    """Read a citation in the active system, or in the system the text itself shows."""
    from parsers import Guide
    from styles import identify

    guide = active()
    if guide is None:
        guide = identify(text).value
    if guide is Guide.CALIFORNIA_STYLE_MANUAL:
        from california import parse as parse_california
        return parse_california(text)
    if guide is Guide.APA:
        return _parse_apa(text)
    from styles_alwd import parse as parse_alwd
    from styles_bluebook import parse as parse_bluebook
    from styles_chicago import parse as parse_chicago
    from styles_indigo import parse as parse_indigo
    from styles_universal import parse as parse_universal
    chosen = {
        Guide.BLUEBOOK: parse_bluebook,
        Guide.INDIGO: parse_indigo,
        Guide.ALWD: parse_alwd,
        Guide.UNIVERSAL: parse_universal,
        Guide.CHICAGO: parse_chicago,
    }.get(guide)
    if chosen is None:
        raise ValueError(text)
    return chosen(text)


def cite(code, span, session=None, article=None):
    """Build a reference from a code member and a span.

    ``code`` is a ``Code`` member, not a token string. ``span`` is the
    result of ``section``, ``span``, or ``series``.
    """
    return Reference(code, span, session=session, article=article)
