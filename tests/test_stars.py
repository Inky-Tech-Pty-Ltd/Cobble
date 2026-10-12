import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from cobble.stars import mint_star, trace_id
from villagelink.codec import make, parse


class StarTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.store = Path(temp.name)
        traces = self.store / "traces"
        traces.mkdir()
        self.members = [f"https://cobble.link/t/{uuid4()}" for _ in range(2)]
        for uri in self.members:
            (traces / f"{trace_id(uri)}.json").write_text(
                json.dumps({"uri": uri, "source_uri": "https://example.org"}),
                encoding="utf-8")

    def test_hypothesis_centre_and_village_link_rays(self):
        star = mint_star(self.store, "Memory is the masterpiece.", self.members)
        self.assertEqual(star["type"], "StarCredential")
        self.assertEqual(star["B"], sorted(self.members))
        centre = star["A"]
        ident = trace_id(centre)
        record = json.loads((self.store / "traces" / f"{ident}.json").read_text())
        self.assertEqual(record["kind"], "hypothesis")
        self.assertEqual(record["selector"]["exact"], "Memory is the masterpiece.")
        self.assertEqual(
            (self.store / "hypotheses" / f"{ident}.txt").read_text().strip(),
            "Memory is the masterpiece.")
        self.assertEqual(
            json.loads((self.store / "stars" / f"{ident}.json").read_text()), star)
        for member in star["B"]:
            uri = make(centre, member)
            name = hashlib.sha256(uri.encode()).hexdigest() + ".json"
            record = json.loads((self.store / "links" / name).read_text())
            self.assertEqual(record["uri"], uri)
            self.assertEqual(parse(uri), (centre, member))

    def test_missing_evidence_rejected_without_writes(self):
        missing = f"https://cobble.link/t/{uuid4()}"
        with self.assertRaisesRegex(ValueError, "Evidence trace missing"):
            mint_star(self.store, "Guess", [self.members[0], missing])
        self.assertFalse((self.store / "stars").exists())

    def test_duplicate_evidence_rejected(self):
        with self.assertRaises(ValueError):
            mint_star(self.store, "Guess", [self.members[0], self.members[0]])

    def test_invalid_evidence_uri_rejected(self):
        with self.assertRaises(ValueError):
            mint_star(self.store, "Guess", [self.members[0], "file:///etc/passwd"])
