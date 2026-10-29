"""Reproducible offline tests of Arena source sensing, without source disclosure."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cobble.arena import init_arena, populate_corpus
from cobble.arena_catalogue import CATEGORIES, catalogue, list_sources


class ArenaCatalogueTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source"
        self.arena = self.root / "arena"
        data = {
            "github/conversations/Inky/Repo/discussions/8/latest.json": b'{"version":"mock"}',
            "github/conversations/Inky/Repo/discussions/8/versions/a.json": b"fictional archived body",
            "github/repositories/Inky/Repo/objects/test": b"\x00\x01\x02",
            "github/manifests/Inky/Repo.json": b"{}",
            "chatgpt/conversations/example.json": b'{"role":"user","message":"hidden"}',
            "traces/one.json": b"trace",
            "notes/extra.txt": b"secret source body is not a tool result",
        }
        for name, contents in data.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        self.data = data
        budget = {
            "memory_bytes": 100000, "model_tokens": 0,
            "attention_steps": 5, "archive_reads": 100,
            "external_ops": 0,
        }
        init_arena(self.source, self.arena, budget)
        populate_corpus(self.arena)

    def test_category_totals_and_no_text(self):
        census = catalogue(self.arena)
        self.assertEqual(census["total_files"], len(self.data))
        self.assertEqual(census["total_bytes"], sum(map(len, self.data.values())))
        self.assertEqual(census["categories"]["github-conversations"]["files"], 2)
        self.assertEqual(census["categories"]["github-repositories"]["files"], 1)
        self.assertEqual(census["categories"]["chatgpt"]["files"], 1)
        self.assertEqual(set(census["categories"]), set(CATEGORIES))
        self.assertNotIn("secret source body", json.dumps(census))
        self.assertNotIn("Inky/Repo", json.dumps(census))

    def test_pages_are_stable_nonoverlapping_and_source_attributed(self):
        first = list_sources(self.arena, limit=3)
        second = list_sources(self.arena, limit=3, offset=first["next_offset"])
        third = list_sources(self.arena, limit=3, offset=second["next_offset"])
        paths = [x["path"] for page in (first, second, third) for x in page["entries"]]
        self.assertEqual(paths, sorted(self.data))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertIsNone(third["next_offset"])
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        for item in first["entries"]:
            self.assertEqual(item["sha256"], hashlib.sha256(
                self.data[item["path"]]).hexdigest())

    def test_filter_by_category_and_path_substring(self):
        page = list_sources(self.arena, category="github-conversations", query="discussions")
        self.assertEqual(page["total_matches"], 2)
        self.assertTrue(all(x["category"] == "github-conversations" for x in page["entries"]))
        page = list_sources(self.arena, query="SOMETHING-ABSENT")
        self.assertEqual(page["entries"], [])
        self.assertIsNone(page["next_offset"])

    def test_source_contents_are_not_returned(self):
        result = list_sources(self.arena, query="extra")
        self.assertEqual(result["total_matches"], 1)
        self.assertNotIn("secret source body", json.dumps(result))
        self.assertNotIn("hidden", json.dumps(result))

    def test_does_not_consume_juvenile_budget(self):
        before = (self.arena / "state.json").read_bytes()
        catalogue(self.arena)
        list_sources(self.arena, category="all")
        self.assertEqual(before, (self.arena / "state.json").read_bytes())

    def test_bad_inputs_and_corrupt_manifest_fail_closed(self):
        invalid = (
            {"category": "arbitrary"},
            {"limit": 10000},
            {"offset": -1},
            {"query": "a" * 81},
        )
        for kwargs in invalid:
            with self.assertRaises(ValueError):
                list_sources(self.arena, **kwargs)
        manifest = self.arena / "corpus" / ".arena-manifest.json"
        record = json.loads(manifest.read_text())
        record["files"][0]["path"] = "../escape"
        manifest.write_text(json.dumps(record))
        with self.assertRaises(ValueError):
            catalogue(self.arena)

    def test_manifest_symlink_rejected(self):
        manifest = self.arena / "corpus" / ".arena-manifest.json"
        destination = self.root / "other.json"
        destination.write_bytes(manifest.read_bytes())
        manifest.unlink()
        manifest.symlink_to(destination)
        with self.assertRaises(ValueError):
            catalogue(self.arena)

    def test_unpopulated_arena_refused(self):
        empty = self.root / "new-arena"
        init_arena(self.source, empty, {
            "memory_bytes": 1000, "model_tokens": 0,
            "attention_steps": 1, "archive_reads": 1, "external_ops": 0})
        with self.assertRaises(ValueError):
            catalogue(empty)


if __name__ == "__main__":
    unittest.main()
