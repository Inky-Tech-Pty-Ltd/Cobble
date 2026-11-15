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
memory or server-side participant access control. The API remains an offline
fixture executor. A **human guest**, human-owned corpus sharing, scoped
cross-membrane queries, private side-consultations and per-attendee meeting
histories are future changes requiring authentication and server-side
permissions, not shortcuts through the local browser.

**The fixtures do not provide AI answers.** The labels are rehearsals rather
than real provider identities. Costs are zero. The existing legacy console at
port 8765 remains separate.

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
one-time preview token. Live suppliers remain unavailable.

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

**Future:** replace the fixture control with genuine approved, audited calls
to Claude, Mistral and GPT; show token usage and estimated USD cost,
then enforce presence, tabled-document sharing and participant-specific history on the server. The ultimate
`demo.cobble.link` location should use a separately permitted public
or synthetic corpus and appropriate authentication, not expose McKay.
