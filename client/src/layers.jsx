/* Layered highlighting: every reading a parser recorded, drawn at once.
 *
 * A span is a layer, a kind, and two offsets into one cut's words. Spans
 * overlap and nest, because the readings do — `Except as provided` is a note,
 * a clause, and a canon over three different lengths of the same phrase — so
 * the text is built as a tree of spans and each layer takes its own channel:
 * a tint for a note, a bar for a clause, a dotted rule for a canon, an
 * underline for a name, a ring for a word class.
 */

import { useContext, useRef, useState } from 'react'

import { local } from './place.js'
import { Reading } from './reading.js'

export const LAYER_WORDS = {
  note: 'notes',
  clause: 'clauses',
  canon: 'canons',
  mention: 'names',
  relation: 'duties',
  needle: 'word classes',
  abbreviation: 'short forms',
}

export const LAYER_ORDER = [
  'note', 'clause', 'canon', 'mention', 'relation', 'abbreviation', 'needle',
]

const OPEN = ['note', 'clause']

/* One tree of spans over one run of words. A span that runs past the end of
 * the span holding it is cut there, so the drawing stays well formed. */
export function nest(spans, length) {
  const root = { start: 0, end: length, span: null, children: [] }
  const stack = [root]
  const queue = (spans || [])
    .filter((span) => span.end > span.start && span.start >= 0)
    .slice()
    .sort((one, two) => (one.start - two.start) || (two.end - one.end))
  queue.forEach((span) => {
    let from = span.start
    const to = Math.min(span.end, length)
    while (from < to) {
      while (stack.length > 1 && stack[stack.length - 1].end <= from) stack.pop()
      const top = stack[stack.length - 1]
      const stop = Math.min(to, top.end)
      if (stop <= from) break
      const node = { start: from, end: stop, span, children: [] }
      top.children.push(node)
      stack.push(node)
      from = stop
    }
  })
  return root
}

function classes(span) {
  const kind = String(span.kind || '').replace(/[^A-Za-z0-9_]/g, '')
  if (span.layer === 'note') return `lay-note note-${kind}`
  return `lay-${span.layer} ${span.layer}-${kind}`
}

function Piece({ node, text, code, path }) {
  const { look, go } = useContext(Reading)
  const wait = useRef(0)
  const inside = []
  let cursor = node.start
  node.children.forEach((child, index) => {
    if (cursor < child.start) {
      inside.push(<span key={`t${index}`}>{text.slice(cursor, child.start)}</span>)
    }
    inside.push(<Piece key={`s${index}`} node={child} text={text} code={code} path={path} />)
    cursor = child.end
  })
  if (cursor < node.end) inside.push(<span key="tail">{text.slice(cursor, node.end)}</span>)
  const span = node.span
  if (!span) return inside
  const detail = { ...span, code, path, term: span.text }
  return (
    <mark
      className={span.href ? `${classes(span)} open` : classes(span)}
      data-layer={span.layer}
      data-kind={span.kind}
      role={span.href ? 'link' : undefined}
      title={`${span.layer} ${String(span.kind).replace(/_/g, ' ')}${span.target ? ` — ${span.target}` : ''}${span.href ? '. Click to open it, hover to read it.' : ''}`}
      onMouseEnter={(event) => {
        const at = { x: event.clientX, y: event.clientY }
        window.clearTimeout(wait.current)
        wait.current = window.setTimeout(() => look({ ...detail, ...at }), 500)
      }}
      onMouseLeave={() => window.clearTimeout(wait.current)}
      onClick={(event) => {
        event.stopPropagation()
        window.clearTimeout(wait.current)
        if (span.href) {
          go(event, local(span.href))
          return
        }
        look({ ...detail, x: event.clientX, y: event.clientY })
      }}
    >
      {inside}
    </mark>
  )
}

/* The words of one cut with every span the reader has left on. */
export function Layered({ spans, text, code, path }) {
  const body = text || ''
  const { shown } = useContext(Reading)
  const kept = (spans || []).filter((span) => shown.has(span.layer, span.kind))
  if (!kept.length) return <>{body}</>
  return <Piece node={nest(kept, body.length)} text={body} code={code} path={path} />
}

const KEPT = 'reader.layers'

