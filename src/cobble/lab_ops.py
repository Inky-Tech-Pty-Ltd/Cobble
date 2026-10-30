"""Narrow laboratory operations with independent local operator switches.

Fixed tests run from Cobble's checkout; the journal is a private append-only
operator record outside the source archive and experimental Arena.
Neither grants a general shell or general filesystem write capability.
"""
from datetime import datetime, timezone
import json
import os
import stat
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


def _journal_dir():
    base = Path.home() / "cobble-lab"
    if base.is_symlink():
        raise ValueError("Lab journal directory must not be a symlink")
    return base


def _open_journal_dir(create=False):
    base = _journal_dir()
    if create:
        base.mkdir(mode=0o700, parents=True, exist_ok=True)
    return os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def _open_journal_file(dir_fd, writing=False):
    flags = os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    if writing:
        flags |= os.O_CREAT | os.O_APPEND | os.O_WRONLY
    else:
        flags |= os.O_RDONLY
    fd = os.open("journal.jsonl", flags, 0o600, dir_fd=dir_fd)
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_JOURNAL_BYTES:
        os.close(fd)
        raise ValueError("Lab journal is not a regular file or has reached its size limit")
    return fd


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
    data = (json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\\n").encode("utf-8")
    if len(data) > 20000:
        raise ValueError("Lab note exceeds byte limit")
    directory_fd = _open_journal_dir(create=True)
    try:
        fd = _open_journal_file(directory_fd, writing=True)
        try:
            if os.fstat(fd).st_size + len(data) > MAX_JOURNAL_BYTES:
                raise ValueError("Journal has reached its size limit")
            # Exactly one append in ordinary use; refuse a partial write.
            written = os.write(fd, data)
            if written != len(data):
                raise OSError("Partial journal append")
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        os.close(directory_fd)
    return {"recorded": True, "kind": kind, "arena": arena, "at": entry["at"],
            "scope": "append-only lab note; does not affect juvenile resources"}


def recent_lab_notes(limit: int = 10):
    """Read up to 20 recent journal notes; no general filesystem access."""
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("limit must be between 1 and 20")
    if not _journal_dir().exists():
        return {"entries": [], "scope": "local laboratory journal"}
    directory_fd = _open_journal_dir()
    try:
        try:
            fd = _open_journal_file(directory_fd)
        except FileNotFoundError:
            return {"entries": [], "scope": "local laboratory journal"}
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            lines = stream.readlines()
    finally:
        os.close(directory_fd)
    notes = [json.loads(line) for line in lines[-limit:]]
    return {"entries": notes, "scope": "local laboratory journal; human/operator notes, not automatically Snug's experiences"}
