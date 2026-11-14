"""Review-only local demo seam over the existing private GitHub search index.

This first increment never invokes an external model. Approval constructs an
exactly scoped offline exchange, preserving source references and continuity.
The later live-call gate must audit attempts before any network transmission.
"""
from pathlib import Path
import re

from cobble.local_search import search, show
from cobble.snug_exchange import exchange, read_event, MAX_CONTEXTS, MAX_PRIOR

DOC_ID = re.compile(r"[a-f0-9]{24}\Z")
EVENT_ID = re.compile(r"[a-f0-9]{32}\Z")


class DemoService:
    def __init__(self, store, index):
        self.store = Path(store).expanduser().resolve()
        self.index = Path(index).expanduser().resolve(strict=True)
        for path in (self.store, self.index):
            if any((parent / ".git").exists() for parent in (path, *path.parents)):
                raise ValueError("Private demo store and index must stay outside Git")

    def find(self, query):
        # This inaugural demo is deliberately restricted to GitHub material.
        if not isinstance(query, str):
            raise ValueError("Query must be text")
        matches = search(self.index, query, limit=20)
        return [item for item in matches if item["source"] == "github"][:8]

    def inspect(self, document_id):
        if not isinstance(document_id, str) or not DOC_ID.fullmatch(document_id):
            raise ValueError("Invalid memory ID")
        item = show(self.index, document_id, max_chars=1500)
        if item["source"] != "github":
            raise PermissionError("Only GitHub memories are available to this demo")
        return {"id": document_id, **item}

    def reviewed_exchange(self, *, question, document_ids, previous_ids=(),
                          fixture="fixture-amber"):
        """Explicit local confirmation only; cannot transmit any memory."""
        if not isinstance(document_ids, (list, tuple)) or len(document_ids) > MAX_CONTEXTS:
            raise ValueError("At most three memory IDs")
        if len(set(document_ids)) != len(document_ids):
            raise ValueError("Duplicate memory selection")
        for document_id in document_ids:
            self.inspect(document_id)
        if (not isinstance(previous_ids, (list, tuple))
                or len(previous_ids) > MAX_PRIOR):
            raise ValueError("At most four previous exchanges")
        for event_id in previous_ids:
            if not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id):
                raise ValueError("Invalid previous exchange ID")
            read_event(self.store, event_id)
        if fixture not in ("fixture-amber", "fixture-indigo"):
            raise PermissionError("Live suppliers are not enabled in this first slice")
        return exchange(store=self.store, index=self.index,
                        question=question, participant="operator", provider=fixture,
                        memory_ids=document_ids,
                        allowed_sources=["github"] if document_ids else [],
                        prior_ids=previous_ids)
