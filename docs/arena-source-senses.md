# Arena One: source senses (stage 1)

**Status:** experimental read-only source catalogue, 30 October 2026.

This is Snug's *first observational interface* into the preserved corpus,
not a claim that Snug has experienced, understood, indexed or learned from
its contents. The source archive and derived Arena remain separate.

The catalogue reads **all saved file metadata** from the complete copied
Arena manifest, not an arbitrary excerpt or a sample. The original
archives are not accessed. Its job is to answer: *what kinds of material
have we inherited, how many files, and where are they?*

## Offline use

Requirements: Python 3.11+, populated Arena One, no extra packages,
no API keys or network calls.

```sh
cd Cobble
PYTHONPATH=src python3 scripts/arena_catalogue.py \
  --arena /path/to/populated/arena summary

PYTHONPATH=src python3 scripts/arena_catalogue.py \
  --arena /path/to/populated/arena list \
  --category github-conversations --limit 25

PYTHONPATH=src python3 -m unittest discover \
  -s tests -p 'test_arena_catalogue.py' -v
```

The `summary` subcommand reports counts and raw bytes grouped into
GitHub conversations, Git repository material, GitHub manifests, ChatGPT,
traces, links, stars, hypotheses and other files. This is a classification
based on **source paths** only. It has no authority concerning semantics
or the contents' quality, integrity or completeness.

The `list` subcommand supports stable path-sorted pages with source
paths, raw byte counts and SHA-256 values recorded when Arena One was
populated. Options: `--category`, `--offset`, `--limit` (1 to 50),
and case-insensitive `--query` over file paths. No file bodies are
returned, no original file is modified, and the existing working
memory budget is not consumed by these **operator diagnostics**.

The catalogue validates manifest structure, source path safety, duplicate
paths, file counts and total bytes against saved Arena state. It does not
re-read files to check that they have not changed since population. Use
the existing `verify_arena` diagnostic for that integrity check.

## Connected Puck–McKay interface

The Cobble MCP server gains two fixed, read-only tools:

- `arena_catalogue(name="arena-a")` — one census of the full manifest,
  without individual file names.
- `arena_list_sources(name="arena-a", category="all", offset=0,
  limit=25, query="")` — bounded list of manifest entries,
  including individual paths and hashes.

Like the earlier Arena diagnostics, these accept only a simple local
Arena name, never an arbitrary filesystem path, network URL, shell
command, or publication action. The tunnel must be restarted and its
tools refreshed **after reviewed code is published and installed**.

**Privacy boundary:** even a *path* can reveal a sensitive project or
person's name. The source-listing tool is for the authorised lab
operator only; it is not a public catalog or a licence to transmit raw
private memories to a third-party model. Content access will need
separately designed disclosure, provenance and resource-budget controls.

## Costs, scope and limits

The two catalogue tools serve the *experimenter* and do not consume
Snug's simulated attention or historical retrieval budget. If we give
Snug its own browsing capability, it will need to be metered under the
five resource allowances and be subject to external permissions.
Otherwise an unmetered sensor would circumvent the scarcity experiment.

This stage does not search **inside** conversations, read Git commits,
retrieve ChatGPT dialogue, form hypotheses, mint Village Links or access
the adjacent web. The entire source corpus remains present in Arena One.
Later senses can traverse complete conversations and Git histories
in bounded calls **without truncating what is retained**.

The public reproducibility fixture and [quickstart](reproducing-arena-one.md)
remain useful independent checks, but a tiny synthetic fixture cannot
establish emergent behaviour in real data.
