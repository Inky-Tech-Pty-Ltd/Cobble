# VillageLink–Cobble Star Credential boundary review

**Status:** Experimental architecture review  
**Branch:** `research/star-boundary-review`  
**Normative effect:** None. This document does not amend VillageLink specification or ADRs.

## Review question

Which Star Credential semantics are owned by VillageLink, which capabilities are
only consumed by Cobble, and which application-specific semantics must remain
owned by Cobble rather than leaking back into the VillageLink primitive?

The review is based on the current VillageLink specification, requirements,
[ADR-004](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/004-star-credential-data-model.md) (Star Credential centred unordered set), [ADR-007](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/007-stateless-composer.md) (stateless Composer
and no persistent credential manager), and the evidence produced by Cobble's
memory-graph experiments.

## Authority boundary

VillageLink is authoritative for the meaning of a Village Link and the abstract
Star Credential model. Cobble is an application experiment that consumes those
semantics and adds memory-specific persistence, evidence, observation and
retrieval behavior.

Cobble MUST NOT redefine a VillageLink semantic merely because its local
implementation stores or ranks the same information differently.

VillageLink MUST NOT acquire Cobble-specific persistence, retrieval, evidence
or memory-lifecycle requirements merely because Cobble finds them useful.

## Semantic ownership matrix

| Property | VillageLink status | Cobble requirement/evidence | Owner / disposition |
| --- | --- | --- | --- |
| Same-entity assertion `A ↔ B` | Core normative VillageLink semantic | Required only when Cobble claims a relationship is a Village Link | **VillageLink** |
| Distinguished centre `A` | Normative Star structure | Useful as stable hypothesis/group identity | **VillageLink semantic; Cobble consumes** |
| Unordered member set `B` | Normative Star structure | Retrieval is order-insensitive | **VillageLink** |
| No duplicate members | Normative Star invariant | Compatible with Cobble group handling | **VillageLink** |
| Star expands to constituent `A ↔ B` assertions | Normative Star meaning | Preserves compatibility with VillageLink graph interpretation | **VillageLink** |
| Concrete Star JSON serialization | Open in VillageLink | Cobble currently has implementation-local JSON | **Unresolved / not Cobble normative** |
| Publisher identity / separate publication acts | VillageLink publication layer | Not required by current local Cobble retrieval | **VillageLink / publisher layer** |
| Audience-specific subsets | Supported by Star model rationale | Not exercised by Cobble | **VillageLink capability; Cobble deferred** |
| Hypothesis lifecycle | Not defined by Star Credential | Required by Cobble memory experiments | **Cobble** |
| Source observation history | Explicitly outside minimal primitive | Demonstrated by Cobble observation contract 0.1 | **Cobble** |
| Retrieval ranking | Application interpretation | Central to Cobble experiments | **Cobble** |
| Graph construction / inferred matches | Application behavior | Experimental; not yet proven reliable | **Cobble** |
| Evidence availability / integrity state | Metadata outside primitive | Needed for Cobble evidence-aware graph | **Cobble** |
| Persistence of local memory graph | Outside VillageLink Composer | Necessary for Cobble continuity experiment | **Cobble, high-risk boundary** |
| Universal confidence / reputation | Not specified | No current evidence | **Deferred** |
| Truth / authoritative identity continuity | Explicitly not established | Not established by Cobble | **Neither may claim** |

The machine-readable counterpart is
`docs/research/star-boundary-manifest.json`.

## What the Cobble ablation establishes

Cobble's Star representation ablation held group membership constant and
compared:

1. current Star Credential membership;
2. a simple group/collection representation; and
3. centre-preserving pairwise relationships from which co-membership was
   reconstructed.

All produced identical retrieval rankings in the current benchmark.

Therefore the **current Cobble retrieval algorithm depends on recoverable
co-membership, not on Star Credential syntax**.

This result does not establish semantic equivalence for VillageLink. In
particular, it does not test publication identity, interchange, provenance,
subsetting, normative Star validation, or the meaning of expanding a Star into
constituent Village Links.

## Why the centre still matters

The ablation does not support replacing the Star with an anonymous set.

Pairwise reconstruction required a common centre/group identity. Cobble also
uses the centre as a persistent hypothesis identity whose supporting membership
may change over time.

A stable hypothesis/group identity is therefore currently useful to Cobble,
even though the specific Star serialization is not necessary to retrieval.

That application requirement must not be misread as permission for Cobble to
redefine the VillageLink centre semantic.

## Persistence boundary created by ADR-007

VillageLink ADR-007 deliberately separates stateless composition from
persistent credential management because cross-context equivalence can itself
be sensitive.

Cobble intentionally crosses into persistence because its research proposition
requires a durable memory graph. That makes Cobble a distinct application and
risk domain rather than an extension of Composer.

The boundary for this experiment is:

> Cobble may persist local hypothesis relationships required for memory
> continuity, but persistence does not imply a mandate to collect, centralize,
> publish, or expose every cross-context identity equivalence representable as
> a Village Link.

Before real personal memories are used, Cobble needs an explicit privacy and
retention design covering at least:

- local-versus-shared storage;
- sensitive correlation;
- deletion and correction;
- source disappearance;
- observation retention;
- access control;
- export/import boundaries; and
- whether graph existence itself is sensitive.

## Cross-repository relationship

The relationship should presently be understood as:

```text
VillageLink
  owns: primitive + Star semantics
       |
       | implements / informative-alignment
       v
Cobble
  owns: memory hypothesis lifecycle, persistence,
        source observations, retrieval and experiments
```

This does **not** imply that Cobble is authoritative for VillageLink semantics,
or that VillageLink requires Cobble's storage or retrieval architecture.

## Decision

1. **Retain** VillageLink Star Credential support in Cobble for compatibility
   and continued experimentation.
2. **Do not** make Star Credential syntax a Cobble architectural requirement
   based solely on retrieval performance.
3. **Retain** a stable hypothesis/group identity in Cobble.
4. **Keep** observation, evidence, persistence and retrieval semantics local to
   Cobble.
5. **Do not** modify VillageLink specification or ADR-004 based on the current
   Cobble evidence.
6. **Escalate to VillageLink** only the unresolved question of which additional
   Star semantics beyond co-membership are necessary for publication,
   interchange, provenance, validation or subsetting.

## Unresolved questions

- Does Star Credential need a normative concrete serialization?
- Is the centre/member distinction required for interchange beyond current
  Cobble use?
- Which provenance belongs to the Star itself versus a publication of it?
- Does a portable Cobble memory package need a Star Credential, or only a
  compatible export projection?
- Can audience-specific Star subsets be safely useful in Cobble without
  becoming credential management?
- What privacy and retention controls are required before persistent Cobble
  graphs contain real cross-context personal equivalences?

## Promotion gate

This review may justify a VillageLink research note or issue. It does not by
itself justify a normative specification change.

Any future VillageLink change should be made on a separate VillageLink branch
and should identify the normative proposition, compatibility impact, evidence,
and unresolved risks independently of Cobble's implementation history.
