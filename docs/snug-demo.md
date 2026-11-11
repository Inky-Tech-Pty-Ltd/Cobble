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

1. Search the *indexed GitHub conversation* corpus on McKay.
2. Expand each result and see its exact bounded passage.
3. Select up to three memory IDs and preview the full bounded source passages,
   question, and any earlier exchange questions and answers supplied as context.
4. Execute the **one-time reviewed snapshot** through an offline fixture. The
   event is persisted in `~/cobble-data/snug/events` with source references.
5. Move between Amber and Indigo rehearsal chairs and explicitly re-review
   the next snapshot, including whichever earlier exchanges are included.

**The fixtures do not provide AI answers.** The labels are rehearsals rather
than real provider identities. Costs are zero. The existing legacy console at
port 8765 remains separate.

## Trust boundary

The server listens only on localhost and validates Host, Origin and a custom
request header. No source file or arbitrary path-serving endpoint exists.
Only the previously built SQLite index is queried. Inspect and search are
operator-local, not external disclosure. Source selection is limited to GitHub
and at most three bounded passages. The preview creates a server-held snapshot with an unguessable one-time approval
identifier, valid for five minutes. Exchange consumes that approval before
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
to Helen/Claude, Mistral and GPT; show token usage and estimated USD cost,
then make the chairs draggable rather than merely selectable. The ultimate
`demo.cobble.link` location should use a separately permitted public
or synthetic corpus and appropriate authentication, not expose McKay.
