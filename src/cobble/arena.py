"""Arena One: preserve a full offline corpus inside a resource-accounted arena.

This is corpus *presence*, not semantic digestion. The protected source store
is never edited. No networking, model invocation or Village Link minting.
"""
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "arena-one-0.2"
FIELDS = ("memory_bytes", "model_tokens", "attention_steps", "archive_reads", "external_ops")


class BudgetExceeded(ValueError):
    """Requested corpus cannot fit within a declared Arena allowance."""


def _path(value):
    return Path(value).expanduser().resolve()


def _locations(archive, arena):
    archive, arena = _path(archive), _path(arena)
    if (archive == arena or archive.is_relative_to(arena)
            or arena.is_relative_to(archive)):
        raise ValueError("Arena and original source archive must be separate")
    return archive, arena


def _state_path(arena):
    path = _path(arena) / "state.json"
    if path.is_symlink():
        raise ValueError("Arena state must not be a symlink")
    return path


def _write_state(arena, state):
    path = _state_path(arena)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            json.dump(state, out, ensure_ascii=False, indent=2, sort_keys=True)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load(arena):
    state = json.loads(_state_path(arena).read_text(encoding="utf-8"))
    if state.get("format") != FORMAT:
        raise ValueError("Unknown Arena state format")
    if set(state.get("limits", {})) != set(FIELDS) or set(state.get("spent", {})) != set(FIELDS):
        raise ValueError("Incomplete Arena budget")
    for field in FIELDS:
        limit, spent = state["limits"][field], state["spent"][field]
        if type(limit) is not int or type(spent) is not int or not 0 <= spent <= limit:
            raise ValueError("Invalid Arena resource counter: " + field)
    if "population" not in state or not isinstance(state.get("archive"), str):
        raise ValueError("Incomplete Arena state")
    return state


def init_arena(archive, arena, limits):
    """Create an empty isolated Arena with five explicit allowances."""
    if set(limits) != set(FIELDS):
        raise ValueError("Exactly five allowances are required")
    if any(type(value) is not int or value < 0 for value in limits.values()):
        raise ValueError("All resource limits must be nonnegative integers")
    if not all(limits[field] > 0 for field in ("memory_bytes", "attention_steps", "archive_reads")):
        raise ValueError("Memory, attention and source-read limits must be positive")
    archive, arena = _locations(archive, arena)
    if not archive.is_dir():
        raise ValueError("Source archive directory not found")
    if arena.exists() and any(arena.iterdir()):
        raise FileExistsError("Arena is not empty: refusing to overwrite")
    arena.mkdir(parents=True, exist_ok=True)
    state = {
        "format": FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "archive": str(archive),
        "limits": dict(limits),
        "spent": {field: 0 for field in FIELDS},
        "population": None,
        "mode": "offline; no provider or external calls",
    }
    _write_state(arena, state)
    return overview(arena)


def _inventory(archive):
    """Inventory *all* archived files. Reject symlinks; never follow them."""
    listing = []
    for path in sorted(archive.rglob("*")):
        if path.is_symlink():
            raise ValueError("Source archive contains a symlink: " + str(path))
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Source archive contains a non-regular file: " + str(path))
        relative = path.relative_to(archive)
        listing.append((path, relative, path.stat().st_size, path.stat().st_mtime_ns))
    if not listing:
        raise ValueError("Source archive contains no files")
    return listing


def populate_corpus(arena):
    """Copy the *entire* preserved corpus to the Arena with no truncation.

    Charges one attention step, one read per source file and the raw bytes of
    each copied file. The staged copy is integrity-checked before exposure.
    Refuses re-population; run experiments in separate Arena directories.
    """
    state = _load(arena)
    archive, arena = _locations(state["archive"], arena)
    corpus = arena / "corpus"
    if state["population"] is not None or corpus.exists():
        raise FileExistsError("Arena already populated; refusing to overwrite")
    if not archive.is_dir():
        raise FileNotFoundError("Source archive no longer exists")
    listing = _inventory(archive)
    total = sum(item[2] for item in listing)
    number = len(listing)
    requested = {"memory_bytes": total, "archive_reads": number, "attention_steps": 1}
    for field, amount in requested.items():
        remaining = state["limits"][field] - state["spent"][field]
        if amount > remaining:
            raise BudgetExceeded(f"{field}: need {amount}; remaining {remaining}")

    # Stage in the *derived* arena, not in the protected archive.
    stage = Path(tempfile.mkdtemp(prefix=".corpus-stage-", dir=arena))
    manifest = []
    try:
        for source, relative, size, mtime in listing:
            # A concurrently modified archive is outside this experiment's
            # contract. Detect simple changes rather than silently accepting.
            if source.is_symlink() or not source.is_file():
                raise ValueError("Source changed during copy: " + str(source))
            before = source.stat()
            if before.st_size != size or before.st_mtime_ns != mtime:
                raise ValueError("Source changed after inventory: " + str(source))
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            written = 0
            with source.open("rb") as original, destination.open("xb") as copied:
                while True:
                    chunk = original.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    copied.write(chunk)
                    written += len(chunk)
            after = source.stat()
            if (written != size or after.st_size != size or
                    after.st_mtime_ns != mtime):
                raise ValueError("Source changed during copy: " + str(source))
            if hashlib.sha256(destination.read_bytes()).hexdigest() != digest.hexdigest():
                raise ValueError("Arena copy integrity mismatch: " + str(relative))
            manifest.append({"path": relative.as_posix(), "bytes": written,
                             "sha256": digest.hexdigest()})

        with (stage / ".arena-manifest.json").open("x", encoding="utf-8") as out:
            json.dump({"format": FORMAT, "files": manifest}, out,
                      indent=2, sort_keys=True)
            out.write("\n")
        os.replace(stage, corpus)
        state["population"] = {"files": number, "source_bytes": total,
                               "manifest": "corpus/.arena-manifest.json",
                               "scope": "complete local archive at this observation, not historical completeness"}
        for field, amount in requested.items():
            state["spent"][field] += amount
        _write_state(arena, state)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return overview(arena)


def overview(arena):
    """Return inventory totals and budgets without exposing private content."""
    state = _load(arena)
    return {
        "format": state["format"],
        "archive": state["archive"],
        "population": state["population"],
        "budget": {
            field: {"limit": state["limits"][field], "spent": state["spent"][field],
                    "remaining": state["limits"][field] - state["spent"][field]}
            for field in FIELDS
        },
        "mode": state["mode"],
        "note": "Corpus copied intact; not yet semantically interpreted or linked.",
    }
