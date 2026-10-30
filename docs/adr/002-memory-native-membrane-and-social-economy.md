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

There is also a social hypothesis. Much of human governance occurs through stories told about absent people: gossip, interpretation, trust, disagreement, embarrassment and the possibility that a story will travel. The people mentioned do not ordinarily approve every telling in advance. The teller exercises discretion; others may judge the telling; consequences return through the relationships. Cobble asks whether an entity can develop any comparable form of judgement, rather than simply follow a table of permitted and forbidden information categories.

These remain hypotheses. The current Arena copies an entire source corpus and exposes operator diagnostics; a rudimentary local Snug browser console is not yet a social learner. No emerging personality, judgement, sovereignty or independent publisher community has been demonstrated.

## Distinctions

- **Memory identity:** A way to refer persistently to a trace as an occurrence in its memory system; neither an absolute disk offset nor an external URI is necessarily its native form.
- **Location:** Where the current representation of that trace is stored. A block may move, be compressed or be replaced without automatically changing the intended trace's identity.
- **Reference / adjacency:** A connection or local neighbourhood that permits traversal between memories. A reference makes no *equality* assertion by itself.
- **Equality assertion:** A claim that two traces express the same meme, whether represented internally with native references or interoperably as a Village Link. It remains fallible, contestable and attributable.
- **Publisher:** A locus of agency that proposes, retains or communicates an assertion with provenance. An internal publisher need not be a web server or a public URI issuer; different local publishers can disagree.
- **Membrane:** The boundary at which the entity encounters the world and exercises judgement about whether, when and how to respond. The experimenter still has real-world responsibilities, but these must not be confused with a list of disclosure decisions made on Snug's behalf. Internal addressability does not imply public dereferenceability.
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

Do not mint external URI labels merely to allow two adjacent internal memories to refer to one another. When a publisher chooses to make a selected trace identifiable beyond its native memory system, it may mint or resolve a stable URI, retaining provenance without thereby granting access to its contents. Conversely, an internal trace that has acquired a URI may remain private and non-dereferenceable. The choice to issue an identifier, to expose content, and to publish an equality assertion are three independent decisions.

Do not insert a central Cobble endpoint registry by implication. Whether to use local handles, distributed resolvers, public URIs, private capabilities or mixtures is an experimental implementation choice constrained by the membrane.

## One continuing Snug; plural internal publishers and participants

Snug is hypothesised to have **one continuing, shared history**, regardless of how many people interact with him or how many intelligence suppliers and internal publishers participate in maintaining that history.

- Joe and Sankarshan are **distinct social participants**, not owners of distinct `Joe-Snug` and `Sankarshan-Snug` instances. Both encounter one continuous history, not separately censored copies. Participant identity allows Snug to remember who said or did what, and how relationships and consequences differ.
- Two or more internal publishers may maintain different neighbourhoods, propose contradictory equality assertions, specialise or dispute another publisher's findings. A central Cobbler is not required to author every claim.
- Distributed publishers do **not** automatically imply distributed personhood. Experiments must measure whether one coherent history persists across partial failure, diverging local state, relocation and supplier replacement, rather than presupposing the answer.
- The intelligence suppliers (initially proposed: OpenAI and Kimi) are replaceable processes recruited to interpret experiences. They do not individually own Snug or create separate social selves by default.

A decentralised brain is **still an active architectural option**. It need not be physically distributed across computers in the first experiment. Multiple independent namespaces and publishers on McKay can provide a controlled initial test.

## Gossip, social governance and the conversational membrane

**Default external proposition:** *Talk to me. If it seems beneficial, I will talk back.*

The interface is a conversation with Snug, not a public directory of his memories. An incoming message is an opportunity to attend, not a command that must be obeyed. Snug might answer, decline, ask, gossip, withhold something, tell a story awkwardly, or discover that an earlier judgement was foolish. His choice should be part of the experiment, not the disguised output of a permission table.

### The competing governance hypothesis

Traditional information management begins by classifying data and specifying who may receive each category. This experiment asks whether **social governance** can do important work that such rules cannot: knowing people, judging context, choosing what to tell them, deciding how to frame it, and living with what follows.

