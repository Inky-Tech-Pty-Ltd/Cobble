"""Synthetic, keyless, no-spend Mistral integration tests."""
from dataclasses import replace
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cobble.local_search import build, search
from cobble.snug_exchange import ExchangeRequest, exchange, read_event
from cobble.mistral_adapter import (
    MODEL, MistralAdapter, _parse_reply, check_preflight, prepare_message,
    predicted_cost_usd,
)


def fake_reply():
    return {
        "id": "cmpl-synthetic-1", "object": "chat.completion",
        "model": "mistral-small-4", "choices": [
            {"index": 0, "message": {"role": "assistant", "content": "Bonjour Snug"},
             "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 70, "completion_tokens": 9},
    }


class MistralTests(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.store = Path(root.name) / "private"
        note = self.store / "hosting" / "inkytech" / "note.md"
        note.parent.mkdir(parents=True)
        note.write_text("Private koala memory", encoding="utf-8")
        self.index = self.store / "index" / "search.sqlite3"
        build(self.store, self.index)
        self.docid = search(self.index, "koala")[0]["id"]
        self.request = ExchangeRequest(
            participant="operator", question="Who are you?",
            selected_memories=({
                "document_id": self.docid, "source": "inkytech",
                "text": "Private koala memory", "reference": "note.md",
            },), previous_exchanges=(),
        )

    def test_preview_keyless_and_no_private_text(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-secret"}):
            preview = MistralAdapter().preview(self.request)
        self.assertFalse(preview["network_enabled"])
        self.assertEqual(preview["model"], MODEL)
        self.assertEqual(preview["selected_memories"][0]["id"], self.docid)
        self.assertNotIn("Private koala", str(preview))
        self.assertNotIn("test-secret", str(preview))

    def test_default_disabled_even_with_key(self):
        with self.assertRaisesRegex(PermissionError, "not enabled"):
            MistralAdapter(key="test-secret").answer(self.request)

    def test_payload_only_selected_memories(self):
        payload = prepare_message(self.request)
        self.assertEqual(payload["tool_choice"], "none")
        self.assertEqual(payload["model"], MODEL)
        self.assertIn("Private koala", payload["messages"][1]["content"])
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("estimated_max_cost_usd", check_preflight(payload))

    def test_prior_exchange_opt_in(self):
        prior = {"event_id": "a" * 32, "provider": "claude", "answer": "Hi",
                 "participant": "operator", "question": "Hello"}
        self.assertIn("Hi", str(prepare_message(replace(
            self.request, previous_exchanges=(prior,)))))
        self.assertNotIn('"answer": "Hi"', str(prepare_message(self.request)))

    def test_preflight_blocks_transport(self):
        called = []
        def fake(payload):
            called.append(1)
            return fake_reply()
        with self.assertRaisesRegex(ValueError, "byte ceiling"):
            MistralAdapter(allow_network=True, transport=fake).answer(
                replace(self.request, question="x" * 20000))
        self.assertFalse(called)

    def test_mock_accounting(self):
        result = MistralAdapter(allow_network=True,
            transport=lambda _: fake_reply()).answer(self.request)
        self.assertEqual(result.usage["network_calls"], 0)
        self.assertEqual(result.usage["kind"], "mock-mistral-api")
        self.assertEqual(result.model, "mistral-small-4")
        self.assertEqual(result.usage["estimated_provider_cost_usd"],
                         str(predicted_cost_usd(70, 9)))

    def test_bad_reply_rejected(self):
        bad = fake_reply()
        bad["choices"][0]["message"]["tool_calls"] = [{"id": "tool"}]
        with self.assertRaisesRegex(ValueError, "tools"):
            _parse_reply(bad, synthetic=True)

    def test_adapter_required(self):
        with self.assertRaises(PermissionError):
            exchange(store=self.store, index=self.index, question="Hello",
                     participant="operator", provider="mistral")

    def test_string_not_accounted(self):
        class Fake:
            name = "mistral"
            def answer(self, request):
                return "A free answer"
        with self.assertRaisesRegex(ValueError, "accounted reply"):
            exchange(store=self.store, index=self.index, question="Hello",
                     participant="operator", provider="mistral", adapter=Fake())

    def test_synthetic_exchange_persists_with_selected_memory(self):
        adapter = MistralAdapter(allow_network=True,
                                 transport=lambda _: fake_reply())
        event = exchange(
            store=self.store, index=self.index, question="Hello",
            participant="operator", provider="mistral", adapter=adapter,
            memory_ids=(self.docid,), allowed_sources=("inkytech",))
        saved = read_event(self.store, event["event_id"])
        self.assertEqual(saved["provider"], "mistral")
        self.assertEqual(saved["provider_model"], "mistral-small-4")
        self.assertEqual(saved["usage"]["network_calls"], 0)
        self.assertEqual(saved["selected_memories"][0]["document_id"], self.docid)

    def test_unapproved_memory_does_not_call_provider(self):
        adapter = MistralAdapter(allow_network=True,
            transport=lambda _: self.fail("Network transport was called"))
        with self.assertRaises(PermissionError):
            exchange(store=self.store, index=self.index, question="Hello",
                     participant="operator", provider="mistral", adapter=adapter,
                     memory_ids=(self.docid,), allowed_sources=("github",))


if __name__ == "__main__":
    unittest.main()
