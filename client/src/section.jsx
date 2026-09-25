/* One section: the stored words, the marks on them, the cuts under them, and
 * the statutes they name.
 *
 * The text is the index's. Nothing here composes a sentence.
 */

import { useContext, useEffect, useState } from 'react'

import { route, useJson } from './api.js'
import { Graph } from './graph.jsx'
import { Contents, Crumbs } from './library.jsx'
import { Layers } from './layers.jsx'
import { Cuts, Link, Pieces, useSelection } from './marks.jsx'
import { Reading } from './reading.js'
import { closureHref, reasonWords, sectionHref } from './place.js'

const HOPS = [
  ['0', 'this section'],
  ['1', 'one hop'],
  ['2', 'two hops'],
  ['all', 'until a repeat'],
]

function Formats({ formats }) {
  if (!formats || !formats.length) return null
  return (
    <p className="formats">
      {formats.map((row) => (
        <a key={row.hint} href={row.href}>{row.hint}</a>
      ))}
    </p>
  )
}

function Sides({ code, previous, next, session, go }) {
  if (!previous && !next) return null
  return (
    <p className="beside">
      {previous
        ? <Link href={sectionHref(code, previous, { session })} go={go}>{`← ${previous}`}</Link>
        : <span className="thin">{'←'}</span>}
      {next
        ? <Link href={sectionHref(code, next, { session })} go={go}>{`${next} →`}</Link>
        : <span className="thin">{'→'}</span>}
    </p>
  )
}

/* The statutes this section names, walked to a depth the reader picks. */
function Refs({ code, number, session, go }) {
  const [hops, setHops] = useState('1')
  const [same, setSame] = useState(false)
  const [open, setOpen] = useState(false)
  const url = open
    ? route('/closure', { code, section: number, use: 'refs', hops, same, session })
    : ''
  const { body, loading } = useJson(url)
  return (
    <section className="refs-block">
      <h2>
        References
        <button
          type="button"
          className="plain"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          {open ? 'hide' : 'walk the citations'}
        </button>
      </h2>
      {open ? (
        <>
          <p className="graph-bar">
            <label>
              Walk
              <select value={hops} onChange={(event) => setHops(event.target.value)}>
                {HOPS.map(([value, words]) => (
                  <option key={value} value={value}>{words}</option>
                ))}
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={same}
                onChange={(event) => setSame(event.target.checked)}
              />
              stay in this book
            </label>
          </p>
          {loading && !body ? <p className="thin">Walking.</p> : null}
          {body && !body.found ? <p className="miss">{reasonWords(body)}</p> : null}
          {body && body.found ? (
            <Graph
              edges={body.edges}
              nodes={body.nodes}
              go={go}
              here={`${code} ${number}`}
              empty="This section names no statute the index holds."
            />
          ) : null}
          {body && body.found && (body.links || []).length ? (
            <details className="links-block">
              <summary>{`Every pointer in the words (${body.links.length})`}</summary>
              <ol className="refs">
                {body.links.map((link, index) => (
                  <li key={index} className={`ref-${link.kind}`}>
                    <span className="ref-source">{link.kind}</span>
                    {link.href
                      ? <Link href={link.href} go={go}>{link.text}</Link>
                      : <span>{link.text}</span>}
                  </li>
                ))}
              </ol>
            </details>
          ) : null}
        </>
      ) : null}
    </section>
  )
}

/* Citation shapes the recorded links did not cover. A gap is a reading to
 * check, not a defect in the text. */
function Gaps({ code, number, session, go }) {
  const [open, setOpen] = useState(false)
  const url = open
    ? route('/closure', { code, section: number, use: 'gaps', hops: '0', session })
    : ''
  const { body, loading } = useJson(url)
  return (
    <section className="gaps-block">
      <h2>
        Gaps
        <button
          type="button"
          className="plain"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          {open ? 'hide' : 'check the citations'}
        </button>
      </h2>
      {open && loading && !body ? <p className="thin">Reading.</p> : null}
      {open && body && !body.found ? <p className="miss">{reasonWords(body)}</p> : null}
      {open && body && body.found ? (
        (body.gaps || []).length ? (
          <ol className="refs">
            {body.gaps.map((gap, index) => (
              <li key={index} className={`gap-${gap.gap}`}>
                <span className="ref-source">{String(gap.gap).replace(/_/g, ' ')}</span>
                <span>{gap.phrase}</span>
                {gap.href ? <Link href={gap.href} go={go}>{gap.citation}</Link> : null}
              </li>
            ))}
          </ol>
        ) : <p className="thin">Every citation in these words was recorded.</p>
      ) : null}
    </section>
  )
}

