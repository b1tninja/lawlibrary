"""A parser is a stack of mixins. Each mixin is one lexical decision.

``CanonMixin`` weighs the canons and reports both readings when they
disagree. ``StyleMixin`` is the style manual a court rule names. The
manual's text is not copied here.
"""

import enum

from canons import ambiguities, find_signals
from citations import annotate
from needles import consider


class Guide(enum.Enum):
    """A style manual a rule names. The value is the string.

    ``BLUEBOOK`` is named by a court rule. It is not a government
    publication, so it is not indexed.
    """

    CALIFORNIA_STYLE_MANUAL = 'california_style_manual'
    BLUEBOOK = 'bluebook'
    GPO = 'gpo'
    OLRC = 'olrc'
    HOLC = 'holc'
    APA = 'apa'
    INDIGO = 'indigo'
    ALWD = 'alwd'
    UNIVERSAL = 'universal'
    CHICAGO = 'chicago'


class Reading:
    """What one pass of the parser found. Signals and notes stay records."""

    def __init__(self, signals, conflicts, notes, guides):
        self.signals = tuple(signals)
        self.conflicts = tuple(conflicts)
        self.notes = tuple(notes)
        self.guides = tuple(guides)


class NeedleMixin:
    """The word classes that apply to this reading. A book may add its own."""

    code = None
    shelf = None

    def words(self):
        return consider(self.code, self.shelf)


class CanonMixin:
    """The canons of construction. A disagreement stays two readings."""

    def canons(self, text):
        return find_signals(text)

    def conflicts(self, text):
        return ambiguities(text)


class StyleMixin:
    """The style manuals that apply to this reading. ``guides`` is a closed set."""

    guides = ()

    def notes(self, text, context=None):
        return annotate(text, context=context)


class ShelfMixin:
    """A hyphenated book on a federal shelf. It is not a section range.

    ``101-336`` is Congress 101, law 336, on the public-law shelf. A heading
    bracket ``[38. - 86.]`` stays a range. ``42 U.S.C. 12101`` is section
    12101 of Title 42, and ``104 Stat. 327`` is page 327 of volume 104.
    """

    def books(self, text):
        return self.public_laws(text) + self.federal_codes(text) + self.statutes(text)

    def public_laws(self, text):
        from citations import find_public_laws
        return find_public_laws(text)

    def federal_codes(self, text):
        from citations import find_federal_codes
        return find_federal_codes(text)

    def statutes(self, text):
        from citations import find_statutes
        return find_statutes(text)

    def named_acts(self, text):
        from citations import find_named_acts
        return find_named_acts(text)


class RomanMixin:
    """A constitution article. Single quotes mark the numeral.

    ``'XIX'`` is article 19. ``'XIII A'`` and ``Article XIX C`` keep the
    letter that follows the numeral. An unquoted ``I`` stays a word.
    """

    def articles(self, text):
        from citations import find_articles
        return find_articles(text)


class FormatMixin:
    """Date, number, and currency conventions on a measured span.

    A dollar is USD. A thousands comma is grouped. A radix point is decimal.
    A printed month is ``month_day_year``. ``YYYY-MM-DD`` is ISO 8601.
    ``M/D/YYYY`` is a numeric month-day-year. A period unit is a designator.
    """

    def formats(self, text):
        from citations import forms
        return forms(text)


class Parser(NeedleMixin, CanonMixin, StyleMixin, FormatMixin, ShelfMixin, RomanMixin):
    """Canons and a style guide, applied to one text."""

    def read(self, text, context=None):
        return Reading(
            self.canons(text),
            self.conflicts(text),
            self.notes(text, context),
            self.guides,
        )


class CaliforniaFiling(Parser):
    """Documents filed in a California court. Rule 1.200 names both guides."""

    guides = (Guide.CALIFORNIA_STYLE_MANUAL, Guide.BLUEBOOK)


class PublicUtilities(Parser):
    """Public Utilities Code. Section and subdivision have the meaning in section 10."""

    def words(self):
        from apa import Code
        return consider(Code.PUBLIC_UTILITIES, self.shelf)


class JointRules(Parser):
    """The Joint Rules. Bill has the meaning in Joint Rule 4."""

    shelf = 'joint-rules'
