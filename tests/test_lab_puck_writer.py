"""Offline negative tests of the Puck socket client and broker."""
import base64
import json
import os
import unittest
from unittest.mock import patch
from cobble import puck_github_writer as client
from cobble import puck_dispatch_broker as broker


class PuckBrokerTests(unittest.TestCase):
    def test_valid_markdown_path_is_accepted(self):
        request = {"path": "docs/experiments/test.md",
                   "content": "hello", "message": "test"}
        self.assertEqual(client.validate_request(request), request)

    def test_disabled_with_joe_credentials(self):
        with patch.dict(os.environ, {"GH_TOKEN": "gho_joe"}, clear=True):
            with self.assertRaises(PermissionError):
                client.submit_write("docs/experiments/test.md", "hello", "test")

    def test_invalid_file_or_request_denied(self):
        for path in ("main", ".github/workflows/backdoor.yml", "../test.md"):
            with self.assertRaises(ValueError):
                client.submit_write(path, "hello", "test")
        with self.assertRaises(ValueError):
            client.validate_request({"path": "docs/experiments/a.md",
                                     "content": "ok", "message": "test", "author": "Joe"})

    def test_requires_isolated_socket(self):
        with patch.dict(os.environ, {"COBBLE_MCP_ALLOW_PUCK_DISPATCH": "1",
                                     "PUCK_DISPATCH_TOKEN": "ghs_fake"}, clear=True):
            with self.assertRaises(PermissionError):
                client.submit_write("docs/experiments/test.md", "hello", "test")

    def test_broker_uses_expected_app_installation_and_permissions(self):
        calls = []
        def fake_api(method, route, token, body=None):
            calls.append((method, route, token, body))
            if route.endswith("/access_tokens"):
                return {"token": "ghs_dispatcher"}
            return {}
        with patch.object(broker, "jwt_for_app", return_value="jwt_of_app_5549836"), \
             patch.object(broker, "api", side_effect=fake_api):
            result = broker.dispatch({"path": "docs/experiments/a.md",
                                      "content": "hi", "message": "hello"}, "/nonexistent/key")
        self.assertTrue(result["submitted"])
        self.assertEqual(calls[0][1], "/app/installations/177074425/access_tokens")
        self.assertEqual(calls[0][3]["repositories"], ["InkyTech"])
        self.assertEqual(calls[0][3]["permissions"], {"actions": "write"})
        self.assertIn("puck-writer-v1.yml/dispatches", calls[1][1])
        self.assertEqual(calls[1][2], "ghs_dispatcher")
        request = json.loads(base64.b64decode(calls[1][3]["inputs"]["request_b64"]))
        self.assertEqual(request["path"], "docs/experiments/a.md")

    def test_broker_does_not_issue_token_for_invalid_target(self):
        with patch.object(broker, "jwt_for_app", side_effect=AssertionError("key used")):
            with self.assertRaises(ValueError):
                broker.dispatch({"path": "README.md", "content": "bad", "message": "test"},
                                "/nonexistent/key")


if __name__ == "__main__":
    unittest.main()
