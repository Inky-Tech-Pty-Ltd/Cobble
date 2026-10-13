import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from cobble.graph import inspect_hypothesis, simple_baseline
from cobble.observations import record_observation, observations_for
from cobble.stars import mint_star, trace_id
from villagelink.codec import make


class MemoryGraphTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Path(temp.name)
        (self.store / "traces").mkdir()
        self.members = [f"https://cobble.link/t/{uuid4()}" for _ in range(3)]
        for uri in self.members:
            (self.store / "traces" / f"{trace_id(uri)}.json").write_text(
                json.dumps({"uri": uri, "source_uri": "file:///synthetic/source.json"}),
                encoding="utf-8")
        self.star = mint_star(self.store, "Shared concept", self.members)

    def test_inspection_preserves_claim_boundary(self):
        result = inspect_hypothesis(self.store, self.star["A"])
        self.assertEqual(result["claim_status"], "asserted-not-verified")
        self.assertEqual(len(result["members"]), 3)
        self.assertTrue(all(m["latest_retrieval"] == "unknown" for m in result["members"]))

    def test_history_is_append_only_and_source_loss_visible(self):
        uri = self.members[0]
        record_observation(self.store, uri, "available", observed_at="2026-10-13T01:00:00Z")
        record_observation(self.store, uri, "unavailable", observed_at="2026-10-14T01:00:00Z")
        self.assertEqual([x["retrieval"]["status"] for x in observations_for(self.store, uri)],
                         ["available", "unavailable"])
        result = inspect_hypothesis(self.store, self.star["A"])
        self.assertEqual(next(m for m in result["members"] if m["trace_uri"] == uri)
                         ["latest_retrieval"], "unavailable")

    def test_no_fabricated_retrieval(self):
        with self.assertRaises(ValueError):
            record_observation(self.store, "https://cobble.link/t/" + str(uuid4()), "available")
        with self.assertRaises(ValueError):
            record_observation(self.store, self.members[0], "verified")
        with self.assertRaises(ValueError):
            record_observation(self.store, self.members[0], "available",
                               observed_at="2026-10-13T01:00:00")

    def test_corrupt_or_missing_ray_fails_closed(self):
        ray = make(self.star["A"], self.members[0])
        filename = hashlib.sha256(ray.encode()).hexdigest() + ".json"
        (self.store / "links" / filename).unlink()
        with self.assertRaises(FileNotFoundError):
            inspect_hypothesis(self.store, self.star["A"])

    def test_g0_g1_differ_only_by_edges(self):
        baseline = simple_baseline(self.store, self.star["A"])
        graph = inspect_hypothesis(self.store, self.star["A"])
        self.assertEqual(baseline["candidate_count"], len(graph["members"]))
        self.assertFalse(baseline["relationships_available"])
        self.assertEqual(set(baseline["candidates"]),
                         {m["trace_uri"] for m in graph["members"]})

    def test_process_restart_from_files(self):
        first = inspect_hypothesis(self.store, self.star["A"])
        second = inspect_hypothesis(Path(str(self.store)), self.star["A"])
        self.assertEqual(first, second)

    def test_unknown_status_does_not_overwrite_prior(self):
        record_observation(self.store, self.members[0], "available")
        with self.assertRaises(ValueError):
            record_observation(self.store, self.members[0], "trustworthy")
        self.assertEqual(len(observations_for(self.store, self.members[0])), 1)


if __name__ == "__main__":
    unittest.main()
