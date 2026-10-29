# Reproducing Arena One without McKay

**Status:** experimental offline reproducibility harness, 30 October 2026.
This demonstrates **whole-corpus copying and resource accounting**, not
cognitive emergence, a model-independent entity, a two-hemisphere agent or
a working ChatGPT export importer.

## Start here: public synthetic corpus

Requirements: Git, **Python 3.11 or newer**, a local filesystem, and
enough space for a disposable copy of the input corpus. No API key,
GitHub account, McKay machine, MCP tunnel, OpenAI account, Kimi account,
network access during the experiment, or third-party Python packages
are necessary.

```sh
git clone https://github.com/Inky-Tech-Pty-Ltd/Cobble.git
cd Cobble

PYTHONPATH=src python3 scripts/reproduce_arena_one.py

PYTHONPATH=src python3 -m unittest discover \
  -s tests -p 'test_arena_reproducibility.py' -v
PYTHONPATH=src python3 -m unittest discover \
  -s tests -p 'test_arena_one.py' -v
```

The runner uses three small, **entirely invented**, committed files:
one ChatGPT-like conversation, one GitHub-like discussion and one unfinished
hypothesis in `tests/fixtures/arena_one_public/`. These are illustrative
documents, **not official OpenAI export files, real GitHub API snapshots,
or a scientific corpus of meaningful scale**.

The runner allocates a new disposable Arena, copies **all three complete
files**, compares content and file names byte for byte, and prints JSON with
the source inventory digest, copied inventory digest, exact byte and file
counts, initial resource limits and consumed allowances. No source content,
personal paths or original conversation text is printed. Nothing is written
to the fixture source tree. The temporary Arena is removed after the run.

Run the command twice on an unchanged commit and machine to compare reports;
the two inventory digests must agree, and the two entire reports should be
identical. The `code_revision` in the report reflects the current Git HEAD,
not a proof of a clean checkout; record any uncommitted changes separately.
For independent comparison, use the same committed code and the same input
bytes. Different private corpora are **not** expected to yield identical
content digests.

To save a report outside the corpus:

```sh
PYTHONPATH=src python3 scripts/reproduce_arena_one.py \
  --report /tmp/cobble-arena-one-report.json
```

Reports are metadata-only but can still reveal corpus size and a digest.
Review before sharing; do not upload private source material.

## Your own corpus

By default, this is a *public fixture* smoke test. To reproduce the same
whole-corpus operation on files you control:

```sh
PYTHONPATH=src python3 scripts/reproduce_arena_one.py \
  --source /path/to/your/local-corpus \
  --memory-bytes 268435456 \
  --archive-reads 100000 \
  --attention-steps 10 \
  --report /tmp/my-arena-reproduction.json
```

The input is a **directory of files**, not a required vendor export schema.
The runner recursively copies everything it contains, with no summarisation
or truncation. It rejects symlinks and refuses to populate if the full input
exceeds the declared limits; it never silently chooses a subset.

The input must be quiescent during the run; this is not an atomic snapshot
of a live changing source. The temporary destination is separate from the
source and is not exposed through an API or sent to an external supplier.

`--report` must point **outside the source corpus**. An existing report
is never overwritten. For source sizes larger than 256 MiB, explicitly raise
the memory budget. These are **raw source-byte limits**, not meaningful
limits on future inference or active derived cognition.

**Private GitHub repositories, personal ChatGPT exports and company data
must not be copied into a public GitHub repository or CI fixture.** The
runner does not parse a native ChatGPT ZIP or import GitHub accounts. See
[GitHub ingestion](github-conversations.md) and [Arena One](arena-one.md)
for the separate acquisition and live-store workflows.

## What counts as a comparable result?

Record at least:

| Quantity | Source |
| --- | --- |
| Code version | `code_revision` / `git rev-parse HEAD` |
| Input identity | `source_inventory_sha256` (hash of sorted file paths, sizes and SHA-256 values) |
| Input scale | `file_count`, `source_bytes` |
| Copy integrity | `byte_identical`, `source_unchanged`, `arena_inventory_sha256` |
| Resource limits | `resource_limits` (five separately named ceilings) |
| Resources spent | `resource_spent` |
| Scope | `report_format`, `arena_format`, experiment description and limitations |

These measurements verify **that the implementation copied this particular
corpus and accounted for the initial operation**. They do not demonstrate
that the data was understood, that an agent developed curiosity, that any
Village Link was correct, or that a persistent identity emerged.

The test corpus is intentionally tiny: it exercises **software reproducibility
only**. Meaningful claims about memory dynamics, model-provider substitution
or emergent behaviour will require real, authorised, independently describable
datasets of appropriate size and experiments with controlled comparisons.

## Portability and automation boundaries

This harness uses the Python standard library and a disposable local
directory. CI runs against **only the committed public fixture**. Native
Windows, network filesystems and concurrent corpus mutation have **not**
been validated as supported targets; Windows users can use WSL.

The connected Puck–McKay tunnel and its bounded diagnostics are useful for
our own laboratory, but **are not installation dependencies**. The private
Puck-GPT publishing workflow is similarly separate. Other researchers can
run this experiment without giving an AI a shell, network access, API key,
write permissions over their original data, or any authority to publish.

For the larger research proposition, see [Cobble's specification](../specification.md).
