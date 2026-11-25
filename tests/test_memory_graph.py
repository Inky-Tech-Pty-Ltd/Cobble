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

    def test_villagelink_consumer_projection_preserves_assertion_boundary(self):
        from villagelink.utility import Graph, Publication
        from villagelink.codec import parse
        centre = self.star["A"]
        records = []
        for member in self.star["B"]:
            ray = make(centre, member)
            path = self.store / "links" / (hashlib.sha256(ray.encode()).hexdigest() + ".json")
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["scope"], "local")
            self.assertEqual(parse(saved["uri"]), (centre, member))
            records.append(Publication(saved["uri"], path.as_uri()))
        # A synthetic reversed occurrence is not a new underlying relation.
        records.append(Publication(make(self.members[0], centre), "urn:fixture:reverse"))
        # Deliberately false bridge, outside the stored hypothesis membership.
        outsider = "urn:fixture:unrelated"
        records.append(Publication(make(self.members[0], outsider), "urn:fixture:false-bridge"))
        graph = Graph(records)
        self.assertTrue(graph.connected(centre, outsider, 2))
        self.assertFalse(graph.connected(centre, outsider, 1))
        edge = next(s for s in graph.adjacent(centre) if s.target == self.members[0])
        self.assertEqual(len(edge.publications), 2)
        record_observation(self.store, self.members[0], "unavailable")
        result = inspect_hypothesis(self.store, centre)
        self.assertEqual(result["claim_status"], "asserted-not-verified")
        self.assertEqual({m["trace_uri"] for m in result["members"]}, set(self.members))
        self.assertNotIn(outsider, {m["trace_uri"] for m in result["members"]})
        member = next(m for m in result["members"] if m["trace_uri"] == self.members[0])
        self.assertEqual(member["latest_retrieval"], "unavailable")
        self.assertFalse(member["observations"][0]["semantics"]["truth_assessed"])

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
