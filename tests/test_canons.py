import query
from apa import Code
from canons import Canon, ambiguities, find_signals, readings


def _office():
    """BPC 10071 and 10080. The sentences that carry shall and may."""
    parts = [
        query.excerpt(Code.BUSINESS_AND_PROFESSIONS, '10071', 'shall enforce'),
        query.excerpt(Code.BUSINESS_AND_PROFESSIONS, '10080', 'may adopt'),
    ]
    return '\n'.join(part for part in parts if part)


def test_shall_and_may_are_different_readings_of_one_office():
    """BPC 10071 and 10080. Shall obliges. May permits."""
    text = _office()
    if not text:
        return
    assert find_signals(text, Canon.MANDATORY)
    assert find_signals(text, Canon.PERMISSIVE)
    assert Canon.MANDATORY in readings(text)
    assert Canon.PERMISSIVE in readings(text)
    mandatory = find_signals(text, Canon.MANDATORY)[0]
    permissive = find_signals(text, Canon.PERMISSIVE)[0]
    assert mandatory.reading != permissive.reading


def test_include_and_or_other_are_left_unresolved():
    """EVID 1410.5. Open set and ejusdem generis disagree. The parser does not choose."""
    graffiti = query.excerpt(Code.EVIDENCE, '1410.5', 'shall include')
    office = _office()
    if not graffiti or not office:
        return
    found = ambiguities(graffiti)
    pair = {Canon.OPEN_SET, Canon.EJUSDEM_GENERIS}
    assert any({item.left.canon, item.right.canon} == pair for item in found)
    assert ambiguities(office) == []
