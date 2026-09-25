"""Expectations a California section usually meets.

A break is a place to look again. It may be a parser miss, or, rarely, the
text itself. The checker does not decide which. Joint Rule 8.5 of the Senate
and Assembly says a bill may not be introduced unless the Legislative Counsel
has attached the cover and the digest. It does not set the subdivision
alphabet. California Rules of Court, rule 1.200, says citations in a filed
document must follow one style manual consistently. That rule governs the
brief, not the code section.
"""

import enum
import re

from drafting import level
from outline import Roman
from structure import Rank, find_links, split_nodes


class Expectation(enum.Enum):
    """A claim a well-formed section usually satisfies."""

    SEQUENCE = 'sequence'
    RANK = 'rank'
    LOCAL_LABEL = 'local_label'
    FOLLOWING = 'following'


class Fault:
    """One place the text does not meet an expectation."""

    def __init__(self, expectation, label, detail):
        self.expectation = expectation
        self.label = label
        self.detail = detail


_FOLLOWING = re.compile(r'(?i)\b(?:either|any|all|both|one)\s+of\s+the\s+following\b')


def _key(label, rank):
    inner = label.strip('().')
    if inner.startswith('_') and inner.endswith('_'):
        inner = inner.strip('_')
    if rank is Rank.NUMBER and inner.isdigit():
        return int(inner)
    if rank in (Rank.HEADING, Rank.CLAUSE):
        roman = Roman.read(inner)
        return None if roman is None else roman.value
    if rank in (Rank.LETTER, Rank.CAPITAL) and inner.isalpha():
        token = inner.lower()
        if len(token) == 1:
            return ord(token) - ord('a')
        if len(token) == 2 and token[0] == token[1]:
            return 26 + (ord(token[0]) - ord('a'))
    return None


def _sequence(children):
    faults = []
    groups = {}
    for child in children:
        if child.rank is None:
            continue
        groups.setdefault(child.rank, []).append(child)
    for rank, nodes in groups.items():
        keys = [(node, _key(node.label, rank)) for node in nodes]
        if any(key is None for _node, key in keys):
            continue
        previous = None
        for node, key in keys:
            if previous is not None and key != previous + 1:
                faults.append(Fault(
                    Expectation.SEQUENCE, node.label,
                    'expected the next %s after %s' % (rank.name.lower(), previous),
                ))
            previous = key
    return faults


def _rank(node):
    faults = []
    if node.rank is None:
        return faults
    for child in node.children:
        deeper = child.margin > node.margin if node.margin is not None else False
        if not deeper and child.rank is not None and child.rank.value <= node.rank.value:
            faults.append(Fault(
                Expectation.RANK, child.label,
                'a %s must nest inside the preceding %s' % (
                    level(child.rank).value, level(node.rank).value,
                ),
            ))
    return faults


def _labels(root, text):
    present = set()
    for node in root.walk():
        if node.label:
            present.add(node.label.strip('().').strip('_').lower())
    faults = []
    for link in find_links(text):
        if link.kind != 'subdivision' or not link.label or link.section:
            continue
        if link.label.lower() not in present:
            faults.append(Fault(
                Expectation.LOCAL_LABEL, '(%s)' % link.label,
                'named in the text and not in the outline',
            ))
    return faults


def _following(node):
    faults = []
    if _FOLLOWING.search(node.text or '') and len(node.children) < 2:
        faults.append(Fault(
            Expectation.FOLLOWING, node.label,
            'the following is not followed by two items',
        ))
    for child in node.children:
        faults.extend(_following(child))
    return faults


def muster(text):
    """The expectations this section does not meet."""
    root = split_nodes(text or '')
    faults = []
    for node in root.walk():
        faults.extend(_sequence(node.children))
        if node is not root:
            faults.extend(_rank(node))
    faults.extend(_labels(root, text or ''))
    faults.extend(_following(root))
    return faults
