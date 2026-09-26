/* Search: the hits the index returned, the book they sit in, and the words
 * beside them before the reader is opened.
 *
 * The query goes to the index. The book chips and the selection are the
 * reader's own, over the hits that came back, so narrowing costs no request.
 */

import { useEffect, useMemo, useRef, useState } from 'react'

import { route, useJson } from './api.js'
import './search.css'
import { Hits } from './find.jsx'
import { editions, reasonWords, searchHref, sectionHref } from './place.js'

const KEYS = [
  ['/', 'edit the search'],
  ['j  k', 'next, previous result'],
  ['↵', 'open the result in the reader'],
  ['c', 'copy its citation'],
  ['d', 'paper or dark'],
  ['esc', 'leave the box, close this list'],
]

const THEME = 'reader.theme'

function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return window.localStorage.getItem(THEME) || 'paper'
    } catch (error) {
      return 'paper'
    }
  })
  function flip() {
    setTheme((was) => {
      const next = was === 'dark' ? 'paper' : 'dark'
      try {
        window.localStorage.setItem(THEME, next)
      } catch (error) { /* a private window keeps nothing */ }
      return next
    })
  }
  return [theme, flip]
}

function terms(q) {
  return String(q || '').toLowerCase().split(/\s+/).filter(Boolean)
}

/* The stored words with the matched ones marked.
 *
 * The index prints its own hit in capitals, so a run of capitals is what it
 * matched -- `habitability` finds `HABIT` and `HABITABLE`. The asked-for term
 * is marked too, in whatever case the section stored it.
 */
function segments(text, q) {
  const asked = terms(q).map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  const words = String(text || '')
  if (!asked.length) return [{ text: words, hit: false }]
  const split = new RegExp(`(${asked.concat('[A-Z]{4,}').join('|')})`, 'g')
  return words.split(split).filter(Boolean).map((part) => ({
    text: part,
    hit: /^[A-Z]{4,}$/.test(part) || asked.some((word) => new RegExp(`^${word}$`, 'i').test(part)),
  }))
}

function Keys({ onClose }) {
  return (
    <aside className="keys" aria-label="Keys">
      <p className="term-title">
        <strong>Keys</strong>
        <span className="term-shut">
          <button type="button" onClick={onClose} aria-label="Close">{'×'}</button>
        </span>
      </p>
      <dl>
        {KEYS.map(([key, words]) => (
          <div key={key}>
            <dt><kbd>{key}</kbd></dt>
            <dd>{words}</dd>
          </div>
        ))}
      </dl>
    </aside>
  )
}

