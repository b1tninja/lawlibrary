/* The expanded table of contents as a list a view can count and sift.
 *
 * A rung is `{ label, children }`; `children` nests the rungs under it the
 * way the publisher nests them. Nothing here reads the unit, because the
 * codes do not share one ladder: depth is where a rung sits, not its name.
 */

/* How many headings a nested tree holds, every level counted. */
export function headings(items) {
  return (items || []).reduce((sum, item) => sum + 1 + headings(item.children), 0)
}

function matches(item, needle) {
  if (String(item.label || '').toLowerCase().includes(needle)) return true
  return (item.children || []).some((child) => matches(child, needle))
}

/* The rungs that match the sift, each with only its own matching rungs. A
 * parent whose caption misses stays when a rung under it hits, so the hit
 * keeps its place in the tree; an empty sift is the tree as given. */
export function sift(items, needle) {
  const want = String(needle || '').trim().toLowerCase()
  if (!want) return items || []
  return (items || []).filter((item) => matches(item, want)).map((item) => (
    item.children && item.children.length
      ? { ...item, children: sift(item.children, want) }
      : item
  ))
}
