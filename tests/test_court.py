from court import (
    Bench,
    CaliforniaCourtOfAppeal,
    CaliforniaSupremeCourt,
    CaliforniaThirdAppellateDistrict,
    Division,
    SacramentoSuperiorCourt,
    courts,
)


def test_bench_values_are_strings():
    assert Bench.SUPREME.value == 'supreme'
    assert Bench.TRIAL.value == 'trial'
    assert Division.TRAFFIC.value == 'traffic'


def test_california_courts_stack_under_the_state():
    assert CaliforniaSupremeCourt.parent == 'US-CA'
    assert CaliforniaCourtOfAppeal.parent is CaliforniaSupremeCourt
    assert CaliforniaThirdAppellateDistrict.parent is CaliforniaCourtOfAppeal
    assert SacramentoSuperiorCourt.parent is CaliforniaThirdAppellateDistrict
    assert SacramentoSuperiorCourt.government() == 'US-CA'
    assert SacramentoSuperiorCourt.bench is Bench.TRIAL
    assert courts('US-CA', Bench.TRIAL) == [SacramentoSuperiorCourt]
    assert CaliforniaSupremeCourt in courts('US-CA', Bench.SUPREME)
    assert CaliforniaThirdAppellateDistrict in courts('US-CA', Bench.APPELLATE)


def test_sacramento_hears_the_trial_dockets():
    assert SacramentoSuperiorCourt.hears(Division.CIVIL)
    assert SacramentoSuperiorCourt.hears(Division.CRIMINAL)
    assert SacramentoSuperiorCourt.hears(Division.TRAFFIC)
    assert not CaliforniaSupremeCourt.hears(Division.TRAFFIC)
    assert SacramentoSuperiorCourt.authority == 'California Constitution article VI, section 4'
    assert SacramentoSuperiorCourt.editions == ()
    local = SacramentoSuperiorCourt.rules[-1]
    assert local.shape == 'pdf'
    assert local.url == 'https://saccourt.ca.gov/local-rules/local-rules.aspx'
    assert SacramentoSuperiorCourt.rules[0].shape == 'html'
    assert SacramentoSuperiorCourt.rules[0].instrument.value == 'rule'


def test_federal_courts_stack_under_the_united_states():
    from court import (
        SupremeCourtOfTheUnitedStates,
        UnitedStatesCourtOfAppealsForTheFederalCircuit,
        UnitedStatesCourtOfFederalClaims,
        UnitedStatesCourtsOfAppeals,
        UnitedStatesDistrictCourts,
        UnitedStatesTaxCourt,
    )
    assert SupremeCourtOfTheUnitedStates.government() == 'US'
    assert UnitedStatesCourtsOfAppeals.parent is SupremeCourtOfTheUnitedStates
    assert UnitedStatesDistrictCourts.parent is UnitedStatesCourtsOfAppeals
    assert UnitedStatesDistrictCourts.bench is Bench.TRIAL
    assert UnitedStatesCourtOfFederalClaims.parent is UnitedStatesCourtOfAppealsForTheFederalCircuit
    assert UnitedStatesCourtOfFederalClaims.government() == 'US'
    assert UnitedStatesTaxCourt.bench is Bench.ARTICLE_I
    assert UnitedStatesTaxCourt.government() == 'US'
    assert courts('US', Bench.SUPREME) == [SupremeCourtOfTheUnitedStates]
