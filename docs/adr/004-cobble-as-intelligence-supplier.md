# ADR-004: Cobble may supply intelligence as well as consume it

**Date:** 8 November 2026  
**Status:** Proposed — requires architectural approval  
**Project:** Cobble  
**Related:** [ADR-003](003-separate-corpus-sovereignty-from-village-link-research.md), [Issue #1](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/1), [Issue #28](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/28), [Issue #29](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/29)

## Context

Cobble has demonstrated a provider-neutral exchange with three external model
suppliers—Claude, Mistral and OpenAI GPT—while retaining memory and conversation
records locally. The architecture currently frames a Cobble instance as a
consumer of intelligence.

An emerging use case is that a Cobble instance, with its own corpus,
permissions, reputation and choice of intelligence suppliers, could itself
answer a bounded question from another instance of Cobble. For example, a
medical or engineering specialist could participate at the same boardroom
table as a general-purpose model. The calling Cobble should not require
knowledge of the specialist's private memory, internal suppliers or internal
organisation.

This raises an interface-level question now, even though implementing
Cobble-to-Cobble communication is not on the immediate demo critical path.

## Proposed decision

**Keep the intelligence supplier boundary composable: a Cobble instance should
be able to act as a supplier to another Cobble instance through substantially
the same provider-neutral contract used for external model suppliers.**

In particular:

1. **Interchangeable role, not assumed equivalence.** A supplier can be an
   LLM, a tool-assisted agent or another Cobble. They need not produce the
   same style, quality, trust or price.
2. **Independent memory and governance.** Each Cobble retains authority over
   its own corpus, permissions, retention, disclosure and supplier choices.
   Calling Cobble B does not confer access to B's source material or entitle
   B to receive A's corpus.
3. **Explicit inputs and auditable outputs.** Requests should carry a scoped
   question and selected context under the caller's authority. Replies should
   carry appropriate identity, provenance, usage, cost and status information.
   Claims of identity or expertise remain assessable claims, not automatic
   guarantees.
4. **Budgets and bounded delegation.** A future implementation must prevent
   uncontrolled recursive calls, loops, unbounded cost and indefinite work.
   Transitive delegation must not silently expand disclosure authority.
5. **Supplier neutrality remains meaningful.** Avoid baking direct-LLM
   assumptions into the stable Cobble exchange contract when a simple generic
   representation will do. Do not prematurely freeze a wire format or require
   every provider to support every optional capability.

This is a *design constraint to preserve an architectural option*, not a
decision that Cobble-to-Cobble exchange is already secure, useful or necessary
for the present product.

## Alternatives considered

- **LLM-only supplier interface:** simpler now, but may force a second,
  incompatible integration path for specialised cobbled entities later.
- **Build a distributed society of Cobble instances immediately:** premature
  for a project still integrating local corpus retrieval with one working
  browser-based demo.
- **Treat all corpora as one shared global corpus:** undermines independent
  membranes, consent, provenance and ownership.

## Consequences

The proposed principle allows specialised, separately governed entities to
participate as suppliers and leaves open markets for intelligence, delegation
and federated collaboration. None of those results is proven by this ADR.

Implementation is **deferred**. For the current demo ([Issue #29](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/29)):

- Build with the three existing live suppliers and local retrieval/disclosure.
- Keep the provider-neutral request/reply boundary clean.
- Record real disclosures, usage and cost.
- Do **not** build recursive orchestration, identity credentials, remote
  Cobble endpoints, payments, an autonomous expert marketplace or an
  infrastructure federation as prerequisites.

A later, separately scoped experiment may introduce a minimal Cobble-as-provider
adapter and endpoint between *two isolated Cobble instances*, then test context
consent, provenance, budgets, cycles, failure behaviour and continuity.

## Review and acceptance

**Proposed only.** Acceptance would establish the interface-level design
direction; it would **not** authorise deployment of a network-accessible
Cobble service or disclosure of real private corpora.

This proposal extends ADR-003's corpus sovereignty principle without
reintroducing graph/salience research as a dependency for the demo.
