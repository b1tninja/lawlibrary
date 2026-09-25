/* What the open page shares with every mark on it: which readings are drawn,
 * what a click looks up, and how a link opens. One module, so the renderer and
 * the marks do not import each other.
 */

import { createContext } from 'react'

export const Reading = createContext({
  shown: { has: () => true, layer: () => true, kind: () => true, layers: [] },
  look: () => {},
  go: () => {},
})
