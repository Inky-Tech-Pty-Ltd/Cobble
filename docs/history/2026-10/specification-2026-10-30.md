# Cobble Specification

**Status:** Experimental working specification; intended behaviour and testable hypotheses, not a claim of completed functionality  
**Updated:** 30 October 2026

For demonstrated implementation and limitations, see [docs/progress.md](docs/progress.md) and the repository's tests. Recent conceptual questions are recorded in [Issue #10](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/10); the proposed arena experiment follows [Village Link Discussion #78, Exhibit B](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/78).

## Proposition

Cobble tests whether connected traces in the memory systems shared by a person and an AI work-partner can constitute a coherent, portable entity carrying an accumulated body of work and reputational asset.

Might the entity persist across changes in the **supplier of intelligence**? Might scarce memory and the consequences of transactions influence what it learns, retains and does? Might a preference for relationships, diversity and trade emerge or prove adaptive?

These are **hypotheses to investigate**, not properties established by the current implementation. The aim goes beyond retrieving historical passages for a chatbot. Memory is proposed as part of an ongoing cycle of **experience → interpretation → action → consequences → changed memory**.

## Boundaries and roles

Keep three things distinct:

1. **Corpus and memory store:** Retained source material, traces, identities, provenance, observations, and any experimental graph structures, held under customer-controlled storage and access policies. An original source can remain external while a recoverable local copy is preserved.
2. **Cobbler:** Application machinery that ingests, selects, mints, retrieves, proposes and maintains candidate connections, and may experiment with compression and resource allocation. It is not a new Village Link primitive.
3. **Suppliers of intelligence:** Models and other processes recruited to examine or act on parts of the corpus. Their providers, instances and configurations may change; no supplier automatically owns the corpus or constitutes a persistent entity. Early use of independent suppliers is itself a test of portability and self-sovereignty, not merely a later optimisation of answer quality.

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

An essential prerequisite is preservation of a **real, interpretable corpus** from GitHub, ChatGPT and other permitted sources, with continuing ingestion and independently testable recovery. Do not infer equality from similar words. The historical archive should be backed up and recoverable independently of an experimental memory budget. The current GitHub acquisition and bounded conversation-portability tools described below are implemented; private ChatGPT archive ingestion, graph portability and arena-scale recovery remain separate tasks.

## Source acquisition and portable corpus: current capabilities

These capabilities now exist on `main`; they are deliberately **separate from the experimental arena**.

**Organisation-wide GitHub acquisition.** [`scripts/sync_github_corpus.sh`](scripts/sync_github_corpus.sh) discovers repositories accessible to the authenticated GitHub account within `Inky-Tech-Pty-Ltd`, maintains dedicated source checkouts under `~/cobble-source-checkouts/`, and imports observed Git history and GitHub issues, pull requests and Discussions under `~/cobble-data/github/`. It has `--dry-run` and deliberately refuses to overwrite unsuitable or locally modified checkouts. It is a **manual, incremental acquisition tool**, not an installed scheduled job. It does not automatically make memory traces, equivalence assertions or an Arena. See [GitHub corpus sync](docs/github-corpus-sync.md).

