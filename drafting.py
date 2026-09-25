"""Official guidance on how a statute is built.

These are the bodies that published the rule. A commentary from a law
school is marked academic. A newspaper is not a source.
"""

import enum

from structure import Rank


class Body(enum.Enum):
    """Who published the guidance."""

    LEGISLATIVE = 'legislative'
    JUDICIAL = 'judicial'
    ACADEMIC = 'academic'


class Level(enum.Enum):
    """The unit a marker names.

    California calls ``(a)`` a subdivision. The House Office of the
    Legislative Counsel calls that same mark a subsection. The deeper
    marks use the same words in both: paragraph, subparagraph, clause.
    """

    HEADING = 'heading'
    SUBDIVISION = 'subdivision'
    PARAGRAPH = 'paragraph'
    SUBPARAGRAPH = 'subparagraph'
    CLAUSE = 'clause'


_LEVELS = {
    Rank.HEADING: Level.HEADING,
    Rank.LETTER: Level.SUBDIVISION,
    Rank.NUMBER: Level.PARAGRAPH,
    Rank.CAPITAL: Level.SUBPARAGRAPH,
    Rank.CLAUSE: Level.CLAUSE,
}


def level(rank):
    """The unit name for a rank, or ``None`` when the rank is empty."""
    if rank is None:
        return None
    return _LEVELS.get(rank)


class Source:
    """One published guide. ``url`` is the official page."""

    def __init__(self, name, body, url, note):
        self.name = name
        self.body = body
        self.url = url
        self.note = note


SOURCES = (
    Source(
        'HOLC Guide to Legislative Drafting',
        Body.LEGISLATIVE,
        'https://legcounsel.house.gov/holc-guide-legislative-drafting',
        'The House Office of the Legislative Counsel. A section is the basic unit. '
        'The guide quotes title 1, United States Code, section 104: a section shall '
        'contain, as nearly as may be, a single proposition of enactment. Title 1 '
        'was not opened in the local index.',
    ),
    Source(
        'House Legislative Counsel Manual on Drafting Style (2022)',
        Body.LEGISLATIVE,
        'https://legcounsel.house.gov/sites/evo-subsites/legcounsel-evo.house.gov/files/documents/ManualDraftStyle_2022.pdf',
        'A further subdivision must nest inside the preceding one. A unique section '
        'number is best practice. An omnibus bill may repeat a section number.',
    ),
    Source(
        'Joint Rules of the California Senate and Assembly',
        Body.LEGISLATIVE,
        'https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=201920200SCR1',
        'Joint Rule 8.5: a bill may not be introduced unless the Legislative Counsel '
        'has attached the cover and a digest. The rule does not require consecutive subdivision letters.',
    ),
    Source(
        'California Rules of Court, rule 1.200',
        Body.JUDICIAL,
        'https://courts.ca.gov/cms/rules/index/one/rule1_200',
        'Citations in a document filed in the courts must follow the California Style '
        'Manual or The Bluebook, consistently. The rule governs the brief, not the code.',
    ),
    Source(
        'Welfare and Institutions Code section 6',
        Body.LEGISLATIVE,
        'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=WIC&sectionNum=6',
        'Headings shall not be deemed to govern, limit, modify, or affect the scope, '
        'meaning, or intent of the provisions.',
    ),
    Source(
        'Public Utilities Code section 10',
        Body.LEGISLATIVE,
        'https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=PUC&sectionNum=10',
        'Section means a section of that code unless another statute is named. '
        'Subdivision means a subdivision of the section in which that word occurs '
        'unless another section is named.',
    ),
    Source(
        'Statutory Construction Guidelines for Bill Drafting in California',
        Body.ACADEMIC,
        'https://scholarlycommons.pacific.edu/cgi/viewcontent.cgi?article=1327&context=uoplawreview',
        'University of the Pacific Law Review. Commentary on the Office of Legislative '
        'Counsel. It is not a statute and it is not a court rule.',
    ),
)
