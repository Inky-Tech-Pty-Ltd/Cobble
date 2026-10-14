import json
import tempfile
import unittest
from pathlib import Path

from cobble.memory_access import get_trace, inspect_star, search_memory
from cobble.stars import mint_star
from cobble.traces import mint_trace


class MemoryAccessTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.store = Path(t.name)
        self.first = mint_trace(self.store, "https://example.org/one",
                                "Memory is the masterpiece.",
                                "Infrastructure of memory.\nMemory is the masterpiece.")
        self.second = mint_trace(self.store, "https://example.org/two",
                                 "Intelligence is paint.", "Intelligence is paint.")
        self.star = mint_star(self.store, "Memory is the masterpiece.",
                              [self.first["uri"], self.second["uri"]])

    def test_get_trace_offline(self):
        result = get_trace(self.store, self.first["uri"])
        self.assertEqual(result["trace"]["source_uri"], "https://example.org/one")
        self.assertIn("Infrastructure", result["content"])
        self.assertFalse(result["truncated"])

    def test_inspect_star_verifies_rays(self):
        result = inspect_star(self.store, self.star["A"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(set(r["member"] for r in result["members"]),
                         {self.first["uri"], self.second["uri"]})

    def test_corrupt_ray_is_rejected(self):
        from hashlib import sha256
        from villagelink.codec import make
        ray = make(self.star["A"], self.first["uri"])
        file = self.store / "links" / (sha256(ray.encode()).hexdigest() + ".json")
        file.write_text(json.dumps({"uri": "vl:not-a-ray"}))
        with self.assertRaisesRegex(ValueError, "Invalid"):
            inspect_star(self.store, self.star["A"])

    def test_search_retained_text_and_selector(self):
        result = search_memory(self.store, "Infrastructure")
        self.assertEqual([r["uri"] for r in result["results"]], [self.first["uri"]])
        result = search_memory(self.store, "Intelligence", 1)
        self.assertEqual(len(result["results"]), 1)

    def test_search_bounded_and_invalid_input(self):
        with self.assertRaises(ValueError):
            search_memory(self.store, "x" * 201)
        with self.assertRaises(ValueError):
            search_memory(self.store, "memory", 21)
        self.assertLessEqual(len(search_memory(self.store, "memory", 1)["results"]), 1)

    def test_no_copy_returns_metadata(self):
        r = mint_trace(self.store, "https://example.org/three", "Absent")
        result = get_trace(self.store, r["uri"])
        self.assertIsNone(result["content"])
