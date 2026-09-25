"""Courts nested under a government or under the court that reviews them.

``Bench`` is the level. ``Division`` is a docket a trial court hears. A
printed name stays the name that court publishes. Two superior courts share
``Bench.TRIAL`` and remain different classes.
"""

import enum

from government import Article, CaliforniaConstitution, UnitedStatesConstitution
from jurisdiction import country, subdivision
from parsers import Guide
from publication import Instrument


class Bench(enum.Enum):
    """A level in a judicial hierarchy. The value is the string."""

    SUPREME = 'supreme'
    APPELLATE = 'appellate'
    TRIAL = 'trial'
    ARTICLE_I = 'article_i'


class Division(enum.Enum):
    """A docket. The value is the string."""

    CIVIL = 'civil'
    CRIMINAL = 'criminal'
    TRAFFIC = 'traffic'
    FAMILY = 'family'
    PROBATE = 'probate'
    JUVENILE = 'juvenile'
    MENTAL_HEALTH = 'mental_health'
    APPELLATE = 'appellate'


_registered = []


def _check_parent(parent):
    if isinstance(parent, str):
        if '-' in parent:
            subdivision(parent)
        else:
            country(parent)
        return
    if isinstance(parent, type) and issubclass(parent, Court):
        return
    raise TypeError('court parent must be a country, a region code, or a Court')


class Rulebook:
    """Where a court publishes its rules. ``shape`` is html or pdf.

    The words are not downloaded here. A PDF stays a pointer until a plain
    text or HTML edition exists.
    """

    instrument = Instrument.RULE

    def __init__(self, title, url, shape, guides=()):
        self.title = title
        self.url = url
        self.shape = shape
        self.guides = tuple(guides)
        if any(not isinstance(guide, Guide) for guide in self.guides):
            raise TypeError('guides must be Guide members')


_CALIFORNIA_RULES = Rulebook(
    'California Rules of Court',
    'https://www.courts.ca.gov/forms-rules/rules-court',
    'html',
    (Guide.CALIFORNIA_STYLE_MANUAL, Guide.BLUEBOOK),
)
_FEDERAL_RULES = Rulebook(
    'Federal Rules of Practice and Procedure',
    'https://www.uscourts.gov/rules-policies/current-rules-practice-procedure',
    'html',
)


class Court:
    """One court. ``parent`` is the government, or the court that reviews it.

    ``authority`` is the citation that creates the court or states its
    jurisdiction. It is a pointer into the index, not a quotation.
    ``editions`` stays empty until an official file of opinions or rules
    yields the words.
    """

    bench = None
    parent = None
    name = None
    source = None
    authority = None
    divisions = ()
    editions = ()
    rules = ()
    charter = None
    article = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'name' not in cls.__dict__ or 'parent' not in cls.__dict__:
            return
        if not isinstance(cls.bench, Bench):
            raise TypeError('%s must set a Bench' % cls.__name__)
        roles = tuple(cls.divisions)
        if any(not isinstance(role, Division) for role in roles):
            raise TypeError('%s divisions must be Division members' % cls.__name__)
        if len(roles) != len(set(roles)):
            raise TypeError('%s repeats a division' % cls.__name__)
        _check_parent(cls.parent)
        _registered.append(cls)

    @classmethod
    def hears(cls, division):
        """True when this court publishes that docket."""
        return division in cls.divisions

    @classmethod
    def government(cls):
        """The country or region code at the top of this court's parents."""
        current = cls
        while isinstance(current, type) and issubclass(current, Court):
            parent = current.parent
            if isinstance(parent, str):
                return parent
            current = parent
        raise TypeError('%s has no government parent' % cls.__name__)

    @classmethod
    def constitution(cls):
        """The charter at the top of this court, when one has been set."""
        current = cls
        while isinstance(current, type) and issubclass(current, Court):
            if current.charter is not None:
                return current.charter
            parent = current.parent
            if not isinstance(parent, type):
                return None
            current = parent
        return None

    @classmethod
    def guides(cls):
        """Style manuals named by this court's rules."""
        found = []
        for book in cls.rules:
            for guide in book.guides:
                if guide not in found:
                    found.append(guide)
        return tuple(found)


def courts(parent=None, bench=None):
    """Registered courts. Filter by government code and by bench."""
    found = list(_registered)
    if parent is not None:
        found = [court for court in found if court.government() == parent]
    if bench is not None:
        found = [court for court in found if court.bench is bench]
    return found


class CaliforniaSupremeCourt(Court):
    bench = Bench.SUPREME
    parent = 'US-CA'
    name = 'Supreme Court of California'
    source = 'https://supreme.courts.ca.gov/'
    authority = 'California Constitution article VI, section 1'
    charter = CaliforniaConstitution
    article = Article.VI
    rules = (_CALIFORNIA_RULES,)


