"""Narrow laboratory operations with independent local operator switches.

Fixed tests run from Cobble's checkout; the journal is a private append-only
operator record outside the source archive and experimental Arena.
Neither grants a general shell or general filesystem write capability.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

SUITES = {
    "arena": "test_arena_*.py",
    "remote": "test_remote_ops.py",
    "console": "test_snug_console.py",
    "lab": "test_lab_*.py",
}
NOTE_KINDS = frozenset({"observation", "hypothesis", "decision", "result", "question"})
MAX_NOTE_CHARS = 4000
MAX_JOURNAL_BYTES = 5_000_000


def run_lab_suite(suite: str):
    """Run only one reviewed offline suite from this checkout, with no secrets."""
    if os.environ.get("COBBLE_MCP_ALLOW_LAB_TESTS") != "1":
        raise PermissionError("Fixed laboratory tests are disabled on McKay")
    if not isinstance(suite, str) or suite not in SUITES:
        raise ValueError("Unknown lab suite")
    root = Path(__file__).resolve().parents[2]
    args = [sys.executable, "-m", "unittest", "discover", "-s", "tests",
            "-p", SUITES[suite], "-v"]
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(Path.home()),
        "PYTHONPATH": str(root / "src"),
        "PYTHONUNBUFFERED": "1",
    }
    try:
        result = subprocess.run(args, cwd=root, env=env, text=True,
                                capture_output=True, timeout=75, check=False)
    except subprocess.TimeoutExpired:
        return {"suite": suite, "passed": False, "reason": "75-second timeout"}
    output = (result.stdout + "\n" + result.stderr)[-6000:]
    return {"suite": suite, "passed": result.returncode == 0,
            "exit_code": result.returncode, "output_tail": output,
            "scope": "fixed offline tests; not a generic command runner"}


def _journal_file():
    base = Path.home() / "cobble-lab"
    if base.is_symlink():
        raise ValueError("Lab journal directory must not be a symlink")
    return base / "journal.jsonl"


def _check_journal_file(path):
    if path.is_symlink():
        raise ValueError("Lab journal must not be a symlink")
    if path.exists() and (not path.is_file() or path.stat().st_size > MAX_JOURNAL_BYTES):
        raise ValueError("Lab journal is not a regular file or has reached its size limit")


def add_lab_note(kind: str, text: str, arena: str = "arena-a"):
    """Append a dated note to the local lab journal, never to source or Arena."""
    if os.environ.get("COBBLE_MCP_ALLOW_LAB_NOTES") != "1":
        raise PermissionError("Lab journal writing is disabled on McKay")
    if not isinstance(kind, str) or kind not in NOTE_KINDS:
        raise ValueError("Unknown lab note kind")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_NOTE_CHARS:
        raise ValueError("Lab note text must be 1–4000 characters")
    from cobble.remote_ops import _arena  # same validated name as diagnostics
    _arena(arena)
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "arena": arena, "kind": kind, "text": text.strip(),
        "authorship": "Puck (laboratory worker via scoped MCP tool)",
    }
    path = _journal_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _check_journal_file(path)
    data = (json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    if len(data) > 20000:
        raise ValueError("Lab note exceeds byte limit")
    flags = os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        if not os.path.isfile(path) or os.fstat(fd).st_size + len(data) > MAX_JOURNAL_BYTES:
            raise ValueError("Journal size or file type invalid")
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    return {"recorded": True, "kind": kind, "arena": arena, "at": entry["at"],
            "scope": "append-only lab note; does not affect juvenile resources"}


def recent_lab_notes(limit: int = 10):
    """Read up to 20 recent journal notes; no general filesystem access."""
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    path = _journal_file()
    _check_journal_file(path)
    if not path.exists():
        return {"entries": [], "scope": "local laboratory journal"}
    with path.open("r", encoding="utf-8") as stream:
        lines = stream.readlines()
    notes = [json.loads(line) for line in lines[-limit:]]
    return {"entries": notes, "scope": "local laboratory journal; human/operator notes, not automatically Snug's experiences"}
