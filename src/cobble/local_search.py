"""Offline, operator-only lexical search across four preserved Cobble sources.

This is the first read-only navigation slice, NOT a provider-facing memory API.
No model calls, remote requests, source writes or automatic sharing.
"""
from contextlib import closing
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import quote


SOURCES = ("chatgpt", "github", "inkytech", "villagelink")
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".html", ".htm",
                 ".xml", ".csv", ".php", ".py"}
EXCLUDED_DIRS = {"mail", "node_modules", "vendor", "cache", "tmp", "logs",
                 ".git", ".svn", "wp-admin", "wp-includes"}
SENSITIVE_NAME = re.compile(r"(^\.|secret|password|credential|token|private.key|"
                            r"(^|[-_.])config([-.]|$))", re.I)
VERSION = re.compile(r"versions/[0-9a-f]{64}\.json\Z")
MAX_TEXT_FILE = 1024 * 1024


def _read_latest(pointer):
    """Only a version sibling of this pointer can be read."""
    if pointer.is_symlink():
        raise ValueError("Symlinked snapshot pointer")
    data = json.loads(pointer.read_text(encoding="utf-8"))
    version = data.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Invalid snapshot version pointer")
    file = pointer.parent / version
    if file.is_symlink():
        raise ValueError("Symlinked snapshot version")
    return json.loads(file.read_text(encoding="utf-8"))


def _chat_text(record):
    lines = []
    title = record.get("title")
    if isinstance(title, str):
        lines.append(title)
    mapping = record.get("mapping")
    if not isinstance(mapping, dict):
        return "\n".join(lines)
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author")
        role = author.get("role", "") if isinstance(author, dict) else ""
        content = message.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts", [])
        if not isinstance(parts, list):
            parts = []
        snippets = []
        for part in parts:
            if isinstance(part, str):
                snippets.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                snippets.append(part["text"])
        if isinstance(content.get("text"), str):
            snippets.append(content["text"])
        if snippets:
            lines.append(f"{role}: " + "\n".join(snippets))
    return "\n\n".join(lines)


def _github_text(record):
    lines = []
    title = ""
    def add(item):
        nonlocal title
        if not isinstance(item, dict):
            return
        if not title and isinstance(item.get("title"), str):
            title = item["title"]
        for key in ("title", "body"):
            if isinstance(item.get(key), str) and item[key]:
                lines.append(item[key])
    for key in ("discussion", "issue", "pull"):
        add(record.get(key))
    for key in ("conversation_comments", "reviews", "review_comments", "timeline"):
        for item in record.get(key, []) or []:
            add(item)
    for thread in record.get("comments", []) or []:
        if isinstance(thread, dict):
            add(thread.get("comment"))
            for reply in thread.get("replies", []) or []:
                add(reply)
    return title, "\n\n".join(lines)


def _iter_hosted(root):
    """Avoid links, opaque formats, known app caches and obvious secret names."""
    for directory, dirs, filenames in os.walk(root, followlinks=False):
        location = Path(directory)
        dirs[:] = sorted(d for d in dirs
                         if d not in EXCLUDED_DIRS and not d.startswith(".")
                         and not (location / d).is_symlink())
        for filename in sorted(filenames):
            path = location / filename
            if (path.is_symlink() or not path.is_file()
                    or SENSITIVE_NAME.search(filename)
                    or path.suffix.lower() not in TEXT_SUFFIXES):
                continue
            if path.stat().st_size > MAX_TEXT_FILE:
                yield path, None
                continue
            raw = path.read_bytes()
            if b"\x00" in raw:
                yield path, None
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                yield path, None
                continue
            yield path, text


def _append(conn, source, ref, title, body):
    if not isinstance(body, str) or not body.strip():
        return False
    stable_id = hashlib.sha256((source + "\0" + ref).encode()).hexdigest()[:24]
    conn.execute("INSERT INTO memory (docid, source, ref, title, body) "
                 "VALUES (?, ?, ?, ?, ?)", (stable_id, source, ref, title, body))
    return True


