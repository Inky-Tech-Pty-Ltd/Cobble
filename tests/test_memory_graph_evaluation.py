"""Evaluation controls, reproducibility, ablation and expected limitations."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_memory_graph import evaluate, load_corpus, outcomes, ranking, observation_report


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.corpus = load_corpus()

    def test_corpus_has_24_traces_six_queries(self):
        self.assertEqual(len(self.corpus["traces"]), 24)
        self.assertEqual(len(self.corpus["queries"]), 6)

    def test_deterministic_repeated_results(self):
        self.assertEqual(evaluate(self.corpus), evaluate(self.corpus))

    def test_equal_candidate_pool_and_budget(self):
        for q in self.corpus["queries"]:
            a0 = ranking(self.corpus, q, "A0")
            a1 = ranking(self.corpus, q, "A1")
            self.assertEqual(set(a0), set(a1))
            self.assertEqual(len(a0), 23)
            for arch in ("A0", "A1", "A2"):
                self.assertEqual(len(outcomes(self.corpus, arch)[0]["retrieved"]), 4)

    def test_ablation_has_expected_equivalence(self):
        self.assertTrue(evaluate(self.corpus)["ablation"]["remove_links_equals_A0"])
        self.assertTrue(evaluate(self.corpus)["ablation"]["remove_observations_equals_A1_reporting"])

    def test_observation_layer_exposes_loss_without_rewriting_history(self):
        a2 = observation_report(self.corpus, "A2")
        self.assertEqual(a2["T01"]["last_seen_status"], "unavailable")
        self.assertTrue(a2["T01"]["historical_available"])
        self.assertEqual(observation_report(self.corpus, "A1")["T01"]["last_seen_status"], "unknown")

    def test_graph_edges_not_equal_to_source_truth(self):
        self.assertTrue(all("verified" not in str(x) for x in self.corpus["stars"]))

    def test_retrieval_scores_a1_a2_equal_without_availability_filtering(self):
        self.assertEqual(outcomes(self.corpus, "A1"), outcomes(self.corpus, "A2"))

    def test_unknown_architecture_rejected(self):
        with self.assertRaises(ValueError):
            outcomes(self.corpus, "A3")


if __name__ == "__main__":
    unittest.main()
