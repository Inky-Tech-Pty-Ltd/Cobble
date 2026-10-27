import json, unittest
from pathlib import Path

MANIFEST=Path(__file__).resolve().parents[1]/"docs"/"research"/"star-boundary-manifest.json"

class StarBoundaryManifestTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_review_has_no_normative_effect(self):
        self.assertEqual(self.data["normative_effect"],"none")
        self.assertFalse(self.data["gates"]["villageLink_normative_change"])

    def test_allowed_owners_are_explicit(self):
        allowed={"VillageLink","Cobble","unresolved","neither"}
        for prop in self.data["properties"]:
            self.assertIn(prop["owner"],allowed)
            self.assertTrue(prop["evidence"])

    def test_villagelink_normative_semantics_not_owned_by_cobble(self):
        normative=[p for p in self.data["properties"] if p["status"]=="normative"]
        self.assertTrue(normative)
        self.assertTrue(all(p["owner"]=="VillageLink" for p in normative))

    def test_cobble_owns_application_specific_state(self):
        by_id={p["id"]:p for p in self.data["properties"]}
        for key in ("hypothesis_lifecycle","source_observation_history","retrieval_ranking","local_persistence"):
            self.assertEqual(by_id[key]["owner"],"Cobble")

    def test_truth_and_reputation_not_claimed(self):
        by_id={p["id"]:p for p in self.data["properties"]}
        self.assertEqual(by_id["truth_or_authoritative_identity"]["owner"],"neither")
        self.assertEqual(by_id["universal_confidence_reputation"]["owner"],"neither")

    def test_relationship_edges_state_non_implications(self):
        self.assertTrue(self.data["relationships"])
        for edge in self.data["relationships"]:
            self.assertTrue(edge["does_not_imply"])

    def test_current_gates_match_evidence(self):
        gates=self.data["gates"]
        self.assertFalse(gates["cobble_star_syntax_required"])
        self.assertTrue(gates["stable_group_identity_required"])
        self.assertFalse(gates["real_personal_memory_ready"])

if __name__=="__main__":
    unittest.main()
