# Jurisdictions

A country is an ISO 3166-1 alpha-2 code. A first-level region is an ISO 3166-2 code. Having a subdivision code does not mean that region publishes its own statutes.

ISO does not ship a Python API. This environment already has `pycountry` (249 countries). The United States is `US` / `USA` / `840`. `pycountry.subdivisions` lists 57 US entries typed State, District, or Outlying area. California is `US-CA`. The state branches are that layer. `babel` names locales. It does not define legal subdivisions.

The United Kingdom's alpha-2 is `GB`. `UK` is reserved, not the standard code. Devolved subdivisions look like `GB-SCT`.

## Who publishes statutes

- **Federal.** National law and first-level law both exist. United States (states), Canada (provinces), Australia (states), Germany (Länder), India (states), Mexico and Brazil (estados), Switzerland (cantons).
- **Unitary.** Primary statutes are national. France and Japan. Prefectures are ISO subdivisions and are not a second statute corpus.
- **Devolved.** The center delegates lawmaking. The UK publishes UK acts and Scotland, Wales, and Northern Ireland acts. England has no separate legislature.

A confederation is not a useful catalog model for current domestic statutes.

## Official national collections

| Code | Subdivision that legislates | Official collection |
| --- | --- | --- |
| US | States | Federal: <https://uscode.house.gov/>. States: each legislature. California: <https://downloads.leginfo.legislature.ca.gov/> |
| CA | Provinces | <https://laws-lois.justice.gc.ca/eng/> |
| GB | Devolved nations | <https://www.legislation.gov.uk/> |
| AU | States | <https://www.legislation.gov.au/> |
| DE | Länder | <https://www.gesetze-im-internet.de/> |
| IN | States | <https://indiacode.gov.in/> |
| MX | Estados | <https://www.diputados.gob.mx/LeyesBiblio/index.htm> |
| BR | Estados | <https://www4.planalto.gov.br/legislacao/> |
| FR | National only | <https://www.legifrance.gouv.fr/> |
| JP | National only | <https://laws.e-gov.go.jp/> |
| ZA | Provinces, limited competence | National acts: <https://www.gov.za/documents/acts>. No single provincial corpus verified |
| CH | Cantons | <https://www.fedlex.admin.ch/> |

State, province, Land, canton, and estado are the same catalog layer as `US-CA`. A Japanese prefecture is not. Louisiana parishes are counties inside `US-LA`, not ISO countries.
