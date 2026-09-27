/* The expanded table of contents, counted and sifted as a tree. */

import assert from 'node:assert/strict'
import { test } from 'node:test'

import { headings, sift } from '../src/outline.js'

const tree = [
  { label: 'Division 1. Persons', children: [] },
  { label: 'Division 2. Property', children: [
    { label: 'Part 1. Property in General', children: [
      { label: 'Title 3. General Definitions', children: [] },
    ] },
  ] },
  { label: 'PRELIMINARY PROVISIONS', children: [] },
]

test('every heading at every level is counted', () => {
  assert.equal(headings(tree), 5)
  assert.equal(headings([]), 0)
  assert.equal(headings(undefined), 0)
})

test('an empty sift is the tree as given', () => {
  assert.equal(sift(tree, ''), tree)
  assert.equal(sift(tree, '   '), tree)
})

test('a hit deep in the tree keeps its ancestors and drops its cousins', () => {
  const kept = sift(tree, 'definitions')
  assert.deepEqual(kept.map((row) => row.label), ['Division 2. Property'])
  assert.deepEqual(kept[0].children.map((row) => row.label), ['Part 1. Property in General'])
  assert.deepEqual(kept[0].children[0].children.map((row) => row.label), ['Title 3. General Definitions'])
})

test('a parent that hits keeps only the children that hit too', () => {
  const kept = sift(tree, 'property')
  assert.equal(kept.length, 1)
  assert.deepEqual(kept[0].children.map((row) => row.label), ['Part 1. Property in General'])
  assert.deepEqual(kept[0].children[0].children, [])
})

test('the sift ignores case and does not read the unit', () => {
  assert.deepEqual(sift(tree, 'PRELIMINARY').map((row) => row.label), ['PRELIMINARY PROVISIONS'])
  assert.deepEqual(sift(tree, 'nowhere'), [])
})
