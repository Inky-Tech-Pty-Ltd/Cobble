"""Offline regression for isolated and explicitly scoped provider handover."""
import tempfile
import unittest
from pathlib import Path

from cobble.claude_adapter import ProviderReply
from cobble.snug_exchange import read_event
from scripts.synthetic_handover import (
    _stage, _prepare, FIRST_QUESTION, SECOND_QUESTION, MEMORY, CONSENT,
)


class MockSupplier:
    def __init__(self, name, root, fail=False):
        self.name, self.root, self.fail = name, root, fail
        self.requests = []

    def answer(self, request):
        self.requests.append(request)
        marker = self.root / "snug" / "handover" / (self.name + "-attempt.json")
        assert marker.is_file(), "Audit must precede supplier call"
        if self.fail:
            raise TimeoutError("No automatic retry")
        if self.name == "claude":
            assert request.question == FIRST_QUESTION
            assert len(request.selected_memories) == 1
            assert MEMORY in request.selected_memories[0]["text"]
            assert request.previous_exchanges == ()
            response = "The fictional password is VIOLET-OTTER-73."
            kind = "mock-claude-api"
        else:
            assert request.question == SECOND_QUESTION
            assert request.selected_memories == ()
            assert len(request.previous_exchanges) == 1
            assert "VIOLET-OTTER-73" in request.previous_exchanges[0]["answer"]
            response = "VIOLET-OTTER-73"
            kind = "mock-openai-api" if self.name == "openai" else "mock-mistral-api"
        return ProviderReply(
            text=response, model="synthetic", request_id="synthetic",
            usage={"kind": kind, "network_calls": 0,
                   "input_tokens": 12, "output_tokens": 5,
                   "estimated_provider_cost_usd": "0",
                   "cost_is_estimate": True},
        )


class HandoverTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "handover"
        self.claude = MockSupplier("claude", self.root)
        self.mistral = MockSupplier("mistral", self.root)
        self.openai = MockSupplier("openai", self.root)

    def stage(self, phase, adapter=None, **kw):
        return _stage(self.root, phase, adapter or (
            {"claude": self.claude, "mistral": self.mistral,
             "openai": self.openai}[phase]), **kw)

    def test_full_handover_preserves_local_memory_without_disclosing_again(self):
        first = self.stage("claude")
        second = self.stage("mistral")
        self.assertIn("VIOLET-OTTER-73", second["answer"])
        self.assertEqual(first["selected_memories"], 1)
        self.assertEqual(first["previous_exchanges"], 0)
        self.assertEqual(second["selected_memories"], 0)
        self.assertEqual(second["previous_exchanges"], 1)
        record = read_event(self.root, second["event_id"])
        self.assertEqual(record["previous_exchange_ids"], [first["event_id"]])
        self.assertEqual(record["selected_memories"], [])
        self.assertEqual(record["usage"]["network_calls"], 0)

    def test_mistral_cannot_go_first(self):
        with self.assertRaises(PermissionError):
            self.stage("mistral")
        self.assertEqual(self.mistral.requests, [])

    def test_second_stage_does_not_change_original_source(self):
        self.stage("claude")
        index, _, docid = _prepare(self.root)
        self.stage("mistral")
        index2, _, docid2 = _prepare(self.root)
        self.assertEqual(docid, docid2)
        self.assertEqual(index, index2)

    def test_first_stage_cannot_repeat(self):
        self.stage("claude")
        with self.assertRaises(FileExistsError):
            self.stage("claude")
        self.assertEqual(len(self.claude.requests), 1)

    def test_second_stage_cannot_repeat(self):
        self.stage("claude")
        self.stage("mistral")
        with self.assertRaises(FileExistsError):
            self.stage("mistral")
        self.assertEqual(len(self.mistral.requests), 1)

    def test_failure_is_recorded_as_unknown_and_never_retried(self):
        bad = MockSupplier("claude", self.root, fail=True)
        with self.assertRaises(TimeoutError):
            self.stage("claude", adapter=bad)
        ledger = self.root / "snug" / "handover"
        self.assertTrue((ledger / "claude-outcome.json").is_file())
        with self.assertRaises(FileExistsError):
            self.stage("claude")
        self.assertFalse(self.claude.requests)

    def test_live_gate_rejects_missing_consent(self):
        with self.assertRaises(PermissionError):
            self.stage("claude", live=True, confirm="no",
                       limit_confirmed=True)
        self.assertFalse(self.claude.requests)
        self.assertFalse((self.root / "snug" / "handover" /
                          "claude-attempt.json").exists())

    def test_live_gate_rejects_missing_spend_limit(self):
        with self.assertRaises(PermissionError):
            self.stage("claude", live=True, confirm=CONSENT,
                       limit_confirmed=False)
        self.assertFalse(self.claude.requests)

    def test_live_gate_allows_explicit_synthetic_adapter(self):
        result = self.stage("claude", live=True, confirm=CONSENT,
                            limit_confirmed=True)
        self.assertEqual(result["usage"]["network_calls"], 0)

    def test_three_suppliers_with_no_raw_memory_at_gpt(self):
        first = self.stage("claude")
        second = self.stage("mistral")
        third = self.stage("openai")
        self.assertEqual(third["selected_memories"], 0)
        self.assertEqual(third["previous_exchanges"], 1)
        self.assertIn("VIOLET-OTTER-73", third["answer"])
        self.assertEqual(len(self.openai.requests), 1)
        previous = self.openai.requests[0].previous_exchanges[0]
        self.assertEqual(previous["event_id"], second["event_id"])
        self.assertEqual(previous["provider"], "mistral")
        self.assertEqual(previous["answer"], second["answer"])
        self.assertEqual(read_event(self.root, third["event_id"])["previous_exchange_ids"],
                         [second["event_id"]])
        self.assertEqual(read_event(self.root, third["event_id"])["selected_memories"], [])
        self.assertEqual(read_event(self.root, first["event_id"])["provider"], "claude")

    def test_gpt_cannot_start_without_mistral(self):
        self.stage("claude")
        with self.assertRaises(PermissionError):
            self.stage("openai")
        self.assertFalse(self.openai.requests)

    def test_gpt_single_attempt(self):
        self.stage("claude")
        self.stage("mistral")
        self.stage("openai")
        with self.assertRaises(FileExistsError):
            self.stage("openai")
        self.assertEqual(len(self.openai.requests), 1)

    def test_gpt_live_requires_new_consent(self):
        self.stage("claude")
        self.stage("mistral")
        with self.assertRaises(PermissionError):
            self.stage("openai", live=True, confirm="wrong",
                       limit_confirmed=True)
        self.assertFalse(self.openai.requests)


if __name__ == "__main__":
    unittest.main()
