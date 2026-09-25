from government import (
    Article,
    Branch,
    CaliforniaConstitution,
    Congress,
    FederalJudicialPower,
    PresidentOfTheUnitedStates,
    UnitedStatesConstitution,
    organs,
)
from court import CaliforniaSupremeCourt, SacramentoSuperiorCourt, SupremeCourtOfTheUnitedStates
from parsers import CaliforniaFiling, Guide


VESTING = """
The commissioner shall enforce this part.
The commissioner may adopt rules.
"""


def test_the_constitution_is_the_root_of_the_three_branches():
    assert Congress.charter is UnitedStatesConstitution
    assert Congress.branch is Branch.LEGISLATIVE
    assert Congress.citation() == 'United States Constitution article I, section 1'
    assert PresidentOfTheUnitedStates.branch is Branch.EXECUTIVE
    assert PresidentOfTheUnitedStates.authority.article is Article.II
    assert FederalJudicialPower.branch is Branch.JUDICIAL
    assert FederalJudicialPower.authority.section == '1'
    assert organs(UnitedStatesConstitution) == [
        Congress,
        PresidentOfTheUnitedStates,
        FederalJudicialPower,
    ]


def test_a_court_keeps_the_charter_of_the_court_above_it():
    assert SupremeCourtOfTheUnitedStates.charter is UnitedStatesConstitution
    assert SupremeCourtOfTheUnitedStates.article is Article.III
    assert SacramentoSuperiorCourt.constitution() is CaliforniaConstitution
    assert SacramentoSuperiorCourt.article is None
    assert CaliforniaSupremeCourt.article is Article.VI
    assert SacramentoSuperiorCourt.guides() == (
        Guide.CALIFORNIA_STYLE_MANUAL,
        Guide.BLUEBOOK,
    )


def test_a_california_filing_uses_the_canon_and_style_mixins():
    reading = CaliforniaFiling().read(VESTING)
    assert any(signal.canon.value == 'mandatory' for signal in reading.signals)
    assert any(signal.canon.value == 'permissive' for signal in reading.signals)
    assert reading.conflicts == ()
    assert reading.guides == SacramentoSuperiorCourt.guides()
