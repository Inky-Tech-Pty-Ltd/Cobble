# Star semantic capability review plan

**Status:** Completed boundary-analysis checklist; normative VillageLink changes deferred.

This note separates Star capabilities that Cobble has actually exercised from
capabilities that remain VillageLink-level hypotheses or open design work.

| Capability | Evidence in Cobble | Result | Next action |
| --- | --- | --- | --- |
| Stable centre identity | Hypothesis-centred stars and ablation | Useful | Retain group identity |
| Unordered membership | Existing star tests / retrieval | Sufficient | No extra Cobble semantics |
| Duplicate rejection | Existing star tests | Tested | Continue compatibility |
| Expansion to centre/member Village Links | Existing star construction | Tested structurally | Keep compatibility |
| Retrieval via co-membership | Independent adversarial benchmark | Demonstrated with benefit and harm | Continue experimentally |
| Star-specific syntax required for retrieval | Representation ablation | **Not demonstrated** | Do not hard-code as necessity |
| Separate publication acts | Not exercised | Unverified | VillageLink/publisher study |
| Publisher provenance | Not exercised by local Cobble | Unverified | VillageLink/publisher study |
| Audience-specific subsets | Not exercised | Unverified | Defer |
| Portable interchange unit | Not exercised | Unverified | Future Cobble portability experiment |
| Canonical bytes/hash/signature | Open in VillageLink | Unverified | Do not invent in Cobble |
| Lifecycle/revocation of Star | Open | Not supported | Separate future design |
| Truth/authority | Explicitly excluded | Not established | Must remain excluded |

## Falsification questions

Future work should ask:

1. Can Cobble export/import its graph across independent implementations
   without requiring a Star-specific serialization?
2. Does a Star object preserve provenance or publication identity that would be
   lost in a generic collection?
3. Can centre-preserving expanded Village Links round-trip back to the same
   Star content without hidden application metadata?
4. Does audience-specific subsetting create privacy or credential-management
   obligations that conflict with the current Cobble boundary?
5. Can two separately published Stars with the same content remain
   distinguishable without putting publisher identity inside the Star?
6. Does any proposed additional Star field belong in VillageLink, publisher
   metadata, or Cobble evidence instead?

## Stop condition

Do not add new Star fields to Cobble merely to make these questions easier to
answer. Where a capability is untested, retain it as untested rather than
encoding an assumption.
