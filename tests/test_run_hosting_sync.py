"""Offline tests for the hosting synchroniser's scheduled entry point."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "run_hosting_sync.sh"


@unittest.skipUnless(os.name == "posix", "requires POSIX shell")
class ScheduledHostingSyncTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        scripts = self.home / "Cobble" / "scripts"
        scripts.mkdir(parents=True)
        self.runner = scripts / SOURCE.name
        shutil.copyfile(SOURCE, self.runner)
        (scripts / "sync_hosting_filesystems.py").touch()
        fake_bin = self.home / "bin"
        fake_bin.mkdir()
        fake_python = fake_bin / "python3"
        fake_python.write_text(
            "#!/bin/sh\n"
            "printf 'mock hosting sync invoked: %s\\n' \"$*\"\n"
            "exit \"$MOCK_EXIT\"\n"
        )
        fake_python.chmod(0o755)
        self.env = dict(os.environ)
        self.env["HOME"] = str(self.home)
        self.env["PATH"] = f"{fake_bin}:{os.environ['PATH']}"
        self.log_dir = self.home / "cobble-data" / "logs" / "hosting-sync"

    def run_job(self, *args, exit_code=0):
        return subprocess.run(
            ["bash", str(self.runner), *args],
            env=dict(self.env, MOCK_EXIT=str(exit_code)),
            capture_output=True, text=True,
        )

    def only_log(self):
        files = list(self.log_dir.glob("sync-*.log"))
        self.assertEqual(len(files), 1)
        self.assertEqual(self.log_dir.stat().st_mode & 0o077, 0)
        self.assertEqual(files[0].stat().st_mode & 0o077, 0)
        return files[0].read_text()

    def test_success_creates_private_log(self):
        result = self.run_job("--source", "all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mock hosting sync invoked:", self.only_log())
        self.assertIn("--source all", self.only_log())
        self.assertIn("exit=0", self.only_log())

    def test_failure_propagates_to_scheduler_and_log(self):
        result = self.run_job("--source", "villagelink", exit_code=23)
        self.assertEqual(result.returncode, 23)
        self.assertIn("--source villagelink", self.only_log())
        self.assertIn("exit=23", self.only_log())

    def test_dry_run_forwarded(self):
        result = self.run_job("--dry-run")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--dry-run", self.only_log())


if __name__ == "__main__":
    unittest.main()
