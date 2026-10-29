"""Arena One tests: preserve every source byte, isolate the archive, budget the copy."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cobble.arena import BudgetExceeded, init_arena, overview, populate_corpus


class ArenaOneTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.archive = self.root / "preserved"
        self.arena = self.root / "derived" / "arena-a"
        self.archive.mkdir()
        self.samples = {
            "github/conversations/Org/Cobble/discussions/8/latest.json": (
                '{"sha256":"mock","version":"versions/mock.json"}\n'.encode()),
            "github/conversations/Org/Cobble/discussions/8/versions/mock.json": (
                b'{"discussion": {"body": "First"},"comments": [{"body": "Second"}]}'),
            "github/git/Cobble/objects/pack/pack-file.pack": b"\x00\xff" * 70,
            "text/full-history.txt": ("A complete 15,000-character history.\n" * 450).encode(),
            "text/other-history.txt": b"Another memory.",
        }
        for name, content in self.samples.items():
            path = self.archive / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        self.total = sum(len(v) for v in self.samples.values())
        self.limits = {"memory_bytes": self.total + 10000, "model_tokens": 0,
                       "attention_steps": 4, "archive_reads": 100,
                       "external_ops": 0}

    def start(self, **changes):
        return init_arena(self.archive, self.arena, dict(self.limits, **changes))

    def test_init_is_empty_and_never_overwrites(self):
        result = self.start()
        self.assertIsNone(result["population"])
        self.assertEqual(result["budget"]["memory_bytes"]["spent"], 0)
        self.assertEqual(result["budget"]["model_tokens"]["limit"], 0)
        with self.assertRaises(FileExistsError):
            self.start()

    def test_entire_corpus_is_byte_identical_and_no_source_changes(self):
        before = {p.relative_to(self.archive): p.read_bytes()
                  for p in self.archive.rglob("*") if p.is_file()}
        self.start()
        result = populate_corpus(self.arena)
        self.assertEqual(result["population"]["files"], len(self.samples))
        self.assertEqual(result["population"]["source_bytes"], self.total)
        self.assertEqual(result["budget"]["memory_bytes"]["spent"], self.total)
        self.assertEqual(result["budget"]["archive_reads"]["spent"], len(self.samples))
        self.assertEqual(result["budget"]["attention_steps"]["spent"], 1)
        copied = self.arena / "corpus"
        for relative, expected in self.samples.items():
            self.assertEqual((copied / relative).read_bytes(), expected)
        self.assertEqual({p.relative_to(self.archive): p.read_bytes()
                          for p in self.archive.rglob("*") if p.is_file()}, before)
        manifest = json.loads((copied / ".arena-manifest.json").read_text())
        self.assertEqual(len(manifest["files"]), len(self.samples))
        self.assertEqual(set(e["path"] for e in manifest["files"]), set(self.samples))
        for entry in manifest["files"]:
            self.assertEqual(entry["sha256"], hashlib.sha256(
                self.samples[entry["path"]]).hexdigest())
        with self.assertRaises(FileExistsError):
            populate_corpus(self.arena)
        self.assertNotIn("First", json.dumps(overview(self.arena)))

    def test_tiny_budget_cannot_silently_truncate(self):
        self.start(memory_bytes=self.total - 1)
        with self.assertRaises(BudgetExceeded):
            populate_corpus(self.arena)
        result = overview(self.arena)
        self.assertIsNone(result["population"])
        self.assertEqual(result["budget"]["memory_bytes"]["spent"], 0)
        self.assertFalse((self.arena / "corpus").exists())

    def test_read_budget_covers_every_file(self):
        self.start(archive_reads=len(self.samples) - 1)
        with self.assertRaises(BudgetExceeded):
            populate_corpus(self.arena)
        self.assertIsNone(overview(self.arena)["population"])

    def test_rejects_symlink_source_without_copying(self):
        outside = self.root / "secret.txt"
        outside.write_text("private material outside source archive")
        (self.archive / "escape.txt").symlink_to(outside)
        self.start()
        with self.assertRaises(ValueError):
            populate_corpus(self.arena)
        self.assertFalse((self.arena / "corpus").exists())

    def test_rejects_overlapping_directories(self):
        with self.assertRaises(ValueError):
            init_arena(self.archive, self.archive / "arena", self.limits)
        with self.assertRaises(ValueError):
            init_arena(self.archive, self.root, self.limits)

    def test_rejects_negative_limits(self):
        with self.assertRaises(ValueError):
            self.start(external_ops=-1)


if __name__ == "__main__":
    unittest.main()
