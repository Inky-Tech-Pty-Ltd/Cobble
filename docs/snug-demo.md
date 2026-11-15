# Snug's first working browser slice

This is an **offline** but corpus-backed implementation of the boardroom,
built for issue #29. It intentionally does not yet call paid suppliers.

## Start on McKay

Refresh the Cobble checkout and build the private search index if it does not
exist or is stale:

```sh
cd ~/Cobble
git pull --ff-only
PYTHONPATH=src python3 scripts/search_cobble.py build
PYTHONPATH=src python3 scripts/snug_demo_web.py
```

Open **http://127.0.0.1:8766/** in Windows Chrome (with WSL localhost
forwarding enabled). Never change the listener to `0.0.0.0`.

The boardroom lets you:

1. **Speak as Snug** from the Chair. The interface treats the human operator
   as Snug's mouthpiece, not as someone asking a separate Snug chatbot.
2. Move participant chairs by dragging or selecting their state: **at the table**
   (may speak/listen), **in the room** (listen-only), or **out** (neither). Only
   active connected rehearsal fixtures at the table can be addressed.
3. Read the scrollable, play-style transcript and expand the precise reviewed
   source and earlier-conversation context used for each new exchange.
4. Visit the **Archivist's room** to query indexed GitHub memories, inspect a
   bounded passage and select up to three passages for the next exchange.
5. Drag a local document onto the tabletop, or choose one with the file picker.
   **This is currently visual filename-only staging:** the browser does not
   read file content or send/store it in an exchange. Do not assume a tabling
   action has actually shared the document.
6. Preview the full immutable disclosure and consume a single-use approval
   for an offline exchange. Exchange events are stored in
   `~/cobble-data/snug/events` but are **not yet reloaded into the page**
   after restart.

Presence is currently enforced only in the local UI, not as separate supplier
memory or server-side participant access control. The offline fixture API remains separate; real GPT is explicitly gated by
`--live-gpt` and one-use approval. A **human guest**, human-owned corpus sharing, scoped
cross-membrane queries, private side-consultations and per-attendee meeting
histories are future changes requiring authentication and server-side
permissions, not shortcuts through the local browser.

**The fixtures do not provide AI answers.** The labels are rehearsals rather
than real provider identities. Costs are zero. The existing legacy console at
port 8765 remains separate.

## Live GPT: locally recorded conversation (opt-in)

**This is a paid API feature, separate from ChatGPT web conversations.** It
does not inherit ChatGPT Projects, account chat history, memory or tools.

1. Use the existing OpenAI API credential securely. The server accepts
   `OPENAI_API_KEY` in the local WSL process environment **or** the safer
   `--key-stdin` switch, which reads a one-time pipe from 1Password CLI.
   Never paste a key into ChatGPT, a browser, shell history or GitHub.
2. Stop the currently running demo with **Ctrl+C**. Update the checkout
   and start the same server with an explicit live switch:

   ```sh
   cd ~/Cobble
   git pull --ff-only
   PYTHONPATH=src python3 scripts/snug_demo_web.py --live-gpt
   ```


   From Windows PowerShell, the earlier 1Password CLI flow also works, with
   the existing private 1Password item reference substituted for the placeholder:

   ```powershell
   op read "op://YOUR_VAULT/YOUR_ITEM/credential" | wsl.exe -d Ubuntu -u cobbler -- bash -lc 'cd ~/Cobble && PYTHONPATH=src python3 scripts/snug_demo_web.py --live-gpt --key-stdin'
   ```

   The key crosses stdin only and is retained in server memory while it runs.
   Standard input closes after delivery; the server keeps running with the key in memory.

3. Open **http://127.0.0.1:8766/**. GPT takes a seat. Speak through Snug's
   input, choose **Review exact context**, read the full current question and
   prior exchanges plus estimated preflight cost, then approve one call.
4. The browser displays the response with provider token usage and **estimated**
   USD cost. Restarting the browser/server restores up to the most recent
   100 locally saved GPT turns. Snug passes up to four **completed** earlier
   GPT exchanges as explicit context. If needed for the 16 KB preflight bound,
   the oldest are omitted transparently in the review. Rejected or unknown-outcome turns are not replayed as
   supplier statements.

GPT output allowance is **2,048 tokens**, rather than the adapter's existing
256-token standalone test default. This is a per-call allowance, *not* a model
billing cap. The upstream OpenAI API and project/vendor billing settings remain
authoritative. All requests are text only with `store=false`, no tool calls,
no automatic retries, and no automatic corpus/archivist disclosure.

Durable record layout (outside Git):
`~/cobble-data/snug/live/default/{turns,attempts,outcomes}/<turn-id>.json`

- `turns`: exact user text and context snapshot, written and fsynced before
  any outbound call;
- `attempts`: immutable outbound attempt marker, written and fsynced before
  a network call may start;
- `outcomes`: response and usage, or `outcome_unknown` on an ambiguous
  failure.

A missing outcome after a crash is reported as **outcome unknown**. It is not
silently retried, since the provider may already have processed and billed it.
The session is authoritative; search indexes can later be derived from these
events. Current browser search still only covers existing indexed GitHub
material. The same UI's Claude/Mistral chairs remain **offline fixtures**.

Tests are keyless/synthetic. Before calling live, verify McKay's existing
project-level budget and local API key. Without `--live-gpt` the server
remains fully offline, just as before.

## Trust boundary

The server listens only on localhost and validates Host, Origin and a custom
request header. No source file or arbitrary path-serving endpoint exists.
Only the previously built SQLite index is queried. Inspect and search are
operator-local, not external disclosure. Source selection is limited to GitHub
and at most three bounded passages. The preview creates a server-held snapshot with an unguessable one-time approval
identifier, valid for five minutes. Both preview and retained event expose the
SHA-256 digest of the exact assembled request (including prior conversation text)
for evidence correlation; the digest is not proof that a memory claim is true. Exchange consumes that approval before
execution and uses the precise reviewed source and historical context, even if
an indexed passage or previously stored event changes afterward. Editing the
question, selection or supplier requires a new review. There is no durable
pre-network attempt ledger in this offline slice, and approval state is lost on
server restart. A preview is bounded local evidence, not authenticated or
transactionally complete historical evidence.

This local approval is **not** consent for a network API call. The HTTP exchange
endpoint refuses ordinary `confirmed=true` requests and accepts only a valid
one-time preview token. The default offline mode still refuses live calls.

Before live suppliers are enabled, implement a persistent pre-call ledger that
records attempts (including uncertain outcomes), an exact immutable reviewed
payload or digest gate, one-shot submission tokens, credentials solely in the
local server process, vendor account spending controls, safe error handling,
and tests. Do not interpret the existing adapter's estimated price ceiling as
a hard cap or assume vendor-side data retention is zero.

Run offline tests (also included in the Snug exchange workflow):

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_demo.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_exchange.py' -v
```

**Future:** connect Claude and Mistral to the same durable session ledger; add incremental search over new turns and per-participant permitted context; then enforce presence, tabled-document sharing and participant-specific histories on the server. The ultimate
`demo.cobble.link` location should use a separately permitted public
or synthetic corpus and appropriate authentication, not expose McKay.
