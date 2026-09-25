/* The root a page of this library sits in.
 *
 * It carries the `reader` class the sheet dresses, and it holds what every
 * mark on the page shares: which readings are drawn, what a click looks up,
 * and how a link opens. A component rendered outside it still works — the
 * context has defaults — but it is not dressed, so wrap the page once.
 */

import { useShown } from './layers.jsx'
import { Reading } from './reading.js'

function stay(event) {
  if (event && event.preventDefault) event.preventDefault()
}

export function Reader({ children, className, go, look, shown, act }) {
  const [held, holding] = useShown()
  const value = {
    shown: shown || held,
    act: act || holding,
    look: look || (() => {}),
    go: go || stay,
  }
  return (
    <Reading.Provider value={value}>
      <div className={className ? `reader ${className}` : 'reader'}>{children}</div>
    </Reading.Provider>
  )
}
