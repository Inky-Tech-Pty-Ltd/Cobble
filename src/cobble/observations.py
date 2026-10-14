"""Versioned experimental source-observation contract for Cobble.

An observation records a bounded claim about a retrieval attempt. It does not
establish source authority, semantic truth, freshness beyond the stated time,
or identity continuity.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from cobble.stars import trace_id

SCHEMA_VERSION = "0.1"
RETRIEVAL_STATUSES = {"available", "unavailable", "restricted", "moved", "not_checked", "unknown"}
INTEGRITY_STATUSES = {"not_checked", "matches_recorded_digest", "differs_from_recorded_digest", "unknown"}
METHODS = {"local-file", "manual", "other"}

def _time(value: str, field: str) -> str:
    try:
        moment=datetime.fromisoformat(value.replace("Z","+00:00"))
        if moment.tzinfo is None: raise ValueError("timezone required")
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{field} must be timezone-aware ISO 8601") from exc
    return value

def validate_observation(record: dict) -> dict:
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported observation schema_version")
    trace_id(record.get("trace_uri",""))
    _time(record.get("observed_at"),"observed_at")
    retrieved_at=record.get("retrieved_at")
    if retrieved_at is not None: _time(retrieved_at,"retrieved_at")
    source_event_at=record.get("source_event_at")
    if source_event_at is not None: _time(source_event_at,"source_event_at")
    retrieval=record.get("retrieval",{})
    if retrieval.get("status") not in RETRIEVAL_STATUSES or retrieval.get("method") not in METHODS:
        raise ValueError("Invalid retrieval status or method")
    integrity=record.get("integrity",{})
    if integrity.get("status") not in INTEGRITY_STATUSES:
        raise ValueError("Invalid integrity status")
    if retrieval["status"] == "not_checked" and retrieved_at is not None:
        raise ValueError("not_checked retrieval must not claim retrieved_at")
    if retrieval["status"] in {"available","unavailable","restricted","moved"} and retrieved_at is None:
        raise ValueError("attempted retrieval status requires retrieved_at")
    return record

def record_observation(store: Path, uri: str, status: str, *, method: str="manual",
                       observed_at: str|None=None, retrieved_at: str|None=None,
                       source_event_at: str|None=None, integrity_status: str="not_checked") -> dict:
    """Append one observation. No source is dereferenced by this function."""
    ident=trace_id(uri); store=Path(store).expanduser().resolve()
    trace_file=store/"traces"/(ident+".json")
    if not trace_file.is_file(): raise ValueError("Unknown evidence trace")
    trace=json.loads(trace_file.read_text(encoding="utf-8"))
    if trace.get("uri") != uri: raise ValueError("Trace URI mismatch")
    now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    observed_at=observed_at or now
    # Backward-compatible convenience: an explicit retrieval outcome historically
    # used observed_at as the attempt time. Preserve that behavior unless the
    # caller supplies a distinct retrieved_at.
    if status in {"available","unavailable","restricted","moved"} and retrieved_at is None:
        retrieved_at=observed_at
    record={
      "schema_version":SCHEMA_VERSION,
      "id":str(uuid4()),
      "trace_uri":uri,
      "observed_at":observed_at,
      "retrieved_at":retrieved_at,
      "source_event_at":source_event_at,
      "retrieval":{"status":status,"method":method},
      "integrity":{"status":integrity_status},
      "semantics":{"authoritative":False,"truth_assessed":False}
    }
    validate_observation(record)
    dest=store/"observations"/ident; dest.mkdir(parents=True,exist_ok=True)
    with (dest/(record["id"]+".json")).open("x",encoding="utf-8") as stream:
        json.dump(record,stream,indent=2); stream.write("\n")
    return record

def observations_for(store: Path, uri: str) -> list[dict]:
    """Return validated history ordered by observation time then ID.

    Ordering is deterministic, not a guarantee of causal order.
    """
    folder=Path(store).expanduser().resolve()/"observations"/trace_id(uri)
    if not folder.is_dir(): return []
    records=[]
    for path in folder.glob("*.json"):
        record=json.loads(path.read_text(encoding="utf-8"))
        if record.get("trace_uri") != uri: raise ValueError(f"Observation mismatch: {path.name}")
        records.append(validate_observation(record))
    return sorted(records,key=lambda x:(x["observed_at"],x["id"]))
