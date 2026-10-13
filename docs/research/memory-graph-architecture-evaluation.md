# Cobble memory graph architecture evaluation

**Tracking:** Cobble #1. **Status:** Experimental protocol, not normative.

## Research objective

Assess the incremental functional value of hypothesis-centred Village Link
grouping and append-only source observations without extending the VillageLink
primitive or implying evidence of identity continuity.

## Architectures and controls

- **A0 flat:** lexical retrieval over independent trace texts.
- **A1 linked:** identical lexical retrieval with a +2 bonus for traces
  sharing an explicitly seeded Star Credential group with the query anchor.
- **A2 evidence-aware:** identical ranking to A1, with availability-history
  reporting from an append-only observation sequence.

Each arm has the same 24 synthetic trace texts, six anchored queries,
23 candidates per query, deterministic lexical tokenization, retrieval budget
of four, and the same reference relevance labels. No model is invoked. A0
has source URIs and the same content; it lacks star relationships.
No source dereferencing occurs during ranking.

The corpus deliberately *seeds* the correct groups and uses those same groups
for relevance labels. This is **label leakage by construction**: positive
performance of A1 is a mechanistic sanity check, not an unbiased measure of
real-world graph accuracy. It must not be claimed as proof that graph inference
improves memory retrieval. A future independent annotation set and out-of-sample
evaluation are necessary.

## Metrics

Precision@4, recall@4, availability history recovered, and structural ablations.
The test explicitly asserts that A1 and A2 share retrieval rankings: observation
metadata must not be presented as a retrieval-quality gain. Status 'available'
is historical retrieval status, not verified semantic truth.

## Failure and risk coverage

Tests examine deterministic replay, equal candidate pool/budget, missing
observations, unavailable/moved/restricted sources, ablation, and the boundary
between links and verification. Core Cobble tests separately exercise missing
Village Link ray detection. Transactional integrity, source content modification
detection, concurrency, authenticated observations and real agent/model
portability remain untested and are promotion risks.

## Reproduce

From Cobble with VillageLink cloned as a sibling:

```sh
PYTHONPATH=src:../VillageLink/prototype python3 -m unittest discover -s tests -v
PYTHONPATH=src:../VillageLink/prototype python3 scripts/evaluate_memory_graph.py
```

JSON output is deterministic and suitable for CI comparison. The report and ADR
must distinguish experimentally *demonstrated structural capabilities* from
hypotheses that require future testing.
