# Cobble Specification

**Status:** Experimental working specification; intended behaviour and testable hypotheses, not a claim of completed functionality  
**Updated:** 29 October 2026

For demonstrated implementation and limitations, see [docs/progress.md](docs/progress.md) and the repository's tests. Recent conceptual questions are recorded in [Issue #10](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/10); the proposed arena experiment follows [Village Link Discussion #78, Exhibit B](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/78).

## Proposition

Cobble tests whether connected traces in the memory systems shared by a person and an AI work-partner can constitute a coherent, portable entity carrying an accumulated body of work and reputational asset.

Might the entity persist across changes in the **supplier of intelligence**? Might scarce memory and the consequences of transactions influence what it learns, retains and does? Might a preference for relationships, diversity and trade emerge or prove adaptive?

These are **hypotheses to investigate**, not properties established by the current implementation. The aim goes beyond retrieving historical passages for a chatbot. Memory is proposed as part of an ongoing cycle of **experience → interpretation → action → consequences → changed memory**.

## Boundaries and roles

Keep three things distinct:

1. **Corpus and memory store:** Retained source material, traces, identities, provenance, observations, and any experimental graph structures, held under customer-controlled storage and access policies. An original source can remain external while a recoverable local copy is preserved.
2. **Cobbler:** Application machinery that ingests, selects, mints, retrieves, proposes and maintains candidate connections, and may experiment with compression and resource allocation. It is not a new Village Link primitive.
3. **Suppliers of intelligence:** Models and other processes recruited to examine or act on parts of the corpus. Their providers, instances and configurations may change; no supplier automatically owns the corpus or constitutes a persistent entity.

