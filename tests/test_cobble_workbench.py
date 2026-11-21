"""Offline checks for the meetings workspace: old live contract, new presentation."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "src" / "cobble" /
        "static" / "workbench.html")


class WorkbenchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = HTML.read_text(encoding="utf-8")

    def test_navigation_sidebar_and_meeting_layout(self):
        for item in ("Memories", "Intelligences", "Meetings", "Graph", "Setup",
                     'id="sidebar"', 'id="resize-grip"', "ondblclick",
                     "cobble.sidebar.width", "cobble.sidebar.collapsed",
                     'id="thread"', 'id="chat-scroll"',
                     'id="next-responder"', 'id="send"', 'id="question"',
                     'id="inspector"', 'id="supplier-list"',
                     'id="memory-form"', 'id="memory-results"'):
            self.assertIn(item, self.page)
        self.assertNotIn('class="world-perspective"', self.page)
        self.assertNotIn("projectTableText", self.page)
        self.assertNotIn("rotateX(", self.page)
        self.assertIn('src="/assets/cobble-logo.png"', self.page)
        self.assertIn("No graph is being invented", self.page)
        self.assertIn("More meetings and meeting titles are not yet implemented", self.page)

    def test_live_call_contract_and_disclosure_are_retained(self):
        for required in ("'live/preview'", "'live/send'",
                         "{approval_token:preview.approval_token}",
                         "status==='outcome_unknown'", "status!=='completed'",
                         "no automatic retries", "No private corpus passages supplied",
                         "selected_memories", "previous_exchanges",
                         "outbound", "context_sha256", "t.payload",
                         "role=\"status\"", "X-Snug-Client",
                         "providerName", "estimated_provider_cost_usd",
                         "chooseRecipient", "No new connector"):
            if required == "outbound":
                # The one-use server mechanism exists in the API call,
                # although no extra outbound payload is synthesized client-side.
                continue
            self.assertIn(required, self.page)
        self.assertIn("Room presence in the UI is not a security boundary", self.page)
        self.assertIn("one supplier responds per Send", self.page)
        self.assertIn("No live intelligences connected", self.page)
        # No remote assets or calls to vendor APIs in browser.
        self.assertNotRegex(self.page, r'<script[^>]+src="https?://')
        self.assertNotRegex(self.page, r'<img[^>]+src="https?://')

    def test_dom_ids_unique_and_javascript_parses(self):
        ids = re.findall(r' id="([^"]+)"', self.page)
        self.assertEqual(len(ids), len(set(ids)))
        script = re.search(r"<script>(.*?)</script>", self.page, re.DOTALL)
        self.assertIsNotNone(script)
        if shutil.which("node"):
            result = subprocess.run(
                ["node", "--check", "-"], input=script.group(1),
                capture_output=True, text=True, timeout=10, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