function read() {
  try {
    const held = window.localStorage.getItem(KEPT)
    const body = held ? JSON.parse(held) : null
    if (!body) return { layers: OPEN.slice(), off: [] }
    return { layers: body.layers || OPEN.slice(), off: body.off || [] }
  } catch (error) {
    return { layers: OPEN.slice(), off: [] }
  }
}

function write(state) {
  try {
    window.localStorage.setItem(KEPT, JSON.stringify(state))
  } catch (error) { /* a private window keeps nothing */ }
}

/* Which layers are drawn, and which kinds inside them are set aside. A note
 * is on when the reader opens the page; the rest are asked for. */
export function useShown() {
  const [state, setState] = useState(read)
  const shown = {
    layers: state.layers,
    has(layer, kind) {
      return state.layers.includes(layer) && !state.off.includes(`${layer}.${kind}`)
    },
    layer(name) {
      return state.layers.includes(name)
    },
    kind(layer, kind) {
      return !state.off.includes(`${layer}.${kind}`)
    },
  }
  function toggleLayer(name) {
    setState((was) => {
      const layers = was.layers.includes(name)
        ? was.layers.filter((item) => item !== name)
        : was.layers.concat(name)
      const next = { ...was, layers }
      write(next)
      return next
    })
  }
  function toggleKind(layer, kind) {
    const key = `${layer}.${kind}`
    setState((was) => {
      const off = was.off.includes(key)
        ? was.off.filter((item) => item !== key)
        : was.off.concat(key)
      const next = { ...was, off }
      write(next)
      return next
    })
  }
  function onlyKind(layer, kind) {
    setState((was) => {
      const next = { layers: [layer], off: was.off.filter((item) => item !== `${layer}.${kind}`) }
      write(next)
      return next
    })
  }
  return [shown, { toggleLayer, toggleKind, onlyKind }]
}

function sample(layer, kind) {
  const word = String(kind).replace(/_/g, ' ')
  if (layer === 'note') return <mark className={`lay-note note-${kind}`}>{word}</mark>
  return <mark className={`lay-${layer} ${layer}-${kind}`}>{word}</mark>
}

/* The legend, and the count of every reading on this section. A kind with no
 * span here is not listed, so the panel is what the words actually carry. */
export function Layers({ counts, shown, act, order }) {
  const [open, setOpen] = useState(false)
  const layers = (order && order.length ? order : LAYER_ORDER)
    .filter((name) => (counts || {})[name] || shown.layer(name))
  if (!layers.length) return null
  return (
    <section className="layers">
      <p className="layers-bar">
        <span className="thin">Readings</span>
        {layers.map((name) => {
          const inside = (counts || {})[name] || {}
          const many = Object.keys(inside).reduce((sum, kind) => sum + inside[kind], 0)
          return (
            <button
              key={name}
              type="button"
              className={shown.layer(name) ? 'layer on' : 'layer'}
              aria-pressed={shown.layer(name)}
              onClick={() => act.toggleLayer(name)}
              title={`${LAYER_WORDS[name] || name}: ${many}`}
            >
              {LAYER_WORDS[name] || name}
              <span className="thin">{many}</span>
            </button>
          )
        })}
        <button
          type="button"
          className="plain"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? 'fewer' : 'each kind'}
        </button>
      </p>
      {open ? (
        <div className="layer-kinds">
          {layers.map((name) => {
            const inside = (counts || {})[name] || {}
            const kinds = Object.keys(inside).sort()
            if (!kinds.length) return null
            return (
              <p key={name} className="layer-row">
                <span className="thin">{LAYER_WORDS[name] || name}</span>
                {kinds.map((kind) => (
                  <button
                    key={kind}
                    type="button"
                    className={shown.has(name, kind) ? 'kind on' : 'kind'}
                    aria-pressed={shown.has(name, kind)}
                    onClick={() => act.toggleKind(name, kind)}
                    onDoubleClick={() => act.onlyKind(name, kind)}
                    title={'Click to set aside. Double-click for this one alone.'}
                  >
                    {sample(name, kind)}
                    <span className="thin">{inside[kind]}</span>
                  </button>
                ))}
              </p>
            )
          })}
        </div>
      ) : null}
    </section>
  )
}
