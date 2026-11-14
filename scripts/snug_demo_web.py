"""Run Snug's first corpus-backed browser slice on localhost.

The initial browser slice is intentionally OFFLINE. It can inspect GitHub
memories, explicitly approve them for fixture exchanges, and swap fixtures.
It cannot invoke a live external provider or leak credentials.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

from cobble.snug_demo import DemoService

HTML = Path(__file__).resolve().parent.parent / "src" / "cobble" / "static" / "snug_demo.html"
MAX_BYTES = 8192


def create_server(store, index, port=8766):
    service = DemoService(store, index)

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
                self.reply(200, {"ok": True, "live_suppliers": False, "source": "github"})
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if not self.trusted():
                return
            if self.path not in ("/api/search", "/api/inspect", "/api/exchange"):
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
                else:
                    if data.get("confirmed") is not True:
                        raise PermissionError("Explicit operator approval required")
                    result = service.reviewed_exchange(
                        question=data.get("question"),
                        document_ids=data.get("memory_ids"),
                        previous_ids=data.get("previous_ids", []),
                        fixture=data.get("provider", "fixture-amber"))
                self.reply(200, result)
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
    args = parser.parse_args()
    index = args.index or args.store / "index" / "search.sqlite3"
    with create_server(args.store, index, args.port) as server:
        print(f"Snug demo (offline): http://127.0.0.1:{server.server_port}/", flush=True)
        print("No external supplier calls; only approved fixture exchanges.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
