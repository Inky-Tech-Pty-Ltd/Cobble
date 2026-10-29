# ADR-002: Memory-native references, a defended conversational membrane, and one social resource economy

**Status:** Proposed — architectural hypothesis, not accepted or implemented  
**Date:** 30 October 2026  
**Scope:** Cobble / Arena One / the proposed entity *Snug*  
**Authority:** Cobble application design only; no change to Village Link's accepted ADRs or wire codec

## Context

Village Link asserts strict equality of *referent* between two traces understood in their memory systems:

```text
[A in X] = [B in Y]
```

The current [Village Link specification](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/specification.md) and [ADR-008](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/008-traces-referent-and-independent-uri.md) use independently meaningful trace **URIs** in their published `vl:` serialization. A publisher's act of making an assertion is separate from the two-ended equality relation: a publisher P may assert `Q = R`, but P is not a third endpoint of that relation.

Cobble asks whether an experimentally evolving entity can instead maintain a **memory-native** world of addressable blocks, local references, adjacency and internally operating publishers, with no mandatory public URI for every internal trace. Its system may reorganise memories and alter local neighbourhoods while preserving their referents and histories. URI-labelled traces may remain useful at a *deliberately chosen* interoperability boundary, without becoming the universal internal naming system.

This question is connected to the proposed entity's **membrane**. If every private memory is externally dereferenceable, Cobble has prematurely chosen a public memory browser as its interface. The alternative under examination is a socially mediated front door: a participant approaches the entity through conversation; the entity attends, deliberates, withholds or replies according to its circumstances, interests, available evidence and resources. A reply is *not* a general grant of addressability into the underlying corpus.

The same resource economy must govern talking to different people, exploring the web, consolidating memory, deciding what to disclose and obtaining intelligence. Scarcity is meaningless if every interaction with another person receives an independent, unmetered model or retrieval allocation.

These remain hypotheses. The current Arena copies an entire source corpus and exposes operator diagnostics; a rudimentary local Snug browser console is not yet a social learner. No emerging personality, judgement, sovereignty or independent publisher community has been demonstrated.

## Distinctions

- **Memory identity:** A way to refer persistently to a trace as an occurrence in its memory system; neither an absolute disk offset nor an external URI is necessarily its native form.
- **Location:** Where the current representation of that trace is stored. A block may move, be compressed or be replaced without automatically changing the intended trace's identity.
- **Reference / adjacency:** A connection or local neighbourhood that permits traversal between memories. A reference makes no *equality* assertion by itself.
- **Equality assertion:** A claim that two traces express the same meme, whether represented internally with native references or interoperably as a Village Link. It remains fallible, contestable and attributable.
- **Publisher:** A locus of agency that proposes, retains or communicates an assertion with provenance. An internal publisher need not be a web server or a public URI issuer; different local publishers can disagree.
- **Membrane:** The boundary at which the entity decides whether and how to interact with something outside its own retained memory, subject to external safeguards. Being able to identify a memory internally does not confer a public right to resolve it.
- **Participant:** Another actor whom the entity encounters. Distinguishing participants is *not* cloning the entity or partitioning its memory into one isolated entity per participant.

## Options: equality, naming and interchange

### A. Native-first memory

Implement the **abstract equality relation** using the memory system's native trace handles and internal assertion records, without first issuing public URI labels. Use established addressing machinery where appropriate: persistent object handles, scoped relative references, immutable content addresses, indirection, relocation maps and graph edges. Do not assume any one representation is universally best.

A trace's **identity** and its **location** must be separable. A relative reference must specify its anchor and resolution context; moving a neighbourhood should preserve internal references only to the extent the chosen addressing scheme guarantees it. Reorganisation, repair and failed resolution have measurable costs. Immutable content hashes describe particular snapshots; they are not automatically the identity of an evolving memory.

An internal equality assertion must record the two trace references and its *publisher/provenance* separately. It does not become true just because it is locally stored.

### B. URI-labelled memory

Mint or resolve URI identities for selected occurrences and compose the existing `vl:` representation. This offers an established interoperable encoding and can use the existing Village Link codec and Composer.

**B does not require one central register.** Different publishers may issue or resolve identities independently. But if applied obligatorily to every internal memory, it adds naming and exposure machinery where the local memory system might have a simpler native reference scheme.

### Proposed approach

**Treat A as a legitimate Cobble-internal implementation of the abstract equality idea, and B as an optional, explicitly mediated interoperability mechanism.**

