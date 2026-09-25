/* The statute reader: one section, its cuts, and every reading drawn over the
 * words, with a panel that carries the layers, the cards, the citation walk,
 * or the chapter it sits in.
 *
 * The words and the readings come from the index. The panel, the formats and
 * the walk are asked for only when the reader opens them.
 */

import { useContext, useEffect, useMemo, useRef, useState } from 'react'

import { route, useJson, useText } from './api.js'
import { Graph } from './graph.jsx'
import { Layers } from './layers.jsx'
import { Contents, Crumbs } from './library.jsx'
import { Cuts, Link, TermCard } from './marks.jsx'
import { Reading } from './reading.js'
import { reasonWords, searchHref, sectionHref } from './place.js'
import './statute.css'

const TABS = [
  ['layers', 'Readings', '1'],
  ['card', 'Card', '2'],
  ['graph', 'Graph', '3'],
  ['contents', 'Chapter', '4'],
]

const FORMATS = ['html', 'txt', 'md', 'xml']

const LAYER_KEYS = { n: 'note', c: 'clause', a: 'canon', w: 'needle' }

const EVERY = ['note', 'clause', 'canon', 'mention', 'relation', 'abbreviation', 'needle']

const KEYS = [
  ['/', 'search the library'],
  ['[  ]', 'previous, next section'],
  ['⌫', 'back where you came from'],
  ['1 – 4', 'readings, card, graph, chapter'],
  ['n c a w', 'notes, clauses, canons, word classes'],
  ['f', 'fold or open every cut'],
  ['v', 'next format'],
  ['k', 'keep the open card'],
  ['d', 'paper or dark'],
  ['esc', 'close a card or this list'],
]

const THEME = 'reader.theme'
const SIZE = 'reader.size'

function kept(key, fallback) {
  try {
    return window.localStorage.getItem(key) || fallback
  } catch (error) {
    return fallback
  }
}

function keep(key, value) {
  try {
    window.localStorage.setItem(key, value)
  } catch (error) { /* a private window keeps nothing */ }
}

