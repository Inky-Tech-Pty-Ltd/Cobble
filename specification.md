# Cobble specification

**Status:** Working architectural specification — implemented capabilities, accepted decisions and research hypotheses are distinguished below.  
**Updated:** 23 November 2026  
**Project:** Inky Tech Pty Ltd — *Infrastructure of memory.*

> Memory is the masterpiece. Intelligence is paint.

This document describes the **current intended architecture**, not a claim that the whole architecture works. The [30 October specification](docs/history/2026-10/specification-2026-10-30.md) is preserved as a historical account of the earlier Arena and Village Link research programme. See the [README](README.md) for an introduction, the repository and tests for implementation evidence, and the accepted [ADRs](docs/adr/) for decisions. The existing [progress report](docs/progress.md) is a **14 October snapshot**, not an up-to-date statement of today's capabilities.

## 1. Proposition and priorities

**Cobble owns memory and tools; suppliers of intelligence use them.**

Cobble aims to make an accumulated body of work usable across changes in model provider, model instance, conversation, participant and eventually organisation. The enduring asset is an independently controlled corpus, its interpreted working memory, the tools and practices associated with it, and the relationships established through its work — **not a particular supplier's chat session**.

A user should be able to replace or combine suppliers without reconstructing the history of the work from scratch. A continuing entity might be associated with an individual, a team, a company, or a nested collection of collaborating entities. Whether memory and relationships suffice to establish a coherent, reputationally meaningful entity is an empirical and philosophical hypothesis, not an achieved feature.

[ADR-003](docs/adr/003-separate-corpus-sovereignty-from-village-link-research.md) sets the current order of work: **demonstrate corpus sovereignty first**. Village Link-based retrieval, salience, compression, adaptive forgetting and forced memory scarcity are valuable research programmes, **not prerequisites** for that demonstration. Established storage, indexing, search and retrieval methods are appropriate in the meantime.

## 2. The architectural objects

The following are **working roles and distinctions**. This list is not a new axiom system, nor does it redefine the Village Link primitive.

| Term | Working meaning |
| --- | --- |
| **Entity** | A continuing, bounded locus of memory, activity and governance; its persistence and coherence are propositions to investigate. |
| **Membrane** | The boundary at which an entity encounters opportunities, risks, resources and other entities. It may mediate access, interaction, connection and the representation of material crossing it. |
| **Corpus / sensory evidence** | Preserved records of encounters: chats, Git repositories, Issues, Discussions, files, observations and other sources. Potentially large, redundant and low-salience; provenance matters more than tidiness. |
| **Operational memory / table** | A selected, maintained representation of what a room needs to work: salient propositions, distinctions, relationships, procedures, context and hypotheses. It is not the underlying archive. |
| **Room** | A bounded process with incoming streams, operational memory, participating intelligences or tools, and an output stream. A room may itself participate in another room. |
| **Chair** | The role coordinating a room's work, including choices about context, suppliers, resources and potentially maintenance of the working table. The Chair need not be human or supplied by any fixed model. |
| **Participant / friend / supplier** | An intelligence or service recruited for a bounded contribution: human, external model, tool-assisted agent or potentially another Cobble. |
| **Connection** | A maintained relationship across a membrane; not the same thing as incorporating or equating the connected entity. |
| **Trust engine** | A proposed function that evaluates opportunities and risks at a membrane, using evidence, hypotheses, practices, relationships and consequences. It need not be a single hard-coded gatekeeper. |

These definitions elaborate the emerging [VillageLink governance grammar](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/89). They remain open to revision through experiments. In particular, **a room as a program** is a productive analogy: many inputs, maintained working state and one output stream. Operational memory is *like code* in the sense that its organisation affects the room's behaviour. This does not mean memory is literally executable source code, or that rooms have demonstrated neuron-like properties.

### Nested rooms and scale

A private Joe–Puck working room, an Inky Tech room shared with Hugo, a specialist room and a future organisation-wide room need not be different architectural species. They may be differently governed instances or compositions of the same general machinery.

A room may expose a bounded service to another room. This permits nested and networked structures **in principle**, without implying that arbitrary recursion, federation or a market in experts is currently implemented.

Membership in a shared room need not imply access to the private corpus of every participant. Similarly, an agent engaged in multiple rooms may exercise judgement about relevance, attribution, abstraction and what to bring across a boundary. An insight derived from private evidence may sometimes be expressed in a different, more appropriate representation — but a good abstraction can still reveal its origin. **Controlled transformation across a membrane** is a research and governance problem, not an automatic permission to publish private evidence.

We are exploring *adaptive permission webbing*: trust and decisions that emerge through relationships and consequences rather than assuming a perfect binary permissions lattice. Some baseline technical controls are still needed for credentials, irreversible actions, costs and explicit disclosure authority. These are enabling infrastructure, not a complete theory of social trust.

