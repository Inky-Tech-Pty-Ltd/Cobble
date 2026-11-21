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
        for item in ("Senses", "Memories", "Intelligences", "Meetings", "Setup", "Help",
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
        self.assertIn('id="screen-senses"', self.page)
        self.assertIn('id="screen-memories"', self.page)
        self.assertIn('id="screen-help"', self.page)
        self.assertNotIn('id="screen-graph"', self.page)
        self.assertNotIn("More meetings and meeting titles are not yet implemented", self.page)
        self.assertNotIn("A room for conversations.", self.page)
        self.assertNotIn('class="supplier-lock"', self.page)
        self.assertNotIn("Use the padlock", self.page)

    def test_editable_browser_local_meeting_title_and_context_help(self):
        for value in ('id="meeting-title"', 'id="meeting-sidebar-title"',
                      "cobble.meeting.title", "'meeting-title').oninput",
                      "'meeting-title').onblur", "'meeting-title').onkeydown",
                      'id="context-help"', "HELP_DOC+'#'",
                      "#senses", "#memories", "#intelligences", "#meetings",
                      "#setup"):
            self.assertIn(value, self.page)
        self.assertIn('target="_blank"', self.page)
        self.assertIn('rel="noopener noreferrer"', self.page)

    def test_drop_to_stage_documents_without_reading_or_sending_bytes(self):
        for item in ('id="drop-cue"', 'id="tabled-files"',
                     'id="add-table-file"', 'id="table-file-input"',
                     'TABLE_FILES_LIMIT=8', "stageFiles(e.dataTransfer.files)",
                     "meetingDrop.ondrop=e=>", "drawTableFiles()",
                     "On table · names only · not shared",
                     "File bytes are never read"):
            self.assertIn(item, self.page)
        for forbidden in ("FileReader", "readAsDataURL(", "file.text(",
                          "file.arrayBuffer(", "new FormData("):
            self.assertNotIn(forbidden, self.page)
        self.assertIn("const preview=await api('live/preview',{question,provider:recipient})", self.page)

    def test_composer_grows_and_resets_after_send(self):
        for item in ("function resizeComposer()", "input.scrollHeight",
                     "window.addEventListener('resize',resizeComposer)",
                     "Math.floor(window.innerHeight*0.38)",
                     "$('question').oninput=()=>{resizeComposer();updateSend()}",
                     "$('question').value='';resizeComposer();"):
            self.assertIn(item, self.page)

    def test_operator_posts_without_live_supplier(self):
        for item in ("'post-only'", "None · post only", "'live/post'",
                     "{text:question}", "result.turn.status!=='posted'",
                     "if(t.status==='posted'&&t.provider==='operator')continue",
                     "serverReady=true", "await reload();",
                     "Posted locally · no supplier called."):
            self.assertIn(item, self.page)
        self.assertNotIn("serverReady=available.size>0", self.page)

    def test_live_call_contract_and_disclosure_are_retained(self):
        for required in ("'live/preview'", "'live/send'",
                         "{approval_token:preview.approval_token}",
                         "status==='outcome_unknown'", "status!=='completed'",
                         "no automatic retries", "No corpus passages supplied",
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
        self.assertIn("Each Send makes exactly one supplier call", self.page)
        self.assertNotIn("To the room · one supplier responds per Send</span>", self.page)
        self.assertNotIn("No live intelligences connected.", self.page)
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
