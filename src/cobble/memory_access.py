"""Read-only, bounded memory queries for Cobble's first MCP interface."""
import hashlib
import json
from pathlib import Path

from cobble.traces import resolve_local, trace_id
from villagelink.codec import make, parse

MAX_TEXT = 20000
MAX_QUERY = 200
MAX_RESULTS = 20


def get_trace(store: Path, uri: str) -> dict:
    """Return metadata and a bounded retained excerpt, without network access."""
    root = Path(store).expanduser().resolve()
    ident = trace_id(uri)
    record = json.loads((root / "traces" / f"{ident}.json").read_text(encoding="utf-8"))
    if record.get("uri") != uri:
        raise ValueError("Trace identity mismatch")
    try:
        content = resolve_local(root, uri)
        return {"trace": record, "content": content[:MAX_TEXT],
                "truncated": len(content) > MAX_TEXT}
    except FileNotFoundError:
        return {"trace": record, "content": None, "truncated": False,
                "note": "No retained local copy."}


def inspect_star(store: Path, centre_uri: str) -> dict:
    """Verify local ray records; avoid a network fetch or truth judgement."""
    root = Path(store).expanduser().resolve()
    ident = trace_id(centre_uri)
    star = json.loads((root / "stars" / f"{ident}.json").read_text(encoding="utf-8"))
    if star.get("type") != "StarCredential" or star.get("A") != centre_uri:
        raise ValueError("Not a matching StarCredential")
    centre = json.loads((root / "traces" / f"{ident}.json").read_text(encoding="utf-8"))
    if centre.get("uri") != centre_uri:
        raise ValueError("Centre trace identity mismatch")
    rays = []
    for member in star["B"]:
        ray = make(centre_uri, member)
        sha = hashlib.sha256(ray.encode("utf-8")).hexdigest()
        link = json.loads((root / "links" / f"{sha}.json").read_text(encoding="utf-8"))
        if link.get("uri") != ray or parse(ray) != (centre_uri, member):
            raise ValueError(f"Invalid locally recorded ray to {member}")
        rays.append({"member": member, "vl_uri": ray})
    return {"centre": centre, "members": rays, "count": len(rays)}


def search_memory(store: Path, query: str, limit: int = 10) -> dict:
    """Search trace selectors and retained text; no crawling or inference.

    This is deliberately a narrow first search, not full GitHub history search.
    """
    if not query or not query.strip() or len(query) > MAX_QUERY:
        raise ValueError("Query must contain 1–200 characters")
    if not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError("Limit must be between 1 and 20")
    root = Path(store).expanduser().resolve()
    needle = query.casefold()
    hits = []
    # Existing trace records are the authoritative catalogue.
    for path in sorted((root / "traces").glob("*.json")):
        if path.is_symlink():
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        uri = record.get("uri", "")
        try:
            if trace_id(uri) != path.stem:
                continue
        except ValueError:
            continue
        exact = record.get("selector", {}).get("exact", "")
        match = needle in exact.casefold()
        # Include retained excerpts only through the safe trace resolver.
        if not match:
            try:
                content = resolve_local(root, uri)
                match = needle in content.casefold()
            except (FileNotFoundError, ValueError):
                pass
        if match:
            hits.append({"uri": uri, "source_uri": record.get("source_uri"),
                         "selector": exact[:500]})
            if len(hits) == limit:
                break
    return {"query": query, "results": hits, "count": len(hits),
            "scope": "Cobble trace selectors and their retained local text"}
