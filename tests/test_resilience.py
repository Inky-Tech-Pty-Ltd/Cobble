import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from cobble.traces import mint_trace, resolve_local, trace_id
from cobble.stars import mint_star, add_ray
from villagelink.codec import make


class TraceResilienceTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.store = Path(t.name)
        self.members = []
        for _ in range(2):
            r = mint_trace(self.store, "https://example.org/notes",
                           "Memory is the masterpiece.", "Memory is the masterpiece.\n")
            self.members.append(r["uri"])

    def test_mint_copy_and_resolve_offline(self):
        r = mint_trace(self.store, "https://chatgpt.com/c/example",
                       "Memory is the masterpiece.",
                       "Before\nMemory is the masterpiece.\nAfter")
        self.assertEqual(resolve_local(self.store, r["uri"]),
                         "Before\nMemory is the masterpiece.\nAfter")
        self.assertEqual(r["source_uri"], "https://chatgpt.com/c/example")
        self.assertTrue(r["local_copy_uri"].startswith("file:"))

    def test_mint_without_copy_is_allowed_but_not_locally_resolvable(self):
        r = mint_trace(self.store, "https://example.org", "A phrase")
        with self.assertRaises(FileNotFoundError):
            resolve_local(self.store, r["uri"])

    def test_copy_missing_selector_rejected_without_writes(self):
        with self.assertRaises(ValueError):
            mint_trace(self.store, "https://example.org", "absent", "different")
        self.assertEqual(len(list((self.store / "traces").glob("*.json"))), 2)

    def test_resolve_rejects_copy_outside_store(self):
        r = mint_trace(self.store, "https://example.org", "secret", "secret")
        path = self.store / "traces" / f"{trace_id(r['uri'])}.json"
        altered = json.loads(path.read_text())
        altered["local_copy_uri"] = (self.store.parent / "private.txt").as_uri()
        path.write_text(json.dumps(altered))
        with self.assertRaisesRegex(ValueError, "outside"):
            resolve_local(self.store, r["uri"])

    def test_extend_star_and_repeat_without_duplication(self):
        star = mint_star(self.store, "Memory is the masterpiece.", self.members)
        centre = star["A"]
        additional = mint_trace(self.store, "https://chatgpt.com/c/example",
                                "Memory is the masterpiece.",
                                "Memory is the masterpiece.")["uri"]
        updated = add_ray(self.store, centre, additional)
        self.assertEqual(updated["A"], centre)
        self.assertEqual(len(updated["B"]), 3)
        self.assertEqual(add_ray(self.store, centre, additional), updated)
        stored = json.loads((self.store / "stars" / f"{trace_id(centre)}.json").read_text())
        self.assertEqual(stored, updated)
        import hashlib
        ray = make(centre, additional)
        filename = hashlib.sha256(ray.encode()).hexdigest() + ".json"
        self.assertEqual(json.loads((self.store / "links" / filename).read_text())["uri"], ray)

    def test_add_missing_member_leaves_star_unchanged(self):
        star = mint_star(self.store, "H", self.members)
        with self.assertRaises(FileNotFoundError):
            add_ray(self.store, star["A"], f"https://cobble.link/t/{uuid4()}")
        actual = json.loads((self.store / "stars" / f"{trace_id(star['A'])}.json").read_text())
        self.assertEqual(actual, star)

    def test_add_ray_rejects_centre_as_member(self):
        star = mint_star(self.store, "H", self.members)
        with self.assertRaises(ValueError):
            add_ray(self.store, star["A"], star["A"])
