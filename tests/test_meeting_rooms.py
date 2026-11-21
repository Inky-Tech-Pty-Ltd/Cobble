"""Meeting registry, durable history isolation and HTTP boundary regression."""
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

from cobble.claude_adapter import ProviderReply
from cobble.local_search import build
from cobble.meeting_rooms import MeetingCatalog
from cobble.snug_live import LiveChatService


class MeetingRoomTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.store = Path(tmp.name) / "private"
        self.store.mkdir(mode=0o700)

    def test_legacy_events_remain_and_new_rooms_have_separate_ledgers(self):
        legacy = LiveChatService(self.store, adapters={})
        old = legacy.post_operator(text="Old boardroom conversation")["turn"]
        cat = MeetingCatalog(self.store)
        self.assertEqual([room["id"] for room in cat.list()], ["default"])
        renamed = cat.rename(meeting_id="default", title="The first ever meeting!!")
        self.assertEqual(renamed["title"], "The first ever meeting!!")
        a = cat.create(title="New room A")
        b = cat.create(title="New room B")
        self.assertEqual(len(cat.list()), 3)
        aa = LiveChatService(self.store, adapters={}, meeting_id=a["id"])
        bb = LiveChatService(self.store, adapters={}, meeting_id=b["id"])
        aa.post_operator(text="Memory exclusive to A")
        bb.post_operator(text="Memory exclusive to B")
        self.assertEqual([t["question"] for t in aa.session()["turns"]],
                         ["Memory exclusive to A"])
        self.assertEqual([t["question"] for t in bb.session()["turns"]],
                         ["Memory exclusive to B"])
        self.assertEqual([t["turn_id"] for t in legacy.session()["turns"]],
                         [old["turn_id"]])
        self.assertEqual(LiveChatService(self.store, adapters={}).session()
                         ["turns"][0]["question"], "Old boardroom conversation")
        self.assertEqual(MeetingCatalog(self.store).list()[0]["title"],
                         "The first ever meeting!!")
        self.assertEqual(cat.rename(meeting_id=a["id"], title="Updated A")["title"],
                         "Updated A")
        self.assertEqual((self.store / "snug/live/rooms" / a["id"] /
                          "room.json").stat().st_mode & 0o777, 0o600)

    def test_validation_refuses_traversal_and_unregistered_rooms(self):
        catalog = MeetingCatalog(self.store)
        for bad_id in ("../default", "something", "../..", "", None):
            with self.assertRaises((ValueError, TypeError)):
                LiveChatService(self.store, adapters={}, meeting_id=bad_id)
            with self.assertRaises((ValueError, TypeError)):
                catalog.require(bad_id)
        with self.assertRaises(ValueError):
            catalog.require("a" * 16)
        for bad_title in ("", " ", "a" * 101, "abc\n", None):
            with self.assertRaises(ValueError):
                catalog.create(title=bad_title)
        with self.assertRaises(ValueError):
            catalog.rename(meeting_id="a" * 16, title="Unknown")
        self.assertEqual(catalog.list()[0]["title"], "Current meeting")

    def test_http_routes_keep_room_context_and_approval_separate(self):
        class Supplier:
            name = "openai"
            def __init__(self):
                self.calls = []
            def answer(self, request):
                self.calls.append(request)
                return ProviderReply(
                    text="Reply " + str(len(self.calls)), model="mock",
                    request_id="mock-request",
                    usage={"kind": "mock-openai-api", "network_calls": 0,
                           "input_tokens": 1, "output_tokens": 1,
                           "estimated_provider_cost_usd": "0.00001",
                           "cost_is_estimate": True})

        folder = self.store / "hosting" / "inkytech"
        folder.mkdir(parents=True)
        (folder / "note.txt").write_text("Harmless", encoding="utf-8")
        index = self.store / "index/search.sqlite3"
        build(self.store, index)
        script = Path(__file__).resolve().parents[1] / "scripts/snug_demo_web.py"
        spec = importlib.util.spec_from_file_location("snug_demo_web_rooms", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        supplier = Supplier()
        with module.create_server(self.store, index, port=0, live_gpt=True,
                                  live_adapter=supplier) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_port

            def call(route, payload=None):
                headers = {"Content-Type": "application/json",
                           "Origin": f"http://127.0.0.1:{port}",
                           "X-Snug-Client": "demo-local"}
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                conn.request("POST" if payload is not None else "GET",
                             route, json.dumps(payload) if payload is not None else None,
                             headers=headers)
                response = conn.getresponse()
                code, raw = response.status, response.read()
                conn.close()
                return code, json.loads(raw)

            try:
                self.assertEqual(call("/api/live/rooms")[1]["rooms"][0]["id"], "default")
                self.assertEqual(call("/api/live/post", {"text": "Old room"})[0], 200)
                code, a = call("/api/live/rooms/create", {"title": "Room A"})
                self.assertEqual(code, 200)
                code, b = call("/api/live/rooms/create", {"title": "Room B"})
                self.assertEqual(code, 200)
                self.assertNotEqual(a["id"], b["id"])
                self.assertEqual(call("/api/live/post", {
                    "text": "Room A secret", "room_id": a["id"]})[0], 200)
                self.assertEqual(call("/api/live/post", {
                    "text": "Room B secret", "room_id": b["id"]})[0], 200)
                old = call("/api/live/session")[1]["turns"]
                aa = call("/api/live/session?room_id=" + a["id"])[1]["turns"]
                bb = call("/api/live/session?room_id=" + b["id"])[1]["turns"]
                self.assertEqual([t["question"] for t in old], ["Old room"])
                self.assertEqual([t["question"] for t in aa], ["Room A secret"])
                self.assertEqual([t["question"] for t in bb], ["Room B secret"])
                code, preview = call("/api/live/preview", {
                    "question": "Examine Room A", "provider": "openai",
                    "room_id": a["id"]})
                self.assertEqual(code, 200)
                self.assertEqual(
                    [t["question"] for t in preview["previous_exchanges"]],
                    ["Room A secret"])
                token = preview["approval_token"]
                self.assertEqual(call("/api/live/send", {
                    "approval_token": token, "room_id": b["id"]})[0], 400)
                self.assertEqual(len(supplier.calls), 0)
                self.assertEqual(call("/api/live/send", {
                    "approval_token": token, "room_id": a["id"]})[0], 200)
                self.assertEqual(len(supplier.calls), 1)
                self.assertEqual(supplier.calls[0].previous_exchanges[0]["question"],
                                 "Room A secret")
                self.assertEqual(len(call("/api/live/session")[1]["turns"]), 1)
                self.assertEqual(len(call("/api/live/session?room_id=" + b["id"])
                                     [1]["turns"]), 1)
                self.assertEqual(call("/api/live/rooms/rename", {
                    "room_id": b["id"], "title": "Room B renamed"})[0], 200)
                self.assertEqual(call("/api/live/rooms")[1]["rooms"][1]["title"],
                                 "Room B renamed")
                self.assertEqual(call("/api/live/session?room_id=../default")[0], 400)
                self.assertEqual(call("/api/live/post", {
                    "text": "No", "room_id": "f" * 16})[0], 400)
            finally:
                server.shutdown()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
