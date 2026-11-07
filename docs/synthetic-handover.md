# Claude → Mistral: synthetic memory handover

This deliberately bounded experiment tests the proposition that *Cobble owns
the memory, while interchangeable suppliers interpret it*. It does not
transmit any real archived memory.

## Sequence

1. In an isolated private store (default:
   `~/cobble-data/snug-handover-synthetic`), create a fictional
   lighthouse note with the invented phrase `VIOLET-OTTER-73`.
2. Claude receives **one explicitly selected indexed passage**, from
   that isolated store. Cobble records its answer locally.
3. Mistral receives **no passage**. It receives the expressly selected
   previous Claude exchange, read from Cobble's local store.
4. Compare Mistral's answer with the fictional phrase. A correct answer
   supports memory continuity by explicit local handoff; it does **not**
   prove that providers retain private state or autonomous retrieval works.

## Preview (no key, network, or writes)

```sh
PYTHONPATH=src python3 scripts/synthetic_handover.py --phase claude
PYTHONPATH=src python3 scripts/synthetic_handover.py --phase mistral
```

## Offline tests

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_synthetic_handover.py' -v
```

Both live stages require an explicit consent phrase, locally supplied provider
credential on stdin, and vendor workspace spending controls. The CLI never
passes secrets as arguments or writes them to disk. It records an immutable
attempt marker *before* invoking the model. A failed/ambiguous attempt cannot
be automatically retried.

Use the independent provider credentials and existing PowerShell
1Password-to-WSL stdin bridge for the separately authorised phases.
`--send-live --confirm 'I AUTHORIZE ONE SYNTHETIC HANDOVER API CALL'
--workspace-limit-confirmed` is required for each phase.

The phase answers and audit metadata stay under the experiment's private
directory, **not GitHub**. Real use incurs model charges and transmits
only the published-in-source synthetic note and prior synthetic conversation.
Review each provider's data-use settings before enabling.

The source document is not a real password. No actual private source corpus
is indexed or transmitted. If an attempt fails, inspect its ledger and billing
before undertaking any new test.
