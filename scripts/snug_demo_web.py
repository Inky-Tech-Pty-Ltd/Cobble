"""Run Cobble's meetings workspace on loopback, offline by default.

Live supplier access is explicit, per-supplier, and uses the shared private
conversation ledger; keys remain only in local server process memory.
"""
import argparse
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

STATIC = Path(__file__).resolve().parent.parent / "src" / "cobble" / "static"
HTML = STATIC / "workbench.html"
BOARDROOM_HTML = STATIC / "snug_demo.html"
LOGO = Path(__file__).resolve().parent.parent / "docs" / "assets" / "cobble-logo.png"
MAX_BYTES = 8192


def create_server(store, index, port=8766, *, live_gpt=False,
                  live_claude=False, live_mistral=False,
                  live_adapter=None, live_adapters=None):
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
    live_sessions = {"default": LiveChatService(store, adapters=adapters)}
    live_lock = threading.Lock()

    def room_session(room_id="default"):
        catalog.require(room_id)
        with live_lock:
            if room_id not in live_sessions:
                live_sessions[room_id] = LiveChatService(
                    store, adapters=adapters, meeting_id=room_id)
            return live_sessions[room_id]

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
                                 "source": "github"})
            elif self.path == "/api/live/rooms":
                try:
                    self.reply(200, {"rooms": catalog.list(), "default_standing_orders": DEFAULT_ORDERS})
                except (ValueError, PermissionError, OSError) as error:
                    self.reply(400, {"error": str(error)})
            elif urlsplit(self.path).path == "/api/live/output":
                try:
                    query = parse_qs(urlsplit(self.path).query)
                    meeting_id = query.get("room_id", ["default"])[0]
                    item = next(r for r in catalog.list() if r["id"] == meeting_id)
                    if item.get("state") == "closed":
                        raise PermissionError("Closed meeting output is unavailable")
                    events = room_session(meeting_id).session()["turns"]
                    selected = set(item.get("room_voice", [])) - set(item.get("redacted", []))
                    self.reply(200, {"agenda": next((e["question"] for e in events if e.get("question")), ""),
                                     "contributions": [e for e in events if e["turn_id"] in selected]})
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
            if not self.trusted():
                return
            if self.path not in ("/api/search", "/api/inspect", "/api/preview", "/api/exchange",
                                 "/api/live/preview", "/api/live/send", "/api/live/post",
                                  "/api/live/rooms/create", "/api/live/rooms/rename",
                                  "/api/live/rooms/configure"):
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
                    if "voice_event" in data or "redact_event" in data:
                        event_id = data.get("voice_event", data.get("redact_event"))
                        if event_id not in {e["turn_id"] for e in room_session(meeting_id).session()["turns"]}:
                            raise ValueError("Contribution does not belong to this meeting")
                    result = catalog.configure(meeting_id=meeting_id, **data)
                elif self.path == "/api/live/post":
                    if next(r for r in catalog.list() if r["id"] == data.get("room_id", "default")).get("state") == "closed":
                        raise PermissionError("Reopen the meeting before contributing")
                    if set(data) not in ({"text"}, {"text", "room_id"}):
                        raise PermissionError("Only a local operator message and room ID may be posted")
                    result = room_session(data.get("room_id", "default")).post_operator(text=data["text"])
                elif self.path == "/api/live/preview":
                    if next(r for r in catalog.list() if r["id"] == data.get("room_id", "default")).get("state") == "closed":
                        raise PermissionError("Reopen the meeting before consulting a supplier")
                    if not requested:
                        raise PermissionError("Live supplier access is disabled")
                    if ("question" not in data or
                        set(data) - {"question", "provider", "room_id"}):
                        raise PermissionError("Only question, supplier and room ID may be reviewed")
                    result = room_session(data.get("room_id", "default")).preview(
                        question=data["question"], provider=data.get("provider", "openai"))
                else:
                    if next(r for r in catalog.list() if r["id"] == data.get("room_id", "default")).get("state") == "closed":
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

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path)
    parser.add_argument("--port", type=int, default=8766)
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
                       live_adapters=adapters if enabled else None) as server:
        description = ", ".join(name for name in ("openai", "claude", "mistral")
                                if name in enabled) if enabled else "offline"
        print(f"Cobble meetings ({description}): http://127.0.0.1:{server.server_port}/", flush=True)
        print("Live calls require one-time exact context review." if enabled else
              "No external supplier calls; only approved fixture exchanges.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
