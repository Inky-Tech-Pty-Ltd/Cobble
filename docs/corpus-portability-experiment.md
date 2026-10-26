# GitHub conversation corpus portability experiment

**Status: bounded experimental implementation.** Related issue: #12.

This test concerns the existing `main` GitHub conversation archive. It is not a graph portability test, a Village Link equivalence check, or evidence of persistent agent identity. Original snapshots, including previously retained revisions and `latest.json` pointers, are preserved without interpretation.

## Reproduction

After authenticating with GitHub read permissions, from the repository root:

```sh
PYTHONPATH=src python scripts/import_github_conversations.py Inky-Tech-Pty-Ltd/VillageLink
PYTHONPATH=src python scripts/import_github_conversations.py Inky-Tech-Pty-Ltd/Cobble

PYTHONPATH=src python scripts/portable_github_corpus.py export \
  --store ~/cobble-data --repo Inky-Tech-Pty-Ltd/VillageLink \
  --repo Inky-Tech-Pty-Ltd/Cobble --output /private/path/corpus.json

PYTHONPATH=src python scripts/portable_github_corpus.py restore \
  --input /private/path/corpus.json --store /private/path/clean-store

PYTHONPATH=src python -m unittest discover -s tests -v
```

The existing importer requires an authenticated GraphQL connection to include Discussions; `--skip-discussions` produces intentionally incomplete acquisition. Do not characterize an incomplete import as a complete conversation record.

The output package contains original text and provenance fields. **Treat it as potentially sensitive even when sourced from public GitHub repositories.** Keep the local store and exported packages outside Git and use appropriate access controls. Do not publish the resulting corpus as a repository fixture.

## Evidence and limitations

A successful round-trip establishes retention of local snapshot bytes and latest pointers without consulting GitHub during restoration. Each content-addressed record's canonical JSON digest and each byte-level entry digest are checked before writing. Missing snapshots, invalid paths, duplicate entries, and conflicting destinations cause explicit errors. Restore preflight checks are not an atomic filesystem transaction; interruption or disk failure can leave a partial destination.

GitHub API acquisitions are not a single atomic source snapshot. API response fields may omit deleted material, binary attachments, or inaccessible items. A restored local archive does not prove that a source is currently accessible, that an assertion is true, or that a publisher has authority. Preserved authorship and timestamps are source-reported claims.

Real VillageLink/Cobble acquisition and its actual counts and artifact hashes must be recorded when observed, not inferred from fixture tests. Graph membership, private ChatGPT history, and agent identity continuity are deliberately outside this experiment.