**Bounded GitHub conversation portability.** [PR #13](https://github.com/Inky-Tech-Pty-Ltd/Cobble/pull/13), now merged, adds export and offline restore of selected GitHub conversation archives, preserving original snapshot bytes, version digests and `latest.json` pointers and rejecting malformed, missing, conflicting or path-unsafe entries. A verified *public GitHub API-view* run on 26 October 2026 included **89 conversations and 178 archived files** from **VillageLink and Cobble**; all restored files matched byte-for-byte. These counts concern those two repositories at that observation time, **not** all repositories or a completeness guarantee. See [corpus portability experiment](docs/corpus-portability-experiment.md) and [Cobble Issue #12](https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/12).

**Testing boundary.** The offline regression tests run through the [corpus portability workflow](.github/workflows/corpus-portability.yml). The networked, authenticated public-corpus round trip is a **manually dispatched** check, not part of every pull request. Neither test proves semantic equivalence, graph portability, stable agent identity, or the continued availability of the original sources.

**Operational boundaries.** GitHub API ingestion is not atomic across a changing organisation; deleted or inaccessible content, Git LFS and some attachments are outside acquisition. A sync interrupted between repositories may leave a partially refreshed archive. The current JSON portability package is assembled in memory, so its behaviour at Arena-scale corpus sizes is untested. Export should use a quiescent archive; restore should use a private destination without concurrent writers. Restoration validates content before writing but is **not** a transactionally atomic filesystem operation. The export package can contain sensitive conversation material; keep it outside Git and protect it and backups accordingly.

The source archive is evidence held for recovery and independent interpretation; it must not be treated as the scarce working memory or modified destructively by arena allocation, forgetting, link experiments or provider changes.

## Exhibit B: experimental arena

An **arena** is a bounded environment for testing changes to memory, interpretation, allocation and action. It is not a new Village Link object.

The initial [Exhibit B](https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/78) design asks us to:

1. **Load historical evidence.** Start with **the complete available local corpus**, without arbitrarily restricting the juvenile learner to excerpts or selecting only the most obviously relevant material. Copy or make it accessible under an independently controlled Arena store, retaining file integrity and source provenance. The protected original archive remains outside the experimental eviction process. Local presence does **not** imply that every byte has been attended to by a hemisphere, or that any private material may be sent to an external model.
2. **Impose explicit resource budgets.** Set initial capacities **after measuring** the full local corpus; the illustrative sizes in Exhibit B are not implementation targets. The first offline scaffold may use a generous raw copied-corpus allowance while subsequent runs constrain *derived working memory* independently. Account separately for memory, intelligence, attention, historical retrieval and external resources (below). A limit must eventually force choices without deleting historical evidence.
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

## Five independent resource budgets

Constrained working memory combined with effectively unlimited intelligence would distort Exhibit B. An entity could simply re-read the complete source corpus, call an external model repeatedly and reconstruct most of its discarded working memory. A finite *memory* budget alone therefore does not test the pressures of a resource-dependent entity.

The arena must support **five independently parameterised and measured budgets**:

| Resource | Example accounting units and boundaries |
| --- | --- |
| **Working memory** | Retained bytes or units in the arena, including summaries, links, candidate hypotheses and derived indexes; eviction affects only the derived arena |
| **Intelligence** | Model invocations, input/output tokens, retries and monetary or compute cost; separate counts for each supplier and joint deliberation |
| **Attention** | Time or bounded processing steps allocated to an incoming experience; record wall-clock latency apart from chargeable model use |
| **Historical retrieval** | Searches and reads against preserved source material, including calls, returned bytes or tokens; a read costs the arena something even though the archive survives |
| **External resources** | Network use, additional storage, paid services, disclosure of source passages and any permitted action outside the arena, with externally enforced ceilings |

For each run declare the **units, maximum allowances, scope and reset rules**, plus how failed and repeated operations consume budgets. A first complete-corpus copy is not the same as an LLM context window, and a raw-copy byte ceiling is only a scaffold for a future budget governing dynamically retained and derived working memories. Record costs actually incurred, not only estimates. Resource ceilings are experimental parameters, not normative constants. A generously resourced control still needs finite, recorded allowances; only the selected dimensions should differ between comparison runs.

**The protected source archive is outside the memory eviction game.** Charging an arena for historical access constrains its working behaviour, not the independent preservation, backup or restoration of source evidence. Simulated rewards or scarcity may never override actual limits on money, privacy, network activity, publication or contact with third parties.

Measure the substitutions and trade-offs: when is retention cheaper than expensive reconstruction? When does compression pay for its model cost? Does additional historical retrieval outperform an extra hemisphere? Does an apparent gain from abundant intelligence vanish once computation and retrieval are priced? An intelligence supplier cannot reconstruct unique events when all evidence of those events has been lost.

## Early multiple-supplier test of sovereignty

Cobble proposes that an entity's persistent history resides in its **corpus**, rather than in any one model or provider's chat session. **Provider substitution should therefore be tested early**, not deferred until the Arena's memory allocation algorithms are sophisticated.

The preferred first real multi-supplier experiment will recruit **OpenAI and Kimi**. Kimi's early presence is an explicit test of *supplier diversity and independence* in the sovereignty proposition, not an assertion that either model is better, that two providers suffice for sovereignty, or that a difference in supplier location by itself guarantees independence. No Kimi account, model version, API entitlement or expenditure is presumed to exist at the time of this specification.

Build a small **provider-neutral adapter** that can assign equivalent, permitted source-attributed material and a declared per-provider budget to each hemisphere. Preserve each provider's independently produced proposals, model/version metadata when available, source references, usage and monetary estimates, disagreements and any reconciliation step. A stub provider can establish that the software works offline; it is **not** evidence of a real two-provider test.

The early controlled comparison asks:

1. **Continuity:** Can both suppliers work from the *same* preserved, independently controlled corpus without making the model supplier's conversation store the authoritative source?
2. **Substitution:** If the first supplier is absent or replaced, can the second resume a subsequent input with the same authorised memory and history, without a bespoke migration of entity identity?
3. **Diversity and cost:** What different hypotheses and errors arise, and are the gains worth added intelligence, attention, retrieval and coordination costs?

Use a small set of **public or otherwise explicitly authorised** source excerpts first; do not transmit the whole GitHub archive, private InkyBooks material or a future ChatGPT export to either provider merely because it was ingested locally. Keep credentials out of the repository and the corpus, and configure spending caps before live model calls.

This test may begin once the offline arena harness can account for a complete input cycle. It **need not wait** for the full ChatGPT export, a mature theory of social value or a large arena. Later runs can vary which models, how many hemispheres and how much resource each receives. Model selection and a working configuration belong to the application, **not** the Village Link primitive.

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

Baseline comparisons should include a single-hemisphere run, multiple hemispheres, simple memory allocation rules and different combinations of the five resource budgets. Compare constrained and generously resourced intelligence at the *same* memory limit, and constrained versus generous historical retrieval at the *same* intelligence limit. Use stub suppliers for repeatable offline tests and real OpenAI/Kimi calls for the early provider-substitution experiment. Run adverse cases involving false links, missing sources and low-quality but socially attractive information. Do not present successful retrieval, an attractive summary or two working API connections as evidence that a social entity or governance has emerged.

**Make the full preserved local GitHub corpus available to the Arena**, without sending its private contents indiscriminately to any model supplier. Provider requests should select only the material necessary and explicitly permitted for that call. The ChatGPT export can be imported and made available in full as an additional source when it arrives; its arrival is not a prerequisite for starting the offline Arena. Earlier graph, ablation and adversarial retrieval experiments remain relevant controls, not immutable architectural constraints.

## Juvenile exploration as a resource-allocation hypothesis

When an immediate task does not consume the Arena's available resources, a **juvenile learner** might devote some spare capacity to its adjacent environment, particularly the web. It can encounter unanticipated material, compare it with its internal memories and retain provisional, sometimes sketchy hypotheses. This is a candidate **curiosity strategy**, not an instruction to indiscriminately collect information, browse continuously or treat encountered statements as true.

Explore two conditions: **task-directed attention** and **idle-capacity exploration**. Compare their costs and later consequences, including whether exploratory hypotheses prove useful when subsequent problems arise. The learner may discover information worth revisiting without retaining an entire external page, provided the preserved source is independently retrievable and lawful to access. There is no requirement that curiosity be intrinsically rewarded or that more collected information be deemed better.

An experimental web-adjacency adapter must respect separate **network permissions, privacy controls, request limits, source-access conditions and intelligence/attention budgets**. The Arena's internal sense of surplus resources cannot create an entitlement to access another person's system, disclose private memory to a supplier or spend money. The initial offline scaffold has no active crawler and does not yet test curiosity.

## Design restraint

Before introducing a special internal object, ask:

> But might that be a meme? Should we really build this from the outside, when maybe it belongs on the inside?

Use conventional, inspectable and portable files for source preservation while exploring alternative derived memory architectures. Do not hard-code a social society, fixed publishers, authoritative truth scores or a required Star Credential serialization merely because they are convenient for an initial prototype.

The broader evolutionary hypotheses — emergent internal publishers, specialisation through trade, memetic cascades, near-critical memory complexes and ultimately a coherent self-sovereign entity — remain research questions. The implementation, or *germ line*, can change independently of the preserved corpus.

## Progress, limits and next checks

Existing work has demonstrated selected trace minting, archived Git history and GitHub conversations, organisation-wide acquisition tooling, a bounded offline GitHub conversation archive round trip, a bounded-memory read path, Star Credential construction and inspection, and read-only MCP access. It has **not** demonstrated organisation-wide snapshot atomicity, portable *semantic graphs*, automatic and reliably correct meme recognition, continuous identity, autonomous social governance, safe independent resource seeking, or a working multi-hemisphere arena. See [progress](docs/progress.md), [corpus sync](docs/github-corpus-sync.md), [portability evidence](docs/corpus-portability-experiment.md) and [research](docs/research) for the actual evidence and qualifications.

Near-term checks:

1. On McKay, fast-forward the Cobble checkout and run `bash scripts/sync_github_corpus.sh --dry-run`; inspect the repositories and intended checkouts before any real sync. Run the sync under existing GitHub credentials only after confirming scope. A successful run is a current observation, not evidence of historical completeness.
2. Inventory **the full available source corpus** and verify source identifiers, available local copies and protected archival backups. Use the [offline Arena One preflight](docs/arena-one.md) to make an untruncated, byte-checked copy into a separate working tree. Use the independent [portability CLI](scripts/portable_github_corpus.py) to test a **bounded, quiescent GitHub conversation subset** in a disposable destination; it is not yet a complete evolving-Arena transport.
3. Establish an isolated derived Arena store, independent recovery of original evidence and reproducible accounting across the **five distinct resource budgets** above. The first copy can use a generous **256 MiB source allowance** (initial GitHub archive approximately 44 MB, with a larger ChatGPT corpus still unmeasured); experimentally constrain and evict only **derived working data** after the complete source environment is available.
4. Implement the minimal replaceable-provider interface with deterministic offline stubs, then integrate **both OpenAI and Kimi early**, using a small explicitly permitted set of source passages. Record independent outputs, token/call/attention/retrieval costs, provider substitution and disagreements, with capped spending and no automatic external publication.
5. Evaluate candidate equality assertions against evidence and independent adversarial cases. Preserve disagreements, rejected suggestions, and proposed versus published assertions; compare single- and multi-hemisphere cycles and competing value rules.
6. Record simulated or human-authorised actions and **observed** consequences separately from predicted outcomes. Independently test backup restore, privacy boundaries and source disappearance before ingesting or transmitting more sensitive material.

**Proposed entity continuity, social fitness and governance are outcomes to test, not properties to assert because the software has been written.**
