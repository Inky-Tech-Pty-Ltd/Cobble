# Cobble MCP: first read-only interface

This experiment exposes three read-only operations over a **local**
Cobble memory store and connects them to ChatGPT through an outbound,
workspace-scoped Secure MCP Tunnel. It does not require a publicly exposed
HTTP listener. It does not establish assistant identity or autonomous memory.

## Server and local verification on McKay

From the Cobble checkout with the existing Python virtual environment:

```bash
python -m pip install "mcp>=1,<2"
PYTHONPATH=src:../VillageLink/prototype python -m unittest discover -s tests -v
```

The integration was tested against MCP Python SDK **1.30.0**. Installing
MCP 2.x instead caused the server import to fail because that SDK renamed
`FastMCP` to `MCPServer` and changed its API. The tests alone did not expose
that version mismatch, so **test the MCP protocol**, not only the Python
functions.

A stdio MCP client can launch:

```bash
PYTHONPATH=src:../VillageLink/prototype python scripts/mcp_server.py
```

The subprocess speaks MCP JSON-RPC on stdin/stdout; it does not print a
command-line greeting. A local MCP client successfully discovered the
three tools and retrieved a retained ChatGPT excerpt over this protocol.

The tools are:

- `get_trace(uri)` — trace metadata and bounded retained content.
- `inspect_star(centre_uri)` — locally verified centre and Village Link rays.
- `search_memory(query, limit=10)` — text search over trace selectors and
  their locally retained excerpts.

The store defaults to `~/cobble-data` and may be overridden by
`COBBLE_DATA_DIR`. The tools do not write to the store, make network
requests, or judge equivalence assertions. Local text results are capped at
20,000 characters; search returns at most 20 traces and does not index the
imported Git history or GitHub conversation JSON.

## Connection established — 14 October 2026

A separate OpenAI Platform tunnel called **Cobble memory** was created for
the ChatGPT workspace, without reusing the **Anna connection test** tunnel.
The OpenAI `tunnel-client` v0.0.16 Linux amd64 binary was installed on
McKay. A dedicated local profile (`cobble-memory`) uses the built-in
`sample_mcp_stdio_local` template, with the stdio MCP target configured
to launch Cobble's virtual-environment Python:

```bash
env PYTHONPATH=/home/cobbler/Cobble/src:/home/cobbler/VillageLink/prototype \
  /home/cobbler/Cobble/.venv/bin/python \
  /home/cobbler/Cobble/scripts/mcp_server.py
```

The runtime requires a **runtime** OpenAI API key, not an admin key.
The profile uses an environment secret reference,
`env:CONTROL_PLANE_API_KEY`. Never store the key in Git, paste it into
chat, or put it in this documentation. Its recovery copy was placed in
1Password. For an interactive session, enter the credential using a
non-echoing prompt rather than typing it as a shell command; future
supervision needs a secure secret-loading arrangement.

With the credential loaded into the environment:

```bash
~/.local/opt/cobble-tunnel/tunnel-client doctor \
  --profile cobble-memory --explain

~/.local/opt/cobble-tunnel/tunnel-client run \
  --profile cobble-memory
```

The tunnel runs in the **foreground** and must stay alive for ChatGPT to use
the server. In another terminal, its local readiness endpoint is:

```bash
curl -s http://127.0.0.1:8080/readyz
```

This returned `ready`. That checks the local runtime; it is **not by
itself** proof that every MCP tool works through ChatGPT.

In ChatGPT's Plugins directory, a custom **Cobble** MCP plugin was added,
selecting the **Cobble memory** tunnel (not Anna's) and **No authentication**
at the MCP application layer. The outbound tunnel authenticates to its
control plane using the runtime key and is scoped to the authorised
workspace. No-auth at the MCP layer is not a substitute for reviewing
workspace access and tunnel permissions. Do not expose this server as an
unauthenticated public HTTP endpoint.

## Observed outcome and current limits

**Successful live ChatGPT tool calls:**

- `search_memory("Memory is the masterpiece.")` returned four matching
  traces from McKay's local store.
- `inspect_star(centre_uri)` returned the hypothesis centre and three
  recorded Village Link rays.

**Not yet confirmed:** `get_trace` called from ChatGPT was blocked by a
platform safety check. The same tool had succeeded via a *local* independent
MCP client. The reason for the ChatGPT-side block has not been established;
do not describe ChatGPT full-text retrieval as working until tested.

This is a prototype: the tunnel process is manually started; startup
automation, auditing, access review, credential rotation, data minimisation
and selective permission design remain. The original memory stays under
user control on McKay, but **contents returned to ChatGPT travel through
ChatGPT's service**; the tunnel is not an end-to-end private computation
boundary.

For milestones and outstanding work, see [progress](progress.md).
