# Snug: three intelligence suppliers, one local memory (7 November 2026)

**Status: live synthetic handover succeeded.** This is a development milestone,
not a production launch or proof of autonomous retrieval.

## What we demonstrated

Cobble kept a fictional lighthouse note and the exchange history in a private
local store on McKay. Each visiting intelligence received only the context
explicitly selected for its turn:

| Phase | Intelligence | Original memory passages sent | Prior exchanges sent | Live outcome |
| --- | --- | ---: | ---: | --- |
| 1 | Claude (Helen) | 1 | 0 | Identified `VIOLET-OTTER-73` |
| 2 | Mistral | 0 | 1 (Claude) | Identified `VIOLET-OTTER-73` |
| 3 | OpenAI GPT-6 Luna | 0 | 1 (Mistral) | Identified `VIOLET-OTTER-73` |

The third answer was the exact invented phrase. Its local event ID is
`54a7aa7cea7e4633b69cb80a037fdb6c`, and its recorded usage is
209 input tokens and 55 output tokens, with estimated provider cost
US$0.0000484 (estimate, not billed charge).

The earlier live synthetic events were Claude
`5addfaaf6e2f4b0d90f5ebc814376365` and Mistral
`6bfe86c67a724c03923c8e4fc2b307e4`. These are *private-store*
event IDs, not downloadable GitHub artifacts.

Combined estimated cost of the three live handover calls: **US$0.0002118**,
excluding the separate first-hello trials and local computing.

**What this supports:** memory and exchange continuity can be held locally by
Cobble, independently of the supplier responding. Context is transferred
explicitly by Cobble, not inherited through the vendors' hosted conversations.

**What it does not support:** automatic relevance-based retrieval; general
identity resolution; production-grade privacy/governance; guaranteed data
non-retention at vendors; long-running relationship continuity; billing
accuracy beyond provider-token estimates.

## Implementation and audit trail

- [PR #38](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/38):
  Mistral adapter and offline tests.
- [PR #39](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/39):
  one-shot Mistral live-call gate.
- [PR #40](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/40):
  isolated Claude-to-Mistral synthetic handover.
- [PR #41](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/41):
  OpenAI Responses adapter and integration into neutral exchange.
- [PR #42](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/42):
  corrected GPT-6 Luna pricing estimates.
- [PR #43](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/43):
  first GPT hello gate and audit.
- [PR #44](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/44):
  response parser fix for reasoning output items.
- [PR #45](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/45):
  explicitly reviewed, separately audited first-call retry.
- [PR #46](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/46):
  third GPT phase in the handover.

An initial GPT hello did reach OpenAI, but the parser rejected a non-message
output item before event storage. The audit retained
`cb416b2eac064074a8108b6af6da13cf` as `outcome_unknown`.
After the parser was corrected and tested, a separately authorised retry
completed, linked back to the original attempt. The previous audit record
was not erased or overwritten. This incident is a useful demonstration of
both the need for robust provider response handling and the reason for
pre-call durable audit markers.

Authentication and spending controls were set up in dedicated provider
projects or workspaces, with credentials held in 1Password and passed into
McKay via stdin. No API keys are stored in this repository. No actual private
corpus documents were sent as part of the synthetic handover.

For reproducibility (offline):

```sh
cd ~/Cobble
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_synthetic_handover.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openai_adapter.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openai_first_call.py' -v
PYTHONPATH=src python3 scripts/synthetic_handover.py --phase openai
```

Do **not** rerun completed live stages: one-shot ledgers intentionally prevent
repeat calls. For full implementation instructions, see
[synthetic-handover.md](synthetic-handover.md),
[openai-adapter.md](openai-adapter.md) and
[openai-first-live.md](openai-first-live.md).

## Next engineering milestone: navigate real corpus

Move from explicit human selection of a synthetic note to one end-to-end
real-corpus question with auditable selection and disclosure:
1. Search the local GitHub corpus for a specific research question (for
   example, Sankarshan's G1 retrieval work).
2. Explain and inspect the selected passages, source IDs and permission scope.
3. Disclose only approved context to one selected supplier.
4. Record the reply, exact disclosed context references and provider usage.
5. Repeat against ChatGPT and the two hosted filesystem corpora after
   validating their freshness.

The four corpus sources remain **ChatGPT, GitHub, Inky Tech filesystem and
Village Link filesystem**. Their archive/sync/gap/navigation maturity should
be assessed separately; the supplier demonstration does not complete that
4×4 ingestion/navigation programme.

## Product demo direction (concept, not committed scope)

A small, whimsical **2D boardroom** could make the architecture tangible:
supplier chairs slide to/from the table to enable participation; running token
costs appear above participants; the default transcript shows only operator
prompts and supplier answers; a chevron reveals exactly what contextual material
was sent. A shallow/deep context slider expresses cost and disclosure tradeoffs.

Later setup can connect filesystems, email, databases, GitHub and social
accounts. Cross-source identity linking is an early salience task, but should
keep provenance, confidence, reversibility and authorisation distinct.

A first compelling demo should not require a commercial sign-up system,
multi-tenant hosted platform or sophisticated 3D animation. Actual supplier
selection, disclosed context and accounting should drive the UI, rather than
merely being theatrical effects.

## Commercial proposition to test

**Cobble owns memory and tools; intelligence suppliers use them.**

The prospective business includes margin on supplier tokens, but its
differentiation is local continuity, selective disclosure, supplier choice,
auditability and spend controls—not simply reselling model tokens. The
boardroom would be a visual expression of these real architectural properties.
