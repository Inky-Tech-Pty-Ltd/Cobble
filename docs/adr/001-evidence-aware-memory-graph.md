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

## Evidence update: independent benchmark, observation contract, and ablation

Subsequent experiments strengthen and narrow this ADR.

The independent adversarial benchmark stores relevance annotations separately
from graph membership. Under four synthetic queries A1 improved aggregate
precision/recall over A0, while also promoting two deliberately mislinked
irrelevant traces. Graph construction quality is therefore both a utility and
a harm-control concern.

Observation schema `0.1` now makes retrieval state, observation time,
retrieval time, source-event time, and integrity status distinct. Records are
machine-validated as non-authoritative and truth-unassessed.

A representation ablation then held memberships constant while comparing the
current Star Credential, a simple collection, and centre-preserving pairwise
relationships. All three produced identical Cobble retrieval rankings.

### Revised proposed decision

The evidence supports a **group-membership capability**, but does not yet show
that Cobble requires the specific Star Credential syntax to obtain its current
retrieval behavior.

Therefore:

- retain Star Credential support for compatibility with the existing project
  direction and VillageLink experiment;
- do not make Star Credential syntax a Cobble architectural requirement solely
  on the basis of retrieval performance;
- preserve a stable hypothesis/group identity in any alternative representation;
- require a separate VillageLink-level analysis of publication, provenance,
  validation and interchange semantics before replacing or generalizing the
  Star Credential;
- keep ADR status **Proposed**, not Accepted.

The next decision is no longer whether graph grouping has any utility. It is
whether the Star Credential carries additional semantics that justify its
specific representation beyond recoverable co-membership.

## Cross-repository boundary review

The dedicated boundary review on `research/star-boundary-review` classifies
Star semantics by authority rather than implementation location.

VillageLink remains authoritative for:

- the same-entity assertion `A ↔ B`;
- the distinguished Star centre;
- unordered membership and duplicate exclusion;
- expansion of a Star into constituent centre/member Village Links; and
- any future normative Star serialization or conformance rules.

Cobble remains authoritative only for its application-specific behavior:

- hypothesis lifecycle;
- local memory-graph persistence;
- source observations and integrity state;
- retrieval/ranking; and
- graph-construction experiments.

The review confirms that Cobble's retrieval evidence does not justify
redefining Star Credential semantics, nor does it justify making the current
Star JSON representation an application requirement. A stable hypothesis/group
identity remains useful and is retained.

VillageLink ADR-007 creates a deliberate risk boundary: Cobble persistence is a
separate application decision and must not be treated as an extension of the
stateless Composer. Real cross-context personal equivalence data remains outside
the demonstrated safe scope of the experiment.

### Boundary decision

**Keep this ADR Proposed.** The current evidence supports continued
Star-compatible experimentation in Cobble, but no normative VillageLink change.

If the open publication, provenance, interchange, subsetting, or serialization
questions are escalated, they should be reviewed in VillageLink under its own
issue/branch and authority trail.