This is a **Cobble research proposal**, not a declaration that native-handle assertions conform to the *current* Village Link URI-based wire specification. A separate Village Link standards decision would be necessary before describing technology-native serializations as alternate interoperable Village Link codecs.

Do not mint external URI labels merely to allow two adjacent internal memories to refer to one another. Where an external participant legitimately needs an identified trace, a publisher may choose to mint or resolve a stable URI for **that selected trace or representation**, preserving provenance and the ability to deny access to its contents. Conversely, an internal trace that has acquired a URI may remain private and non-dereferenceable. The choice to issue an identifier, to expose content, and to publish an equality assertion are three independent decisions.

Do not insert a central Cobble endpoint registry by implication. Whether to use local handles, distributed resolvers, public URIs, private capabilities or mixtures is an experimental implementation choice constrained by the membrane.

## One continuing Snug; plural internal publishers and participants

Snug is hypothesised to have **one continuing, shared history**, regardless of how many people interact with him or how many intelligence suppliers and internal publishers participate in maintaining that history.

- Joe and Sankarshan are **distinct social participants**, not owners of distinct `Joe-Snug` and `Sankarshan-Snug` instances. Participant identity exists so their actions, conversations, relationships and consequences can be distinguished in the *same* evolving memory.
- Two or more internal publishers may maintain different neighbourhoods, propose contradictory equality assertions, specialise or dispute another publisher's findings. A central Cobbler is not required to author every claim.
- Distributed publishers do **not** automatically imply distributed personhood. Experiments must measure whether one coherent history persists across partial failure, diverging local state, relocation and supplier replacement, rather than presupposing the answer.
- The intelligence suppliers (initially proposed: OpenAI and Kimi) are replaceable processes recruited to interpret experiences. They do not individually own Snug or create separate social selves by default.

A decentralised brain is **still an active architectural option**. It need not be physically distributed across computers in the first experiment. Multiple independent namespaces and publishers on McKay can provide a controlled initial test.

## The membrane's conversational front door

**Default external proposition:** *Talk to me. If it seems beneficial, I will talk back.*

The outside world does not receive a directory, API or dereferenceable URI inventory of Snug's inherited memories merely by communicating with him.

An incoming message is a *request for attention*, not an instruction that must be obeyed or an entitlement to internal data. Snug's experimental deliberation can allocate scarce attention, decide whether to respond, choose an appropriate scope and framing, ask a question, defer, refuse, or remain silent. A silence, refusal, disclosure or mistaken judgement may become an experience with social consequences.

A participant who is able to contact Snug must not automatically be able to obtain source passages, internal trace handles, hidden identities, private relations or assertions not intended for that participant. A published URI or Village Link, when one is intentionally produced, does not convert the underlying corpus into a public content service.

**Discretion rather than per-memory whitelists:** Do not require the experimenters to preselect a static list of every memory Snug may consider relevant to each conversation. Such a rule would preempt the judgement, trust and social learning the experiment is intended to investigate. Within legitimate disclosure boundaries, Snug should test *whether*, *when*, *to whom* and *how* to present information, including contextual sensitivity, tact, uncertainty, restraint and honest framing. Framing need not be deception; the goal is to study judgement and its consequences, not to program dishonesty.

**Non-negotiable external boundary:** An experimental entity is not itself the rights-holder for other people's private data. Possession of inherited information does not grant permission to reveal it to a new participant, a model provider or the public. Operators must enforce real confidentiality, consent, lawful access, spending and publication limits *outside* Snug's discretion. These are **envelope constraints** on the experiment, not a manual per-memory answer script. The learner may deliberate over all appropriately held internal experience, but external transmission must stay within the authorised envelope. In particular, model-provider prompts are external disclosures and require separate controls.

To study **teenage mistakes**, use fictional/synthetic or knowingly shared data, consented experimental participants, and reversible or contained disclosures. Record genuine mistakes, correction, loss of trust, repair attempts and any real consequences permitted in the sandbox. Do not engineer irreversible exposure of unconsenting third parties merely to demonstrate autonomy. At a later stage, expansion of disclosure authority requires a separately reviewed governance and safety decision.

A model may be *asked* to play the role of conversational intelligence, but its unverified self-description is not evidence that the entity has developed private interests or autonomous judgement.

## One resource economy for all encounters

The Arena declares independent dimensions (memory, intelligence, attention, historical retrieval and external resources), but the **allowances in each dimension belong to the same continuing experiment**.

