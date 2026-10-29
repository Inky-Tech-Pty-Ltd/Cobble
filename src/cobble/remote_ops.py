"""Narrow, local Arena diagnostics for the Cobble MCP interface.

No arbitrary commands, arbitrary paths or source-content export. Executing
the fixed offline test suite requires explicit local operator opt-in.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from cobble.arena import overview

_ARENA_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _arena(name="arena-a"):
    if not isinstance(name, str) or not _ARENA_NAME.fullmatch(name):
        raise ValueError("Arena name must be a simple directory name")
    root = Path.home() / "cobble-arenas"
    path = root / name
    if root.is_symlink() or path.is_symlink():
        raise ValueError("Arena path cannot be a symlink")
    return path


def arena_status(name="arena-a"):
    """Read the existing Arena's population totals and resource budget."""
    report = overview(_arena(name))
    return {"arena": name, "report": report,
            "scope": "local derived Arena metadata; no source text returned"}


def verify_arena(name="arena-a"):
    """Rehash copied Arena files against its saved manifest; return counts only.

    The archive is not changed or contacted. Integrity of the derived copy
    is not evidence that the original historical source was true or complete.
    """
    directory = _arena(name)
    report = overview(directory)
    population = report.get("population")
    if not isinstance(population, dict):
        return {"arena": name, "verified": False, "reason": "Arena not populated"}
    corpus = directory / "corpus"
    if corpus.is_symlink() or not corpus.is_dir():
        raise ValueError("Missing or symlinked Arena corpus")
    manifest_path = corpus / ".arena-manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("Manifest is a symlink")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("format") != report["format"]:
        raise ValueError("Invalid Arena manifest")
    if len(files) != population.get("files"):
        raise ValueError("Manifest file count differs from Arena state")
    total = 0
    seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError("Invalid manifest entry")
        relative = entry.get("path")
        digest = entry.get("sha256")
        size = entry.get("bytes")
        if not isinstance(relative, str) or relative.startswith("/") or "\\" in relative:
            raise ValueError("Unsafe Arena manifest path")
        parts = relative.split("/")
        if any(p in ("", ".", "..") for p in parts) or relative == ".arena-manifest.json":
            raise ValueError("Unsafe Arena manifest component")
        if relative in seen:
            raise ValueError("Duplicate Arena manifest entry")
        seen.add(relative)
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("Invalid file digest")
        if type(size) is not int or size < 0:
            raise ValueError("Invalid file size")
        path = corpus
        for component in parts:
            path = path / component
            if path.is_symlink():
                raise ValueError("Arena file path is a symlink")
        if not path.is_file() or path.stat().st_size != size:
            raise ValueError("Arena file missing or wrong size")
        sha = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(chunk)
        if sha.hexdigest() != digest:
            raise ValueError("Arena file differs from its manifest hash")
        total += size
    if total != population.get("source_bytes"):
        raise ValueError("Population total differs from manifest")
    # Do not silently ignore extra symlinks or non-regular objects.
    encountered = list(corpus.rglob("*"))
    if any(p.is_symlink() for p in encountered):
        raise ValueError("Arena corpus contains an unmanifested symlink")
    actual = {p.relative_to(corpus).as_posix() for p in encountered if p.is_file()}
    if actual != seen | {".arena-manifest.json"}:
        raise ValueError("Unmanifested or missing Arena files")
    return {"arena": name, "verified": True, "files": len(files), "source_bytes": total,
            "scope": "local copied bytes only; does not establish original source truth"}


def run_arena_tests():
    """Run only the reviewed offline Arena unit suite, with a safe environment.

    Disabled by default; McKay's operator must set the local opt-in flag.
    No command string, test path, working directory or environment is supplied
    by the caller. This is *not* a general-purpose remote shell.
    """
    if os.environ.get("COBBLE_MCP_ALLOW_ARENA_TESTS") != "1":
        raise PermissionError("Arena test execution disabled on McKay")
    root = Path(__file__).resolve().parents[2]
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(Path.home()),
        "PYTHONPATH": str(root / "src"),
        "PYTHONUNBUFFERED": "1",
    }
    args = [sys.executable, "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_arena_one.py", "-v"]
    try:
        proc = subprocess.run(args, cwd=root, env=env, text=True,
                              capture_output=True, timeout=45, check=False)
    except subprocess.TimeoutExpired:
        return {"suite": "arena_one", "passed": False, "reason": "45-second timeout"}
    output = (proc.stdout + "\n" + proc.stderr)
    return {
        "suite": "arena_one",
        "passed": proc.returncode == 0,
        "exit_code": proc.returncode,
        "output_tail": output[-8000:],
        "scope": "fixed offline unittest suite; no arbitrary shell command",
    }
