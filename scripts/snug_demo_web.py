"""Run Cobble's meetings workspace on loopback, offline by default.

Live supplier access is explicit, per-supplier, and uses the shared private
conversation ledger; keys remain only in local server process memory.
"""
import argparse
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys
import threading
from urllib.parse import parse_qs, urlsplit

from cobble.openai_adapter import OpenAIAdapter
from cobble.claude_adapter import ClaudeAdapter
from cobble.mistral_adapter import MistralAdapter
from pathlib import Path

from cobble.snug_demo import DemoService
from cobble.snug_live import LiveChatService, OutcomeUnknown
from cobble.meeting_rooms import MeetingCatalog, DEFAULT_ORDERS
from cobble.meeting_door import MeetingDoor
from cobble.instance_identity import load as load_instance, require_index
from cobble.puck_meeting_bridge import bind_invitation, unbind_invitation

STATIC = Path(__file__).resolve().parent.parent / "src" / "cobble" / "static"
HTML = STATIC / "workbench.html"
BOARDROOM_HTML = STATIC / "snug_demo.html"
GUEST_HTML = STATIC / "guest_room.html"
LOGO = Path(__file__).resolve().parent.parent / "docs" / "assets" / "cobble-logo.png"
MAX_BYTES = 8192


def create_server(store, index, port=8766, *, live_gpt=False,
                  live_claude=False, live_mistral=False,
                  live_adapter=None, live_adapters=None, guest_port=None):
    identity = load_instance(Path(store).expanduser().resolve())
    operator_name = identity["name"] if identity else "Joe"
    if identity:
        require_index(store, index)
    service = DemoService(store, index)
    requested = {
        name for name, enabled in (("openai", live_gpt),
                                   ("claude", live_claude),
                                   ("mistral", live_mistral)) if enabled
    }
    if live_adapter is not None and (not live_gpt or live_adapters is not None):
        raise ValueError("Legacy adapter requires live_gpt and no adapter mapping")
    if live_adapters is not None and set(live_adapters) != requested:
        raise ValueError("Enabled suppliers must match configured adapters")
    if live_adapters is not None:
        adapters = dict(live_adapters)
    else:
        adapters = {}
        if live_gpt:
            adapters["openai"] = (live_adapter if live_adapter is not None else
                                  OpenAIAdapter(allow_network=True, output_tokens=2048))
        if live_claude:
            adapters["claude"] = ClaudeAdapter(allow_network=True, output_tokens=2048)
        if live_mistral:
            adapters["mistral"] = MistralAdapter(allow_network=True, output_tokens=2048)
    # The legacy boardroom retains the default room's original ledger.
    catalog = MeetingCatalog(store)
    door = MeetingDoor(store, convenor=operator_name)
    live_sessions = {"default": LiveChatService(store, adapters=adapters,
                                                   operator_name=operator_name)}
    live_lock = threading.Lock()

    def room_session(room_id="default"):
        catalog.require(room_id)
        with live_lock:
            if room_id not in live_sessions:
                live_sessions[room_id] = LiveChatService(
                    store, adapters=adapters, meeting_id=room_id,
                    operator_name=operator_name)
            return live_sessions[room_id]

    def rooms_with_accounting():
        """One server-owned snapshot for all rooms, including unopened ones."""
        listed = catalog.list()
        total = Decimal("0")
        rooms = []
        for room in listed:
            estimated = room_session(room["id"]).recorded_estimated_cost_usd()
            rooms.append({**room, "estimated_cost_usd": estimated})
            total += Decimal(estimated)
        return {"rooms": rooms, "estimated_total_usd": format(total, "f"),
                "default_standing_orders": DEFAULT_ORDERS}

    # Serialize governance transitions and live actions in this single local server.
    # This is not a multi-process or multi-user authorization mechanism.
    governance_lock = threading.RLock()

    def contributions(events):
        """Stable utterance IDs; legacy bare IDs retain their original meaning."""
        for e in events:
            base = e["turn_id"]
            if e["provider"] != "operator" and isinstance(e["question"], str) and e["question"].strip():
                yield {"turn_id": base + ":question", "provider": "operator",
                       "speaker": e.get("speaker", "Joe"), "text": e["question"]}
            if e["status"] == "posted" and e["provider"] == "operator":
                yield {"turn_id": base, "provider": "operator",
                       "speaker": e.get("speaker", "Joe"), "text": e["question"]}
            elif e["provider"] != "operator" and e["status"] == "completed" and isinstance(e["answer"], str) and e["answer"].strip():
                yield {"turn_id": base, "provider": e["provider"],
                       "speaker": e["provider"], "text": e["answer"]}

    def room_output(meeting_id):
        item = next(r for r in catalog.list() if r["id"] == catalog.require(meeting_id))
        if item.get("state") == "closed":
            raise PermissionError("Closed meeting output is unavailable")
        events = room_session(meeting_id).complete_history()
        selected = set(item.get("room_voice", [])) - set(item.get("redacted", []))
        available = {c["turn_id"]: c for c in contributions(events)}
        if not selected.issubset(available):
            raise ValueError("Room voice contains unavailable or ineligible evidence")
        # The convenor owns the agenda, even for an early experimental room
        # where a guest happened to post before Joe. Never elevate guest
        # speech to the room's opening agenda by accident.
        agenda_turn = next((e for e in events if e["provider"] == "operator"
                            and e.get("speaker", "Joe") == operator_name), None)
        if agenda_turn is None:
            agenda_turn = next((e for e in events
                                if e.get("speaker", "Joe") == operator_name), None)
        return {"agenda": agenda_turn["question"] if agenda_turn else "",
                "contributions": [c for key, c in available.items() if key in selected]}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass  # Never log user prompts or selected memories.

        def reply(self, status, value, content_type="application/json; charset=utf-8"):
            raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'; img-src 'self'; "
                             "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def trusted(self):
            origin = f"http://127.0.0.1:{self.server.server_port}"
            alternate = f"http://localhost:{self.server.server_port}"
            if self.headers.get("Host") not in (origin[7:], alternate[7:]):
                self.reply(403, {"error": "Local host only"})
                return False
            if self.command == "POST" and (
                self.headers.get("Origin") not in (origin, alternate)
                or self.headers.get("X-Snug-Client") != "demo-local"
            ):
                self.reply(403, {"error": "Same-origin operator console required"})
                return False
            return True

        def do_GET(self):
            if not self.trusted():
                return
            if self.path == "/":
                self.reply(200, HTML.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/boardroom":
                self.reply(200, BOARDROOM_HTML.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/assets/cobble-logo.png":
                self.reply(200, LOGO.read_bytes(), "image/png")
            elif self.path == "/api/health":
                self.reply(200, {"ok": True, "live_suppliers": bool(requested),
                                 "live_gpt": "openai" in requested,
                                 "live_providers": [p for p in ("openai", "claude", "mistral")
                                                    if p in requested],
                                 "source": "github", "instance": identity,
                                 "operator_name": operator_name})
            elif self.path == "/api/live/rooms":
                try:
                    with governance_lock:
                        snapshot = rooms_with_accounting()
                    self.reply(200, snapshot)
                except (ValueError, PermissionError, OSError) as error:
                    self.reply(400, {"error": str(error)})
            elif urlsplit(self.path).path == "/api/live/rooms/door":
                try:
                    query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
                    if set(query) != {"room_id"} or len(query["room_id"]) != 1:
                        raise ValueError("One room ID required")
                    with governance_lock:
                        room_id = catalog.require(query["room_id"][0])
                        result = (door.status(room_id=room_id) if operator_name != "Sankarshan"
                                  else {"room_id": room_id, "open": False, "arrived": False, "expires_utc": None})
                        result["puck"] = (door.status(room_id=room_id, speaker="Puck")
                                          if operator_name != "Puck" else
                                          {"room_id": room_id, "open": False, "arrived": False, "expires_utc": None})
                    self.reply(200, result)
                except (ValueError, PermissionError, OSError, TypeError) as error:
                    self.reply(400, {"error": str(error)})
            elif urlsplit(self.path).path == "/api/live/output":
                try:
                    query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
                    if set(query) - {"room_id"} or len(query.get("room_id", [])) > 1:
                        raise ValueError("Invalid room selector")
                    meeting_id = query.get("room_id", ["default"])[0]
                    with governance_lock:
                        output = room_output(meeting_id)
                    self.reply(200, output)
                except (ValueError, PermissionError, OSError, StopIteration) as error:
                    self.reply(400, {"error": str(error)})
            elif urlsplit(self.path).path == "/api/live/session":
                try:
                    query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
                    if set(query) - {"room_id"} or len(query.get("room_id", [])) > 1:
                        raise ValueError("Invalid room selector")
                    meeting_id = query.get("room_id", ["default"])[0]
                    self.reply(200, room_session(meeting_id).session())
                except (ValueError, PermissionError, OSError, TypeError) as error:
                    self.reply(400, {"error": str(error)})
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if self.path.startswith('/api/live/'):
                with governance_lock:
                    return self._post()
            return self._post()

        def _post(self):
            if not self.trusted():
                return
            if self.path not in ("/api/search", "/api/inspect", "/api/preview", "/api/exchange",
                                 "/api/live/preview", "/api/live/send", "/api/live/post",
                                  "/api/live/rooms/create", "/api/live/rooms/rename",
                                  "/api/live/rooms/configure", "/api/live/rooms/invite",
                                  "/api/live/rooms/revoke"):
                self.reply(404, {"error": "Not found"})
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.reply(415, {"error": "JSON body required"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 0
            if not 0 < size <= MAX_BYTES:
                self.reply(413, {"error": "Invalid request size"})
                return
            try:
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Expected an object")
                if self.path == "/api/search":
                    result = {"results": service.find(data.get("query"))}
                elif self.path == "/api/inspect":
                    result = service.inspect(data.get("id"))
                elif self.path == "/api/preview":
                    result = service.preview_exchange(
                        question=data.get("question"),
                        document_ids=data.get("memory_ids"),
                        previous_ids=data.get("previous_ids", []),
                        fixture=data.get("provider", "fixture-amber"))
                elif self.path == "/api/exchange":
                    if set(data) != {"approval_token"}:
                        raise PermissionError("Execute only a reviewed one-shot approval")
                    result = service.reviewed_exchange(
                        approval_token=data["approval_token"])
                elif self.path == "/api/live/rooms/create":
                    if set(data) != {"title"}:
                        raise PermissionError("Only a new room title is accepted")
                    result = catalog.create(title=data["title"])
                elif self.path == "/api/live/rooms/rename":
                    if set(data) != {"room_id", "title"}:
                        raise PermissionError("Room ID and title required")
                    result = catalog.rename(meeting_id=data["room_id"],
                                            title=data["title"])
                elif self.path == "/api/live/rooms/configure":
                    permitted = {"room_id", "standing_orders", "state", "precedence",
                                 "voice_event", "redact_event"}
                    if "room_id" not in data or set(data) - permitted:
                        raise PermissionError("Invalid meeting configuration")
                    meeting_id = data.pop("room_id")
                    if "voice_event" in data and "redact_event" in data:
                        raise ValueError("Select or redact one contribution at a time")
                    session = room_session(meeting_id)
                    if "voice_event" in data or "redact_event" in data:
                        event_id = data.get("voice_event", data.get("redact_event"))
                        if not any(c["turn_id"] == event_id
                                   for c in contributions(session.complete_history())):
                            raise ValueError("Contribution is not eligible in this meeting")
                    result = catalog.configure(meeting_id=meeting_id, **data)
                    session.invalidate_previews()
                elif self.path == "/api/live/rooms/invite":
                    if set(data) not in ({"room_id"}, {"room_id", "speaker"}, {"room_id", "speaker", "mode"}):
                        raise PermissionError("Only room ID, guest seat and optional peer mode may be provided")
                    speaker = data.get("speaker", "Sankarshan")
                    peer = data.get("mode") == "peer"
                    if "mode" in data and (not peer or not identity):
                        raise PermissionError("Peer mode requires a named host instance")
                    if speaker == "Puck" and not peer and operator_name != "Joe":
                        raise PermissionError("Legacy Puck bridge belongs to Joe-hosted rooms only")
                    if guest_server is None:
                        raise PermissionError("Room guest Door is disabled on this local server")
                    meeting_id = catalog.require(data["room_id"])
                    room = next(r for r in catalog.list() if r["id"] == meeting_id)
                    if room.get("state") == "closed":
                        raise PermissionError("Reopen the meeting before issuing an invitation")
                    issued = door.issue(room_id=meeting_id, speaker=speaker)
                    if speaker == "Puck" and not peer:
                        try:
                            bind_invitation(store, meeting_id, guest_server.server_port, issued["token"])
                        except Exception:
                            door.revoke(room_id=meeting_id, speaker="Puck")
                            raise
                        result = {"room_id": meeting_id, "speaker": speaker,
                                  "expires_utc": issued["expires_utc"]}
                    else:
                        result = {
                            "guest_url": f"http://127.0.0.1:{guest_server.server_port}/"
                                         f"#invite={issued['token']}",
                            "expires_utc": issued["expires_utc"], "room_id": meeting_id,
                            "notice": f"Anyone holding this link may speak as {speaker} in this one room.",
                        }
                        if peer:
                            result.update({"speaker": speaker, "host_instance_id": identity["instance_id"]})
                elif self.path == "/api/live/rooms/revoke":
                    if set(data) not in ({"room_id"}, {"room_id", "speaker"}):
                        raise PermissionError("Only room ID and guest seat may be provided")
                    speaker = data.get("speaker", "Sankarshan")
                    meeting_id = catalog.require(data["room_id"])
                    result = door.revoke(room_id=meeting_id, speaker=speaker)
                    if speaker == "Puck":
                        unbind_invitation(store, meeting_id)
                elif self.path == "/api/live/post":
                    if next(r for r in catalog.list() if r["id"] == catalog.require(data.get("room_id", "default"))).get("state") == "closed":
                        raise PermissionError("Reopen the meeting before contributing")
                    if set(data) not in ({"text"}, {"text", "room_id"}):
                        raise PermissionError("Only a local operator message and room ID may be posted")
                    result = room_session(data.get("room_id", "default")).post_operator(text=data["text"])
                elif self.path == "/api/live/preview":
                    if next(r for r in catalog.list() if r["id"] == catalog.require(data.get("room_id", "default"))).get("state") == "closed":
                        raise PermissionError("Reopen the meeting before consulting a supplier")
                    if not requested:
                        raise PermissionError("Live supplier access is disabled")
                    if ("question" not in data or
                        set(data) - {"question", "provider", "room_id"}):
                        raise PermissionError("Only question, supplier and room ID may be reviewed")
                    meeting_id = data.get("room_id", "default")
                    room_info = next(r for r in catalog.list()
                                     if r["id"] == catalog.require(meeting_id))
                    result = room_session(meeting_id).preview(
                        question=data["question"], provider=data.get("provider", "openai"),
                        room_standing_orders=room_info.get("standing_orders", DEFAULT_ORDERS),
                        room_output=room_output(meeting_id))
                else:
                    if next(r for r in catalog.list() if r["id"] == catalog.require(data.get("room_id", "default"))).get("state") == "closed":
                        raise PermissionError("Reopen the meeting before consulting a supplier")
                    if not requested:
                        raise PermissionError("Live supplier access is disabled")
                    if ("approval_token" not in data or
                        set(data) - {"approval_token", "room_id"}):
                        raise PermissionError("Only the exact one-time live approval is accepted")
                    result = room_session(data.get("room_id", "default")).send(
                        approval_token=data["approval_token"])
                self.reply(200, result)
            except OutcomeUnknown as error:
                self.reply(502, {"error": str(error), "turn_id": error.turn_id,
                                 "outcome_unknown": True})
            except (ValueError, TypeError, KeyError, PermissionError) as error:
                self.reply(400, {"error": str(error)})
            except (OSError, RuntimeError):
                self.reply(503, {"error": "Private local data unavailable"})

    class GuestHandler(BaseHTTPRequestHandler):
        """A different HTTP surface: no route reaches the operator API."""

        def log_message(self, fmt, *args):
            pass  # Never log invitations, messages or identities.

        def reply(self, code, data, content_type="application/json; charset=utf-8"):
            raw = data if isinstance(data, bytes) else json.dumps(
                data, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'; "
                             "base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)

        def guard(self):
            port = self.server.server_port
            hosts = (f"127.0.0.1:{port}", f"localhost:{port}")
            if self.headers.get("Host") not in hosts:
                raise PermissionError("Unrecognised guest host")
            if self.command == "POST":
                origins = (f"http://{hosts[0]}", f"http://{hosts[1]}")
                if self.headers.get("Origin") not in origins:
                    raise PermissionError("Guest origin not recognised")
                if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    raise ValueError("JSON body required")
            return door.require(self.headers.get("X-Cobble-Room-Token"))

        def do_GET(self):
            if self.path == "/":
                self.reply(200, GUEST_HTML.read_bytes(), "text/html; charset=utf-8")
                return
            if self.path != "/api/guest/session":
                self.reply(404, {"error": "Not found"})
                return
            try:
                with governance_lock:
                    admit = self.guard()
                    room_id = catalog.require(admit["room_id"])
                    meeting = next(r for r in catalog.list() if r["id"] == room_id)
                    if meeting.get("state") == "closed":
                        raise PermissionError("This meeting is closed")
                    history = room_session(room_id).complete_history()
                    # A successful view is admission, not evidence of who
                    # holds the bearer invitation.
                    door.require(self.headers.get("X-Cobble-Room-Token"),
                                 mark_arrival=True)
                    convenor_started = any(
                        t["provider"] == "operator" and
                        t.get("speaker", "Joe") == operator_name and
                        t["status"] == "posted" for t in history)
                    projection = [{
                        "turn_id": t["turn_id"],
                        "created_utc": t["created_utc"],
                        "status": t["status"],
                        "speaker": t["speaker"],
                        "provider": t["provider"],
                        "question": t["question"],
                        "answer": t["answer"] if t["status"] == "completed" else None,
                        "authorised_question": (t["turn_id"] if t["provider"] == "operator"
                                                else t["turn_id"] + ":question") in
                            (set(meeting.get("room_voice", [])) -
                             set(meeting.get("redacted", []))),
                        "authorised_voice": t["turn_id"] in
                            (set(meeting.get("room_voice", [])) -
                             set(meeting.get("redacted", []))),
                    } for t in history]
                    result = {
                        "meeting": {
                            "id": room_id, "title": meeting["title"],
                            "state": meeting.get("state", "open"),
                            "standing_orders": meeting.get("standing_orders", DEFAULT_ORDERS),
                            "convenor_started": convenor_started,
                        },
                        "speaker": admit["speaker"],
                        "host_instance_id": identity["instance_id"] if identity else None,
                        "turns": projection, "room_output": room_output(room_id),
                    }
                self.reply(200, result)
            except (ValueError, PermissionError, OSError, TypeError, StopIteration):
                self.reply(403, {"error": "Room invitation invalid or unavailable"})

        def do_POST(self):
            if self.path != "/api/guest/post":
                self.reply(404, {"error": "Not found"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= MAX_BYTES:
                    raise ValueError("Invalid guest message size")
                with governance_lock:
                    admit = self.guard()
                    data = json.loads(self.rfile.read(size))
                    if not isinstance(data, dict) or set(data) != {"text"}:
                        raise ValueError("Only a meeting contribution may be posted")
                    room_id = catalog.require(admit["room_id"])
                    meeting = next(r for r in catalog.list() if r["id"] == room_id)
                    if meeting.get("state") == "closed":
                        raise PermissionError("This meeting is closed")
                    history = room_session(room_id).complete_history()
                    if not any(t["provider"] == "operator" and
                               t.get("speaker", "Joe") == operator_name and
                               t["status"] == "posted" for t in history):
                        raise PermissionError("Waiting for convenor's opening agenda")
                    outcome = room_session(room_id).post_operator(
                        text=data["text"], speaker=admit["speaker"])
                self.reply(200, {"turn_id": outcome["turn"]["turn_id"],
                                 "speaker": admit["speaker"]})
            except (ValueError, PermissionError, TypeError, KeyError, OSError, StopIteration):
                self.reply(403, {"error": "Guest contribution refused"})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    guest_server = None
    if guest_port is not None:
        try:
            guest_server = ThreadingHTTPServer(("127.0.0.1", guest_port), GuestHandler)
        except Exception:
            server.server_close()
            raise
    server.guest_server = guest_server
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--guest-port", type=int, default=None,
                        help="Optional local-only separate guest Door port; never expose operator port")
    parser.add_argument("--live-gpt", action="store_true",
                        help="Enable paid GPT API calls")
    parser.add_argument("--live-claude", action="store_true",
                        help="Enable paid Claude API calls")
    parser.add_argument("--live-mistral", action="store_true",
                        help="Enable paid Mistral API calls")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--key-stdin", action="store_true",
                       help="Read one GPT key from stdin (legacy GPT-only setup)")
    group.add_argument("--keys-json-stdin", action="store_true",
                       help="Read a JSON object of provider keys from stdin")
    args = parser.parse_args()
    enabled = {
        name for name, active in (("openai", args.live_gpt),
                                  ("claude", args.live_claude),
                                  ("mistral", args.live_mistral)) if active
    }
    if args.key_stdin and enabled != {"openai"}:
        parser.error("--key-stdin supports only --live-gpt; use --keys-json-stdin for multiple suppliers")
    if args.keys_json_stdin and not enabled:
        parser.error("--keys-json-stdin requires a live supplier")
    config = {
        "openai": (OpenAIAdapter, "OPENAI_API_KEY"),
        "claude": (ClaudeAdapter, "ANTHROPIC_API_KEY"),
        "mistral": (MistralAdapter, "MISTRAL_API_KEY"),
    }
    credentials = {}
    if args.key_stdin:
        key = sys.stdin.read(4096).strip()
        if not 1 <= len(key) <= 512:
            parser.error("Invalid GPT key from stdin")
        credentials = {"openai": key}
    elif args.keys_json_stdin:
        raw = sys.stdin.read(8193)
        if len(raw) > 8192:
            parser.error("Too much credential input")
        try:
            supplied = json.loads(raw)
        except (ValueError, TypeError):
            parser.error("Expected a JSON credential object")
        if not isinstance(supplied, dict) or set(supplied) != enabled:
            parser.error("Credential keys must exactly match selected live suppliers")
        if any(not isinstance(value, str) or
               not 1 <= len(value.strip()) <= 512 or
               "\n" in value or "\r" in value
               for value in supplied.values()):
            parser.error("Invalid local credential data")
        credentials = {name: value.strip() for name, value in supplied.items()}

    for name in enabled:
        if not credentials.get(name) and not os.environ.get(config[name][1]):
            parser.error("Missing configured credential for " + name +
                         " (use local environment or stdin)")
    adapters = {
        name: config[name][0](allow_network=True,
                              key=credentials.get(name),
                              output_tokens=2048)
        for name in enabled
    }
    index = args.index or args.store / "index" / "search.sqlite3"
    with create_server(args.store, index, args.port,
                       live_gpt=args.live_gpt, live_claude=args.live_claude,
                       live_mistral=args.live_mistral,
                       live_adapters=adapters if enabled else None,
                       guest_port=args.guest_port) as server:
        description = ", ".join(name for name in ("openai", "claude", "mistral")
                                if name in enabled) if enabled else "offline"
        print(f"Cobble meetings ({description}): http://127.0.0.1:{server.server_port}/", flush=True)
        print("Live calls require one-time exact context review." if enabled else
              "No external supplier calls; only approved fixture exchanges.", flush=True)
        thread = None
        if server.guest_server is not None:
            thread = threading.Thread(target=server.guest_server.serve_forever,
                                      daemon=True)
            thread.start()
            print(f"Guest Door (LOCAL ONLY): "
                  f"http://127.0.0.1:{server.guest_server.server_port}/", flush=True)
            print("DO NOT expose the operator port; remote HTTPS is not configured.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            if server.guest_server is not None:
                server.guest_server.shutdown()
                server.guest_server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    main()
