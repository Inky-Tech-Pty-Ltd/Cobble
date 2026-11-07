"""One-shot GPT hello with immutable pre-call reservation and local audit.

The only permitted live payload is a fixed harmless greeting; no memory or
previous exchanges. CLI callers read the key on stdin after explicit consent.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import uuid

from cobble.openai_adapter import OpenAIAdapter, MODEL, prepare_message, check_preflight
from cobble.snug_exchange import ExchangeRequest, exchange
from cobble.mistral_first_call import _exclusive_record

HELLO = "Hello GPT. You are visiting Snug's locally owned memory workspace. Please greet Snug in one short sentence."
CONSENT = "I AUTHORIZE ONE OPENAI API CALL"
REVIEWED_CONSENT = "I AUTHORIZE ONE REVIEWED OPENAI RETRY"
REVIEWED_FORMAT = "snug-openai-reviewed-retry-1"
FORMAT = "snug-openai-first-live-1"


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _request():
    return ExchangeRequest(participant="operator", question=HELLO,
                           selected_memories=(), previous_exchanges=())


def first_call_status(store):
    root = Path(store).expanduser().resolve() / "snug" / "provider-attempts"
    marker = root / "first-live-openai.json"
    if marker.is_symlink():
        raise ValueError("Unsafe first-live marker")
    if not marker.is_file():
        return {"reserved": False, "state": "never-attempted", "provider": "openai"}
    started = json.loads(marker.read_text(encoding="utf-8"))
    if started.get("format") != FORMAT:
        raise ValueError("Unrecognised first-call marker")
    attempt_id = started["attempt_id"]
    outcome_file = root / (attempt_id + ".outcome.json")
    if outcome_file.is_symlink():
        raise ValueError("Unsafe first-call outcome")
    outcome = (json.loads(outcome_file.read_text(encoding="utf-8"))
               if outcome_file.is_file() else {})
    return {"reserved": True,
            "state": outcome.get("status", "outcome_unknown"),
            "attempt_id": attempt_id, "event_id": outcome.get("event_id"),
            "provider": "openai"}


def first_live_hello(*, store, index, live=False, confirm=None,
                     project_limit_confirmed=False, api_key=None, adapter=None,
                     reviewed_retry=False):
    required_consent = REVIEWED_CONSENT if reviewed_retry else CONSENT
    if live is not True or confirm != required_consent:
        raise PermissionError("OpenAI live call requires exact operator consent")
    if project_limit_confirmed is not True:
        raise PermissionError("Confirm OpenAI project limit before live call")
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        raise PermissionError("No local OpenAI API key; no request attempted")
    store = Path(store).expanduser().resolve()
    index = Path(index).expanduser().resolve(strict=True)
    if not index.is_file():
        raise FileNotFoundError("Private Snug search index is missing")
    if any((p / ".git").exists() for p in (store, *store.parents)):
        raise ValueError("Refusing to write inside a Git checkout")

    previous_attempt = None
    if reviewed_retry:
        previous = first_call_status(store)
        if not previous["reserved"] or previous["state"] != "outcome_unknown":
            raise PermissionError("Reviewed retry requires an unknown-outcome first attempt")
        previous_attempt = previous["attempt_id"]

    plan = check_preflight(prepare_message(_request()))
    root = store / "snug" / "provider-attempts"
    attempt_id = uuid.uuid4().hex
    marker = ("reviewed-retry-openai.json" if reviewed_retry
              else "first-live-openai.json")
    audit_format = REVIEWED_FORMAT if reviewed_retry else FORMAT
    _exclusive_record(root / marker, {
        "format": audit_format,
        "review_of_attempt_id": previous_attempt, "attempt_id": attempt_id, "created_utc": _utc(),
        "status": "attempted", "provider": "openai", "model": MODEL,
        "selected_memories": 0, "previous_exchanges": 0,
        "operator_confirmed_external_disclosure": True,
        "operator_confirmed_vendor_project_limit": True,
        "estimated_max_cost_usd": plan["estimated_max_cost_usd"],
        "actual_charge_usd": None,
        "cost_limit_note": "Local estimate; confirm amount in vendor billing",
    })
    try:
        intelligence = (adapter if adapter is not None else
                        OpenAIAdapter(allow_network=True, key=api_key.strip()))
        event = exchange(store=store, index=index, question=HELLO,
                         participant="operator", provider="openai",
                         adapter=intelligence, memory_ids=(),
                         allowed_sources=(), prior_ids=())
        _exclusive_record(root / (attempt_id + ".outcome.json"), {
            "format": audit_format, "attempt_id": attempt_id,
            "review_of_attempt_id": previous_attempt,
            "completed_utc": _utc(), "status": "completed",
            "event_id": event["event_id"],
            "provider_request_id": event["provider_request_id"],
            "usage": event["usage"], "actual_charge_usd": None,
            "billing_note": "Estimated tokens only; check actual invoice",
        })
        return {"attempt_id": attempt_id, "state": "completed",
                "review_of_attempt_id": previous_attempt, "provider": "openai", "model": MODEL,
                "inherited_memories_sent": 0, "event_id": event["event_id"],
                "usage": event["usage"]}
    except Exception as exc:
        _exclusive_record(root / (attempt_id + ".outcome.json"), {
            "format": audit_format, "attempt_id": attempt_id,
            "review_of_attempt_id": previous_attempt,
            "completed_utc": _utc(), "status": "outcome_unknown",
            "error_type": type(exc).__name__, "actual_charge_usd": None,
            "billing_note": "Provider may charge even if request fails",
        })
        raise
