"""Political agencies nested under a country or a region.

The printed name stays the name on that state's directory. ``Function`` is
the shared role. Two offices with different titles register under the same
function and remain different classes. A function class is where that
office's code edition is attached.
"""

import enum

from jurisdiction import country, subdivision
from publication import Instrument


class Function(enum.Enum):
    """A role many states staff under different titles. The value is the string."""

    AGRICULTURE = 'agriculture'
    INSURANCE = 'insurance'
    REAL_ESTATE = 'real_estate'
    HOUSING = 'housing'
    FIRE = 'fire'
    ENVIRONMENT = 'environment'
    LABOR = 'labor'
    REVENUE = 'revenue'
    TRANSPORTATION = 'transportation'
    HEALTH = 'health'


_registered = []


def _check_parent(parent):
    if isinstance(parent, str):
        if '-' in parent:
            subdivision(parent)
        else:
            country(parent)
        return
    if isinstance(parent, type) and issubclass(parent, Agency):
        return
    raise TypeError('agency parent must be a country, a region code, or an Agency')


class Agency:
    """One office. ``parent`` is the government it sits in. ``name`` is printed.

    ``functions`` is every shared role that office carries. One printed body
    may hold several. ``editions`` is the registration point for that office's
    code, one publication for the whole office. It stays empty until an
    official file yields the words.
    """

    functions = ()
    parent = None
    name = None
    source = None
    authority = None
    editions = ()
    instrument = Instrument.REGULATION

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if 'name' not in cls.__dict__ or 'parent' not in cls.__dict__:
            return
        roles = tuple(cls.functions)
        if not roles or any(not isinstance(role, Function) for role in roles):
            raise TypeError('%s must name one or more Functions' % cls.__name__)
        if len(roles) != len(set(roles)):
            raise TypeError('%s repeats a function' % cls.__name__)
        _check_parent(cls.parent)
        _registered.append(cls)

    @classmethod
    def covers(cls, function):
        """True when this office carries that role, alone or with others."""
        return function in cls.functions


def agencies(parent=None, function=None):
    """Registered offices. Filter by region code and by shared function."""
    found = list(_registered)
    if parent is not None:
        found = [cls for cls in found if cls.parent == parent]
    if function is not None:
        found = [cls for cls in found if cls.covers(function)]
    return found


class Agriculture(Agency):
    """Offices whose printed duty is agriculture, whether or not they also do more."""

    functions = (Function.AGRICULTURE,)


class Insurance(Agency):
    functions = (Function.INSURANCE,)


class RealEstate(Agency):
    functions = (Function.REAL_ESTATE,)


class Housing(Agency):
    functions = (Function.HOUSING,)


class FireProtection(Agency):
    functions = (Function.FIRE,)


class Environment(Agency):
    functions = (Function.ENVIRONMENT,)


class Labor(Agency):
    functions = (Function.LABOR,)


class Revenue(Agency):
    functions = (Function.REVENUE,)


class Transportation(Agency):
    functions = (Function.TRANSPORTATION,)


class Health(Agency):
    functions = (Function.HEALTH,)


class CaliforniaDepartmentOfRealEstate(RealEstate):
    parent = 'US-CA'
    name = 'Real Estate, Department of (DRE)'
    source = 'https://www.dre.ca.gov/'
    authority = 'BPC 10050'


class FloridaDepartmentOfAgriculture(Agriculture):
    parent = 'US-FL'
    name = 'Florida Department of Agriculture & Consumer Services'
    source = 'https://flgov.com/eog/info/agencies'


class IdahoDepartmentOfAgriculture(Agriculture):
    parent = 'US-ID'
    name = 'Department of Agriculture'
    source = 'https://idaho.gov/government/executive-branch/'


class GeorgiaInsuranceAndFire(Agency):
    """One printed office. The directory names both insurance and fire."""

    functions = (Function.INSURANCE, Function.FIRE)
    parent = 'US-GA'
    name = 'Office of Insurance and Safety Fire Commissioner'
    source = 'https://georgia.gov/state-organizations'


class KansasHealthAndEnvironment(Agency):
    """One printed office. The directory names both health and environment."""

    functions = (Function.HEALTH, Function.ENVIRONMENT)
    parent = 'US-KS'
    name = 'Department of Health & Environment'
    source = 'https://portal.kansas.gov/government/agency-list/'
