"""Bounded, verified source inspection for authorised Cobble laboratory workers.

This is an *operator* sense, not Snug's learner sense. It reads only the
derived Arena's manifested copy, never the original archive. It is deliberately
not a network-facing file browser or an arbitrary filesystem read endpoint.
"""
import hashlib
import os
import stat
from pathlib import Path

from cobble.arena_catalogue import _records

MAX_BYTES = 12000
MIN_BYTES = 1000


def _open_manifested_file(corpus: Path, relative: str):
    """Follow only regular path components; never traverse symlinks."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    current = os.open(corpus, flags | os.O_DIRECTORY)
    try:
        parts = relative.split("/")
        for part in parts[:-1]:
            next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=current)
            os.close(current)
            current = next_fd
        file_fd = os.open(parts[-1], flags, dir_fd=current)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            os.close(file_fd)
            raise ValueError("Source is not a regular file")
        return os.fdopen(file_fd, "rb")
    finally:
        os.close(current)


def read_source(arena, path: str, offset: int = 0, max_bytes: int = 8000):
    """Return a verified UTF-8 byte-page, never more than 12 KB of source text.

    The source must appear in the populated Arena's manifest. Its complete
    SHA-256 is verified before returning a text page. Pagination uses byte
    offsets; callers should always use the returned next_offset. Files that
    cannot be represented as UTF-8 text are not exposed by this tool.
    """
    if not isinstance(path, str) or not path or len(path) > 2048:
        raise ValueError("path must be a nonempty manifested relative path")
    if type(offset) is not int or offset < 0:
        raise ValueError("offset must be a nonnegative byte index")
    if type(max_bytes) is not int or not MIN_BYTES <= max_bytes <= MAX_BYTES:
        raise ValueError("max_bytes must be between 1000 and 12000")
    arena = Path(arena).expanduser().resolve()
    _, entries, manifest_digest = _records(arena)
    record = next((item for item in entries if item["path"] == path), None)
    if record is None:
        raise ValueError("Source is not in Arena manifest")
    size = record["bytes"]
    if offset > size:
        raise ValueError("offset lies beyond source end")
    with _open_manifested_file(arena / "corpus", path) as stream:
        before = os.fstat(stream.fileno())
        if before.st_size != size:
            raise ValueError("Source size differs from manifest")
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        if (before.st_mtime_ns != after.st_mtime_ns or
                before.st_ctime_ns != after.st_ctime_ns or
                before.st_size != after.st_size or digest.hexdigest() != record["sha256"]):
            raise ValueError("Source differs from its populated Arena manifest")
        stream.seek(offset)
        data = stream.read(min(max_bytes, size - offset))
    if b"\x00" in data:
        raise ValueError("Binary source cannot be read using the text tool")
    try:
        text = data.decode("utf-8")
        consumed = len(data)
    except UnicodeDecodeError as exc:
        # A page may end inside a multi-byte code point; do not lose bytes.
        if exc.reason != "unexpected end of data" or exc.start < len(data) - 4:
            raise ValueError("Source is not valid UTF-8 at this offset") from exc
        text = data[:exc.start].decode("utf-8")
        consumed = exc.start
    next_offset = offset + consumed
    return {
        "path": path,
        "content": text,
        "offset": offset,
        "next_offset": next_offset if next_offset < size else None,
        "total_bytes": size,
        "source_sha256": record["sha256"],
        "manifest_sha256": manifest_digest,
        "scope": "Verified copied Arena text; read by an authorised laboratory operator, not Snug's metered attention",
    }
