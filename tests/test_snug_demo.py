"""Tests for the local GitHub-only Snug boardroom slice."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from cobble.local_search import build, search
from cobble.snug_demo import DemoService
from cobble.snug_exchange import read_event


class DemoTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name) / "private"
        folder = self.store / "github" / "conversations" / "test"
        (folder / "versions").mkdir(parents=True)
        version = "a" * 64
        record = {"issue": {"title": "G1 experiment", "body": "Sankarshan tested a memory retrieval experiment."}}
        (folder / "versions" / f"{version}.json").write_text(json.dumps(record))
        (folder / "latest.json").write_text(json.dumps({"version": f"versions/{version}.json"}))
        other = self.store / "hosting" / "inkytech"
        other.mkdir(parents=True)
        (other / "private.txt").write_text("SECRET-DO-NOT-DISCLOSE")
        self.index = self.store / "index" / "search.sqlite3"
        build(self.store, self.index)
        self.service = DemoService(self.store, self.index)
        self.github_id = search(self.index, "Sankarshan")[0]["id"]
        self.private_id = search(self.index, "SECRET")[0]["id"]

    def test_search_and_inspect_allow_only_github(self):
        self.assertEqual(self.service.find("Sankarshan")[0]["id"], self.github_id)
        self.assertEqual(self.service.find("SECRET"), [])
        self.assertIn("Sankarshan", self.service.inspect(self.github_id)["text"])
        with self.assertRaises(PermissionError):
            self.service.inspect(self.private_id)

    def test_explicit_exchange_and_supplier_substitution(self):
        first = self.service.reviewed_exchange(
            question="What was examined?", document_ids=[self.github_id])
        second = self.service.reviewed_exchange(
            question="Do you retain continuity?", document_ids=[],
            previous_ids=[first["event_id"]], fixture="fixture-indigo")
        self.assertEqual(first["usage"]["network_calls"], 0)
        self.assertEqual(second["previous_exchange_ids"], [first["event_id"]])
        self.assertEqual(second["selected_memories"], [])
        self.assertIn("1 expressly supplied", second["answer"])
        self.assertEqual(read_event(self.store, first["event_id"]), first)

    def test_live_supplier_refused_before_any_event(self):
        with self.assertRaises(PermissionError):
            self.service.reviewed_exchange(question="No", document_ids=[],
                                          fixture="claude")
        with self.assertRaises(PermissionError):
            self.service.reviewed_exchange(question="No", document_ids=[self.private_id])
        self.assertFalse((self.store / "snug" / "events").exists())

    def test_local_http_browser_security_and_confirmation(self):
        # Import the entrypoint as a regular Python module to avoid requiring
        # the scripts directory to become a distributable Python package.
        import importlib.util
        file = Path(__file__).resolve().parents[1] / "scripts" / "snug_demo_web.py"
        spec = importlib.util.spec_from_file_location("snug_demo_web", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.create_server(self.store, self.index, 0) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_port
            def request(path, payload=None, headers=None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                body = json.dumps(payload) if payload is not None else None
                base = {"Content-Type": "application/json",
                        "Origin": f"http://127.0.0.1:{port}",
                        "X-Snug-Client": "demo-local"}
                conn.request("POST" if payload is not None else "GET",
                             path, body=body, headers=headers if headers is not None else base)
                response = conn.getresponse()
                result = response.status, response.read()
                conn.close()
                return result
            try:
                status, html = request("/")
                self.assertEqual(status, 200)
                self.assertIn(b"Snug's Boardroom", html)
                self.assertNotIn(b"SECRET-DO-NOT-DISCLOSE", html)
                status, result = request("/api/health")
                self.assertEqual(status, 200)
                self.assertFalse(json.loads(result)["live_suppliers"])
                status, result = request("/api/search", {"query": "Sankarshan"})
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(result)["results"][0]["id"], self.github_id)
                status, _ = request("/api/inspect", {"id": self.private_id})
                self.assertEqual(status, 400)
                status, _ = request("/api/exchange", {"question": "Hi",
                    "memory_ids": [self.github_id], "confirmed": False})
                self.assertEqual(status, 400)
                status, _ = request("/api/exchange", {"question": "Hi",
                    "memory_ids": [], "provider": "claude", "confirmed": True})
                self.assertEqual(status, 400)
                status, _ = request("/api/search", {"query": "Sankarshan"},
                                   {"Host": "evil.example"})
                self.assertEqual(status, 403)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
