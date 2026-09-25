/* The citation graph as inline SVG.
 *
 * The edge list is the drawing: `source`, `target`, and `label`, with the href
 * that opens each end. A node click opens the next section, which the mermaid
 * string cannot do. Mermaid stays the static export.
 *
 * A kind keeps one colour and one stroke pattern, so the two readings agree and
 * neither depends on colour alone. Every node carries its own label.
 */

import { useMemo, useState } from 'react'

import { local } from './place.js'

const KINDS = [
  { stroke: '#1f5aa8', dash: '' },
  { stroke: '#a35a12', dash: '7 4' },
  { stroke: '#2f7d4f', dash: '2 3' },
]
const OTHER = { stroke: '#8a8172', dash: '1 4' }

const INK = '#1a1814'
const MUTED = '#6b6458'
const PAPER = '#fbf8f1'
const RULE = '#c8c0b0'

function width(label) {
  return Math.max(54, Math.min(210, String(label || '').length * 6.6 + 16))
}

function kinds(edges) {
  const order = []
  edges.forEach((edge) => {
    const label = edge.label || 'cites'
    if (!order.includes(label)) order.push(label)
  })
  const paint = {}
  order.forEach((label, index) => {
    paint[label] = index < KINDS.length ? KINDS[index] : OTHER
  })
  return { order, paint }
}

/* One row per node, with the hop it was reached on. A node the walk named but
 * did not open keeps `found` false. */
function collect(edges, nodes) {
  const rows = new Map()
  function put(id, extra) {
    if (!id) return
    const was = rows.get(id) || { id, label: id, href: '', found: true, hop: null, out: 0, in: 0 }
    rows.set(id, { ...was, ...(extra || {}) })
  }
  const listed = nodes || []
  listed.forEach((node) => put(node.id, {
    label: node.label || node.citation || node.id,
    href: node.href || '',
    found: node.found !== false,
    hop: typeof node.hop === 'number' ? node.hop : null,
  }))
  edges.forEach((edge) => {
    put(edge.source, { href: rows.has(edge.source) ? rows.get(edge.source).href : (edge.source_href || '') })
    put(edge.target, { href: rows.has(edge.target) ? rows.get(edge.target).href : (edge.target_href || '') })
    if (edge.source_href && rows.get(edge.source) && !rows.get(edge.source).href) {
      rows.get(edge.source).href = edge.source_href
    }
    if (edge.target_href && rows.get(edge.target) && !rows.get(edge.target).href) {
      rows.get(edge.target).href = edge.target_href
    }
  })
  edges.forEach((edge) => {
    const from = rows.get(edge.source)
    const to = rows.get(edge.target)
    if (from) from.out += 1
    if (to) to.in += 1
  })
  return rows
}

/* The hop each node sits on. A walk that named its hops keeps them; otherwise
 * the first reach wins, so a book that cites back does not deepen forever. */
function layers(rows, edges) {
  const depth = new Map()
  rows.forEach((row, id) => { if (row.hop != null) depth.set(id, row.hop) })
  if (depth.size === rows.size) return depth
  const out = new Map()
  const incoming = new Set()
  edges.forEach((edge) => {
    if (edge.source === edge.target) return
    if (!out.has(edge.source)) out.set(edge.source, [])
    out.get(edge.source).push(edge.target)
    incoming.add(edge.target)
  })
  const queue = []
  rows.forEach((_row, id) => {
    if (!depth.has(id) && !incoming.has(id)) { depth.set(id, 0); queue.push(id) }
  })
  if (!queue.length) {
    const first = rows.keys().next().value
    if (first !== undefined) { depth.set(first, 0); queue.push(first) }
  }
  while (queue.length) {
    const id = queue.shift()
    const kids = out.get(id) || []
    kids.forEach((kid) => {
      if (!depth.has(kid)) { depth.set(kid, (depth.get(id) || 0) + 1); queue.push(kid) }
    })
  }
  rows.forEach((_row, id) => { if (!depth.has(id)) depth.set(id, 0) })
  return depth
}

function layered(rows, depth) {
  const byLayer = new Map()
  Array.from(rows.values())
    .sort((one, two) => (depth.get(one.id) - depth.get(two.id)) || one.id.localeCompare(two.id))
    .forEach((row) => {
      const layer = depth.get(row.id) || 0
      if (!byLayer.has(layer)) byLayer.set(layer, [])
      byLayer.get(layer).push(row)
    })
  const place = new Map()
  let tallest = 1
  byLayer.forEach((column, layer) => {
    tallest = Math.max(tallest, column.length)
    column.forEach((row, index) => {
      place.set(row.id, { x: 16 + layer * 236, y: 22 + index * 44, w: width(row.label), h: 24 })
    })
  })
  return {
    place,
    box: [0, 0, 16 + byLayer.size * 236 + 40, 22 + tallest * 44 + 24],
  }
}

