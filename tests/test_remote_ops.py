"""Tests for fixed MCP Arena diagnostics and their privilege boundary."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cobble.arena import init_arena, populate_corpus
from cobble.remote_ops import (arena_status, verify_arena, run_arena_tests,
                               arena_catalogue, arena_list_sources)


class ArenaRemoteTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.archive = self.home / "archive"
        self.archive.mkdir()
        (self.archive / "hello.txt").write_text("real archived memory", encoding="utf-8")
        self.arena = self.home / "cobble-arenas" / "arena-a"
        self.home_patch = patch("cobble.remote_ops.Path.home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)
        limits = {"memory_bytes": 10000, "model_tokens": 0,
                  "attention_steps": 2, "archive_reads": 2,
                  "external_ops": 0}
        init_arena(self.archive, self.arena, limits)
        populate_corpus(self.arena)

    def test_status_is_metadata_only(self):
        report = arena_status()
        self.assertEqual(report["report"]["population"]["files"], 1)
        self.assertNotIn("real archived memory", str(report))
        self.assertIn("remaining", report["report"]["budget"]["memory_bytes"])

    def test_verify_whole_copy_and_detect_changes(self):
        result = verify_arena()
        self.assertTrue(result["verified"])
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["source_bytes"], len("real archived memory"))
        (self.arena / "corpus" / "hello.txt").write_text("another fake archived memory", encoding="utf-8")
        with self.assertRaises(ValueError):
            verify_arena()

    def test_rejects_path_escape(self):
        for name in ("../archive", "/etc", "foo/bar", ".", "..", "a b"):
            with self.assertRaises(ValueError, msg=name):
                arena_status(name)
                verify_arena(name)

    def test_source_senses_are_read_only_and_path_confined(self):
        before = (self.arena / "state.json").read_bytes()
        census = arena_catalogue()
        self.assertEqual(census["catalogue"]["total_files"], 1)
        listing = arena_list_sources(limit=1)
        self.assertEqual(listing["page"]["total_matches"], 1)
        self.assertEqual(listing["page"]["entries"][0]["path"], "hello.txt")
        self.assertNotIn("real archived memory", str(listing))
        self.assertEqual(before, (self.arena / "state.json").read_bytes())
        with self.assertRaises(ValueError):
            arena_list_sources("../secrets")

    def test_tests_are_disabled_by_default(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_ARENA_TESTS": "0"}):
            with self.assertRaises(PermissionError):
                run_arena_tests()

    def test_opt_in_only_runs_reviewed_command_with_secret_free_env(self):
        import subprocess
        result = subprocess.CompletedProcess(["fixed"], 0, stdout="ok", stderr="Ran 7 tests")
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_ARENA_TESTS": "1",
                                     "GH_TOKEN": "fake-secret"}):
            with patch("cobble.remote_ops.subprocess.run", return_value=result) as run:
                report = run_arena_tests()
        self.assertTrue(report["passed"])
        args, kwargs = run.call_args
        self.assertEqual(args[0][1:4], ["-m", "unittest", "discover"])
        self.assertEqual(kwargs["env"]["PYTHONUNBUFFERED"], "1")
        self.assertNotIn("GH_TOKEN", kwargs["env"])
        self.assertEqual(kwargs["timeout"], 45)
        self.assertNotIn("shell", kwargs)
        self.assertEqual(args[0][-1], "-v")


if __name__ == "__main__":
    unittest.main()
