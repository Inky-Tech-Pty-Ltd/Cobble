import json
import tempfile
import unittest
from pathlib import Path

from cobble.github_conversations import (
    GitHubAPI, graphql_nodes, ingest_conversations, preserve
)


class FakeAPI:
    token = "fake"
    def __init__(self):
        self.events = []
        self.issue = {"number": 7, "title": "A thought", "body": "Why?", "user": {"login": "Joe"}}
        self.pull_issue = {"number": 8, "title": "Change", "pull_request": {"url": "/pull/8"}}

    def pages(self, path):
        self.events.append(path)
        if path.endswith("/issues?state=all"):
            return iter([self.issue, self.pull_issue])
        if path.endswith("/issues/7/comments"):
            return iter([{"id": 70, "body": "Because"}])
        if path.endswith("/pulls/8/reviews"):
            return iter([{"id": 80, "body": "Looks good"}])
        if path.endswith("/pulls/8/comments"):
            return iter([{"id": 81, "body": "Change this line"}])
        if path.endswith("/issues/8/comments"):
            return iter([{"id": 82, "body": "Discussion"}])
        if path.endswith("/issues/7/timeline") or path.endswith("/issues/8/timeline"):
            return iter([])
        raise AssertionError(path)

    def request(self, path, payload=None):
        self.events.append(path)
        if path.endswith("/pulls/8"):
            return {"number": 8, "body": "Implementation"}, ""
        raise AssertionError(path)

    def graphql(self, query, **variables):
        self.events.append(("graphql", variables))
        if "repository(owner:" in query:
            return {"repository": {"discussions": {
                "nodes": [{"id": "D1", "number": 3, "body": "Idea", "title": "Memory"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }}}
        if "... on Discussion {" in query:
            return {"node": {"comments": {
                "nodes": [{"id": "C1", "body": "What about this?"}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}
            }}}
        return {"node": {"replies": {
            "nodes": [{"id": "R1", "body": "Yes!"}],
            "pageInfo": {"hasNextPage": False, "endCursor": None}
        }}}


class ConversationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name)
        self.slug = "Inky-Tech-Pty-Ltd/Cobble"

    def record(self, kind, number):
        root = self.store / "github" / "conversations" / "Inky-Tech-Pty-Ltd" / "Cobble"
        base = root / kind / str(number)
        pointer = json.loads((base / "latest.json").read_text())
        return json.loads((base / pointer["version"]).read_text())

    def test_issues_prs_review_comments_and_discussion_replies(self):
        counts = ingest_conversations(self.store, self.slug, FakeAPI())
        self.assertEqual(counts, {"issues": 1, "pulls": 1, "discussions": 1})
        self.assertEqual(self.record("issues", 7)["conversation_comments"][0]["body"], "Because")
        self.assertEqual(self.record("pulls", 8)["reviews"][0]["body"], "Looks good")
        self.assertEqual(self.record("pulls", 8)["review_comments"][0]["body"], "Change this line")
        self.assertEqual(self.record("discussions", 3)["comments"][0]["replies"][0]["body"], "Yes!")

    def test_repeat_is_idempotent_and_edit_keeps_old_revision(self):
        api = FakeAPI()
        ingest_conversations(self.store, self.slug, api)
        path = self.store / "github" / "conversations" / "Inky-Tech-Pty-Ltd" / "Cobble" / "issues" / "7" / "versions"
        self.assertEqual(len(list(path.glob("*.json"))), 1)
        ingest_conversations(self.store, self.slug, api)
        self.assertEqual(len(list(path.glob("*.json"))), 1)
        api.issue = {**api.issue, "body": "Changed question"}
        ingest_conversations(self.store, self.slug, api)
        self.assertEqual(len(list(path.glob("*.json"))), 2)
        self.assertEqual(self.record("issues", 7)["issue"]["body"], "Changed question")

    def test_partial_import_is_explicit(self):
        result = ingest_conversations(self.store, self.slug, FakeAPI(), False)
        self.assertEqual(result["discussions"], "SKIPPED")

    def test_pagination_uses_all_cursor_pages(self):
        class Pages:
            def graphql(self, query, **vars):
                cursor = vars["after"]
                return {"repository": {"discussions": {
                    "nodes": [{"number": 1 if cursor is None else 2}],
                    "pageInfo": {"hasNextPage": cursor is None,
                                 "endCursor": "next" if cursor is None else None}
                }}}
        nodes = list(graphql_nodes(Pages(), "query", ("repository", "discussions"),
                                  owner="x", repo="y"))
        self.assertEqual([n["number"] for n in nodes], [1, 2])

    def test_rejects_unsafe_repository_names(self):
        with self.assertRaises(ValueError):
            preserve(self.store, "../oops", "issues", 1, {"x": 1})
