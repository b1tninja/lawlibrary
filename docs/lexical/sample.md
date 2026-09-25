# Sampling a book

Parser work needs a few real sections, not a whole code. `sample.sources` lists what can be drawn. `sample.sample` returns at most twenty sections from one book. The same seed returns the same sections.

| Kind | Book | Words |
| --- | --- | --- |
| `statute` | A code abbreviation, such as `CIV` or `Civil Code` | The Whoosh index. `pattern` keeps sections that match those words |
| `regulation` | A CFR title number, such as `24` | `data/codes/US/cfr/{title}.sqlite`. A missing file is `not_in_index` |
| `rule` | A court class, such as `SacramentoSuperiorCourt` | A pointer only. `found` is false and `reason` is `not_indexed`, with the official `url` and `shape` |
| `manual` | `OLRC`, `HOLC`, or `GPO` | `data/codes/US/manuals/{book}.sqlite`. A missing file is `not_in_index`. `GPO-2016`, `HOLC-2022`, and `CSM` are pointers |

MCP: `list_sources` and `sample_book`. A draw is for development. It does not pin a fact and it does not download a rule book.
