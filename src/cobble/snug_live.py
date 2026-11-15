"""Durable, local, single-operator GPT boardroom session.

The accepted human turn and an immutable attempt record are fsynced *before*
the provider call. No automatic retries. Missing outcomes after a crash are
represented as uncertain, never silently discarded or resubmitted.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
import time

from cobble.claude_adapter import ProviderReply
from cobble.openai_adapter import OpenAIAdapter, check_preflight, prepare_message
from cobble.snug_exchange import ExchangeRequest, request_context_digest

TURN_ID = re.compile(r"[0-9]{20}-[0-9a-f]{12}\Z")
TTL_SECONDS = 300
MAX_PENDING = 16
MAX_QUESTION = 2000
MAX_PRIOR = 4
OUTPUT_TOKENS = 2048


class OutcomeUnknown(RuntimeError):
    """A request may have been processed by the provider; do not retry."""
    def __init__(self, turn_id):
        super().__init__("Outcome unknown. Inspect the retained turn; do not retry automatically.")
        self.turn_id = turn_id


class LiveChatService:
    def __init__(self, store, *, adapter=None):
        self.store = Path(store).expanduser().resolve()
        if any((p / ".git").exists() for p in (self.store, *self.store.parents)):
            raise ValueError("Private conversations must stay outside Git")
        self.root = self.store / "snug" / "live" / "default"
        self._lock = threading.Lock()
        self._pending = {}
        self._inflight = False
        self._adapter = adapter if adapter is not None else OpenAIAdapter(
            allow_network=True, output_tokens=OUTPUT_TOKENS)

    def _path(self, kind, turn_id):
        if kind not in ("turns", "attempts", "outcomes") or not TURN_ID.fullmatch(turn_id):
            raise ValueError("Invalid live event path")
        folder = self.root / kind
        if folder.is_symlink():
            raise PermissionError("Live event directory must not be a symlink")
        return folder / (turn_id + ".json")

    def _write(self, kind, turn_id, value):
        target = self._path(kind, turn_id)
        folder = target.parent
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        if folder.is_symlink() or target.exists() or target.is_symlink():
            raise FileExistsError("Live event record already exists or is unsafe")
        raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        fd, temp = tempfile.mkstemp(prefix=".pending-", dir=folder)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temp, target)  # Publish completely written record, never overwrite.
            folder_fd = os.open(folder, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(folder_fd)
            finally:
                os.close(folder_fd)
        finally:
            Path(temp).unlink(missing_ok=True)

    def _read(self, kind, turn_id):
        path = self._path(kind, turn_id)
        if path.is_symlink() or not path.is_file():
            return None
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("turn_id") != turn_id:
            raise ValueError("Live event identity mismatch")
        return result

    def _turns(self):
        folder = self.root / "turns"
        if folder.is_symlink():
            raise PermissionError("Unsafe live history directory")
        if not folder.exists():
            return []
        turns = []
        for p in sorted(folder.glob("*.json")):
            if not TURN_ID.fullmatch(p.stem) or p.is_symlink():
                raise ValueError("Unsafe live event in session")
            start = self._read("turns", p.stem)
            attempt = self._read("attempts", p.stem)
            outcome = self._read("outcomes", p.stem)
            status = outcome["status"] if outcome else (
                "outcome_unknown" if attempt else "saved_not_sent")
            turns.append({
                "turn_id": p.stem,
                "created_utc": start["created_utc"],
                "provider": start["provider"],
                "question": start["question"],
                "context_sha256": start["context_sha256"],
                "context": start["context"],
                "status": status,
                "answer": outcome.get("answer") if outcome else None,
                "usage": outcome.get("usage") if outcome else None,
                "model": outcome.get("model") if outcome else None,
                "provider_request_id": outcome.get("provider_request_id") if outcome else None,
            })
        return turns

    def session(self):
        with self._lock:
            return {"turns": self._turns()[-100:],
                    "live_provider": "openai", "inflight": self._inflight}

    def _history(self, turns):
        return tuple({
            "event_id": turn["turn_id"],
            "provider": turn["provider"],
            "participant": "operator",
            "question": turn["question"],
            "answer": turn["answer"],
        } for turn in turns if turn["status"] == "completed")[-MAX_PRIOR:]

    def preview(self, *, question):
        if not isinstance(question, str) or not 0 < len(question.strip()) <= MAX_QUESTION:
            raise ValueError("Question must contain 1–2000 characters")
        with self._lock:
            turns = self._turns()
            history = self._history(turns)
            request = ExchangeRequest(
                participant="operator", question=question,
                selected_memories=(), previous_exchanges=history)
            payload = prepare_message(request, output_tokens=OUTPUT_TOKENS)
            budget = check_preflight(payload)
            token = secrets.token_urlsafe(32)
            now = time.monotonic()
            self._pending = {
                k: v for k, v in self._pending.items() if now - v[0] <= TTL_SECONDS
            }
            if len(self._pending) >= MAX_PENDING:
                raise PermissionError("Too many unconsumed previews")
            latest_id = turns[-1]["turn_id"] if turns else None
            self._pending[token] = (now, request, payload, latest_id)
            return {
                "approval_token": token,
                "provider": "openai", "question": question,
                "selected_memories": [],
                "previous_exchanges": list(history),
                "context_sha256": request_context_digest(request),
                "outbound_payload_sha256": _digest(payload),
                "preflight": budget,
                "network_calls_if_approved": 1,
            }

    def send(self, *, approval_token):
        if not isinstance(approval_token, str) or len(approval_token) > 128:
            raise PermissionError("Exact one-time approval token required")
        with self._lock:
            entry = self._pending.pop(approval_token, None)
            if entry is None:
                raise PermissionError("Approval absent or already consumed")
            issued, request, payload, previous_last = entry
            if time.monotonic() - issued > TTL_SECONDS:
                raise PermissionError("Review expired; preview again")
            if self._inflight:
                raise PermissionError("Another live request is underway")
            turns = self._turns()
            latest = turns[-1]["turn_id"] if turns else None
            if latest != previous_last:
                raise PermissionError("Conversation changed after review; preview again")
            # Refuse a missing key BEFORE saving any outbound attempt.
            # Injected adapter is permitted only in offline unit tests.
            if isinstance(self._adapter, OpenAIAdapter) and not (
                self._adapter.key or os.environ.get("OPENAI_API_KEY")
            ):
                raise PermissionError("OPENAI_API_KEY is not configured on McKay")
            self._inflight = True

        turn_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f") + "-" + secrets.token_hex(6)
        accepted = False
        try:
            self._write("turns", turn_id, {
                "turn_id": turn_id, "created_utc": datetime.now(timezone.utc).isoformat(),
                "provider": "openai", "question": request.question,
                "context_sha256": request_context_digest(request),
                "context": asdict(request), "payload": payload,
                "outbound_payload_sha256": _digest(payload),
            })
            accepted = True
            self._write("attempts", turn_id, {
                "turn_id": turn_id, "provider": "openai",
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "outbound_payload_sha256": _digest(payload),
                "kind": "network_attempt_may_have_occurred",
            })
            reply = self._adapter.answer(request)
            if (not isinstance(reply, ProviderReply)
                or reply.usage.get("kind") not in ("openai-api", "mock-openai-api")
                or not isinstance(reply.text, str) or not reply.text.strip()
                or len(reply.text) > 12000):
                raise ValueError("Unaccounted or invalid GPT reply")
            self._write("outcomes", turn_id, {
                "turn_id": turn_id, "status": "completed",
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "answer": reply.text, "usage": reply.usage,
                "model": reply.model, "provider_request_id": reply.request_id,
            })
            return {"turn": self._turns_by_id(turn_id)}
        except Exception:
            if accepted:
                try:
                    self._write("outcomes", turn_id, {
                        "turn_id": turn_id, "status": "outcome_unknown",
                        "recorded_utc": datetime.now(timezone.utc).isoformat(),
                        "reason": "Call did not yield a verified retained completion; no auto retry",
                    })
                except FileExistsError:
                    pass  # A complete outcome may already exist.
                except OSError:
                    pass  # The accepted turn and attempt remain on disk.
                raise OutcomeUnknown(turn_id) from None
            raise
        finally:
            with self._lock:
                self._inflight = False

    def _turns_by_id(self, turn_id):
        # No lock here; called during completion before releasing _inflight.
        return next(t for t in self._turns() if t["turn_id"] == turn_id)


def _digest(payload):
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()
