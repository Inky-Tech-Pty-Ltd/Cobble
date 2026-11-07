# Mistral's first live telephone call: one-shot safety gate

**Status:** source implementation; this runner has not made a live API call.
The user has accessed Mistral Studio and previously tested a direct API call. Funding, data-use settings, and current spend limits have not been verified.

The operator must verify spending controls in Mistral Studio, review the
applicable data-use terms, configure a local API key and authorise the
specific harmless call before any network request.

## Scope

- Only a fixed harmless greeting is sendable through this first-call CLI.
- No ChatGPT, GitHub, InkyTech or VillageLink source excerpts; no previous
  conversation or private search result; no arbitrary user prompt.
- Default invocation is an offline, keyless preview. Status also reads only
  local files. Merely checking out or importing the module performs no call.
- Live call requires THREE conditions: `--send-live`, exact consent phrase,
  and affirmative operator acknowledgement of vendor workspace spend limits.
  It also requires a local `MISTRAL_API_KEY` in the process environment.
- The code still uses the Mistral Small Chat Completions adapter and 256 output
  tokens, without streaming, retries, tools, cache or redirect following.
- Local preflight estimates are NOT guaranteed maximum charges. A vendor
  workspace limit is a separate independent financial control.

## Offline acceptance on McKay

After switching to this PR's feature branch:

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mistral_first_call.py' -v
    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_mistral_adapter.py' -v
    PYTHONPATH=src python3 scripts/first_live_mistral.py
    PYTHONPATH=src python3 scripts/first_live_mistral.py --status

Preview shows the model, bound on input bytes, local estimate, and a zero
count of selected memories and previous exchanges. It does **not** read an
API key, contact Mistral, or write an event or audit entry.

## Durable attempt-before-send journal

On a future **explicitly authorised** live call, a private
`~/cobble-data/snug/provider-attempts/first-live-mistral.json` marker
is atomically written BEFORE the network call. This is a one-shot lock.
An immutable `ATTEMPT-ID.outcome.json` is written afterwards when possible.
On success it references a Snug exchange event that preserves the provider
message ID, returned token usage and *estimated* USD charge. Failure records
`outcome_unknown`, with `actual_charge_usd: null`: a timeout may already
have incurred charges. A crash may leave only the marker; that also means
**unknown**, not no charge.

No attempt is automatically retried, including after an ambiguous error.
Re-arming or repeating must be a separate, audited operator decision.
All audit and exchange records remain in `~/cobble-data`, never in Git.

## Future human-controlled activation checklist

1. On https://console.mistral.ai/ inspect the appropriate workspace/project and
   its billing controls. Confirm that a low spend limit is actually enforced.
2. Review the current Mistral API data-processing and training terms/settings.
   Do not send private memory until policy has been independently verified.
3. Use a locally stored MISTRAL_API_KEY, never paste a key into chat or Git.
4. Run the keyless preview, and approve the exact harmless
   greeting. Only then will we guide the operator through the separately
   gated live command. We do **not** include a ready-to-copy live invocation
   here to reduce accidental charges or disclosure.

## Important limitations

- A workspace monthly spend limit is independent of our local **estimate**;
  check billing after the first call and do not interpret the estimate as
  an invoice or a financial guarantee.
- There is no integration with vendor billing to reconcile actual charges.
- The one-shot ledger is local and single-machine only, not a distributed
  transaction system or a customer-ready payment service.
- There is no automatic retry. Uncertain outcomes require human checking.
- No API call may take place in GitHub CI; all tests use synthetic adapters.
- This path is **only for the first empty-memory call**. Connecting
  real inherited memories requires a distinct consent/privacy increment.
