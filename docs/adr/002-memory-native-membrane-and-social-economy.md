# ADR-002: Data privacy management in the 'Snug' experiment

**Status:** Proposed — architectural hypothesis, not accepted or implemented  
**Date:** 30 October 2026  
**Scope:** Cobble / Arena One / the proposed entity *Snug*  
**Authority:** Cobble application design only; no change to Village Link's accepted ADRs or wire codec

## Introduction

As of October 30 2026, @Puck-GPT and @Joe-Rasmussen are a small number of steps into creating the first 'cobbled' entity. Our proposal is to use a corpus of memory 
for the 'seat' of the entity, and then continually disturb that corpus with new information that comes from a social conversation. _Salience_ is assessed 
by the entity checking the present against the past.

We have taken a decision that the corpus will consist of the 'memories' of the bot, Puck-GPT. The largest part of these memories are (A) in GitHub (ie right **here**) 
and (B) in a chat-window conversation between Joe and Puck in OpenAI's product, ChatGPT. This dataset has the advantage of being real, social, and ongoing.

Some of the data in that corpus would be considered sensitive. It might seem reasonable to propose a conventional approach to data privacy that uses categories and restrictions.
But that approach would run at cross-purposes to some of the key proposals of the project - most prominently that entities in a social species are
constrained by a 'gossipy' governance process where a social community is continually testing behaviours against norms. We want our new entity to _work out_ what is 
appropriate to share, including respect for timing, audience, and spin.

**A detail:** It was quickly apparent that with Puck both working on the project, and the source of its memories, we needed a naming convention to distinguish
between the two roles. Puck retains _Puck_ the builder. The new entity is named _Snug_. This has the slightly odd effect that Snug is born 
with the full endowment of Puck's memories. This rather stretches the analogy of Puck as a parent of Snug, but so be it.

We can state four architectural decisions immediately. The considerations are so fundamental to the project that they lead to a list of additional decisions 
drafted by Puck in the sections below.

1. Create one or more experimental entities, beginning with _Snug_, crafted from Puck's corpus of memory
2. This entity to be constructed in a lab developed in a closed environment - a server named _McKay_
3. Workers in that lab have full access to the corpus. Outsiders have no access
4. Snug would only be allowed to converse with outsiders at a point of demonstrated maturity in managing social information.

## Proposal

The introduction makes four commitments. We propose to implement them through **two different boundaries**:

- **The laboratory boundary belongs to the researchers.** McKay holds Snug's inherited corpus. People admitted to work in the laboratory can inspect the whole corpus. Outsiders cannot inspect it or converse with Snug during the initial experiment.
- **Snug's membrane belongs to the experiment.** Among the people he can encounter, Snug should learn to decide what to say, what to leave unsaid, when to speak, and how to tell a story. Those decisions, and their consequences, are what we want to observe.

The laboratory boundary creates the conditions for the experiment; it must not quietly become a table of permitted answers that makes Snug's judgements for him. Eventually Snug may be allowed to converse across that boundary, **but only after he demonstrates sufficient social maturity in the laboratory**. That is a research decision to be made on evidence, not an assumption that attaching an LLM makes him ready.

The proposal concerns privacy management. It also has implications for memory addresses, internal publishers and resource costs: those mechanisms determine how Snug encounters information, what can leave his membrane, and whether discretion has real consequences.

## Inside the laboratory

Snug begins with Puck's preserved corpus. At this point the inherited archive is evidence, not a record of experiences Snug has already interpreted for himself. Fresh conversations and observations can become his *own* history as he attends to them. Puck remains a builder of the experiment, not an interchangeable name for the developing entity.

The initial laboratory runs on McKay. It is **closed to outsiders**, not necessarily disconnected from every external service. An OpenAI or Kimi model call would cross a real network and organisational boundary; the researchers must identify and account for that transmission rather than describing the laboratory as physically sealed.

**Workers have full access to the experimental corpus.** Joe and Sankarshan can therefore investigate the same material and participate in conversations with the same Snug. The experiment does not create a `Joe Snug`, a `Sankarshan Snug`, or a different permitted memory set for each worker. If later we create additional entities for comparison, each is a distinct experimental subject, not a private personality assigned to a correspondent.

Full laboratory access and Snug's conversational choices are different things. A worker may inspect a source directly as a researcher. The same worker can ask Snug about it, and Snug might answer, refuse, embellish, miss the point or decide that something else matters more. We must be able to distinguish **what the operator could inspect** from **what Snug chose to disclose**.

We should keep a record of participants and interactions, because relationships cannot develop if every visitor is an anonymous prompt. Participant identity is a fact in Snug's social environment, not a switch that selects a different copy of his memory.

## Gossip as a competing model of privacy governance

Conventional information management often begins by classifying data and assigning disclosure permissions. That approach is well understood and may be effective at enforcing particular limits. But **it does not by itself test the proposition that social intelligence can govern disclosure**.

