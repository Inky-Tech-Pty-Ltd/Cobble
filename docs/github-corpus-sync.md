# Organisation-wide GitHub corpus sync

`bash scripts/sync_github_corpus.sh` discovers the repositories visible to the
authenticated GitHub CLI in `Inky-Tech-Pty-Ltd`, including newly created and
private repositories that the account can read. For each repository it refreshes
a **dedicated source checkout**, calls Cobble's existing Git archive importer,
then calls the GitHub conversation importer (issues, PRs and Discussions).

From McKay's Ubuntu environment, with GitHub CLI authentication and the Cobble
Python environment available:

```sh
cd ~/Cobble
git pull --ff-only
bash scripts/sync_github_corpus.sh --dry-run
bash scripts/sync_github_corpus.sh
```

The script can be run from any directory. Defaults are:

- Archive: `~/cobble-data/github/` (outside Git).
- Disposable source checkouts: `~/cobble-source-checkouts/` (not the developer's
  own `~/Cobble` or `~/InkyBooks` checkout).
- Organisation: `Inky-Tech-Pty-Ltd`.

Use `--org`, `--store` and `--checkouts` to override these paths or the owner.
`--dry-run` discovers repositories and prints its intended actions without
writing files. Private repositories require the authenticated account to have
read access; the conversation importer also requires authenticated access to
Discussions. Do not pass tokens as command arguments, copy them into scripts,
or store GitHub archive material in the Cobble repository.

On a subsequent run, a dedicated checkout is fetched and fast-forwarded rather
than reset. If it has local edits, diverged commits, or the directory is not a
Git checkout, the script stops instead of overwriting it. This is intentionally
conservative. The Git archive retains prior captured HEAD references; the
conversation importer retains immutable, versioned snapshots. The final count
reports **new conversation-version files**, not messages or threads.

The command fails visibly if repository discovery, clone/fetch, either importer,
or archival checks fail. Already archived snapshots are retained, so a failure
can leave a partially refreshed organisation corpus. Re-running is supported.
This tool is designed for manual use today; it does not install a scheduler,
coordinate simultaneous invocations, or create Cobble memory graphs.

**Completeness limits:** only repositories visible to the authenticated user
are enumerated (up to 1,000 per invocation). The Git importer archives Git
objects and refs observed from the checkout, not Git LFS binaries or submodule
contents; the conversation importer does not download attached binaries or
recover deleted/unavailable messages. API acquisition is not an atomic
organisation-wide snapshot. Source-reported timestamps and authorship are
evidence, not verified identity claims. The archive may contain sensitive
content and Git history may include secrets: keep it private and include it in
an encrypted off-device backup strategy. The script changes local files only;
it never pushes to GitHub.

This is **source acquisition**, deliberately independent of arenas, hypothesis
links, memory addresses, salience and any proposed memory graph architecture.