/* The sections that name this one. A stored citation edge points here. */
function NamedBy({ citation, go }) {
  const { body } = useJson(citation ? route('/citing', { citation }) : '')
  const rows = ((body && body.rows) || []).filter((row) => row.names)
  if (!rows.length) return null
  return (
    <section className="contents-block">
      <h2>Named by<span className="thin"> {rows.length}</span></h2>
      <ol className="contents">
        {rows.map((row) => (
          <li key={row.citation} className="cut-section">
            {row.href
              ? <Link href={row.href} go={go}>{row.citation}</Link>
              : <span>{row.citation}</span>}
          </li>
        ))}
      </ol>
    </section>
  )
}


function Elsewhere({ code, rows, go }) {
  if (!rows || !rows.length) return null
  return (
    <p className="beside">
      <span className="thin">Indexed in</span>
      {rows.map((row) => (
        <Link key={row.session} href={sectionHref(code, String(row.citation).split(' ').pop(), { session: row.session })} go={go}>
          {row.session}
        </Link>
      ))}
    </p>
  )
}

export function Section({ code, number, session, sessions, order, sides, go }) {
  const { shown, act, look } = useContext(Reading)
  const lookUp = useSelection(look)
  const { body, loading } = useJson(route(`/section/${encodeURIComponent(code)}/${encodeURIComponent(number)}`, { session }))
  const drawn = useJson(route(`/marks/${encodeURIComponent(code)}/${encodeURIComponent(number)}`, { session }))
  const [cut, setCut] = useState(null)
  useEffect(() => {
    if (!sides || !body || !body.found) return
    sides.current = {
      code,
      previous: body.previous || '',
      next: body.next || '',
      params: { session },
    }
  }, [body, sides, code, session])
  if (loading && !body) {
    return (
      <>
        <h1>{`${code} ${number}`}</h1>
        <p className="thin">Reading the index.</p>
      </>
    )
  }
  if (!body) return null
  if (!body.found) {
    return (
      <>
        <h1>{`${code} ${number}`}</h1>
        <p className="miss">{reasonWords(body)}</p>
        <Elsewhere code={code} rows={body.indexed_in} go={go} />
      </>
    )
  }
  const year = body.session || ''
  return (
    <>
      <Crumbs crumbs={body.crumbs} go={go} />
      <h1>{body.citation || `${code} ${number}`}</h1>
      <div className="section-bar">
        <Sides code={code} previous={body.previous} next={body.next} session={session} go={go} />
        {sessions && sessions.length ? (
          <label>
            Year
            <select
              value={session || ''}
              onChange={(event) => go(null, sectionHref(code, number, { session: event.target.value }))}
            >
              <option value="">current{year ? ` (${year})` : ''}</option>
              {sessions.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
        ) : null}
        <Formats formats={body.formats} />
      </div>
      <div className="spread">
        <div className="column">
          <Layers
            counts={(drawn.body && drawn.body.counts) || {}}
            shown={shown}
            act={act}
            order={order}
          />
          <article
            className="reading"
            onDoubleClick={lookUp}
            title="Double-click a word to look it up"
          >
            <Cuts
              tree={body.nodes}
              code={code}
              spans={(drawn.body && drawn.body.spans) || null}
              onCut={(node, mark) => setCut({ node, mark })}
            />
          </article>
          {cut ? (
            <p className="cut-chosen">
              <span className="thin">{`${cut.node.unit} (${cut.mark})`}</span>
              <Link
                href={closureHref({ code, section: number, subdivision: cut.mark, use: 'read', session })}
                go={go}
              >
                close over it
              </Link>
              <button type="button" className="plain" onClick={() => setCut(null)}>clear</button>
            </p>
          ) : null}
          {body.history ? (
            <p className="history">
              <Pieces pieces={body.credit} text={body.history} code={code} />
            </p>
          ) : null}
          <Refs code={code} number={number} session={session} go={go} />
          <Gaps code={code} number={number} session={session} go={go} />
        </div>
        <aside className="rail">
          <Contents items={body.contents} go={go} heading="Beside it" sift short />
          <NamedBy citation={body.citation || `${code} ${number}`} go={go} />
          {(body.links || []).length ? (
            <section className="contents-block">
              <h2>Names<span className="thin"> {body.links.length}</span></h2>
              <ol className="contents">
                {body.links.map((link, index) => (
                  <li key={link.href + index} className="cut-section">
                    <Link href={link.href} go={go}>{link.label}</Link>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}
        </aside>
      </div>
    </>
  )
}
