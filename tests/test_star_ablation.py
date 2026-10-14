import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evaluate_star_ablation import evaluate, membership_views
from evaluate_independent_benchmark import load

class StarAblationTests(unittest.TestCase):
    def setUp(self): self.corpus,_=load()
    def test_collection_and_reconstructed_pairwise_match_star_retrieval(self):
        result=evaluate()
        self.assertTrue(result["equivalence"]["collection_matches_star"])
        self.assertTrue(result["equivalence"]["pairwise_reconstructed_matches_star"])
    def test_bare_pairwise_records_need_shared_centre_to_reconstruct_group(self):
        views=membership_views(self.corpus)
        self.assertTrue(views["pairwise"])
        self.assertTrue(all(isinstance(key,tuple) and len(key)==2 for key in views["pairwise"]))
    def test_false_membership_survives_representation_change(self):
        views=membership_views(self.corpus)
        self.assertIn("B04",views["star"]["B01"])
        self.assertIn("B04",views["collection"]["B01"])
        self.assertIn("B04",views["pairwise_reconstructed"]["B01"])

if __name__=="__main__": unittest.main()