function curve(from, to) {
  const ax = from.x + from.w
  const ay = from.y + from.h / 2
  const bx = to.x
  const by = to.y + to.h / 2
  const span = Math.max(30, (bx - ax) / 2)
  return `M ${ax} ${ay} C ${ax + span} ${ay} ${bx - span} ${by} ${bx} ${by}`
}


/* The walk: one column per hop, left to right. A node keeps its own label, so
 * identity never rests on the colour. */
function Walk({ rows, edges, paint, go, here, over, setOver }) {
  const depth = layers(rows, edges)
  const laid = layered(rows, depth)
  const [, , boxWidth, boxHeight] = laid.box
  const touching = (edge) => !over || edge.source === over || edge.target === over
  const labels = Array.from(new Set(edges.map((edge) => edge.label || 'cites')))
  return (
    <div className="graph-frame">
      <svg
        viewBox={`0 0 ${boxWidth} ${boxHeight}`}
        width={boxWidth}
        height={boxHeight}
        role="img"
        aria-label="The sections this walk opened"
      >
        <defs>
          {labels.map((label) => (
            <marker
              key={label}
              id={`head-${label}`}
              viewBox="0 0 8 8"
              refX="7"
              refY="4"
              markerWidth="7"
              markerHeight="7"
              orient="auto"
            >
              <path d="M 0 0 L 8 4 L 0 8 z" fill={(paint[label] || OTHER).stroke} />
            </marker>
          ))}
        </defs>
        {edges.map((edge, index) => {
          const from = laid.place.get(edge.source)
          const to = laid.place.get(edge.target)
          if (!from || !to) return null
          const label = edge.label || 'cites'
          const paints = paint[label] || OTHER
          if (edge.source === edge.target) {
            return (
              <circle
                key={index}
                cx={from.x + from.w + 7}
                cy={from.y + from.h / 2}
                r="4"
                fill="none"
                stroke={paints.stroke}
                strokeWidth="2"
                opacity={touching(edge) ? 0.9 : 0.12}
              />
            )
          }
          return (
            <path
              key={index}
              d={curve(from, to)}
              fill="none"
              stroke={paints.stroke}
              strokeWidth="2"
              strokeDasharray={paints.dash || undefined}
              markerEnd={`url(#head-${label})`}
              opacity={touching(edge) ? 0.85 : 0.1}
            >
              <title>{`${edge.source} ${label} ${edge.target}`}</title>
            </path>
          )
        })}
        {Array.from(rows.values()).map((row) => {
          const at = laid.place.get(row.id)
          if (!at) return null
          const target = local(row.href)
          const focus = row.id === here
          return (
            <g
              key={row.id}
              className={target ? 'node open' : 'node'}
              onMouseEnter={() => setOver(row.id)}
              onMouseLeave={() => setOver('')}
              onClick={target ? (event) => go(event, target) : undefined}
              opacity={!over || over === row.id ? 1 : 0.45}
            >
              <rect
                x={at.x}
                y={at.y}
                width={at.w}
                height={at.h}
                rx="3"
                fill={focus ? '#f3e6c4' : PAPER}
                stroke={row.found ? INK : RULE}
                strokeDasharray={row.found ? undefined : '3 3'}
                strokeWidth={focus ? 2 : 1}
              />
              <text
                x={at.x + at.w / 2}
                y={at.y + 16}
                textAnchor="middle"
                fontSize="12"
                fill={row.found ? INK : MUTED}
              >
                {row.label}
              </text>
              <title>
                {`${row.label}${row.found ? '' : ' (not opened)'} — ${row.out} out, ${row.in} in`}
              </title>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

const RAMP = [232, 238, 247, 20, 56, 107]

/* Counts here are heavily skewed: a book cites itself thousands of times and
 * another book a dozen. A log step keeps the dozen visible. */
function shade(weight, most) {
  const step = most > 1 ? Math.log1p(weight) / Math.log1p(most) : 1
  const parts = [0, 1, 2].map((index) => Math.round(
    RAMP[index] + (RAMP[index + 3] - RAMP[index]) * step,
  ))
  return `rgb(${parts[0]}, ${parts[1]}, ${parts[2]})`
}

/* Every pair at once. A hairball of a few hundred edges says nothing, so a
 * dense graph is a grid: the row cites, the column is cited, and the shade is
 * how many stored citations that pair holds. */
function Matrix({ rows, edges, go, over, setOver }) {
  const books = Array.from(rows.keys()).sort()
  const cell = 17
  const gutter = 92
  const weights = new Map()
  edges.forEach((edge) => {
    const key = `${edge.source}|${edge.target}`
    weights.set(key, (weights.get(key) || 0) + (edge.weight || 1))
  })
  const most = Math.max(1, ...weights.values())
  const size = gutter + books.length * cell + 12
  const lit = (name) => !over || over === name
  return (
    <div className="graph-frame">
      <svg
        viewBox={`0 0 ${size} ${size}`}
        width={size}
        height={size}
        role="img"
        aria-label="Which book cites which"
      >
        {books.map((name, index) => (
          <text
            key={`top-${name}`}
            x={gutter + index * cell + cell / 2}
            y={gutter - 6}
            fontSize="10"
            textAnchor="start"
            fill={lit(name) ? INK : MUTED}
            transform={`rotate(-60 ${gutter + index * cell + cell / 2} ${gutter - 6})`}
            onMouseEnter={() => setOver(name)}
            onMouseLeave={() => setOver('')}
          >
            {name}
          </text>
        ))}
        {books.map((name, index) => {
          const target = local((rows.get(name) || {}).href)
          return (
            <text
              key={`side-${name}`}
              x={gutter - 6}
              y={gutter + index * cell + 12}
              fontSize="10"
              textAnchor="end"
              fill={lit(name) ? INK : MUTED}
              className={target ? 'side open' : 'side'}
              onMouseEnter={() => setOver(name)}
              onMouseLeave={() => setOver('')}
              onClick={target ? (event) => go(event, target) : undefined}
            >
              {name}
            </text>
          )
        })}
        {books.map((source, down) => books.map((target, across) => {
          const weight = weights.get(`${source}|${target}`) || 0
          if (!weight) return null
          return (
            <rect
              key={`${source}-${target}`}
              x={gutter + across * cell + 1}
              y={gutter + down * cell + 1}
              width={cell - 2}
              height={cell - 2}
              fill={shade(weight, most)}
              opacity={lit(source) || lit(target) ? 1 : 0.2}
            >
              <title>{`${source} cites ${target}, ${weight}`}</title>
            </rect>
          )
        }))}
        <rect
          x={gutter}
          y={gutter}
          width={books.length * cell}
          height={books.length * cell}
          fill="none"
          stroke={RULE}
        />
      </svg>
      <p className="graph-bar">
        <span className="thin">row cites column</span>
        <span className="graph-kind">
          <svg width="90" height="9" aria-hidden="true">
            {[1, 2, 3, 4, 5, 6].map((step) => (
              <rect
                key={step}
                x={(step - 1) * 15}
                y="0"
                width="15"
                height="9"
                fill={shade((step * most) / 6, most)}
              />
            ))}
          </svg>
          {`1 to ${most}`}
        </span>
      </p>
    </div>
  )
}

/* One drawing of an edge list. `here` is the node the reader came from. A
 * walk is a few nodes and reads as a tree; a whole book-to-book relation is
 * hundreds of edges and reads as a grid. */
export function Graph({ edges, nodes, go, here, empty }) {
  const [over, setOver] = useState('')
  const [only, setOnly] = useState('')
  const kept = useMemo(() => {
    const needle = only.trim().toLowerCase()
    const listed = (edges || []).filter((edge) => edge.source && edge.target)
    if (!needle) return listed
    return listed.filter((edge) => (
      String(edge.source).toLowerCase().includes(needle)
      || String(edge.target).toLowerCase().includes(needle)
    ))
  }, [edges, only])
  const rows = useMemo(() => collect(kept, nodes), [kept, nodes])
  const paint = useMemo(() => kinds(kept), [kept])
  if (!kept.length && !rows.size) {
    return <p className="thin">{empty || 'No edge of that kind is stored.'}</p>
  }
  const dense = rows.size > 15 || kept.length > 60
  return (
    <div className="graph">
      <p className="graph-bar">
        <label>
          Keep
          <input
            value={only}
            placeholder="a book or a section"
            onChange={(event) => setOnly(event.target.value)}
          />
        </label>
        <span className="thin">{`${rows.size} nodes, ${kept.length} edges`}</span>
        {dense ? null : (
          <span className="graph-legend">
            {paint.order.map((label) => (
              <span key={label} className="graph-kind">
                <svg width="26" height="8" aria-hidden="true">
                  <line
                    x1="1"
                    y1="4"
                    x2="25"
                    y2="4"
                    stroke={paint.paint[label].stroke}
                    strokeWidth="2"
                    strokeDasharray={paint.paint[label].dash || undefined}
                  />
                </svg>
                {label}
              </span>
            ))}
          </span>
        )}
      </p>
      {dense
        ? <Matrix rows={rows} edges={kept} go={go} over={over} setOver={setOver} />
        : (
          <Walk
            rows={rows}
            edges={kept}
            paint={paint.paint}
            go={go}
            here={here}
            over={over}
            setOver={setOver}
          />
        )}
      <details className="graph-table">
        <summary>{`The same edges as a list (${kept.length})`}</summary>
        <ol className="refs">
          {kept.slice(0, 400).map((edge, index) => (
            <li key={index} className={`ref-${edge.label || 'cites'}`}>
              <span className="ref-source">{edge.source}</span>
              {local(edge.target_href)
                ? (
                  <a
                    href={local(edge.target_href)}
                    onClick={(event) => go(event, local(edge.target_href))}
                  >
                    {edge.target}
                  </a>
                )
                : <span>{edge.target}</span>}
              {edge.weight > 1 ? <span className="thin">{edge.weight}</span> : null}
            </li>
          ))}
        </ol>
      </details>
    </div>
  )
}
