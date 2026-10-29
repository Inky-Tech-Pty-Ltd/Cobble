"""Read-only source senses for a copied Arena corpus.

Only its immutable-at-population manifest is inspected. This code does not
scan original archives, interpret text, visit the web or spend Arena budgets.
Source paths and hashes are metadata, not verified meaning.
"""
import hashlib
import json
import re
from pathlib import Path

from cobble.arena import overview

VERSION = "arena-catalogue-0.1"
CATEGORIES = (
    "github-conversations",
    "github-repositories",
    "github-manifests",
    "chatgpt",
    "traces",
    "links",
    "stars",
    "hypotheses",
    "other",
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def category_of(path: str) -> str:
    if path.startswith("github/conversations/"):
        return "github-conversations"
    if path.startswith("github/repositories/"):
        return "github-repositories"
    if path.startswith("github/manifests/"):
        return "github-manifests"
    for key in ("chatgpt", "traces", "links", "stars", "hypotheses"):
        if path.startswith(key + "/"):
            return key
    return "other"


def _records(arena):
    """Validate file metadata from the populated Arena's saved manifest."""
    arena = Path(arena).expanduser().resolve()
    state = overview(arena)
    population = state.get("population")
    if not isinstance(population, dict):
        raise ValueError("Arena has no populated corpus")
    corpus = arena / "corpus"
    pointer = corpus / ".arena-manifest.json"
    if corpus.is_symlink() or pointer.is_symlink():
        raise ValueError("Arena corpus or manifest is a symlink")
    if not corpus.is_dir() or not pointer.is_file():
        raise ValueError("Arena manifest missing")
    if population.get("manifest") != "corpus/.arena-manifest.json":
        raise ValueError("Unrecognised Arena manifest location")
    contents = pointer.read_bytes()
    manifest = json.loads(contents)
    if manifest.get("format") != state["format"] or not isinstance(manifest.get("files"), list):
        raise ValueError("Incompatible Arena manifest")
    files = []
    seen = set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise ValueError("Malformed manifest entry")
        path, size, digest = entry.get("path"), entry.get("bytes"), entry.get("sha256")
        if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
            raise ValueError("Invalid source path")
        if any(part in ("", ".", "..") for part in path.split("/")):
            raise ValueError("Unsafe source path")
        if path in seen or path == ".arena-manifest.json":
            raise ValueError("Duplicate or reserved source path")
        seen.add(path)
        if type(size) is not int or size < 0:
            raise ValueError("Invalid file size")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("Invalid file digest")
        files.append({"path": path, "bytes": size, "sha256": digest,
                      "category": category_of(path)})
    files.sort(key=lambda item: item["path"])
    if len(files) != population.get("files") or sum(f["bytes"] for f in files) != population.get("source_bytes"):
        raise ValueError("Manifest does not agree with Arena population")
    return state, files, hashlib.sha256(contents).hexdigest()


def catalogue(arena):
    """Return a complete, bounded-size category census without source names."""
    state, files, manifest_digest = _records(arena)
    census = {key: {"files": 0, "bytes": 0} for key in CATEGORIES}
    for item in files:
        row = census[item["category"]]
        row["files"] += 1
        row["bytes"] += item["bytes"]
    return {
        "schema": VERSION,
        "arena_format": state["format"],
        "manifest_sha256": manifest_digest,
        "total_files": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "categories": census,
        "scope": "Source filenames classified from the saved copy manifest; no text inspected",
        "accounting": "Operator diagnostics only; not yet metered juvenile attention",
    }


def list_sources(arena, category: str = "all", offset: int = 0, limit: int = 25,
                 query: str = ""):
    """Page source paths from the same manifest; disclose no source contents."""
    if category != "all" and category not in CATEGORIES:
        raise ValueError("Unknown source category")
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be nonnegative")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("limit must be 1–50")
    if not isinstance(query, str) or len(query) > 80:
        raise ValueError("query must be at most 80 characters")
    state, entries, manifest_digest = _records(arena)
    needle = query.casefold()
    matches = [
        item for item in entries
        if (category == "all" or item["category"] == category)
        and needle in item["path"].casefold()
    ]
    page = matches[offset:offset + limit]
    next_offset = offset + len(page)
    return {
        "schema": VERSION,
        "arena_format": state["format"],
        "manifest_sha256": manifest_digest,
        "filter": {"category": category, "query": query},
        "offset": offset,
        "total_matches": len(matches),
        "entries": page,
        "next_offset": next_offset if next_offset < len(matches) else None,
        "scope": "Read-only manifest metadata including potentially sensitive filenames; no source text",
    }
