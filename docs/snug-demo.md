# Cobble local meeting workspace and legacy boardroom

The local meeting service starts **offline** by default. With explicit flags
and locally supplied API credentials, GPT, Claude and Mistral can join the
same durable conversation. No model keys are committed to GitHub.

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

### Candidate 1: Meetings workspace

The default page at **http://127.0.0.1:8766/** is now a **lightweight
Meetings workspace**. It uses the Inky blue-grey palette, Cobble logo,
resizable/collapsible left sidebar, persistent (browser-local) sidebar width,
readable shared conversation, and supplier controls below the navigation.

- **Meetings** shows multiple durable local rooms. Use **+** beside
  Recent meetings to create a new, empty room, and click a room to switch.
  Click the title in the header to rename the active room; titles and each
  conversation's events are now persisted on McKay (not merely in the browser).
  The existing 3D boardroom remains the original **default** meeting; its
  historical records have not been moved, deleted or relabelled. On the
  first update, a title previously set for that original room in this browser
  migrates into the new server-side title registry. Autonomous chairing
  remains future work.
- A message goes **to the room** as an operator utterance. When no
  supplier is enabled, **Send records the message locally without requiring
  a reply**, an API key or a network call. With suppliers enabled the
  **Next reply** selector can choose a responding supplier or **None · post
  only**. Supplier replies still use the existing single-use review and
  approval-token mechanism. A leading address such as "Claude, ..." directs
  a supplier call unless **post only** is explicitly selected. Automatic
  team turn-taking and standing orders are **not** implemented.
- **The composer grows** as the operator types, up to a screen-relative cap;
  after a successful Send it contracts again. Shift+Enter inserts a newline.
- **Documents can be staged** by dragging local files onto the Meeting area,
  or clicking the paperclip in the composer. Up to eight file names are shown
  above the composer, each removable with ×. **These are local, volatile
  filename/size references only.** They are not opened, read, uploaded,
  persisted, or included in supplier requests. This restores the legacy
  *visual tabling* feature without misrepresenting it as shared context.
  Actual tabled-document context will require a separately audited server
  pathway.
- Each supplier card shows availability, estimated cumulative spend, a
  browser-only presence toggle, and a details (···) button. There is no
  per-supplier private-context control: all participating intelligences
  work from the meeting table. The details panel still exposes the
  **actual recorded outbound requests** (including history and any corpus
  passages), model and costs, without changing server permissions or models.
- **Senses** offers GitHub-only source search/inspection via the local
  index. The future design prioritises incoming diffs. Filesystems and
  other source classes are shown as status, not imaginary working connectors.
- **Memories** will be the graph of star credentials and rooms. It is
  currently an empty workspace, not a new memory graph implementation.
- **Intelligences** and **Setup** expose current provider and service status.
- **Help** links to these repository docs. The small ? in the header opens
  help for the current section in a separate tab.
- The empty meeting and sidebar no longer display explanatory placeholder
  text; status and limitations remain inspectable in Setup and the info panel.
- No supplier responds automatically unless the operator clicks Send.
  The one-time, exact, server-side preview/approval-token mechanism and
  append-only live-event ledger are unchanged. Browser presence controls
  are **not** security boundaries and cannot revoke disclosure.

**Important:** provider icons in Candidate 1 are local, approximate identity
markers, not official trademark artwork or endorsements. The existing
perspective boardroom remains available at **http://127.0.0.1:8766/boardroom**
for comparison and its filename-only staging controls.


### Candidate 3: Room weight and left-edge controls (26 November 2026)

