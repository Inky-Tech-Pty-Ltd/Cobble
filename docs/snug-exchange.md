# Snug's telephone exchange — offline fixture

**Status:** first provider-neutral seam; two *simulated* providers only.
No real OpenAI, Anthropic or Mistral API call is made by this code.
The existing 13,217-document local index is the retrieval source.

## What it proves

- An operator chooses one of two identically shaped intelligence adapters.
- Selected source IDs are checked against an explicit per-request source
  allowlist *before* any data reaches the adapter.
- The user can explicitly attach prior exchange IDs after changing providers.
- A record of the question, response, participant, provider, selected memory
  passages, their source references and hashes, and prior exchange IDs is
  saved immutably in the private store.
- The common local corpus continues to exist when a fixture changes.
- No interpretation, memory salience or privacy judgement is assigned to Snug.

## Synthetic tests on McKay

From the `puck/snug-provider-exchange-offline` branch:

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_snug_exchange.py' -v

## Manual offline experiment

These commands create private records under `~/cobble-data/snug/events/`.
Choose the known GitHub issue discovered by the earlier search:

    PYTHONPATH=src python3 scripts/snug_exchange.py ask \
      --participant operator --provider fixture-amber \
      --question 'What source memory have you received?' \
      --allow-source github \
      --memory-id 1dea2041445ab800580a28b6

The command prints a 32-character `event_id`. Use it in the second call:

    PYTHONPATH=src python3 scripts/snug_exchange.py ask \
      --participant operator --provider fixture-indigo \
      --question 'Can you see the previous exchange?' \
      --previous EVENT_ID_FROM_FIRST_CALL

Second call supplies the chosen earlier question and answer but **not**
all other exchanges and **not** any implicit archive access. Both providers
only report what they received; neither reasons or provides an AI answer.
Original archives and Arena A are not modified.

## Privacy and integration boundaries

- **Operator-only command line:** no network listener, no public API.
- Only exact search-document IDs explicitly selected by the operator are
  retrieved. There is no autonomous source browsing.
- A request can include at most three 1,500-character passages and four
  prior events. Larger contexts need a separately designed policy.
- Selecting a memory requires explicit `--allow-source` matching its
  recorded source family. An unauthorised or missing ID raises before
  the fixture is called; it does not create a successful exchange event.
- Source selection is a demonstration of an operator disclosure boundary,
  *not* Snug exercising socially learned discretion.
- Saved events contain real private question/answer data and selected
  passages. They are outside Git and must remain in the protected backup.
- The tool does not log failed external calls, since **there are no real
  providers yet**. An actual adapter will require failure and cost accounting.
- Event persistence is immutable per generated UUID. There is not yet
  a transactional multi-event timeline or tenant isolation.
- The store and FTS5 index must remain private to McKay. No customer-facing
  use, external access or real private-data disclosure is authorised by
  this experiment.

## Next acceptance gate

Run the synthetic tests and two CLI fixtures locally, confirm that the
second exchange explicitly references the first and that both immutable
records exist. Then review/merge.

Next real capability: implement explicit operator-approved provider
adapters for GPT, Claude and Mistral with provider-specific credentials,
cost ceilings, auditable disclosure, disconnect controls and a recorded
exchange/usage ledger. That step crosses external trust and billing boundaries
and needs separate confirmation before any real corpus leaves McKay.
