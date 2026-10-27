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


## Independent adversarial benchmark (CI run #38505600739)

A second benchmark separates relevance annotations from graph membership and
introduces deliberately wrong and incomplete graph relationships.

| Architecture | Mean precision@4 | Mean recall@4 | Linked irrelevant retrieved |
| --- | ---: | ---: | ---: |
| A0 flat | 0.3750 | 0.6250 | 0 |
| A1 linked | 0.5000 | 0.8750 | 2 |

This is a materially stronger result than the original seeded sanity check,
but it remains bounded. A1 improves aggregate retrieval under these four
independently annotated synthetic queries, while also promoting two deliberately
mislinked irrelevant traces. The graph therefore demonstrates both **utility**
and **harm sensitivity**. It is not an unqualified retrieval improvement.

Per-query behavior is mixed: graph assistance has no recall gain on some cases
and improves recall on others. Relevant traces intentionally omitted from graph
membership remain dependent on lexical retrieval. This supports continued
experimentation with graph-assisted retrieval while making graph-construction
quality a first-class assurance problem.

CI executed the complete suite plus both evaluation harnesses successfully:
https://github.com/Inky-Tech-Pty-Ltd/Cobble/actions/runs/38505600739

### Consequence for the architecture decision

The previous label-leakage blocker is partially addressed: relevance labels are
now stored independently from graph membership and the graph contains known
errors. However, memberships are still hand-seeded. The benchmark therefore
does **not** establish that Cobble can infer useful relationships reliably from
real memories.

The next gate is observation/lifecycle semantics, followed by a focused Star
Credential ablation review. Automated graph induction should remain deferred
until those semantics and failure modes are explicit.

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

## Observation contract and lifecycle hardening

The observation layer now uses experimental schema version `0.1` with
separate retrieval, time, integrity, and semantic dimensions.

Key invariants are executable:

- `not_checked` is distinct from `unavailable`;
- retrieval attempt time can differ from observation-record time;
- source event time is optional and is never inferred;
- availability does not imply integrity;
- observations remain explicitly non-authoritative and truth-unassessed;
- tampering with those semantic boundaries fails validation.

CI initially found that the Python validator did not enforce the schema's
non-authoritative semantic invariant. The validator was corrected; the test was
retained. The corrected suite passed in run #38505873518.

## Star Credential representation ablation (CI run #38505938236)

The same benchmark memberships were encoded three ways:

1. current Star Credential membership;
2. a simple hypothesis/group collection;
3. centre-to-member pairwise relationships with the shared centre retained so
   co-membership can be reconstructed.

All three produced identical retrieval rankings for every independent benchmark
query:

- `collection_matches_star: true`
- `pairwise_reconstructed_matches_star: true`

The full suite completed **38 tests successfully**.

This result is intentionally narrow. It demonstrates that Cobble's current
ranking algorithm consumes **recoverable co-membership**, not the specific
Star Credential syntax. It does not establish that collections or reconstructed
pairwise relationships have equivalent VillageLink publication, provenance,
validation, interchange, or governance semantics.

### Updated architectural disposition

- Stable trace identity: **retain**.
- Hypothesis/group identity: **retain**, because pairwise reconstruction still
  requires a common grouping identity.
- Star Credential syntax: **retain experimentally, but no longer justify it
  solely by Cobble retrieval utility**.
- Observation contract 0.1: **retain experimentally**, with production
  promotion blocked on authentication, retention, privacy, integrity, and
  transactional guarantees.
- Automated graph induction: **defer**.
