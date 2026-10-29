"""Offline reproducibility checks for independent users of Cobble."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cobble.arena import BudgetExceeded
from scripts.reproduce_arena_one import FIXTURE, ROOT, reproduce


class ArenaReproductionTests(unittest.TestCase):
    def test_public_fixture_is_complete_and_repeatable(self):
        first = reproduce()
        second = reproduce()
        self.assertEqual(first, second)
        self.assertEqual(first["result"], "passed")
        self.assertTrue(first["byte_identical"])
        self.assertTrue(first["source_unchanged"])
        self.assertEqual(first["file_count"], 3)
        self.assertEqual(first["resource_spent"]["archive_reads"], 3)
        self.assertEqual(first["resource_spent"]["model_tokens"], 0)
        self.assertEqual(first["resource_spent"]["external_ops"], 0)
        self.assertEqual(first["source_inventory_sha256"],
                         first["arena_inventory_sha256"])
        self.assertTrue((FIXTURE / "chatgpt" / "conversations" / "sample.json").is_file())
        self.assertTrue((FIXTURE / "github" / "discussions" / "sample.json").is_file())

    def test_user_corpus_is_not_edited_or_returned(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "my-private-corpus"
            source.mkdir()
            content = b"Do not disclose this text in a result"
            (source / "private.txt").write_bytes(content)
            report = reproduce(source)
            self.assertEqual((source / "private.txt").read_bytes(), content)
            self.assertEqual(report["source"], "user-selected-local-corpus")
            self.assertEqual(report["file_count"], 1)
            self.assertNotIn("Do not disclose", json.dumps(report))
            self.assertEqual(report["source_bytes"], len(content))

    def test_memory_and_retrieval_caps_are_enforced(self):
        with self.assertRaises(BudgetExceeded):
            reproduce(memory_bytes=1)
        with self.assertRaises(BudgetExceeded):
            reproduce(archive_reads=1)

    def test_source_symlink_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "archive"
            source.mkdir()
            outside = Path(temp) / "secret"
            outside.write_text("secret")
            (source / "link").symlink_to(outside)
            with self.assertRaises(ValueError):
                reproduce(source)

    def test_cli_output_is_stable_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            report_path = Path(temp) / "report.json"
            cmd = [sys.executable, "scripts/reproduce_arena_one.py",
                   "--report", str(report_path)]
            env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
            first = subprocess.run(cmd, cwd=ROOT, env=env,
                                   capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(first.stdout),
                             json.loads(report_path.read_text()))
            second = subprocess.run(cmd, cwd=ROOT, env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(json.loads(report_path.read_text()),
                             json.loads(first.stdout))

    def test_report_cannot_be_written_inside_source(self):
        cmd = [sys.executable, "scripts/reproduce_arena_one.py",
               "--report", str(FIXTURE / "bad-report.json")]
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        check = subprocess.run(cmd, cwd=ROOT, env=env,
                               capture_output=True, text=True)
        self.assertNotEqual(check.returncode, 0)
        self.assertFalse((FIXTURE / "bad-report.json").exists())


if __name__ == "__main__":
    unittest.main()
