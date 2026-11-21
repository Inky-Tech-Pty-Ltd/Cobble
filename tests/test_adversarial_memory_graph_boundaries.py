"""Adversarial regression cases for the experimental memory graph contract.

Source observations remain non-authoritative. These tests do not claim
tamper-evident storage, authenticated evidence, or production readiness.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from cobble.graph import inspect_hypothesis
from cobble.observations import observations_for, record_observation
from cobble.stars import mint_star, trace_id
from villagelink.codec import make


class AdversarialMemoryGraphBoundaries(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = Path(temporary.name)
        traces = self.store / "traces"
        traces.mkdir()
        self.members = [f"https://cobble.link/t/{uuid4()}" for _ in range(2)]
        for uri in self.members:
            (traces / (trace_id(uri) + ".json")).write_text(
                json.dumps({"uri": uri, "source_uri": "urn:test:synthetic"}),
                encoding="utf-8",
            )
        self.star = mint_star(self.store, "Synthetic assertion", self.members)

    def member(self, uri):
        graph = inspect_hypothesis(self.store, self.star["A"])
        return next(entry for entry in graph["members"] if entry["trace_uri"] == uri)

    def test_out_of_order_observations_preserve_history(self):
        uri = self.members[0]
        record_observation(self.store, uri, "unavailable",
                           observed_at="2026-10-03T00:00:00Z")
        record_observation(self.store, uri, "available",
                           observed_at="2026-10-01T00:00:00Z")
        records = observations_for(self.store, uri)
        self.assertEqual([r["retrieval"]["status"] for r in records],
                         ["available", "unavailable"])
        self.assertEqual(self.member(uri)["latest_retrieval"], "unavailable")

    def test_available_with_digest_mismatch_remains_unverified(self):
        uri = self.members[0]
        record_observation(self.store, uri, "available",
                           integrity_status="differs_from_recorded_digest")
        result = inspect_hypothesis(self.store, self.star["A"])
        self.assertEqual(result["claim_status"], "asserted-not-verified")
        entry = self.member(uri)
        self.assertEqual(entry["latest_retrieval"], "available")
        self.assertEqual(entry["observations"][-1]["integrity"]["status"],
                         "differs_from_recorded_digest")

    def test_tampered_ray_fails_without_silent_repair(self):
        ray = make(self.star["A"], self.members[0])
        path = self.store / "links" / (hashlib.sha256(ray.encode()).hexdigest() + ".json")
        path.write_text(json.dumps({"uri": make(self.star["A"], self.members[1])}),
                        encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect_hypothesis(self.store, self.star["A"])
        self.assertTrue(path.exists())

    def test_member_trace_replaced_under_same_id_fails_closed(self):
        path = self.store / "traces" / (trace_id(self.members[0]) + ".json")
        path.write_text(json.dumps({"uri": self.members[1]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect_hypothesis(self.store, self.star["A"])

    def test_observation_history_mismatched_trace_is_rejected(self):
        uri = self.members[0]
        event = record_observation(self.store, uri, "available")
        path = self.store / "observations" / trace_id(uri) / (event["id"] + ".json")
        event["trace_uri"] = self.members[1]
        path.write_text(json.dumps(event), encoding="utf-8")
        with self.assertRaises(ValueError):
            observations_for(self.store, uri)


if __name__ == "__main__":
    unittest.main()