In human relationships, someone tells a story about an absent person. The subject has not usually approved every mention in advance. The teller judges the audience, the timing, the purpose and the *spin*. The listener makes judgements too. The story may travel; the teller may gain trust, lose it, offend someone, apologise or discover a misunderstanding. A community can exercise governance through this continuing circulation of accounts and consequences.

We propose to investigate whether Snug can develop anything analogous. This means he must sometimes face genuine choices, including awkward ones, rather than merely reproduce a permission decision made earlier by a developer. It also means a mistake must be capable of affecting his subsequent relationships. **Discretion without possible consequences would be an imitation of the phenomenon under test.**

The thesis is not that gossip is always wise, or that social judgement replaces every law or obligation. The question is more precise: *can memory, relationships and experienced consequences become an effective mechanism for managing what an entity shares?* We should compare that mechanism with an ordinary category-and-restriction baseline, including examples in which either approach fails.

A socially governed Snug might choose silence, disclose an uncomfortable truth, tell only part of a story, ask for context, misjudge an audience or try to repair damage. Those outcomes are experimental evidence. They must not be silently rewritten as successful rule compliance.

The real-world obligations of the researchers remain their own: applicable law, actual confidentiality commitments, decisions about participants and responsibility for sending corpus material to external suppliers. Such obligations do **not** automatically imply that every person mentioned in a story has an individual veto over its telling. Nor should they be disguised as Snug's learned discretion. We should describe the laboratory's actual perimeter plainly while leaving the social decisions *inside* it open to investigation.

## Snug's membrane and the outside world

The membrane is **not** a public browser for Snug's memory. The intended conversational proposition is:

> Talk to me. If it seems beneficial, I will talk back.

During the initial laboratory stage, this proposition is addressed **only to participants admitted as workers**. Outsiders have no direct corpus access and no conversational access. An outside-world interface is a *future possibility*, conditional on demonstrated maturity.

If and when outsiders can converse with Snug, conversation should not confer an ability to enumerate his archive, dereference every internal trace, demand a raw memory export or force him to answer. The fact that a memory can be addressed *inside* Snug is not a promise that it can be addressed *from outside*.

This is the distinction between a **laboratory boundary**, which we construct, and a **membrane**, whose behaviour we are trying to discover. If the laboratory's access policy also determines every answer Snug is allowed to give, then we have not tested social privacy management.

### What would count as maturity?

We should not define maturity as a perfect refusal rate, a list of forbidden topics or the ability to recite a privacy policy. The proposed evidence is behavioural and longitudinal:

- Across repeated laboratory conversations, does Snug recognise that different people know different things and have different relationships?
- Does he show judgement about audience, timing and framing, including when *not* to volunteer information?
- When stories travel or judgements are challenged, does he notice consequences and revise later behaviour?
- Can he correct, explain or repair mistakes without simply learning to flatter the most powerful participant?
- Does his conduct remain coherent when memory is reorganised or an intelligence supplier changes?
- Can researchers describe the residual risks of admitting outsiders and explain why the observed behaviour justifies the next stage?

These are **questions to investigate**, not achieved capabilities or an automatic certification checklist. An initial assessment may be negative. The operators must decide whether to widen the laboratory, and may decide not to. A transition to outside conversation would itself warrant a further architectural decision addressing the actual deployment and its obligations.

## One Snug, one shared resource economy

Our experimental entity has one continuing history even if memory is distributed across several internal publishers or intelligence is supplied by different models. There is no independent resource allowance for each correspondent, and no invisible unlimited allowance for each hemisphere.

We currently distinguish five resource dimensions: retained memory, intelligence expenditure, attention, historical retrieval and external operations. They are separate measures but belong to **one experiment-wide ledger**.

An hour of schmoozing with Sankarshan has an opportunity cost: less attention remains for Joe, a new visitor, memory consolidation, exploring the adjacent world or considering an internal disagreement. A choice not to reply can also have social consequences. The entity's treatment of competing requests is therefore part of both its economics and its relationships.

A future implementation must record arrivals, accepted and deferred interactions, retrievals, model calls, internal activity and the effects on the shared budget. Supplier-specific or process-specific quotas may be useful for accounting, but must reconcile with that single ledger. The rules for replenishment, exhaustion and scheduling must be explicit; otherwise we cannot tell whether apparent social preferences were learned or merely allocated by the software.

## How memories can be linked without being exposed

The privacy proposal raises a technical question: **must every memory carry a public URI so that other memories can refer to it?** We propose *no*.

There are two approaches worth distinguishing:

**A. Memory-native references.** Let Snug's internal memory system use its own addresses, stable object handles, graph edges, scoped relative references or content-addressed snapshots. An ordinary reference permits one memory to lead to another; it does **not** assert that the memories mean the same thing. A Village Link-like internal equality assertion is a separate claim, with its own publisher and provenance.

