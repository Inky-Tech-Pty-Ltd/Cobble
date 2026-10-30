"""Offline denial tests for the Puck-scoped GitHub writer."""
import os
import unittest
from unittest.mock import patch

from cobble import puck_github_writer as w


class PuckWriterTests(unittest.TestCase):
    def test_disabled_even_with_joe_oauth_token(self):
        with patch.dict(os.environ, {"GH_TOKEN": "gho_joe", "GITHUB_TOKEN": "gho_joe"}, clear=True):
            with self.assertRaises(PermissionError):
                w.create_branch("puck/work/safe")

    def test_refuses_joe_token_even_if_enabled(self):
        with patch.dict(os.environ, {
            "COBBLE_MCP_ALLOW_PUCK_WRITES": "1",
            "PUCK_GITHUB_INSTALLATION_TOKEN": "gho_joe",
        }, clear=True):
            with self.assertRaises(PermissionError):
                w.create_branch("puck/work/safe")

    def test_invalid_target_rejected_without_network(self):
        with patch.object(w, "_request", side_effect=AssertionError("network accessed")):
            with self.assertRaises(ValueError):
                w.create_branch("main")
            with self.assertRaises(ValueError):
                w.write_file("main", "docs/experiments/test.md", "hi", "msg")
            with self.assertRaises(ValueError):
                w.write_file("puck/work/safe", ".github/workflows/evil.yml", "hi", "msg")
            with self.assertRaises(ValueError):
                w.write_file("puck/work/safe", "docs/experiments/good.md", "hi", "bad\nmsg")

    def test_valid_branch_and_file_use_only_scoped_token(self):
        calls = []
        def fake(method, path, token, body=None):
            calls.append((method, path, token, body))
            if path.startswith("/installation/repositories"):
                return {"repositories": [{"full_name": w.REPOSITORY}]}
            if method == "GET":
                return {"object": {"sha": "abc123"}}
            if method == "POST":
                return {"ref": "refs/heads/puck/work/good"}
            return {"commit": {"sha": "def456"}}
        with patch.dict(os.environ, {
            "COBBLE_MCP_ALLOW_PUCK_WRITES": "1",
            "PUCK_GITHUB_INSTALLATION_TOKEN": "ghs_puckfake",
            "GH_TOKEN": "gho_joe",
        }, clear=True), patch.object(w, "_request", side_effect=fake):
            result = w.create_branch("puck/work/good")
            self.assertTrue(result["created"])
            result = w.write_file("puck/work/good", "docs/experiments/test.md", "body", "message")
            self.assertEqual(result["commit_sha"], "def456")
        self.assertTrue(all(call[2] == "ghs_puckfake" for call in calls))
        write = [c for c in calls if c[0] == "PUT"][0]
        self.assertEqual(write[3]["author"]["name"], w.BOT_NAME)
        self.assertEqual(write[3]["committer"]["name"], w.BOT_NAME)
        self.assertNotIn("gho_joe", str(calls))

    def test_installation_must_include_repository(self):
        with patch.object(w, "_request", return_value={"repositories": []}):
            with self.assertRaises(PermissionError):
                w._installation("ghs_puckfake")


if __name__ == "__main__":
    unittest.main()
