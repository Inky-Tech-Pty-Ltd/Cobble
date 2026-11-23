"""Candidate 2: durable room-state and editorial authority regression checks."""
import tempfile
import unittest
from pathlib import Path
from cobble.meeting_rooms import MeetingCatalog, DEFAULT_ORDERS


class RoomVoiceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.catalog = MeetingCatalog(Path(temp.name) / "private")
        self.room = self.catalog.create(title="Test meeting")

    def test_new_room_starts_with_orders_and_precedence(self):
        room = self.room
        self.assertEqual(room["state"], "open")
        self.assertIn("convenor", room["standing_orders"])
        self.assertEqual(room["precedence"], ["openai", "claude", "mistral"])
        self.assertEqual(room["room_voice"], [])

    def test_redaction_preserves_ledger_reference_and_can_be_restored(self):
        ident = "20261123142345678901-abcdef123456"
        room = self.catalog.configure(meeting_id=self.room["id"], voice_event=ident)
        self.assertEqual(room["room_voice"], [ident])
        room = self.catalog.configure(meeting_id=self.room["id"], redact_event=ident)
        self.assertIn(ident, room["room_voice"])
        self.assertIn(ident, room["redacted"])
        room = self.catalog.configure(meeting_id=self.room["id"], voice_event=ident)
        self.assertNotIn(ident, room["redacted"])
        self.assertEqual(self.catalog.list()[1]["room_voice"], [ident])

    def test_lifecycle_and_precedence_are_persistent(self):
        reverse = ["mistral", "claude", "openai"]
        self.catalog.configure(meeting_id=self.room["id"], precedence=reverse, state="closed")
        again = MeetingCatalog(self.catalog.store)
        stored = next(room for room in again.list() if room["id"] == self.room["id"])
        self.assertEqual(stored["state"], "closed")
        self.assertEqual(stored["precedence"], reverse)
        again.configure(meeting_id=self.room["id"], state="adjourned")
        self.assertEqual(again.list()[1]["state"], "adjourned")

    def test_invalid_edits_rejected(self):
        with self.assertRaises(ValueError):
            self.catalog.configure(meeting_id=self.room["id"], precedence=["openai"])
        with self.assertRaises(ValueError):
            self.catalog.configure(meeting_id=self.room["id"], state="deleted")
        with self.assertRaises(ValueError):
            self.catalog.configure(meeting_id=self.room["id"], redact_event="not-published")
        self.assertTrue(DEFAULT_ORDERS)


if __name__ == "__main__":
    unittest.main()
