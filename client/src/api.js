/* The JSON routes, and the hooks that read them.
 *
 * Every route answers `found`. A miss keeps `reason`, so a view says why
 * instead of showing an empty page. The catalog, the publication years, and
 * the closed sets are read once and kept.
 */

import { useEffect, useState } from 'react'

function search(params) {
  const asked = new URLSearchParams()
  Object.keys(params || {}).forEach((name) => {
    const value = params[name]
    if (value === undefined || value === null || value === '' || value === false) return
    asked.set(name, value === true ? '1' : String(value))
  })
  const text = asked.toString()
  return text ? '?' + text : ''
}

export function route(path, params) {
  return path + search(params)
}

const held = new Map()

async function read(url, signal) {
  const response = await fetch(url, { signal, headers: { Accept: 'application/json' } })
  const text = await response.text()
  try {
    return JSON.parse(text)
  } catch (error) {
    return { found: false, reason: 'not_found' }
  }
}

/* One GET. `url` empty holds the view at rest. A second call for the same url
 * while the first is open replaces it, so a fast typist does not race. */
export function useJson(url) {
  const [state, setState] = useState(() => ({ url, body: null, loading: Boolean(url) }))
  useEffect(() => {
    if (!url) {
      setState({ url, body: null, loading: false })
      return undefined
    }
    const controller = new AbortController()
    setState((was) => ({ url, body: was.url === url ? was.body : null, loading: true }))
    read(url, controller.signal).then(
      (body) => setState({ url, body, loading: false }),
      () => {},
    )
    return () => controller.abort()
  }, [url])
  return state
}

/* A route whose answer does not change while the page is open. */
export function useKept(url, empty) {
  const [body, setBody] = useState(() => held.get(url) || empty)
  useEffect(() => {
    if (held.has(url)) {
      setBody(held.get(url))
      return undefined
    }
    let live = true
    read(url).then((payload) => {
      held.set(url, payload)
      if (live) setBody(payload)
    }, () => {})
    return () => { live = false }
  }, [url])
  return body
}

const NO_CATALOG = { codes: [], sessions: [] }

export function useCatalog() {
  const books = useKept('/codes', { codes: [] })
  const years = useKept('/sessions', { sessions: [] })
  const codes = books.codes || NO_CATALOG.codes
  const sessions = years.sessions || NO_CATALOG.sessions
  return { codes, sessions }
}

const NO_SURFACES = { note: [], cite: [], join: [], cut: [], use: [], gap: [], hint: [] }

/* The closed sets, so the legend and the filters are the words the server
 * stores and not a copy kept here. */
export function useSurfaces() {
  const body = useKept('/surfaces', { surfaces: NO_SURFACES, units: [] })
  return { ...NO_SURFACES, ...(body.surfaces || {}), units: body.units || [] }
}

export function codeTitle(codes, token) {
  const row = (codes || []).find((item) => item.code === token)
  return row ? row.title : token
}
