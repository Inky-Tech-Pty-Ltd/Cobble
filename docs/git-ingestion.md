# GitHub repository memory: first ingestion experiment

Cobble archives **a local Git clone** as a standalone bare Git repository in
`~/cobble-data/github/repositories/`, keeping the Git object database,
commits, trees, blobs and references. It does not rely on GitHub's API,
does not modify the source checkout and does not require network access.
Fetching remote GitHub changes **into your source checkout** is a separate action.

From `~/Cobble` with the virtual environment activated:

```bash
PYTHONPATH=src python scripts/import_git.py Inky-Tech-Pty-Ltd/Cobble ~/Cobble
```

Repeat to capture changes since the last import. Previously observed HEADs
are pinned under `refs/cobble/snapshots/<sha>` to preserve reachable objects,
even if branches later move. The archive is outside the Cobble Git checkout.

To create a trace for a *selected passage*, use the **full SHA** printed by
the importer:

```bash
PYTHONPATH=src python scripts/capture_git_file.py \
  Inky-Tech-Pty-Ltd/Cobble FULL_COMMIT_SHA README.md \
  'Memory is the masterpiece.'
```

This preserves the selected UTF-8 file under `~/cobble-data/copies/` and
mints a Cobble trace with a commit-pinned GitHub URI. Resolve the retained
text without network access:

```bash
PYTHONPATH=src python scripts/resolve_trace.py \
  'https://cobble.link/t/TRACE_UUID'
```

Files and commits are not automatically declared equivalent memes; Village
Links remain deliberate assertions. Nothing is publicly published.

**Limitations:** Git repositories only. GitHub Issues, PR conversations,
reviews, Discussions, LFS blobs, submodule content and GitHub-specific
metadata are not included. Shallow/partial clones produce shallow/partial
archives. No simultaneous-writer coordination or automatic backup is provided.
Git history may contain secrets; keep the Cobble data store private and
encrypted in its off-device backup.
