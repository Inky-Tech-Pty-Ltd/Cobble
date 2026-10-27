# Star Credential representation ablation

**Status:** Experimental Cobble architecture review.

## Question

Does Cobble's demonstrated retrieval behavior depend on the current
`StarCredential` syntax, or on the simpler fact that a query anchor and other
traces share a recoverable hypothesis membership?

## Compared views

1. **Star:** current seeded Star Credential membership.
2. **Collection:** one hypothesis/group object containing the same members.
3. **Pairwise reconstructed:** centre-to-member relationships from which
   co-membership is reconstructed using the retained shared centre.

The same lexical scoring, graph bonus, corpus, annotations and retrieval budget
are used for all views.

## Result interpretation

If all three produce identical retrieval, the result establishes only that
**Cobble's present retrieval algorithm consumes co-membership, not Star
Credential syntax**.

It does not establish semantic equivalence for VillageLink. The Star Credential
may still provide publication, interchange, provenance, validation or
governance properties that this Cobble experiment does not test.

A particularly important boundary is that unrelated bare pairwise links do not
reconstruct group membership without a common centre or group identity.

## Architectural consequence

Do not justify Star Credential retention solely by the retrieval benchmark.
Retain it experimentally because it is the project's current grouping
representation, but require separate justification for any claim that its
specific syntax is necessary to Cobble.
