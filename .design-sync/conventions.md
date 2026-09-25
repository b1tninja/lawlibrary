# The law library's reading components

These parts draw official statute text: the trail above a section, the cuts
under it, every reading a parser recorded over the words, the citation graph,
and the card a mark opens. They take records and draw them — none of them
fetches, and none composes a sentence. The words in any design you build with
them are words a caller handed in.

## Wrap the page in `Reader`

`Reader` is the root. It carries the `reader` class the sheet dresses, and it
holds what every mark shares: which readings are drawn (`shown`), what turns
one on (`act`), what a click looks up (`look`), and how a link opens (`go`).
Outside it components still render, but undressed — no paper ground, no serif,
no cut ladder. Wrap once, at the top.

```jsx
<Reader go={go}>
  <Crumbs crumbs={crumbs} go={go} />
  <h1>CIV 1940</h1>
  <Sides code="CIV" next="1940.1" go={go} />
  <Layers counts={counts} shown={shown} act={act} />
  <Cuts tree={tree} code="CIV" spans={spans} />
</Reader>
```

`go(event, href)` is the only navigation contract: every link and every span
that opens a place calls it. `Reader`'s default keeps the page where it is, so
a static design needs no router.

## The styling idiom: semantic classes, no utilities

There is no utility vocabulary here — no `bg-*`, no `p-4`. The sheet styles
element-and-class selectors, and your own layout glue should use the same
names so it sits inside the design rather than beside it.

| Family | Real names | What it is |
|---|---|---|
| Root | `reader` | the page ground: paper, serif, measure |
| Trail | `crumbs` | the heading trail (a `nav` with an `ol`) |
| Lists | `contents`, `cuts`, `refs`, `hits` | ordered lists the library draws |
| Cut ladder | `cut-division`, `cut-title`, `cut-part`, `cut-chapter`, `cut-article`, `cut-section`, `cut-subdivision`, `cut-subsection`, `cut-paragraph`, `cut-subparagraph`, `cut-clause`, `cut-subclause`, `cut-item`, `cut-subitem` | one class per unit, on the `li`; also `cut-library`, `cut-region`, `cut-code` for the rungs above a book |
| Reading surface | `reading` (on the `article` or `ol.cuts`), `cut-head`, `cut-unit`, `cut-words` | the words and the unit label beside them |
| Notes | `note-citation`, `note-cross_reference`, `note-cut`, `note-named_act`, `note-short_form`, `note-amount`, `note-period`, `note-date`, `note-occasion`, `note-session`, `note-case`, `note-definition`, `note-compound`, `note-override`, `note-exception`, `note-limit`, `note-proviso` | one tint per `Note` member, on a `mark` |
| Layer channels | `lay-note` (tint), `lay-clause` (bar), `lay-canon` (dotted rule), `lay-mention` (underline), `lay-relation` (wavy), `lay-abbreviation` (dashed), `lay-needle` (ring) | each layer owns one visual channel, so overlapping readings all show |
| Chrome | `term-card`, `layers`, `graph`, `history`, `beside`, `formats`, `legend`, `thin`, `miss` | the card, the readings bar, the drawing, the credit line, the sides, the representations, small print, a miss |

Type is `"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif` — a
system stack by design, with Georgia as the shipped fallback; there is no
webfont to load. Ink `#1a1814`, links `#1a3654`, rules `#ddd6c8`, paper
`#f4f0e6`, card `#fffdf8`, small print `#5c4a32`, muted `#8a8172`. Graph edge
kinds are `#1f5aa8` / `#a35a12` / `#2f7d4f`, each also carrying its own stroke
pattern so identity never rests on colour alone.

## Where the truth is

Read `_ds/<folder>/styles.css` and the `_ds_bundle.css` it imports before
styling anything — that sheet is the whole vocabulary, and it is short.
Per component, `<Name>.d.ts` is the prop contract and `<Name>.prompt.md` is
the usage reference. The record shapes the props take — `Piece`, `Span`,
`CutNode`, `Crumb`, `Item`, `Hit`, `Edge`, `WalkNode` — are all declared in
those `.d.ts` files.

## Two things that will bite

- **Spans are keyed by cut `path`.** `Cuts` looks up `spans[node.path]`; a
  `CutNode` without its `path` draws its words unlayered. Keep the server's
  paths (`"0"`, `"0.1"`, `"0.1.0"`) intact.
- **A layer that is off draws nothing.** `Reader`'s default shows notes and
  clauses only. To show canons, word classes, names or duties, pass a `shown`
  whose `layer()` and `has()` return true for them.
