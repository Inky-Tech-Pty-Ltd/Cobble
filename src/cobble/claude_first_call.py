"""One-shot first live Claude call, fenced by operator approval and durable audit.

This experiment deliberately sends ONLY a fixed harmless hello. No inherited
memory, source path, previous exchange, or arbitrary prompt can be included.
It performs no network call unless the operator explicitly opts in, confirms
a vendor-side spending limit, and has a locally available API key.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import uuid

from cobble.claude_adapter import (
    ClaudeAdapter, MODEL, prepare_message, check_preflight,
)
from cobble.snug_exchange import ExchangeRequest, exchange

HELLO = "Hello, Helen. You are speaking to Snug's local memory steward. Please say hello in one sentence."
CONSENT = "I AUTHORIZE ONE CLAUDE API CALL"
FORMAT = "snug-first-live-attempt-1"


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


def _exclusive_record(path, data):
    """Owner-private append-only JSON via atomic hard link, never overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".claude-audit-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _summary(attempt_id, state, *, event=None):
    summary = {"attempt_id": attempt_id, "state": state, "provider": "claude",
               "model": MODEL, "inherited_memories_sent": 0}
    if event is not None:
        summary["event_id"] = event["event_id"]
        summary["usage"] = event["usage"]
    return summary


def first_live_hello(*, store, index, live=False, confirm=None,
                     workspace_limit_confirmed=False, api_key=None,
                     adapter=None):
    """Make at most one deliberately authorised real invocation.

    Adapter injection is for offline synthetic tests, NEVER the CLI.
    The marker remains after failures. A retry requires a separate
    operational investigation, not silently rerunning a charged call.
    """
    if live is not True or confirm != CONSENT:
        raise PermissionError("A live Claude call needs explicit operator consent")
    if workspace_limit_confirmed is not True:
        raise PermissionError("Confirm vendor-side workspace spending controls first")
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        raise PermissionError("No local Anthropic API key; no request attempted")
    store = Path(store).expanduser().resolve()
    index = Path(index).expanduser().resolve(strict=True)
    if not index.is_file():
        raise FileNotFoundError("Snug's private search index is missing")

    # Exact contract, no selected memories and no previous exchanges.
    request = ExchangeRequest(
        participant="operator", question=HELLO,
        selected_memories=(), previous_exchanges=())
    plan = check_preflight(prepare_message(request))

    root = store / "snug" / "provider-attempts"
    attempt_id = uuid.uuid4().hex
    started = {
        "format": FORMAT, "attempt_id": attempt_id,
        "created_utc": _timestamp(), "status": "attempted",
        "provider": "claude", "model": MODEL,
        "selected_memories": 0, "previous_exchanges": 0,
        "operator_confirmed_external_disclosure": True,
        "operator_confirmed_vendor_workspace_limit": True,
        "estimated_max_cost_usd": plan["estimated_max_cost_usd"],
        "cost_limit_note": "Estimate only; not a vendor hard spending cap",
        "actual_charge_usd": None,
    }
    # The one-shot marker is created BEFORE the provider can be contacted.
    # A crash or timeout leaves an unambiguous attempt requiring investigation.
    _exclusive_record(root / "first-live-claude.json", started)
    try:
        intelligence = adapter if adapter is not None else ClaudeAdapter(
            allow_network=True, key=api_key.strip())
        event = exchange(
            store=store, index=index, question=HELLO,
            participant="operator", provider="claude", adapter=intelligence,
            memory_ids=(), allowed_sources=(), prior_ids=())
        outcome = {
            "format": FORMAT, "attempt_id": attempt_id,
            "completed_utc": _timestamp(), "status": "completed",
            "event_id": event["event_id"], "provider_request_id":
                event["provider_request_id"],
            "usage": event["usage"], "actual_charge_usd": None,
            "billing_note": "Token-based amount is an estimate; check vendor billing",
        }
        _exclusive_record(root / (attempt_id + ".outcome.json"), outcome)
        return _summary(attempt_id, "completed", event=event)
    except Exception as exc:
        # Never copy arbitrary error text into the ledger: third-party errors
        # can include sensitive details. The cause class is sufficient.
        outcome = {
            "format": FORMAT, "attempt_id": attempt_id,
            "completed_utc": _timestamp(), "status": "outcome_unknown",
            "error_type": type(exc).__name__,
            "actual_charge_usd": None,
            "billing_note": "A failed or timed-out request may still incur charges",
        }
        _exclusive_record(root / (attempt_id + ".outcome.json"), outcome)
        raise


def first_call_status(store):
    """Inspect the one-shot marker and result without any network access."""
    root = Path(store).expanduser().resolve() / "snug" / "provider-attempts"
    marker = root / "first-live-claude.json"
    if not marker.exists():
        return {"reserved": False, "state": "never-attempted"}
    started = json.loads(marker.read_text(encoding="utf-8"))
    if started.get("format") != FORMAT:
        raise ValueError("Unrecognised first-call marker")
    attempt_id = started["attempt_id"]
    outcome_file = root / (attempt_id + ".outcome.json")
    state = "outcome_unknown"
    event_id = None
    if outcome_file.exists():
        outcome = json.loads(outcome_file.read_text(encoding="utf-8"))
        state = outcome.get("status", "outcome_unknown")
        event_id = outcome.get("event_id")
    return {"reserved": True, "state": state, "attempt_id": attempt_id,
            "event_id": event_id, "provider": "claude"}
