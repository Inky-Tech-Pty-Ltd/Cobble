"""Snug's private, offline provider-neutral conversation exchange.

Only explicitly chosen indexed passages and prior exchanges enter a request.
This first implementation offers two deterministic *fixtures*, not real AI
providers. It does not call a network API or modify the original corpus.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from cobble.local_search import SOURCES, show

MAX_QUESTION = 2000
MAX_CONTEXTS = 3
MAX_PRIOR = 4
MAX_PASSAGE = 1500
MAX_REPLY = 12000
EVENT = re.compile(r"[0-9a-f]{32}\Z")
DOCID = re.compile(r"[0-9a-f]{24}\Z")


@dataclass(frozen=True)
class ExchangeRequest:
    participant: str
    question: str
    selected_memories: tuple
    previous_exchanges: tuple


class FixtureIntelligence:
    """A test stand-in that can be replaced by a real adapter in later work."""

    def __init__(self, name):
        if name not in ("fixture-amber", "fixture-indigo"):
            raise ValueError("Unknown offline fixture intelligence")
        self.name = name

    def answer(self, request: ExchangeRequest):
        """No model or interpretation: report precisely what was supplied."""
        origins = ", ".join(sorted({item["source"]
                                     for item in request.selected_memories})) or "none"
        return (
            f"{self.name}: received {len(request.selected_memories)} selected "
            f"memory passage(s) from {origins}, plus "
            f"{len(request.previous_exchanges)} expressly supplied earlier "
            "exchange(s). This is an offline wiring test, not an AI answer."
        )


def _validate(question, participant, provider, memory_ids, allowed_sources, prior_ids):
    if not isinstance(question, str) or not 0 < len(question.strip()) <= MAX_QUESTION:
        raise ValueError("Question must have 1–2000 characters")
    if not isinstance(participant, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", participant):
        raise ValueError("Participant must be a short local identifier")
    if provider not in ("fixture-amber", "fixture-indigo", "claude", "mistral", "openai"):
        raise ValueError("Unsupported provider")
    if (not isinstance(memory_ids, (list, tuple)) or
            len(memory_ids) > MAX_CONTEXTS or len(set(memory_ids)) != len(memory_ids) or
            any(not isinstance(x, str) or not DOCID.fullmatch(x) for x in memory_ids)):
        raise ValueError("Expected up to three unique indexed memory IDs")
    if (not isinstance(prior_ids, (list, tuple)) or
            len(prior_ids) > MAX_PRIOR or len(set(prior_ids)) != len(prior_ids) or
            any(not isinstance(x, str) or not EVENT.fullmatch(x) for x in prior_ids)):
        raise ValueError("Expected up to four unique previous exchange IDs")
    if (not isinstance(allowed_sources, (set, list, tuple)) or
            any(source not in SOURCES for source in allowed_sources)):
        raise ValueError("Unknown permitted source")
    if memory_ids and not allowed_sources:
        raise PermissionError("No source has been explicitly authorised")


def _event_path(store, event_id):
    if not isinstance(event_id, str) or not EVENT.fullmatch(event_id):
        raise ValueError("Invalid event identifier")
    return store / "snug" / "events" / (event_id + ".json")


def read_event(store, event_id):
    path = _event_path(Path(store).expanduser().resolve(), event_id)
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError("Missing or unsafe exchange record")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("event_id") != event_id or record.get("format") != "snug-exchange-1":
        raise ValueError("Exchange record identity/format mismatch")
    return record


def _save_event(store, record):
    path = _event_path(store, record["event_id"])
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.exists() or path.is_symlink():
        raise FileExistsError("Exchange event already exists")
    encoded = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False)
               + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=".snug-event-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)  # no overwrite; never change past exchanges
    finally:
        Path(temporary).unlink(missing_ok=True)


def exchange(*, store, index, question, participant, provider,
             memory_ids=(), allowed_sources=(), prior_ids=(), adapter=None):
    """Explicitly scoped, one-shot private conversation; return an immutable event.

    Model-ready payload is built only from exact selected IDs. No automatic
    retrieval or ambient context is shared. Prior exchange history is opt-in.
    """
    _validate(question, participant, provider, memory_ids, allowed_sources, prior_ids)
    store = Path(store).expanduser().resolve()
    index = Path(index).expanduser().resolve(strict=True)
    allowed = set(allowed_sources)

    memories = []
    for docid in memory_ids:
        item = show(index, docid, max_chars=MAX_PASSAGE)
        if item["source"] not in allowed:
            raise PermissionError("Selected memory is outside authorised sources")
        text = item["text"]
        memories.append({
            "document_id": docid, "source": item["source"],
            "reference": item["reference"], "title": item["title"],
            "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "source_length": item["length"], "truncated": item["truncated"],
        })

    previous = [read_event(store, event_id) for event_id in prior_ids]
    prior_context = []
    for item in previous:
        prior_context.append({
            "event_id": item["event_id"], "provider": item["provider"],
            "participant": item["participant"], "question": item["question"],
            "answer": item["answer"],
        })

    request = ExchangeRequest(participant=participant, question=question,
                              selected_memories=tuple(memories),
                              previous_exchanges=tuple(prior_context))
    if provider in ("claude", "mistral", "openai") and adapter is None:
        raise PermissionError("Real provider adapter must be explicitly supplied")
    intelligence = adapter if adapter is not None else FixtureIntelligence(provider)
    if getattr(intelligence, "name", None) != provider:
        raise ValueError("Adapter identity mismatch")
    response = intelligence.answer(request)
    if provider in ("claude", "mistral", "openai"):
        # Real providers MUST return truthful accounting. Refuse any bare
        # string that could silently be recorded as an offline fixture.
        from cobble.claude_adapter import ProviderReply
        if not isinstance(response, ProviderReply):
            raise ValueError("Real provider must return an accounted reply")
        answer = response.text
        usage = response.usage
        expected_kinds = {
            "claude": ("anthropic-api", "mock-claude-api"),
            "mistral": ("mistral-api", "mock-mistral-api"),
            "openai": ("openai-api", "mock-openai-api"),
        }[provider]
        if (usage.get("kind") not in expected_kinds or
                type(usage.get("network_calls")) is not int or
                usage["network_calls"] not in (0, 1)):
            raise ValueError("Unrecognised provider accounting")
        model, request_id = response.model, response.request_id
    else:
        answer = response
        usage = {"network_calls": 0, "provider_cost": 0,
                 "kind": "offline-fixture"}
        model, request_id = None, None
    if not isinstance(answer, str) or not 0 < len(answer) <= MAX_REPLY:
        raise ValueError("Invalid or oversized intelligence answer")

    event = {
        "format": "snug-exchange-1",
        "event_id": uuid.uuid4().hex,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "participant": participant,
        "provider": provider,
        "question": question,
        "selected_memories": memories,
        "previous_exchange_ids": list(prior_ids),
        "answer": answer,
        "provider_model": model,
        "provider_request_id": request_id,
        "usage": usage,
    }
    _save_event(store, event)
    return event
