# The constitution is the root

`UnitedStatesConstitution` is the root of the federal government. Three organs hang from it. The citation is the article and section. The sentence itself stays in the constitution's edition.

| Organ | Branch | Authority |
| --- | --- | --- |
| Congress | `Branch.LEGISLATIVE` | United States Constitution article I, section 1 |
| President of the United States | `Branch.EXECUTIVE` | United States Constitution article II, section 1 |
| Supreme Court and inferior courts | `Branch.JUDICIAL` | United States Constitution article III, section 1 |

`CaliforniaConstitution` is the root for California courts. The Supreme Court of California carries article VI. Sacramento Superior Court reaches that charter through the courts above it. Its own creating section remains article VI, section 4, already stored on the court.

A department such as the Department of Real Estate is created by statute (`BPC 10050`). It is not one of these three organs.

## Style manuals named by court rules

California Rules of Court, rule 1.200, was opened at [courts.ca.gov](https://courts.ca.gov/cms/rules/index/one/rule1_200). Citations in documents filed in the courts must follow either the California Style Manual or The Bluebook, used consistently. That pair is `Guide.CALIFORNIA_STYLE_MANUAL` and `Guide.BLUEBOOK` on the California Rules of Court book. Sacramento Superior Court carries that book, so a filing there uses both guides. The Style Manual text is not posted on that host. The Bluebook is not a government publication and is not indexed.

Rule 8.204, on the same host, points brief writers back to rule 1.200 and encourages the California Style Manual (4th ed., 2000).

The Eastern District of California local rules effective February 23, 2026, were opened as text. They do not name a style manual. A judge's standing note on the same court site prefers The Bluebook for that judge's cases. That note is not the local rules.

The Sacramento local-rules file is a PDF. It was not opened for a style-manual sentence. The statewide rule above is the one this court already carries.

## Parser mixins

`Parser` is `CanonMixin` and `StyleMixin`. The canon mixin reports both readings when one sentence supports two canons that disagree. The style mixin holds the `Guide` members the court rule names. `CaliforniaFiling` is that pair for a document filed in a California court.
