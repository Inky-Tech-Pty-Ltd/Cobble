"""Local-only regression coverage for the three GitHub conversation namespaces."""
import json
import tempfile
import unittest
from pathlib import Path

from cobble.github_conversations import preserve
from cobble.github_conversation_access import (
    read_github_conversation, read_github_conversation_mcp_text,
)
from cobble.github_memory_access import read_github_discussion


class ArchivedConversationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name)
        self.repo = "Inky-Tech-Pty-Ltd/VillageLink"
        self.issue = {
            "kind": "issue",
            "issue": {
                "number": 81,
                "title": "Interop: membrane boundaries",
                "body": "This is the opening proposal. " + "Long source context. " * 115,
                "user": {"login": "Joe-Rasmussen"},
                "html_url": f"https://github.com/{self.repo}/issues/81",
                "created_at": "2026-11-03T10:00:00Z",
                "updated_at": "2026-11-12T10:00:00Z",
                "state": "open",
            },
            "conversation_comments": [
                {"body": "Later Joe comment about linkage.",
                 "user": {"login": "Joe-Rasmussen"},
                 "html_url": "https://github.com/issue-comment/102",
                 "created_at": "2026-11-12T09:00:00Z"},
                {"body": "Sankarshan's earlier interop response.",
                 "user": {"login": "sankarshanmukhopadhyay"},
                 "html_url": "https://github.com/issue-comment/101",
                 "created_at": "2026-11-10T09:00:00Z"},
            ],
            "timeline": [
                {"event": "labeled", "actor": {"login": "Joe-Rasmussen"},
                 "created_at": "2026-11-11T09:00:00Z",
                 "url": "https://api.github.com/timeline/8"},
                {"event": "commented", "actor": {"login": "Joe-Rasmussen"},
                 "body": "A duplicate event, already in comments.",
                 "created_at": "2026-11-12T09:00:00Z"},
            ],
        }
        self.pull = {
            "kind": "pull_request",
            "issue": {
                "number": 81, "title": "Review the interchange boundary",
                "body": "PR conversation opening.",
                "user": {"login": "Joe-Rasmussen"},
                "html_url": f"https://github.com/{self.repo}/pull/81",
                "created_at": "2026-11-03T10:00:00Z",
            },
            "pull": {
                "number": 81, "body": "Implementation notes.",
                "merged_at": "2026-11-15T08:00:00Z",
            },
            "conversation_comments": [
                {"body": "Issue-style comment on PR.",
                 "user": {"login": "reviewer"},
                 "created_at": "2026-11-05T10:00:00Z"},
            ],
            "reviews": [
                {"body": "The boundary needs a test.",
                 "user": {"login": "sankarshanmukhopadhyay"},
                 "html_url": "https://github.com/reviews/10",
                 "state": "CHANGES_REQUESTED",
                 "submitted_at": "2026-11-06T11:00:00Z"},
            ],
            "review_comments": [
                {"body": "This line is unsafe.",
                 "user": {"login": "reviewer"},
                 "html_url": "https://github.com/review-comments/20",
                 "path": "src/cobble/membrane.py", "line": 41,
                 "side": "RIGHT", "in_reply_to_id": 19,
                 "created_at": "2026-11-07T11:00:00Z"},
            ],
            "timeline": [{"event": "merged", "actor": {"login": "maintainer"},
                          "created_at": "2026-11-15T08:00:00Z"}],
        }
        self.discussion = {
            "kind": "discussion",
            "discussion": {
                "number": 85, "title": "HCP boundaries",
                "body": "Does the relationship leak?",
                "author": {"login": "sankarshanmukhopadhyay"},
                "url": f"https://github.com/{self.repo}/discussions/85",
            },
            "comments": [{"comment": {
                "body": "We need to test the membranes.",
                "author": {"login": "Joe-Rasmussen"}},
                "replies": [{"body": "Agreed.", "author": {"login": "reviewer"}}]}],
        }
        preserve(self.store, self.repo, "issues", 81, self.issue)
        preserve(self.store, self.repo, "pulls", 81, self.pull)
        preserve(self.store, self.repo, "discussions", 85, self.discussion)

    def test_issue_81_has_correct_type_author_comments_and_order(self):
        r = read_github_conversation(self.store, self.repo, "issue", 81)
        self.assertEqual(r["kind"], "issue")
        self.assertEqual(r["number"], 81)
        self.assertEqual(r["author"], "Joe-Rasmussen")
        self.assertEqual(r["source_uri"], self.issue["issue"]["html_url"])
        combined = "".join(self.pages("issue", 81))
        self.assertIn("Interop: membrane boundaries", combined)
        self.assertIn("Sankarshan's earlier interop response.", combined)
        self.assertIn("Later Joe comment about linkage.", combined)
        self.assertIn("Timeline: labeled — Joe-Rasmussen", combined)
        self.assertIn("https://github.com/issue-comment/101", combined)
        self.assertLess(combined.index("Sankarshan's earlier"),
                        combined.index("Later Joe comment"))
        self.assertNotIn("A duplicate event", combined)

    def test_pr_has_review_inline_comments_and_file_provenance(self):
        content = "".join(self.pages("pull", 81))
        self.assertIn("PR conversation opening.", content)
        self.assertIn("Implementation notes.", content)
        self.assertIn("Issue-style comment on PR.", content)
        self.assertIn("Review — sankarshanmukhopadhyay", content)
        self.assertIn("State: CHANGES_REQUESTED", content)
        self.assertIn("Inline review comment — reviewer", content)
        self.assertIn("File: src/cobble/membrane.py", content)
        self.assertIn("Line: 41", content)
        self.assertIn("Reply to comment: 19", content)
        self.assertIn("Timeline: merged — maintainer", content)
        self.assertLess(content.index("Issue-style comment"),
                        content.index("The boundary needs a test"))
        self.assertNotIn("Interop: membrane boundaries", content)

    def test_discussion_compatibility_and_source_url(self):
        original = read_github_discussion(self.store, self.repo, 85)
        generic = read_github_conversation(self.store, self.repo, "discussion", 85)
        self.assertEqual(generic, {"kind": "discussion", **original})
        self.assertIn("We need to test the membranes.", generic["content"])
        self.assertIn("### Reply — reviewer", generic["content"])

    def pages(self, kind, number):
        parts, offset = [], 0
        while True:
            r = read_github_conversation(self.store, self.repo, kind, number,
                                         offset=offset, max_chars=1000)
            self.assertLessEqual(len(r["content"]), 1000)
            parts.append(r["content"])
            if r["next_offset"] is None:
                self.assertEqual(len("".join(parts)), r["total_chars"])
                return parts
            self.assertGreater(r["next_offset"], offset)
            offset = r["next_offset"]

    def test_mcp_wire_is_json_text_not_structured_dict(self):
        for kind, number in (("issue", 81), ("pull", 81), ("discussion", 85)):
            wire = read_github_conversation_mcp_text(
                self.store, self.repo, kind, number, 0, 1000)
            self.assertIsInstance(wire, str)
            self.assertEqual(json.loads(wire), read_github_conversation(
                self.store, self.repo, kind, number, 0, 1000))

    def test_missing_type_or_number_does_not_fall_back_to_github(self):
        for kind in ("pull_request", "issues", "../issues", "", None):
            with self.assertRaises(ValueError):
                read_github_conversation(self.store, self.repo, kind, 81)
        for kind in ("issue", "pull", "discussion"):
            with self.assertRaises(FileNotFoundError):
                read_github_conversation(self.store, self.repo, kind, 9999)
        with self.assertRaises(FileNotFoundError):
            read_github_conversation(self.store, self.repo, "discussion", 81)
        for invalid in (-1, True, "81"):
            with self.assertRaises(ValueError):
                read_github_conversation(self.store, self.repo, "issue", invalid)
        for invalid in (-5, "bad"):
            with self.assertRaises(ValueError):
                read_github_conversation(self.store, self.repo, "issue", 81, offset=invalid)
        for invalid in (1, 20000):
            with self.assertRaises(ValueError):
                read_github_conversation(self.store, self.repo, "issue", 81, max_chars=invalid)

    def test_archive_digest_and_record_identity_are_checked(self):
        root = self.store / "github" / "conversations" / "Inky-Tech-Pty-Ltd" / "VillageLink"
        base = root / "issues" / "81"
        pointer = json.loads((base / "latest.json").read_text())
        version = base / pointer["version"]
        version.write_text(version.read_text().replace("interop response", "tampered response"))
        with self.assertRaisesRegex(ValueError, "digest"):
            read_github_conversation(self.store, self.repo, "issue", 81)
        preserve(self.store, self.repo, "issues", 81, {
            **self.issue, "issue": {**self.issue["issue"], "number": 82}
        })
        with self.assertRaisesRegex(ValueError, "requested issue"):
            read_github_conversation(self.store, self.repo, "issue", 81)
        preserve(self.store, self.repo, "pulls", 81, {
            **self.pull, "pull": {**self.pull["pull"], "number": 82}
        })
        with self.assertRaisesRegex(ValueError, "pull metadata"):
            read_github_conversation(self.store, self.repo, "pull", 81)


if __name__ == "__main__":
    unittest.main()
