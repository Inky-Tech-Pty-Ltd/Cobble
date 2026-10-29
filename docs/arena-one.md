# Arena One — complete-corpus offline preflight

**Status: experimental first executable slice, 30 October 2026.** This is a
complete-source-copy and resource-accounting harness, **not** a multi-hemisphere
agent, a semantic memory system, a model gateway, a crawler, or proof of a
persistent entity.

See the [Cobble specification](../specification.md) for the five distinct
resource constraints, the early OpenAI/Kimi experiment and the juvenile
learner's proposed curiosity-driven exploration.

## A big world, not a tiny sample

The **protected source archive** is `~/cobble-data/`. The initial Arena is
`~/cobble-arenas/arena-a/`. These are separate trees. The Arena gets an
**untruncated byte-for-byte copy of every regular file in the local archive**,
including Git objects and conversation revisions; it does not discard
comments, trim old conversations, or select 1,600-character excerpts.
File-level SHA-256 digests and paths are recorded in a derived manifest.

The observed 30 October GitHub/other archive takes about **44 MB on disk**.
The eventual ChatGPT history may bring the collection to approximately
**120–150 MB**, but that is a planning guess, not a measurement or a confirmed
export. Start with a **256 MiB** raw-copied-source allowance for the first
Arena. There is plenty of disk space on McKay; later experiments can lower
the constraints deliberately.

The whole corpus is **present and available locally**, but nothing in this
first version has *read, indexed, interpreted, connected or trained on* its
contents. A 150 MB corpus cannot simply be placed in an LLM context window
and called an entity. Subsequent attention, indexing, hypothesis selection,
specialisation and web-adjacent curiosity are separate experiments.

The copy contains whatever is actually present in the archive at the time of
population. It is not proof of a complete history. The current GitHub source
archive contains private material; do **not** upload it to either intelligence
supplier, publish it, or treat its accessibility on disk as permission to share.
When the ChatGPT export arrives, preserve and ingest it separately before
recreating an Arena for a new measurement. The present code does not yet
understand or import OpenAI's ZIP export format.

## Budget accounting, version 0.2

The Arena declares five independent budgets:

| Resource | Initial accounting |
| --- | --- |
| `memory_bytes` | Sum of **raw source file bytes** copied into the Arena, not JSON/manifest overhead or model context tokens |
| `model_tokens` | Zero; model calls are absent |
| `attention_steps` | One step for the complete corpus population |
| `archive_reads` | One source-file read charged per copied source file |
| `external_ops` | Zero; no network or third-party action supported |

The source archive remains protected and recoverable outside these limits.
This copy is the initial *full available experience*, not a mature competitive
working-memory allocation policy. **No forgetting, summarisation, eviction
or adaptive learning occurs in this version.** A stricter working-memory
ceiling can be introduced later without throwing away historical evidence.

File counts and raw byte sizes are inventoried before copying. If the
declared memory or read budget is insufficient, population refuses the
operation rather than silently sampling a subset. The code rejects source
symlinks, checks for changed file sizes/timestamps while copying and
records SHA-256 digests for the copy. All source reads are local.

## First run on McKay

Only after the central Puck publication command has succeeded:

```sh
cd ~/Cobble
git pull --ff-only
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_arena_one.py' -v

PYTHONPATH=src python3 scripts/arena_one.py init \
  --archive ~/cobble-data \
  --arena ~/cobble-arenas/arena-a \
  --memory-bytes 268435456 \
  --attention-steps 10 \
  --archive-reads 100000 \
  --model-tokens 0 \
  --external-ops 0

PYTHONPATH=src python3 scripts/arena_one.py populate \
  --arena ~/cobble-arenas/arena-a

PYTHONPATH=src python3 scripts/arena_one.py status \
  --arena ~/cobble-arenas/arena-a
```

`init` refuses to overwrite an existing Arena. `populate` refuses to
replace a previous copy. Use a different `--arena` directory for a new
experiment; never delete or alter `~/cobble-data` to restart one.

The status output contains budgets, raw source counts and paths, but no
conversation text. The derived `corpus/` directory **contains the entire
potentially sensitive archive**: protect it like the original and exclude
it from Git, public CI, model-provider uploads and shared folders.

## Implementation limitations

A successful run establishes **full local byte preservation** and a bounded
initial copied-corpus allocation. It does not demonstrate graph-assisted
memory, corpus completeness, free-form exploration, continued bot identity,
correct Village Link equality or cross-provider sovereignty.

Version 0.2 has a single local writer, no concurrent locking, no incremental
source import, no eviction, no intelligent reading, no provider adapter, and
no web activity. The inventory + copy assumes the source archive is quiescent.
Metadata checks are not an atomic snapshot; concurrent mutation is not
supported. If a copy or local-state update fails, the Arena may need to be
discarded and reinitialised at a **new derived path**; the protected source
archive is not touched. Tests use small local fixtures, so the actual
McKay run is the first measured population at its real scale.

The five budget counters are a **first experimental ledger**, not yet a
universal enforcement mechanism for arbitrary future integrations.

## Next increments

1. Confirm the size and integrity of the actual populated corpus; preserve
   and add the full ChatGPT export once obtained, in a *fresh* Arena.
2. Make the complete local corpus **addressable and traversable** to the
   juvenile learner; expose text and GitHub history through permission-aware
   adapters without truncating the underlying source material.
3. Introduce multiple **competing internal working-memory policies** with
   bounded attention, retrieval and intelligence, without deleting source
   history.
4. Add early **OpenAI and Kimi** hemispheres using an interchangeable adapter,
   with cost ceilings and explicitly selected, authorised material.
5. Compare task-driven learning with budgeted idle **exploration of the
   adjacent web**. Curiosity should use only spare resources, and external
   network access must be permissioned and metered.