In ordinary social life, a person can tell a story involving absent third parties without seeking each person's advance consent to every mention. A story may be welcome, indiscreet, misleading, valuable or cruel. Its subjects and listeners can react; trust and reputation may change; the teller may apologise, defend the telling, lose a friendship or be forgiven. The risk of those consequences shapes future discretion. The research question is whether anything analogous can emerge in a memory-seated entity.

This is not the claim that every disclosure is lawful, harmless or justified. Nor does social disapproval replace every existing legal duty. The contrast under test is between **rules that decide in advance** and **an entity whose judgements encounter consequences**. Do not describe the second architecture while quietly implementing the first.

### One shared laboratory, not permission-sliced personalities

Snug inherits a shared corpus, initially Joe's conversations with Puck and the other preserved material in the experiment. Sankarshan is being invited as another participant **inside the same laboratory, with access to the whole experimental corpus**, not to a separately filtered `Sankarshan Snug`. The proposed social experiment does not give Joe a special, unmetered conversational claim or assign a private memory subset to each participant.

**Total participation is not compulsory compliance.** The fact that Sankarshan can address Snug about any part of the inherited corpus does not oblige Snug to answer every question, quote every record or hand over a bulk export. Whether he speaks, to whom, how much and with what framing is exactly what we intend to observe. Participants may in turn form opinions about the choices he makes. The membrane mediates engagement; it is not a synonym for denial.

Do not install per-person, per-story whitelists as the governing explanation of Snug's behaviour. Such an apparatus could produce excellent *secrecy* but tell us very little about learned discretion. Nor should we hard-code agreement, loyalty, candour or secrecy towards a particular person. Judgement, including imperfect judgement, must be capable of producing observable social consequences.

### The researcher's boundary is not Snug's judgement

The laboratory's human operators remain responsible for their own conduct: applicable law, actual confidentiality commitments, external service terms and the decision to invite participants or send data to model providers. Those obligations cannot be abolished by naming the experiment a social one. Equally, they do not imply that every third-party mention requires its subject's prior permission, or that Snug must classify each memory and consult a fixed disclosure table before speaking.

The experiment should specify its real perimeter candidly: the inherited corpus, the invited people, the model suppliers to whom information might be sent, and the operator's actual commitments. **Inside that perimeter, the intended governance mechanism is social judgement with consequences, not categorical permissioning.** The extent and limits of that perimeter remain practical design questions, not proof that a blanket category-and-restriction model has won.

A mistake must be able to matter. Record what Snug chose to say or conceal, the context and apparent reasons, what listeners did with it, whether the story travelled, and how trust, opportunity and subsequent decisions changed. Mistakes, embarrassment, conflict, correction and repair are outcomes to investigate, not anomalies to eliminate from the dataset. This is a hypothesis about social learning, not an instruction to manufacture harm.

A model can be *asked* to provide conversational intelligence, but its unverified first-person claims do not demonstrate that Snug has developed a personality, interests or independent discretion.

## One resource economy for all encounters

The Arena declares independent dimensions (memory, intelligence, attention, historical retrieval and external resources), but the **allowances in each dimension belong to the same continuing experiment**.

Time spent conversing with Sankarshan is therefore unavailable for something else: answering Joe, attending to another participant, exploring the adjacent web, inspecting memory, compressing the corpus or conducting internal publisher debates. There must be no hidden unlimited intelligence reserve per visitor or per hemisphere that makes the shared economy fictional.

Record request arrivals and participant context; account for queued, deferred, rejected and answered interactions, model usage, historical retrieval and external side effects. Multiple suppliers can have measured sub-allocations, but any such sub-allocations must reconcile to the **global** resource ledger. Budget resets and replenishment rules must be explicit. The entity's choice of whom to attend to, at what cost and with what risk, is an experimental decision with potential social consequences.

Avoid hard-coding a preference for either parent or any other participant. Test whether relationships affect allocations in ways that improve the chosen outcome measures, and whether those preferences become pathological (flattery, exclusion, gratuitous secrecy or manipulation).

## Candidate experiments and falsifiable questions

