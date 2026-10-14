"""Read locally archived GitHub Discussions, without fetching GitHub.

Return bounded pages of original discussion text with source metadata.
This is an archive reader, not a Village Link truth judgement.
"""
import hashlib
import json
import re
from pathlib import Path

from cobble.git_archive import _slug


def _archive_record(store: Path, slug: str, number: int) -> dict:
    slug = _slug(slug)
    if type(number) is not int or number < 1:
        raise ValueError("Discussion number must be a positive integer")
    owner, repo = slug.split("/")
    base = (Path(store).expanduser().resolve() / "github" / "conversations"
            / owner / repo / "discussions" / str(number))
    pointer_path = base / "latest.json"
    if pointer_path.is_symlink():
        raise ValueError("Archive pointer cannot be a symlink")
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    digest = pointer.get("sha256")
    version = pointer.get("version")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid archive digest")
    if version != f"versions/{digest}.json":
        raise ValueError("Invalid archived version reference")
    version_path = base / "versions" / (digest + ".json")
    if version_path.is_symlink():
        raise ValueError("Archive version cannot be a symlink")
    record = json.loads(version_path.read_text(encoding="utf-8"))
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != digest:
        raise ValueError("Archived discussion does not match its digest")
    discussion = record.get("discussion", {})
    if record.get("kind") != "discussion" or discussion.get("number") != number:
        raise ValueError("Archive record is not the requested discussion")
    return record


def _author(item: dict) -> str:
    return (item.get("author") or {}).get("login") or "unknown"


def read_github_discussion(store: Path, repository: str, number: int,
                           offset: int = 0, max_chars: int = 12000) -> dict:
    """Read a page of a preserved discussion, including comments and replies.

    Character offsets paginate a consistent content-addressed snapshot.
    Re-imported edits may change the latest version between calls.
    """
    if type(offset) is not int or offset < 0:
        raise ValueError("Offset must be nonnegative")
    if type(max_chars) is not int or not 1000 <= max_chars <= 16000:
        raise ValueError("max_chars must be between 1000 and 16000")
    record = _archive_record(store, repository, number)
    d = record["discussion"]
    sections = [
        f"# {d.get('title') or '(untitled)'}",
        f"Source: {d.get('url') or 'https://github.com/' + repository + '/discussions/' + str(number)}",
        f"Author: {_author(d)}",
        f"Created: {d.get('createdAt') or 'unknown'}",
        "",
        d.get("body") or "",
    ]
    for entry in record.get("comments", []):
        c = entry.get("comment") or {}
        sections.extend(["", f"## Comment — {_author(c)}",
                         f"Source: {c.get('url') or '(not supplied)'}",
                         c.get("body") or ""])
        for reply in entry.get("replies", []):
            sections.extend(["", f"### Reply — {_author(reply)}",
                             f"Source: {reply.get('url') or '(not supplied)'}",
                             reply.get("body") or ""])
    text = "\n".join(sections)
    page = text[offset:offset + max_chars]
    next_offset = offset + len(page)
    return {
        "repository": _slug(repository),
        "number": number,
        "source_uri": d.get("url") or f"https://github.com/{repository}/discussions/{number}",
        "title": d.get("title"),
        "author": _author(d),
        "updated_at": d.get("updatedAt"),
        "content": page,
        "offset": offset,
        "next_offset": next_offset if next_offset < len(text) else None,
        "total_chars": len(text),
        "truncated": next_offset < len(text),
        "scope": "Locally archived GitHub discussion; no live GitHub request",
    }
