# Meeting output: Candidate 2 review contract

This guide describes the proposed Candidate 2 correction, not the released or default-branch behaviour. Run the workbench only on loopback with a private store outside Git. The existing operator console is not a multi-user authentication or authorization system.

## First result (no supplier keys)

From the repository root, on a branch containing Candidate 2:

```sh
PYTHONPATH=src python -m unittest discover -s tests -p 'test_snug_live.py' -v
```

The HTTP tests use synthetic data and injected suppliers, with no external calls. The long-history case opens a local server, posts an agenda, selects a supplier contribution, adds 101 ordinary turns, and checks the actual output endpoint. Follow the existing workbench setup documentation for an interactive session; do not enable live suppliers for an offline exercise.

## Output and private history

The local GET /api/live/output?room_id=default returns an agenda string and a list of selected contributions, each containing only turn_id, provider and text. Operator posts contribute their text; completed supplier turns contribute their answer, not the operator question or complete exchange. The original agenda is the first recorded question under the current meeting convention. The output is reconstructed from complete retained history; /api/live/session remains limited to the latest 100 turns for display.

An empty meeting has an empty agenda and no contributions. Selection does not validate the truth of an utterance or authorize onward publication to a third party. The selected text itself can still contain sensitive information and needs operator judgment. Standing orders, provider payloads, context, usage and provider request identifiers are not projected. This is a local output interface, not a federation or nested-room transport implementation.

## Editorial controls and failure handling

The Room output control displays the actual projected agenda and selected contribution text, including older selected turns outside the display window. A successfully recorded post or supplier reply is distinct from a successfully selected room-voice contribution. If selection fails, the workbench reports the partial outcome and clears the recorded draft; do not resend it. The selection intent is captured at the start of Send. This is not an atomic record-and-publish transaction.

- Select or redact one eligible event at a time through the existing configure endpoint. Posted operator utterances and completed supplier answers are eligible; failed/unknown or foreign-room events are not.
- Redaction removes a contribution from the output projection but retains its underlying private ledger record; selection restores it.
- An output referencing missing or ineligible active selections fails instead of silently returning a partial result. Explicit invalid lifecycle values, malformed selection lists and redactions of unselected events also fail; absent fields in pre-Candidate-2 records remain compatible. This validation is not tamper evidence.
- Closed rooms reject output and new contributions; configuration remains available for reopening. Successful configuration invalidates outstanding supplier previews, including close/reopen transitions. Preview again before execution.
- Governance mutations and live actions are serialized within one local server process. An already executing supplier call is not cancelled by a later close request. Multi-process enforcement, authenticated principals, durable floor events, document content tabling and external tool authority are outside this correction.

## Validation and limitations

The regression tests exercise old selected turns, redaction/restoration, isolation, invalid selectors, closed rooms, stale previews and ambiguous supplier outcomes. They do not establish tamper-proof storage, actual provider behavioural continuity, semantic safety of selected text or production readiness. The projection changes the draft output response shape; experimental consumers should use contribution.text rather than raw question/answer fields.
