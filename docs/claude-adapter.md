# Claude adapter: offline readiness and explicit live gate

**Status (6 Nov 2026):** code prototype, keyless dry run only.
Contains an optional Anthropic HTTPS implementation behind `allow_network=True`,
but no executable user-facing live-call command is provided. The organisation
had $0.00 credits at reconnaissance. Nothing here purchases credits, creates
a key, contacts Anthropic, or transmits the private source corpus.

## Why this increment

Snug owns local memory; GPT, Claude and Mistral are visitors. The previously
merged exchange stored `network_calls: 0` and `provider_cost: 0` for simulated
intelligences. A real Claude response now carries model, message ID, input and
output token counts and a local *estimated* charge. Real billing is authoritative.
The existing offline fixture behaviour and event format remain readable.

## API choices (verify before real use)

- Endpoint: POST https://api.anthropic.com/v1/messages; API version 2026-10-21.
- Model: `claude-haiku-5-5`; max output 256 tokens; adaptive thinking explicitly disabled for this simple bounded text-only path. No streaming, caching,
  tools, web access or retries; fixed endpoint, no HTTP redirects.
- Header authentication from the **local** ANTHROPIC_API_KEY environment only
  when a live adapter is explicitly enabled. Never put keys in Git, chat,
  CLI arguments or screenshots.
- Indicative published USD pricing for Haiku 5.5 under 100K prompt tokens:
  $0.10/million input tokens and $0.50/million output tokens.
- This code has a 16,000-byte request preflight cap, a 256-token output cap
  and a $0.01 preflight **estimate threshold**. Preflight calculations based
  on UTF-8 bytes are *not authoritative token counts* and **are not a hard
  vendor spending limit**. Price tiers, taxes, regional rates and vendor
  pricing changes can alter real costs.

Official API references:
- https://platform.claude.com/docs/en/api/python/messages/create
- https://platform.claude.com/docs/en/api/versioning
- https://platform.claude.com/docs/en/models/haiku-5-5/overview

## First McKay acceptance (offline, no keys)

From the feature branch:

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_claude_adapter.py' -v
    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_exchange.py' -v

Then preview a harmless, memory-free consultation:

    PYTHONPATH=src python3 scripts/preview_claude.py \
      --question 'Hello Helen. What is your role?'

Then preview ONE already indexed, explicitly selected memory:

    PYTHONPATH=src python3 scripts/preview_claude.py \
      --question 'What does this earlier memory say?' \
      --allow-source github \
      --memory-id 1dea2041445ab800580a28b6

Both commands print **metadata only**: chosen model, selected source IDs,
estimated budget and a statement that no data was transmitted. They DO NOT
read or use any API key, transmit source content or append an exchange event.

## Tests and privacy

- Offline tests inject a synthetic transport and verify exact selected
  memories, earlier exchange handoff, accounting and failure behaviour.
- A normal `ClaudeAdapter()` refuses to call the network even when an API
  key exists. The existing CLI `snug_exchange.py` still offers only
  the two simulated fixtures. A live provider requires a separately
  supplied adapter with explicit network enablement.
- Memory disclosures remain selected by exact document ID and checked
  against source-family allowlists *before* an adapter is invoked.
- The local exchange records full authorised passages and replies.
  They belong in the private encrypted-backup scope, never GitHub.
- A provider error after transmission can incur vendor charges without a
  successful exchange event. A durable attempted-call ledger, duplicate
  prevention and robust reconciliation remain required before production.
- Model token responses permit a pricing **estimate**, not final invoices.
- Do not treat the local preflight threshold as a firm hard cap; implement
  account/workspace budget restrictions on the vendor platform first.

## Live activation is deliberately deferred

Before conducting the first real call: obtain explicit approval for
the transmitted question/context, establish a small prepaid funding amount
and platform workspace spending controls, create an expiry-bounded API key
stored securely on McKay, add an operator CLI with an explicit live-confirm
switch and durable attempted-call accounting, then verify with a question
that contains **no inherited memory**. Only after that trial should we
allow a single selected archived passage to cross the provider boundary.

The user is not being asked to buy credits or create an API key for this PR.
