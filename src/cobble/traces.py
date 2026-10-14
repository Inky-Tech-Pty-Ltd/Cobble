"""Local, portable trace identities and optional faithful text copies."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4


def mint_trace_uri(base_uri: str = "https://cobble.link/t") -> str:
    """Mint a new trace identity independent of storage location."""
    return f"{base_uri.rstrip('/')}/{uuid4()}"


def trace_id(uri: str) -> str:
    """Validate a Cobble trace URI before using its ID as a filename."""
    parts = urlsplit(uri)
    if (parts.scheme, parts.netloc) != ("https", "cobble.link"):
        raise ValueError(f"Not a Cobble trace URI: {uri!r}")
    if not parts.path.startswith("/t/") or parts.query or parts.fragment:
        raise ValueError(f"Not a Cobble trace URI: {uri!r}")
    value = parts.path.removeprefix("/t/")
    try:
        if str(UUID(value)) != value:
            raise ValueError("non-canonical ID")
    except ValueError as exc:
        raise ValueError(f"Invalid Cobble trace ID: {uri!r}") from exc
    return value


def mint_trace(store: Path, source_uri: str, exact: str, copy_text: str | None = None) -> dict:
    """Store a selected trace, optionally preserving a local text excerpt.

    Copies are snapshots of supplied text, not automatic fetches of the source.
    """
    if not source_uri or not urlsplit(source_uri).scheme:
        raise ValueError("Source URI required")
    if not exact:
        raise ValueError("Nonempty selector required")
    if copy_text is not None and exact not in copy_text:
        raise ValueError("Selected passage not found in local copy")
    store = Path(store).expanduser().resolve()
    uri = mint_trace_uri()
    ident = trace_id(uri)
    traces = store / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    record = {
        "uri": uri,
        "source_uri": source_uri,
        "selector": {"type": "TextQuoteSelector", "exact": exact},
    }
    if copy_text is not None:
        copies = store / "copies"
        copies.mkdir(parents=True, exist_ok=True)
        copy_path = copies / f"{ident}.txt"
        with copy_path.open("x", encoding="utf-8") as stream:
            stream.write(copy_text)
        record["local_copy_uri"] = copy_path.as_uri()
    trace_path = traces / f"{ident}.json"
    with trace_path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return record


def resolve_local(store: Path, uri: str) -> str:
    """Retrieve a retained text copy without consulting its original source.

    Only copies inside the Cobble store can be read.
    """
    store = Path(store).expanduser().resolve()
    ident = trace_id(uri)
    record_path = store / "traces" / f"{ident}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("uri") != uri:
        raise ValueError("Trace identity mismatch")
    copy_uri = record.get("local_copy_uri")
    if not copy_uri:
        raise FileNotFoundError(f"No local copy for {uri}")
    parts = urlsplit(copy_uri)
    if parts.scheme != "file" or parts.netloc not in ("", "localhost") or parts.query or parts.fragment:
        raise ValueError("Invalid local copy URI")
    from urllib.parse import unquote
    copy_path = Path(unquote(parts.path)).resolve()
    if not copy_path.is_relative_to(store):
        raise ValueError("Copy is outside the Cobble store")
    content = copy_path.read_text(encoding="utf-8")
    if record["selector"]["exact"] not in content:
        raise ValueError("Selected passage missing from local copy")
    return content
