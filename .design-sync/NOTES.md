# design-sync notes — lawlibrary-reader

## What this package is

`client/` builds two things from one source tree. `npm run build` is the
**application** (`static/reader.js`, mounts on `#root`, fetches the WSGI
routes). `npm run build:lib` is the **library** this sync ships
(`client/dist/lawlibrary-reader.js`), which holds only the parts that take a
record and draw it. The views that read the index — `Section`, `Library`,
`Search`, `Cite`, `Closure`, `GraphView`, `Annotations` — are deliberately not
exported: they fetch on mount and render nothing without a server and a Whoosh
index behind them.

- Build the library before every sync: `npm --prefix client run build:lib`
  (`cfg.buildCmd`). Its `prebuild:lib` regenerates `client/src/tokens.css`.
- `client/src/tokens.css` is **generated** by `client/tokens.mjs` from
  `templates/style.html`, which is the one copy of the palette, the type, the
  cut ladder and the marks — the script-free Jinja pages include that same
  file. Never edit `tokens.css`; edit the template. The only rewrite is the
  opening `body` rule, which becomes `.reader` so a design that embeds these
  components dresses the root the library renders rather than the host page.
- `@types/react` must stay in `client/devDependencies` — without it the
  converter prints `[DTS_REACT]` and every props body comes out empty.
- `client/src/index.d.ts` is hand-written and copied to `dist/` by
  `build:lib`. It IS the API contract the design agent codes against; when a
  component's props change, change it in the same commit.

## Fixes this sync recorded

- `componentSrcMap.Reading = null`: `Reading` is a React context, not a
  component. Without the exclusion it becomes a 14th card that renders nothing.
- `cfg.provider = {component: "Reader"}`: every preview is wrapped in the
  library's own root, which is what carries the `reader` class and the shared
  context. Without it the cards render undressed.
- `overrides.Cuts` / `overrides.TermCard` = `{"cardMode": "column"}`: both are
  wider than a grid cell (`[GRID_OVERFLOW]`), so each story gets a full-width
  row.
- `cfg.tokensGlob` was removed as inert: `copyTokens` returns early unless
  `tokensPkg` names a package in `node_modules`, and this DS keeps its tokens
  inside its own stylesheet. `ds-bundle/tokens/` is therefore empty **by
  design** — the palette ships in `_ds_bundle.css`, which `styles.css`
  imports, so it does reach rendered designs. The conventions header points
  readers at that sheet, not at `tokens/`.
- Playwright: this machine already had chromium builds 1148 and 1234 cached in
  `%LOCALAPPDATA%\ms-playwright`. `playwright@1.62.0` pins 1234, so that is the
  version to install in `.ds-sync/` — a newer release downloads ~200MB for
  nothing. Check `node_modules/playwright-core/browsers.json` before installing.

## Known render warns

- `[FONT_MISSING] "Iowan Old Style", "Palatino Linotype", "Palatino"` — **not a
  missing brand font.** The library's type is a system stack ending in
  `Georgia, serif`; there is no webfont to ship and Palatino is not
  redistributable. Cards and designs render in Georgia where the first three
  are absent, which is the intended fallback. *Pending the user's explicit OK;
  until they give it, report it rather than suppressing it. If they want it
  silenced, `cfg.runtimeFontPrefixes` is the knob.*

## Preview sources

`.design-sync/previews/_data.ts` holds **real records** pulled once from the
running reader (`/section/CIV/1940`, `/marks/CIV/1940`, `/search`, `/closure
?use=refs`, `/diagram/codes`, `/term?q=dwelling`), one export per record so a
card carries only what it draws. To refresh it, start the server
(`python -c "from application import serve; serve(8765)"`) and re-fetch.

## Re-sync risks

- **`_data.ts` is a copy.** It was true of the index on the day it was taken.
  A reindex, a new session year, or a change to a payload's shape (a renamed
  field in `/marks` spans, say) leaves the cards rendering stale but
  plausible-looking records. Nothing detects this — re-fetch when the server's
  JSON changes.
- **`index.d.ts` is hand-written**, so it can drift from the components it
  describes. Nothing cross-checks them; a prop added in `marks.jsx` without a
  matching declaration is invisible to the design agent.
- **`tokens.css` is generated from a Jinja template.** If someone moves the
  `<style>` block out of `templates/style.html`, `tokens.mjs` throws by design
  rather than shipping an empty sheet — fix the script, don't bypass it.
- **The app and the library share source.** A change to `marks.jsx` or
  `layers.jsx` for the app changes the shipped library too. Run
  `npm --prefix client run build:lib` and re-sync after any such change.
- **Only the presentational layer is synced.** If someone exports a
  fetch-coupled view from `client/src/index.js`, its preview will render an
  empty state at best; keep the boundary.
