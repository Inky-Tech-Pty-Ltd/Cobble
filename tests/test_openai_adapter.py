"""Keyless offline tests for OpenAI supplier and shared exchange."""
import tempfile
import unittest
from pathlib import Path
from dataclasses import replace

from cobble.openai_adapter import (
    OpenAIAdapter, MODEL, prepare_message, check_preflight, _parse_reply,
)
from cobble.snug_exchange import ExchangeRequest, exchange, read_event
from cobble.local_search import build, search


def response():
    return {
        "id": "resp_synthetic", "object": "response",
        "model": MODEL, "status": "completed", "error": None,
        "output": [{
            "type": "message", "role": "assistant", "id": "msg_test",
            "content": [{"type": "output_text", "text": "VIOLET-OTTER-73"}],
        }],
        "usage": {"input_tokens": 86, "output_tokens": 24},
    }


class OpenAIAdapterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = Path(temporary.name) / "private"
        note = self.store / "hosting" / "inkytech" / "note.md"
        note.parent.mkdir(parents=True)
        note.write_text("Fictional phrase VIOLET-OTTER-73")
        self.index = self.store / "index" / "search.sqlite3"
        build(self.store, self.index)
        self.docid = search(self.index, "VIOLET")[0]["id"]
        self.req = ExchangeRequest(
            participant="operator", question="What is the phrase?",
            selected_memories=({"document_id": self.docid, "source": "inkytech",
                                "text": "Fictional phrase VIOLET-OTTER-73"},),
            previous_exchanges=(),
        )

    def test_preview_no_secret_and_no_memory_text(self):
        plan = OpenAIAdapter().preview(self.req)
        self.assertEqual(plan["model"], MODEL)
        self.assertEqual(plan["selected_memories"][0]["id"], self.docid)
        self.assertNotIn("VIOLET-OTTER", str(plan))
        self.assertFalse(plan["network_enabled"])
        self.assertFalse(plan["provider_storage_requested"])

    def test_default_network_denied_even_with_key(self):
        with self.assertRaises(PermissionError):
            OpenAIAdapter(key="test-key").answer(self.req)

    def test_explicit_payload_only_and_store_disabled(self):
        payload = prepare_message(self.req)
        self.assertFalse(payload["store"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["tools"], [])
        self.assertIn("VIOLET-OTTER", payload["input"])
        self.assertIn("estimated_max_cost_usd", check_preflight(payload))

    def test_prior_exchange_opt_in(self):
        prior = {"event_id": "a"*32, "provider": "mistral", "answer": "The phrase is VIOLET-OTTER-73"}
        self.assertIn("VIOLET-OTTER", prepare_message(replace(
            self.req, selected_memories=(), previous_exchanges=(prior,)))["input"])
        self.assertNotIn("previous_response_id", str(prepare_message(self.req)))

    def test_budget_blocks_before_transport(self):
        calls = []
        def fake(payload):
            calls.append(True)
            return response()
        with self.assertRaisesRegex(ValueError, "byte ceiling"):
            OpenAIAdapter(allow_network=True, transport=fake).answer(replace(
                self.req, question="x"*20000))
        self.assertFalse(calls)

    def test_synthetic_accounting(self):
        reply = OpenAIAdapter(allow_network=True,
            transport=lambda _: response()).answer(self.req)
        self.assertEqual(reply.usage["kind"], "mock-openai-api")
        self.assertEqual(reply.usage["network_calls"], 0)
        self.assertEqual(reply.request_id, "resp_synthetic")

    def test_reasoning_item_precedes_final_text(self):
        example = response()
        example["output"].insert(0, {
            "id": "rs_test", "type": "reasoning", "summary": []
        })
        reply = _parse_reply(example, synthetic=True)
        self.assertEqual(reply.text, "VIOLET-OTTER-73")
        self.assertNotIn("reasoning", reply.text)

    def test_unexpected_tool_output_rejected(self):
        broken = response()
        broken["output"] = [{"type": "web_search_call"}]
        with self.assertRaisesRegex(ValueError, "Unexpected OpenAI output item"):
            _parse_reply(broken, synthetic=True)

    def test_reasoning_without_message_rejected(self):
        broken = response()
        broken["output"] = [{"type": "reasoning", "summary": []}]
        with self.assertRaisesRegex(ValueError, "text missing"):
            _parse_reply(broken, synthetic=True)

    def test_incomplete_response_rejected(self):
        broken = response()
        broken["status"] = "incomplete"
        with self.assertRaisesRegex(ValueError, "not completed"):
            _parse_reply(broken, synthetic=True)

    def test_adapter_required(self):
        with self.assertRaises(PermissionError):
            exchange(store=self.store, index=self.index, question="Hi",
                     participant="operator", provider="openai")

    def test_string_reply_rejected(self):
        class Bad:
            name = "openai"
            def answer(self, request):
                return "unaccounted"
        with self.assertRaisesRegex(ValueError, "accounted"):
            exchange(store=self.store, index=self.index, question="Hi",
                     participant="operator", provider="openai", adapter=Bad())

    def test_synthetic_exchange_saved(self):
        adapter = OpenAIAdapter(allow_network=True, transport=lambda _: response())
        event = exchange(store=self.store, index=self.index,
                         question="What is the phrase?", participant="operator",
                         provider="openai", adapter=adapter,
                         memory_ids=(self.docid,), allowed_sources=("inkytech",))
        saved = read_event(self.store, event["event_id"])
        self.assertEqual(saved["provider"], "openai")
        self.assertEqual(saved["usage"]["kind"], "mock-openai-api")
        self.assertEqual(saved["usage"]["network_calls"], 0)
        self.assertEqual(len(saved["selected_memories"]), 1)

    def test_source_scope_prevents_transmission(self):
        adapter = OpenAIAdapter(allow_network=True,
            transport=lambda _: self.fail("Transport called"))
        with self.assertRaises(PermissionError):
            exchange(store=self.store, index=self.index, question="Hi",
                     participant="operator", provider="openai", adapter=adapter,
                     memory_ids=(self.docid,), allowed_sources=("github",))


if __name__ == "__main__":
    unittest.main()
