"""A jurisdiction diagram drawn from vesting clauses.

The strategy has three steps.

1. Keep only sentences ``find_enactments`` marks as vesting. A vested
   property right stays out.
2. Read the office that receives the powers and, when the sentence names
   one, the office that held them before. ``shall succeed to, and is vested
   with`` names the receiver. ``previously vested in`` or ``vested by law in``
   names the prior office.
3. Draw one edge from the prior office to the receiver. A receiver with no
   prior office is a node and no edge. The diagram is that graph.
"""

import re

from mentions import find_enactments


class Grant:
    """Powers moving from one office to another. ``prior`` may be empty."""

    def __init__(self, receiver, prior, text):
        self.receiver = receiver
        self.prior = prior
        self.text = text


_SUCCESSION = re.compile(
    r'(?i)(?P<receiver>[A-Z][^.]{0,180}?)\s+(?:shall|may) succeed to'
    r'(?:,?\s+and is (?:hereby )?vested with)?\b'
    r'(?P<body>[^.]*)'
)
_PRIOR = re.compile(
    r'(?i)\b(?:vested (?:by law |previously )?in|powers of) (?:the )?(?:former )?(?P<prior>[^.,]+)'
)
_AUTHORITY = re.compile(
    r'(?i)(?P<receiver>[A-Z][^.]{0,120}?)\s+shall have all authority previously vested in (?:the )?(?P<prior>[^.,]+)'
)
_GENERIC = frozenset({
    'board', 'commission', 'department', 'director', 'chief', 'secretary',
    'office', 'officer', 'committee', 'bureau', 'agency', 'state',
    'him', 'her', 'him or her', 'existing board', 'previous board', 'former board',
    'the board', 'the commission', 'the department',
})
_CREATED = re.compile(
    r'(?i)\bthere is hereby created (?:the )?(?P<receiver>[^,]+?)(?=,|\s+which\b|\s+hereinafter\b)'
)


def _clean(name):
    name = re.sub(r'\s+', ' ', name or '').strip(' .')
    name = re.sub(r'^(?:\([a-zA-Z0-9]+\)|[a-zA-Z0-9]+\)|\d+\.)\s*', '', name)
    name = re.sub(r'(?i)^(?:in the|in|the|former) ', '', name)
    return name


def _offices(name):
    """One name, or two when the clause says ``A or B``."""
    return [kept for kept in (_keep(part) for part in re.split(r'\s+or\s+', name or '')) if kept]


def _keep(name):
    """A named office. A bare board, a pronoun, or a citation clause is not one."""
    cleaned = _clean(name)
    if not cleaned or len(cleaned) > 90:
        return ''
    if cleaned.casefold() in _GENERIC:
        return ''
    if re.search(r'(?i)\b(which|pursuant|commencing|section)\b', cleaned):
        return ''
    if not re.search(r'[A-Z]', cleaned[1:]):
        return ''
    return cleaned


def grants(text):
    """Vesting sentences in ``text``, each as a ``Grant``."""
    if not text:
        return []
    found = []
    spans = [
        (mark.start, mark.end)
        for mark in find_enactments(text)
        if mark.name == 'vesting'
    ]
    for match in _SUCCESSION.finditer(text):
        receiver = _keep(match.group('receiver'))
        earlier = _PRIOR.search(match.group('body') or '')
        priors = _offices(earlier.group('prior')) if earlier else []
        for prior in priors:
            if receiver and prior.casefold() != receiver.casefold():
                found.append(Grant(receiver, prior, match.group(0)))
    for match in _AUTHORITY.finditer(text):
        if not any(match.start() < end and match.end() > start for start, end in spans):
            continue
        receiver = _keep(match.group('receiver'))
        for prior in _offices(match.group('prior')):
            if receiver and prior.casefold() != receiver.casefold():
                found.append(Grant(receiver, prior, match.group(0)))
    for match in _CREATED.finditer(text):
        if not any(match.start() < end and match.end() > start for start, end in spans):
            continue
        receiver = _clean(match.group('receiver'))
        if receiver and not any(item.receiver == receiver for item in found):
            found.append(Grant(receiver, '', match.group(0)))
    return found


def diagram(text):
    """A mermaid flowchart of the grants in ``text``. A receiver with no prior office is a node and no edge."""
    from structure import _chart
    found = grants(text)
    return _chart(
        [(grant.prior, grant.receiver) for grant in found if grant.prior and grant.receiver],
        'vested',
        nodes=[grant.receiver for grant in found if grant.receiver and not grant.prior],
    )