The [Village Link](https://github.com/Inky-Tech-Pty-Ltd/VillageLink) specification owns the semantics of the primitive and the abstract Star Credential. In its current conceptual form:

```text
vl:[A in X]=[B in Y]
```

This is a **strict assertion of equality of referent** between traces in their memory systems, not a measure of similarity, a typed relationship, or proof that the assertion is true.

Cobble may assign trace URIs, record source observations, construct candidate hypotheses, inspect asserted rays and build indexes or local representations. Such application structures must not redefine Village Link equality, make uncertain assertions true by fiat, or silently turn internal proposals into published claims.

A **hypothesis**, including the centre of a Star Credential, is itself an ordinary addressable trace in the corpus. It should not require a conceptually privileged class of meanings outside the corpus merely because an implementation currently stores hypotheses separately.

## Memory and provenance

The working picture is:

**Memory systems → traces → assertions and observations → local graph/representations → services and action**

- A **trace** is an addressable expression in a source memory system. Original source identity, selected occurrence, local copy and stable Cobble identifier remain distinct.
- A **Village Link** asserts the same referent for two traces. Its presence does not establish equality; imperfect and contradictory assertions are experimental inputs.
- A **Star Credential** records one centre and an unordered set of member traces, using ordinary Village Link rays. Its representation may be useful for publication or interchange, but retrieval performance alone does not establish that particular JSON syntax as necessary.
- **Provenance and observations** record how material was obtained or whether access later succeeded. Unavailability should not erase historical evidence; recorded availability does not guarantee future retrieval or integrity.
- **The graph** is a candidate mechanism for coherent memory, not yet demonstrated to create an enduring entity.
- **Indexes, rankings, summaries and embeddings** are expendable application machinery, not independent sources of semantic authority.

The first practical task remains preservation of a **real, interpretable corpus** from GitHub, ChatGPT and other permitted sources, with continuing ingestion and independently testable recovery. Do not infer equality from similar words. The historical archive should be backed up and recoverable independently of an experimental memory budget.

## Exhibit B: experimental arena

An **arena** is a bounded environment for testing changes to memory, interpretation, allocation and action. It is not a new Village Link object.

The initial [Exhibit B](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/78) design asks us to:

1. **Load historical evidence.** Begin with available source memories, retaining their provenance and source distinctions. Do not require a pre-constructed semantic graph.
2. **Impose a finite working budget.** Create an arena with a measurable capacity for retained working material; the source archive remains independently recoverable. A memory limit must eventually force choices.
3. **Introduce fresh experience.** A new prompt, observation, interaction or feedback event enters the arena. The input itself becomes addressable evidence.
4. **Recruit hemispheres.** One or more semi-independent intelligence processes examine the experience and relevant history. They may use different model suppliers.
5. **Run a separated-and-recombined cycle.** Hemispheres independently propose memes, matching traces, equivalence hypotheses, Village Links, possible star centres and natural-language interpretations. They then compare their proposals, challenge evidence, preserve disagreement where appropriate and decide what action to recommend.
6. **Choose how to spend scarce memory.** Retain, connect, abstract, compress, weaken or release working material under an inspectable, experimentally varied value function.
7. **Act and record consequences.** Begin with sandboxed or human-authorised actions. Outcomes and feedback enter the next cycle as fresh evidence.

An arena can run with **one, two, five or more hemispheres**. A hemisphere is a role in a particular experiment, not a permanent half of a brain, a specific nationality, model brand, person or guaranteed continuing identity. Disagreement need not be forced into consensus; a contested hypothesis can itself remain part of the memory.

A fast, context-sensitive **salience summary** supplied to an external conversation is one possible by-product. It is **not** Exhibit B's principal success criterion.

## Scarcity, value and social consequences

The finite-memory experiment should compare value functions rather than assume that one is correct. Candidate strategies include recency, apparent relevance, compression efficiency, retrieval utility and **social status arising through relationships, reputation and trade**.

Exhibit B proposes that a social strategy may help an entity obtain resources indirectly from mutually beneficial relationships. This is speculative; neither rewards for popularity nor a self-asserted reputation are proof of social fitness.

Measure consequences, including harm: usefulness to collaborators, fulfilled commitments, correction of errors, independent corroboration, diversity of contacts, and costs imposed on others. Contrast successes with failures such as sycophancy, overconfident identity linking, status chasing and exclusion of dissent.

The user or experimenter sets and enforces actual limits on storage, model spending, calls and publication. **No simulated resource pressure authorises an agent to seek real resources, contact people, spend money, reveal private history or publish assertions without separately granted permission.** We test a value function; we do not grant it unrestricted authority.

## First sprint: a falsifiable, inspectable loop

The near-term experiment should produce an auditable record of one or more complete cycles:

```text
new experience
  → independent interpretations
  → evidence search and candidate equality assertions
  → disagreement / reconciliation
  → bounded-memory decision
  → proposed or permitted action
  → observed consequence
  → updated memory
```

Each cycle should retain the input, source identifiers, independent hemisphere outputs, rejected as well as accepted suggestions, reasons for retention or eviction, measured costs, and observed (not merely predicted) consequences. Preserve the **difference between proposing, minting and publishing** a Village Link or Star Credential.

Baseline comparisons should include a single-hemisphere run, multiple hemispheres, and simple memory allocation rules. Run adverse cases involving false links, missing sources and low-quality but socially attractive information. Do not present a successful retrieval or attractive summary as evidence that a social entity or governance has emerged.

Use the **existing imported GitHub corpus** to begin. The pending ChatGPT export can be ingested as a separate source later; its arrival is not a prerequisite for the first arena. Earlier graph, ablation and adversarial retrieval experiments remain relevant controls, not immutable architectural constraints.

## Design restraint

Before introducing a special internal object, ask:

> But might that be a meme? Should we really build this from the outside, when maybe it belongs on the inside?

Use conventional, inspectable and portable files for source preservation while exploring alternative derived memory architectures. Do not hard-code a social society, fixed publishers, authoritative truth scores or a required Star Credential serialization merely because they are convenient for an initial prototype.

The broader evolutionary hypotheses — emergent internal publishers, specialisation through trade, memetic cascades, near-critical memory complexes and ultimately a coherent self-sovereign entity — remain research questions. The implementation, or *germ line*, can change independently of the preserved corpus.

## Progress, limits and next checks

Existing work has demonstrated selected trace minting, archived Git history and GitHub conversations, a bounded-memory read path, Star Credential construction and inspection, and read-only MCP access. It has **not** demonstrated automatic and reliably correct meme recognition, continuous identity, autonomous social governance, safe independent resource seeking, or a working multi-hemisphere arena. See [progress](docs/progress.md) and [research](docs/research) for the actual evidence and qualifications.

Near-term checks:

1. Confirm full import and recovery of the selected real corpus, retaining original identifiers and data provenance.
2. Establish reproducible arena budgets and resource accounting without risking the archival copies.
3. Integrate replaceable intelligence providers behind a limited interface; keep model input permissions and expenses explicit.
4. Evaluate candidate equality assertions against evidence before publication and preserve dissenting interpretations.
5. Compare single- and multi-hemisphere cycles and competing memory-value rules on real, inspectable cases.
6. Independently test backup restore, privacy boundaries and source disappearance before ingesting more sensitive material.

**Proposed entity continuity, social fitness and governance are outcomes to test, not properties to assert because the software has been written.**
