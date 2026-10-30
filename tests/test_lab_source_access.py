"""Offline, private-fixture tests of bounded laboratory worker source reads."""
import tempfile
import unittest
from pathlib import Path

from cobble.arena import init_arena, populate_corpus
from cobble.arena_source_access import read_source


class LabSourceAccessTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        source = self.home / "original"
        source.mkdir()
        (source / "github").mkdir()
        (source / "github" / "discussion.txt").write_text(
            "The first record. " + "Snug's supposed private conversation. " * 500,
            encoding="utf-8")
        (source / "unicode.txt").write_text("é" * 6000, encoding="utf-8")
        (source / "pack.bin").write_bytes(b"\x00\x01git-object")
        self.arena = self.home / "arena"
        init_arena(source, self.arena, {
            "memory_bytes": 100000, "model_tokens": 0,
            "attention_steps": 2, "archive_reads": 20, "external_ops": 0})
        populate_corpus(self.arena)
        self.before = (self.arena / "state.json").read_bytes()

    def test_verified_pages_and_no_mutation(self):
        first = read_source(self.arena, "github/discussion.txt", max_bytes=1000)
        self.assertIn("first record", first["content"])
        self.assertEqual(first["offset"], 0)
        self.assertEqual(first["next_offset"], 1000)
        second = read_source(self.arena, "github/discussion.txt",
                             offset=first["next_offset"], max_bytes=1000)
        self.assertEqual(second["offset"], 1000)
        self.assertNotEqual(second["content"], "")
        self.assertRegex(first["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(self.before, (self.arena / "state.json").read_bytes())

    def test_unicode_boundaries_do_not_drop_bytes(self):
        first = read_source(self.arena, "unicode.txt", max_bytes=1001)
        self.assertEqual(first["next_offset"], 1000)
        self.assertEqual(len(first["content"]), 500)
        second = read_source(self.arena, "unicode.txt", offset=first["next_offset"],
                             max_bytes=1001)
        self.assertEqual(second["offset"], 1000)
        self.assertEqual(len(second["content"]), 500)

    def test_binary_rejected(self):
        with self.assertRaises(ValueError):
            read_source(self.arena, "pack.bin")

    def test_manifest_only_and_path_confined(self):
        for name in ("../original/github/discussion.txt", "/etc/passwd",
                     "github/../../unicode.txt", ".arena-manifest.json",
                     "missing.txt", "github\\discussion.txt"):
            with self.assertRaises(ValueError, msg=name):
                read_source(self.arena, name)
        for kwargs in ({"offset": -1}, {"max_bytes": 0},
                       {"max_bytes": 20000}, {"offset": 100000}):
            with self.assertRaises(ValueError):
                read_source(self.arena, "unicode.txt", **kwargs)

    def test_changed_source_refused(self):
        (self.arena / "corpus" / "unicode.txt").write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_source(self.arena, "unicode.txt")

    def test_symlink_and_symlinked_directory_refused(self):
        path = self.arena / "corpus" / "unicode.txt"
        path.unlink()
        path.symlink_to(self.home / "original" / "unicode.txt")
        with self.assertRaises((ValueError, OSError)):
            read_source(self.arena, "unicode.txt")
        folder = self.arena / "corpus" / "github"
        (folder / "discussion.txt").unlink()
        folder.rmdir()
        folder.symlink_to(self.home / "original" / "github", target_is_directory=True)
        with self.assertRaises((ValueError, OSError)):
            read_source(self.arena, "github/discussion.txt")


if __name__ == "__main__":
    unittest.main()