export function Search({ here, codes, sessions, go }) {
  const [asked, setAsked] = useState(here.q || '')
  const [book, setBook] = useState(here.code || '')
  const [sel, setSel] = useState(0)
  const [keys, setKeys] = useState(false)
  const [said, setSaid] = useState('')
  const [theme, flipTheme] = useTheme()
  const box = useRef(null)
  const timer = useRef(0)

  useEffect(() => { setAsked(here.q || '') }, [here.q])
  useEffect(() => { setBook(here.code || ''); setSel(0) }, [here.q, here.code])

  const url = here.q
    ? route('/search', {
      q: here.q, start: here.start, end: here.end, session: here.session, limit: 50,
    })
    : ''
  const { body, loading } = useJson(url)
  const found = useMemo(() => (body && body.found && body.hits) || [], [body])
  const shown = useMemo(
    () => (book ? found.filter((hit) => hit.code === book) : found),
    [found, book],
  )
  const books = useMemo(() => {
    const order = []
    found.forEach((hit) => { if (!order.includes(hit.code)) order.push(hit.code) })
    return [{ id: '', label: 'every book', count: found.length }].concat(
      order.map((code) => ({
        id: code,
        label: code,
        count: found.filter((hit) => hit.code === code).length,
      })),
    )
  }, [found])

  const place = Math.min(sel, Math.max(0, shown.length - 1))
  const hit = shown[place] || null

  function say(words) {
    window.clearTimeout(timer.current)
    setSaid(words)
    timer.current = window.setTimeout(() => setSaid(''), 2400)
  }
  function open() {
    if (hit) go(null, sectionHref(hit.code, hit.section, { session: here.session }))
  }
  function copyCite() {
    if (!hit) return
    try {
      window.navigator.clipboard.writeText(hit.citation).then(
        () => say(`Copied ${hit.citation}`),
        () => say('Copying was refused by the browser.'),
      )
    } catch (error) {
      say('Copying was refused by the browser.')
    }
  }
  function move(step) {
    if (!shown.length) return
    setSel(Math.max(0, Math.min(shown.length - 1, place + step)))
  }

  useEffect(() => {
    function onKey(event) {
      const tag = (event.target && event.target.tagName) || ''
      if (/INPUT|TEXTAREA|SELECT/.test(tag)) {
        if (event.key === 'Escape') event.target.blur()
        else if (event.key === 'ArrowDown') { event.preventDefault(); move(1) }
        else if (event.key === 'ArrowUp') { event.preventDefault(); move(-1) }
        return
      }
      if (event.metaKey || event.ctrlKey || event.altKey) return
      const key = event.key
      const mine = ['/', 'j', 'k', 'ArrowDown', 'ArrowUp', 'Enter', 'o', 'c', 'd', '?', 'Escape']
      if (!mine.includes(key)) return
      event.preventDefault()
      event.stopPropagation()
      if (key === '/') {
        if (box.current) { box.current.focus(); box.current.select() }
      } else if (key === 'j' || key === 'ArrowDown') move(1)
      else if (key === 'k' || key === 'ArrowUp') move(-1)
      else if (key === 'Enter' || key === 'o') open()
      else if (key === 'c') copyCite()
      else if (key === 'd') flipTheme()
      else if (key === '?') setKeys((was) => !was)
      else if (key === 'Escape') setKeys(false)
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  })

  useEffect(() => () => window.clearTimeout(timer.current), [])

  function pickRow(event) {
    const row = event.target.closest && event.target.closest('ol.hits > li')
    if (!row || !row.parentNode) return
    const index = Array.prototype.indexOf.call(row.parentNode.children, row)
    if (index >= 0) setSel(index)
  }

  const words = (here.q || '').trim()
  const summary = !words
    ? 'Write words, a phrase, or a citation.'
    : loading && !body
      ? 'Searching the index.'
      : shown.length
        ? `${shown.length} ${shown.length === 1 ? 'section carries' : 'sections carry'} “${words}”${book ? ` in ${book}` : ''}.`
        : `No section carries “${words}”${book ? ` in ${book}` : ''}. ${editions(sessions)}`

  return (
    <div className="ll" data-theme={theme}>
      <div className="ll-bar">
        <span className="ll-where">California</span>
        <span className="ll-switches">
          <button
            type="button"
            className="ll-switch"
            onClick={flipTheme}
            title="Paper or dark (d)"
          >
            {theme === 'dark' ? 'paper' : 'dark'}
          </button>
          <button
            type="button"
            className="ll-switch"
            onClick={() => setKeys((was) => !was)}
            title="Keys (?)"
          >
            keys
          </button>
        </span>
      </div>

      <form
        className="ll-ask"
        onSubmit={(event) => {
          event.preventDefault()
          const wanted = asked.trim()
          if (wanted && wanted !== here.q) go(event, searchHref({ ...here, q: wanted, kind: undefined }))
          else open()
        }}
      >
        <input
          ref={box}
          value={asked}
          onChange={(event) => setAsked(event.target.value)}
          placeholder="Words, a phrase, or a citation"
          aria-label="Search the library"
        />
        <kbd>/</kbd>
      </form>

      <div className="ll-books">
        <span className="thin">Book</span>
        {books.map((row) => (
          <button
            key={row.id || 'every'}
            type="button"
            data-ll="chip"
            aria-pressed={book === row.id}
            onClick={() => { setBook(row.id); setSel(0) }}
          >
            {row.label}
            <span className="thin">{row.count}</span>
          </button>
        ))}
      </div>

      <p className="ll-summary">{summary}</p>
      {body && !body.found && !loading ? <p className="miss">{reasonWords(body)}</p> : null}

      <div className="spread">
        <main>
          <div
            className="ll-hits"
            data-sel={String(place)}
            onClick={pickRow}
            onDoubleClick={open}
          >
            <Hits hits={shown} go={go} />
          </div>
        </main>

        <aside className="ll-panel">
          {hit ? (
            <div>
              <p className="ll-book">{hit.code}</p>
              <h1>{hit.citation}</h1>
              <h2>Where it sits</h2>
              <ol className="contents">
                {(hit.path || []).map((step, index) => (
                  <li key={index} className={`cut-${step.level}`}>{step.heading}</li>
                ))}
                <li className="cut-section">{`§ ${hit.section}`}</li>
              </ol>
              <h2>The words</h2>
              <p className="ll-words">
                {segments(hit.snippet, words).map((part, index) => (
                  part.hit
                    ? <mark key={index} className="note-definition">{part.text}</mark>
                    : <span key={index}>{part.text}</span>
                ))}
              </p>
              <div className="ll-ways">
                <button type="button" className="ll-open" onClick={open}>
                  Open in the reader
                </button>
                <button type="button" className="ll-copy" onClick={copyCite}>
                  copy citation
                </button>
                <span className="thin"><kbd>{'↵'}</kbd> opens</span>
              </div>
            </div>
          ) : (
            <p className="thin">Nothing to preview. Try other words, or a different book.</p>
          )}
        </aside>
      </div>

      {keys ? <Keys onClose={() => setKeys(false)} /> : null}
      {said ? <div className="ll-toast" role="status">{said}</div> : null}
    </div>
  )
}
