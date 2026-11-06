# ChatGPT Privacy Portal export ingestion (experimental)

This is a native Cobble importer for local, private ChatGPT conversation snapshots.
External open-source projects (especially Gusarovv/chatgpt-export-viewer and
temnoon/openai_export_parser) informed format reconnaissance; the importer
uses Python's standard library without copying third-party code.

## Scope and privacy

- Accepts a full nested Privacy Portal ZIP or an extracted conversations ZIP.
- Reads numbered conversations-NNN.json shards and retains the entire raw
  conversation object, including all message mapping nodes, alternate branches,
  titles, context scopes and tool metadata present in the export.
- Does **not** upload, publish, call a model, alter the original ZIP or modify
  an existing Arena. Keep the store outside Git and inside encrypted backups.
- Attachment binaries (.dat and other assets) remain in the original, protected
  ZIP: this first implementation preserves message references but does **not**
  yet extract, index or make binaries navigable. It does not recover messages
  or files omitted by OpenAI's export.
- Project display names may not be available in the export; raw identifiers
  are kept intact rather than inventing names.

## Run on McKay

From ~/Cobble, after checking out the feature branch:

    PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_openai_export.py' -v

Compare against the already-preserved old and new ZIPs without writing:

    PYTHONPATH=src python3 scripts/import_openai_export.py --dry-run \
      ~/cobble-data/openai-exports/2026-10-31/conversations.zip

Run the real imports **oldest first**:

    PYTHONPATH=src python3 scripts/import_openai_export.py \
      ~/cobble-data/openai-exports/2026-10-31/conversations.zip \
      ~/cobble-data/openai-exports/2026-11-06/conversations.zip

Expected (from the manually inspected November 2026 exports): October
contains 716 unique conversation IDs. November has 761 IDs: 45 first seen
in November, four revised October records, 712 unchanged, and zero October
IDs missing. These are **local acceptance expectations**, not committed test
fixtures or an assertion that the importer has already passed on McKay.

## Storage and version semantics

Under ~/cobble-data/openai/:

- conversations/CONVERSATION-ID/versions/SHA256.json: immutable, canonical
  full-record version. Different exports of the same conversation do not
  create redundant versions when the canonical record is unchanged.
- conversations/CONVERSATION-ID/latest.json: latest known record pointer,
  guarded by the source ZIP timestamp so backfilling an older export doesn't
  normally roll back a newer observation.
- imports/ZIP-SHA256.json: snapshot manifest containing the ZIP fingerprint
  and complete ID-to-record-digest membership for that export.

ZIP member timestamps are used only as archive provenance/order hints, not
as authoritative message timestamps. Any collision or unexpected schema
fails explicitly. Importing a later snapshot never deletes older records.
The importer validates all numbered conversation shards before writing,
though an interrupted write can leave complete versions without the final
import manifest; rerunning the import is safe.

## Next increments

1. Run local acceptance against the two preserved exports and inspect the
   counts, including the four known revised conversations.
2. Resolve and preserve attachment binaries by stable reference with content
   hashes, then add a local, permission-aware conversation navigation API.
3. Only after verification, construct a **fresh** Arena from the reconciled
   corpus. Do not rewrite Arena A in place.