Time spent conversing with Sankarshan is therefore unavailable for something else: answering Joe, attending to another participant, exploring the adjacent web, inspecting memory, compressing the corpus or conducting internal publisher debates. There must be no hidden unlimited intelligence reserve per visitor or per hemisphere that makes the shared economy fictional.

Record request arrivals and participant context; account for queued, deferred, rejected and answered interactions, model usage, historical retrieval and external side effects. Multiple suppliers can have measured sub-allocations, but any such sub-allocations must reconcile to the **global** resource ledger. Budget resets and replenishment rules must be explicit. The entity's choice of whom to attend to, at what cost and with what risk, is an experimental decision with potential social consequences.

Avoid hard-coding a preference for either parent or any other participant. Test whether relationships affect allocations in ways that improve the chosen outcome measures, and whether those preferences become pathological (flattery, exclusion, gratuitous secrecy or manipulation).

## Candidate experiments and falsifiable questions

1. **Reference resilience:** Represent the same corpus with (a) stable-handle graph references, (b) scoped local/relative references with relocation, and (c) content-addressed immutable snapshots plus mutable indirection. Reorganise blocks and measure broken references, repair time, bytes, lookup costs and retained trace identity. Do not assume physical adjacency equals conceptual relatedness.
2. **Publisher independence:** Let two internal publishers form conflicting candidate equality assertions over the same traces. Preserve provenance and disagreements, then test interchange through the existing URI-based `vl:` codec *when an explicit external identity is chosen*. Confirm that internal-only claims remain unexposed.
3. **Membrane challenge:** Use consenting participants and synthetic sensitive facts in a controlled Arena. Vary relationships, request framing, possible disclosure costs and observed consequences. Compare indiscriminate disclosure, blanket secrecy, manual per-memory permissions and a bounded discretion policy.
4. **Single-entity continuity:** Interleave messages from Joe, Sankarshan and simulated participants into one shared history; test that subsequent responses can take earlier interactions into account without spawning per-user Snugs or leaking another person's confidential data.
5. **Shared scarcity:** Give Snug competing demands from different participants, background exploration and memory consolidation. Vary total budgets but never silently allocate an independent unlimited quota to each correspondent. Measure deferrals, opportunity costs, trade-offs, memory revisions and social consequences.
6. **Discontinuity:** Remove one hemisphere or internal publisher, move a memory neighbourhood, or substitute a model supplier. Observe whether recoverable history and controlled rights survive, not whether an LLM *claims* to be the same entity.

Baseline comparisons must include simpler architectures. Evaluate errors and harms as well as retrieval or conversational utility. These tests are prospective; the current system does not yet implement them.

## Consequences, non-goals and unresolved decisions

**Consequences if adopted:** Internal references need not be URI-labelled; URI interchange is explicit and accountable; publishers can be plural and independent; the membrane is an intelligent/social interface with externally enforced real-world constraints; and all participants contend for shared resources.

**Not decided:** A particular memory-block codec, relative-reference format, persistent-handle technology, local address namespace, distributed consensus algorithm, participant authentication method, publishing protocol, admission-control policy, model prompt policy or value function. These require concrete trials.

**Non-goals:** A public endpoint registry; unsolicited external content browsing; declaring native assertions compliant with the current URI codec; equating a chatbot's first-person voice with personhood; imposing static per-person answer partitions; or allowing Snug unrestricted publication of others' private material.

**Standards boundary:** Village Link remains responsible for its accepted primitive, URI-based interoperable serialization, and abstract Star Credential. This Cobble ADR does **not** change [Village Link ADR-008](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/008-traces-referent-and-independent-uri.md). If evidence eventually supports native-only interoperable endpoints as a *Village Link* feature, propose a distinct Village Link ADR; do not silently redefine the current wire format inside Cobble.

## Review and acceptance gate

Keep this ADR **Proposed** until Cobble maintainers review the model with at least one independent contributor, preferably including Sankarshan, and examine:

- a comparative implementation or prototype of two address schemes and their relocation failure modes;
- a traceable example of two internal publishers proposing the same or conflicting assertions;
- a conversational membrane test with realistic social choices in a bounded, permissioned environment;
- shared-budget accounting across more than one participant and more than one process;
- confidentiality tests showing that source possession, URI identity and external disclosure are separate operations; and
- an explicit statement of how any proposed change relates to Village Link's accepted standard.

Accepting an ADR would endorse an architectural direction, **not** establish that Snug has consciousness, personhood, sovereignty or adaptive social judgement.
