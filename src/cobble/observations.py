"""Append-only local observations about whether evidence sources can be retrieved.

Observations report retrieval outcomes, not the truth or trustworthiness of a trace.
One JSON file per observation avoids mutable 'current status' state.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from cobble.stars import trace_id

STATUSES = {"available", "unavailable", "restricted", "moved", "unknown"}
METHODS = {"local-file", "manual", "other"}


def record_observation(store: Path, uri: str, status: str, *,
                       method: str = "manual", observed_at: str | None = None) -> dict:
    """Append a validated observation; never dereference remote sources."""
    ident = trace_id(uri)
    store = Path(store).expanduser().resolve()
    trace_file = store / "traces" / (ident + ".json")
    if not trace_file.is_file():
        raise ValueError("Unknown evidence trace")
    trace = json.loads(trace_file.read_text(encoding="utf-8"))
    if trace.get("uri") != uri:
        raise ValueError("Trace URI mismatch")
    if status not in STATUSES or method not in METHODS:
        raise ValueError("Invalid observation status or method")
    timestamp = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if moment.tzinfo is None:
            raise ValueError("Timezone required")
    except (ValueError, TypeError) as exc:
        raise ValueError("observed_at must be timezone-aware ISO 8601") from exc
    observation = {
        "id": str(uuid4()),
        "trace_uri": uri,
        "observed_at": timestamp,
        "retrieval": {"status": status, "method": method},
        "integrity": {"status": "not_checked"},
    }
    dest = store / "observations" / ident
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / (observation["id"] + ".json")
    # Exclusive creation; never overwrite an earlier observation.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(observation, stream, indent=2)
        stream.write("\n")
    return observation


def observations_for(store: Path, uri: str) -> list[dict]:
    """Return an ordered history, using timestamps then IDs for deterministic ties."""
    folder = Path(store).expanduser().resolve() / "observations" / trace_id(uri)
    if not folder.is_dir():
        return []
    records = []
    for path in folder.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("trace_uri") != uri:
            raise ValueError(f"Observation mismatch: {path.name}")
        records.append(record)
    return sorted(records, key=lambda x: (x["observed_at"], x["id"]))
