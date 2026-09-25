/* The term cloud: the words of one heading, sized by how often they appear.
 *
 * Four families share the drawing — the surface words the library's word
 * classes matched, the annotation kinds it recorded, the acts and codes it
 * saw named, and the bodies. Every count comes from rows the index already
 * wrote, so a chapter answers in one pass.
 *
 * Three readings of the same cloud: `tint` gives a word the colour of the
 * code that uses it most, `rim` stands the codes around it and draws a line
 * to each one, `channels` tints the annotation kinds the way the reader does
 * and draws a line to the words a section carries alongside.
 */

import { useEffect, useMemo, useRef, useState } from 'react'

import { route, useKept } from './api.js'
import './cloud.css'

const FAMILIES = [
  ['term', 'terms'],
  ['note', 'annotations'],
  ['act', 'acts and codes'],
  ['body', 'agencies and bodies'],
]

const FAMILY_WORD = {
  term: 'term',
  note: 'annotation',
  act: 'named act or code',
  body: 'agency or body',
}

/* A note wears the tint the reader already gives it. */
const TINT = {
  citation: '#e6dff5',
  cross_reference: '#e6dff5',
  period: '#d9ead3',
  amount: '#f3e6c4',
  date: '#d0e2f3',
  definition: '#e7f0d8',
  limit: '#f3efc0',
  exception: '#f8e0c8',
  proviso: '#e8e4f8',
  named_act: '#f3e6c4',
  session: '#fde7d0',
  cut: '#f3e6c4',
  case: '#f6d6d6',
  compound: '#f7efe2',
  override: '#f8d0d0',
  occasion: '#e7d4f5',
  short_form: '#f3e6c4',
  antecedent: '#ece6d8',
}

let ruler = null

/* How wide a word will be drawn, before it is placed. */
function measure(words, size, family) {
  if (!ruler) ruler = document.createElement('canvas').getContext('2d')
  const caps = family === 'act' || family === 'body'
  ruler.font = `${family === 'note' ? 'italic ' : ''}${size}px "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif`
  let wide = ruler.measureText(caps ? words.toUpperCase() : words).width
  if (caps) wide = wide * 0.86 + words.length * size * 0.03
  return wide
}

/* The tree the server sent, as the lookups the cloud reads it through. */
function shelve(tree) {
  const byId = {}
  const parent = {}
  const under = {}
  function walk(node, above) {
    byId[node.id] = node
    if (above) parent[node.id] = above.id
    const kids = node.children || []
    if (!kids.length) {
      under[node.id] = [node.id]
    } else {
      kids.forEach((kid) => walk(kid, node))
      under[node.id] = kids.reduce((all, kid) => all.concat(under[kid.id]), [])
    }
  }
  if (tree) walk(tree, null)
  return { byId, parent, under }
}

function trail(shelf, id) {
  const rungs = []
  let here = id
  while (here) {
    if (shelf.byId[here]) rungs.unshift(shelf.byId[here])
    here = shelf.parent[here]
  }
  return rungs
}

/* Every word under one heading, with the sections and codes that carry it.
 *
 * The size is the count in this scope. The codes are the whole library's,
 * because every section of one heading shares a code and a word only points
 * somewhere by the company it keeps elsewhere. */
function gather(shelf, leaves, id, books) {
  const wanted = new Set(shelf.under[id] || [])
  const here = leaves.filter((leaf) => wanted.has(leaf.id))
  const held = {}
  here.forEach((leaf, at) => {
    FAMILIES.forEach(([family]) => {
      const counted = (leaf.counts && leaf.counts[family]) || {}
      Object.keys(counted).forEach((word) => {
        const key = `${family}|${word}`
        const one = held[key] || (held[key] = {
          key,
          w: family === 'note' ? word.replace(/_/g, ' ') : word,
          raw: word,
          f: family,
          n: 0,
          codes: {},
          leaves: [],
        })
        one.n += counted[word]
        one.codes[leaf.code] = (one.codes[leaf.code] || 0) + counted[word]
        one.leaves.push([at, counted[word]])
      })
    })
  })
  const items = Object.values(held).sort((one, two) => two.n - one.n || one.w.localeCompare(two.w))
  items.forEach((one) => {
    const wide = books && books[one.key]
    if (wide && Object.keys(wide).length) one.codes = wide
    one.top = Object.keys(one.codes).sort((a, b) => one.codes[b] - one.codes[a])[0]
  })
  return { items, byKey: held, leaves: here }
}

