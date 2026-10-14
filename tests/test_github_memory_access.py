import json
import tempfile
import unittest
from pathlib import Path

from cobble.github_conversations import preserve
from cobble.github_memory_access import read_github_discussion


class ArchivedDiscussionReaderTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name)
        self.repo = "Inky-Tech-Pty-Ltd/Cobble"
        self.record = {
            "kind": "discussion",
            "discussion": {
                "number": 8, "title": "Independent review",
                "url": "https://github.com/Inky-Tech-Pty-Ltd/Cobble/discussions/8",
                "body": "Sankarshan's analysis: " + ("important detail " * 1500),
                "author": {"login": "Sankarshan"},
                "createdAt": "2026-10-14T00:00:00Z",
                "updatedAt": "2026-10-14T01:00:00Z",
            },
            "comments": [{
                "comment": {
                    "body": "A follow-up from Joe.",
                    "author": {"login": "Joe"},
                    "url": "https://github.com/comment/1",
                },
                "replies": [{
                    "body": "And a reply.",
                    "author": {"login": "Sankarshan"},
                    "url": "https://github.com/reply/1",
                }],
            }],
        }
        preserve(self.store, self.repo, "discussions", 8, self.record)

    def test_first_page_provenance_and_bounded_size(self):
        r = read_github_discussion(self.store, self.repo, 8)
        self.assertEqual(r["author"], "Sankarshan")
        self.assertIn("Sankarshan's analysis", r["content"])
        self.assertEqual(len(r["content"]), 12000)
        self.assertTrue(r["truncated"])
        self.assertEqual(r["next_offset"], 12000)
        self.assertEqual(r["source_uri"], self.record["discussion"]["url"])

    def test_paginate_without_losing_comment_and_reply(self):
        pages = []
        offset = 0
        while True:
            r = read_github_discussion(self.store, self.repo, 8,
                                       offset=offset, max_chars=3000)
            pages.append(r["content"])
            if r["next_offset"] is None:
                break
            offset = r["next_offset"]
        combined = "".join(pages)
        self.assertEqual(len(combined), r["total_chars"])
        self.assertIn("A follow-up from Joe.", combined)
        self.assertIn("And a reply.", combined)
        self.assertIn("## Comment — Joe", combined)

    def test_preserved_snapshot_is_used_not_network(self):
        r = read_github_discussion(self.store, self.repo, 8, offset=10)
        self.assertIn("Locally archived", r["scope"])
        self.assertGreater(len(r["content"]), 0)

    def test_malformed_names_and_pagination_rejected(self):
        for slug in ("../Cobble", "someone/../../secret"):
            with self.assertRaises(ValueError):
                read_github_discussion(self.store, slug, 8)
        for number in (0, -1, True):
            with self.assertRaises(ValueError):
                read_github_discussion(self.store, self.repo, number)
        for offset in (-1, "zero"):
            with self.assertRaises(ValueError):
                read_github_discussion(self.store, self.repo, 8, offset=offset)
        with self.assertRaises(ValueError):
            read_github_discussion(self.store, self.repo, 8, max_chars=40000)

    def test_tampered_snapshot_detected(self):
        base = (self.store / "github" / "conversations"
                / "Inky-Tech-Pty-Ltd" / "Cobble" / "discussions" / "8")
        pointer = json.loads((base / "latest.json").read_text())
        path = base / pointer["version"]
        path.write_text(path.read_text().replace("Independent review", "Corrupted!"))
        with self.assertRaisesRegex(ValueError, "digest"):
            read_github_discussion(self.store, self.repo, 8)

    def test_missing_discussion_is_not_silently_fetched(self):
        with self.assertRaises(FileNotFoundError):
            read_github_discussion(self.store, self.repo, 9)
