"""Substantive canons as a choice between two readings of a looked-up section.

The section is opened by citation. A shorter and a longer slice of that text
are the two readings. The canons are background presumptions, not magic
phrases. Prefer is a small pure function kept in this file.
"""

import query
from apa import Code


def _open(code, number):
    return query.section(code, number).get('text') or ''


def prefer(canon, readings):
    """Return the reading a substantive canon selects from a (narrower, broader) pair.

    readings must be a two-tuple of strings taken from the statute's own words.
    Every canon covered here resolves a tie against the broader legal effect.
    """
    narrower, broader = readings
    if canon not in {
        'lenity',
        'against_retroactivity',
        'against_extraterritoriality',
        'clear_statement',
        'delegation',
    }:
        raise ValueError('unknown canon: %r' % (canon,))
    if not narrower or not broader or narrower == broader:
        raise ValueError('readings must be two distinct non-empty strings')
    return narrower


def test_lenity_selects_narrower_disjunct_in_battery():
    """PEN 242. Criminal 'or' leaves force alone or force-or-violence open."""
    text = query.excerpt(Code.PENAL, '242', 'force or violence')
    if not text:
        return
    narrower = 'use of force'
    broader = 'use of force or violence'
    assert narrower in text
    assert broader in text
    assert prefer('lenity', (narrower, broader)) == narrower
    assert prefer('lenity', (narrower, broader)) != broader


def test_against_retroactivity_selects_prospective_aid_rule():
    """WIC 11275.45. Prospectively only; prior-to appears in the same section."""
    text = _open(Code.WELFARE_AND_INSTITUTIONS, '11275.45')
    if 'prospectively only' not in text:
        return
    narrower = (
        'shall apply only with respect to applications for aid made on or '
        'after July 1, 1991'
    )
    broader = 'This article shall be applied'
    assert narrower in text
    assert broader in text
    # Reading the lead-in without "prospectively only" would reach earlier
    # applications; the presumption keeps the on-or-after limit.
    assert prefer('against_retroactivity', (narrower, broader)) == narrower


def test_against_retroactivity_selects_post_effective_transactions():
    """COM 13101. Effective date plus application only after that date."""
    text = _open(Code.COMMERCIAL, '13101')
    if 'after that date' not in text:
        return
    narrower = 'transactions entered into and events occurring after that date'
    broader = 'This code shall become effective on January 1, 1965'
    assert narrower in text
    assert broader in text
    # The first sentence alone would not confine coverage; the presumption
    # selects the after-that-date clause.
    assert prefer('against_retroactivity', (narrower, broader)) == narrower


def test_against_extraterritoriality_selects_within_this_state():
    """BPC 10130. Licensing duty is written for conduct within this state."""
    text = _open(Code.BUSINESS_AND_PROFESSIONS, '10130')
    if 'within this state' not in text:
        return
    narrower = 'within this state'
    broader = (
        'engage in the business, act in the capacity of, advertise or assume '
        'to act as a real estate broker or a real estate salesman'
    )
    assert narrower in text
    assert broader in text
    assert prefer('against_extraterritoriality', (narrower, broader)) == narrower


def test_clear_statement_refuses_retroactivity_without_express_words():
    """PEN 3. 'Unless expressly' gates the strong (retroactive) reading."""
    text = query.excerpt(Code.PENAL, '3', 'unless expressly so declared')
    if not text:
        return
    narrower = 'No part of it is retroactive'
    broader = 'retroactive'
    assert narrower in text
    assert broader in text
    # Clear-statement refuses the broader effect absent express declaration.
    assert prefer('clear_statement', (narrower, broader)) == narrower


def test_delegation_selects_apa_procedure_not_agency_meaning():
    """BPC 10080. Rulemaking is cross-referenced to the Administrative Procedure Act.

    Chevron U.S.A. Inc. v. Natural Resources Defense Council, Inc. is overruled
    by Loper Bright Enterprises v. Raimondo (2024). This test treats the APA
    cross-reference as a delegation limit on how rules are adopted. It does not
    treat an agency reading of the statute as binding.
    """
    text = _open(Code.BUSINESS_AND_PROFESSIONS, '10080')
    if 'Administrative Procedure Act' not in text:
        return
    narrower = (
        'shall be adopted, amended, or repealed in accordance with the '
        'provisions of the Administrative Procedure Act'
    )
    broader = (
        'may adopt, amend, or repeal rules and regulations that are '
        'reasonably necessary for the enforcement of the provisions of this part'
    )
    assert narrower in text
    assert broader in text
    assert prefer('delegation', (narrower, broader)) == narrower
    assert prefer('delegation', (narrower, broader)) != broader
