"""Local, lossless conversation-record snapshots from OpenAI Privacy Portal exports.

The original ZIP remains the source of truth. Nothing is sent over the network.
Do not put the derived store in a Git repository or a publicly served directory.
"""
from contextlib import contextmanager
from datetime import datetime
from hashlib import sha256
from io import TextIOWrapper
from pathlib import Path
from tempfile import NamedTemporaryFile, SpooledTemporaryFile
from zipfile import ZipFile
import json
import os
import re
import shutil


SHARD = re.compile(r"(^|/)conversations-[0-9]+\.json$")
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
MAX_SHARD_BYTES = 512 * 1024 * 1024


def _shards(archive):
    return sorted(name for name in archive.namelist() if SHARD.search(name))


@contextmanager
def _conversation_archive(path):
    """Accept an inner conversation ZIP or a Privacy Portal outer ZIP."""
    with ZipFile(path) as outer:
        if _shards(outer):
            yield outer
            return

        inner = [
            name for name in outer.namelist()
            if name.lower().endswith(".zip") and "chatgpt" in name.lower()
        ]
        if len(inner) != 1:
            raise ValueError("Expected exactly one nested ChatGPT ZIP")
        # ZipFile needs random access. Spool rather than unpacking untrusted
        # archive paths or retaining a potentially huge inner ZIP in RAM.
        with SpooledTemporaryFile(max_size=32 * 1024 * 1024) as spool:
            with outer.open(inner[0]) as source:
                shutil.copyfileobj(source, spool, length=1024 * 1024)
            spool.seek(0)
            with ZipFile(spool) as nested:
                yield nested


def read_conversations(path):
    """Return (records_by_id, archive_timestamp); preserve complete mappings.

    Never infer message order by flattening 'mapping': edited/alternate
    branches and tool-step metadata are part of the preserved record.
    ZIP timestamps are provenance hints, not message creation timestamps.
    """
    records = {}
    with _conversation_archive(path) as archive:
        names = _shards(archive)
        if not names:
            raise ValueError("No numbered conversation JSON shards found")
        for name in names:
            info = archive.getinfo(name)
            if info.file_size > MAX_SHARD_BYTES:
                raise ValueError("Conversation shard exceeds supported size")
            with archive.open(name) as stream:
                data = json.load(TextIOWrapper(stream, encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Expected a list of conversations in " + name)
            for record in data:
                if not isinstance(record, dict):
                    raise ValueError("Conversation entry is not an object")
                cid = record.get("conversation_id") or record.get("id")
                if not isinstance(cid, str) or not SAFE_ID.fullmatch(cid):
                    raise ValueError("Invalid or unsafe conversation ID")
                if cid in records:
                    raise ValueError("Duplicate conversation ID across shards")
                records[cid] = record
        timestamp = max(
            datetime(*info.date_time).isoformat(timespec="seconds")
            for info in archive.infolist()
        )
    return records, timestamp


def _encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with NamedTemporaryFile(mode="wb", dir=path.parent,
                            prefix=".import-", delete=False) as temp:
        name = temp.name
        try:
            temp.write(content)
            temp.flush()
            os.fsync(temp.fileno())
        except BaseException:
            Path(name).unlink(missing_ok=True)
            raise
    try:
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def _file_digest(path):
    digest = sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_export(source, store, dry_run=False):
    """Import a complete snapshot; retain immutable conversation revisions.

    A newer archive may omit a conversation: that never deletes earlier data.
    Repeated imports of the same ZIP are no-ops. No Arena is changed.
    All JSON is validated before any store write.
    """
    source_path = Path(source).expanduser()
    if source_path.is_symlink():
        raise ValueError("Refusing to follow a source ZIP symlink")
    source = source_path.resolve(strict=True)
    if not source.is_file():
        raise ValueError("Source must be an ordinary ZIP file")
    store = Path(store).expanduser().resolve()
    root = store / "openai"
    source_sha = _file_digest(source)
    manifest_path = root / "imports" / (source_sha + ".json")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {"already_imported": True, "conversations": manifest["conversations"],
                "created": 0, "revised": 0, "unchanged": 0, "dry_run": dry_run}

    records, source_timestamp = read_conversations(source)
    operations = []
    for cid, record in records.items():
        encoded = _encoded(record)
        digest = sha256(encoded).hexdigest()
        base = root / "conversations" / cid
        pointer = base / "latest.json"
        prior = json.loads(pointer.read_text(encoding="utf-8")) if pointer.exists() else None
        previous_digest = prior.get("sha256") if prior else None
        kind = ("created" if prior is None else
                "unchanged" if digest == previous_digest else "revised")
        operations.append((cid, base, encoded, digest, prior, kind))

    counts = {name: sum(op[5] == name for op in operations)
              for name in ("created", "revised", "unchanged")}
    summary = {"already_imported": False, "conversations": len(records),
               **counts, "dry_run": dry_run}
    if dry_run:
        return summary

    entries = {}
    for cid, base, encoded, digest, prior, kind in operations:
        version = base / "versions" / (digest + ".json")
        if version.exists():
            if version.read_bytes() != encoded:
                raise ValueError("Stored conversation digest collision or corruption")
        else:
            _atomic_write(version, encoded)
        entries[cid] = digest

        # An older export imported late must not roll back the latest pointer.
        # The original versions remain available either way.
        previous_timestamp = prior.get("source_timestamp", "") if prior else ""
        if prior is None or source_timestamp >= previous_timestamp:
            pointer = {"sha256": digest, "version": "versions/" + digest + ".json",
                       "source_export": source_sha,
                       "source_timestamp": source_timestamp}
            _atomic_write(base / "latest.json", _encoded(pointer))

    manifest = {"format": "openai-export-snapshot-1",
                "archive_sha256": source_sha,
                "archive_name": source.name,
                "source_timestamp": source_timestamp,
                "conversations": len(records),
                "record_sha256": entries}
    _atomic_write(manifest_path, _encoded(manifest))
    return summary
