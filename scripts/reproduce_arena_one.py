"""Reproduce the offline Arena One corpus-copy experiment.

Runs against the repository's public synthetic fixture by default. Private
corpora are accepted by explicit opt-in; only non-content summary metrics are
reported. No network, model calls, keys, or machine-specific paths required.
"""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from cobble.arena import FORMAT, init_arena, populate_corpus

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "arena_one_public"
REPORT_FORMAT = "cobble-arena-reproduction-0.1"


def _inventory(root, *, copied=False):
    """Inventory content only, sorted by relative pathname, without symlinks."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Corpus root must be a normal directory")
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("A corpus symlink is not an allowed source")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("A corpus entry is not a regular file")
        relative = path.relative_to(root).as_posix()
        if copied and relative == ".arena-manifest.json":
            continue
        size = 0
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                digest.update(chunk)
        entries.append({"path": relative, "bytes": size, "sha256": digest.hexdigest()})
    if not entries:
        raise ValueError("Source corpus is empty")
    return entries


def _digest(entries):
    data = json.dumps(entries, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _git_revision():
    try:
        result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"],
                                cwd=ROOT, capture_output=True, text=True,
                                check=True, timeout=5)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def reproduce(source=FIXTURE, *, memory_bytes=268435456, archive_reads=100000,
              attention_steps=10):
    """Run in a disposable directory; produce a content-free, stable report."""
    source = Path(source).expanduser().resolve()
    before = _inventory(source)
    expected_bytes = sum(entry["bytes"] for entry in before)
    limits = {
        "memory_bytes": memory_bytes, "model_tokens": 0,
        "attention_steps": attention_steps, "archive_reads": archive_reads,
        "external_ops": 0,
    }
    with tempfile.TemporaryDirectory(prefix="cobble-reproduction-") as root:
        arena = Path(root) / "arena"
        init_arena(source, arena, limits)
        outcome = populate_corpus(arena)
        copied = _inventory(arena / "corpus", copied=True)
        after = _inventory(source)
    if before != after:
        raise ValueError("Source corpus changed while reproducing")
    if before != copied:
        raise ValueError("Arena does not match original corpus bytes")
    if outcome["population"]["files"] != len(before):
        raise ValueError("Arena counted the wrong number of files")
    if outcome["population"]["source_bytes"] != expected_bytes:
        raise ValueError("Arena counted the wrong number of bytes")
    spent = {name: value["spent"] for name, value in outcome["budget"].items()}
    if spent != {
        "memory_bytes": expected_bytes, "model_tokens": 0,
        "attention_steps": 1, "archive_reads": len(before), "external_ops": 0,
    }:
        raise ValueError("Arena budget accounting failed")
    digest = _digest(before)
    return {
        "report_format": REPORT_FORMAT,
        "arena_format": FORMAT,
        "code_revision": _git_revision(),
        "result": "passed",
        "source": "public-synthetic-fixture" if source == FIXTURE.resolve()
                  else "user-selected-local-corpus",
        "file_count": len(before),
        "source_bytes": expected_bytes,
        "source_inventory_sha256": digest,
        "arena_inventory_sha256": _digest(copied),
        "byte_identical": True,
        "source_unchanged": True,
        "resource_limits": limits,
        "resource_spent": spent,
        "network_model_and_external_operations": 0,
        "interpretation": "Copies validated; no model learning or emergent behavior tested",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=FIXTURE,
                        help="Full corpus directory; defaults to public synthetic fixture")
    parser.add_argument("--memory-bytes", type=int, default=268435456)
    parser.add_argument("--archive-reads", type=int, default=100000)
    parser.add_argument("--attention-steps", type=int, default=10)
    parser.add_argument("--report", type=Path,
                        help="Optional JSON output file; must not be inside source tree")
    args = parser.parse_args()
    if args.report is not None:
        source = args.source.expanduser().resolve()
        report_path = args.report.expanduser().resolve()
        if report_path.is_relative_to(source):
            parser.error("Report destination must be outside the source corpus")
        if report_path.exists():
            parser.error("Report already exists; refusing to overwrite")
    report = reproduce(args.source, memory_bytes=args.memory_bytes,
                       archive_reads=args.archive_reads,
                       attention_steps=args.attention_steps)
    output = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            stream.write(output)
    print(output, end="")


if __name__ == "__main__":
    main()
