"""City of Sacramento, the catalog's home."""

from publication import City

from us.ca.counties.sacramento import SacramentoCounty


class Sacramento(City):
    name = 'Sacramento'
    parent = SacramentoCounty
