# GitHub conversation ingestion (prototype)

Capture the *conversations*, not just Git commits: Issues, pull requests,
general comments, reviews, inline review comments, timeline events and
Discussions (including discussion comment replies).

From McKay, with the Python environment activated:

```bash
PYTHONPATH=src python scripts/import_github_conversations.py \
  Inky-Tech-Pty-Ltd/Cobble
```

The importer uses read-only GitHub APIs. Set `GH_TOKEN` or `GITHUB_TOKEN`,
or authenticate the GitHub CLI with `gh auth login`, to access Discussions
through GraphQL. Never paste a token in a chat or put it in the repository.
For a public repository with no authentication, it is possible to archive
REST conversations only, with an **explicitly incomplete** result:

```bash
PYTHONPATH=src python scripts/import_github_conversations.py \
  Inky-Tech-Pty-Ltd/Cobble --skip-discussions
```

Records are saved under `~/cobble-data/github/conversations/OWNER/REPO/`
in `issues/`, `pulls/`, and `discussions/`. Each numbered thread gets
an immutable SHA-256-addressed JSON version and a `latest.json` pointer.
Unchanged re-imports do not duplicate records; changed conversations retain
earlier snapshots. All paginated items are retrieved before writing each
thread, so a request error doesn't overwrite that thread with a partial
snapshot. Import errors stop execution, and previous saved records remain.

This is **preservation, not interpretation**: GitHub item URLs and identifiers,
original text, authorship and timestamps are preserved as returned by GitHub.
No Village Links are automatically asserted.

Current limitations: no GitHub-hosted attachment binaries, reaction-specific
feeds, deleted comments not present in the API, or commit-linked PR review
thread resolution metadata beyond REST fields. A snapshot of a repository
is **not an atomic, point-in-time API view** if people edit threads during
the import. A repository-level import that errors partway through can have
a mixture of earlier and newer complete per-thread snapshots. Large repo
imports can hit rate limits; token permissions must allow reading the
requested resources. Keep local archives private; include them in the
encrypted backup cycle.
