# Citation manuals

Each guide the citation parser can name has an official page in `companions.editions`. A **posted** edition is free to read at that page. A **lesser** edition is sold or behind a subscription. The library does not download either. `Companion.read` opens a file that is already on disk. HTML is split on headings. A PDF returns `reason: pdf` until a text extractor exists. A lesser edition with no local file returns `reason: lesser`.

| Guide | Posted source | Lesser source |
| --- | --- | --- |
| California Style Manual | [Rule 1.200](https://courts.ca.gov/cms/rules/index/one/rule1_200) and [rule 8.204](https://courts.ca.gov/cms/rules/index/eight/rule8_204) on courts.ca.gov. Rule 1.200 requires this manual or The Bluebook, used consistently. Rule 8.204 encourages the California Style Manual (4th ed. 2000). The Fourth Appellate District self-help appendix tells a filer to give the code name and the word "section". | The manual itself. The Reporter of Decisions prepares it. The full text is not on courts.ca.gov. Copies are sold. |
| The Bluebook | None. Court rules name it. | [legalbluebook.com](https://www.legalbluebook.com/). The Harvard, Columbia, Pennsylvania, and Yale law reviews publish it. The book is sold. |
| The Indigo Book | [Second edition HTML](https://law.resource.org/pub/us/code/blue/indigobook-2.1.html) at Public.Resource.Org, CC0. It implements the practitioner citation system and is not The Bluebook. | None. |
| ALWD Guide to Legal Citation | The Association describes the guide. The Indigo Book names it as a paid competitor. | [alwd.org/about-guide](https://www.alwd.org/about-guide). The current edition is sold. |
| Universal Citation Guide | The American Association of Law Libraries describes medium-neutral citation (year, jurisdiction, number) on its publications page. | [The guide](https://www.aallnet.org/resources-publications/publications/universal-citation-guide/), third edition, sold by William S. Hein & Co. (2014). |
| APA Style | [Legal examples](https://apastyle.apa.org/style-grammar-guidelines/references/examples/clinical-practice-references) on the APA Style site. A statute is the name, the source, a section sign, and the year, with no italics. | The Publication Manual, 7th edition. Chapter 11 is the legal chapter. The book is sold. |
| Chicago Manual of Style | None in this catalog. | [chicagomanualofstyle.org](https://www.chicagomanualofstyle.org/). The University of Chicago Press sells it. It defers to The Bluebook for a legal cite and uses ibid for a repeated note. |

Cornell's Legal Information Institute posts a free [Introduction to Basic Legal Citation](https://www.law.cornell.edu/citation/). That work points at The Bluebook, ALWD, the Indigo Book, and the Universal Citation Guide. It is an explanation, not one of the manuals above.

`fetch_posted` saves the posted HTML under the codes directory and `load_posted` indexes it. The Indigo Book and California Rules of Court rules 1.200 and 8.204 are indexed. The APA Style examples page answered with a block page and was not indexed. Lesser manuals are not fetched.

MCP: `list_style_manuals` and `search_style_manual`.
