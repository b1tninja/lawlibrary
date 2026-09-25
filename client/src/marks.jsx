/* The reading surface: the marks on a section, the cuts under it, and the card
 * a mark opens.
 *
 * A piece is a slice of the stored text. A piece with a kind is one
 * annotation, and the kind is a `Note` member. The legend is built from the
 * closed set the server sends, so a new note needs no change here.
 */

import { useContext, useEffect, useRef, useState } from 'react'

import { route, useJson } from './api.js'
import { Layered } from './layers.jsx'
import { local } from './place.js'
import { Reading } from './reading.js'

export { Reading }

const HOVER_MS = 450

export const NOTE_WORDS = {
  cross_reference: 'cross reference',
  named_act: 'named act',
  short_form: 'short form',
  case: 'name',
}

export function noteWords(kind) {
  return NOTE_WORDS[kind] || String(kind || '').replace(/_/g, ' ')
}

export function Link({ href, go, title, className, children }) {
  const target = local(href)
  return (
    <a
      href={target}
      className={className}
      title={title}
      onClick={(event) => go(event, target)}
    >
      {children}
    </a>
  )
}

function Mark({ piece, code }) {
  const { shown, look, go } = useContext(Reading)
  const wait = useRef(0)
  const kind = piece.kind
  const off = !shown.has('note', kind)
  const detail = {
    term: piece.text,
    text: piece.text,
    code,
    layer: 'note',
    kind,
    target: piece.title,
    href: piece.href || '',
    detail: { cite: piece.cite || '' },
  }
  const mark = (
    <mark
      className={off ? `note-${kind} off` : `note-${kind}`}
      data-note={kind}
      data-cite={piece.cite || undefined}
      title={piece.title}
      onMouseEnter={(event) => {
        const at = { x: event.clientX, y: event.clientY }
        window.clearTimeout(wait.current)
        wait.current = window.setTimeout(() => look({ ...detail, ...at }), HOVER_MS)
      }}
      onMouseLeave={() => window.clearTimeout(wait.current)}
      onClick={(event) => {
        if (piece.href) return
        event.stopPropagation()
        look({ ...detail, x: event.clientX, y: event.clientY })
      }}
    >
      {piece.text}
    </mark>
  )
  if (!piece.href) return mark
  return (
    <a
      href={local(piece.href)}
      className="mark-link"
      onClick={(event) => go(event, local(piece.href))}
    >
      {mark}
    </a>
  )
}

/* The stored text with each annotation wrapped. A run with no kind is words. */
export function Pieces({ pieces, text, code }) {
  if (!pieces || !pieces.length) return <>{text || ''}</>
  return pieces.map((piece, index) => (
    piece.kind
      ? <Mark key={index} piece={piece} code={code} />
      : <span key={index}>{piece.text}</span>
  ))
}

/* Double-click any word to look it up, so a plain word costs nothing until it
 * is asked for. */
export function useSelection(look) {
  return function lookUp(event) {
    const chosen = String(window.getSelection ? window.getSelection().toString() : '').trim()
    if (!chosen || chosen.length > 120) return
    look({ term: chosen, x: event.clientX, y: event.clientY })
  }
}

function cutKey(trail) {
  return trail.join('.')
}

function words(node) {
  return (node.pieces || []).map((piece) => piece.text).join('')
}

function CutRow({ node, code, trail, folded, fold, onCut, spans }) {
  const key = cutKey(trail)
  const shut = folded.has(key)
  const kids = node.children || []
  const mark = (String(node.label || '').match(/^\(([^)]{1,4})\)/) || [])[1] || ''
  return (
    <li className={`cut-${node.unit}`}>
      <span className="cut-head">
        {kids.length ? (
          <button
            type="button"
            className="fold"
            aria-expanded={!shut}
            onClick={() => fold(key)}
            title={shut ? 'Open' : 'Close'}
          >
            {shut ? '+' : '−'}
          </button>
        ) : <span className="fold blank" />}
        <span className="cut-unit" title={node.unit}>{node.unit}</span>
        <span className="cut-words">
          {spans && spans[node.path]
            ? (
              <Layered
                spans={spans[node.path]}
                text={words(node)}
                code={code}
                path={node.path}
              />
            )
            : <Pieces pieces={node.pieces} code={code} />}
        </span>
        {mark && onCut ? (
          <button
            type="button"
            className="cut-cite"
            title={`Close over ${node.unit} (${mark})`}
            onClick={() => onCut(node, mark)}
          >
            {'§'}
          </button>
        ) : null}
      </span>
      {kids.length && !shut ? (
        <ol className="cuts">
          {kids.map((child, index) => (
            <CutRow
              key={index}
              node={child}
              code={code}
              trail={trail.concat(index)}
              folded={folded}
              fold={fold}
              onCut={onCut}
              spans={spans}
            />
          ))}
        </ol>
      ) : null}
    </li>
  )
}

/* The section as its cuts. A book that names `(a)` a subdivision says
 * subdivision; the House word is subsection. The server decided which. */
