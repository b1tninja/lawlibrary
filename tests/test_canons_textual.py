"""Textual canons illustrated from indexed California statute text."""

from canons import Canon, find_signals, readings


def test_mandatory_shall_and_permissive_may():
    """Gov. Code § 14."""
    text = """
\u201cShall\u201d is mandatory and \u201cmay\u201d is permissive.
"""
    assert find_signals(text, Canon.MANDATORY)
    assert find_signals(text, Canon.PERMISSIVE)


def test_means_closed_set_and_includes_open_set():
    """Pub. Res. Code § 828."""
    text = """
As used in this chapter, \u201caquaculture\u201d means the culture and husbandry of aquatic organisms, including, but not limited to, fish, shellfish, mollusks, crustaceans, kelp, and algae.
"""
    found = readings(text)
    assert Canon.CLOSED_SET in found
    assert Canon.OPEN_SET in found


def test_ejusdem_generis_or_other():
    """Fish & G. Code § 9050."""
    text = """
A spade, shovel, hoe, rake, or other appliance operated by hand may be used to take mollusks, sand crabs, and shrimps in Districts 1, 112, 2, 212, 3, 312, 4, 418, 434, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 19A, 20, 20A, and 21, except as specified in Sections 7332 and 8303, and except that freshwater clams shall not be taken by means of such appliances on any levee or on the berm of any levee.
"""
    found = readings(text)
    assert Canon.EJUSDEM_GENERIS in found
    assert Canon.PERMISSIVE in found


def test_expressio_unius_only():
    """Civ. Code § 1756."""
    text = """
The substantive and procedural provisions of this title shall only apply to actions filed on or after January 1, 1971.
"""
    found = readings(text)
    assert Canon.EXPRESSIO_UNIUS in found
    assert Canon.MANDATORY in found


def test_noscitur_and_or_neighbors():
    """Food & Agr. Code § 55608."""
    text = """
Accurate grading and weight receipts shall be given by all processors to each producer, or his agent, upon each and every delivery.
"""
    found = readings(text)
    assert Canon.NOSCITUR in found
    assert Canon.CONJUNCTION in found
    assert Canon.DISJUNCTION in found


def test_last_antecedent_which():
    """Educ. Code § 48206.3."""
    text = """
(a)Except for those pupils receiving individual instruction provided pursuant to Section 48206.5, a pupil with a temporary disability which makes attendance in the regular day classes or alternative education program in which the pupil is enrolled impossible or inadvisable shall receive individual instruction provided by the district in which the pupil is deemed to reside.
"""
    found = readings(text)
    assert Canon.LAST_ANTECEDENT in found
    assert Canon.MANDATORY in found


def test_series_qualifier():
    """Fish & G. Code § 9050."""
    text = """
A spade, shovel, hoe, rake, or other appliance operated by hand may be used to take mollusks, sand crabs, and shrimps in Districts 1, 112, 2, 212, 3, 312, 4, 418, 434, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 18, 19, 19A, 20, 20A, and 21, except as specified in Sections 7332 and 8303, and except that freshwater clams shall not be taken by means of such appliances on any levee or on the berm of any levee.
"""
    found = readings(text)
    assert Canon.SERIES_QUALIFIER in found
    assert Canon.EJUSDEM_GENERIS in found


def test_specific_controls_general():
    """Prob. Code § 3612."""
    text = """
(a)Notwithstanding any other provision of law and except to the extent the court orders otherwise, the court making the order under Section 3611 shall have continuing jurisdiction of the money and other property paid, delivered, deposited, or invested under this article until the minor reaches 18 years of age.
"""
    found = readings(text)
    assert Canon.SPECIFIC in found
    assert Canon.GENERAL in found


def test_surplusage_null_and_void():
    """Bus. & Prof. Code § 678."""
    text = """
The failure to give the notice required by this article shall make any contract entered into between the parties null and void.
"""
    found = readings(text)
    assert Canon.SURPLUSAGE in found
    assert Canon.MANDATORY in found
