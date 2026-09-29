"""City of Sacramento, the catalog's home.

The City Code is codified for the City by Quality Code Publishing and
served by American Legal Publishing: the City's own City Code page
forwards there. A commercial host is never a source here, so the City
Code is a pointer, and the City keeps no edition of the words itself. The
ordinances are the City Clerk's records.
"""

from jurisdiction import Codification, Host
from publication import City

from us.ca.counties.sacramento import SacramentoCounty

CITY_CODE = Codification(
    title='Sacramento City Code',
    abbreviation='SCC',
    host=Host.AMERICAN_LEGAL,
    pointer='https://www.cityofsacramento.gov/city-government/services/city-code',
    ordinances='https://www.cityofsacramento.gov/clerk',
)


class Sacramento(City):
    name = 'Sacramento'
    parent = SacramentoCounty
    codes = (CITY_CODE,)
