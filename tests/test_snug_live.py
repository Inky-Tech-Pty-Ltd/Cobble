"""Keyless offline tests for Snug's durable GPT boardroom session."""
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

from cobble.claude_adapter import ProviderReply, prepare_message as prepare_claude
from cobble.mistral_adapter import prepare_message as prepare_mistral
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
        paid_turns = [p for p in turns if json.loads(p.read_text()).get("kind") != "operator_message"]
        assert len(paid_turns) == len(attempts) > 0, "Provider called before durable attempt"
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

    def test_standing_orders_are_distinct_and_in_exact_payload_for_all_suppliers(self):
        orders = "Convenor rule: listen before speaking."
        request = ExchangeRequest(
            participant="operator", question="What is the agenda?",
            selected_memories=(), previous_exchanges=(), room_standing_orders=orders)
        outputs = (
            json.loads(prepare_message(request)["input"]),
            json.loads(prepare_claude(request)["messages"][0]["content"]),
            json.loads(prepare_mistral(request)["messages"][1]["content"]),
        )
        for output in outputs:
            self.assertEqual(output["room_standing_orders"], orders)
            self.assertEqual(output["question"], "What is the agenda?")
            self.assertEqual(output["selected_previous_exchanges"], [])
        before = self.svc.preview(question="Hello", room_standing_orders=orders)
        self.assertEqual(before["room_standing_orders"], orders)
        event = self.svc.send(approval_token=before["approval_token"])["turn"]
        self.assertEqual(event["context"]["room_standing_orders"], orders)
        self.assertEqual(json.loads(event["payload"]["input"])["room_standing_orders"], orders)
        self.assertEqual(self.supplier.calls[-1].room_standing_orders, orders)
        with self.assertRaisesRegex(ValueError, "standing orders"):
            self.svc.preview(question="Bad", room_standing_orders="x" * 8001)

    def test_room_authorised_output_reaches_all_supplier_payloads(self):
        """A decision is distinct from recent chat, and survives history trimming."""
        output = {
            "agenda": "Do we agree?",
            "contributions": [
                {"turn_id": "20261126000000000000-abc123abc123",
                 "provider": "operator", "text": "The room has decided YES."},
            ],
        }
        p = self.svc.preview(question="What did the room decide?",
                             room_output=output)
        selected = p["room_authorised_output"]
        self.assertEqual(selected["agenda"], "Do we agree?")
        self.assertEqual(selected["contributions"], output["contributions"])
        self.assertEqual(selected["older_contributions_omitted"], 0)
        turn = self.svc.send(approval_token=p["approval_token"])["turn"]
        self.assertEqual(turn["context"]["room_output"], selected)
        self.assertEqual(self.supplier.calls[-1].room_output, selected)
        for prepared in (
                prepare_message(self.supplier.calls[-1]),
                prepare_claude(self.supplier.calls[-1]),
                prepare_mistral(self.supplier.calls[-1])):
            if "input" in prepared:
                context = json.loads(prepared["input"])
            else:
                context = json.loads(prepared["messages"][-1]["content"])
            self.assertEqual(context["room_authorised_output"], selected)
        self.assertEqual(
            json.loads(turn["payload"]["input"])["room_authorised_output"],
            selected)

    def test_full_authorised_voice_plus_recent_conversation(self):
        """Whole adopted position is visible even after remarks fall off the window."""
        contributions = [
            {"turn_id": f"2026112600000000000{i}-abc123abc123",
             "provider": "operator", "text": f"Decision {i}"}
            for i in range(7)
        ]
        for i in range(6):
            self.svc.post_operator(text=f"Aside {i}")
        p = self.svc.preview(question="Current position?",
                             room_output={"agenda": "Consider decisions",
                                          "contributions": contributions})
        voice = p["room_authorised_output"]
        self.assertEqual(voice["contributions"], contributions)
        self.assertEqual(voice["agenda"], "Consider decisions")
        self.assertNotIn("older_contributions_omitted", voice)
        self.assertEqual([x["question"] for x in p["previous_exchanges"]],
                         [f"Aside {i}" for i in range(2, 6)])
        self.assertEqual(p["older_exchanges_omitted"], 2)

    def test_oversized_authorised_voice_fails_closed_instead_of_silently_truncating(self):
        contributions = [
            {"turn_id": f"2026112600000000000{i}-abc123abc123",
             "provider": "operator", "text": "confidential decision " + ("x" * 2000)}
            for i in range(12)
        ]
        with self.assertRaisesRegex(ValueError, "complete authorised output exceeds"):
            self.svc.preview(question="Report our whole position.",
                             room_output={"agenda": "Oversized agenda",
                                          "contributions": contributions})
        self.assertEqual(self.supplier.calls, [])
        self.assertFalse((self.store / "snug" / "live" / "default" / "attempts").exists())

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
        self.assertEqual(saved["turns"][0]["payload"]["model"], MODEL)
        self.assertIn("input", saved["turns"][0]["payload"])
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

    def test_operator_can_post_without_supplier_and_future_context_is_explicit(self):
        offline = LiveChatService(self.store, adapters={})
        post = offline.post_operator(text="  Standing order: listen first.  ")["turn"]
        self.assertEqual(post["provider"], "operator")
        self.assertEqual(post["status"], "posted")
        self.assertEqual(post["question"], "Standing order: listen first.")
        self.assertIsNone(post["answer"])
        self.assertEqual(post["payload"], {})
        self.assertEqual(offline.session()["live_providers"], [])
        with self.assertRaisesRegex(PermissionError, "unavailable"):
            offline.preview(question="No supplier here")
        folder = self.store / "snug" / "live" / "default"
        self.assertEqual(len(list((folder / "attempts").glob("*.json"))), 0)
        self.assertFalse((folder / "outcomes").exists())
        path = folder / "turns" / (post["turn_id"] + ".json")
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        again = LiveChatService(self.store, adapter=self.supplier)
        self.assertEqual(again.session()["turns"][0]["question"], post["question"])
        next_preview = again.preview(question="What is on the table?")
        self.assertEqual(next_preview["previous_exchanges"][0]["provider"], "operator")
        self.assertEqual(next_preview["previous_exchanges"][0]["question"], post["question"])
        self.assertEqual(next_preview["previous_exchanges"][0]["answer"], "")

    def test_post_is_bounded_and_invalidates_prior_supplier_review(self):
        for value in ("", " ", "x" * 2001, None):
            with self.assertRaises(ValueError):
                self.svc.post_operator(text=value)
        preview = self.svc.preview(question="Before the convenor posts")
        self.svc.post_operator(text="A new fact is on the table")
        self.assertEqual(len(self.supplier.calls), 0)
        with self.assertRaisesRegex(PermissionError, "changed after review"):
            self.svc.send(approval_token=preview["approval_token"])

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


    def test_room_output_complete_history_minimal_projection_and_lifecycle(self):
        folder = self.store / "hosting" / "inkytech"
        folder.mkdir(parents=True)
        (folder / "notes.txt").write_text("private corpus marker")
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

            def call(route, data=None, expected=200):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                try:
                    conn.request("POST" if data is not None else "GET", route,
                                 body=json.dumps(data) if data is not None else None,
                                 headers={"Content-Type": "application/json",
                                          "Origin": f"http://127.0.0.1:{port}",
                                          "X-Snug-Client": "demo-local"})
                    response = conn.getresponse()
                    body = json.loads(response.read())
                    self.assertEqual(response.status, expected, body)
                    return body
                finally:
                    conn.close()

            try:
                prefix = "/api/live/"
                call(prefix + "post", {"text": "Original agenda"})
                call(prefix + "rooms/configure", {"room_id": "default",
                     "standing_orders": "Private standing orders"})
                preview = call(prefix + "preview", {"question": "Private supplier prompt"})
                self.assertEqual(preview["room_standing_orders"], "Private standing orders")
                event = call(prefix + "send", {"approval_token": preview["approval_token"]})["turn"]
                event_id = event["turn_id"]
                self.assertEqual(event["context"]["room_standing_orders"],
                                 "Private standing orders")
                self.assertEqual(json.loads(event["payload"]["input"])["room_standing_orders"],
                                 "Private standing orders")
                call(prefix + "rooms/configure", {"room_id": "default",
                                                   "voice_event": event_id})
                for i in range(101):
                    call(prefix + "post", {"text": f"Ordinary deliberation {i}"})
                self.assertEqual(len(call(prefix + "session")["turns"]), 100)
                output = call(prefix + "output")
                decision_preview = call(prefix + "preview",
                                        {"question": "What is our decision?"})
                self.assertEqual(
                    decision_preview["room_authorised_output"]["contributions"],
                    [{"turn_id": event_id, "provider": "openai",
                      "text": event["answer"]}])
                self.assertEqual(decision_preview["room_authorised_output"]["agenda"],
                                 "Original agenda")
                self.assertEqual(output, {"agenda": "Original agenda",
                    "contributions": [{"turn_id": event_id, "provider": "openai",
                                       "text": event["answer"]}]})
                self.assertNotIn("Private supplier prompt", json.dumps(output))
                self.assertNotIn("Private standing orders", json.dumps(output))
                call(prefix + "rooms/configure", {"room_id": "default", "redact_event": event_id})
                self.assertEqual(call(prefix + "output")["contributions"], [])
                withdrawn = call(prefix + "preview", {"question": "Still authorised?"})
                self.assertEqual(withdrawn["room_authorised_output"]["contributions"], [])
                call(prefix + "rooms/configure", {"room_id": "default", "voice_event": event_id})
                restored = call(prefix + "preview", {"question": "Now authorised?"})
                self.assertEqual(len(restored["room_authorised_output"]["contributions"]), 1)
                self.assertEqual(call(prefix + "output"), output)
                other = call(prefix + "rooms/create", {"title": "Other"})["id"]
                call(prefix + "rooms/configure", {"room_id": other, "voice_event": event_id}, 400)
                call(prefix + "rooms/configure", {"room_id": "default", "voice_event": event_id,
                     "redact_event": event_id}, 400)
                call(prefix + "output?room_id=default&room_id=" + other, expected=400)
                pending = call(prefix + "preview", {"question": "Before orders change"})
                call(prefix + "rooms/configure", {"room_id": "default",
                     "standing_orders": "Updated meeting rules"})
                call(prefix + "send", {"approval_token": pending["approval_token"]}, 400)
                pending = call(prefix + "preview", {"question": "Before closure"})
                self.assertEqual(pending["room_standing_orders"], "Updated meeting rules")
                call(prefix + "rooms/configure", {"room_id": "default", "state": "closed"})
                call(prefix + "output", expected=400)
                call(prefix + "post", {"text": "Forbidden"}, 400)
                call(prefix + "rooms/configure", {"room_id": "default", "state": "open"})
                call(prefix + "send", {"approval_token": pending["approval_token"]}, 400)
                self.assertEqual(len(self.supplier.calls), 1)
                self.assertEqual(call(prefix + "output"), output)
                self.supplier.fail = True
                pending = call(prefix + "preview", {"question": "Unknown outcome"})
                unknown = call(prefix + "send", {"approval_token": pending["approval_token"]}, 502)
                call(prefix + "rooms/configure", {"room_id": "default",
                     "voice_event": unknown["turn_id"]}, 400)
                self.assertEqual(call(prefix + "output"), output)
                metadata = self.store / "snug" / "live" / "default" / "room.json"
                original = json.loads(metadata.read_text())
                for corrupt in ({"state": "unknown"}, {"state": None},
                                {"room_voice": None}, {"room_voice": [event_id, event_id]},
                                {"redacted": ["20261123142345678901-abcdef123456"]}):
                    with self.subTest(corrupt=corrupt):
                        metadata.write_text(json.dumps({**original, **corrupt}))
                        call(prefix + "output", expected=400)
                        call(prefix + "post", {"text": "Must not be accepted"}, 400)
                metadata.write_text(json.dumps(original))
                self.assertEqual(call(prefix + "output"), output)
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
