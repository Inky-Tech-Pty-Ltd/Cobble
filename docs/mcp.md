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
- `read_github_discussion(repository, number, offset=0, max_chars=12000)` —
  read paginated text from a **previously archived** GitHub Discussion,
  including comments and replies, with original author and source URL.

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


## Next integration exercise: a live GitHub Discussion

GitHub Discussion #8 in the Cobble repository is a real-world test input.
This exercise deliberately uses **preserved local memory**, not a GitHub
call made by the MCP server. On McKay, after updating the Cobble checkout:

```bash
PYTHONPATH=src python scripts/import_github_conversations.py Inky-Tech-Pty-Ltd/Cobble
PYTHONPATH=src:../VillageLink/prototype python -m unittest discover -s tests -v
```

The first command contacts GitHub from an **ingestion tool** and writes
versioned records under the local memory store. The second command includes
offline tests of the reader's pagination, original provenance, path
validation and archive digest. The runtime tunnel must then be restarted
to load the new MCP tool definition.

From ChatGPT, call `read_github_discussion` with repository
`Inky-Tech-Pty-Ltd/Cobble` and number `8`. If the response has a non-null
`next_offset`, call again with that offset until the entire snapshot has
been retrieved. The read operation makes **no GitHub network request**.
It does **not** mint a Village Link or assert two traces are equivalent.

This experimental reader accesses a specific archived conversation by
its repository and discussion number. It is not yet a full search index
over all GitHub conversations, and the archive represents a snapshot
that will only change when the importer is run again.


## Scoped Arena operations — experimental, 30 October 2026

The existing memory tunnel can also expose three small operations for the
derived Arena. They reuse the same outbound tunnel and require **no public
SSH endpoint or incoming port**:

- `arena_status(name="arena-a")`: read the Arena's population and five
  resource budgets, without returning source text.
- `verify_arena(name="arena-a")`: rehash **all files in the local Arena
  copy**, compare against the copied manifest, and report aggregate byte/file
  counts. It does not write to the source archive or the Arena.
- `run_arena_tests()`: optionally execute the **one fixed, offline test
  suite** `test_arena_one.py` in the Cobble checkout, with a 45-second
  timeout and an explicit locally configured opt-in.

These do **not** constitute an unrestricted server shell. The tools accept
no arbitrary command strings, paths outside `~/cobble-arenas/`, environment
variables or shell arguments. The fixed test process runs with a minimal
environment that does not forward tunnel or GitHub tokens. The test suite is
still executable Python code on McKay, so review repository changes before
enabling it; it is not an OS sandbox.

The sensitive source archive remains outside the control boundary for all
three tools. The status and integrity tools can read the **derived** Arena,
but they return no raw conversation or file contents. The existing memory
read tools have their previous capabilities and limitations.

### Operator enablement

1. Publish reviewed tool code via the normal Puck-GPT express workflow.
2. On McKay, update the Cobble checkout and run the new **offline tests**:

   ```sh
   cd ~/Cobble
   git pull --ff-only
   PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_remote_ops.py' -v
   ```

3. Restart the existing `cobble-memory` Secure MCP Tunnel so that its
   subprocess loads the newly published tool definitions. In ChatGPT,
   refresh the Cobble plugin tools; if necessary, start a new chat.
4. For **status and integrity checks**, no additional environment flag
   is necessary. Puck can call those two tools from a connected chat.
5. **Only if the operator explicitly approves remote test execution**,
   arrange for the MCP subprocess to inherit
   `COBBLE_MCP_ALLOW_ARENA_TESTS=1`. This can be set in its local
   stdio command configuration; do not commit credentials or put secrets
   in chat. With the flag absent or any other value, the test tool
   refuses to execute. Restart the tunnel after changing the flag.

This is a reversible, incremental bridge from read-only retrieval to bounded
agentic checks. Later, **separately reviewed and explicitly authorised**
Arena-only actions might add an operation dispatcher for creating derived
experiments, traversing the copied corpus and running controlled providers.
Do not smuggle arbitrary shell access, network crawling, publication rights
or writes into `~/cobble-data` under this diagnostic interface.

### Governance boundary

The tunnel still uses the workspace's existing access and control-plane
authentication; its local MCP layer has no separate per-tool user login.
Therefore any workspace principal who is permitted to invoke these tools
may see the Arena's metadata, and (when the flag is enabled) run the fixed
test. Treat adding *any* action as a security-boundary decision. Maintain
reviewable code and a way to disable the service by stopping the tunnel.
