# English and legal parsers

The first lexical pass in `lexical.py` is a set of patterns for customary clauses. A sentence grammar is a later pass. These libraries are the ones that fit that pass. None of them is a source of statute text.

| Library | What it does | Fit |
| --- | --- | --- |
| [spaCy](https://spacy.io/) `en_core_web_*` | Tokenizer, part of speech, dependency parse | The general English parser. Legal sentences are long, so its sentence breaks need rules around citations and provisos |
| [Stanza](https://stanfordnlp.github.io/stanza/) | Neural tokenizer, tags, and dependency parse | Same job as spaCy, with Stanford's models. Heavier. Useful when a dependency label (subject, object, modifier) is the fact being pinned |
| [NLTK](https://www.nltk.org/) | Tokenizers, taggers, chunk grammars | A small grammar for "shall" and "may" can live here without a neural model |
| [Blackstone](https://github.com/ICLRandD/Blackstone) | spaCy pipeline for English case law: sentence segmenter, named entities, text categories | Built for law reports, not the United States Code. The sentence segmenter is the piece worth copying: it refuses to split inside a citation |
| [eyecite](https://github.com/freelawproject/eyecite) | Finds and resolves American citations, including `id.` and `supra` | The tool for "under what statute." A clause marked `authority` can be handed to eyecite to pull the citation out of the phrase |
| LexNLP | Legal segmentation and fact extractors on top of NLTK | Another clause finder. Overlaps the patterns already in `lexical.py`. Use it to compare, not as a second corpus |

Do not add these to the required install until a canon needs a parse tree. The enacting-clause search runs on the plain text the index already stores.

## What the first pass marks

`Clause` is an enum. Each value is the string written on an annotation.

| Clause | Customary words |
| --- | --- |
| `enactment` | "Be it enacted…" or "The people of the State of … do enact as follows" |
| `short_title` | "This Act shall be known as" |
| `definitions` | "For purposes of this" / "As used in this" |
| `severability` | "If any provision of this Act … invalid" |
| `effective_date` | "This Act shall take effect" |
| `authority` | "pursuant to", "under the authority of", "as authorized by", followed by a section number |
| `long_title` | "An Act to…" |
| `purpose` | "Whereas" or "The purpose of this Act is" |
| `findings` | "finds and declares" |
| `proviso` | "provided that" |
| `exception` | "except that", "except as", "unless otherwise" |
| `savings` | "Nothing in this Act affects" |
| `sunset` | "remains in effect until", "is repealed on", "shall expire" |
| `repealer` | "is hereby repealed" |

An `authority` mark is how an agency's enacting statute gets pinned: the office is the agency class, and the mark is the section that created it or authorized it. Court-creating phrases (vesting, jurisdiction, delegation) are a later pass, listed in [clauses.md](clauses.md). The eighty canon notes are indexed in [canons/index.md](canons/index.md).
