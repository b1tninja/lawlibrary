from agency import (
    Agriculture,
    Function,
    GeorgiaInsuranceAndFire,
    agencies,
    CaliforniaDepartmentOfRealEstate,
    FloridaDepartmentOfAgriculture,
    IdahoDepartmentOfAgriculture,
)


def test_function_values_are_the_shared_strings():
    assert Function.AGRICULTURE.value == 'agriculture'
    assert Function.REAL_ESTATE.value == 'real_estate'
    assert Function['AGRICULTURE'] is Function.AGRICULTURE


def test_different_titles_share_one_function():
    assert FloridaDepartmentOfAgriculture.functions == (Function.AGRICULTURE,)
    assert IdahoDepartmentOfAgriculture.functions == (Function.AGRICULTURE,)
    assert FloridaDepartmentOfAgriculture.covers(Function.AGRICULTURE)
    assert FloridaDepartmentOfAgriculture.name != IdahoDepartmentOfAgriculture.name
    assert agencies('US-FL', Function.AGRICULTURE) == [FloridaDepartmentOfAgriculture]
    assert agencies(function=Function.AGRICULTURE)
    assert CaliforniaDepartmentOfRealEstate in agencies('US-CA', Function.REAL_ESTATE)
    assert CaliforniaDepartmentOfRealEstate.name == 'Real Estate, Department of (DRE)'


def test_one_office_can_carry_two_functions():
    assert GeorgiaInsuranceAndFire.functions == (Function.INSURANCE, Function.FIRE)
    assert GeorgiaInsuranceAndFire.covers(Function.INSURANCE)
    assert GeorgiaInsuranceAndFire.covers(Function.FIRE)
    assert not GeorgiaInsuranceAndFire.covers(Function.HEALTH)
    assert GeorgiaInsuranceAndFire in agencies('US-GA', Function.FIRE)
    assert GeorgiaInsuranceAndFire in agencies('US-GA', Function.INSURANCE)
    assert agencies('US-GA', Function.FIRE) == [GeorgiaInsuranceAndFire]
    from agency import KansasHealthAndEnvironment
    assert KansasHealthAndEnvironment in agencies(function=Function.HEALTH)
    assert KansasHealthAndEnvironment in agencies(function=Function.ENVIRONMENT)
    assert GeorgiaInsuranceAndFire.editions == ()
    assert issubclass(FloridaDepartmentOfAgriculture, Agriculture)
