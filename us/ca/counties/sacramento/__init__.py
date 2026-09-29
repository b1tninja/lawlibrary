"""Sacramento County.

The County Code is codified for the County by General Code and served on
eCode360, which County Counsel's page links to and says is not maintained
by the County; a commercial host is never a source here, so the County
Code is a pointer. The Zoning Code is different: the County's Planning
department publishes it itself, chapter by chapter, at
landuse.saccounty.gov, and those words may be read (``zoning``).
"""

from jurisdiction import Codification, Host
from publication import County

COUNTY_CODE = Codification(
    title='Sacramento County Code',
    abbreviation='SCC',
    host=Host.GENERAL_CODE,
    pointer='https://countycounsel.saccounty.gov/content/coco/us/en/county-code.html',
    ordinances='https://agendanet.saccounty.gov/BoardOfSupervisors/',
)

ZONING_CODE = Codification(
    title='Zoning Code of Sacramento County',
    abbreviation='SZC',
    host=Host.OFFICIAL,
    pointer='https://landuse.saccounty.gov/szc/0_about/',
    text='https://landuse.saccounty.gov/szc/',
    ordinances='https://agendanet.saccounty.gov/BoardOfSupervisors/',
)


class SacramentoCounty(County):
    name = 'Sacramento'
    parent = 'US-CA'
    codes = (COUNTY_CODE, ZONING_CODE)
