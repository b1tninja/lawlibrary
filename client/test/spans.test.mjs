/* The span algebra. Run with `npm --prefix client test`.
 *
 * These are the readings a section carries, as shapes: a note inside a clause
 * inside a subdivision. The offsets stand for words; nothing here is legal
 * text, and no section is quoted.
 */

import assert from 'node:assert/strict'
import { test } from 'node:test'

import { nest, spanClasses } from '../src/spans.js'

const span = (layer, kind, start, end) => ({ layer, kind, start, end })

/* Every offset the tree covers, in order, with the span drawn over it.
 *
 * This walks the tree the way `Piece` renders it: a node's own words are the
 * gaps between its children and the run after the last one, and they are the
 * words its own mark wraps. */
function flat(node, held = []) {
  let cursor = node.start
  node.children.forEach((child) => {
    if (cursor < child.start) held.push([cursor, child.start, node.span])
    flat(child, held)
    cursor = child.end
  })
  if (cursor < node.end) held.push([cursor, node.end, node.span])
  return held
}

function words(node) {
  return flat(node).map(([from, to, held]) => [from, to, held ? held.kind : null])
}

test('a span inside another is a child of it', () => {
  const tree = nest([span('clause', 'exception', 0, 20), span('note', 'citation', 5, 10)], 30)
  assert.equal(tree.children.length, 1, 'only a span makes a node')
  const [clause] = tree.children
  assert.equal(clause.span.kind, 'exception')
  assert.equal(clause.children.length, 1)
  assert.equal(clause.children[0].span.kind, 'citation', 'the note sits inside the clause')
  assert.deepEqual(
    words(tree),
    [[0, 5, 'exception'], [5, 10, 'citation'], [10, 20, 'exception'], [20, 30, null]],
  )
})

test('a span that leaves the one holding it is cut at the boundary', () => {
  // HTML cannot overlap, so the second half carries on as its own node.
  const tree = nest([span('clause', 'condition', 0, 10), span('canon', 'mandatory', 5, 15)], 20)
  const drawn = words(tree)
  assert.deepEqual(
    drawn,
    [[0, 5, 'condition'], [5, 10, 'mandatory'], [10, 15, 'mandatory'], [15, 20, null]],
  )
  const inside = tree.children[0].children
  assert.equal(inside.length, 1, 'the first half sits inside the clause')
  assert.equal(inside[0].span.kind, 'mandatory')
})

test('three readings over one phrase each keep their own length', () => {
  const tree = nest([
    span('note', 'exception', 0, 18),
    span('clause', 'condition', 0, 12),
    span('canon', 'mandatory', 0, 6),
  ], 18)
  let node = tree.children[0]
  const seen = []
  while (node) {
    seen.push([node.span.kind, node.start, node.end])
    node = node.children[0]
  }
  assert.deepEqual(seen, [
    ['exception', 0, 18], ['condition', 0, 12], ['mandatory', 0, 6],
  ])
})

test('the whole run is covered exactly once, whatever the spans', () => {
  const spans = [
    span('note', 'citation', 3, 9),
    span('needle', 'Section', 3, 10),
    span('clause', 'enactment', 0, 7),
    span('canon', 'mandatory', 7, 7),
    span('mention', 'agency', 12, 40),
  ]
  const held = flat(nest(spans, 20))
  assert.equal(held[0][0], 0)
  assert.equal(held[held.length - 1][1], 20)
  held.slice(1).forEach(([from], index) => {
    assert.equal(from, held[index][1], 'no gap and no overlap between nodes')
  })
})

test('a span outside the words is left out', () => {
  assert.deepEqual(words(nest([span('note', 'citation', 40, 50)], 20)), [[0, 20, null]])
  assert.deepEqual(words(nest([span('note', 'citation', -5, -1)], 20)), [[0, 20, null]])
  assert.deepEqual(words(nest([span('note', 'citation', 8, 8)], 20)), [[0, 20, null]])
  assert.deepEqual(words(nest([], 0)), [])
  assert.deepEqual(words(nest(null, 5)), [[0, 5, null]])
})

test('a span reaching past the end stops at the last word', () => {
  const tree = nest([span('note', 'citation', 5, 500)], 10)
  assert.deepEqual(words(tree), [[0, 5, null], [5, 10, 'citation']])
})

/* What `Piece` puts on the page, as a string. */
function draw(node, text) {
  let out = ''
  let cursor = node.start
  node.children.forEach((child) => {
    if (cursor < child.start) out += text.slice(cursor, child.start)
    out += draw(child, text)
    cursor = child.end
  })
  if (cursor < node.end) out += text.slice(cursor, node.end)
  return out
}

test('a crossing span does not make the words repeat', () => {
  // A span cut at a boundary carries on as a node that begins later than the
  // words a following span opens on. Hanging that following span off the last
  // node touched put it outside its parent, and the run it covered was drawn
  // twice — 471 characters for a 442-character subdivision of CIV 1950.5.
  const text = 'abcdefghijklmnopqrst'
  const spans = [
    { layer: 'clause', kind: 'enactment', start: 0, end: 7 },
    { layer: 'needle', kind: 'Section', start: 3, end: 10 },
    { layer: 'note', kind: 'citation', start: 3, end: 9 },
  ]
  assert.equal(draw(nest(spans, text.length), text), text)
})

test('the words drawn are the words given, whatever the spans', () => {
  // A small deterministic sweep: overlapping, nested, crossing and repeated
  // spans over the same run. The reader must never add or drop a character.
  const text = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let seed = 20260925
  const next = (most) => {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff
    return seed % most
  }
  for (let round = 0; round < 500; round += 1) {
    const spans = []
    for (let n = 0; n < 1 + next(9); n += 1) {
      const start = next(text.length)
      spans.push({
        layer: 'note',
        kind: `k${n}`,
        start,
        end: start + next(text.length - start + 6),
      })
    }
    const tree = nest(spans, text.length)
    assert.equal(draw(tree, text), text, `round ${round}: ${JSON.stringify(spans)}`)
    const inside = (node) => {
      let cursor = node.start
      node.children.forEach((child) => {
        assert.ok(child.start >= node.start && child.end <= node.end, 'a child leaves its parent')
        assert.ok(child.start >= cursor, 'children out of order')
        cursor = child.end
        inside(child)
      })
    }
    inside(tree)
  }
})

test('the legend swatch and the mark are drawn by the same names', () => {
  assert.equal(spanClasses('note', 'cross_reference'), 'lay-note note-cross_reference')
  assert.equal(spanClasses('canon', 'mandatory'), 'lay-canon canon-mandatory')
  // A kind is an enum value, but a class name cannot carry punctuation.
  assert.equal(spanClasses('needle', 'a.b c'), 'lay-needle needle-ab_c'.replace('_', ''))
  assert.equal(spanClasses('note', ''), 'lay-note note-')
})
