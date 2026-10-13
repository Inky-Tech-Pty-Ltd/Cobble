# ADR 001: Evidence-aware local memory graph

**Status: Proposed — experimental, not accepted**  
**Tracking:** Cobble issue #1  
**Date:** 2026-10-13

## Context

Cobble currently mints a hypothesis-centre trace, a Star Credential with
`type`, `A` and `B`, and Village Link rays. A source URI may disappear;
a link asserts proposed equivalence but cannot establish that its evidence is
true, current or available. The experimental branch adds local append-only
retrieval observations and read-only graph inspection.

## Options

1. **A0 flat traces:** Fewest structures. No explicit hypothesis relationships
   or observation chronology.
2. **A1 existing links:** Reuses existing star/ray representation. Preserves
   hypothesis group membership, but no historical retrieval observations.
3. **A2 evidence-aware:** Keeps A1 unchanged and adds optional, local,
   append-only source observations. Increases operational metadata and the
   burden of access control, retention and integrity protection.

## Proposed decision

**Retain** existing hypothesis-centre and Star Credential structures as the
experimental grouping representation. **Retain experimentally, not normatively**
the read-only graph inspector. **Revise before promotion** the observation
layer: demonstrate historical retrieval reporting, but do not yet promise a
tamper-evident timeline, causal ordering, transaction guarantees or an
authoritative source-state registry.

**Defer** similarity inference, confidence/reputation scoring, provider
plugins and autonomous reconciliation. Do not extend VillageLink's primitive.

## Reasons and evidence

The synthetic A0/A1/A2 harness demonstrates that seeded hypothesis edges
change ranking and that only A2 exposes a historical availability trace.
Removing edges or observations removes the corresponding capability by
construction. The evaluation **does not establish** improved real-world
retrieval accuracy, agent continuity, correctness of machine-generated
equivalence, or an adequate performance/complexity trade-off. Dataset groups
and relevance labels coincide and are not independent ground truth.

## Consequences / non-goals

The optional observation layer introduces local privacy, custody, retention
and integrity obligations. Code is experimental and file-based. Current star
writes can be interrupted; inspection fails on missing rays but does not
repair partial data. Real-memory ingestion remains excluded.

## Acceptance authority and next gate

Maintainers may accept this ADR only after reviewing the experiment, failure
modes, a fair independent relevance benchmark, retention/privacy boundaries
and whether A1 plus ordinary logs is sufficient. Merge of this experimental
implementation does not itself imply ADR acceptance.
