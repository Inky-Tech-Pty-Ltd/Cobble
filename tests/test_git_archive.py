import subprocess
import tempfile
import unittest
from pathlib import Path
from cobble.git_archive import archive_repository, capture_file_trace
from cobble.traces import resolve_local


def git(*args, cwd=None):
    command = ["git", *(["-C", str(cwd)] if cwd else []), *args]
    return subprocess.check_output(command, stderr=subprocess.PIPE).decode().strip()


class GitArchiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        self.source = base / "source"
        self.store = base / "memory"
        self.source.mkdir()
        git("init", "-q", "-b", "main", str(self.source))
        git("config", "user.email", "test@example.org", cwd=self.source)
        git("config", "user.name", "Test", cwd=self.source)
        (self.source / "README.md").write_text("Memory is the masterpiece.\n")
        git("add", "README.md", cwd=self.source)
        git("commit", "-qm", "First memory", cwd=self.source)
        self.first = git("rev-parse", "HEAD", cwd=self.source)

    def test_archive_is_local_and_contains_history(self):
        record = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        self.assertEqual(record["head"], self.first)
        dest = Path(record["archive_path"])
        self.assertEqual(git("cat-file", "-t", self.first, cwd=dest), "commit")
        self.assertEqual(git("show", f"{self.first}:README.md", cwd=dest),
                         "Memory is the masterpiece.")
        manifest = self.store / "github" / "manifests" / "Inky-Tech-Pty-Ltd" / "Cobble" / f"{self.first}.json"
        self.assertTrue(manifest.exists())

    def test_incremental_capture_keeps_earlier_revisions(self):
        first = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        (self.source / "README.md").write_text("Second revision\n")
        git("commit", "-qam", "Second memory", cwd=self.source)
        second = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        self.assertNotEqual(first["head"], second["head"])
        archive = Path(second["archive_path"])
        self.assertEqual(git("show", f"{self.first}:README.md", cwd=archive),
                         "Memory is the masterpiece.")
        self.assertEqual(git("show", f"{second['head']}:README.md", cwd=archive),
                         "Second revision")
        again = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        self.assertEqual(second["head"], again["head"])
        directory = self.store / "github" / "manifests" / "Inky-Tech-Pty-Ltd" / "Cobble"
        self.assertEqual(len(list(directory.glob("*.json"))), 2)

    def test_minted_trace_resolves_from_archive_copy(self):
        record = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        trace = capture_file_trace(self.store, "Inky-Tech-Pty-Ltd/Cobble",
                                   record["head"], "README.md", "Memory is the masterpiece.")
        self.assertEqual(resolve_local(self.store, trace["uri"]),
                         "Memory is the masterpiece.\n")
        self.assertIn(self.first, trace["source_uri"])

    def test_rejects_bad_paths_and_slugs(self):
        record = archive_repository(self.store, "Inky-Tech-Pty-Ltd/Cobble", self.source)
        with self.assertRaises(ValueError):
            archive_repository(self.store, "../bad", self.source)
        with self.assertRaises(ValueError):
            capture_file_trace(self.store, "Inky-Tech-Pty-Ltd/Cobble",
                               record["head"], "../private", "secret")
