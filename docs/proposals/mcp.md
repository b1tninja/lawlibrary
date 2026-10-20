# MCP

The server is `mcp_server.py`. It is the `mcp` extra (`pip install 'lawlibrary[mcp]'`, or `.[dev]` which includes it). A plain install does not pull the server in. `lawlibrary-mcp` starts it on stdio. The tools read the local index. They do not scrape a commercial host.

The names follow the same rule as [hardly](https://github.com/b1tninja/hardly): the first word says what the call does.

| First word | What it does |
| --- | --- |
| `send_` | Fetches from the network, rebuilds an index, or starts or stops the local reader. Without `confirm=true` the tool returns a plan and does nothing. |
| `write_` | Writes a pin. Refuses to replace pins already stored for that citation unless `overwrite=true`. |
| anything else | Only reads. |

`server_status` advertises the version, the feature flags, and every tool name, the same report hardly puts on `hardly_server_status`. Call it when a tool seems to be missing, then restart the server if the list is stale. The server instructions say the same rule.

Download (`python ca.py --download`) and a rebuild (`python ca.py --index`) stay on the command line. They are not tools. A tool that later does either job is `send_` and confirm-gated.

## Names that were already registered

Three calls keep their old names. Each one runs the gated function, so the old name does not skip the gate.

| Old name | Calls | Gate |
| --- | --- | --- |
| `serve_reader` | `send_reader` | `start` and `stop` need `confirm=true`. `status` is a read. |
| `pin_section` | `write_pin_section` | `overwrite=true` to replace pins already stored for that citation. A first pin for a citation that has none is a write. A miss writes nothing. |
| `_named_codes` | the same helper `search_law` uses | Read-only. The decorator had been sitting on this helper, so `search_law` was not a tool. `search_law` is the tool. `_named_codes` remains so a caller that found the old name still gets an answer. |

`search_law` is the search the readme names. It only reads the index.