class CaliforniaCourtOfAppeal(Court):
    bench = Bench.APPELLATE
    parent = CaliforniaSupremeCourt
    name = 'California Courts of Appeal'
    source = 'https://courts.ca.gov/courts'
    authority = 'California Constitution article VI, section 3'
    rules = (_CALIFORNIA_RULES,)


_SUPERIOR_DIVISIONS = (
    Division.CIVIL,
    Division.CRIMINAL,
    Division.TRAFFIC,
    Division.FAMILY,
    Division.PROBATE,
    Division.JUVENILE,
    Division.MENTAL_HEALTH,
    Division.APPELLATE,
)


class CaliforniaThirdAppellateDistrict(Court):
    bench = Bench.APPELLATE
    parent = CaliforniaCourtOfAppeal
    name = 'Third Appellate District'
    source = 'https://appellate.courts.ca.gov/district-courts/3dca/about'
    authority = 'California Constitution article VI, section 3'
    rules = (_CALIFORNIA_RULES,)


class SupremeCourtOfTheUnitedStates(Court):
    bench = Bench.SUPREME
    parent = 'US'
    name = 'Supreme Court of the United States'
    source = 'https://www.supremecourt.gov/'
    authority = 'United States Constitution article III, section 1; 28 U.S.C. section 1'
    charter = UnitedStatesConstitution
    article = Article.III
    rules = (Rulebook(
        'Rules of the Supreme Court of the United States',
        'https://www.supremecourt.gov/filingandrules/rules_guidance.aspx',
        'html',
    ),)


class UnitedStatesCourtsOfAppeals(Court):
    bench = Bench.APPELLATE
    parent = SupremeCourtOfTheUnitedStates
    name = 'United States courts of appeals'
    source = 'https://www.uscourts.gov/about-federal-courts/court-role-and-structure/about-us-courts-appeals'
    authority = '28 U.S.C. sections 41 and 43'
    rules = (_FEDERAL_RULES,)


class UnitedStatesCourtOfAppealsForTheFederalCircuit(Court):
    bench = Bench.APPELLATE
    parent = SupremeCourtOfTheUnitedStates
    name = 'United States Court of Appeals for the Federal Circuit'
    source = 'https://www.uscourts.gov/about-federal-courts/court-role-and-structure/about-us-courts-appeals'
    authority = '28 U.S.C. sections 41 and 1295'
    rules = (Rulebook(
        'Federal Circuit Rules of Practice',
        'https://www.cafc.uscourts.gov/home/rules-procedures-forms/rules-of-practice-amendments/rules-of-practice-amendments-2025/',
        'pdf',
    ),)


class UnitedStatesDistrictCourts(Court):
    bench = Bench.TRIAL
    parent = UnitedStatesCourtsOfAppeals
    name = 'United States district courts'
    source = 'https://www.uscourts.gov/about-federal-courts/court-role-and-structure/about-us-district-courts'
    authority = '28 U.S.C. section 132'
    rules = (_FEDERAL_RULES,)


class UnitedStatesTaxCourt(Court):
    bench = Bench.ARTICLE_I
    parent = 'US'
    name = 'United States Tax Court'
    source = 'https://www.ustaxcourt.gov/'
    authority = '26 U.S.C. section 7441'
    rules = (Rulebook(
        'Tax Court Rules of Practice and Procedure',
        'https://ustaxcourt.gov/rules',
        'html',
    ),)


class UnitedStatesCourtOfFederalClaims(Court):
    bench = Bench.ARTICLE_I
    parent = UnitedStatesCourtOfAppealsForTheFederalCircuit
    name = 'United States Court of Federal Claims'
    source = 'https://www.cfc.uscourts.gov/court-info'
    authority = '28 U.S.C. section 171'
    rules = (Rulebook(
        'Rules of the United States Court of Federal Claims',
        'https://www.cfc.uscourts.gov/sites/cfc/files/Rules%207.27.2026.pdf',
        'pdf',
    ),)


class SacramentoSuperiorCourt(Court):
    bench = Bench.TRIAL
    parent = CaliforniaThirdAppellateDistrict
    name = 'Superior Court of California, County of Sacramento'
    source = 'https://saccourt.ca.gov/'
    authority = 'California Constitution article VI, section 4'
    divisions = _SUPERIOR_DIVISIONS
    rules = (
        _CALIFORNIA_RULES,
        Rulebook(
            'Local Rules of the Superior Court of California, County of Sacramento',
            'https://saccourt.ca.gov/local-rules/local-rules.aspx',
            'pdf',
        ),
    )
