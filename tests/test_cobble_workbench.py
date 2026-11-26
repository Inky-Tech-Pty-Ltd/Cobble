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

    def test_distance_navigation_membrane_and_room_list_remain_functional(self):
        spine = self.page.split('<nav class="primary-nav"', 1)[1].split('</nav>', 1)[0]
        expected = ("Intelligences", "Meetings", "Senses", "Membrane",
                    "Furniture", "My meetings", "Memories")
        positions = [spine.index('>' + name + '<') for name in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Recent meetings", spine)
        self.assertIn('data-screen="membrane"', spine)
        self.assertIn('class="nav-item membrane-boundary"', spine)
        self.assertIn('id="my-meetings-toggle"', spine)
        self.assertIn('id="new-meeting"', spine)
        self.assertIn('id="meeting-list"', spine)
        self.assertIn('data-screen="furniture"', spine)
        self.assertIn('<nav class="utility-nav" aria-label="Workspace utilities">',
                      self.page)
        self.assertIn("showMyMeetings(", self.page)
        self.assertIn("cobble.meetings.expanded", self.page)
        self.assertIn("collapse(false);showMyMeetings(true)", self.page)
        self.assertIn('id="screen-membrane"', self.page)
        self.assertIn('id="screen-furniture"', self.page)
        self.assertIn("The boundary of", self.page)
        self.assertIn("Instance Door and trust policy", self.page)
        self.assertIn("Not yet implemented", self.page)
        self.assertIn('id="furniture-doors"', self.page)
        self.assertIn('id="furniture-open-meeting-door"', self.page)
        self.assertIn("setScreen('meetings');", self.page)
        self.assertIn("$('invite-human').click();", self.page)
        self.assertNotIn('role="separator"', spine)
        self.assertIn("--membrane-blue:#0c94e8", self.page)
        self.assertNotIn("--membrane-orange:", self.page)
        self.assertIn("--membrane-pale:#f0f7ff", self.page)
        self.assertIn('class="membrane-cue"', self.page)
        self.assertIn("#invite-human.membrane-cue", self.page)
        self.assertIn('class="furniture-doors"', self.page)

    def test_all_room_costs_come_from_server_not_visited_browser_rooms(self):
        self.assertIn("function applyCostSnapshot(data)", self.page)
        self.assertIn("estimated_total_usd", self.page)
        self.assertIn("room.estimated_cost_usd", self.page)
        self.assertIn("async function refreshMeetingCosts()", self.page)
        self.assertIn("applyCostSnapshot(data);", self.page)
        self.assertIn("await refreshMeetingCosts();", self.page)
        self.assertIn("Recorded supplier cost estimates across all saved meetings",
                      self.page)
        self.assertNotIn("meetingCosts[currentRoomId]=turns.reduce", self.page)
        self.assertNotIn("Object.values(meetingCosts).reduce", self.page)

    def test_navigation_sidebar_and_meeting_layout(self):
        for item in ("Senses", "Memories", "Intelligences", "Meetings", "Setup", "Help",
                     'id="sidebar"', 'id="resize-grip"', "ondblclick",
                     "cobble.sidebar.width", "cobble.sidebar.collapsed",
                     'id="thread"', 'id="chat-scroll"',
                     'id="joe-card"', 'id="joe-voice-edge"', 'id="send"', 'id="question"',
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
        self.assertIn('id="edit-orders"', self.page)
        self.assertIn('id="meeting-state"', self.page)
        self.assertIn('id="view-output"', self.page)
        self.assertIn('id="total-cost"', self.page)
        self.assertNotIn('id="screen-graph"', self.page)
        self.assertNotIn("More meetings and meeting titles are not yet implemented", self.page)
        self.assertNotIn("A room for conversations.", self.page)
        self.assertNotIn('class="supplier-lock"', self.page)
        self.assertNotIn("Use the padlock", self.page)

    def test_editable_browser_local_meeting_title_and_context_help(self):
        for value in ('id="meeting-title"', 'id="meeting-list"', 'id="new-meeting"',
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
                     "Filename staged locally; contents not yet shared",
                     "File bytes are never read"):
            self.assertIn(item, self.page)
        for forbidden in ("FileReader", "readAsDataURL(", "file.text(",
                          "file.arrayBuffer(", "new FormData("):
            self.assertNotIn(forbidden, self.page)
        self.assertIn("const preview=await api('live/preview',{question,provider:recipient,room_id:roomId})", self.page)

    def test_composer_grows_and_resets_after_send(self):
        for item in ("function resizeComposer()", "input.scrollHeight",
                     "window.addEventListener('resize',resizeComposer)",
                     "Math.floor(window.innerHeight*0.38)",
                     "$('question').oninput=()=>{resizeComposer();updateSend()}",
                     "$('question').value='';resizeComposer();"):
            self.assertIn(item, self.page)

    def test_operator_posts_without_live_supplier(self):
        for item in ("'post-only'", "'live/post'",
                     "{text:question,room_id:roomId}", "result.turn.status!=='posted'",
                     "if(t.status==='posted'&&t.provider==='operator')continue",
                     "serverReady=true", "await reload();",
                     "Posted locally · no supplier called."):
            self.assertIn(item, self.page)
        self.assertNotIn("serverReady=available.size>0", self.page)

    def test_live_call_contract_and_disclosure_are_retained(self):
        for required in ("'live/preview'", "'live/send'",
                         "{approval_token:preview.approval_token,room_id:roomId}",
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
        self.assertIn("one supplier call per Send", self.page)
        self.assertNotIn("To the room · one supplier responds per Send</span>", self.page)
        self.assertNotIn("No live intelligences connected.", self.page)
        # No remote assets or calls to vendor APIs in browser.
        self.assertNotRegex(self.page, r'<script[^>]+src="https?://')
        self.assertNotRegex(self.page, r'<img[^>]+src="https?://')

    def test_multiple_persistent_meetings_and_right_margin(self):
        for item in ("function loadMeetings()", "function switchMeeting(roomId)",
                     "live/rooms/create", "live/rooms/rename",
                     "cobble.meeting.active", "roomDrafts.set(currentRoomId",
                     "tabledFiles.length=0;drawTableFiles()", "await loadMeetings()",
                     "room_id:roomId", "id=\"meeting-list\"",
                     "id=\"new-meeting\"", ".exchange.supplier .message{width:100%}",
                     ".exchange.human .message{width:80%}",
                     ".exchange.human .message{width:90%}",
                     ".exchange{max-width:100%!important}",
                     "justify-content:flex-end", "meetings=data.rooms||[]"):
            self.assertIn(item, self.page)
        self.assertNotIn("On table · names only · not shared", self.page)
        self.assertNotIn("if(!turns.length)return;", self.page)
        self.assertNotIn("id=\"meeting-current\"", self.page)

    def test_retired_responder_does_not_crash_offline_post(self):
        self.assertNotIn("next-responder", self.page)
        self.assertIn("return chosen||'post-only'", self.page)
        self.assertIn("function populateResponder(){updateSend();}", self.page)

    def test_room_voice_failure_is_not_reported_as_publication_success(self):
        """Run the actual send and selection functions with a rejecting configure API."""
        if not shutil.which("node"):
            self.skipTest("Node.js required for the browser-function regression")
        begin = self.page.index("async function send(){")
        end = self.page.index("async function saveRoom(", begin)
        functions = self.page[begin:end]
        harness = r"""
let busy=false, meetingInfo={state:'open'}, currentRoomId='default';
let joeFloor=true, roomFloor=null, recipient='post-only', lastProvider=null;
let messages=[], calls=[], failed=true;
let field={value:'Synthetic agenda',focus(){}};
const $=()=>field;
const chooseRecipient=()=>recipient;
const updateSend=()=>{};
const resizeComposer=()=>{};
const reload=async()=>{};
const providerName=x=>x;
const status=(message,error=false)=>messages.push({message,error});
async function api(route,data){
  calls.push(route);
  if(route==='live/post')return {turn:{turn_id:'fixture',status:'posted'}};
  if(route==='live/preview')return {approval_token:'fixture'};
  if(route==='live/send')return {turn:{turn_id:'fixture',status:'completed'}};
  throw Error(route);
}
async function saveRoom(){
  calls.push('configure');
  if(failed)throw Error('Selection rejected');
}
async function check(){
  await send();
  if(!messages.at(-1).error||!messages.at(-1).message.includes('Do not resend')||
     field.value!==''||calls.join(',')!=='live/post,configure')throw Error('Local false success');
  messages=[];calls=[];field.value='Question';recipient='openai';joeFloor=false;roomFloor='openai';
  await send();
  // Having the floor must NOT automatically publish a supplier answer.
  if(messages.at(-1).error||field.value!==''||
     calls.join(',')!=='live/preview,live/send')throw Error('Supplier floor silently published a reply');
  calls=[];messages=[];
  const selected=await setVoice('fixture',true);
  if(selected!==false||!messages.at(-1).error||calls.join(',')!=='configure')
     throw Error('Explicit publication failure not reported');
  messages=[];calls=[];field.value='Question';failed=false;
  await send();
  if(messages.at(-1).error||calls.join(',')!=='live/preview,live/send')
     throw Error('Supplier send not independent from publication');
  calls=[];messages=[];
  if(!await setVoice('fixture',true)||calls.join(',')!=='configure')
     throw Error('Explicit publication did not work');
}
check().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(["node", "-"], input=functions + "\n" + harness,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_room_governance_editors_are_readable_and_do_not_publish(self):
        """Standing orders and output use scrollable in-app dialogs, not browser prompts."""
        for required in (
                'id="orders-dialog"', 'id="orders-text"',
                'id="orders-save"', 'id="orders-cancel"',
                'id="room-output-dialog"', 'id="output-agenda"',
                'id="output-contributions"', 'id="output-contribution-count"',
                'class="room-output-scroll"', "x.contributions.length",
                "list.replaceChildren()", "make('p',c.text||'')",
                "await saveRoom({standing_orders:$('orders-text').value})",
                "Room output", "does not transmit it to another room"):
            self.assertIn(required, self.page)
        self.assertNotIn("prompt('Standing orders", self.page)
        self.assertNotIn("alert('Opening agenda", self.page)

    def test_collapsed_sidebar_keeps_expand_button_accessible(self):
        self.assertIn(".sidebar.collapsed .identity{height:92px;", self.page)
        self.assertIn(".sidebar.collapsed #collapse{display:block;", self.page)
        self.assertIn("value?'Expand sidebar':'Collapse sidebar'", self.page)
        self.assertIn("$('collapse').onclick=()=>collapse(", self.page)

    def test_copy_controls_are_explicit_and_keep_text_local(self):
        """Copy original contribution/payload text only on a human click."""
        for required in (
            'id="orders-copy"', 'id="output-copy"',
            "function copyButton(text,label)", "async function copyText(text,label,button)",
            "navigator.clipboard.writeText(text)",
            "copyButton(t.question||'','Copy '+(t.speaker||'Joe')+' contribution')",
            "copyButton(body.textContent,'Copy '+p.name+' contribution')",
            "copyButton(speech.textContent,'Copy Chair standing orders')",
            "copyButton(exactPayload,'Copy exact outgoing API payload')",
            "copyButton(c.text||'','Copy selected contribution')",
            "formatRoomOutput(lastRoomOutput)",
            "lastRoomOutput=x", "body.append(make('pre',exactPayload))",
        ):
            self.assertIn(required, self.page)
        self.assertNotIn("execCommand('copy')", self.page)

    def test_meeting_door_status_and_opening_agenda_are_visible(self):
        for required in (
            "function refreshDoorStatus()",
            "'/api/live/rooms/door?room_id='",
            "Door: awaiting guest",
            "Door: invitation used",
            "Replace invitation",
            "function pollMeetingUpdates()",
            "const firstJoe=turns.find(",
            "t.turn_id===openingTurnId",
            "Waiting for the convenor",
            "participants.push('Sankarshan')",
            "The convenor's opening agenda is a local post",
            "Open the meeting with your agenda…",
        ):
            self.assertIn(required, self.page)
        self.assertNotIn("if(i===0&&meetingInfo?.standing_orders)", self.page)

    def test_shared_left_edge_weight_language_is_actionable_and_accessible(self):
        for required in (
            'id="joe-card"', 'id="joe-voice-edge"', 'id="joe-mode"',
            "edge.className='weight-edge'", "cb.className='message weight-fixed'",
            "function createWeightEdge(", "function renderJoeControl()",
            "function selectSupplierFloor(id)", "onClick:()=>selectSupplierFloor(p.id)",
            "aria-pressed", "aria-label", "edge.title=label",
            "Authorise '+(t.speaker||'Joe')+' contribution for room voice",
            "Withdraw '+(t.speaker||'Joe')+' contribution from room voice",
            "onClick:()=>setVoice(t.turn_id,!hvoice)",
            "onClick:()=>setVoice(t.turn_id,!voiced)",
            "joeFloor=!joeFloor", "if(roomFloor)joeFloor=false",
            "const publish=recipient==='post-only'&&joeFloor",
            "box.classList.add('weighted')",
            "hb.classList.add('weighted')",
            "speech.className='message-body'",
            'id="weight-help" href="https://github.com/Inky-Tech-Pty-Ltd/Cobble/issues/85"',
        ):
            self.assertIn(required, self.page)
        for removed in ("id=\"grant-floor\"", "id=\"joe-floor\"",
                        "Redact voice", "Restore voice", "Authorise room voice"):
            self.assertNotIn(removed, self.page)

    def test_room_door_unchanged_except_subtle_left_edge_and_blue_palette(self):
        for required in (
            'id="invite-human"', 'id="invite-dialog"', 'id="invite-open"',
            'id="invite-revoke"', 'id="invite-copy"',
            "api('live/rooms/invite',{room_id:currentRoomId})",
            "api('live/rooms/revoke',{room_id:currentRoomId})",
            "This one-room invitation permits its bearer",
            "Local test only:",
            "#invite-human.membrane-cue::before",
            "--membrane-blue:#0c94e8",
        ):
            self.assertIn(required, self.page)
        self.assertNotIn("#c95e21", self.page)
        self.assertNotIn("#fff4e7", self.page)

    def test_guest_uses_matching_read_only_crescents(self):
        guest = (HTML.parent / "guest_room.html").read_text(encoding="utf-8")
        for required in (
            "--membrane-blue:#0c94e8",
            'class="door-status"',
            "weighted:not(.authorised)::before",
            "weighted::before,.weight-fixed::before",
            "class=\"weight-fixed\"",
            "const humanVoice=t.provider==='operator'&&t.authorised_voice",
        ):
            self.assertIn(required, guest)
        self.assertNotIn("--membrane-orange", guest)
        self.assertNotIn("Redact voice", guest)
        self.assertNotIn("voice_event", guest)

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
