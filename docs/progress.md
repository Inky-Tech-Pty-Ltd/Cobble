# Cobble progress — 14 October 2026

A snapshot of what has **actually been demonstrated**, what remains a
hypothesis, and what comes next. This is an experiment log, not a product
announcement. For intent, see [the specification](../specification.md).

## Demonstrated

### 1. User-controlled persistent memory

Cobble stores working records on McKay under `~/cobble-data/`, outside the
software's Git repository. The store includes trace records, hypotheses,
star credentials, Village Link rays, retained text and imported GitHub data.
The source memory systems remain distinct from the local copies.

### 2. First hypothesis-centred star

The hypothesis **“Memory is the masterpiece.”** was given a minted Cobble
trace URI as its centre and linked to three traces in separate source contexts:
the Cobble README, an InkyTech README and a ChatGPT conversation. Each ray is
an ordinary `vl:` assertion. The star is not a new primitive, and no
equivalence assertion has been independently established as true.

### 3. Local retrieval of a ChatGPT memory

An excerpt from a ChatGPT conversation was saved with its original source
URI, a text-quote selector and a local-copy URI. A reusable Cobble resolver
later retrieved the excerpt without contacting ChatGPT:

> Infrastructure of memory.
>
> Memory is the masterpiece.  
> Intelligence is paint.

The same resolver worked with the record created by an earlier manual
experiment. **This proves local retrieval of one retained excerpt**, not
resilience of the complete ChatGPT conversation history.

### 4. Encrypted off-machine backup

A Cobble memory archive was encrypted with `age` and copied through iCloud
Drive. Its presence was verified on iCloud.com. A restoration on McKay
successfully decrypted and compared the original small archive against its
working memory store, with no differences. A later encrypted archive included
the newly ingested Git history; that second archive was also visible on
iCloud.com.

The **larger archive has not yet undergone an independent restore test**;
neither has recovery using a separately downloaded archive and the key
retrieved independently from 1Password. Backup automation and retention
policy remain future work.

### 5. Git repository ingestion

A reusable importer copies Git objects and refs from a local checkout into a
separate bare repository under `~/cobble-data/github/`. Observed HEAD commits
are pinned as snapshots, and subsequent imports can acquire new commits while
retaining earlier referenced history. The archived Cobble Git repository
passed `git fsck --full` over 118 objects; two dangling commits were reported,
but no corruption.

After publication to `main`, Cobble re-imported its own newly published
commit, `a127303687b98290993ec4ecb88884cb699fb6c1`.

This captures history available in the local checkout; it is not a complete
export of GitHub or of Git LFS and submodule content.

### 6. GitHub conversations

A second importer uses GitHub REST and authenticated GraphQL access to
preserve Issues, PRs, reviews, Discussions, comments and replies in
versioned local JSON snapshots. Re-importing unchanged records avoids
duplicates; updated conversations retain earlier snapshots.

A live ingestion of **the Cobble repository** succeeded:

| Source | Count |
| --- | ---: |
| Issues | 4 |
| Pull requests | 1 |
| Discussions | 2 |

Seven `latest.json` records were verified on McKay, occupying about 212 KB
across the GitHub conversation archive at that point. The API records retain
available identifiers, authorship, URLs and timestamps.

**VillageLink conversation ingestion was proposed, not yet confirmed as run.**
The importer does not capture all GitHub attachments, deleted content or
every category of provider metadata.

### 7. Tested, published software

The Cobble tests progressed from 5 to 12 to **16**, then to **21 passing
automated tests** on McKay. The local trace, star-extension, recovery,
Git import and GitHub conversation tools were staged and published through
the InkyTech Puck-GPT Express Lane. The GitHub conversation importer
subsequently succeeded against real GitHub APIs.

These tests cover specific behaviours, not the entire intended system.

## Not yet established

- Automatic detection of recurring memes, or reliable judgements about
  whether asserted equivalences hold.
- A coherent, continuous bot identity residing in the graph, or an entity
  carrying a measurable reputational asset.
- Governance emerging from consequences across memory systems.
- Autonomous maintenance, resource optimisation or forgetting by a Cobbler
  service.
- An MCP connection giving a ChatGPT instance direct access to McKay's store.
- Full historical ChatGPT ingestion or ongoing synchronisation.

These are subjects for experiments rather than assumptions to encode in the
Village Link primitive.

## Next experiments

1. **ChatGPT history:** Await the requested archive, inspect its structure,
   then build repeatable ingestion of complete conversations.
2. **Broader GitHub history:** Import VillageLink conversations and consider
   the other Inky Tech repositories.
3. **Memory access:** Expose a narrow, permissioned interface (potentially
   MCP) for looking up traces, retrieving local copies and inspecting stars.
   Establish what the connecting assistant can actually access.
4. **Cross-system links:** Test deliberate Village Links between the same
   meme represented in ChatGPT, Git files and GitHub conversations; do not
   infer equivalence from text similarity alone.
5. **Resilience:** Independently restore the larger encrypted archive and
   later automate snapshots, retention and periodic verification.

## Useful implementation notes

- [First star experiment](first-star.md)
- [Local trace resilience](trace-resilience.md)
- [Git ingestion](git-ingestion.md)
- [GitHub conversation ingestion](github-conversations.md)

**Principle:** Preserve the distinction between *a published assertion* and
*an established equivalence*, and between *preserving memory* and *creating
an entity from it*.
