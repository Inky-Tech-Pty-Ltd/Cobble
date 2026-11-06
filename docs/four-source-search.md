# Four-source local search — first navigation slice

**Status:** experimental, operator-only and offline. No model/provider connection.

This slice adds lexical search over four kinds of already preserved material
on McKay. It implements immediate corpus sovereignty, not a Village Link
graph or evidence that Snug has understood the material.

| Source | Searchable now | Exclusions / next increment |
| --- | --- | --- |
| ChatGPT | Latest snapshot, all available text message nodes including branches | Attachments, earlier searchable revisions |
| GitHub | Latest stored Issues, PRs, Discussions, comments and reviews | Git blobs, commits, old revisions |
| InkyTech hosting | UTF-8 text files in current rsync mirror | DBs, binaries, old revisions |
| VillageLink hosting | Same as InkyTech | Same |

The source trees are unchanged. A build creates a private SQLite FTS5 index
under ~/cobble-data/index/. It stores **copies of private text** and must
never be committed or published. Keep it within encrypted backup coverage.

## Try on McKay (Ubuntu WSL)

From ~/Cobble on the feature branch:

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_local_search.py' -v
    PYTHONPATH=src python3 scripts/search_cobble.py build

Build prints indexed/skipped counts, **not** private content or filenames.
Check all four sources say present=true and indexed > 0. If one is empty,
investigate format coverage rather than claiming success.

    PYTHONPATH=src python3 scripts/search_cobble.py search 'memory masterpiece'

Each result has a source, source-relative reference, a short excerpt, and a
stable document ID. To read a bounded beginning of a result:

    PYTHONPATH=src python3 scripts/search_cobble.py show DOCUMENT_ID

Show defaults to 1,800 characters (allowable: 100–12,000). Results and
previews may contain real private memories or hosting content. **Do not paste
these into a public issue or another AI service** without appropriate permission.
Aggregate build counts are safe to use for importer diagnosis.

## Boundaries

- No API token, network call, paid model, or change to original corpus.
- Failed rebuild leaves the previous SQLite index intact.
- FTS5 is lexical search, not embeddings or semantic understanding.
- References remain source-relative. Document IDs are stable across rebuilds
  while each source/reference pair exists.
- ChatGPT revisions remain available in the archive but only the latest
  version is searchable in this first slice.
- Hosting text types: .md, .txt, .html, .xml, .csv, .php, .py and related.
  Files larger than 1 MiB, binary content, symlinks, dotfiles, known caches,
  and obvious secret/config filenames are excluded. This is not a full census.
- WordPress/MediaWiki databases were not included in rsync capture.
- This is strictly an **operator** tool, not a Snug or customer API.
- SQLite index is not separately encrypted: it relies on local permissions
  and encrypted backup. Do not deploy in a multi-tenant context.

## Acceptance and next work

Synthetic CI tests one hit from each family, revisions, stable references,
bounded reads, literal matching, atomic rebuild and symlink/secret exclusions.
Real McKay file coverage and quality must be verified locally.

The next slice is a **permission-aware Snug retrieval interface**, with
selected sources, audit, token/cost accounting and explicit limits on what
external intelligence providers may receive. This first operator tool is
not that interface.
