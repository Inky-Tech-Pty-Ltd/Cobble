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
        first_preview = self.service.preview_exchange(
            question="What was examined?", document_ids=[self.github_id])
        self.assertEqual(len(first_preview["selected_memories"]), 1)
        self.assertEqual(first_preview["network_calls"], 0)
        self.assertEqual(len(first_preview["context_sha256"]), 64)
        first = self.service.reviewed_exchange(
            approval_token=first_preview["approval_token"])
        self.assertEqual(first["context_sha256"], first_preview["context_sha256"])
        second_preview = self.service.preview_exchange(
            question="Do you retain continuity?", document_ids=[],
            previous_ids=[first["event_id"]], fixture="fixture-indigo")
        self.assertEqual(second_preview["previous_exchanges"][0]["question"],
                         "What was examined?")
        self.assertEqual(second_preview["previous_exchanges"][0]["answer"],
                         first["answer"])
        second = self.service.reviewed_exchange(
            approval_token=second_preview["approval_token"])
        self.assertEqual(second["previous_exchange_ids"], [first["event_id"]])
        self.assertEqual(second["selected_memories"], [])
        self.assertIn("1 expressly supplied", second["answer"])
        self.assertEqual(read_event(self.store, first["event_id"]), first)

    def test_approval_is_single_use_and_does_not_re_read_sources(self):
        preview = self.service.preview_exchange(
            question="Show remembered source", document_ids=[self.github_id])
        # Remove the index after approval. Execution must use the precise
        # snapshot already reviewed, not a second retrieval of altered state.
        self.index.unlink()
        result = self.service.reviewed_exchange(
            approval_token=preview["approval_token"])
        self.assertEqual(result["selected_memories"],
                         preview["selected_memories"])
        self.assertEqual(result["context_sha256"], preview["context_sha256"])
        with self.assertRaises(PermissionError):
            self.service.reviewed_exchange(
                approval_token=preview["approval_token"])

    def test_prior_exchange_snapshot_survives_history_change(self):
        earlier = self.service.reviewed_exchange(
            approval_token=self.service.preview_exchange(
                question="Earlier prompt", document_ids=[])["approval_token"])
        preview = self.service.preview_exchange(
            question="Use prior context", document_ids=[],
            previous_ids=[earlier["event_id"]])
        # Alter the local earlier record after review. The approved request
        # must not silently pick up this unreviewed content.
        event_path = self.store / "snug" / "events" / (earlier["event_id"] + ".json")
        altered = json.loads(event_path.read_text())
        altered["question"] = "UNREVIEWED DIFFERENT QUESTION"
        event_path.write_text(json.dumps(altered))
        from unittest.mock import patch
        from cobble import snug_demo
        actual_exchange = snug_demo.exchange
        captured = []
        def capture(**kwargs):
            captured.append(kwargs["prepared_request"])
            return actual_exchange(**kwargs)
        with patch.object(snug_demo, "exchange", side_effect=capture):
            result = self.service.reviewed_exchange(approval_token=preview["approval_token"])
        self.assertEqual(result["context_sha256"], preview["context_sha256"])
        self.assertEqual(captured[0].previous_exchanges[0]["question"],
                         "Earlier prompt")
        self.assertNotEqual(captured[0].previous_exchanges[0]["question"],
                            altered["question"])

    def test_live_supplier_refused_before_any_event(self):
        with self.assertRaises(PermissionError):
            self.service.preview_exchange(question="No", document_ids=[],
                                          fixture="claude")
        with self.assertRaises(PermissionError):
            self.service.preview_exchange(question="No", document_ids=[self.private_id])
        with self.assertRaises(PermissionError):
            self.service.reviewed_exchange(approval_token="invalid")
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
                    "memory_ids": [self.github_id], "confirmed": True})
                self.assertEqual(status, 400)
                status, _ = request("/api/preview", {"question": "Hi",
                    "memory_ids": [], "provider": "claude"})
                self.assertEqual(status, 400)
                status, data = request("/api/preview", {"question": "Hi",
                    "memory_ids": [self.github_id]})
                self.assertEqual(status, 200)
                approved = json.loads(data)
                self.assertEqual(len(approved["selected_memories"]), 1)
                status, _ = request("/api/exchange", {"approval_token":
                    approved["approval_token"], "question": "changed"})
                self.assertEqual(status, 400)
                status, data = request("/api/exchange",
                    {"approval_token": approved["approval_token"]})
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(data)["question"], "Hi")
                status, _ = request("/api/exchange",
                    {"approval_token": approved["approval_token"]})
                self.assertEqual(status, 400)
                status, _ = request("/api/search", {"query": "Sankarshan"},
                                   {"Host": "evil.example"})
                self.assertEqual(status, 403)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
