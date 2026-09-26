/* What a miss says about the edition it read.
 *
 * A section the index does not carry may still be law: the index holds the
 * publication years it was built from. CIV 4600 is in the Civil Code today
 * and is not in the 2011 edition, where the same law sits at CIV 1350.
 */

import assert from 'node:assert/strict'
import { test } from 'node:test'

import { editions } from '../src/place.js'

test('one edition is named by its year', () => {
  assert.equal(editions(['2011']), 'The index holds the 2011 edition.')
})

test('several editions are named as a span, oldest first', () => {
  assert.equal(
    editions(['2025', '2011', '2013']),
    'The index holds the 2011–2025 editions.',
  )
})

test('an index that names no edition says nothing about one', () => {
  assert.equal(editions([]), '')
  assert.equal(editions(null), '')
  assert.equal(editions(undefined), '')
})
