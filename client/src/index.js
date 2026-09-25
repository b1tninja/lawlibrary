/* The law library's reading components.
 *
 * These are the parts that take what they are given and draw it: the trail
 * above a section, the cuts under it, every reading layered over the words,
 * the citation graph, and the card a mark opens. The views that read the
 * index are not here — they are the application, and they need a server.
 *
 * Wrap a page in `Reader` once. It dresses the page and holds what the marks
 * share.
 */

import './library.css'

export { Reader } from './root.jsx'
export { Reading } from './reading.js'
export { Link, Pieces, Cuts, TermCard, NOTE_WORDS, noteWords } from './marks.jsx'
export { Layered, Layers, nest, useShown, LAYER_ORDER, LAYER_WORDS } from './layers.jsx'
export { Crumbs, Contents } from './library.jsx'
export { Graph } from './graph.jsx'
export { Hits } from './find.jsx'
export { Formats, Sides } from './section.jsx'
