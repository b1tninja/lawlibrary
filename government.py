"""A constitution is the root. A branch hangs from one article.

The citation is a pointer. The words stay in the constitution's own
edition. California article VI is already the authority on the state
courts. These classes name the United States articles that create the
three branches.
"""

import enum


class Article(enum.Enum):
    """One article. The value is the roman numeral as printed."""

    I = 'I'
    II = 'II'
    III = 'III'
    IV = 'IV'
    V = 'V'
    VI = 'VI'


class ArticleMark:
    """A constitution article printed beyond the branch articles, such as XIII A."""

    def __init__(self, label):
        self.value = ' '.join(str(label).upper().split())


class Branch(enum.Enum):
    """A power the constitution names. The value is the string."""

    LEGISLATIVE = 'legislative'
    EXECUTIVE = 'executive'
    JUDICIAL = 'judicial'


class Provision:
    """One article and section. ``citation`` is the pointer, not the text."""

    def __init__(self, article, section):
        if not isinstance(article, Article):
            raise TypeError('article must be an Article')
        self.article = article
        self.section = str(section)

    def citation(self, charter):
        return '%s article %s, section %s' % (charter.short, self.article.value, self.section)


class Charter:
    """A constitution. Courts and organs hang from this, not from a bare code."""

    code = None
    name = None
    short = None
    source = None


class UnitedStatesConstitution(Charter):
    code = 'US'
    name = 'Constitution of the United States'
    short = 'United States Constitution'
    source = 'https://constitution.congress.gov/'


class CaliforniaConstitution(Charter):
    code = 'US-CA'
    name = 'Constitution of the State of California'
    short = 'California Constitution'
    source = 'https://leginfo.legislature.ca.gov/faces/codes.xhtml'


_organs = []


class Organ:
    """A branch the constitution creates. ``authority`` is the vesting section."""

    branch = None
    charter = None
    authority = None
    name = None
    source = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'name' not in cls.__dict__:
            return
        if not isinstance(cls.branch, Branch):
            raise TypeError('%s must set a Branch' % cls.__name__)
        if not isinstance(cls.charter, type) or not issubclass(cls.charter, Charter):
            raise TypeError('%s must set a Charter' % cls.__name__)
        if not isinstance(cls.authority, Provision):
            raise TypeError('%s authority must be a Provision' % cls.__name__)
        _organs.append(cls)

    @classmethod
    def citation(cls):
        return cls.authority.citation(cls.charter)


def organs(charter=None, branch=None):
    found = list(_organs)
    if charter is not None:
        found = [item for item in found if item.charter is charter]
    if branch is not None:
        found = [item for item in found if item.branch is branch]
    return found


class Congress(Organ):
    branch = Branch.LEGISLATIVE
    charter = UnitedStatesConstitution
    authority = Provision(Article.I, '1')
    name = 'Congress'
    source = 'https://www.congress.gov/'


class PresidentOfTheUnitedStates(Organ):
    branch = Branch.EXECUTIVE
    charter = UnitedStatesConstitution
    authority = Provision(Article.II, '1')
    name = 'President of the United States'
    source = 'https://www.whitehouse.gov/'


class FederalJudicialPower(Organ):
    branch = Branch.JUDICIAL
    charter = UnitedStatesConstitution
    authority = Provision(Article.III, '1')
    name = 'Supreme Court and inferior courts'
    source = 'https://www.supremecourt.gov/'
