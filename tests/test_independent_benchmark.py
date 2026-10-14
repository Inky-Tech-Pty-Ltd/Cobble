import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evaluate_independent_benchmark import evaluate, load, rank, star_neighbors

class IndependentBenchmarkTests(unittest.TestCase):
    def setUp(self): self.corpus,self.annotations=load()
    def test_annotations_are_not_graph_membership(self):
        for q in self.corpus["queries"]:
            self.assertNotEqual(set(self.annotations["relevance"][q["id"]]),
                                star_neighbors(self.corpus,q["anchor"]))
    def test_adversarial_false_links_present(self):
        self.assertIn("B04",star_neighbors(self.corpus,"B01"))
        self.assertNotIn("B04",self.annotations["relevance"]["IQ1"])
        self.assertIn("B10",star_neighbors(self.corpus,"B07"))
        self.assertNotIn("B10",self.annotations["relevance"]["IQ2"])
    def test_relevant_missing_links_present(self):
        self.assertIn("B11",self.annotations["relevance"]["IQ2"])
        self.assertNotIn("B11",star_neighbors(self.corpus,"B07"))
        self.assertIn("B06",self.annotations["relevance"]["IQ4"])
        self.assertNotIn("B06",star_neighbors(self.corpus,"B16"))
    def test_candidate_pool_is_equal(self):
        for q in self.corpus["queries"]:
            self.assertEqual({x[1] for x in rank(self.corpus,q,"A0")},
                             {x[1] for x in rank(self.corpus,q,"A1")})
    def test_mixed_result_not_uniform_graph_win(self):
        rows={x["query"]:x for x in evaluate()["queries"]}
        self.assertEqual(rows["IQ1"]["architectures"]["A0"]["recall_at_4"],
                         rows["IQ1"]["architectures"]["A1"]["recall_at_4"])
        self.assertGreater(rows["IQ3"]["architectures"]["A1"]["recall_at_4"],
                           rows["IQ3"]["architectures"]["A0"]["recall_at_4"])
    def test_false_links_are_observable_harm_signal(self):
        self.assertGreater(evaluate()["summary"]["A1"]["linked_irrelevant_retrieved"],0)
    def test_deterministic(self): self.assertEqual(evaluate(),evaluate())

if __name__=="__main__": unittest.main()
