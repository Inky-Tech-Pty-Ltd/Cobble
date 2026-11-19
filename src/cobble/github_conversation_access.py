"""Render verified local GitHub conversations as paginated MCP-ready text.

The archive is the sole source. Do not fetch from GitHub, modify snapshots,
infer comment authorship, or treat Village Links as established truth.
"""
import json
from pathlib import Path

from cobble.git_archive import _slug
from cobble.github_memory_access import _archive_record, _KINDS, read_github_discussion


def _actor(item: dict) -> str:
    user = item.get("user") or item.get("actor") or item.get("author") or {}
    if not isinstance(user, dict):
        return "unknown"
    return user.get("login") or "unknown"


def _url(item: dict, default: str = "(not supplied)") -> str:
    # GitHub's html_url is a user-facing permalink; url may be a REST URL.
    return item.get("html_url") or item.get("url") or default


def _render_rest(record: dict, repository: str, kind: str, number: int):
    issue = record["issue"]
    pull = record.get("pull") if kind == "pull" else None
    primary = pull or issue
    fallback = (f"https://github.com/{repository}/"
                f"{'pull' if kind == 'pull' else 'issues'}/{number}")
    source = issue.get("html_url") or primary.get("html_url") or fallback
    parts = [
        "# " + (issue.get("title") or primary.get("title") or "(untitled)"),
        "Source: " + source,
        "Kind: " + ("Pull request" if kind == "pull" else "Issue"),
        "Author: " + _actor(issue),
        "Created: " + (issue.get("created_at") or "unknown"),
        "Updated: " + (issue.get("updated_at") or "unknown"),
        "State: " + (issue.get("state") or "unknown"),
        "",
        issue.get("body") or "",
    ]
    if pull is not None:
        if pull.get("body") and pull["body"] != (issue.get("body") or ""):
            parts.extend(["", "## Pull request description", pull["body"]])
        if pull.get("merged_at"):
            parts.extend(["", "Merged: " + pull["merged_at"]])

    entries = []

    def append(item: dict, heading: str, details=(), date_field=None):
        if not isinstance(item, dict):
            raise ValueError("Invalid archived conversation entry")
        date = item.get(date_field) if date_field else None
        date = date or item.get("created_at") or item.get("submitted_at")
        lines = [
            "", f"## {heading} — {_actor(item)}",
            "Source: " + _url(item),
            "Created: " + (date or "unknown"),
        ]
        for field, value in details:
            if value is not None and value != "":
                lines.append(f"{field}: {value}")
        lines.extend(["", item.get("body") or ""])
        entries.append((date or "", len(entries), lines))

    for comment in record.get("conversation_comments", []):
        append(comment, "Comment")

    if kind == "pull":
        for review in record.get("reviews", []):
            append(review, "Review",
                   details=(("State", review.get("state")),),
                   date_field="submitted_at")
        for comment in record.get("review_comments", []):
            append(comment, "Inline review comment",
                   details=(("File", comment.get("path")),
                            ("Line", comment.get("line") or comment.get("original_line")),
                            ("Side", comment.get("side")),
                            ("Reply to comment", comment.get("in_reply_to_id"))))

    for event in record.get("timeline", []):
        # The REST timeline's commented events duplicate issue comments.
        if event.get("event") == "commented":
            continue
        append(event, "Timeline: " + str(event.get("event") or "event"),
               details=(("Commit", event.get("commit_id")),))

    # GitHub ISO8601 timestamps sort lexically. Stable ties preserve the
    # archive's original order; missing timestamps follow dated entries.
    for _, _, lines in sorted(entries, key=lambda e: (not bool(e[0]), e[0], e[1])):
        parts.extend(lines)
    return "\n".join(parts), source, issue, primary


def read_github_conversation(store: Path, repository: str, kind: str,
                             number: int, offset: int = 0,
                             max_chars: int = 12000) -> dict:
    """Read one preserved Issue, PR, or Discussion with explicit type.

    The immutable content-addressed snapshot is verified before rendering.
    Distinct namespaces avoid Issue/PR/Discussion number ambiguity.
    """
    if type(kind) is not str or kind not in _KINDS:
        raise ValueError("Kind must be issue, pull or discussion")
    if type(offset) is not int or offset < 0:
        raise ValueError("Offset must be nonnegative")
    if type(max_chars) is not int or not 1000 <= max_chars <= 16000:
        raise ValueError("max_chars must be between 1000 and 16000")
    if kind == "discussion":
        # Retain the already verified Discussion renderer unchanged.
        return {"kind": kind, **read_github_discussion(
            store, repository, number, offset, max_chars)}

    record = _archive_record(store, repository, number, kind)
    body, source, issue, primary = _render_rest(record, repository, kind, number)
    page = body[offset:offset + max_chars]
    end = offset + len(page)
    return {
        "repository": _slug(repository),
        "kind": kind,
        "number": number,
        "source_uri": source,
        "title": issue.get("title") or primary.get("title"),
        "author": _actor(issue),
        "updated_at": issue.get("updated_at") or primary.get("updated_at"),
        "content": page,
        "offset": offset,
        "next_offset": end if end < len(body) else None,
        "total_chars": len(body),
        "truncated": end < len(body),
        "scope": "Locally archived GitHub conversation; no live GitHub request",
    }


def read_github_conversation_mcp_text(store: Path, repository: str, kind: str,
                                      number: int, offset: int = 0,
                                      max_chars: int = 12000) -> str:
    """Serialize the complete bounded page as MCP-friendly JSON text."""
    return json.dumps(read_github_conversation(
        store, repository, kind, number, offset, max_chars), ensure_ascii=False)