/* The words that keep this one company: how many sections they share. */
function beside(bag, one) {
  if (!one) return []
  const mine = new Set(one.leaves.map((row) => row[0]))
  const score = {}
  bag.items.forEach((other) => {
    if (other.key === one.key) return
    let sum = 0
    other.leaves.forEach(([at, many]) => { if (mine.has(at)) sum += Math.min(many, 4) })
    if (sum) score[other.key] = sum
  })
  return Object.keys(score)
    .sort((a, b) => score[b] - score[a])
    .slice(0, 10)
    .map((key) => ({ key, s: score[key] }))
}

/* The other family's words in the same sections. */
function alongside(bag, one, family) {
  const found = {}
  one.leaves.forEach(([at]) => {
    const leaf = bag.leaves[at]
    const counted = (leaf && leaf.counts && leaf.counts[family]) || {}
    Object.keys(counted).forEach((word) => {
      if (`${family}|${word}` === one.key) return
      found[word] = (found[word] || 0) + counted[word]
    })
  })
  return Object.keys(found)
    .sort((a, b) => found[b] - found[a])
    .slice(0, 5)
    .map((word) => ({ w: word, n: found[word], key: `${family}|${word}` }))
}

/* The spiral. A word is placed on the first turn that clears the ones before
 * it, so the big words hold the middle and the rest wind outward. */
function spiral(items, { W, H, s0, s1, rim, count }) {
  const kept = items.slice(0, count)
  const cx = W / 2
  const cy = H / 2
  const ex = rim ? W / 2 - 118 : W / 2 - 6
  const ey = rim ? H / 2 - 54 : H / 2 - 6
  const aspect = ex / ey
  const most = kept.length ? Math.sqrt(kept[0].n) : 1
  const least = kept.length ? Math.sqrt(kept[kept.length - 1].n) : 1
  const boxes = []
  const placed = []
  kept.forEach((one, index) => {
    const share = most === least ? 1 : (Math.sqrt(one.n) - least) / (most - least)
    const size = Math.round(s0 + (s1 - s0) * share)
    const pill = one.f === 'note'
    const padX = pill ? size * 0.32 : 2
    const padY = pill ? size * 0.12 : 0
    const wide = measure(one.w, size, one.f) + padX * 2
    const tall = size * 1.08 + padY * 2
    const turn = (index * 2.4) % (Math.PI * 2)
    for (let step = 0; step < 4200; step += 1) {
      const angle = step * 0.1
      const out = 1.35 * angle
      const x = cx + out * Math.cos(angle + turn) * aspect
      const y = cy + out * Math.sin(angle + turn)
      const left = x - wide / 2
      const top = y - tall / 2
      const inside = rim
        ? [[left, top], [left + wide, top], [left, top + tall], [left + wide, top + tall]]
          .every(([px, py]) => (((px - cx) / ex) ** 2) + (((py - cy) / ey) ** 2) <= 1)
        : left >= 4 && top >= 4 && left + wide <= W - 4 && top + tall <= H - 4
      if (!inside) {
        if (out > Math.max(ex, ey) * 1.2) break
        continue
      }
      const clash = boxes.some((box) => (
        left < box[0] + box[2] + 2 && left + wide + 2 > box[0]
        && top < box[1] + box[3] + 1 && top + tall + 1 > box[1]
      ))
      if (clash) continue
      boxes.push([left, top, wide, tall])
      placed.push({
        one,
        x: Math.round(x * 10) / 10,
        y: Math.round(y * 10) / 10,
        size,
        w: wide,
        h: tall,
        pill,
      })
      break
    }
  })
  return { placed, asked: kept.length, drawn: placed.length }
}

