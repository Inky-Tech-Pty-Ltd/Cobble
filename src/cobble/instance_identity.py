"""Local instance identity for the explicitly provisioned Candidate 5 pilot.

An ID is a durable local label, not a public key or proof of identity.
A fresh store avoids inheriting any other entity's private memories.
"""
import json
import os
from pathlib import Path
import re
import secrets

PILOT_NAMES = ("Joe", "Puck", "Sankarshan")
ID_PATTERN = re.compile(r"[0-9a-f]{32}\Z")
FILENAME = "cobble-instance.json"


def _root(store):
    path = Path(store).expanduser().absolute()
    if path.is_symlink() or path.resolve() != path:
        raise PermissionError("Instance store must not be redirected")
    if any((p / ".git").exists() for p in (path, *path.parents)):
        raise PermissionError("Instance store must stay outside Git")
    return path


def provision(store, name):
    """Create a new private store, never relabel an existing one."""
    if name not in PILOT_NAMES:
        raise ValueError("Unknown pilot identity")
    root = _root(store)
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    identity = {"instance_id": secrets.token_hex(16), "name": name}
    fd = os.open(root / FILENAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(identity, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return identity


def load(store):
    """Read an existing identity; legacy stores have no instance manifest."""
    root = _root(store)
    path = root / FILENAME
    if path.is_symlink():
        raise PermissionError("Unsafe instance identity")
    if not path.exists():
        return None
    if not path.is_file() or path.stat().st_size > 1024:
        raise ValueError("Invalid instance identity")
    identity = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(identity, dict) or set(identity) != {"instance_id", "name"}
            or identity["name"] not in PILOT_NAMES
            or not isinstance(identity["instance_id"], str)
            or not ID_PATTERN.fullmatch(identity["instance_id"])):
        raise ValueError("Invalid instance identity")
    return identity


def require_index(store, index):
    """A named pilot must not point its search at another entity's index."""
    root = _root(store)
    path = Path(index).expanduser().absolute()
    if path.resolve() != path or not path.is_relative_to(root):
        raise PermissionError("Named instance requires its own local index")
