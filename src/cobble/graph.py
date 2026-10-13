"""Read-only evidence-aware inspection of a local hypothesis-centred star.

The graph contains assertions, not verified truth. Missing sources and partial
writes are visible and never silently repaired or accepted as complete.
"""
import hashlib
import json
from pathlib import Path

from cobble.observations import observations_for
from cobble.stars import trace_id
from villagelink.codec import make, parse


def inspect_hypothesis(store: Path, centre_uri: str) -> dict:
    store = Path(store).expanduser().resolve()
    ident = trace_id(centre_uri)
    star_path = store / "stars" / (ident + ".json")
    centre_path = store / "traces" / (ident + ".json")
    star = json.loads(star_path.read_text(encoding="utf-8"))
    centre = json.loads(centre_path.read_text(encoding="utf-8"))
    members = star.get("B")
    if (star.get("type") != "StarCredential" or star.get("A") != centre_uri
            or centre.get("uri") != centre_uri or centre.get("kind") != "hypothesis"
            or not isinstance(members, list) or len(members) < 2
            or len(set(members)) != len(members)):
        raise ValueError("Invalid hypothesis star or centre")
    evidence = []
    for uri in members:
        member_id = trace_id(uri)
        trace_path = store / "traces" / (member_id + ".json")
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        if trace.get("uri") != uri:
            raise ValueError("Evidence trace URI mismatch")
        ray = make(centre_uri, uri)
        if parse(ray) != (centre_uri, uri):
            raise ValueError("Village Link codec disagreement")
        ray_file = store / "links" / (hashlib.sha256(ray.encode("utf-8")).hexdigest() + ".json")
        saved = json.loads(ray_file.read_text(encoding="utf-8"))
        if saved.get("uri") != ray:
            raise ValueError("Missing or inconsistent Village Link ray")
        history = observations_for(store, uri)
        evidence.append({
            "trace_uri": uri,
            "source_uri": trace.get("source_uri"),
            "observations": history,
            "latest_retrieval": history[-1]["retrieval"]["status"] if history else "unknown",
        })
    return {
        "hypothesis_uri": centre_uri,
        "hypothesis": centre.get("selector", {}).get("exact"),
        "claim_status": "asserted-not-verified",
        "members": evidence,
    }


def simple_baseline(store: Path, centre_uri: str) -> dict:
    """G0: unconnected trace inventory without star-member relationships.

    This is an illustrative structural baseline, not evidence of improved
    semantic retrieval accuracy or model-independent continuity.
    """
    ident = trace_id(centre_uri)
    store = Path(store).expanduser().resolve()
    centre = json.loads((store / "traces" / (ident + ".json")).read_text(encoding="utf-8"))
    if centre.get("uri") != centre_uri or centre.get("kind") != "hypothesis":
        raise ValueError("Invalid hypothesis centre")
    folder = store / "traces"
    inventory = []
    for path in folder.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("kind") != "hypothesis":
            inventory.append(record["uri"])
    return {"query": centre.get("selector", {}).get("exact"), "candidate_count": len(inventory),
            "candidates": sorted(inventory), "relationships_available": False}
