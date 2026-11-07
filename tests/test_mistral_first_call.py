"""Strictly offline synthetic tests for the first Mistral API call gate."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cobble.mistral_adapter import MODEL, ProviderReply
from cobble.mistral_first_call import (
    CONSENT, HELLO, first_call_status, first_live_hello,
)
from cobble.local_search import build
from cobble.snug_exchange import read_event


class CaptureAdapter:
    name = "mistral"

    def __init__(self, store=None, fail=False):
        self.called = 0
        self.store = store
        self.fail = fail

    def answer(self, request):
        self.called += 1
        assert request.question == HELLO
        assert request.participant == "operator"
        assert request.selected_memories == ()
        assert request.previous_exchanges == ()
        if self.store:
            marker = self.store / "snug" / "provider-attempts" / "first-live-mistral.json"
            assert marker.exists(), "Audit marker must precede provider call"
        if self.fail:
            raise RuntimeError("synthetic timeout that may have been charged")
        return ProviderReply(
            text="Hello from a synthetic Mistral.",
            model=MODEL,
            request_id="cmpl_synthetic_for_test",
            usage={
                "kind": "mock-mistral-api",
                "network_calls": 0,
                "input_tokens": 48,
                "output_tokens": 12,
                "estimated_provider_cost_usd": "0.0000108",
                "cost_is_estimate": True,
            },
        )


class FirstLiveCallTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Path(temp.name) / "private"
        self.index = self.store / "index" / "search.sqlite3"
        build(self.store, self.index)

    def call(self, **overrides):
        options = {
            "store": self.store,
            "index": self.index,
            "live": True,
            "confirm": CONSENT,
            "workspace_limit_confirmed": True,
            "api_key": "synthetic-key-only",
            "adapter": CaptureAdapter(self.store),
        }
        options.update(overrides)
        return first_live_hello(**options)

    def attempts(self):
        root = self.store / "snug" / "provider-attempts"
        return list(root.iterdir()) if root.exists() else []

    def test_default_does_not_call_or_record(self):
        fake = CaptureAdapter(self.store)
        with self.assertRaises(PermissionError):
            self.call(live=False, adapter=fake)
        self.assertEqual(fake.called, 0)
        self.assertEqual(self.attempts(), [])

    def test_wrong_disclosure_phrase_prevents_call(self):
        with self.assertRaises(PermissionError):
            self.call(confirm="YES")
        self.assertEqual(self.attempts(), [])

    def test_workspace_spending_control_must_be_confirmed(self):
        with self.assertRaises(PermissionError):
            self.call(workspace_limit_confirmed=False)
        self.assertEqual(self.attempts(), [])

    def test_missing_api_key_never_creates_attempt(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(PermissionError):
                self.call(api_key=None)
        self.assertEqual(self.attempts(), [])

    def test_first_hello_creates_attempt_before_mock_transport(self):
        fake = CaptureAdapter(self.store)
        outcome = self.call(adapter=fake)
        self.assertEqual(fake.called, 1)
        self.assertEqual(outcome["state"], "completed")
        self.assertEqual(outcome["inherited_memories_sent"], 0)
        self.assertEqual(outcome["usage"]["network_calls"], 0)
        self.assertEqual(first_call_status(self.store)["state"], "completed")
        event = read_event(self.store, outcome["event_id"])
        self.assertEqual(event["question"], HELLO)
        self.assertEqual(event["selected_memories"], [])
        self.assertEqual(event["previous_exchange_ids"], [])
        self.assertEqual(event["usage"]["kind"], "mock-mistral-api")
        self.assertEqual(len(self.attempts()), 2)
        for file in self.attempts():
            self.assertEqual(file.stat().st_mode & 0o077, 0)

    def test_second_call_is_blocked_even_if_first_succeeded(self):
        self.call()
        fake = CaptureAdapter(self.store)
        with self.assertRaises(FileExistsError):
            self.call(adapter=fake)
        self.assertEqual(fake.called, 0)
        self.assertEqual(len(self.attempts()), 2)

    def test_failed_attempt_is_recorded_as_uncertain_not_zero_charge(self):
        fake = CaptureAdapter(self.store, fail=True)
        with self.assertRaisesRegex(RuntimeError, "synthetic timeout"):
            self.call(adapter=fake)
        self.assertEqual(fake.called, 1)
        self.assertEqual(first_call_status(self.store)["state"], "outcome_unknown")
        self.assertEqual(len(self.attempts()), 2)
        outcome = next(x for x in self.attempts() if x.name.endswith(".outcome.json"))
        content = json.loads(outcome.read_text())
        self.assertEqual(content["status"], "outcome_unknown")
        self.assertIsNone(content["actual_charge_usd"])
        self.assertNotIn("synthetic timeout", outcome.read_text())

    def test_failed_first_call_also_blocks_automatic_retry(self):
        with self.assertRaises(RuntimeError):
            self.call(adapter=CaptureAdapter(self.store, fail=True))
        fake = CaptureAdapter(self.store)
        with self.assertRaises(FileExistsError):
            self.call(adapter=fake)
        self.assertEqual(fake.called, 0)

    def test_started_audit_contains_no_key_or_source_content(self):
        self.call()
        audit = (self.store / "snug" / "provider-attempts"
                 / "first-live-mistral.json").read_text()
        self.assertNotIn("synthetic-key-only", audit)
        self.assertEqual(json.loads(audit)["selected_memories"], 0)
        self.assertIn("estimated_max_cost_usd", audit)
        self.assertIsNone(json.loads(audit)["actual_charge_usd"])

    def test_status_before_first_call_is_never_attempted(self):
        self.assertEqual(first_call_status(self.store),
                         {"reserved": False, "state": "never-attempted"})


if __name__ == "__main__":
    unittest.main()
