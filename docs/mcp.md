# Cobble MCP: first read-only interface

This experiment offers an AI client three operations over a **local**
Cobble memory store. It does not grant ChatGPT direct access merely by
starting the server. First test the server on McKay using local stdio.

## Setup on McKay

In the Cobble checkout with the existing Python virtual environment:

```bash
python -m pip install "mcp>=1,<2"
PYTHONPATH=src:../VillageLink/prototype python -m unittest discover -s tests -v
```

To inspect the MCP tool definitions locally, use an MCP client/inspector
that supports stdio and launch:

```bash
PYTHONPATH=src:../VillageLink/prototype python scripts/mcp_server.py
```

The subprocess communicates **MCP JSON-RPC on standard input/output**;
it is not a command-line chat. Do not expect a textual greeting.

The tools are:

- `get_trace(uri)` — trace metadata and bounded retained content.
- `inspect_star(centre_uri)` — locally verified star centre and rays.
- `search_memory(query, limit=10)` — simple text search over trace
  selectors and their locally retained excerpts.

The store defaults to `~/cobble-data` and may be overridden with
`COBBLE_DATA_DIR`. No tool writes to the store, performs network
requests, or assigns truth values to equivalence assertions. The local
text result is capped at 20,000 characters; searches return at most 20
traces and do not index Git object history or GitHub conversation JSON.

## Connection boundary

A stdio server on McKay is not directly reachable by ChatGPT on the
web. Connecting ChatGPT requires a supported remote MCP deployment or
private tunnel, plus appropriate access controls. **Do not open an
unauthenticated listener or share the memory archive publicly.**

A later increment should implement an authenticated remote transport
and verify actual ChatGPT plugin connection. For now the deliverable
is a locally testable, read-only MCP server.