## 3. Sovereign memory: evidence versus working state

Cobble preserves source identity, versions, provenance, local copies and recoverability. Importers must not rewrite source history to suit a current hypothesis or memory budget.

Keep distinct:

1. **Source archive / sensory material:** the durable historical record, retained outside experimental eviction. Its messiness and redundancy can be an asset.
2. **Derived operational memory:** summaries, hypotheses, indexes, relations, selected context and practices that can be maintained, tested, revised or discarded without destroying evidence.
3. **Supplier context:** the exact bounded material actually sent to a particular external intelligence at a particular time. Merely having a source locally does not mean it was sent to a model.

A room can receive several incoming streams yet expose one outward stream of work, accompanied by inspectable provenance, context disclosure and resource accounting where applicable. Selection and representation decisions should be observable enough to compare approaches, not presented as magic.

**Corpus ownership and access are separate from supplier choice.** A supplier receives selected context for a call, not general ownership of the archive. Changes in supplier must not erase the source record or silently transfer disclosure authority.

The history of a relationship — including evolving terminology, commitments, corrections and shared work — is a candidate continuity asset. A model called through an API does **not** automatically inherit a ChatGPT session's memory or permissions; Cobble must supply any authorised context and tools.

## 4. Intelligence suppliers and tools

The first live supplier adapters have been built for **OpenAI GPT, Anthropic Claude and Mistral**, with recorded live exchanges. In the earliest supplier checks, no inherited memories were sent; subsequent selected-context and handover experiments are distinct from a completed continuous-identity demonstration.

A supplier-neutral interface should record, to the extent available:

- selected input context and disclosure boundaries;
- model/provider identity and configuration, status and errors;
- replies, provenance and any proposed actions;
- usage, latency and actual or estimated financial cost;
- enough exchange history to support repeatability, comparison and substitution.

Supplier requests must remain bounded by actual cost and authority constraints. No source archive is automatically transmitted just because it has been ingested.

**Cobble also owns the tools.** A tool may read a local archive, test an Arena, consult a source, or perform an authorised external write. Tool access in this ChatGPT conversation is **not automatically inherited** by GPT when invoked through the OpenAI API in a Cobble room. A separately designed, reviewed tool-dispatch boundary is needed inside Meetings.

### Demonstrated tool identity boundary — 23 November 2026

