"""Claude adapter tests are fully synthetic, offline, keyless and no-spend."""
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cobble.local_search import build, search
from cobble.snug_exchange import ExchangeRequest, exchange, read_event
from cobble.claude_adapter import (
    API_VERSION, MODEL, ClaudeAdapter, MAX_OUTPUT_TOKENS,
    _parse_reply, check_preflight, prepare_message, predicted_cost_usd,
)


def fixture_response():
    return {
        "id": "msg_synthetic1",
        "type": "message", "role": "assistant", "model": MODEL,
        "content": [{"type": "text", "text": "Synthetic response; no network"}],
        "usage": {"input_tokens": 80, "output_tokens": 16},
        "stop_reason": "end_turn",
    }


class ClaudeAdapterTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.store = Path(d.name) / "private"
        note = self.store / "hosting" / "inkytech" / "note.md"
        note.parent.mkdir(parents=True)
        note.write_text("Koala memory remains local", encoding="utf-8")
        self.index = self.store / "index" / "search.sqlite3"
        build(self.store, self.index)
        self.docid = search(self.index, "koala")[0]["id"]
        self.item = {
            "document_id": self.docid, "source": "inkytech",
            "reference": "note.md", "title": "note.md",
            "text": "Koala memory remains local",
        }
        self.request = ExchangeRequest(
            participant="operator", question="What is this?", 
            selected_memories=(self.item,), previous_exchanges=())

    def test_preview_requires_no_key_and_does_not_disclose_text(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "synthetic-secret"}):
            plan = ClaudeAdapter().preview(self.request)
        self.assertFalse(plan["network_enabled"])
        self.assertEqual(plan["model"], MODEL)
        self.assertEqual(plan["selected_memories"][0]["id"], self.docid)
        self.assertNotIn("Koala memory", str(plan))
        self.assertNotIn("synthetic-secret", str(plan))

    def test_default_adapter_cannot_send_even_with_a_key(self):
        adapter = ClaudeAdapter(key="fake-key")
        with self.assertRaisesRegex(PermissionError, "not enabled"):
            adapter.answer(self.request)

    def test_payload_contains_only_exact_selected_memories(self):
        payload = prepare_message(self.request)
        self.assertEqual(payload["model"], MODEL)
        self.assertEqual(payload["max_tokens"], MAX_OUTPUT_TOKENS)
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn("Koala memory", payload["messages"][0]["content"])
        self.assertNotIn("internet", str(payload))
        self.assertIn("estimated_max_cost_usd", check_preflight(payload))

    def test_selected_previous_exchange_appears_only_when_passed(self):
        previous = {"event_id": "a" * 32, "provider": "fixture-amber",
                    "participant": "operator", "question": "Earlier question",
                    "answer": "Earlier answer"}
        req = replace(self.request, previous_exchanges=(previous,))
        self.assertIn("Earlier answer", str(prepare_message(req)))
        self.assertNotIn("Earlier answer", str(prepare_message(self.request)))

    def test_payload_ceiling_blocks_before_transport(self):
        huge = replace(self.request, question="x" * 20000)
        called = []
        def never(payload):
            called.append(True)
            return fixture_response()
        with self.assertRaisesRegex(ValueError, "byte ceiling"):
            ClaudeAdapter(allow_network=True, transport=never).answer(huge)
        self.assertEqual(called, [])

    def test_mocked_response_has_truthful_accounting(self):
        reply = ClaudeAdapter(allow_network=True,
                              transport=lambda payload: fixture_response()).answer(
                                  self.request)
        self.assertEqual(reply.usage["kind"], "mock-claude-api")
        self.assertEqual(reply.usage["network_calls"], 0)
        self.assertEqual(reply.usage["input_tokens"], 80)
        self.assertEqual(reply.usage["output_tokens"], 16)
        self.assertEqual(reply.usage["estimated_provider_cost_usd"],
                         str(predicted_cost_usd(80, 16)))
        self.assertEqual(reply.model, MODEL)
        self.assertEqual(reply.request_id, "msg_synthetic1")

    def test_bad_api_reply_rejected_not_saved(self):
        broken = fixture_response()
        broken["content"] = [{"type": "tool_use", "id": "tool_123"}]
        with self.assertRaisesRegex(ValueError, "text-only"):
            _parse_reply(broken, synthetic=True)
        self.assertFalse((self.store / "snug" / "events").exists())

    def test_live_provider_requires_explicit_adapter(self):
        with self.assertRaises(PermissionError):
            exchange(store=self.store, index=self.index, question="Hello",
                     participant="operator", provider="claude")
        self.assertFalse((self.store / "snug" / "events").exists())

    def test_live_provider_rejects_bare_string_accounting(self):
        class Fake:
            name = "claude"
            def answer(self, request):
                return "I cost zero dollars"
        with self.assertRaisesRegex(ValueError, "accounted reply"):
            exchange(store=self.store, index=self.index, question="Hello",
                     participant="operator", provider="claude", adapter=Fake())
        self.assertFalse((self.store / "snug" / "events").exists())

    def test_synthetic_provider_reply_integrates_with_exchange(self):
        fake = ClaudeAdapter(allow_network=True,
                             transport=lambda payload: fixture_response())
        event = exchange(
            store=self.store, index=self.index, question="Can you see the koala?",
            participant="operator", provider="claude",
            adapter=fake, memory_ids=(self.docid,), allowed_sources=("inkytech",))
        saved = read_event(self.store, event["event_id"])
        self.assertEqual(saved["provider"], "claude")
        self.assertEqual(saved["provider_model"], MODEL)
        self.assertEqual(saved["provider_request_id"], "msg_synthetic1")
        self.assertEqual(saved["usage"]["network_calls"], 0)
        self.assertEqual(saved["usage"]["kind"], "mock-claude-api")
        self.assertEqual(len(saved["selected_memories"]), 1)

    def test_existing_fixture_still_records_offline_usage(self):
        event = exchange(store=self.store, index=self.index, question="Hello",
                         participant="operator", provider="fixture-amber")
        self.assertEqual(event["usage"]["kind"], "offline-fixture")
        self.assertEqual(event["usage"]["network_calls"], 0)
        self.assertIsNone(event["provider_model"])

    def test_invalid_scoped_memory_is_never_disclosed(self):
        fake = ClaudeAdapter(allow_network=True,
                             transport=lambda payload: self.fail("Called transport"))
        with self.assertRaises(PermissionError):
            exchange(
                store=self.store, index=self.index, question="What is this?",
                participant="operator", provider="claude", adapter=fake,
                memory_ids=(self.docid,), allowed_sources=("github",))
        self.assertFalse((self.store / "snug" / "events").exists())


if __name__ == "__main__":
    unittest.main()
