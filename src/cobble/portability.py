"""Offline round-trip of Cobble's existing GitHub conversation snapshots.

Preservation is not proof of authority, availability or trace equivalence.
"""
import base64
import hashlib
import json
import re
from pathlib import Path

VERSION = re.compile(r"versions/([0-9a-f]{64})\.json\Z")
PART = re.compile(r"[A-Za-z0-9_.-]+\Z")
KINDS = {"issues", "pulls", "discussions"}


def _digest(record):
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _identity(path):
    if not isinstance(path, str) or "\\" in path or path.startswith("/"):
        raise ValueError("Unsafe archive path")
    parts = path.split("/")
    if len(parts) == 6 and parts[4] == "versions" and VERSION.fullmatch("/".join(parts[4:])):
        owner, repo, kind, number = parts[:4]
        file_type = "version"
    elif len(parts) == 5 and parts[4] == "latest.json":
        owner, repo, kind, number = parts[:4]
        file_type = "pointer"
    else:
        raise ValueError("Unexpected archive path")
    if any(not PART.fullmatch(p) or p in (".", "..") for p in (owner, repo, kind, number)):
        raise ValueError("Unsafe archive identity")
    if kind not in KINDS or not number.isascii() or not number.isdecimal() or int(number) < 1:
        raise ValueError("Invalid archive identity")
    return (owner, repo, kind, number), file_type


def _verify(files):
    groups = {}
    for name, data in files.items():
        if not isinstance(data, bytes):
            raise ValueError("Invalid content")
        key, kind = _identity(name)
        entry = groups.setdefault(key, {"versions": set()})
        if kind == "version":
            version = name.rsplit("/", 1)[-1][:-5]
            try:
                record = json.loads(data)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError("Invalid snapshot JSON") from exc
            if _digest(record) != version:
                raise ValueError("Snapshot digest mismatch")
            entry["versions"].add(version)
        else:
            try:
                pointer = json.loads(data)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError("Invalid latest pointer JSON") from exc
            if not isinstance(pointer, dict) or set(pointer) != {"sha256", "version"}:
                raise ValueError("Invalid pointer shape")
            entry["pointer"] = pointer
    if not groups:
        raise ValueError("Empty corpus")
    for entry in groups.values():
        pointer = entry.get("pointer")
        if not pointer or not entry["versions"]:
            raise ValueError("Missing pointer or versions")
        version = pointer.get("version")
        match = VERSION.fullmatch(version) if isinstance(version, str) else None
        if not match or pointer.get("sha256") != match.group(1) or match.group(1) not in entry["versions"]:
            raise ValueError("Unresolvable latest pointer")
    return len(groups)


def _root(store):
    return Path(store).expanduser().resolve() / "github" / "conversations"


def _reject_symlink_components(path, store):
    """Reject archive symlinks at any depth below the canonical store root."""
    current = Path(store).expanduser().resolve()
    for part in path.relative_to(current).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("Symlinks not supported")


def export_corpus(store, output, repositories):
    """Export explicitly selected archives without interpreting their contents."""
    if not repositories:
        raise ValueError("Explicit repository selection required")
    root = _root(store)
    files = {}
    for slug in sorted(set(repositories)):
        parts = slug.split("/") if isinstance(slug, str) else []
        if len(parts) != 2 or any(not PART.fullmatch(p) or p in (".", "..") for p in parts):
            raise ValueError("Invalid repository selector")
        repo_root = root.joinpath(*parts)
        _reject_symlink_components(repo_root, store)
        if not repo_root.is_dir():
            raise ValueError("Repository not ingested: " + slug)
        for path in sorted(repo_root.rglob("*")):
            _reject_symlink_components(path, store)
            if path.is_file():
                files[path.relative_to(root).as_posix()] = path.read_bytes()
    count = _verify(files)
    entries = [{"path": path, "sha256": hashlib.sha256(data).hexdigest(),
                "data_base64": base64.b64encode(data).decode("ascii")}
               for path, data in sorted(files.items())]
    package = {"format": "cobble-github-conversations", "version": 1,
               "repositories": sorted(set(repositories)), "entries": entries}
    dest = Path(output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"conversations": count, "files": len(files)}


def restore_corpus(source, store):
    """Validate entire package before writing. Conflicting paths are rejected."""
    package = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(package, dict) or package.get("format") != "cobble-github-conversations" or package.get("version") != 1:
        raise ValueError("Unsupported package")
    entries = package.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Invalid entries")
    files = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "data_base64"}:
            raise ValueError("Invalid entry")
        path = entry["path"]
        if not isinstance(path, str) or path in files:
            raise ValueError("Duplicate or invalid path")
        try:
            data = base64.b64decode(entry["data_base64"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid encoded content") from exc
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Entry integrity mismatch")
        files[path] = data
    count = _verify(files)
    actual = sorted({"/".join(path.split("/")[:2]) for path in files})
    if package.get("repositories") != actual:
        raise ValueError("Repository manifest mismatch")
    root = _root(store)
    for path, data in files.items():
        dest = root.joinpath(*path.split("/"))
        _reject_symlink_components(dest, store)
        if dest.exists() and (not dest.is_file() or dest.read_bytes() != data):
            raise ValueError("Conflicting destination")
    for path, data in sorted(files.items()):
        dest = root.joinpath(*path.split("/"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            dest.write_bytes(data)
    return {"conversations": count, "files": len(files)}
