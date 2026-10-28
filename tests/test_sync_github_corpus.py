"""Offline smoke tests for the organisation-wide GitHub sync wrapper."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "sync_github_corpus.sh"


class SyncGithubCorpusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "Cobble"
        scripts = self.project / "scripts"
        scripts.mkdir(parents=True)
        self.sync = scripts / SOURCE.name
        shutil.copyfile(SOURCE, self.sync)
        for name in ("import_git.py", "import_github_conversations.py"):
            (scripts / name).touch()
        tools = self.root / "bin"
        tools.mkdir()
        self.log = self.root / "commands.log"
        self.make_tool("gh", r'''#!/bin/sh
printf 'gh %s\n' "$*" >> "$MOCK_LOG"
if [ "$1" = repo ] && [ "$2" = list ]; then
  if [ "${GH_FAIL:-}" = 1 ]; then exit 23; fi
  printf 'Cobble\nInkyBooks\n'
elif [ "$1" = repo ] && [ "$2" = clone ]; then
  mkdir -p "$4/.git"
else
  exit 11
fi
''')
        self.make_tool("git", r'''#!/bin/sh
printf 'git %s\n' "$*" >> "$MOCK_LOG"
''')
        self.make_tool("python3", r'''#!/bin/sh
printf 'python3 %s\n' "$*" >> "$MOCK_LOG"
case "$1" in
  */import_github_conversations.py)
    owner="${2%/*}"
    name="${2#*/}"
    folder="$4/github/conversations/$owner/$name/issues/1/versions"
    mkdir -p "$folder"
    printf 'snapshot' > "$folder/one.json"
    ;;
esac
''')
        self.store = self.root / "archive"
        self.checkouts = self.root / "checkouts"
        self.env = dict(os.environ)
        self.env["PATH"] = f"{tools}:{os.environ['PATH']}"
        self.env["MOCK_LOG"] = str(self.log)

    def make_tool(self, name, content):
        path = self.root / "bin" / name
        path.write_text(content)
        path.chmod(0o755)

    def run_sync(self, *extra, **env_overrides):
        env = dict(self.env, **env_overrides)
        return subprocess.run([
            "bash", str(self.sync),
            "--store", str(self.store),
            "--checkouts", str(self.checkouts), *extra
        ], env=env, cwd=self.root, text=True, capture_output=True)

    def test_dry_run_does_not_create_archive_or_checkouts(self):
        run = self.run_sync("--dry-run")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("DRY RUN: 2 accessible repositories", run.stdout)
        self.assertIn("Inky-Tech-Pty-Ltd/InkyBooks", run.stdout)
        self.assertFalse(self.store.exists())
        self.assertFalse(self.checkouts.exists())
        self.assertNotIn("python3", self.log.read_text())
        self.assertNotIn("gh repo clone", self.log.read_text())

    def test_archives_all_and_repeats_without_recloning(self):
        first = self.run_sync()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("Sync complete: 2 repositories; 2 new conversation versions.", first.stdout)
        self.assertTrue((self.checkouts / "Cobble" / ".git").exists())
        second = self.run_sync()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("Sync complete: 2 repositories; 0 new conversation versions.", second.stdout)
        log = self.log.read_text()
        self.assertEqual(log.count("gh repo clone"), 2)
        self.assertIn("git -C", log)
        self.assertIn("fetch origin --tags", log)
        self.assertEqual(log.count("import_git.py"), 4)
        self.assertEqual(log.count("import_github_conversations.py"), 4)

    def test_discovery_failure_stops_before_changes(self):
        run = self.run_sync(GH_FAIL="1")
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse(self.store.exists())
        self.assertFalse(self.checkouts.exists())

    def test_existing_non_checkout_refuses_to_overwrite(self):
        (self.checkouts / "Cobble").mkdir(parents=True)
        (self.checkouts / "Cobble" / "keep.txt").write_text("important")
        run = self.run_sync()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("not a Git checkout", run.stderr)
        self.assertEqual((self.checkouts / "Cobble" / "keep.txt").read_text(), "important")
        self.assertNotIn("python3", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
