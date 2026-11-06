"""Synthetic-only tests: no real Cobble corpus is ever committed or needed."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cobble.local_search import build, search, show


def snapshot(folder, record):
    digest = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    versions = folder / "versions"
    versions.mkdir(parents=True)
    (versions / (digest + ".json")).write_text(json.dumps(record), encoding="utf-8")
    (folder / "latest.json").write_text(
        json.dumps({"version": f"versions/{digest}.json", "sha256": digest}),
        encoding="utf-8")
    return versions / (digest + ".json")


class LocalSearchTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.store = self.root / "private-store"
        self.index = self.store / "index" / "search.sqlite3"

        snapshot(self.store / "openai" / "conversations" / "chat-a", {
            "title": "The Lighthouse",
            "mapping": {
                "one": {"message": {"author": {"role": "user"},
                                    "content": {"parts": ["Saffron birds and sunlight"]}}},
                "branch": {"message": {"author": {"role": "assistant"},
                                       "content": {"parts": ["alternate branch saffron"]}}},
            },
        })
        snapshot(self.store / "github" / "conversations" / "Inky-Tech-Pty-Ltd"
                 / "Cobble" / "issues" / "3", {
            "issue": {"title": "Sandstone software", "body": "Should we use SQLite?"},
            "conversation_comments": [{"body": "Yes; sandstone testing first."}],
        })
        for source, filename, words in (
            ("inkytech", "about.html", "<h1>Koala memory workshop</h1>"),
            ("villagelink", "readme.md", "Willow governance and relations"),
        ):
            dest = self.store / "hosting" / source / filename
            dest.parent.mkdir(parents=True)
            dest.write_text(words, encoding="utf-8")

    def test_all_four_source_families_searchable(self):
        report = build(self.store, self.index)
        self.assertEqual([report[x]["indexed"] for x in
                          ("chatgpt", "github", "inkytech", "villagelink")],
                         [1, 1, 1, 1])
        for query, source, reference in (
            ("saffron", "chatgpt", "chat-a"),
            ("sandstone", "github", "Inky-Tech-Pty-Ltd/Cobble/issues/3"),
            ("koala", "inkytech", "about.html"),
            ("willow", "villagelink", "readme.md"),
        ):
            hits = search(self.index, query)
            self.assertEqual(len(hits), 1, hits)
            self.assertEqual(hits[0]["source"], source)
            self.assertEqual(hits[0]["reference"], reference)
            preview = show(self.index, hits[0]["id"])
            self.assertIn(query.casefold(), preview["text"].casefold())

    def test_edited_chat_branch_retained_for_retrieval(self):
        build(self.store, self.index)
        result = search(self.index, "alternate branch")
        self.assertEqual(result[0]["source"], "chatgpt")
        self.assertIn("alternate branch", show(self.index, result[0]["id"])["text"])

    def test_rebuild_replaces_stale_snapshot_results(self):
        build(self.store, self.index)
        self.assertEqual(len(search(self.index, "willow")), 1)
        target = self.store / "hosting" / "villagelink" / "readme.md"
        target.write_text("cedar governance", encoding="utf-8")
        build(self.store, self.index)
        self.assertEqual(search(self.index, "willow"), [])
        self.assertEqual(len(search(self.index, "cedar")), 1)

    def test_search_query_is_literal_and_not_fts_syntax(self):
        build(self.store, self.index)
        self.assertEqual(search(self.index, 'saffron" OR nonexistent'), [])
        self.assertEqual(len(search(self.index, "saffron")), 1)
        self.assertEqual(search(self.index, '""('), [])

    def test_no_symlinks_secrets_or_large_files(self):
        hosting = self.store / "hosting" / "inkytech"
        (hosting / "wp-config.php").write_text("forbiddenconfigkeyword", encoding="utf-8")
        (hosting / "giant.txt").write_bytes(b"x" * (1024 * 1024 + 1))
        (hosting / "link.txt").symlink_to(hosting / "about.html")
        build(self.store, self.index)
        self.assertEqual(search(self.index, "forbiddenconfigkeyword"), [])
        self.assertEqual(search(self.index, "giant"), [])
        self.assertEqual(len(search(self.index, "koala")), 1)

    def test_missing_source_is_reported_not_fabricated(self):
        only = self.root / "empty"
        report = build(only, self.root / "empty-index.sqlite3")
        self.assertTrue(all(not item["present"] for item in report.values()))
        self.assertEqual(search(self.root / "empty-index.sqlite3", "anything"), [])

    def test_bad_latest_pointer_fails_without_replacing_index(self):
        build(self.store, self.index)
        pointer = (self.store / "openai" / "conversations" / "chat-a" / "latest.json")
        pointer.write_text(json.dumps({"version": "../../secret.json"}))
        with self.assertRaisesRegex(ValueError, "Invalid snapshot version"):
            build(self.store, self.index)
        self.assertEqual(len(search(self.index, "saffron")), 1)

    def test_bounded_show_and_rejects_invalid_ids(self):
        build(self.store, self.index)
        hit = search(self.index, "saffron")[0]
        page = show(self.index, hit["id"], max_chars=100)
        self.assertLessEqual(len(page["text"]), 100)
        with self.assertRaises(ValueError):
            show(self.index, "../a")
        with self.assertRaises(ValueError):
            show(self.index, hit["id"], max_chars=100000)


if __name__ == "__main__":
    unittest.main()