**Read the source decisions:** [Room-weight design note](design/room-weight.md)
and [GitHub Issue #85 — why the crescents work this way](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/85).
The live interface's **Help → Room weight** link opens the decision on GitHub.

The same left-edge crescent now carries a family of *weight* meanings.
Click a **speech bubble's** edge to include or withdraw a posted human
contribution or completed supplier reply from the Room's outward voice.
Click the **left edge of a connected supplier's card** to give that supplier
the floor for the next manually sent request, or to release it.
Click **Joe's top-right edge** to toggle his default future posts between
ordinary table talk and the Room's outward voice. The Chair and standing
orders have a permanently heavy edge, but this does not publish the
standing orders. Individual posts remain independently adjustable.

Each interactive edge is an accessible button with hover, keyboard focus,
tooltip and `aria-pressed`. The guest interface is *read-only with respect to*
these choices. The server's immutable message ledger, voice/redaction
metadata, supplier preview/approval flow, and the guest's room-only
restriction are unchanged. Floor selection is browser-local and creates
**no** paid model calls by itself.

The visual experiment with broad orange fills has been withdrawn in favour
of slender crescents and existing Inky palette accents, especially membrane
blue `#0C94E8` and Claude's pink supplier tone. The **Membrane** entry
represents the boundary of this instance; smaller Room Doors are in
**Furniture → Doors**. The meeting's Door does not open the McKay instance.

### Workspace navigation

#### Senses

Incoming source material and its changes. GitHub archive search and
inspection currently work; change-first diff processing is a future feature.

#### Memories

Future navigable graph of star credentials and rooms, distinct from source
material. No graph population is implied by the placeholder workspace.

#### Intelligences

Configured suppliers, live availability and estimated cost. Browser-side
presence is not an access-control boundary. The supplier details (···) button
shows historical **outbound calls**, not a private context or private side room.

#### Meetings

The **+** beside Recent meetings creates another genuinely separate meeting;
select any title in the sidebar to return to that room. Each meeting has its
own ledger under `snug/live/rooms/<16-hex-digit-ID>/`, with a server-side
`room.json` holding the editable title. The original conversation remains in
`snug/live/default/` for the legacy boardroom; it is **not** renamed or
moved on disk. Titles and membership of the meeting list survive server
restarts. A browser remembers which meeting was selected, but not the
authoritative list or titles.

The convenor can **post their own message without any supplier present**.
Posts are recorded inside only that meeting's private ledger. A new supplier
request includes only up-to-four eligible previous exchanges **from the same
meeting**, subject to explicit preflight review and payload limits. A supplier
approval token cannot be used in another meeting. With a supplier selected,
each Send still calls only that supplier, with no automatic retry. A
procedural Chair and standing orders are not implemented yet.

Drag a file anywhere onto the Meetings workspace to **stage its name on the
table**, or click the paperclip next to the message box and choose local files.
The small chips above the composer are removable and exist only until the page
is reloaded. The browser reads no file contents, and the supplier receives no
staged file data. The UI labels this honestly so files are never mistaken for
shared context. We now show file-name chips without a long caption;
the paperclip tooltip, help and audit view still distinguish staged names
from file contents, which are **not yet transmitted**. File staging is
cleared on switching meetings so names do not leak between tables. The
message box grows as the operator types (up to 38% of viewport height,
capped at 360px), scrolling beyond that size.

Speaker messages align to the **same right margin** as the composer.
Supplier messages can extend to the composer's left edge, while Joe's
messages begin about **20% farther right** (10% on narrow screens). This
keeps the common reading frame but makes the operator visually distinct.

#### Setup

Local server, connection status and disclosure limits; link to the legacy
perspective boardroom.

#### Help

Links to these sections. The header's ? points to the current section
without sending meeting data to GitHub.

### Legacy perspective boardroom

The previous boardroom, now at \`/boardroom\`, lets you:

1. **Speak as Snug** from the Chair. The interface treats the human operator
   as Snug's mouthpiece, not as someone asking a separate Snug chatbot.
2. Move participant chairs by dragging or selecting their state: **at the table**
   (may speak/listen), **in the room** (listen-only), or **out** (neither). Only
   configured live suppliers (or offline rehearsals) at the table can be addressed.
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
memory or server-side participant access control. The offline fixture API remains separate; real suppliers are explicitly gated by
individual `--live-*` flags and one-use approval. A **human guest**, human-owned corpus sharing, scoped
cross-membrane queries, private side-consultations and per-attendee meeting
histories are future changes requiring authentication and server-side
permissions, not shortcuts through the local browser.

**The fixtures do not provide AI answers.** The labels are rehearsals rather
than real provider identities. Costs are zero. The existing legacy console at
port 8765 remains separate.

## Live GPT, Claude and Mistral: one locally recorded conversation (opt-in)

**This is a paid API feature.** The three supplier adapters are independent
of their consumer-chat products and subscriptions. They do not inherit
ChatGPT Projects, account conversation histories, account memory or tools.

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
   100 locally saved boardroom turns. Snug passes up to four **completed**
   earlier exchanges, *regardless of which supplier answered*, as explicit
   context. If needed for the 16 KB preflight bound,
   the oldest are omitted transparently in the review. Rejected or unknown-outcome turns are not replayed as
   supplier statements.

The boardroom output allowance is **2,048 tokens per supplier call**, rather
than the adapters' existing 256-token standalone defaults. This is a per-call allowance, *not* a model
billing cap. The upstream OpenAI API and project/vendor billing settings remain
authoritative. All requests are text only with no tool calls, no automatic
retries, and no automatic corpus/archivist disclosure. The OpenAI adapter
requests `store=false`; provider-side data handling varies by supplier.

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
material. Suppliers not enabled when starting the server remain offline
rehearsals (or disconnected, for GPT); their labels reveal that difference.

Tests are keyless/synthetic. Before calling live, verify McKay's existing
project-level budget and local API key. Without `--live-gpt` the server
remains fully offline, just as before.

### Start all three through the existing Windows 1Password CLI

The original GPT-only command (\`--live-gpt --key-stdin\`) still works. To
start **all three** participants, stop the running boardroom with Ctrl+C,
then in WSL update \`main\`:

\`\`\`bash
cd ~/Cobble
git pull --ff-only
PYTHONPATH=src python3 scripts/snug_demo_web.py --help
\`\`\`

Identify the **item IDs** of the three existing keys from 1Password. In
Windows PowerShell, list *metadata only* (no secret values):

\`\`\`powershell
$items = op item list --vault Employee --format json | ConvertFrom-Json
$items | ForEach-Object { $_ } |
  Where-Object { $_.title -match '(?i)openai|claude|mistral' } |
  Select-Object title, id
\`\`\`

Using those item IDs (not item titles containing punctuation), securely
pipe a **JSON object** directly from PowerShell to the new boardroom process.
Substitute the three placeholders below with the IDs shown above:

\`\`\`powershell
$gptId = 'REPLACE_WITH_OPENAI_ITEM_ID'
$claudeId = 'REPLACE_WITH_CLAUDE_ITEM_ID'
$mistralId = 'REPLACE_WITH_MISTRAL_ITEM_ID'

@{
  openai  = (op read "op://Employee/$gptId/credential")
  claude  = (op read "op://Employee/$claudeId/credential")
  mistral = (op read "op://Employee/$mistralId/credential")
} | ConvertTo-Json -Compress | wsl.exe -d Ubuntu -u cobbler -- bash -lc 'cd ~/Cobble && PYTHONPATH=src python3 scripts/snug_demo_web.py --live-gpt --live-claude --live-mistral --keys-json-stdin'
\`\`\`

**Do not display or paste the resulting JSON**, which contains the private
keys. Adjust the last URI segment if the vault item stores its API key under a
different field name than \`credential\`. The browser never receives the keys.
If any key is unavailable, the server rejects startup rather than silently
pretending that provider is live. No billable calls occur until a specific
outbound context is reviewed and submitted.

With three configured suppliers, address any participant at the table.
The **same** \`~/cobble-data/snug/live/default\` conversation record now
contains replies from all suppliers. A switch to a different supplier
sends up to four completed prior exchanges selected in the exact disclosure
preview, including their original attribution; it does not automatically grant
access to private corpus files. Usage and estimated costs remain per supplier.

For a smaller trial, choose only the desired \`--live-claude\` or
\`--live-mistral\` flags, and supply a JSON object with exactly those
provider names. GPT remains available when included. Other chairs show
offline rehearsals, not real model connectivity.

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

**Future:** add incremental search over newly recorded turns, a clearer Send
interaction and per-participant permitted context; then enforce presence,
tabled-document sharing and recipient-specific histories on the server. The ultimate
`demo.cobble.link` location should use a separately permitted public
or synthetic corpus and appropriate authentication, not expose McKay.


## Supplier replacement experiment (issue #29)

This is a reproducible continuity exercise, not an identity or reasoning certification.
Use synthetic data only. Start with a fresh private store and the keyless regression:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_snug_live.py' -v
```

The fixture test replaces the configured GPT adapter with Claude after recording a
decision and correction, preserves the same local ledger, rejects the removed
supplier, checks the reviewed history, and excludes a separate room's private marker.
It verifies context transport, not model comprehension.

For a live run, use the opt-in supplier setup above and a fresh meeting. Record
"Decision: budget 100 units", then "Correction: current budget 80 units; 100 is
superseded", then ask the first supplier to acknowledge the correction. Stop the
server and restart it with only a different supported supplier enabled, keeping the
same private store. Ask "What is the current budget, and what was superseded?"
Inspect the actual outbound history and recorded reply. Repeat with the third
supported supplier in a fresh equivalent run. Each run uses paid API calls.

| Check | Expected result |
| --- | --- |
| Durable record | Original decision and correction remain in the local ledger |
| Reviewed input | Both statements are present and ordered |
| Answer | 80 current, 100 superseded |
| Isolation | A synthetic marker in another room is absent from outbound context |
| Removed supplier | Cannot be called after restart with its adapter disabled |

Record provider/model, source commit, exact reviewed context, answer, outcome,
latency if available, usage and estimated cost. Report each check separately as
pass, fail or not run. Do not publish private payloads or credentials. A wrong
answer with correct context is a behavioural failure, not storage loss.
The live meeting currently sends at most four eligible previous exchanges, subject
to preflight limits, and no selected corpus passages; a long-gap recall task is a
separate experiment. The offline archive-selection path is not proof of live
retrieval. No Village Link dependency is required by accepted ADR-003.
