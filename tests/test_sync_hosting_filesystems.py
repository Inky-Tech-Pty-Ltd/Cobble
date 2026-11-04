"""Offline real-rsync tests: no SSH, hosting accounts or user home directories."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_hosting_filesystems.py"
spec = importlib.util.spec_from_file_location("sync_hosting_filesystems", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


@unittest.skipUnless(shutil.which("rsync") and os.name == "posix", "requires rsync and Linux")
class HostingSyncTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.remote = self.root / "remote"
        self.remote.mkdir()
        self.store = self.root / "private"
        self.source = module.Source("fixture", str(self.remote) + "/", excludes=("/mail/",))
        self.archive = self.store / "hosting" / "fixture"

    def sync(self, name):
        return module.sync_source(self.source, self.store, run_id=name)

    def test_added_modified_deleted_and_repeated_files_preserve_history(self):
        (self.remote / "a.txt").write_text("first version")
        (self.remote / "removed.txt").write_text("please preserve")
        (self.remote / "mail").mkdir()
        (self.remote / "mail" / "secret.eml").write_text("not in capture")
        (self.remote / "pointer").symlink_to("a.txt")
        first = self.sync("one")
        self.assertEqual(first["counts"]["added"], 3)  # two files + link; excluded mail
        self.assertFalse((self.archive / "mail").exists())
        self.assertTrue((self.archive / "pointer").is_symlink())
        self.assertEqual((self.archive / "a.txt").read_text(), "first version")
        self.assertEqual(self.archive.stat().st_mode & 0o077, 0)

        (self.remote / "a.txt").write_text("second version with different size")
        (self.remote / "removed.txt").unlink()
        (self.remote / "added.txt").write_text("new")
        second = self.sync("two")
        self.assertIn("a.txt", second["changes"]["modified"])
        self.assertIn("removed.txt", second["changes"]["deleted"])
        self.assertIn("added.txt", second["changes"]["added"])
        self.assertEqual((self.archive / "a.txt").read_text(), "second version with different size")
        history = self.store / "hosting" / "history" / "fixture" / "two"
        self.assertEqual((history / "refresh" / "a.txt").read_text(), "first version")
        self.assertEqual((history / "finalise" / "removed.txt").read_text(), "please preserve")
        self.assertFalse((self.archive / "removed.txt").exists())

        third = self.sync("three")
        self.assertEqual(third["counts"], {"added": 0, "modified": 0, "deleted": 0})
        report = json.loads((self.store / "hosting" / "news" / "fixture" / "two.json").read_text())
        self.assertEqual(report["status"], "complete")
        self.assertEqual((self.store / "hosting" / "news" / "fixture").stat().st_mode & 0o077, 0)

    def test_dry_run_makes_no_local_files(self):
        (self.remote / "some.txt").write_text("abc")
        self.assertIsNone(module.sync_source(self.source, self.store, run_id="dry", dry_run=True))
        self.assertFalse(self.store.exists())

    def test_failed_content_pass_does_not_delete_old_files(self):
        (self.remote / "keep.txt").write_text("old")
        (self.remote / "gone.txt").write_text("stored")
        self.sync("one")
        (self.remote / "keep.txt").write_text("newer and bigger")
        (self.remote / "gone.txt").unlink()
        original = module.execute
        commands = []

        def fail_first_command(cmd):
            commands.append(cmd)
            raise module.SyncError("mock failure before transfer")

        module.execute = fail_first_command
        try:
            with self.assertRaises(module.SyncError):
                self.sync("failed")
        finally:
            module.execute = original
        self.assertEqual(len(commands), 1)
        self.assertEqual((self.archive / "keep.txt").read_text(), "old")
        self.assertEqual((self.archive / "gone.txt").read_text(), "stored")
        report = json.loads((self.store / "hosting" / "news" / "fixture" / "failed.json").read_text())
        self.assertEqual(report["status"], "failed")

    def test_source_config_exact_remote_paths_and_private_key(self):
        a = module.SOURCES["inkytech"]
        b = module.SOURCES["villagelink"]
        self.assertIn("/home12/inkytech/", a.origin)
        self.assertIn("/home1/villagel/", b.origin)
        self.assertIn("/mail/", a.excludes)
        self.assertIn("/public_ftp/.ftpquota", b.excludes)
        self.assertEqual(a.remote_rsync, "/home12/inkytech/.local/bin/rsync")


if __name__ == "__main__":
    unittest.main()