function Tree({ shelf, rows, at, open, onToggle, onPick }) {
  return (
    <nav className="tc-tree" aria-label="Scope" style={{ fontSize: '0.88rem', minWidth: 0 }}>
      <h2 className="tc-head">Scope</h2>
      {rows.map((row) => {
        const node = shelf.byId[row.id]
        const kids = (node.children || []).length > 0
        const shown = open.has(row.id)
        return (
          <div
            key={row.id}
            className="tc-row"
            data-depth={String(row.depth)}
            aria-current={row.id === at ? 'true' : 'false'}
          >
            <button
              type="button"
              className="tc-caret"
              aria-label={kids ? (shown ? 'Close' : 'Open') : ''}
              onClick={(event) => { event.stopPropagation(); if (kids) onToggle(row.id) }}
            >
              {kids ? (shown ? '▾' : '▸') : ''}
            </button>
            <button type="button" className="tc-rl" title={node.label} onClick={() => onPick(row.id)}>
              {node.label}
            </button>
            <span className="tc-count">{row.count}</span>
          </div>
        )
      })}
    </nav>
  )
}

function Card({ bag, one, shelf, at, codes, held, onLetGo, onPick, onOpen }) {
  const books = Object.keys(one.codes).sort((a, b) => one.codes[b] - one.codes[a])
  const most = one.codes[books[0]] || 1
  const names = Object.keys(codes).find((code) => codes[code] === one.w)
  const bodies = alongside(bag, one, 'body').slice(0, 3)
  const acts = alongside(bag, one, 'act').slice(0, 3)
  const near = beside(bag, one).slice(0, 6)
  const where = one.leaves.slice().sort((a, b) => b[1] - a[1]).slice(0, 4)
  const node = shelf.byId[at]
  return (
    <div style={{ animation: 'tcCard .16s ease-out' }}>
      <p className="tc-fam">
        {FAMILY_WORD[one.f]}
        {held ? (
          <button type="button" className="tc-letgo" onClick={onLetGo} aria-label="Let go">
            {'×'}
          </button>
        ) : null}
      </p>
      <h2 className="tc-word">{one.w}</h2>
      <p className="tc-sum">
        {`${one.n} ${one.n === 1 ? 'time' : 'times'} in ${one.leaves.length} ${one.leaves.length === 1 ? 'section' : 'sections'} of ${node ? node.label : ''}`}
      </p>
      {names ? (
        <p className="tc-names">
          <svg width="10" height="10" aria-hidden="true">
            <rect className="sw" data-code={names} width="10" height="10" rx="2" />
          </svg>
          <span>Names the code <strong>{names}</strong></span>
        </p>
      ) : null}
      <h3>Codes that use it</h3>
      {books.slice(0, 5).map((code) => (
        <div key={code} className="tc-bar" title={codes[code] || code}>
          <span className="tc-code">{code}</span>
          <svg width="100%" height="6" aria-hidden="true">
            <rect className="track" width="100%" height="6" rx="3" />
            <rect
              className="bar"
              data-code={code}
              width={`${Math.max(4, Math.round((100 * one.codes[code]) / most))}%`}
              height="6"
              rx="3"
            />
          </svg>
          <span className="tc-n">{one.codes[code]}</span>
        </div>
      ))}
      {bodies.length ? (
        <>
          <h3>Bodies beside it</h3>
          {bodies.map((row) => (
            <button key={row.key} type="button" className="tc-beside" onClick={() => onPick(row.key)}>
              <span>{row.w}</span>
              <span className="tc-n">{row.n}</span>
            </button>
          ))}
        </>
      ) : null}
      {acts.length ? (
        <>
          <h3>Acts and codes beside it</h3>
          {acts.map((row) => (
            <button key={row.key} type="button" className="tc-beside" onClick={() => onPick(row.key)}>
              <span>{row.w}</span>
              <span className="tc-n">{row.n}</span>
            </button>
          ))}
        </>
      ) : null}
      {near.length ? (
        <>
          <h3>Travels with</h3>
          <div className="tc-near">
            {near.map((row) => (
              <button key={row.key} type="button" onClick={() => onPick(row.key)}>
                {bag.byKey[row.key].w}
              </button>
            ))}
          </div>
        </>
      ) : null}
      <h3>Where it appears</h3>
      {where.map(([at2, many]) => {
        const leaf = bag.leaves[at2]
        return (
          <button
            key={leaf.id}
            type="button"
            className="tc-beside"
            onClick={() => onOpen(leaf.code, leaf.num)}
          >
            <span>{leaf.id}</span>
            <span className="tc-n">{many}</span>
          </button>
        )
      })}
    </div>
  )
}

