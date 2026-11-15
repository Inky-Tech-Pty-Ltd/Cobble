"""Run Snug's first corpus-backed browser slice on localhost.

The initial browser slice is intentionally OFFLINE. It can inspect GitHub
memories, explicitly approve them for fixture exchanges, and swap fixtures.
It cannot invoke a live external provider or leak credentials.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import sys

from cobble.openai_adapter import OpenAIAdapter
from pathlib import Path

from cobble.snug_demo import DemoService
from cobble.snug_live import LiveChatService, OutcomeUnknown

HTML = Path(__file__).resolve().parent.parent / "src" / "cobble" / "static" / "snug_demo.html"
MAX_BYTES = 8192


def create_server(store, index, port=8766, *, live_gpt=False, live_adapter=None):
    service = DemoService(store, index)
    if live_adapter is not None and not live_gpt:
        raise ValueError("Injected adapter requires an explicitly live test server")
    live = LiveChatService(store, adapter=live_adapter) if live_gpt else None

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
                             "style-src 'unsafe-inline'; connect-src 'self'; "
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
            elif self.path == "/api/health":
                self.reply(200, {"ok": True, "live_suppliers": bool(live),
                                 "live_gpt": bool(live), "source": "github"})
            elif self.path == "/api/live/session" and live is not None:
                self.reply(200, live.session())
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if not self.trusted():
                return
            if self.path not in ("/api/search", "/api/inspect", "/api/preview", "/api/exchange",
                                 "/api/live/preview", "/api/live/send"):
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
                elif self.path == "/api/live/preview":
                    if live is None:
                        raise PermissionError("Live GPT is disabled")
                    if set(data) != {"question"}:
                        raise PermissionError("Only a question is accepted for live review")
                    result = live.preview(question=data["question"])
                else:
                    if live is None:
                        raise PermissionError("Live GPT is disabled")
                    if set(data) != {"approval_token"}:
                        raise PermissionError("Only the exact one-time live approval is accepted")
                    result = live.send(approval_token=data["approval_token"])
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
                        help="Explicitly enable billable GPT calls")
    parser.add_argument("--key-stdin", action="store_true",
                        help="Read the existing API key once from stdin (not from shell history)")
    args = parser.parse_args()
    if args.key_stdin and not args.live_gpt:
        parser.error("--key-stdin requires --live-gpt")
    injected_adapter = None
    if args.key_stdin:
        key = sys.stdin.read(4096).strip()
        if not 1 <= len(key) <= 512:
            parser.error("Invalid API key from stdin")
        injected_adapter = OpenAIAdapter(
            allow_network=True, key=key, output_tokens=2048)
    elif args.live_gpt and not os.environ.get("OPENAI_API_KEY"):
        parser.error("--live-gpt requires OPENAI_API_KEY or --key-stdin")
    index = args.index or args.store / "index" / "search.sqlite3"
    with create_server(args.store, index, args.port, live_gpt=args.live_gpt,
                       live_adapter=injected_adapter) as server:
        mode = "live GPT enabled" if args.live_gpt else "offline"
        print(f"Snug demo ({mode}): http://127.0.0.1:{server.server_port}/", flush=True)
        print("Live GPT calls require one-time exact context review." if args.live_gpt
              else "No external supplier calls; only approved fixture exchanges.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