def build(store, index):
    """Rebuild in a temporary database, publish only if every source succeeds."""
    store = Path(store).expanduser().resolve()
    index = Path(index).expanduser().absolute()
    index.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, staging = tempfile.mkstemp(prefix=".cobble-search-", suffix=".sqlite3",
                                   dir=index.parent)
    os.close(fd)
    report = {name: {"indexed": 0, "skipped": 0, "present": False}
              for name in SOURCES}
    conn = None
    try:
        conn = sqlite3.connect(staging)
        try:
            conn.execute("CREATE VIRTUAL TABLE memory USING fts5("
                         "docid UNINDEXED, source UNINDEXED, ref UNINDEXED, "
                         "title, body)")
        except sqlite3.OperationalError as exc:
            raise RuntimeError("Python SQLite needs FTS5 support") from exc

        for source in SOURCES:
            if source == "chatgpt":
                root = store / "openai" / "conversations"
            elif source == "github":
                root = store / "github" / "conversations"
            else:
                root = store / "hosting" / source
            if root.is_symlink():
                raise ValueError("Source root must not be a symlink")
            report[source]["present"] = root.is_dir()
            if not root.is_dir():
                continue
            if source in ("chatgpt", "github"):
                for pointer in sorted(root.rglob("latest.json")):
                    record = _read_latest(pointer)
                    ref = pointer.parent.relative_to(root).as_posix()
                    if source == "chatgpt":
                        title = record.get("title") or ref
                        body = _chat_text(record)
                    else:
                        title, body = _github_text(record)
                        title = title or ref
                    counted = "indexed" if _append(conn, source, ref, title, body) else "skipped"
                    report[source][counted] += 1
            else:
                for file, text in _iter_hosted(root):
                    ref = file.relative_to(root).as_posix()
                    counted = "indexed" if _append(conn, source, ref, file.name, text) else "skipped"
                    report[source][counted] += 1
        conn.commit()
        conn.close()
        conn = None
        os.replace(staging, index)
        os.chmod(index, 0o600)
    finally:
        if conn is not None:
            conn.close()
        Path(staging).unlink(missing_ok=True)
    return report


def _readonly(index):
    index = Path(index).expanduser().resolve(strict=True)
    uri = "file:" + quote(str(index), safe="/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def search(index, words, limit=8):
    """Literal user terms, not executable FTS query syntax."""
    if not isinstance(words, str) or len(words) > 240:
        raise ValueError("Search terms must be 1 to 240 characters")
    terms = re.findall(r"\w+", words, flags=re.UNICODE)
    if not terms:
        return []
    if not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError("Limit must be between 1 and 20")
    expression = " AND ".join('"' + token.replace('"', '""') + '"' for token in terms)
    with closing(_readonly(index)) as conn:
        cursor = conn.execute(
            "SELECT docid, source, ref, title, "
            "snippet(memory, 4, '[', ']', '…', 16) "
            "FROM memory WHERE memory MATCH ? ORDER BY rank LIMIT ?",
            (expression, limit))
        return [dict(zip(("id", "source", "reference", "title", "excerpt"), row))
                for row in cursor]


def show(index, docid, max_chars=1800):
    if not isinstance(docid, str) or not re.fullmatch(r"[a-f0-9]{24}", docid):
        raise ValueError("Invalid search document identifier")
    if type(max_chars) is not int or not 100 <= max_chars <= 12000:
        raise ValueError("max_chars must be 100 to 12000")
    with closing(_readonly(index)) as conn:
        row = conn.execute(
            "SELECT source, ref, title, body FROM memory WHERE docid = ? LIMIT 1",
            (docid,)).fetchone()
    if row is None:
        raise KeyError("Document not found in this index")
    body = row[3]
    return {"source": row[0], "reference": row[1], "title": row[2],
            "length": len(body), "text": body[:max_chars],
            "truncated": len(body) > max_chars}
