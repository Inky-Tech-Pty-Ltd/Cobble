"""Offline tests for explicit lab-worker authority and the local journal."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from cobble.lab_ops import (
    add_lab_note, recent_lab_notes, run_lab_suite, SUITES,
)
from cobble.remote_ops import arena_read_source


class LabOpsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        homepatch = patch("cobble.lab_ops.Path.home", return_value=self.home)
        homepatch.start()
        self.addCleanup(homepatch.stop)

    def test_fixed_suite_requires_opt_in_and_disallows_commands(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_LAB_TESTS": "0"}):
            with self.assertRaises(PermissionError):
                run_lab_suite("arena")
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_LAB_TESTS": "1",
                                     "GH_TOKEN": "should-not-leak",
                                     "CONTROL_PLANE_API_KEY": "also-private"}):
            with self.assertRaises(ValueError):
                run_lab_suite("../../tmp")
            for suite in SUITES:
                fake = subprocess.CompletedProcess([], 0, "ok", "Ran 4 tests")
                with patch("cobble.lab_ops.subprocess.run", return_value=fake) as run:
                    result = run_lab_suite(suite)
                self.assertTrue(result["passed"])
                args, kwargs = run.call_args
                self.assertEqual(args[0][:4][1:], ["-m", "unittest", "discover"])
                self.assertNotIn("shell", kwargs)
                self.assertEqual(kwargs["timeout"], 75)
                self.assertNotIn("GH_TOKEN", kwargs["env"])
                self.assertNotIn("CONTROL_PLANE_API_KEY", kwargs["env"])
                self.assertEqual(args[0][-2:], [SUITES[suite], "-v"])

    def test_journal_is_behind_local_switch(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_LAB_NOTES": "0"}):
            with self.assertRaises(PermissionError):
                add_lab_note("observation", "lab is healthy")
        self.assertEqual(recent_lab_notes()["entries"], [])

    def test_append_journal_records_and_bounds(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_LAB_NOTES": "1"}):
            for kind in ("observation", "hypothesis"):
                result = add_lab_note(kind, "Snug's budget is shared")
                self.assertTrue(result["recorded"])
            notes = recent_lab_notes(limit=1)["entries"]
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["kind"], "hypothesis")
            self.assertIn("Puck", notes[0]["authorship"])
            path = self.home / "cobble-lab" / "journal.jsonl"
            self.assertEqual(len(path.read_text().splitlines()), 2)
            self.assertEqual(len([json.loads(line) for line in path.read_text().splitlines()]), 2)
            for kwargs in ({"kind": "hack", "text": "abc"},
                           {"kind": "result", "text": ""},
                           {"kind": "result", "text": "X" * 4001},
                           {"kind": "result", "text": "ok", "arena": "../source"}):
                with self.assertRaises(ValueError):
                    add_lab_note(**kwargs)
        with self.assertRaises(ValueError):
            recent_lab_notes(limit=21)

    def test_symlinked_journal_refused(self):
        base = self.home / "cobble-lab"
        base.mkdir()
        victim = self.home / "victim.txt"
        victim.write_text("do not write", encoding="utf-8")
        (base / "journal.jsonl").symlink_to(victim)
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_LAB_NOTES": "1"}):
            with self.assertRaises((OSError, ValueError)):
                add_lab_note("result", "some note")
        with self.assertRaises((OSError, ValueError)):
            recent_lab_notes()
        self.assertEqual(victim.read_text(), "do not write")

    def test_source_tool_requires_explicit_worker_switch(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_SOURCE_READS": "0"}):
            with patch("cobble.remote_ops.read_arena_text") as reader:
                with self.assertRaises(PermissionError):
                    arena_read_source(path="test.txt")
                reader.assert_not_called()
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_SOURCE_READS": "1"}):
            with patch("cobble.remote_ops.read_arena_text", return_value={"content": "test"}) as reader:
                result = arena_read_source(name="arena-a", path="test.txt")
                self.assertEqual(result["page"]["content"], "test")
                reader.assert_called_once()


if __name__ == "__main__":
    unittest.main()
