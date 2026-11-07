"""Offline tests for immutable, explicitly authorised OpenAI first call."""
from pathlib import Path
import tempfile
import unittest

from cobble.openai_adapter import OpenAIAdapter, MODEL
from cobble.openai_first_call import CONSENT, REVIEWED_CONSENT, _request, first_call_status, first_live_hello


def fake_response():
    return {"id": "resp_test", "object": "response", "model": MODEL,
            "status": "completed", "error": None,
            "output": [{"type": "message", "role": "assistant",
                        "content": [{"type": "output_text", "text": "Hello Snug!"}]}],
            "usage": {"input_tokens": 50, "output_tokens": 9}}


class FirstLiveOpenAITests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name) / "private"
        self.index = self.store / "index" / "search.sqlite3"
        self.index.parent.mkdir(parents=True)
        self.index.touch()

    def call(self, **kwargs):
        return first_live_hello(
            store=self.store, index=self.index, api_key="test-only",
            adapter=OpenAIAdapter(allow_network=True,
                                  transport=lambda _: fake_response()),
            **kwargs)

    def test_status_no_marker(self):
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_exact_consent(self):
        with self.assertRaises(PermissionError):
            self.call(live=True, confirm="not exact", project_limit_confirmed=True)
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_limit_required(self):
        with self.assertRaises(PermissionError):
            self.call(live=True, confirm=CONSENT)
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_key_required_before_marker(self):
        with self.assertRaises(PermissionError):
            first_live_hello(store=self.store, index=self.index, live=True,
                             confirm=CONSENT, project_limit_confirmed=True,
                             api_key="")
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_fixed_prompt_without_context(self):
        self.assertEqual(_request().selected_memories, ())
        self.assertEqual(_request().previous_exchanges, ())

    def test_success_one_shot_accounted(self):
        result = self.call(live=True, confirm=CONSENT,
                           project_limit_confirmed=True)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["inherited_memories_sent"], 0)
        self.assertEqual(result["usage"]["network_calls"], 0)
        self.assertEqual(first_call_status(self.store)["state"], "completed")
        with self.assertRaises(FileExistsError):
            self.call(live=True, confirm=CONSENT, project_limit_confirmed=True)

    def test_failure_reserves_no_retry(self):
        class FailingAdapter:
            name = "openai"
            def answer(self, request):
                raise TimeoutError("unknown vendor outcome")
        with self.assertRaises(TimeoutError):
            first_live_hello(store=self.store, index=self.index, live=True,
                confirm=CONSENT, project_limit_confirmed=True,
                api_key="test-only", adapter=FailingAdapter())
        self.assertEqual(first_call_status(self.store)["state"], "outcome_unknown")
        with self.assertRaises(FileExistsError):
            self.call(live=True, confirm=CONSENT, project_limit_confirmed=True)

    def test_absent_index_prevents_attempt(self):
        self.index.unlink()
        with self.assertRaises(FileNotFoundError):
            self.call(live=True, confirm=CONSENT, project_limit_confirmed=True)
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_no_key_leaked_to_receipt(self):
        self.call(live=True, confirm=CONSENT, project_limit_confirmed=True)
        ledger = self.store / "snug" / "provider-attempts"
        self.assertNotIn("test-only", "".join(p.read_text() for p in ledger.iterdir()))

    def test_reviewed_retry_after_unknown_preserves_original(self):
        class FailingAdapter:
            name = "openai"
            def answer(self, request):
                raise TimeoutError("unknown")
        with self.assertRaises(TimeoutError):
            first_live_hello(store=self.store, index=self.index, live=True,
                confirm=CONSENT, project_limit_confirmed=True,
                api_key="test-only", adapter=FailingAdapter())
        original = first_call_status(self.store)
        result = self.call(live=True, confirm=REVIEWED_CONSENT,
                           project_limit_confirmed=True, reviewed_retry=True)
        self.assertEqual(result["review_of_attempt_id"], original["attempt_id"])
        self.assertEqual(first_call_status(self.store), original)
        with self.assertRaises(FileExistsError):
            self.call(live=True, confirm=REVIEWED_CONSENT,
                      project_limit_confirmed=True, reviewed_retry=True)

    def test_reviewed_retry_requires_unknown_outcome(self):
        with self.assertRaises(PermissionError):
            self.call(live=True, confirm=REVIEWED_CONSENT,
                      project_limit_confirmed=True, reviewed_retry=True)
        self.assertFalse(first_call_status(self.store)["reserved"])

    def test_reviewed_retry_requires_distinct_consent(self):
        with self.assertRaises(PermissionError):
            self.call(live=True, confirm=CONSENT,
                      project_limit_confirmed=True, reviewed_retry=True)
        self.assertFalse(first_call_status(self.store)["reserved"])


if __name__ == "__main__":
    unittest.main()
