"""Snug's offline browser interface: tests run without providers or Internet."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from cobble.arena import init_arena, populate_corpus
from cobble.snug_console import create_server, respond


class SnugConsoleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        archive = root / "original"
        self.arena = root / "arena"
        (archive / "github" / "conversations").mkdir(parents=True)
        (archive / "github" / "conversations" / "sample.txt").write_text(
            "Very private memory; do not share through HTTP.", encoding="utf-8")
        (archive / "notes").mkdir()
        (archive / "notes" / "note.txt").write_text("An unanswered hypothesis", encoding="utf-8")
        limits = {"memory_bytes": 100000, "model_tokens": 0,
                  "attention_steps": 10, "archive_reads": 100,
                  "external_ops": 0}
        init_arena(archive, self.arena, limits)
        populate_corpus(self.arena)
        self.state_before = (self.arena / "state.json").read_bytes()

    def test_explicit_capability_boundaries(self):
        self.assertIn("2 preserved files", respond(self.arena, "status")["response"])
        report = respond(self.arena, "sources")
        self.assertEqual(report["sources"]["total_files"], 2)
        self.assertEqual(report["kind"], "catalogue")
        self.assertIn("intelligence supplier", respond(self.arena, "help")["response"])
        self.assertEqual(respond(self.arena, "Could you write me a poem?")["kind"], "unsupported")
        self.assertEqual(respond(self.arena, "who are you?")["kind"], "identity")
        self.assertNotIn("Very private memory", json.dumps(report))
        self.assertEqual(self.state_before, (self.arena / "state.json").read_bytes())

    def test_empty_prompt_rejected(self):
        with self.assertRaises(ValueError):
            respond(self.arena, "  ")
        with self.assertRaises(ValueError):
            respond(self.arena, "A" * 1201)

    def test_http_loopback_no_corpus_leak_and_same_origin(self):
        with create_server(self.arena, 0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_port
            try:
                def request(method, path, body=None, headers=None):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                    try:
                        connection.request(method, path, body=body, headers=headers or {})
                        response = connection.getresponse()
                        return response.status, dict(response.getheaders()), response.read()
                    finally:
                        connection.close()

                status, headers, html = request("GET", "/")
                self.assertEqual(status, 200)
                self.assertIn(b"<title>Snug", html)
                self.assertIn(b"offline", html.lower())
                self.assertIn("Content-Security-Policy", headers)
                self.assertNotIn(b"Very private memory", html)

                status, _, result = request("GET", "/api/health")
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(result)["agent"], False)
                status, _, _ = request("GET", "/private.txt")
                self.assertEqual(status, 404)

                prompt = json.dumps({"prompt": "sources"}).encode("utf-8")
                correct = {
                    "Content-Type": "application/json",
                    "Origin": f"http://127.0.0.1:{port}",
                    "X-Snug-Client": "local-console",
                }
                status, _, answer = request("POST", "/api/ask", prompt, correct)
                self.assertEqual(status, 200)
                answer = json.loads(answer)
                self.assertEqual(answer["speaker"], "Snug (offline console)")
                self.assertEqual(answer["kind"], "catalogue")
                self.assertEqual(answer["sources"]["total_files"], 2)
                self.assertNotIn("Very private memory", json.dumps(answer))
                self.assertEqual(self.state_before, (self.arena / "state.json").read_bytes())

                wrong_origin = {**correct, "Origin": "https://untrusted.example"}
                status, _, _ = request("POST", "/api/ask", prompt, wrong_origin)
                self.assertEqual(status, 403)
                no_client = {k:v for k,v in correct.items() if k != "X-Snug-Client"}
                status, _, _ = request("POST", "/api/ask", prompt, no_client)
                self.assertEqual(status, 403)

                status, _, _ = request("POST", "/api/ask", b"not json", correct)
                self.assertEqual(status, 400)
                status, _, _ = request("POST", "/api/ask", json.dumps({"prompt": "X"*1300}), correct)
                self.assertEqual(status, 400)
                status, _, _ = request("GET", "/../../etc/passwd")
                self.assertEqual(status, 404)

                status, _, _ = request("GET", "/", headers={"Host": "attacker.example"})
                self.assertEqual(status, 403)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
