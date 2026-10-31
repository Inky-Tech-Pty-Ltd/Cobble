"""Offline negative and dispatch-contract tests."""
import base64
import json
import os
import unittest
from unittest.mock import patch
from cobble import puck_github_writer as w


class PuckDispatcherTests(unittest.TestCase):
    def test_disabled_when_only_joe_credentials_exist(self):
        with patch.dict(os.environ, {"GH_TOKEN": "gho_joe"}, clear=True):
            with self.assertRaises(PermissionError):
                w.submit_write("docs/experiments/a.md", "hi", "write")

    def test_refuses_joe_as_configured_identity(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISPATCH": "1",
                                     "PUCK_DISPATCH_LOGIN": "Joe-Rasmussen",
                                     "PUCK_DISPATCH_TOKEN": "ghp_joe"}, clear=True):
            with self.assertRaises(PermissionError):
                w.submit_write("docs/experiments/a.md", "hi", "write")

    def test_invalid_payload_never_uses_network(self):
        with patch.object(w, "_api", side_effect=AssertionError("network")):
            for path in (".github/workflows/x.yml", "../escape.md", "README.md"):
                with self.assertRaises(ValueError):
                    w.submit_write(path, "hi", "test")
            with self.assertRaises(ValueError):
                w.submit_write("docs/experiments/a.md", "hi", "two\nlines")
            with self.assertRaises(ValueError):
                w.submit_write("docs/experiments/a.md", "x" * 12001, "test")

    def test_wrong_authenticated_actor_refused(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISPATCH": "1",
                                     "PUCK_DISPATCH_LOGIN": "puck-trigger",
                                     "PUCK_DISPATCH_TOKEN": "service-secret"}, clear=True):
            with patch.object(w, "_api", return_value={"login": "Joe-Rasmussen"}):
                with self.assertRaises(PermissionError):
                    w.submit_write("docs/experiments/a.md", "hi", "test")

    def test_valid_dispatch_is_bounded_and_not_a_commit(self):
        calls = []
        def api(method, path, token, payload=None):
            calls.append((method, path, token, payload))
            if path == "/user":
                return {"login": "puck-trigger"}
            return {}
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISPATCH": "1",
                                     "PUCK_DISPATCH_LOGIN": "puck-trigger",
                                     "PUCK_DISPATCH_TOKEN": "service-secret",
                                     "GH_TOKEN": "gho_joe"}, clear=True):
            with patch.object(w, "_api", side_effect=api):
                result = w.submit_write("docs/experiments/a.md", "hello", "test")
        self.assertTrue(result["submitted"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1][0], "POST")
        self.assertEqual(calls[1][2], "service-secret")
        self.assertEqual(calls[1][3]["ref"], "main")
        self.assertEqual(set(calls[1][3]["inputs"]), {"request_b64"})
        request = json.loads(base64.b64decode(calls[1][3]["inputs"]["request_b64"]))
        self.assertEqual(request, {"path": "docs/experiments/a.md",
                                   "content": "hello", "message": "test"})


if __name__ == "__main__":
    unittest.main()
