"""Offline archive portability regression and negative tests."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cobble.portability import export_corpus, restore_corpus


def snapshot(store, slug, kind, number, record):
    base = Path(store) / "github/conversations" / slug / kind / str(number)
    canonical = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    version = base / "versions" / (digest + ".json")
    version.parent.mkdir(parents=True, exist_ok=True)
    version.write_text(json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    (base / "latest.json").write_text(
        json.dumps({"sha256": digest, "version": f"versions/{digest}.json"}))


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.src, self.dst = self.root / "original", self.root / "restored"
        self.package = self.root / "corpus.json"
        self.repo = "Inky-Tech-Pty-Ltd/Cobble"
        snapshot(self.src, self.repo, "issues", 1, {"body": "initial", "kind": "issue"})
        snapshot(self.src, self.repo, "issues", 1, {"body": "updated", "kind": "issue"})
        snapshot(self.src, self.repo, "discussions", 8, {"comments": [], "kind": "discussion"})

    def export(self):
        return export_corpus(self.src, self.package, [self.repo])

    def test_roundtrip_and_determinism(self):
        self.assertEqual(self.export()["conversations"], 2)
        before = self.package.read_bytes()
        self.export()
        self.assertEqual(self.package.read_bytes(), before)
        self.assertEqual(restore_corpus(self.package, self.dst)["conversations"], 2)
        restore_corpus(self.package, self.dst)
        original = self.src / "github/conversations"
        restored = self.dst / "github/conversations"
        for file in original.rglob("*.json"):
            self.assertEqual(file.read_bytes(), (restored / file.relative_to(original)).read_bytes())

    def assert_rejects(self, mutator):
        self.export()
        package = json.loads(self.package.read_text())
        mutator(package)
        self.package.write_text(json.dumps(package))
        with self.assertRaises(ValueError):
            restore_corpus(self.package, self.dst)
        self.assertFalse((self.dst / "github").exists())

    def test_rejects_path_traversal(self):
        self.assert_rejects(lambda p: p["entries"][0].update(path="../../escape"))

    def test_rejects_corrupted_entry_digest(self):
        self.assert_rejects(lambda p: p["entries"][0].update(sha256="0" * 64))

    def test_rejects_missing_snapshots(self):
        self.assert_rejects(lambda p: p.update(
            entries=[e for e in p["entries"] if "/versions/" not in e["path"]]))

    def test_rejects_duplicate_entries(self):
        self.assert_rejects(lambda p: p["entries"].append(dict(p["entries"][0])))

    def test_rejects_destination_conflicts(self):
        self.export()
        restore_corpus(self.package, self.dst)
        next((self.dst / "github/conversations").rglob("latest.json")).write_text("conflict")
        with self.assertRaises(ValueError):
            restore_corpus(self.package, self.dst)


    def test_rejects_invalid_latest_pointer(self):
        import base64
        import hashlib
        def mutate(package):
            pointer = next(e for e in package["entries"] if e["path"].endswith("latest.json"))
            content = b'{"sha256": "0", "version": "versions/other.json"}'
            pointer["data_base64"] = base64.b64encode(content).decode("ascii")
            pointer["sha256"] = hashlib.sha256(content).hexdigest()
        self.assert_rejects(mutate)

    def test_rejects_symlink_in_source(self):
        self.export()
        root = self.src / "github/conversations" / self.repo
        (root / "linked.json").symlink_to(self.package)
        with self.assertRaises(ValueError):
            self.export()

    def test_rejects_symlink_in_destination(self):
        self.export()
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = self.dst / "github"
            root.mkdir(parents=True)
            (root / "conversations").symlink_to(temp, target_is_directory=True)
            with self.assertRaises(ValueError):
                restore_corpus(self.package, self.dst)

    def test_rejects_symlink_in_export_github_parent(self):
        github = self.src / "github"
        moved = self.root / "external-github"
        github.rename(moved)
        github.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.export()

    def test_rejects_symlink_in_export_owner_parent(self):
        owner = self.src / "github/conversations/Inky-Tech-Pty-Ltd"
        moved = self.root / "external-owner"
        owner.rename(moved)
        owner.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.export()

    def test_rejects_symlink_in_restore_github_parent(self):
        self.export()
        external = self.root / "external-output"
        external.mkdir()
        self.dst.mkdir()
        (self.dst / "github").symlink_to(external, target_is_directory=True)
        with self.assertRaises(ValueError):
            restore_corpus(self.package, self.dst)
        self.assertEqual(list(external.iterdir()), [])

    def test_rejects_uningested_repo(self):
        with self.assertRaises(ValueError):
            export_corpus(self.src, self.package, ["Unknown/Repo"])


if __name__ == "__main__":
    unittest.main()
