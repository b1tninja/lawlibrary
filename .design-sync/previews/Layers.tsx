import { Layers, Reader } from 'lawlibrary-reader'

import { counts } from './_data'

const act = { toggleLayer() {}, toggleKind() {}, onlyKind() {} }

function showing(on: string[]) {
  return {
    layers: on,
    layer: (name: string) => on.includes(name),
    kind: () => true,
    has: (layer: string) => on.includes(layer),
  }
}

/** What Civil Code 1940 carries, with notes and clauses drawn. */
export const WhatTheWordsCarry = () => (
  <Reader>
    <Layers counts={counts} shown={showing(['note', 'clause'])} act={act} />
  </Reader>
)

/** Every layer turned on. */
export const EveryLayer = () => (
  <Reader>
    <Layers
      counts={counts}
      shown={showing(['note', 'clause', 'canon', 'needle'])}
      act={act}
    />
  </Reader>
)

/** Nothing drawn: the words are read without a single mark. */
export const NothingDrawn = () => (
  <Reader>
    <Layers counts={counts} shown={showing([])} act={act} />
  </Reader>
)
