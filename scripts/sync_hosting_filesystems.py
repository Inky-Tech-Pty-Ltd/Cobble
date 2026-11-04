#!/usr/bin/env python3
"""Preserve versioned local mirrors of Cobble's two hosting filesystems.

Source acquisition only: no model, indexing, or memory-graph dependencies.
"""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import uuid


@dataclass(frozen=True)
class Source:
    name: str
    origin: str  # rsync source, with a trailing slash
    key: str | None = None
    remote_rsync: str | None = None
    excludes: tuple[str, ...] = ("/mail/",)


SOURCES = {
    "inkytech": Source(
        name="inkytech",
        origin="inkytech@cp-wc36.per01.ds.network:/home12/inkytech/",
        key="~/.ssh/cobble_inkytech",
        remote_rsync="/home12/inkytech/.local/bin/rsync",
    ),
    "villagelink": Source(
        name="villagelink",
        origin="villagel@sh00046.cd.ds.network:/home1/villagel/",
        key="~/.ssh/cobble_villagelink",
        excludes=("/mail/", "/public_ftp/.ftpquota"),
    ),
}


class SyncError(RuntimeError):
    pass


def private_dir(path: Path) -> None:
    if path.is_symlink():
        raise SyncError(f"Refusing symlinked archive directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def inventory(root: Path) -> dict[str, tuple]:
    """Metadata inventory, never follows directory symlinks or reads file content."""
    result: dict[str, tuple] = {}
    if not root.exists():
        return result
    if root.is_symlink() or not root.is_dir():
        raise SyncError(f"Expected ordinary archive directory: {root}")
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            meta = path.lstat()
            rel = path.relative_to(root).as_posix()
            if stat.S_ISLNK(meta.st_mode):
                result[rel] = ("link", os.readlink(path))
            elif stat.S_ISDIR(meta.st_mode):
                result[rel] = ("dir", stat.S_IMODE(meta.st_mode))
            elif stat.S_ISREG(meta.st_mode):
                result[rel] = (
                    "file", meta.st_size, meta.st_mtime_ns,
                    stat.S_IMODE(meta.st_mode),
                )
            else:
                result[rel] = ("other", stat.S_IFMT(meta.st_mode))
    return result


def changes(before: dict[str, tuple], after: dict[str, tuple]) -> dict[str, list[str]]:
    old, new = set(before), set(after)
    return {
        "added": sorted(new - old),
        "modified": sorted(path for path in new & old if before[path] != after[path]),
        "deleted": sorted(old - new),
    }


def rsync_command(source: Source, archive: Path, *, dry_run: bool,
                  history: Path | None = None, delete: bool = False) -> list[str]:
    cmd = ["rsync", "-a", "--itemize-changes"]
    if dry_run:
        cmd += ["--dry-run"]
    elif history is not None:
        cmd += ["--backup", f"--backup-dir={history}"]
    if delete:
        cmd += ["--delete-after"]
    for pattern in source.excludes:
        cmd += [f"--exclude={pattern}"]
    if source.key:
        key = Path(source.key).expanduser()
        if not key.is_file():
            raise SyncError(f"SSH key not found: {key}")
        transport = f"ssh -i {shlex.quote(str(key))} -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes"
        cmd += ["-e", transport]
    if source.remote_rsync:
        cmd += [f"--rsync-path={source.remote_rsync}"]
    cmd += [source.origin, str(archive) + "/"]
    return cmd


def execute(cmd: list[str]) -> str:
    completed = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode:
        # Path names and sensitive material can appear in stderr; keep logs private.
        details = (completed.stderr or completed.stdout).strip()
        raise SyncError(f"rsync exited {completed.returncode}: {details[-2000:]}")
    return completed.stdout


def write_news(path: Path, *, source: Source, run_id: str, state: str,
               before: dict[str, tuple], after: dict[str, tuple],
               error: str | None = None) -> dict:
    result = changes(before, after)
    document = {
        "source": source.name,
        "run_id": run_id,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "status": state,
        "method": "rsync archive, metadata comparison (size/time/mode/link target)",
        "changes": result,
        "counts": {name: len(paths) for name, paths in result.items()},
    }
    if error is not None:
        document["error"] = error
    temp = path.with_name(path.name + ".tmp")
    with temp.open("x", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temp.replace(path)
    path.chmod(0o600)
    return document


def sync_source(source: Source, store: Path, *, run_id: str, dry_run: bool = False) -> dict | None:
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", source.name):
        raise SyncError(f"Unsafe source name: {source.name}")
    if not re.fullmatch(r"[0-9A-Za-z_.-]+", run_id):
        raise SyncError("Unsafe run ID")
    hosting = store / "hosting"
    archive = hosting / source.name
    history = hosting / "history" / source.name / run_id
    news_dir = hosting / "news" / source.name

    if dry_run:
        print(f"=== {source.name}: DRY RUN (no changes) ===")
        print(execute(rsync_command(source, archive, dry_run=True, delete=True)), end="")
        return None

    private_dir(hosting)
    private_dir(archive)
    private_dir(history)
    private_dir(news_dir)
    before = inventory(archive)
    failure = None
    try:
        # Never delete local files until a non-deleting content refresh succeeds.
        private_dir(history / "refresh")
        private_dir(history / "finalise")
        execute(rsync_command(source, archive, dry_run=False, history=history / "refresh"))
        execute(rsync_command(source, archive, dry_run=False, history=history / "finalise", delete=True))
    except (SyncError, OSError) as exc:
        failure = str(exc)
    finally:
        # rsync -a can restore the hosting account's permissive root mode.
        archive.chmod(0o700)
    after = inventory(archive)
    report = write_news(
        news_dir / f"{run_id}.json", source=source, run_id=run_id,
        state="failed" if failure else "complete", before=before,
        after=after, error=failure,
    )
    print(f"{source.name}: {report['status']} — "
          + ", ".join(f"{key}={value}" for key, value in report["counts"].items()))
    print(f"News: {news_dir / (run_id + '.json')}")
    if failure:
        raise SyncError(f"{source.name}: {failure}. Local snapshot may be partially refreshed; preserved backups and failure news remain.")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("all", *SOURCES), default="all")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    os.umask(0o077)
    selected = list(SOURCES.values()) if args.source == "all" else [SOURCES[args.source]]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:6]
    try:
        if args.dry_run:
            for source in selected:
                sync_source(source, args.store.expanduser(), run_id=run_id, dry_run=True)
            return 0
        logs = args.store.expanduser() / "logs" / "hosting-sync"
        private_dir(logs)
        lock_path = logs / ".sync.lock"
        with lock_path.open("a+") as lock:
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise SyncError("Another hosting sync is running; refusing to overlap") from exc
            for source in selected:
                sync_source(source, args.store.expanduser(), run_id=run_id)
    except (SyncError, OSError) as exc:
        print(f"Hosting sync failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
