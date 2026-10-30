# Cobble worker tools on McKay

**Status:** Experimental, 30 October 2026. This is tooling for authorised
laboratory workers, **not** a new capability or free resource allowance for
Snug's juvenile learner.

The [proposed privacy ADR](adr/002-memory-native-membrane-and-social-economy.md)
distinguishes researchers working inside the laboratory from outsiders and
from Snug's own conversational membrane. Puck is a lab worker and is
authorised by the operator to inspect Snug's inherited corpus. This does
not require creating an externally dereferenceable URI for every memory.

## Additional MCP tools

Existing `arena_status`, `verify_arena`, `arena_catalogue`, and
`arena_list_sources` remain available. New tools:

| Name | Operation | Local switch |
| --- | --- | --- |
| `arena_read_source(name, path, offset, max_bytes)` | Read up to **12,000 bytes** of a copied Arena text file from its verified SHA-256 manifest, with byte-offset pagination. Does not read the protected source archive or accept absolute paths. | `COBBLE_MCP_ALLOW_SOURCE_READS=1` |
| `run_lab_suite(suite)` | Run one fixed offline test group: `arena`, `remote`, `console` or `lab`; 75-second limit, no caller-supplied command. | `COBBLE_MCP_ALLOW_LAB_TESTS=1` |
| `lab_add_note(kind, text, arena)` | Append a dated Puck-attributed laboratory note (max 4,000 characters). Allowed kinds: observation, hypothesis, decision, result, question. | `COBBLE_MCP_ALLOW_LAB_NOTES=1` |
| `lab_recent_notes(limit)` | Retrieve the 1–20 most recent laboratory notes. | None |

The private journal is `~/cobble-lab/journal.jsonl`, independent from
`~/cobble-data/`, the derived `~/cobble-arenas/` tree, and Git.
These notes are **operator records**, not automatically changes to
Snug's history, biography, value function or resource ledger. A future
experiment can decide which observations become experiences.

**Scope of source reads:** the user has expressly authorised Puck to
inspect inherited sources as a laboratory worker. Filenames are obtained
using `arena_list_sources`; `arena_read_source` can read the matching
**copied** text, including text with mentions of other people. It checks
the whole file digest before returning each page. Binary Git objects
and malformed text are not returned by this endpoint; specialised,
bounded interpreters for Git repositories may be developed later.
The underlying complete archive is not truncated.

**Privacy and provider boundary:** when Puck retrieves source text via
the Cobble plugin, that text is transmitted to the ChatGPT/OpenAI service
to form the tool response. It is **not** public GitHub publication or
a general outside-user API, but it is not computation exclusively
within McKay either. A later Claude or Kimi hemisphere is likewise a
distinct external provider and will require its own explicit operator
approval and usage accounting.

## One-time installation after reviewed publication

On McKay, in a fresh terminal after any old foreground tunnel has
been stopped with Ctrl+C:

```sh
cd ~/Cobble
git status -sb
git switch main
git pull --ff-only
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_lab_*.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_remote_ops.py' -v
```

You do **not** need to reinstall the tunnel or create a second ChatGPT
plugin. The existing profile is `cobble-memory`, and
`scripts/mcp_server.py` gains the four reviewed tool names.

If the tunnel's `CONTROL_PLANE_API_KEY` is **already securely loaded**
into the terminal, use one of the following **fixed** launch modes:

```sh
# Read and inspect source content, but do not allow test runs or journal writes:
bash scripts/lab_tunnel.sh observe

# Allow approved test suites and append-only notes as well as source inspection:
bash scripts/lab_tunnel.sh operate
```

The wrapper does not ask for, display, log or store credentials. If a
credential is not loaded, it stops and asks you to use the **existing
secure credential-loading workflow** rather than pasting keys into chat.
It sets explicit environment flags inherited by the MCP subprocess and
starts the existing outbound tunnel in the foreground. Stop with Ctrl+C.
A restart is required to change the mode; changing the mode in a
different terminal does not alter an already-running process.

Refresh tools for the Cobble plugin in ChatGPT after the restart. A
fresh chat may be required for newly registered tools to appear.

The helper must be invoked as `bash scripts/lab_tunnel.sh` because
files created through GitHub's contents API need not have an executable
bit.

## Proposed working practice

Puck performs approved metadata and source inspections, runs the
reviewed tests, and writes short, attributed notes to the lab journal.
The human retains control of experiment objectives, access to the
laboratory, substantial resource allocations, publication and external
model-provider use.

This first slice intentionally does **not** remotely pull Git updates,
edit source code on McKay, write inside the Arena, run arbitrary Python
or shell, import new real-world records, enable autonomous crawling,
delete anything or contact an LLM. Puck writes code to a review branch
in GitHub; an authorised human publishes through Puck's existing
express workflow, then McKay's operator runs `git pull --ff-only`.
This keeps deployment and code-execution authority auditable while
removing routine output copy-paste.

The test runner executes **reviewed repository Python code**. It is
not an OS sandbox, even with no API keys forwarded. Keep the switch
disabled until the code has been reviewed and published.

## Independently check the tool boundary

```sh
PYTHONPATH=src python3 -m unittest discover -s tests \
  -p 'test_lab_*.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests \
  -p 'test_remote_ops.py' -v
```

These synthetic offline tests cover path confinement, symlink
rejection, SHA-256 verification, Unicode paging, read-only state,
the local operation switches, append-only note records and fixed,
secret-free test invocation.

There is no promise of operating-system containment against a
compromised process. Treat the MCP profile as a privileged laboratory
interface available only to authorised workspace principals.
