import { Crumbs, Cuts, Layers, Reader, Sides } from 'lawlibrary-reader'

import { counts, crumbs, spans, tree } from './_data'

const go = () => {}
const act = { toggleLayer() {}, toggleKind() {}, onlyKind() {} }
const shown = {
  layers: ['note', 'clause'],
  layer: (name: string) => ['note', 'clause'].includes(name),
  kind: () => true,
  has: (layer: string) => ['note', 'clause'].includes(layer),
}

/**
 * A page of the library: the trail, the sections beside it, the readings drawn
 * over the words. Everything inside one `Reader` shares what it holds.
 */
export const APageOfTheLibrary = () => (
  <Reader go={go} shown={shown} act={act}>
    <Crumbs crumbs={crumbs} go={go} />
    <h1>CIV 1940</h1>
    <Sides code="CIV" next="1940.1" go={go} />
    <Layers counts={counts} shown={shown} act={act} />
    <Cuts tree={tree.children[0]} code="CIV" spans={spans} />
  </Reader>
)

/** The root on its own, holding one heading and one paragraph. */
export const TheRootAlone = () => (
  <Reader>
    <h1>Civil Code</h1>
    <p>Every part inside this root is dressed by the library's own sheet.</p>
  </Reader>
)
