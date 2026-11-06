"""Synthetic-only regression tests for the private, local OpenAI importer."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from cobble.openai_export import import_export, read_conversations


def conversation(cid, title, nodes=1, updated=1):
    mapping = {
        f"node-{i}": {
            "id": f"node-{i}",
            "parent": f"node-{i-1}" if i else None,
            "message": {"content": {"parts": [f"synthetic message {i}"]}},
        }
        for i in range(nodes)
    }
    return {"id": cid, "conversation_id": cid, "title": title,
            "create_time": 1, "update_time": updated,
            "current_node": f"node-{nodes-1}", "mapping": mapping,
            "context_scopes": [{"synthetic": "project-relation"}]}


def make_export(path, records, nested=False, extra_shards=None):
    inner = path.parent / ("inner-" + path.stem + ".zip")
    with ZipFile(inner, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("conversations-000.json", json.dumps(records))
        for name, contents in (extra_shards or {}).items():
            archive.writestr(name, json.dumps(contents))
        archive.writestr("file_0000000000.dat", b"not conversation content")
    if nested:
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as outer:
            outer.write(inner, "User Online Activity/Conversations__fake-chatgpt-0001.zip")
            outer.writestr("report.html", "synthetic")
    else:
        path.write_bytes(inner.read_bytes())
    inner.unlink()


class OpenAIExportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.store = self.root / "private-store"

    def archive(self, name, records, nested=False, extra_shards=None):
        path = self.root / name
        make_export(path, records, nested=nested, extra_shards=extra_shards)
        return path

    def version(self, cid):
        base = self.store / "openai" / "conversations" / cid
        pointer = json.loads((base / "latest.json").read_text())
        return json.loads((base / pointer["version"]).read_text()), base

    def test_nested_and_direct_exports_read_identically(self):
        records = [conversation("a", "one"), conversation("b", "two", 2)]
        direct = self.archive("direct.zip", records)
        nested = self.archive("outer.zip", records, nested=True)
        self.assertEqual(read_conversations(direct)[0], read_conversations(nested)[0])

    def test_incremental_import_keeps_raw_branches_and_old_versions(self):
        first = [
            conversation("a", "old name", 2),
            conversation("b", "unchanged", 1)
        ]
        updated = [
            conversation("a", "renamed", 5, updated=2),
            conversation("b", "unchanged", 1),
            conversation("c", "new", 3, updated=2),
        ]
        october = self.archive("october.zip", first)
        november = self.archive("november.zip", updated, nested=True)

        before = import_export(october, self.store)
        self.assertEqual((before["created"], before["revised"]), (2, 0))
        old_record, base = self.version("a")
        old_digest = json.loads((base / "latest.json").read_text())["sha256"]

        after = import_export(november, self.store)
        self.assertEqual((after["created"], after["revised"], after["unchanged"]),
                         (1, 1, 1))
        new_record, base = self.version("a")
        self.assertEqual(new_record, updated[0])  # all metadata + nodes retained
        self.assertEqual(len(new_record["mapping"]), 5)
        self.assertEqual(len(list((base / "versions").glob("*.json"))), 2)
        self.assertEqual(
            json.loads((base / "versions" / (old_digest + ".json")).read_text()),
            old_record)
        self.assertTrue((self.store / "openai" / "imports").is_dir())

        repeat = import_export(november, self.store)
        self.assertTrue(repeat["already_imported"])
        self.assertEqual(len(list((base / "versions").glob("*.json"))), 2)

    def test_dry_run_has_no_side_effects(self):
        archive = self.archive("only.zip", [conversation("a", "test")])
        result = import_export(archive, self.store, dry_run=True)
        self.assertEqual(result["created"], 1)
        self.assertFalse(self.store.exists())

    def test_duplicate_ids_are_rejected_without_writes(self):
        archive = self.archive("dup.zip", [conversation("a", "test")],
                               extra_shards={"conversations-001.json":
                                             [conversation("a", "duplicate")]})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            import_export(archive, self.store)
        self.assertFalse(self.store.exists())

    def test_malformed_shard_rejected_without_writes(self):
        archive = self.archive("bad.zip", [],
                               extra_shards={"conversations-001.json":
                                             {"not": "a conversation list"}})
        with self.assertRaisesRegex(ValueError, "Expected a list"):
            import_export(archive, self.store)
        self.assertFalse(self.store.exists())

    def test_unsafe_id_rejected(self):
        archive = self.archive("unsafe.zip", [conversation("../private", "bad")])
        with self.assertRaisesRegex(ValueError, "unsafe"):
            import_export(archive, self.store)
        self.assertFalse(self.store.exists())

    def test_new_snapshot_does_not_delete_absent_old_conversation(self):
        older = self.archive("older.zip", [conversation("a", "preserve")])
        newer = self.archive("newer.zip", [conversation("b", "different")])
        import_export(older, self.store)
        import_export(newer, self.store)
        self.assertTrue((self.store / "openai" / "conversations" / "a").exists())
        self.assertEqual(self.version("a")[0]["title"], "preserve")


if __name__ == "__main__":
    unittest.main()
