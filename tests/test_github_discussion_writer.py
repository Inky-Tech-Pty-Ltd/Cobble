"""Offline regression coverage for Puck identity, input scope and API flow."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cobble import github_discussion_writer as writer

REPO = "Inky-Tech-Pty-Ltd/VillageLink"


class DiscussionWriterTests(unittest.TestCase):
    def test_validation_restricts_repository_and_input(self):
        self.assertEqual(writer.validate_request(REPO, 89, "hello"), (REPO, 89, "hello"))
        for repo in ("Inky-Tech-Pty-Ltd/Cobble", "Other/VillageLink", "../VillageLink"):
            with self.assertRaises(ValueError):
                writer.validate_request(repo, 89, "hello")
        for number in (0, -1, True, "89", 1000001):
            with self.assertRaises(ValueError):
                writer.validate_request(REPO, number, "hello")
        for body in ("", "  ", "☃" * 5000, None):
            with self.assertRaises(ValueError):
                writer.validate_request(REPO, 89, body)

    def test_disabled_by_default_even_with_joe_token(self):
        with patch.dict(os.environ, {"GH_TOKEN": "gho_joe"}, clear=True):
            with self.assertRaises(PermissionError):
                writer.post_discussion_comment(REPO, 89, "hello")

    def test_token_file_requires_private_owner_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "puck-token"
            path.write_text("token-just-for-tests\n")
            with patch.dict(os.environ, {"COBBLE_PUCK_GITHUB_TOKEN_FILE": str(path)}, clear=True):
                path.chmod(0o644)
                with self.assertRaises(PermissionError):
                    writer._read_puck_token()
                path.chmod(0o600)
                self.assertEqual(writer._read_puck_token(), "token-just-for-tests")
                link = Path(tmp) / "link"
                link.symlink_to(path)
                os.environ["COBBLE_PUCK_GITHUB_TOKEN_FILE"] = str(link)
                with self.assertRaises(PermissionError):
                    writer._read_puck_token()

    def test_wrong_identity_never_mutates(self):
        calls = []
        def fake_graphql(query, variables, token):
            calls.append(query)
            return {"viewer": {"login": "Joe-Rasmussen"},
                    "repository": {"discussion": {"id": "D_89", "url": "https://github.test"}}}
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISCUSSIONS": "1"}, clear=True), \
             patch.object(writer, "_read_puck_token", return_value="test"), \
             patch.object(writer, "_graphql", side_effect=fake_graphql):
            with self.assertRaises(PermissionError):
                writer.post_discussion_comment(REPO, 89, "hello")
        self.assertEqual(calls, [writer._LOOKUP])

    def test_missing_discussion_never_mutates(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISCUSSIONS": "1"}, clear=True), \
             patch.object(writer, "_read_puck_token", return_value="test"), \
             patch.object(writer, "_graphql", return_value={"viewer": {"login": "puck-inky"},
                                                            "repository": {"discussion": None}}) as call:
            with self.assertRaises(ValueError):
                writer.post_discussion_comment(REPO, 89, "hello")
        self.assertEqual(call.call_count, 1)

    def test_posts_and_returns_actual_comment_url(self):
        calls = []
        def fake_graphql(query, variables, token):
            calls.append((query, variables, token))
            if query == writer._LOOKUP:
                return {"viewer": {"login": "puck-inky"},
                        "repository": {"discussion": {"id": "D_89"}}}
            return {"addDiscussionComment": {"comment": {
                "id": "DC_1", "url": "https://github.com/Inky-Tech-Pty-Ltd/VillageLink/discussions/89#discussioncomment-1",
                "author": {"login": "puck-inky"}}}}
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISCUSSIONS": "1"}, clear=True), \
             patch.object(writer, "_read_puck_token", return_value="fake-puck-token"), \
             patch.object(writer, "_graphql", side_effect=fake_graphql):
            result = writer.post_discussion_comment(REPO, 89, "Thoughts on membranes")
        self.assertTrue(result["posted"])
        self.assertEqual(result["author"], "puck-inky")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][1], {"discussionId": "D_89", "body": "Thoughts on membranes"})
        self.assertEqual(calls[1][2], "fake-puck-token")

    def test_graphql_permission_error_is_classified_without_echoing_text(self):
        secret = "github_pat_should_never_appear"
        response = json.dumps({"errors": [{"message":
            "Resource not accessible by personal access token " + secret}]}).encode()
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, amount): return response
        with patch.object(writer.urllib.request, "urlopen", return_value=FakeResponse()):
            with self.assertRaisesRegex(PermissionError,
                    "GitHub comment mutation rejected: token lacks the required repository permission") as caught:
                writer._graphql(writer._POST, {}, secret)
            self.assertNotIn(secret, str(caught.exception))


    def test_invalid_graphql_response_denied_without_echoing_secrets(self):
        response = json.dumps({"errors": [{"message": "a token might be echoed here"}]}).encode()
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, amount): return response
        with patch.object(writer.urllib.request, "urlopen", return_value=FakeResponse()):
            with self.assertRaisesRegex(PermissionError, "GitHub discussion lookup rejected: unclassified GraphQL error") as caught:
                writer._graphql(writer._LOOKUP, {}, "private-secret")
            self.assertNotIn("private-secret", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
