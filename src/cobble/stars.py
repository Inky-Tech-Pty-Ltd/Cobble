"""Hypothesis-centred star credentials using real Village Link rays.

Everything remains in the local Cobble store; nothing is publicly published.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from cobble.traces import mint_trace_uri
from villagelink.codec import make, parse


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


def save_json(path: Path, record: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def mint_star(store: Path, hypothesis: str, members: list[str]) -> dict:
    """Mint a new centre trace, star credential and its VL rays.

    Evidence trace records must already exist. Equivalence is asserted,
    not established. This is not yet a transaction-safe storage engine.
    """
    store = Path(store).expanduser().resolve()
    hypothesis = hypothesis.strip()
    if not hypothesis:
        raise ValueError("Hypothesis is empty")
    if len(members) < 2 or len(set(members)) != len(members):
        raise ValueError("Provide at least two distinct evidence trace URIs")

    traces = store / "traces"
    for uri in members:
        record_path = traces / f"{trace_id(uri)}.json"
        if not record_path.is_file():
            raise ValueError(f"Evidence trace missing: {uri}")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("uri") != uri:
            raise ValueError(f"Evidence URI mismatch: {uri}")

    centre = mint_trace_uri()
    ident = trace_id(centre)
    hypotheses, stars, links = (
        store / "hypotheses", store / "stars", store / "links"
    )
    for directory in (traces, hypotheses, stars, links):
        directory.mkdir(parents=True, exist_ok=True)

    hypothesis_file = hypotheses / f"{ident}.txt"
    with hypothesis_file.open("x", encoding="utf-8") as stream:
        stream.write(hypothesis + "\n")

    save_json(traces / f"{ident}.json", {
        "uri": centre,
        "kind": "hypothesis",
        "source_uri": hypothesis_file.as_uri(),
        "selector": {"type": "TextQuoteSelector", "exact": hypothesis},
    })
    star = {"type": "StarCredential", "A": centre, "B": sorted(members)}
    save_json(stars / f"{ident}.json", star)

    for member in star["B"]:
        ray = make(centre, member)
        assert parse(ray) == (centre, member)
        filename = hashlib.sha256(ray.encode("utf-8")).hexdigest() + ".json"
        save_json(links / filename, {"uri": ray, "scope": "local"})
    return star
