import json, tempfile, unittest
from pathlib import Path
from uuid import uuid4
from cobble.observations import record_observation, observations_for, validate_observation, SCHEMA_VERSION
from cobble.stars import trace_id

class ObservationContractTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.store=Path(t.name)
        (self.store/"traces").mkdir()
        self.uri=f"https://cobble.link/t/{uuid4()}"
        (self.store/"traces"/f"{trace_id(self.uri)}.json").write_text(json.dumps({"uri":self.uri}),encoding="utf-8")

    def test_not_checked_is_distinct_from_unavailable(self):
        r=record_observation(self.store,self.uri,"not_checked",observed_at="2026-10-14T00:00:00Z")
        self.assertIsNone(r["retrieved_at"])
        self.assertEqual(r["retrieval"]["status"],"not_checked")

    def test_unknown_is_not_success(self):
        r=record_observation(self.store,self.uri,"unknown",observed_at="2026-10-14T00:00:00Z")
        self.assertFalse(r["semantics"]["authoritative"])
        self.assertFalse(r["semantics"]["truth_assessed"])

    def test_attempt_records_distinct_retrieval_time(self):
        r=record_observation(self.store,self.uri,"available",
          observed_at="2026-10-14T00:05:00Z",retrieved_at="2026-10-14T00:04:00Z")
        self.assertNotEqual(r["observed_at"],r["retrieved_at"])

    def test_source_event_time_is_optional_and_not_inferred(self):
        r=record_observation(self.store,self.uri,"moved",observed_at="2026-10-14T00:05:00Z")
        self.assertIsNone(r["source_event_at"])

    def test_integrity_is_separate_from_availability(self):
        r=record_observation(self.store,self.uri,"available",observed_at="2026-10-14T00:00:00Z",
          integrity_status="differs_from_recorded_digest")
        self.assertEqual(r["retrieval"]["status"],"available")
        self.assertEqual(r["integrity"]["status"],"differs_from_recorded_digest")

    def test_not_checked_cannot_claim_retrieval_time(self):
        with self.assertRaises(ValueError):
            record_observation(self.store,self.uri,"not_checked",observed_at="2026-10-14T00:00:00Z",
                               retrieved_at="2026-10-14T00:00:00Z")

    def test_tampered_semantics_fail_validation(self):
        r=record_observation(self.store,self.uri,"available",observed_at="2026-10-14T00:00:00Z")
        r["semantics"]["authoritative"]=True
        with self.assertRaises(ValueError): validate_observation(r)

    def test_history_validates_schema_version(self):
        record_observation(self.store,self.uri,"available",observed_at="2026-10-14T00:00:00Z")
        records=observations_for(self.store,self.uri)
        self.assertEqual(records[0]["schema_version"],SCHEMA_VERSION)

if __name__=="__main__": unittest.main()
