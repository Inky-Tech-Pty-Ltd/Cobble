"""Offline tests for the locked, logged GitHub sync scheduler entry point."""
import fcntl
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "run_github_sync.sh"


@unittest.skipUnless(os.name == "posix" and shutil.which("flock"), "requires Linux flock")
class ScheduledGithubSyncTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        scripts = self.home / "Cobble" / "scripts"
        scripts.mkdir(parents=True)
        self.runner = scripts / SOURCE.name
        shutil.copyfile(SOURCE, self.runner)
        self.importer = scripts / "sync_github_corpus.sh"
        self.importer.write_text("#!/bin/bash\necho 'mock importer ran'\nexit \"${MOCK_STATUS:-0}\"\n")
        self.logs = self.home / "cobble-data" / "logs" / "github-sync"

    def run_job(self, **extra_env):
        env = dict(os.environ, HOME=str(self.home), **extra_env)
        return subprocess.run(["bash", str(self.runner)], env=env, text=True, capture_output=True)

    def log_text(self):
        files = list(self.logs.glob("sync-*.log"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].stat().st_mode & 0o077, 0)  # private to owner
        return files[0].read_text()

    def test_success_writes_private_dated_log(self):
        result = self.run_job()
        self.assertEqual(result.returncode, 0, result.stderr)
        log = self.log_text()
        self.assertIn("mock importer ran", log)
        self.assertIn("exit=0", log)

    def test_importer_failure_propagates_to_scheduler(self):
        result = self.run_job(MOCK_STATUS="42")
        self.assertEqual(result.returncode, 42)
        self.assertIn("exit=42", self.log_text())

    def test_overlapping_run_refused(self):
        self.logs.mkdir(parents=True)
        with (self.logs / ".sync.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_job()
        self.assertEqual(result.returncode, 75)
        self.assertIn("refusing to overlap", self.log_text())
        self.assertNotIn("mock importer ran", self.log_text())


if __name__ == "__main__":
    unittest.main()