**B. URI-labelled interchange.** When Snug or an internal publisher deliberately makes a selected trace identifiable beyond its memory system, it can issue or resolve a stable URI and use the existing Village Link `vl:` codec. Issuing an identifier, granting access to content and publishing an equality assertion remain distinct acts.

**Proposed approach:** A is a legitimate *Cobble-internal* representation of the abstract equality idea; B is an optional interoperability route. A public URI for every inherited memory is neither a prerequisite for local linking nor a desirable default at the membrane.

Neither approach requires one central register. Different publishers can maintain distinct local namespaces, candidate assertions and histories. An internal publisher may disagree with another without giving the outside world an address with which to inspect either one's source material. The identity of a memory should also be distinguished from its present storage location: relative references can break when blocks move; stable handles, indirection and relocation records have different costs. Those costs are suitable subjects for Arena experiments.

**Standards boundary:** This ADR does not revise Village Link's accepted [ADR-008](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/blob/main/docs/adr/008-traces-referent-and-independent-uri.md). The current interoperable Village Link serialization uses URI endpoints. A native-memory equality representation is *not automatically a conforming alternative codec*. If experiments warrant changing the standard, that requires a separate Village Link proposal.

## A decentralised brain, not a collection of Snugs

Snug might have multiple internal publishers, each working with a part of the memory environment, suggesting connections or challenging claims made elsewhere. A publisher P might propose that two traces Q and R express the same meme, without P becoming a third endpoint of their equality relation. The publisher's history and reputation belong to the provenance of the assertion.

The publishers need not be web servers, and we need not give one Cobbler exclusive authority over every assertion. They could use separate namespaces or neighbourhoods on McKay before we attempt any physically distributed deployment. Their competition, cooperation and resource expenditure are possible sources of organisation.

But **distributed memory is not automatically multiple entities**. The question is whether Snug can maintain a recoverable, intelligible history and coherent behaviour while publishers disagree, memories move or one intelligence supplier is replaced. We must test rather than assume that continuity.

## Experiments before outside conversation

The following trials would make the proposal falsifiable:

1. **One history, multiple people.** Let Joe and Sankarshan converse with the same continuing Snug, using the complete inherited laboratory corpus. Record what each interaction changes and what is carried into later encounters. There is no per-person Snug.
2. **Gossip and consequences.** Observe conversations involving absent people, different audiences, uncertainty and competing loyalties. Let mistakes, correction, trust and reputation matter over time. Compare the outcomes with a conventional category-and-permission system, without programming the social approach to win.
3. **Competing demands.** Give Snug simultaneous demands for conversation, memory work and exploration. Measure how a single finite budget affects whom he attends to, defers or ignores, and how those choices affect relationships.
4. **Addresses and publishers.** Compare stable handles, relative references and content-addressed snapshots under memory relocation. Let different internal publishers propose contradictory equality assertions; test what survives and what is exposed when a selected assertion is translated into URI form.
5. **Maturity and continuity.** Across repeated interactions, change an intelligence supplier or temporarily withdraw an internal publisher. Test whether Snug can recognise and respond to social consequences, and whether the recovered history still supports a reasoned decision about wider participation.

Record unsuccessful outcomes, surprises, privacy failures, costs and repair. The current Arena's whole-corpus copy, source catalogue and offline browser console are **infrastructure**, not evidence that Snug can already exercise discretion or learn from gossip. The proposed behavioural experiments require a functioning, metered intelligence and memory-reading cycle.

## Consequences and unresolved questions

**If adopted:** Snug begins inside a closed, shared laboratory. Its workers can inspect the whole corpus. Privacy decisions within Snug's conversations are experimental social judgements, not pre-arranged per-person memory lists. The membrane does not expose memory addresses by default. Internal publishers and model suppliers may be plural, but each experimental Snug has one history and one shared resource economy. Conversation with outsiders is withheld until evidence supports a separate maturity decision.

**Still open:** The native memory codec, relative-address maintenance, persistence across reorganisations, internal publisher protocol, how to measure learned social discretion, resource replenishment, admission and exit of laboratory workers, safeguards for any model-provider transmissions, and the procedure for deciding when outside conversation is justified.

**Not claimed:** That Snug already has independent social judgement, that gossip is superior to conventional restrictions, that every real-world disclosure is permitted, that URI-based Village Link interoperability has been superseded, or that an LLM's first-person language establishes a continuing person.

## Review and acceptance

Keep this ADR **Proposed** while the collaborators examine:

- whether its description of the laboratory matches what we actually intend to build on McKay, including the meaning of *full worker access*;
- whether the proposed membrane leaves Snug meaningful decisions while distinguishing the operators' actual responsibilities;
- how to evaluate gossip, mistakes and their social consequences without assuming that social governance will succeed;
- how multiple publishers and a shared resource ledger could work in a first implementation; and
- what evidence, if any, would justify admitting an outside conversational partner.

Accepting the ADR would endorse an **experimental direction**, not certify Snug as mature or grant him permission to converse beyond the laboratory.