function same(one, two) {
  if (!one || !two) return false
  return (one.term || one.text) === (two.term || two.text)
    && one.kind === two.kind
    && one.path === two.path
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

export function StatuteReader({ here, go }) {
  const { shown, act } = useContext(Reading)
  const [looking, setLooking] = useState(null)
  const [peek, setPeek] = useState(null)
  const [tab, setTab] = useState('layers')
  const [fmt, setFmt] = useState('html')
  const [chosen, setChosen] = useState(null)
  const [held, setHeld] = useState([])
  const [keys, setKeys] = useState(false)
  const [said, setSaid] = useState('')
  const [folded, setFolded] = useState(false)
  const [theme, setTheme] = useState(() => kept(THEME, 'paper'))
  const [size, setSize] = useState(() => kept(SIZE, 'm'))
  const box = useRef(null)
  const text = useRef(null)
  const timer = useRef(0)

  const { code, number, session } = here
  const cite = `${code} ${number}`

  const { body, loading } = useJson(
    route(`/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}`, { session }),
  )
  const drawn = useJson(
    route(`/marks/${encodeURIComponent(code)}/${encodeURIComponent(number)}`, { session }),
  )
  const walk = useJson(
    tab === 'graph'
      ? route('/closure', { code, section: number, use: 'refs', hops: 1, session })
      : '',
  )
  const plain = useText(
    fmt === 'html' ? '' : `/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}.${fmt}`,
  )

  useEffect(() => { setChosen(null); setFolded(false) }, [code, number])
  useEffect(() => () => window.clearTimeout(timer.current), [])

  function say(words) {
    window.clearTimeout(timer.current)
    setSaid(words)
    timer.current = window.setTimeout(() => setSaid(''), 2400)
  }
  function copy(words, told) {
    try {
      window.navigator.clipboard.writeText(words).then(
        () => say(told),
        () => say('Copying was refused by the browser.'),
      )
    } catch (error) {
      say('Copying was refused by the browser.')
    }
  }
  function flipTheme() {
    setTheme((was) => {
      const next = was === 'dark' ? 'paper' : 'dark'
      keep(THEME, next)
      return next
    })
  }
  function step(way) {
    const to = way < 0 ? body && body.previous : body && body.next
    if (!to) {
      say(way < 0 ? 'This is the first section in the heading.' : 'This is the last section in the heading.')
      return
    }
    go(null, sectionHref(code, to, { session }))
  }

  /* The cut tree folds itself: every open fold is a button the reader could
   * have pressed, so pressing them all is the same state. */
  async function foldAll() {
    const root = text.current
    if (!root) return
    const folds = () => Array.from(root.querySelectorAll('button.fold')).slice(1)
    if (!folded) {
      folds().filter((one) => one.getAttribute('aria-expanded') === 'true').forEach((one) => one.click())
      setFolded(true)
      return
    }
    for (let pass = 0; pass < 8; pass += 1) {
      const shut = folds().filter((one) => one.getAttribute('aria-expanded') === 'false')
      if (!shut.length) break
      shut.forEach((one) => one.click())
      await new Promise((rest) => { window.setTimeout(rest, 30) })
    }
    setFolded(false)
  }

  function pin(card) {
    if (!card) return
    setHeld((was) => (was.some((one) => same(one, card)) ? was : [card].concat(was).slice(0, 8)))
    setPeek(null)
    setTab('card')
    if (same(looking, card)) setLooking(null)
  }

  /* A mark answers a click by opening in the panel and a hover by floating
   * beside the words, so reading is never interrupted by a card. */
  const clicking = useRef(false)
  useEffect(() => {
    function onClick(event) {
      clicking.current = true
      window.setTimeout(() => { clicking.current = false }, 0)
      const target = event.target
      if (peek && !(target.closest && target.closest('.term-card.floating'))) setPeek(null)
    }
    function onMove(event) {
      if (!peek) return
      const target = event.target
      if (target.closest && (target.closest('.term-card.floating') || target.closest('mark'))) return
      const across = event.clientX - (peek.x || 0)
      const down = event.clientY - (peek.y || 0)
      if ((across * across) + (down * down) > 230 * 230) setPeek(null)
    }
    document.addEventListener('click', onClick, true)
    document.addEventListener('mousemove', onMove)
    return () => {
      document.removeEventListener('click', onClick, true)
      document.removeEventListener('mousemove', onMove)
    }
  }, [peek])

  function look(detail) {
    if (clicking.current) {
      setLooking(detail)
      setPeek(null)
      setTab('card')
    } else {
      setPeek(detail)
    }
  }

  function lookWord(event) {
    if (event.target.closest && event.target.closest('mark,button')) return
    const chosenWord = String(window.getSelection ? window.getSelection().toString() : '')
      .trim()
      .replace(/[^\w'-]/g, '')
    if (chosenWord.length < 2) return
    setLooking({ term: chosenWord.toLowerCase(), code, x: event.clientX, y: event.clientY })
    setPeek(null)
    setTab('card')
  }

  useEffect(() => {
    function onKey(event) {
      const tag = (event.target && event.target.tagName) || ''
      if (/INPUT|TEXTAREA|SELECT/.test(tag) || (event.target && event.target.isContentEditable)) {
        if (event.key === 'Escape') event.target.blur()
        return
      }
      if (event.metaKey || event.ctrlKey || event.altKey) return
      const key = event.key
      const layer = LAYER_KEYS[key]
      const onTab = TABS.find((row) => row[2] === key)
      const mine = layer || onTab || [
        '/', '?', '[', ']', 'Backspace', 'f', 'v', 'd', 'k', 'Escape',
      ].includes(key)
      if (!mine) return
      event.preventDefault()
      event.stopPropagation()
      if (layer) act.toggleLayer(layer)
      else if (onTab) setTab(onTab[0])
      else if (key === '/') { if (box.current) { box.current.focus(); box.current.select() } }
      else if (key === '?') setKeys((was) => !was)
      else if (key === '[') step(-1)
      else if (key === ']') step(1)
      else if (key === 'Backspace') window.history.back()
      else if (key === 'f') foldAll()
      else if (key === 'v') setFmt((was) => FORMATS[(FORMATS.indexOf(was) + 1) % FORMATS.length])
      else if (key === 'd') flipTheme()
      else if (key === 'k') pin(peek || looking)
      else if (key === 'Escape') {
        if (peek) setPeek(null)
        else if (keys) setKeys(false)
        else if (looking) setLooking(null)
      }
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  })

  const counts = (drawn.body && drawn.body.counts) || {}
  const spans = (drawn.body && drawn.body.spans) || null
  const total = Object.keys(counts).reduce(
    (sum, layer) => sum + Object.values(counts[layer]).reduce((a, b) => a + b, 0),
    0,
  )
  const contents = (body && body.contents) || []
  const place = contents.findIndex((row) => row.current)
  const cards = held.length + (looking ? 1 : 0)
  const reading = useMemo(
    () => ({ shown, act, look, go }),
    [shown, act, go, peek, looking],
  )

  if (loading && !body) {
    return (
      <div className="ll ll-statute" data-theme={theme} data-size={size}>
        <h1>{cite}</h1>
        <p className="thin">Reading the index.</p>
      </div>
    )
  }
  if (!body) return null

  return (
    <Reading.Provider value={reading}>
      <div className="ll ll-statute" data-theme={theme} data-size={size}>
        <div className="ll-bar">
          <span className="ll-where">{`California · ${code}`}</span>
          <form
            className="ll-ask"
            style={{ flex: '1 1 14rem', maxWidth: '26rem', marginLeft: 'auto' }}
            onSubmit={(event) => {
              event.preventDefault()
              const asked = (box.current && box.current.value || '').trim()
              if (asked) go(event, searchHref({ q: asked }))
            }}
          >
            <input
              ref={box}
              name="q"
              placeholder="Search the library"
              aria-label="Search the library"
              style={{ fontSize: '0.92rem', padding: '0.35rem 2rem 0.35rem 0.6rem' }}
            />
            <kbd>/</kbd>
          </form>
          <span className="ll-switches">
            <button type="button" className="ll-switch" onClick={flipTheme} title="Paper or dark (d)">
              {theme === 'dark' ? 'paper' : 'dark'}
            </button>
            <button
              type="button"
              className="ll-switch"
              onClick={() => setSize((was) => {
                const next = was === 's' ? 'm' : was === 'm' ? 'l' : 's'
                keep(SIZE, next)
                return next
              })}
              title="The size of the words"
            >
              {`size ${size}`}
            </button>
            <button type="button" className="ll-switch" onClick={() => setKeys((was) => !was)} title="Keys (?)">
              keys
            </button>
          </span>
        </div>

        {!body.found ? (
          <>
            <h1>{cite}</h1>
            <p className="miss">{reasonWords(body)}</p>
          </>
        ) : (
          <div className="spread" data-wide={tab === 'graph' ? 'true' : 'false'}>
            <main>
              <Crumbs crumbs={body.crumbs} go={go} />
              <h1>{body.citation || cite}</h1>
              <p className="ll-caption">{body.title || ''}</p>

              <div className="section-bar">
                <p className="beside">
                  {body.previous
                    ? <Link href={sectionHref(code, body.previous, { session })} go={go}>{`← ${body.previous}`}</Link>
                    : <span className="thin">{'←'}</span>}
                  {body.next
                    ? <Link href={sectionHref(code, body.next, { session })} go={go}>{`${body.next} →`}</Link>
                    : <span className="thin">{'→'}</span>}
                </p>
                {place >= 0 ? (
                  <span className="ll-where-in">{`${place + 1} of ${contents.length} in the heading`}</span>
                ) : null}
                <div className="ll-fmts" role="tablist" aria-label="Format">
                  {FORMATS.map((one) => (
                    <button
                      key={one}
                      type="button"
                      role="tab"
                      data-ll="fmt"
                      aria-selected={fmt === one}
                      onClick={() => setFmt(one)}
                    >
                      {one}
                    </button>
                  ))}
                </div>
                <button
                  type="button"
                  className="ll-plain-link"
                  onClick={foldAll}
                  title="Fold or open every cut (f)"
                >
                  {folded ? 'open all' : 'fold all'}
                </button>
              </div>

              {chosen ? (
                <div className="ll-chosen">
                  <strong>{chosen.cite}</strong>
                  <span className="ll-unit">{chosen.unit}</span>
                  <span className="ll-ways">
                    <button
                      type="button"
                      className="ll-plain-link"
                      onClick={() => copy(chosen.cite, `Copied ${chosen.cite}`)}
                    >
                      copy citation
                    </button>
                    <button
                      type="button"
                      className="ll-plain-link"
                      onClick={() => setChosen(null)}
                      aria-label="Close"
                    >
                      {'×'}
                    </button>
                  </span>
                </div>
              ) : null}

              {fmt === 'html' ? (
                <>
                  <div className="ll-text" ref={text} onDoubleClick={lookWord}>
                    <Cuts
                      tree={body.nodes}
                      code={code}
                      spans={spans}
                      onCut={(node, mark) => setChosen({
                        cite: `${cite}(${mark})`,
                        unit: node.unit,
                      })}
                    />
                  </div>
                  <p className="ll-hint">
                    Hover a mark to peek at it, click to keep it in the panel, double-click any
                    word to look it up. <kbd>?</kbd> lists the keys.
                  </p>
                </>
              ) : (
                <div className="ll-plain">
                  <button
                    type="button"
                    className="ll-copy-plain"
                    onClick={() => copy(plain.raw || '', `Copied the ${fmt} of ${cite}`)}
                  >
                    copy
                  </button>
                  <pre data-fmt={fmt}>{plain.loading ? 'Asking the library.' : (plain.raw || '')}</pre>
                </div>
              )}
            </main>

            <aside className="ll-panel">
              <div className="ll-tabs" role="tablist" aria-label="Panel">
                {TABS.map(([id, label, key]) => (
                  <button
                    key={id}
                    type="button"
                    role="tab"
                    data-ll="tab"
                    aria-selected={tab === id}
                    title={`Key ${key}`}
                    onClick={() => setTab(id)}
                  >
                    {label}
                    <span className="thin">
                      {id === 'layers' ? (total || '')
                        : id === 'card' ? (cards || '')
                          : id === 'contents' ? (contents.length || '') : ''}
                    </span>
                  </button>
                ))}
              </div>

              {tab === 'layers' ? (
                <>
                  <Layers counts={counts} shown={shown} act={act} />
                  <div className="ll-presets">
                    <span className="thin">Show</span>
                    <button type="button" className="ll-plain-link" onClick={() => EVERY.forEach((one) => { if (!shown.layer(one)) act.toggleLayer(one) })}>
                      every layer
                    </button>
                    <button
                      type="button"
                      className="ll-plain-link"
                      onClick={() => EVERY.forEach((one) => {
                        const wanted = one === 'note' || one === 'clause'
                        if (shown.layer(one) !== wanted) act.toggleLayer(one)
                      })}
                    >
                      notes and clauses
                    </button>
                    <button type="button" className="ll-plain-link" onClick={() => EVERY.forEach((one) => { if (shown.layer(one)) act.toggleLayer(one) })}>
                      bare words
                    </button>
                  </div>
                  <h2>How each layer is drawn</h2>
                  <dl className="ll-drawn">
                    <dt><mark className="lay-note note-definition">tint</mark></dt>
                    <dd>notes <kbd>n</kbd></dd>
                    <dt><mark className="lay-clause clause-exception">bar</mark></dt>
                    <dd>clauses <kbd>c</kbd></dd>
                    <dt><mark className="lay-canon canon-mandatory">dotted rule</mark></dt>
                    <dd>canons <kbd>a</kbd></dd>
                    <dt><mark className="lay-needle needle-Section">ring</mark></dt>
                    <dd>word classes <kbd>w</kbd></dd>
                  </dl>
                </>
              ) : null}

              {tab === 'card' ? (
                <>
                  {looking ? (
                    <TermCard
                      looking={looking}
                      go={go}
                      pinned
                      onPin={pin}
                      onClose={() => setLooking(null)}
                    />
                  ) : null}
                  {!looking && !held.length ? (
                    <p className="thin">
                      Click a mark in the text to read it here. Double-click a word to count it
                      across the library. Press <em>keep</em> on a card to hold it below while
                      you read on.
                    </p>
                  ) : null}
                  {held.length ? (
                    <>
                      <h2>Kept<span className="thin"> {held.length}</span></h2>
                      {held.map((card, index) => (
                        <TermCard
                          key={`${card.term || card.text}${index}`}
                          looking={card}
                          go={go}
                          pinned
                          onClose={() => setHeld((was) => was.filter((_one, at) => at !== index))}
                        />
                      ))}
                    </>
                  ) : null}
                </>
              ) : null}

              {tab === 'graph' ? (
                <>
                  <p className="thin">
                    {`Sections ${cite} reaches in a walk of the citations. Hover a box to follow its edges; click one to open it.`}
                  </p>
                  {walk.loading && !walk.body ? <p className="thin">Walking.</p> : null}
                  {walk.body && !walk.body.found ? <p className="miss">{reasonWords(walk.body)}</p> : null}
                  {walk.body && walk.body.found ? (
                    <Graph
                      edges={walk.body.edges}
                      nodes={walk.body.nodes}
                      go={go}
                      here={cite}
                      empty="This section names no statute the index holds."
                    />
                  ) : null}
                </>
              ) : null}

              {tab === 'contents' ? (
                <Contents items={contents} go={go} heading="In this heading" sift short />
              ) : null}
            </aside>
          </div>
        )}

        {peek ? (
          <TermCard
            looking={peek}
            go={go}
            onPin={pin}
            onClose={() => setPeek(null)}
          />
        ) : null}
        {keys ? <Keys onClose={() => setKeys(false)} /> : null}
        {said ? <div className="ll-toast" role="status">{said}</div> : null}
      </div>
    </Reading.Provider>
  )
}
