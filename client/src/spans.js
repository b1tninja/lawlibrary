/* The span algebra: overlapping readings turned into one well-formed tree.
 *
 * A span is a layer, a kind, and two offsets into one run of words. Spans
 * overlap and nest, because the readings do — `Except as provided` is a note,
 * a clause, and a canon over three different lengths of the same phrase. HTML
 * has no overlap, so a span that leaves the span holding it is cut at the
 * boundary and carried on as a second node of the same span.
 *
 * Nothing here draws anything. It is the shape `layers.jsx` renders.
 */

/* How long the reader hovers a mark before its card opens. One delay for
 * every mark, whichever surface drew it. */
export const HOVER_MS = 450

/* The innermost node holding this offset. Siblings never overlap, so at most
 * one child can hold it. */
function holder(node, at) {
  if (at < node.start || at >= node.end) return null
  for (let index = 0; index < node.children.length; index += 1) {
    const found = holder(node.children[index], at)
    if (found) return found
  }
  return node
}

function ordered(node) {
  node.children.sort((one, two) => one.start - two.start)
  node.children.forEach(ordered)
  return node
}

/* One tree of spans over one run of `length` words. A span that runs past the
 * end of the span holding it is cut there and carries on as its own node, so
 * the drawing stays well formed. A span outside the words is dropped.
 *
 * Each piece is hung from the innermost node that holds where it starts, found
 * from the root. A crossing span leaves a fragment that begins later than the
 * words a following span opens on, so the place to hang a piece cannot be read
 * off the last one that was hung. */
export function nest(spans, length) {
  const root = { start: 0, end: length, span: null, children: [] }
  const queue = (spans || [])
    .filter((span) => span.end > span.start && span.start >= 0)
    .slice()
    .sort((one, two) => (one.start - two.start) || (two.end - one.end))
  queue.forEach((span) => {
    let from = span.start
    const to = Math.min(span.end, length)
    while (from < to) {
      const host = holder(root, from)
      if (!host) break
      const stop = Math.min(to, host.end)
      if (stop <= from) break
      host.children.push({ start: from, end: stop, span, children: [] })
      from = stop
    }
  })
  return ordered(root)
}

/* The class names one span is drawn with. The legend and the words share this,
 * so a swatch cannot drift from the mark it stands for. */
export function spanClasses(layer, kind) {
  const word = String(kind || '').replace(/[^A-Za-z0-9_]/g, '')
  if (layer === 'note') return `lay-note note-${word}`
  return `lay-${layer} ${layer}-${word}`
}
