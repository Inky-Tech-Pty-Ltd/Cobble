"""Loopback-only, offline preview and one-shot fixture approval for Snug.

A preview captures the exact request including earlier exchange text. The
server executes that reviewed snapshot, not another read of mutable sources.
This is not authorisation to contact any external intelligence supplier.
"""
from pathlib import Path
import secrets
import threading
import time

from cobble.local_search import search, show
from cobble.snug_exchange import (
    exchange, prepare_exchange_request, MAX_CONTEXTS, MAX_PRIOR,
)

APPROVAL_TTL_SECONDS = 300
MAX_PENDING_APPROVALS = 32


class DemoService:
    def __init__(self, store, index):
        self.store = Path(store).expanduser().resolve()
        self.index = Path(index).expanduser().resolve(strict=True)
        for path in (self.store, self.index):
            if any((parent / ".git").exists() for parent in (path, *path.parents)):
                raise ValueError("Private demo store and index must stay outside Git")
        self._pending = {}
        self._lock = threading.Lock()

    def find(self, query):
        if not isinstance(query, str):
            raise ValueError("Query must be text")
        matches = search(self.index, query, limit=20)
        return [item for item in matches if item["source"] == "github"][:8]

    def inspect(self, document_id):
        # Let the indexed reader validate the ID and locate the record.
        if not isinstance(document_id, str):
            raise ValueError("Invalid memory ID")
        item = show(self.index, document_id, max_chars=1500)
        if item["source"] != "github":
            raise PermissionError("Only GitHub memories are available to this demo")
        return {"id": document_id, **item}

    def preview_exchange(self, *, question, document_ids, previous_ids=(),
                         fixture="fixture-amber"):
        if fixture not in ("fixture-amber", "fixture-indigo"):
            raise PermissionError("Only offline fixture suppliers are permitted")
        if (not isinstance(document_ids, (list, tuple)) or
                len(document_ids) > MAX_CONTEXTS):
            raise ValueError("At most three memory IDs")
        if (not isinstance(previous_ids, (list, tuple)) or
                len(previous_ids) > MAX_PRIOR):
            raise ValueError("At most four previous exchanges")
        for document_id in document_ids:
            self.inspect(document_id)
        request = prepare_exchange_request(
            store=self.store, index=self.index, question=question,
            participant="operator", provider=fixture,
            memory_ids=document_ids,
            allowed_sources=["github"] if document_ids else [],
            prior_ids=previous_ids)
        token = secrets.token_urlsafe(32)
        with self._lock:
            now = time.monotonic()
            self._pending = {
                key: value for key, value in self._pending.items()
                if now - value[0] <= APPROVAL_TTL_SECONDS
            }
            if len(self._pending) >= MAX_PENDING_APPROVALS:
                raise PermissionError("Too many pending previews; retry later")
            self._pending[token] = (now, fixture, request)
        return {
            "approval_token": token,
            "question": request.question,
            "provider": fixture,
            "selected_memories": list(request.selected_memories),
            "previous_exchanges": list(request.previous_exchanges),
            "network_calls": 0,
        }

    def reviewed_exchange(self, *, approval_token):
        if not isinstance(approval_token, str) or len(approval_token) > 128:
            raise PermissionError("A valid reviewed approval token is required")
        # Consume the approval before performing any operation: replay or
        # concurrent duplicate requests never create multiple events.
        with self._lock:
            entry = self._pending.pop(approval_token, None)
        if entry is None:
            raise PermissionError("Approval not found or already consumed")
        issued, fixture, request = entry
        if time.monotonic() - issued > APPROVAL_TTL_SECONDS:
            raise PermissionError("Approval expired; review the context again")
        memory_ids = [m["document_id"] for m in request.selected_memories]
        previous_ids = [p["event_id"] for p in request.previous_exchanges]
        return exchange(
            store=self.store, index=self.index, question=request.question,
            participant=request.participant, provider=fixture,
            memory_ids=memory_ids, prior_ids=previous_ids,
            allowed_sources=["github"] if memory_ids else [],
            prepared_request=request)
