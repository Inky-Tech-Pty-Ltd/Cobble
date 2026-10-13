# Evidence-aware memory graph: evaluation and disposition

**Status:** Research result for controlled synthetic experiment  
**Date:** 2026-10-13

## Design

The deterministic harness uses 24 synthetic traces, six anchored queries,
four retrieved candidates per query, and a common lexical ranker. A0 contains
only flat traces. A1 adds seeded hypothesis membership. A2 preserves A1
rankings while exposing append-only observation history.

## Measured results (CI run #38337374916)

| Architecture | Mean precision@4 | Mean recall@4 |
| --- | ---: | ---: |
| A0 | 0.4583 | 0.6111 |
| A1 | 0.7500 | 1.0000 |
| A2 | 0.7500 | 1.0000 |

The full test suite completed **20 tests successfully** using the actual
VillageLink prototype codec. A1's improvement is expected under the deliberately
seeded relevance labels; **it must not be generalized** to unseen memories.
A2 has no retrieval gain over A1 in this harness. Its incremental utility
is historical source-availability reporting. See the Actions run:
https://github.com/Inky-Tech-Pty-Ltd/Cobble/actions/runs/38337374916

## Results that the tests establish

- A0/A1/A2 use an equal candidate set and retrieval budget.
- A1 and A2 have identical relevance rankings in this harness.
- Removal of star relations from A1 reproduces A0 rankings exactly.
- Removal of observations from A2 reproduces A1's unknown retrieval statuses.
- The A2 observation history for T01 preserves `available` followed by
  `unavailable`, without changing the underlying trace.
- The existing graph inspector rejects missing rays rather than quietly
  presenting an incomplete Star Credential.

Reproduce the exact precision and recall numbers using
`python scripts/evaluate_memory_graph.py`. Because seeded groups are also
used as relevance labels, **these numbers are internal sanity checks only**,
not evidence of an externally validated retrieval improvement.

## Interpretation

The graph and observation layer provide different capabilities: group-aware
ranking and historical source-status reporting. Neither has yet earned a
production architectural obligation. This test is incapable of assessing
quality of graph induction, real provider continuity, tamper resistance,
semantic truth, transaction safety or operational costs.

## Proposed disposition

- Stable trace URI and existing star construction: **retain**.
- Graph inspection: **retain experimentally**, subject to adversarial testing.
- Append-only observations: **revise before promotion**; ensure retention,
  integrity and verification of status claims.
- LLM inference, confidence/reputation and plugins: **defer**.

**Decision gate:** Proposed ADR, not accepted. Maintainer review and a
non-leaking external annotation benchmark are required before an evidence-
based claim of retrieval superiority or promotion into reference architecture.
