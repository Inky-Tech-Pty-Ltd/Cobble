"""Synthetic tests for Snug's offline provider-neutral conversation seam."""
import json
import tempfile
import unittest
from pathlib import Path

from cobble.local_search import build, search
from cobble.snug_exchange import exchange, read_event


class SnugExchangeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "private"
        self.root.mkdir()
        file = self.root / "hosting" / "inkytech" / "note.md"
        file.parent.mkdir(parents=True)
        file.write_text("Lighthouse memory belongs to the store.", encoding="utf-8")
        other = self.root / "hosting" / "villagelink" / "other.md"
        other.parent.mkdir(parents=True)
        other.write_text("Willow independence is valuable.", encoding="utf-8")
        self.index = self.root / "index" / "search.sqlite3"
        build(self.root, self.index)
        self.first_id = search(self.index, "lighthouse")[0]["id"]
        self.other_id = search(self.index, "willow")[0]["id"]

    def ask(self, **overrides):
        kwargs = dict(store=self.root, index=self.index,
                      question="What do you remember?", participant="joe",
                      provider="fixture-amber",
                      allowed_sources=["inkytech"],
                      memory_ids=[self.first_id])
        kwargs.update(overrides)
        return exchange(**kwargs)

    def records(self):
        return list((self.root / "snug" / "events").glob("*.json")) if (
            self.root / "snug" / "events").exists() else []

    def test_one_exchange_preserves_exact_selected_memory_and_provenance(self):
        event = self.ask()
        saved = read_event(self.root, event["event_id"])
        self.assertEqual(saved, event)
        self.assertEqual(saved["usage"]["network_calls"], 0)
        self.assertEqual(saved["selected_memories"][0]["source"], "inkytech")
        self.assertIn("Lighthouse", saved["selected_memories"][0]["text"])
        self.assertEqual(len(self.records()), 1)
        self.assertEqual(self.records()[0].stat().st_mode & 0o077, 0)

    def test_switch_provider_retains_explicit_prior_exchange(self):
        first = self.ask()
        second = self.ask(provider="fixture-indigo", memory_ids=[],
                          allowed_sources=[], prior_ids=[first["event_id"]])
        self.assertEqual(second["provider"], "fixture-indigo")
        self.assertEqual(second["previous_exchange_ids"], [first["event_id"]])
        self.assertIn("1 expressly supplied", second["answer"])
        self.assertEqual(read_event(self.root, first["event_id"]), first)
        self.assertEqual(len(self.records()), 2)

    def test_unauthorised_context_fails_closed_without_writing(self):
        with self.assertRaises(PermissionError):
            self.ask(memory_ids=[self.other_id], allowed_sources=["inkytech"])
        self.assertEqual(self.records(), [])

    def test_no_implicit_memory_access(self):
        event = self.ask(memory_ids=[], allowed_sources=[])
        self.assertEqual(event["selected_memories"], [])
        self.assertIn("0 selected", event["answer"])

    def test_previous_exchange_requires_explicit_id(self):
        first = self.ask()
        second = self.ask(memory_ids=[], allowed_sources=[])
        self.assertNotIn(first["event_id"], second["previous_exchange_ids"])
        with self.assertRaises(FileNotFoundError):
            self.ask(memory_ids=[], allowed_sources=[],
                     prior_ids=["a" * 32])
        self.assertEqual(len(self.records()), 2)

    def test_bad_indexed_id_and_unknown_source_fail(self):
        with self.assertRaises(KeyError):
            self.ask(memory_ids=["0" * 24])
        with self.assertRaises(ValueError):
            self.ask(allowed_sources=["internet"])
        self.assertEqual(self.records(), [])

    def test_bad_adapter_cannot_impersonate_provider(self):
        class Impostor:
            name = "fixture-indigo"
            def answer(self, request):
                raise AssertionError("must not be invoked")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.ask(adapter=Impostor())
        self.assertEqual(self.records(), [])

    def test_adapter_receives_only_selected_data(self):
        class Capture:
            name = "fixture-amber"
            request = None
            def answer(self, request):
                self.request = request
                return "Received chosen memories"
        adapter = Capture()
        first = self.ask(adapter=adapter)
        self.assertEqual(len(adapter.request.selected_memories), 1)
        self.assertEqual(adapter.request.selected_memories[0]["document_id"],
                         self.first_id)
        self.assertEqual(adapter.request.previous_exchanges, ())
        self.assertEqual(first["answer"], "Received chosen memories")

    def test_failure_never_logs_a_successful_exchange(self):
        class Failure:
            name = "fixture-amber"
            def answer(self, request):
                raise RuntimeError("synthetic provider failure")
        with self.assertRaisesRegex(RuntimeError, "synthetic provider failure"):
            self.ask(adapter=Failure())
        self.assertEqual(self.records(), [])

    def test_no_path_traversal_in_event_lookup(self):
        with self.assertRaises(ValueError):
            read_event(self.root, "../../secret")
        self.assertEqual(self.records(), [])

    def test_event_is_not_overwritten(self):
        event = self.ask()
        path = self.records()[0]
        old_bytes = path.read_bytes()
        with self.assertRaises(FileExistsError):
            from cobble.snug_exchange import _save_event
            _save_event(self.root, event)
        self.assertEqual(path.read_bytes(), old_bytes)


if __name__ == "__main__":
    unittest.main()