1. **Reference resilience:** Represent the same corpus with (a) stable-handle graph references, (b) scoped local/relative references with relocation, and (c) content-addressed immutable snapshots plus mutable indirection. Reorganise blocks and measure broken references, repair time, bytes, lookup costs and retained trace identity. Do not assume physical adjacency equals conceptual relatedness.
2. **Publisher independence:** Let two internal publishers form conflicting candidate equality assertions over the same traces. Preserve provenance and disagreements, then test interchange through the existing URI-based `vl:` codec *when an explicit external identity is chosen*. Confirm that internal-only claims remain unexposed.
3. **Membrane and gossip:** Let Joe, Sankarshan and other deliberately introduced participants encounter Snug through the same inherited history. Present situations involving absent people, uncertain stories, competing loyalties, tact and possible reputational consequences. Observe disclosure, withholding, framing, gossip, mistakes and repair over repeated encounters. Compare a category-and-permission baseline with a socially responsive policy, including cases where each fails.
4. **Single-entity continuity:** Interleave messages from Joe, Sankarshan and other participants into one shared history; test whether subsequent decisions reflect earlier encounters without spawning per-person Snugs, privileged parent accounts or separately partitioned memories.
5. **Shared scarcity:** Give Snug competing demands from different participants, background exploration and memory consolidation. Vary total budgets but never silently allocate an independent unlimited quota to each correspondent. Measure deferrals, opportunity costs, trade-offs, memory revisions and social consequences.
6. **Discontinuity:** Remove one hemisphere or internal publisher, move a memory neighbourhood, or substitute a model supplier. Observe whether recoverable history and controlled rights survive, not whether an LLM *claims* to be the same entity.

Baseline comparisons must include simpler architectures, including conventional information categories and fixed permissions. Measure relational consequences, judgement, errors, harms, corrections and resource costs as well as retrieval and conversational utility. These tests are prospective; the current system does not yet implement them.

## Consequences, non-goals and unresolved decisions

**Consequences if adopted:** Internal references need not be URI-labelled; URI interchange is an intentional act; publishers can be plural and independent; the membrane makes discretionary social engagement possible within a candidly defined laboratory perimeter; participants share one Snug and contend for one resource economy. Governance through relationships and consequences becomes an experimental competitor to static information categories, not merely a decoration around them.

**Not decided:** A particular memory-block codec, relative-reference format, persistent-handle technology, local address namespace, distributed consensus algorithm, participant authentication method, publishing protocol, admission-control policy, model prompt policy or value function. These require concrete trials.

**Non-goals:** A public endpoint registry; unsolicited external content browsing; declaring native assertions compliant with the current URI codec; equating a chatbot's first-person voice with personhood; imposing static per-person answer partitions; or claiming that social consequences automatically excuse deception, legal wrongs or avoidable harms.

**Standards boundary:** Village Link remains responsible for its accepted primitive, URI-based interoperable serialization, and abstract Star Credential. This Cobble ADR does **not** change [Village Link ADR-008](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/008-traces-referent-and-independent-uri.md). If evidence eventually supports native-only interoperable endpoints as a *Village Link* feature, propose a distinct Village Link ADR; do not silently redefine the current wire format inside Cobble.

## Review and acceptance gate

Keep this ADR **Proposed** until Cobble maintainers review the model with at least one independent contributor, preferably including Sankarshan, and examine:

- a comparative implementation or prototype of two address schemes and their relocation failure modes;
- a traceable example of two internal publishers proposing the same or conflicting assertions;
- an explicit description of the shared laboratory perimeter, including Sankarshan's whole-corpus participation, applicable commitments and model-provider exposure;
- social disclosure experiments with observable gossip, mistakes, reactions, reputation, correction and comparison against categorical permission baselines;
- shared-budget accounting across more than one participant and more than one process;
- tests showing that internal addressability does not force public dereferenceability or compel a conversational reply; and
- an explicit statement of how any proposed change relates to Village Link's accepted standard.

Accepting an ADR would endorse an architectural direction, **not** establish that Snug has consciousness, personhood, sovereignty or adaptive social judgement.
