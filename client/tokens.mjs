/* The token sheet, taken from the page that already carries it.
 *
 * `templates/style.html` is the one copy of the library's type, palette, cut
 * ladder, and marks: the script-free pages include it and the reader loads it.
 * A package cannot include a Jinja template, so this lifts the same bytes into
 * a stylesheet the bundler can read. It is generated, never edited, and never
 * committed.
 *
 * The only rewrite is the opening `body` rule. A page of this library dresses
 * its own body; a design that embeds these components dresses the root the
 * library renders, so that one selector becomes `.reader`, which both carry.
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const from = resolve(here, '..', 'templates', 'style.html')
const to = resolve(here, 'src', 'tokens.css')

const page = readFileSync(from, 'utf8')
const opened = page.indexOf('<style>')
const closed = page.lastIndexOf('</style>')
if (opened < 0 || closed < 0) {
  throw new Error(`no <style> block in ${from}`)
}

const body = page.slice(opened + '<style>'.length, closed).trim()
if (!/^body \{/m.test(body)) {
  throw new Error('the token sheet no longer opens with a body rule')
}

const sheet = body.replace(/^body \{/m, '.reader {')
writeFileSync(to, `/* Generated from templates/style.html by tokens.mjs. Do not edit. */\n${sheet}\n`)
process.stdout.write(`tokens.css <- templates/style.html (${sheet.length} bytes)\n`)