A dedicated GitHub machine user, **`puck-inky`**, has successfully posted to [VillageLink Discussion #89](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/89#discussioncomment-19820233) through Cobble's MCP Discussion-writing tool. The call returned a real comment URL and confirmed the author as `puck-inky`; it did not use Joe's identity. The token belongs to Puck and currently has organisation-wide repository Discussions read/write authorisation, while the **implemented MCP tool is still restricted to VillageLink**. Neither credential access nor this successful external write implies that an autonomous Cobble Meeting can dispatch arbitrary tools.

The role/identity boundary matters beyond this example: a delegated agent may act for an organisation while remaining independently attributable. Credentials are kept outside Git and source archives.

## 5. Rooms, Chairs and the demo

The working demonstration is a boardroom-oriented interface for calling intelligences into a shared task with visible context and costs. The intended user should be able to see who is at the table, what context each participant received, what each produced and what was spent.

The **Chair** is not synonymous with a human owner, a particular language model, or a static controller. It is the coordinating role. A future Chair may also maintain operational memory:

- inspect dependencies, contradictions, duplication, stale propositions and unclear provenance;
- suggest removal or consolidation from the table without erasing historical sources;
- propose and compare memory refactorings, ideally against capability-oriented regression cases;
- learn which inspection and maintenance methods work, and evolve its **own toolkit**.

This **evolving Chair-as-expert-system** is a hypothesis and prospective experiment, **not a demonstrated autonomous feature**. Salience need not mean frequency of use: rarely consulted knowledge can be vital when circumstances change. Compression, response quality, attention cost and future robustness may conflict. Tests must compare behaviour and consequences, not merely table size.

Roles may change occupants while the entity retains its accumulated expertise. This is one possible route towards a Chair being more than a fixed instruction prompt.

## 6. Membranes and governance

A membrane is not only a binary filter that admits or rejects material. It may also support:

- **connection** to another entity while preserving separate boundaries;
- **selective disclosure** of appropriately scoped evidence or memory;
- **transformation** into an abstraction, summary or different representation;
- **deliberate non-disclosure** where a source or context should stay elsewhere.

An agent acting in more than one room may encounter conflicting expectations. The hypothesis is that much practical governance can be achieved through delegated judgement, reputation, relationships, transaction costs and observed consequences. There is no claim that a perfect inference or privacy mechanism already exists.

Hard constraints on secrets, publishing authority, spending and irreversible operations remain practical engineering controls. They should be distinguished from — rather than mistaken for — a complete model of how people and organisations actually negotiate trust.

## 7. Cobble as supplier to Cobble

[ADR-004](docs/adr/004-cobble-as-intelligence-supplier.md) is accepted: preserve an interface through which a Cobble can be a bounded supplier to another Cobble, without either side assuming ownership of the other's memory, tools or governance.

A future request should communicate selected context, question, authority and budget; a response should communicate output, provenance, identity, status and resource usage. The caller should not have to know the internal suppliers of a specialist Cobble.

**This is an interface direction, not a completed federation.** Network endpoints, recursion control, cross-room delegation, inter-entity reputation and commercial settlement are not requirements for the present demo. Any implementation requires separate tests of cycles, failure, privacy, costs and provenance.

## 8. Village Link semantics and research boundary

The [Village Link](https://github.com/Inky-Tech-Pty-Ltd/VillageLink) project retains responsibility for the primitive. Conceptually:

```text
vl:[A in X]=[B in Y]
```

This asserts **identity of referent**, not similarity, a weighted edge, a typed relationship or an established fact. A Star Credential can express a hypothesis at the centre with supporting trace rays. Assertions and evidence are not to be conflated. A hypothesis is itself an addressable trace, not a privileged ontological class.

Cobble may ingest traces, preserve source identifiers, record observations, mint candidate hypotheses, inspect star rays and construct application indexes. These derived structures cannot silently redefine equality or publish uncertain claims as true.

Research still worth pursuing includes linked memory, salience, graph retrieval, compression, curiosity, scarce resources, specialisation, trade, social fitness and governance at multiple scales. The older [30 October specification](docs/history/2026-10/specification-2026-10-30.md) preserves the detailed **Exhibit B** Arena design, its five independent resource budgets, proposed tests and experimental constraints.

Under **ADR-003**, none of those unproven mechanisms is on the critical path for corpus sovereignty or the present boardroom demonstration. Existing prototypes should be preserved and assessed experimentally, not promoted to architectural obligations by inertia.

## 9. Current evidence and limitations

The following is an evidence-oriented summary, not an exhaustive release note. Implementation and local state may differ; verify before claiming a feature works end-to-end.

| Area | Demonstrated or recorded | Not thereby demonstrated |
| --- | --- | --- |
| Local memory | Retained trace and GitHub archives, provenance, source retrieval and Arena experiments on McKay | Complete accurate semantic graph or enduring identity |
| GitHub ingestion | Organisation-wide sync tooling and a reported six-repository run, with incremental versioned conversations | Complete recovery of all deleted, inaccessible or external data |
| Backups | Encrypted backup and at least one restore verification | Universal recovery guarantees for every later archive |
| Supplier interface | Live OpenAI, Claude and Mistral adapter exchanges; selected-context handover experiments | Supplier-independent continuity of a fully autonomous agent |
| Boardroom demo | Working local demo under development with real supplier integration and disclosure/cost features under test | Production multi-user rooms, mature Chair or recursive Cobble network |
| MCP | ChatGPT access to Cobble local tools via McKay tunnel; attributed `puck-inky` Discussion comment | General supplier-side tool dispatch or blanket external authority |
| Village Links | Trace/star experiments, inspection and conceptual grammar | Reliable emergent salience, governance or neuron analogue |

Some older documentation (notably [docs/progress.md](docs/progress.md)) is a dated snapshot and must not be read as the latest deployment status. For the evolving demo consult [the demo notes](docs/snug-demo.md), [room design](docs/boardroom-room-design.md), implementation, tests, and related Issues/ADRs.

## 10. Present priorities and test discipline

1. **Working sovereignty demonstration:** keep the corpus and tool boundary independent of intelligence suppliers; make provider calls, context disclosure, costs and results inspectable.
2. **Usable boardroom:** refine the current demo without conflating mock, staged, recorded and live behaviour.
3. **Real handover and continuity tests:** test resumed work across supplier changes, with enough source and disclosure metadata to explain differences.
4. **Institutional memory and nested rooms:** elaborate the Joe/Puck/Inky Tech use case and the distinct roles of private and shared memory; define testable behaviour before claiming it works.
5. **Independent research:** keep Village Link salience, adaptive memory maintenance, evolving Chairs and governance grammar alive as separately evaluated experiments.

For each claimed demonstration distinguish **offline stub**, **live external call**, **recorded replay**, and **anticipated feature**. Record what was sent, by whom, under whose authority, what was returned, what it cost, and what limitations remain. A pretty room is not proof of persistent identity; a successful API call is not proof of emergence.

The architecture is allowed to evolve. Substantive decisions should be captured in ADRs, and material changes should trigger a review of this specification. Preserve historical documents rather than rewriting the project's past.
