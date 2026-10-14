"""Incremental, offline-capable archive of a local Git repository.

Git stores objects by content. This copies Git history, not just worktree files.
"""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from cobble.traces import mint_trace

SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _git(*args: str, cwd: Path | None = None, decode: bool = True):
    cmd = ["git", *(["-C", str(cwd)] if cwd else []), *map(str, args)]
    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout.decode("utf-8") if decode else result.stdout


def _slug(slug: str) -> str:
    if not SLUG_RE.fullmatch(slug) or ".." in slug:
        raise ValueError("Expected an owner/repository name")
    return slug


def archive_repository(store: Path, slug: str, source: Path) -> dict:
    """Capture local Git objects and refs; subsequent calls fetch new objects.

    Preserve every observed HEAD under refs/cobble/snapshots/<sha>.
    No source changes, no network access, and no automatic meme inference.
    """
    slug = _slug(slug)
    store = Path(store).expanduser().resolve()
    source = Path(source).expanduser().resolve()
    if not source.is_dir():
        raise ValueError("Local Git repository directory is missing")
    toplevel = _git("rev-parse", "--show-toplevel", cwd=source).strip()
    if Path(toplevel).resolve() != source:
        raise ValueError("Source must be the repository root")
    _git("rev-parse", "--verify", "HEAD", cwd=source)
    owner, name = slug.split("/")
    dest = store / "github" / "repositories" / owner / (name + ".git")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        _git("clone", "--mirror", "--no-hardlinks", str(source), str(dest))
    else:
        if _git("rev-parse", "--is-bare-repository", cwd=dest).strip() != "true":
            raise ValueError("Archive destination is not a bare Git repository")
        # Do not prune: retain history referenced by existing snapshot refs.
        _git("fetch", "--no-prune", str(source), "+refs/*:refs/*", cwd=dest)

    head = _git("rev-parse", "HEAD", cwd=source).strip()
    _git("update-ref", f"refs/cobble/snapshots/{head}", head, cwd=dest)
    if _git("cat-file", "-t", head, cwd=dest).strip() != "commit":
        raise ValueError("Archive is missing the source HEAD commit")
    record = {
        "type": "GitRepositorySnapshot",
        "repository": slug,
        "source_uri": f"https://github.com/{slug}",
        "source_path": str(source),
        "archive_path": str(dest),
        "head": head,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    manifests = store / "github" / "manifests" / owner / name
    manifests.mkdir(parents=True, exist_ok=True)
    manifest = manifests / f"{head}.json"
    if not manifest.exists():
        with manifest.open("x", encoding="utf-8") as fp:
            json.dump(record, fp, indent=2)
            fp.write("\n")
    return record


def capture_file_trace(store: Path, slug: str, commit: str, path: str,
                       exact: str) -> dict:
    """Mint a trace for a selected UTF-8 passage in an archived Git blob."""
    slug = _slug(slug)
    store = Path(store).expanduser().resolve()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("Expected full Git commit SHA")
    if not path or path.startswith("/") or "\\" in path or any(
        part in ("", ".", "..") for part in path.split("/")
    ):
        raise ValueError("Invalid repository-relative file path")
    owner, name = slug.split("/")
    archive = store / "github" / "repositories" / owner / (name + ".git")
    if _git("cat-file", "-t", commit, cwd=archive).strip() != "commit":
        raise ValueError("Not a commit")
    content = _git("show", f"{commit}:{path}", cwd=archive)
    uri = f"https://github.com/{slug}/blob/{commit}/{quote(path, safe='/')}"
    return mint_trace(store, uri, exact, content)
