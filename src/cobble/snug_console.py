"""Snug's first browser console: local-only, deterministic and read-only.

This is a transparent operator interface over Arena metadata, NOT an agent
and not a model-powered conversation. The original source corpus is never
read through HTTP. The console has no external network dependencies.
"""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cobble.arena_catalogue import catalogue

MAX_PROMPT_CHARS = 1200
MAX_REQUEST_BYTES = 4096
STATIC_HTML = Path(__file__).resolve().parent / "static" / "snug.html"


def respond(arena, prompt):
    """Interpret only a small fixed set of offline commands."""
    if not isinstance(prompt, str) or not 0 < len(prompt.strip()) <= MAX_PROMPT_CHARS:
        raise ValueError("Prompt must contain 1–1200 characters")
    raw = prompt.strip()
    key = re.sub(r"[^a-z0-9 ]", " ", raw.casefold())
    key = " ".join(key.split())
    if key in ("hello", "hi", "hey", "hello snug", "hi snug"):
        return {
            "kind": "greeting",
            "response": "Hello. This is Snug's experimental console. I have a preserved corpus, but no intelligence supplier or independent learning process is connected yet. Ask 'status' or 'sources' to inspect what is here.",
        }
    if key in ("status", "memory", "what do you remember", "what do you know", "how much do you remember", "what is your status"):
        summary = catalogue(arena)
        return {
            "kind": "status",
            "response": f"Arena One contains {summary['total_files']} preserved files and {summary['total_bytes']:,} source bytes. This is stored experience, not evidence that I have understood it. No model calls or autonomous browsing are enabled.",
            "sources": {"total_files": summary["total_files"], "total_bytes": summary["total_bytes"]},
        }
    if key in ("sources", "corpus", "catalogue", "catalog", "what is in your corpus", "show sources", "show your sources"):
        summary = catalogue(arena)
        categories = [
            {"name": name, "files": v["files"], "bytes": v["bytes"]}
            for name, v in summary["categories"].items() if v["files"]
        ]
        return {
            "kind": "catalogue",
            "response": "These are source categories inferred from filenames, not memories I have interpreted. There is no live connection to either OpenAI or Kimi.",
            "sources": {"total_files": summary["total_files"], "total_bytes": summary["total_bytes"], "categories": categories},
        }
    if key in ("who are you", "are you snug", "are you alive", "what is your name"):
        return {
            "kind": "identity",
            "response": "Snug is the working name of an experimental, corpus-seated entity. Today this interface can observe copied-source metadata. An independent conversation, hypotheses, learning and a stable identity have not been demonstrated.",
        }
    if key in ("help", "what can you do"):
        return {
            "kind": "help",
            "response": "I can currently answer only these offline commands: hello, status, sources, who are you, help. Other questions require a future metered intelligence supplier and permission-controlled retrieval.",
        }
    return {
        "kind": "unsupported",
        "response": "I can't answer that yet. No model or memory-reading hemisphere is connected, and I won't invent an answer. Try 'sources', 'status' or 'help'.",
    }


def create_server(arena, port=8765):
    """Listen on loopback only, with no general filesystem or command endpoint."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    arena = Path(arena).expanduser().resolve()
    # Fail before opening a listener if the local Arena is not populated.
    catalogue(arena)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Prompt bodies never appear in access logs.
            pass

        def _host_ok(self):
            port_now = self.server.server_port
            return self.headers.get("Host") in (
                f"127.0.0.1:{port_now}", f"localhost:{port_now}")

        def _reply(self, status, payload, mime="application/json; charset=utf-8"):
            content = (payload if isinstance(payload, bytes)
                       else json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'; "
                             "form-action 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def _invalid_host(self):
            if not self._host_ok():
                self._reply(403, {"error": "Local loopback host required"})
                return True
            return False

        def do_GET(self):
            if self._invalid_host():
                return
            if self.path == "/":
                self._reply(200, STATIC_HTML.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/api/health":
                self._reply(200, {"ok": True, "mode": "offline-local", "agent": False})
            else:
                self._reply(404, {"error": "Not found"})

        def do_POST(self):
            if self._invalid_host():
                return
            if self.path != "/api/ask":
                self._reply(404, {"error": "Not found"})
                return
            allowed_origins = (
                f"http://127.0.0.1:{self.server.server_port}",
                f"http://localhost:{self.server.server_port}",
            )
            if (self.headers.get("Origin") not in allowed_origins or
                    self.headers.get("X-Snug-Client") != "local-console"):
                self._reply(403, {"error": "Same-origin local console required"})
                return
            if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
                self._reply(415, {"error": "JSON request required"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = -1
            if not 0 < size <= MAX_REQUEST_BYTES:
                self._reply(413, {"error": "Request too large or absent"})
                return
            try:
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Request must be an object")
                result = respond(arena, data.get("prompt"))
            except (ValueError, UnicodeError, TypeError) as exc:
                self._reply(400, {"error": str(exc)})
                return
            except (OSError, KeyError) as exc:
                self._reply(503, {"error": "Arena catalogue unavailable"})
                return
            self._reply(200, {"speaker": "Snug (offline console)",
                              "provider": None, **result})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