export function Cuts({ tree, code, onCut, spans }) {
  const [folded, setFolded] = useState(() => new Set())
  function fold(key) {
    setFolded((was) => {
      const next = new Set(was)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }
  useEffect(() => { setFolded(new Set()) }, [tree])
  if (!tree) return null
  return (
    <ol className="cuts reading">
      <CutRow
        node={tree}
        code={code}
        trail={[0]}
        folded={folded}
        fold={fold}
        onCut={onCut}
        spans={spans}
      />
    </ol>
  )
}


function count(many, word) {
  return `${many} ${word}${many === 1 ? '' : 's'}`
}

/* One row per section. The table holds a row per occurrence; the card names
 * the section once. */
function once(rows) {
  const seen = new Set()
  return (rows || []).filter((row) => {
    const key = row.href || row.citation
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function plain(kind) {
  return String(kind || '').replace(/_/g, ' ')
}

/* What this reading is, and where the rest of it lives.
 *
 * A note is a stored annotation, so the count is its target across the index.
 * A canon, a clause, or a word class is read from the words each time, so the
 * count is the phrase itself. Either way the card is a way out: the section
 * the citation names, the heading `this chapter` means, the other sections
 * that carry the same reading.
 */
export function TermCard({ looking, go, onPin, onClose, pinned }) {
  const [asked, setAsked] = useState(looking)
  useEffect(() => { setAsked(looking) }, [looking])
  const stored = asked && asked.layer === 'note' && asked.kind
  const url = asked && (asked.term || asked.target)
    ? route('/term', stored
      ? { note: asked.kind, target: asked.target || asked.term, code: asked.code || '' }
      : { q: asked.term || asked.text, code: asked.code || '' })
    : ''
  const { body, loading } = useJson(url)
  if (!asked) return null
  const style = pinned ? undefined : {
    left: Math.min(Math.max(8, (asked.x || 0) - 40), Math.max(8, window.innerWidth - 336)),
    top: Math.min((asked.y || 0) + 18, Math.max(8, window.innerHeight - 300)),
  }
  const frequency = (body && body.frequency) || {}
  const detail = asked.detail || {}
  const phrase = asked.term || asked.text || ''
  return (
    <aside className={pinned ? 'term-card kept' : 'term-card floating'} style={style}>
      <p className="term-title">
        <strong>{asked.target || phrase}</strong>
        <span className="term-shut">
          {onPin ? (
            <button type="button" onClick={() => onPin(asked)} title="Keep this card">keep</button>
          ) : null}
          <button type="button" onClick={onClose} title="Close">{'×'}</button>
        </span>
      </p>
      <p className="term-kinds">
        {asked.layer ? (
          <mark className={asked.layer === 'note' ? `lay-note note-${asked.kind}` : `lay-${asked.layer} ${asked.layer}-${asked.kind}`}>
            {plain(asked.kind)}
          </mark>
        ) : null}
        <span className="term-kind">{asked.layer || (body && body.kind) || 'term'}</span>
        {detail.cite ? <span className="term-kind">{detail.cite}</span> : null}
        {detail.join ? <span className="term-kind">{detail.join}</span> : null}
        {detail.government ? <span className="term-kind">{detail.government}</span> : null}
      </p>
      {asked.reading ? <p className="term-reading">{asked.reading}</p> : null}
      {detail.resolved ? <p className="thin">{detail.resolved}</p> : null}
      <p className="term-ways">
        {asked.href ? <Link href={asked.href} go={go}>open</Link> : null}
        <Link href={`/reader/search?q=${encodeURIComponent(phrase)}`} go={go}>these words</Link>
        {stored ? (
          <Link
            href={`/reader/annotations?note=${encodeURIComponent(asked.kind)}&target=${encodeURIComponent(asked.target || '')}`}
            go={go}
          >
            every row
          </Link>
        ) : null}
        {asked.target && /^[A-Z]{2,}\s+\d/.test(asked.target) ? (
          <Link href={`/reader/cite?q=${encodeURIComponent(asked.target)}`} go={go}>the citation</Link>
        ) : null}
      </p>
      {loading ? <p className="thin">Counting.</p> : null}
      {body && !body.found && !loading ? <p className="thin">No other section carries it.</p> : null}
      {body && body.found ? (
        <>
          <p className="term-count thin">
            {`${frequency.pf || 0} here, ${count(frequency.df || 0, 'section')}`}
            {frequency.indexed != null ? `, ${frequency.indexed} indexed` : ''}
          </p>
          {(body.neighbors || []).length ? (
            <p className="term-neighbors">
              {body.neighbors.slice(0, 10).map((item) => (
                <button
                  key={item.phrase}
                  type="button"
                  title={`${item.pf || 0} together`}
                  onClick={() => setAsked({
                    term: item.phrase, code: asked.code, x: asked.x, y: asked.y,
                  })}
                >
                  {item.phrase}
                </button>
              ))}
            </p>
          ) : null}
          {(body.occurrences || []).length ? (
            <ul className="term-hits">
              {once(body.occurrences).slice(0, 12).map((hit, index) => (
                <li key={(hit.href || hit.citation) + index}>
                  {hit.href
                    ? <Link href={hit.href} go={go}>{hit.citation || hit.href}</Link>
                    : hit.citation}
                </li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </aside>
  )
}
