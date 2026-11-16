"""Keyless offline tests for Snug's durable GPT boardroom session."""
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

from cobble.claude_adapter import ProviderReply
from cobble.local_search import build
from cobble.openai_adapter import OpenAIAdapter, MODEL, prepare_message
from cobble.snug_live import LiveChatService, OutcomeUnknown
from cobble.snug_exchange import ExchangeRequest


def fake_reply(text="A recorded response."):
    return ProviderReply(text=text, model=MODEL, request_id="resp_test",
                         usage={"kind": "mock-openai-api", "network_calls": 0,
                                "input_tokens": 50, "output_tokens": 17,
                                "estimated_provider_cost_usd": "0.00001",
                                "cost_is_estimate": True})


class Supplier:
    name = "openai"

    def __init__(self, store, *, fail=False):
        self.store = Path(store)
        self.calls = []
        self.fail = fail

    def answer(self, request):
        folder = self.store / "snug" / "live" / "default"
        turns = list((folder / "turns").glob("*.json"))
        attempts = list((folder / "attempts").glob("*.json"))
        assert len(turns) == len(attempts) > 0, "Provider called before durable attempt"
        self.calls.append(request)
        if self.fail:
            raise RuntimeError("Simulated ambiguous supplier failure")
        return fake_reply("Response " + str(len(self.calls)))


class LiveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name) / "private"
        self.store.mkdir(mode=0o700)
        self.supplier = Supplier(self.store)
        self.svc = LiveChatService(self.store, adapter=self.supplier)

    def send(self, question="Hello"):
        p = self.svc.preview(question=question)
        return self.svc.send(approval_token=p["approval_token"])["turn"]

    def test_acceptance_precedes_call_and_is_durable(self):
        first = self.send()
        self.assertEqual(first["status"], "completed")
        self.assertEqual(first["answer"], "Response 1")
        self.assertEqual(len(self.supplier.calls), 1)
        self.assertEqual(self.supplier.calls[0].previous_exchanges, ())
        saved = LiveChatService(self.store, adapter=Supplier(self.store)).session()
        self.assertEqual(saved["turns"][0]["question"], "Hello")
        self.assertEqual(saved["turns"][0]["answer"], "Response 1")
        self.assertEqual(saved["turns"][0]["usage"]["input_tokens"], 50)
        p = self.store / "snug" / "live" / "default" / "turns" / (first["turn_id"] + ".json")
        self.assertEqual(p.stat().st_mode & 0o777, 0o600)
        evidence = json.loads(p.read_text())
        self.assertEqual(evidence["payload"]["store"], False)
        self.assertEqual(evidence["payload"]["tools"], [])
        self.assertEqual(evidence["payload"]["max_output_tokens"], 2048)

    def test_resume_and_exact_history(self):
        first = self.send("First point")
        new = LiveChatService(self.store, adapter=self.supplier)
        preview = new.preview(question="Second point")
        self.assertEqual(len(preview["previous_exchanges"]), 1)
        self.assertEqual(preview["previous_exchanges"][0]["question"], first["question"])
        self.assertEqual(preview["previous_exchanges"][0]["answer"], first["answer"])
        second = new.send(approval_token=preview["approval_token"])["turn"]
        self.assertEqual(second["status"], "completed")
        self.assertEqual(len(self.supplier.calls[1].previous_exchanges), 1)

    def test_unknown_outcome_is_retained_without_retry(self):
        failure = Supplier(self.store, fail=True)
        svc = LiveChatService(self.store, adapter=failure)
        preview = svc.preview(question="Do not lose me")
        with self.assertRaises(OutcomeUnknown) as caught:
            svc.send(approval_token=preview["approval_token"])
        self.assertEqual(len(failure.calls), 1)
        self.assertEqual(len(svc.session()["turns"]), 1)
        event = svc.session()["turns"][0]
        self.assertEqual(event["turn_id"], caught.exception.turn_id)
        self.assertEqual(event["question"], "Do not lose me")
        self.assertEqual(event["status"], "outcome_unknown")
        with self.assertRaises(PermissionError):
            svc.send(approval_token=preview["approval_token"])
        reloaded = LiveChatService(self.store, adapter=self.supplier)
        self.assertEqual(reloaded.session()["turns"][0]["status"], "outcome_unknown")
        self.assertEqual(len(self.supplier.calls), 0)
        # Unknown responses do not get smuggled into subsequent model context.
        self.assertEqual(reloaded.preview(question="Next")["previous_exchanges"], [])

    def test_supplier_switch_preserves_shared_ledger_and_context(self):
        """GPT -> Claude -> Mistral use a single durable conversation."""
        class FakeOther(Supplier):
            def __init__(self, store, name):
                super().__init__(store)
                self.name = name

            def answer(self, request):
                folder = self.store / "snug" / "live" / "default"
                assert len(list((folder / "turns").glob("*.json"))) == len(
                    list((folder / "attempts").glob("*.json")))
                self.calls.append(request)
                kind = {"claude": "mock-claude-api",
                        "mistral": "mock-mistral-api"}[self.name]
                result = fake_reply(self.name + " sees " +
                                    str(len(request.previous_exchanges)) + " prior turns")
                return ProviderReply(
                    text=result.text, model=self.name+"-test",
                    request_id=self.name+"-test-id",
                    usage={**result.usage, "kind": kind})

        claude = FakeOther(self.store, "claude")
        mistral = FakeOther(self.store, "mistral")
        adapters = {"openai": self.supplier, "claude": claude, "mistral": mistral}
        svc = LiveChatService(self.store, adapters=adapters)
        first_preview = svc.preview(question="Mr GPT, come here.", provider="openai")
        first = svc.send(approval_token=first_preview["approval_token"])["turn"]
        self.assertEqual(first["provider"], "openai")
        second_preview = svc.preview(question="Claude, do you recognise that?", provider="claude")
        self.assertEqual(second_preview["provider"], "claude")
        self.assertEqual(second_preview["previous_exchanges"][0]["question"], first["question"])
        self.assertEqual(second_preview["previous_exchanges"][0]["answer"], first["answer"])
        self.assertEqual(second_preview["network_calls_if_approved"], 1)
        second = svc.send(approval_token=second_preview["approval_token"])["turn"]
        self.assertEqual(second["provider"], "claude")
        self.assertEqual(second["answer"], "claude sees 1 prior turns")
        third_preview = svc.preview(question="Mistral, any thoughts?", provider="mistral")
        self.assertEqual([p["provider"] for p in third_preview["previous_exchanges"]],
                         ["openai", "claude"])
        self.assertEqual([p["answer"] for p in third_preview["previous_exchanges"]],
                         ["Response 1", "claude sees 1 prior turns"])
        third = svc.send(approval_token=third_preview["approval_token"])["turn"]
        self.assertEqual(third["provider"], "mistral")
        self.assertEqual(third["answer"], "mistral sees 2 prior turns")
        fresh = LiveChatService(self.store, adapters=adapters)
        self.assertEqual([t["provider"] for t in fresh.session()["turns"]],
                         ["openai", "claude", "mistral"])
        self.assertEqual(set(fresh.session()["live_providers"]),
                         {"openai", "claude", "mistral"})
        self.assertEqual(len(claude.calls[0].previous_exchanges), 1)
        self.assertEqual(len(mistral.calls[0].previous_exchanges), 2)
        for turn in fresh.session()["turns"]:
            self.assertEqual(turn["status"], "completed")
            self.assertIsNotNone(turn["usage"]["estimated_provider_cost_usd"])

    def test_live_supplier_capabilities_and_approval_binding(self):
        from cobble.claude_adapter import ClaudeAdapter, prepare_message as make_claude
        from cobble.mistral_adapter import MistralAdapter, prepare_message as make_mistral
        from cobble.snug_exchange import ExchangeRequest
        with self.assertRaisesRegex(PermissionError, "unavailable"):
            self.svc.preview(question="No Claude", provider="claude")
        with self.assertRaisesRegex(PermissionError, "unavailable"):
            self.svc.preview(question="No rogue provider", provider="unknown")
        request = ExchangeRequest("operator", "Hi", (), ())
        self.assertEqual(make_claude(request, output_tokens=2048)["max_tokens"], 2048)
        self.assertEqual(make_mistral(request, output_tokens=2048)["max_tokens"], 2048)
        self.assertEqual(make_claude(request)["max_tokens"], 256)
        self.assertEqual(make_mistral(request)["max_tokens"], 256)
        with self.assertRaises(ValueError):
            ClaudeAdapter(output_tokens=5000)
        with self.assertRaises(ValueError):
            MistralAdapter(output_tokens=5000)
        with self.assertRaisesRegex(ValueError, "identity"):
            LiveChatService(self.store, adapters={"claude": self.supplier})
        one = self.svc.preview(question="GPT question")
        two = self.svc.preview(question="Other question")
        self.svc.send(approval_token=one["approval_token"])
        with self.assertRaisesRegex(PermissionError, "changed after review"):
            self.svc.send(approval_token=two["approval_token"])

    def test_crash_gap_without_attempt_is_distinguished(self):
        turn_id = "20261115010203000000-" + "a" * 12
        self.svc._write("turns", turn_id, {
            "turn_id": turn_id, "created_utc": "2026-11-15T01:02:03+00:00",
            "provider": "openai", "question": "Saved only",
            "context_sha256": "abc", "context": {}, "payload": {}})
        restarted = LiveChatService(self.store, adapter=self.supplier)
        self.assertEqual(restarted.session()["turns"][0]["status"], "saved_not_sent")
        restarted._write("attempts", turn_id, {"turn_id": turn_id})
        self.assertEqual(restarted.session()["turns"][0]["status"], "outcome_unknown")

    def test_approval_is_one_time_and_snapshot_must_be_current(self):
        p1 = self.svc.preview(question="One")
        p2 = self.svc.preview(question="One but stale")
        self.svc.send(approval_token=p1["approval_token"])
        with self.assertRaises(PermissionError):
            self.svc.send(approval_token=p1["approval_token"])
        with self.assertRaisesRegex(PermissionError, "changed after review"):
            self.svc.send(approval_token=p2["approval_token"])

    def test_long_history_is_trimmed_without_fabricating_context(self):
        for i in range(4):
            turn_id = "20261115010203000000-" + format(i, "012x")
            self.svc._write("turns", turn_id, {
                "turn_id": turn_id, "created_utc": "2026-11-15T01:02:03+00:00",
                "provider": "openai", "question": "Question " + str(i),
                "context_sha256": "abc", "context": {}, "payload": {}})
            self.svc._write("outcomes", turn_id, {
                "turn_id": turn_id, "status": "completed",
                "answer": "long " * 1400, "model": MODEL, "usage": {},
                "provider_request_id": "resp_test"})
        p = self.svc.preview(question="Continue our discussion")
        self.assertGreater(p["older_exchanges_omitted"], 0)
        self.assertLess(len(p["previous_exchanges"]), 4)
        self.assertEqual(p["previous_exchanges"][-1]["question"], "Question 3")

    def test_bounded_question_and_outgoing_source_scope(self):
        note = self.store / "unshared.txt"
        note.write_text("NEVER-SEND-THIS-SECRET")
        with self.assertRaises(ValueError):
            self.svc.preview(question="x" * 2001)
        p = self.svc.preview(question="What is today's plan?")
        self.assertEqual(p["selected_memories"], [])
        self.assertNotIn("NEVER-SEND-THIS-SECRET", json.dumps(p))
        request = ExchangeRequest("operator", "Hi", (), ())
        self.assertEqual(prepare_message(request)["max_output_tokens"], 256)
        self.assertEqual(prepare_message(request, output_tokens=2048)["max_output_tokens"], 2048)
        with self.assertRaises(ValueError):
            OpenAIAdapter(output_tokens=5000)

    def test_local_http_boundary_and_keyless_fake(self):
        folder = self.store / "hosting" / "inkytech"
        folder.mkdir(parents=True)
        (folder / "notes.txt").write_text("harmless")
        index = self.store / "index" / "search.sqlite3"
        build(self.store, index)
        entry = Path(__file__).resolve().parents[1] / "scripts" / "snug_demo_web.py"
        spec = importlib.util.spec_from_file_location("snug_demo_web", entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.create_server(self.store, index, port=0, live_gpt=True,
                                  live_adapter=self.supplier) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_port

            def call(route, data=None, headers=None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                method = "POST" if data is not None else "GET"
                default_headers = {
                    "Content-Type": "application/json",
                    "Origin": "http://127.0.0.1:" + str(port),
                    "X-Snug-Client": "demo-local",
                }
                conn.request(method, route,
                             body=json.dumps(data) if data is not None else None,
                             headers=headers or default_headers)
                response = conn.getresponse()
                status, body = response.status, response.read()
                conn.close()
                return status, json.loads(body)

            try:
                status, health = call("/api/health")
                self.assertEqual(status, 200)
                self.assertTrue(health["live_gpt"])
                status, p = call("/api/live/preview", {"question": "Hello from browser"})
                self.assertEqual(status, 200)
                self.assertEqual(p["network_calls_if_approved"], 1)
                status, _ = call("/api/live/send", {"question": "bypass"})
                self.assertEqual(status, 400)
                status, result = call("/api/live/send", {"approval_token": p["approval_token"]})
                self.assertEqual(status, 200)
                self.assertEqual(result["turn"]["status"], "completed")
                status, saved = call("/api/live/session")
                self.assertEqual(status, 200)
                self.assertEqual(saved["turns"][0]["question"], "Hello from browser")
                status, _ = call("/api/live/preview", {"question": "Hi"}, {"Host": "evil.test"})
                self.assertEqual(status, 403)
            finally:
                server.shutdown()
                thread.join(timeout=5)


    def test_http_routes_live_supplier_selection_and_history(self):
        """Server routes only the specifically reviewed supplier into one ledger."""
        class Named(Supplier):
            def __init__(self, store, name):
                super().__init__(store)
                self.name = name

            def answer(self, request):
                self.calls.append(request)
                return ProviderReply(
                    text="Hello from " + self.name,
                    model="synthetic-" + self.name,
                    request_id="fixture-" + self.name,
                    usage={
                        "kind": "mock-" + self.name + "-api" if self.name != "claude"
                        else "mock-claude-api",
                        "network_calls": 0, "input_tokens": 30,
                        "output_tokens": 10,
                        "estimated_provider_cost_usd": "0.00001",
                        "cost_is_estimate": True,
                    },
                )

        claude = Named(self.store, "claude")
        mistral = Named(self.store, "mistral")
        note = self.store / "hosting" / "inkytech" / "harmless.txt"
        note.parent.mkdir(parents=True)
        note.write_text("harmless")
        index = self.store / "index" / "search.sqlite3"
        build(self.store, index)
        entry = Path(__file__).resolve().parents[1] / "scripts" / "snug_demo_web.py"
        spec = importlib.util.spec_from_file_location("snug_demo_web", entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.create_server(
            self.store, index, port=0, live_gpt=True, live_claude=True,
            live_mistral=True,
            live_adapters={"openai": self.supplier,
                           "claude": claude, "mistral": mistral}
        ) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_port
            def call(route, payload=None):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                headers = {"Content-Type": "application/json",
                           "Origin": f"http://127.0.0.1:{port}",
                           "X-Snug-Client": "demo-local"}
                conn.request("POST" if payload is not None else "GET",
                             route, json.dumps(payload) if payload is not None else None,
                             headers=headers)
                response = conn.getresponse()
                result = response.status, json.loads(response.read())
                conn.close()
                return result
            try:
                status, health = call("/api/health")
                self.assertEqual(status, 200)
                self.assertEqual(health["live_providers"],
                                 ["openai", "claude", "mistral"])
                status, _ = call("/api/live/preview", {
                    "question": "No ambient memory", "provider": "claude",
                    "memory_ids": ["private"]})
                self.assertEqual(status, 400)
                status, p = call("/api/live/preview", {
                    "question": "Hello Claude", "provider": "claude"})
                self.assertEqual(status, 200)
                self.assertEqual(p["provider"], "claude")
                status, _ = call("/api/live/send", {
                    "approval_token": p["approval_token"], "provider": "mistral"})
                self.assertEqual(status, 400)
                status, reply = call("/api/live/send", {
                    "approval_token": p["approval_token"]})
                self.assertEqual(status, 200)
                self.assertEqual(reply["turn"]["answer"], "Hello from claude")
                status, _ = call("/api/live/send", {
                    "approval_token": p["approval_token"]})
                self.assertEqual(status, 400)
                status, p = call("/api/live/preview", {
                    "question": "Continue, Mistral", "provider": "mistral"})
                self.assertEqual(status, 200)
                self.assertEqual(p["previous_exchanges"][0]["provider"], "claude")
                status, reply = call("/api/live/send", {
                    "approval_token": p["approval_token"]})
                self.assertEqual(status, 200)
                self.assertEqual(reply["turn"]["provider"], "mistral")
                status, saved = call("/api/live/session")
                self.assertEqual(status, 200)
                self.assertEqual([t["provider"] for t in saved["turns"]],
                                 ["claude", "mistral"])
                self.assertEqual(len(mistral.calls[0].previous_exchanges), 1)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