const SIZES = { page: [40, 60, 90], panel: [30, 45, 70] };

export function TermCloud({
  url, variant = 'tint', mode = 'page', theme = 'paper', words, onOpen,
}) {
  const [at, setAt] = useState('')
  const [open, setOpen] = useState(() => new Set())
  const [fam, setFam] = useState({ term: true, note: true, act: true, body: true })
  const [many, setMany] = useState(null)
  const [over, setOver] = useState(null)
  const [held, setHeld] = useState(null)
  const here = useRef(false)

  /* Three readings of one heading ask for it once: the counts do not change
   * while the page is open. */
  const body = useKept(route('/cloud', { url }), null)
  const loading = !body
  const shelf = useMemo(() => shelve(body && body.found ? body.tree : null), [body])
  const leaves = (body && body.leaves) || []
  const codes = (body && body.codes) || {}
  const root = body && body.found ? body.tree.id : ''
  const scope = shelf.byId[at] ? at : root

  useEffect(() => {
    if (!root) return
    setAt(root)
    setOpen(new Set(trail(shelf, root).map((node) => node.id)))
    setHeld(null)
    setOver(null)
  }, [root])

  const bag = useMemo(
    () => (scope
      ? gather(shelf, leaves, scope, (body && body.books) || null)
      : { items: [], byKey: {}, leaves: [] }),
    [shelf, leaves, scope, body],
  )
  const count = many || words || (mode === 'panel' ? 45 : 60)
  const sizes = SIZES[mode] || SIZES.page
  const board = mode === 'panel'
    ? { W: 640, H: 440, s0: 12, s1: 40 }
    : { W: 880, H: 540, s0: 13, s1: 58 }
  const shown = useMemo(
    () => spiral(bag.items.filter((one) => fam[one.f]), {
      ...board, rim: variant === 'rim', count,
    }),
    [bag, fam, variant, count, mode],
  )

  const focusKey = held || over
  const focus = focusKey ? bag.byKey[focusKey] : null
  const near = useMemo(() => beside(bag, focus), [bag, focusKey])
  const nearSet = useMemo(() => new Set(near.map((row) => row.key)), [near])
  const nearMost = near.length ? near[0].s : 1
  const where = {}
  shown.placed.forEach((spot) => { where[spot.one.key] = spot })

  function stateOf(key) {
    if (!focus) return 'idle'
    if (key === focus.key) return 'on'
    return nearSet.has(key) ? 'rel' : 'dim'
  }
  function openSection(code, num) {
    if (onOpen) onOpen(code, num)
  }

  /* The keys work while the pointer is over the cloud, so a page holding one
   * beside other things keeps its own. */
  const rows = []
  if (root) {
    const visit = (node, depth) => {
      const kids = node.children || []
      const counted = (shelf.under[node.id] || []).length
      rows.push({ id: node.id, depth, count: counted })
      if (kids.length && open.has(node.id)) kids.forEach((kid) => visit(kid, depth + 1))
    }
    visit(shelf.byId[root], 0)
  }

  useEffect(() => {
    function onKey(event) {
      if (!here.current || mode !== 'page') return
      const tag = (event.target && event.target.tagName) || ''
      if (/INPUT|TEXTAREA|SELECT/.test(tag) || event.metaKey || event.ctrlKey || event.altKey) return
      const listed = rows.map((row) => row.id)
      const place = listed.indexOf(scope)
      const node = shelf.byId[scope]
      if (event.key === 'ArrowDown' && place >= 0 && place < listed.length - 1) {
        event.preventDefault()
        setAt(listed[place + 1])
      } else if (event.key === 'ArrowUp' && place > 0) {
        event.preventDefault()
        setAt(listed[place - 1])
      } else if (event.key === 'ArrowRight') {
        event.preventDefault()
        const kids = (node && node.children) || []
        if (kids.length) {
          if (open.has(scope)) setAt(kids[0].id)
          else setOpen((was) => new Set(was).add(scope))
        }
      } else if (event.key === 'ArrowLeft') {
        event.preventDefault()
        if (open.has(scope) && (node.children || []).length) {
          setOpen((was) => { const next = new Set(was); next.delete(scope); return next })
        } else if (shelf.parent[scope]) setAt(shelf.parent[scope])
      } else if (event.key === 'Escape') setHeld(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  if (loading && !body) return <p className="thin">Counting the words.</p>
  if (!body || !body.found) return <p className="miss">That heading is not in the index.</p>

  const node = shelf.byId[scope] || shelf.byId[root]
  const famCounts = {}
  bag.items.forEach((one) => { famCounts[one.f] = (famCounts[one.f] || 0) + 1 })
  const ladder = trail(shelf, scope)
  const rim = variant === 'rim'
  const books = Object.keys(codes).filter((code) => bag.items.some((one) => one.top === code))
  const rimPoints = rim
    ? books.map((code, index) => {
      const angle = -Math.PI / 2 + ((index * 2 * Math.PI) / Math.max(1, books.length))
      return {
        code,
        x: Math.round((board.W / 2) + ((board.W / 2) - 52) * Math.cos(angle)),
        y: Math.round((board.H / 2) + ((board.H / 2) - 20) * Math.sin(angle)),
      }
    })
    : []
  let lines = []
  if (rim && focus && where[focus.key]) {
    const spot = where[focus.key]
    lines = rimPoints.filter((point) => focus.codes[point.code]).map((point) => {
      const dx = point.x - spot.x
      const dy = point.y - spot.y
      const far = Math.hypot(dx, dy) || 1
      return {
        x1: spot.x,
        y1: spot.y,
        x2: Math.round(point.x - ((dx / far) * 14)),
        y2: Math.round(point.y - ((dy / far) * 14)),
        sw: (1 + ((6 * focus.codes[point.code]) / focus.n)).toFixed(1),
        code: point.code,
      }
    })
  } else if (variant === 'channels' && focus && where[focus.key]) {
    const spot = where[focus.key]
    lines = near.filter((row) => where[row.key]).map((row) => ({
      x1: spot.x,
      y1: spot.y,
      x2: where[row.key].x,
      y2: where[row.key].y,
      sw: (0.8 + ((2.4 * row.s) / nearMost)).toFixed(1),
      code: '',
    }))
  }

  return (
    <div
      className="tc"
      data-theme={theme}
      data-variant={variant}
      data-mode={mode}
      onMouseEnter={() => { here.current = true }}
      onMouseLeave={() => { here.current = false; setOver(null) }}
    >
      <div className="tc-grid">
        <Tree
          shelf={shelf}
          rows={rows}
          at={scope}
          open={open}
          onToggle={(id) => setOpen((was) => {
            const next = new Set(was)
            if (next.has(id)) next.delete(id)
            else next.add(id)
            return next
          })}
          onPick={(id) => {
            setOpen((was) => {
              const next = new Set(was)
              trail(shelf, id).forEach((one) => next.add(one.id))
              return next
            })
            setAt(id)
            setHeld(null)
            setOver(null)
          }}
        />

        <main style={{ minWidth: 0 }}>
          <div className="tc-ladder">
            <span className="tc-lead">Scope</span>
            {ladder.map((one) => (
              <button
                key={one.id}
                type="button"
                aria-pressed={one.id === scope}
                title={one.label}
                onClick={() => { setAt(one.id); setHeld(null) }}
              >
                {one.unit === 'section' || one.unit === 'code'
                  ? one.label
                  : one.label.replace(/^(\w+ [\w.]+)\..*$/, '$1')}
              </button>
            ))}
          </div>

          <div className="tc-title">
            <h1>{node.label}</h1>
            <span className="tc-sum">
              {`${bag.leaves.length} ${bag.leaves.length === 1 ? 'section' : 'sections'}, ${bag.items.length} distinct words${shown.drawn < shown.asked ? `, ${shown.drawn} drawn` : ''}`}
            </span>
          </div>

          <div className="tc-picks">
            {FAMILIES.map(([family, label]) => (
              <button
                key={family}
                type="button"
                aria-pressed={!!fam[family]}
                onClick={() => { setFam((was) => ({ ...was, [family]: !was[family] })); setHeld(null) }}
              >
                {label}
                <span className="tc-n">{famCounts[family] || 0}</span>
              </button>
            ))}
            <span className="tc-sizes">
              {sizes.map((size) => (
                <button
                  key={size}
                  type="button"
                  aria-pressed={count === size}
                  title="Words drawn"
                  onClick={() => { setMany(size); setHeld(null) }}
                >
                  {size}
                </button>
              ))}
            </span>
          </div>

          <svg
            className="tc-cloud"
            viewBox={`0 0 ${board.W} ${board.H}`}
            width="100%"
            role="img"
            aria-label={`Terms and names in ${node.label}`}
            onClick={() => setHeld(null)}
            style={{ display: 'block', overflow: 'visible' }}
          >
            <g>
              {rimPoints.map((point) => {
                const total = bag.items.reduce((sum, one) => sum + (one.codes[point.code] || 0), 0)
                return (
                  <text
                    key={point.code}
                    className="rim"
                    x={point.x}
                    y={point.y}
                    data-code={point.code}
                    data-on={String(!!(focus && focus.codes[point.code]))}
                    data-zero={String(!total)}
                  >
                    <title>{codes[point.code] || point.code}</title>
                    {point.code}
                    <tspan dx={4} fontSize={11}>{total || ''}</tspan>
                  </text>
                )
              })}
            </g>
            <g>
              {lines.map((line, index) => (
                <line
                  key={index}
                  className="ln"
                  x1={line.x1}
                  y1={line.y1}
                  x2={line.x2}
                  y2={line.y2}
                  strokeWidth={line.sw}
                  data-code={line.code || undefined}
                />
              ))}
            </g>
            <g>
              {variant === 'channels' ? shown.placed.filter((spot) => spot.pill).map((spot, index) => (
                <rect
                  key={index}
                  className="pill"
                  x={Math.round(spot.x - (spot.w / 2))}
                  y={Math.round(spot.y - (spot.h / 2))}
                  width={Math.round(spot.w)}
                  height={Math.round(spot.h)}
                  rx={Math.round(spot.h / 4)}
                  fill={TINT[spot.one.raw] || '#efe8da'}
                  data-state={stateOf(spot.one.key)}
                />
              )) : null}
            </g>
            <g>
              {shown.placed.map((spot) => (
                <text
                  key={spot.one.key}
                  className="w"
                  x={spot.x}
                  y={spot.y}
                  fontSize={spot.size}
                  data-f={spot.one.f}
                  data-code={spot.one.top}
                  data-state={stateOf(spot.one.key)}
                  data-pill={String(variant === 'channels' && spot.pill)}
                  onMouseEnter={() => setOver(spot.one.key)}
                  onMouseLeave={() => setOver(null)}
                  onClick={(event) => {
                    event.stopPropagation()
                    setHeld((was) => (was === spot.one.key ? null : spot.one.key))
                  }}
                >
                  <title>
                    {`${spot.one.w} — ${spot.one.n} in ${spot.one.leaves.length} ${spot.one.leaves.length === 1 ? 'section' : 'sections'}`}
                  </title>
                  {spot.one.w}
                </text>
              ))}
            </g>
          </svg>

          {variant === 'tint' && books.length ? (
            <div className="tc-key">
              <span className="tc-lead">Colour is the code that uses it most</span>
              {books.map((code) => (
                <span key={code} title={codes[code] || code}>
                  <svg width="10" height="10" aria-hidden="true">
                    <rect className="sw" data-code={code} width="10" height="10" rx="2" />
                  </svg>
                  {code}
                </span>
              ))}
            </div>
          ) : null}

          <p className="tc-foot">
            {`Counted from the rows the index wrote. Size is how often the word appears in this scope${body.more ? `, and ${body.more} further sections were left out` : ''}.`}
          </p>
        </main>

        <aside className="tc-aside">
          {focus ? (
            <Card
              bag={bag}
              one={focus}
              shelf={shelf}
              at={scope}
              codes={codes}
              held={!!held}
              onLetGo={() => setHeld(null)}
              onPick={(key) => setHeld(key)}
              onOpen={openSection}
            />
          ) : (
            <>
              <p className="tc-hint">
                Hover a word to see what travels with it. Click to hold it here with the codes
                and bodies that use it.
              </p>
              <p className="tc-hint thin">
                {mode === 'page'
                  ? 'With the pointer over this view: ↑ ↓ move through the headings, ← → close and open them, esc lets a word go.'
                  : 'Widen the scope with the chips above to see the chapter, the code, or the whole book.'}
              </p>
            </>
          )}
        </aside>
      </div>
    </div>
  )
}

const READINGS = [
  ['tint', '1a', 'Tinted by code',
    'Each word takes the colour of the code that uses it most. Unrelated words fade on hover.'],
  ['rim', '1b', 'Codes on the rim',
    'The codes sit around the cloud. A held or hovered word draws a line to each code that uses it, as thick as its share.'],
  ['channels', '1c', "Reader's channels",
    'Annotation kinds wear the reader’s own tints. A word draws lines to the words it shares sections with; codes and bodies are in the card.'],
]

/* The three readings side by side, over the same heading. */
export function Explore({ here, go }) {
  const url = here.url || 'us-ca/civ/division/3/title/5/part/4/chapter/2'
  const open = (code, num) => go(null, `/reader/section/${encodeURIComponent(code)}/${encodeURIComponent(num)}`)
  return (
    <div className="tc-explore">
      <div style={{ maxWidth: '60rem' }}>
        <h1>Term cloud, three ways to show a word&apos;s codes</h1>
        <p>
          All three are scoped to the same heading tree and sized by how often a word appears.
          Hover a word to see what travels with it, click to hold it in the card. They differ in
          how a word points to the codes and bodies that use it.
        </p>
      </div>
      <div className="tc-board">
        {READINGS.map(([variant, tag, name, what]) => (
          <section key={variant} className="tc-one">
            <div className="tc-caption">
              <span className="tc-tag">{tag}</span>
              <strong>{name}</strong>
              <span className="thin">{what}</span>
            </div>
            <div className="tc-frame">
              <TermCloud url={url} variant={variant} mode="page" onOpen={open} />
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
