"""Hypothesis-centred star credentials using real Village Link rays.

Everything remains in the local Cobble store; nothing is publicly published.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from cobble.traces import mint_trace_uri, trace_id
from villagelink.codec import make, parse


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


def add_ray(store: Path, centre_uri: str, member_uri: str) -> dict:
    """Add a member to an existing star; do not mint a new centre.

    Repeated additions are no-ops. Writes use atomic replacement for the star,
    but the separate link and star files are not a multi-file transaction.
    """
    store = Path(store).expanduser().resolve()
    centre_id = trace_id(centre_uri)
    member_id = trace_id(member_uri)
    member_path = store / "traces" / f"{member_id}.json"
    member = json.loads(member_path.read_text(encoding="utf-8"))
    if member.get("uri") != member_uri:
        raise ValueError("Member trace identity mismatch")
    star_path = store / "stars" / f"{centre_id}.json"
    star = json.loads(star_path.read_text(encoding="utf-8"))
    if star.get("type") != "StarCredential" or star.get("A") != centre_uri:
        raise ValueError("Not a matching StarCredential")
    if member_uri == centre_uri:
        raise ValueError("Centre cannot be its own ray")
    if member_uri in star["B"]:
        return star

    ray = make(centre_uri, member_uri)
    if parse(ray) != (centre_uri, member_uri):
        raise ValueError("Village Link codec round-trip failed")
    link_path = store / "links" / (hashlib.sha256(ray.encode("utf-8")).hexdigest() + ".json")
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists():
        existing = json.loads(link_path.read_text(encoding="utf-8"))
        if existing.get("uri") != ray:
            raise ValueError("Existing ray record conflicts")
    else:
        save_json(link_path, {"uri": ray, "scope": "local"})
    updated = {**star, "B": sorted([*star["B"], member_uri])}
    # Atomic replacement of the star document (not a transaction with link file).
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                     dir=star_path.parent, prefix=".star-",
                                     suffix=".tmp", delete=False) as tmp:
        temp_path = Path(tmp.name)
        try:
            json.dump(updated, tmp, indent=2, ensure_ascii=False)
            tmp.write("\n")
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise
    os.replace(temp_path, star_path)
    return updated
