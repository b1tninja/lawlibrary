# Named things by frame

A statute repeats a few frames around a proper name. The frame is the classifier. The name is whatever follows it. `mentions.py` does not keep a list of every city or every department.

| Frame | Kind | Example |
| --- | --- | --- |
| `State of …` or `Commonwealth of …` | `state` | State of California |
| `County of …` | `county` | County of Sacramento |
| `City of …` | `city` | City of Sacramento |
| `Supreme Court of …`, `Superior Court of …, County of …`, `Third Appellate District` | `court` | Superior Court of the State of California, County of Sacramento |
| `Department of …`, `Office of …`, `Commission of …`, `Board of …`, `Agency of …` | `agency` | Department of Real Estate |

`Kind` is an enum. The value is the string `state`, `county`, `city`, `court`, or `agency`.

## Resolve after the frame

The frame always yields a mention. A second step asks the catalogs already in this project whether the name is known:

- A state name is checked against the ISO 3166-2 subdivisions of `US`. `California` becomes `US-CA`. `Atlantis` stays a state mention with no code.
- A city or county name is checked against the localities this catalog has loaded. One match stores that place's parent. Two matches store nothing, so the frame is not forced onto the wrong place.
- A court frame is checked against the courts registered in `court.py`.
- An agency frame is checked against the offices registered in `agency.py`.

An unknown name is still classified. Adding a city to the catalog is how that city becomes resolvable. It is not a new pattern.

`analysis.analyze` splits the text into sentences and turns each framed name into an instance. A known name is an instance of its registered class, such as `CaliforniaDepartmentOfRealEstate` or `SacramentoSuperiorCourt`. An unknown department is an instance of `Agency`. Duties in a later sentence that names no new office stay on the office the previous sentence introduced.

`analysis.pin` writes those instances to `pins.sqlite`. Each row is one fact for one citation and one class: the jurisdiction (`US-CA`), an enactment frame, or a duty such as `responsibility`. Pinning the same citation again replaces those rows. The file is an index of jurisdiction and delegation. It is not a copy of the statute.

A registered office is then a search key. The ways a statute creates that office — “there is in … a department”, “the chief officer of which is named”, “hereby created” — are [authority.md](authority.md). A section sign in that text is a citation: `§` is one section and `§§` is a range or a series, as [citations.md](citations.md) describes.
