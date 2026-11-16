# Boardroom · first spatial design pass (November 2026)

This page is a **meeting**, not a dashboard. It is based on the two hand-drawn
boardroom / private-context sketches and subsequent operator discussion.

## Visible scene

- Snug, facing the human, upstage at the head of a rectangular boardroom table.
  The **human speaks through Snug**. The prompt has one obvious arrow: **Send**.
- A quiet corner skyscraper office with sky/city through large windows; a
  glazed office corridor stage-right, with a visible door and waiting suppliers.
- GPT, Claude and Mistral have distinct visual treatments, names, latest
  speech bubbles, per-supplier running **estimated** cost, and a padlock to
  inspect received context. The table contains the **scrollable shared
  conversation**, with older utterances visually narrower/fainter upstage.
- A folder at the foot of the table allows names of documents to be staged
  by drop or chooser (the bytes are **not** read, transmitted or durably
  tabled yet).
- On the scene itself, no permanent explanatory prose. Icon controls use
  accessible names and tooltips; technical details live in a separate
  information dialogue.

## Speaking and costs — current functional approximation

**Every human utterance is published to the local shared meeting transcript.**
The current server still performs **one supplier call per operator utterance**.
The first pass chooses that respondent when the utterance *begins* with a
participant's name or greeting (e.g., "Hey Mistral"), or defaults to the most
recent available supplier. No separate "address this participant" control is
required.

Supplier calls use the existing **exact frozen-context preview + one-time
approval token**, but the two operations happen automatically after one
human Send. This does **not** bypass server preflight checks or retrieve
private corpus material. Sending is an explicit user instruction to perform
one potentially billable API call. Failed/ambiguous calls are **not
automatically retried**. Secrets, tabled file contents and private corpus
passages are not added to outgoing context by this UI.

The current meeting is still Cobble's existing default persistent live
session. Running cost is the **sum of provider-estimated charges recorded
for this session**, including earlier turns before the redesign. It is not
a vendor invoice. A true start/end lifecycle, distinct meeting IDs and
retained meeting-specific documents and costs are the **next functional
milestone**, not a claim of this first visual pass.

## Private pane — paired by invocation

Click a participant's **padlock** to inspect that participant's consultations.
For every API call to that participant:

- **Left: Context passed** — the exact recorded outgoing payload (via a
  nested disclosure) plus its top-level instructions, current Snug utterance,
  private corpus material if present, and content digest.
- **Right: What [participant] heard** — the explicitly supplied previous
  exchanges with their original speaker attributions, plus the current
  Snug utterance. **Collapsed to a narrow right strip by default.**
- Both panes are synchronised by consultation, not independently scrolled
  through unrelated histories. Arrow controls advance the consultation
  selection, updating both panes as a pair.

This is an *API disclosure audit*, not a claim that stateless provider APIs
maintain hidden live hearing between requests.

## Honest boundaries

The current room model is not yet a physical, authenticated meeting with
enforced recipient entitlements. Moving a model into the glass corridor
prevents its **selection in this browser**, but the server does not yet
retain entrance/exit events or prevent providing older public exchanges when
that model returns. Model replies do not spontaneously interrupt one another;
Cobble still chooses at most one supplier per human utterance. Guests,
separate human identities, side-consultations, archival query negotiation,
retained private meeting documents and actual per-attendee heard histories
remain future work.

**Do not use the corridor or padlocks as a confidentiality guarantee yet.**

## Follow-on development order

1. Actual meeting lifecycle with begin/end, explicit membership events,
   per-meeting documents and cost accounting, preserving existing local
   history without loss.
2. Server-enforced room visibility and safe distribution of meeting events;
   no retroactive catch-up without permission.
3. Turn-taking and voluntary supplier contributions with observable social
   norms, coupled to token budget and interruption policy.
4. True document tabling and per-supplier private context retrieval.
5. Visual refinement on real McKay screen sizes: low-angle table typography,
   responsive portrait layout, richer distinct avatars, corridor transitions.

The design is intentionally a **first testable pass**, not a final visual
artwork. The crucial invariant is unchanged: **Cobble owns the persistent
conversation; the intelligence suppliers are replaceable.**
