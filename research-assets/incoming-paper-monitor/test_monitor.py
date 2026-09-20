import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("monitor", Path(__file__).with_name("monitor.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
S = m.SECOND


def item(group="10.1_old", role="main", birth=10*S, mtime=20*S, size=12):
    return {"group_id": group, "role": role, "size": size, "mtime_ns": mtime,
            "birthtime_ns": birth, "birthtime_basis": "windows_creation_time"}


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.path = self.root / "private" / "ledger.json"
        self.ledger = m.new_ledger(self.source, 1000*S)

    def tearDown(self):
        self.temp.cleanup()

    def stable(self, observed):
        m.scan_state(self.ledger, observed, 1000*S)
        m.scan_state(self.ledger, observed, 1061*S)
        m.save_ledger(self.path, self.ledger)

    def test_creation_order_and_later_arrivals_never_jump_backlog(self):
        observed = {"10.1_new.pdf": item("10.1_new", birth=20*S, mtime=1*S),
                    "10.1_old.pdf": item(birth=10*S, mtime=500*S)}
        self.stable(observed)
        self.assertEqual(m.queued(self.ledger), ["10.1_old", "10.1_new"])
        observed["10.1_late.pdf"] = item("10.1_late", birth=1*S, mtime=1*S)
        m.scan_state(self.ledger, observed, 1100*S)
        self.assertEqual(m.queued(self.ledger), ["10.1_old", "10.1_new", "10.1_late"])

    def test_stability_needs_two_observations_and_si_resets_group(self):
        observed = {"10.1_old.pdf": item()}
        m.scan_state(self.ledger, observed, 1000*S)
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1100*S))
        m.scan_state(self.ledger, observed, 1030*S)
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1030*S))
        # Passage of time alone does not replace an actual second stable observation.
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1200*S))
        m.scan_state(self.ledger, observed, 1060*S)
        self.assertTrue(m.eligible(self.ledger, "10.1_old", 1060*S))
        observed["10.1_old_si_1.docx"] = item(role="si", mtime=1050*S)
        m.scan_state(self.ledger, observed, 1061*S)
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1061*S))
        m.scan_state(self.ledger, observed, 1122*S)
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1122*S))
        m.scan_state(self.ledger, observed, 1171*S)
        self.assertTrue(m.eligible(self.ledger, "10.1_old", 1171*S))

    def test_later_scan_orders_its_newcomers_by_birth_after_fixed_backlog(self):
        observed = {"10.1_old.pdf": item(birth=100*S)}
        self.stable(observed)
        observed.update({"10.1_aaa.pdf": item("10.1_aaa", birth=20*S),
                         "10.1_zzz.pdf": item("10.1_zzz", birth=10*S)})
        m.scan_state(self.ledger, observed, 1100*S)
        self.assertEqual(m.queued(self.ledger), ["10.1_old", "10.1_zzz", "10.1_aaa"])

    def test_late_si_reopens_without_overwriting_completed_review(self):
        observed = {"10.1_old.pdf": item()}
        self.stable(observed)
        review = self.ledger["groups"]["10.1_old"]["review"]
        review.update(status="complete", checkpoint={"pages_read": [1, 2], "evidence": "notes.md"})
        observed["10.1_old_si_1.zip"] = item(role="si")
        m.scan_state(self.ledger, observed, 1200*S)
        group = self.ledger["groups"]["10.1_old"]
        self.assertTrue(group["needs_recheck"])
        self.assertEqual(group["review"]["status"], "complete")
        self.assertEqual(group["review"]["checkpoint"]["pages_read"], [1, 2])
        self.assertIn("10.1_old", m.queued(self.ledger))

    def test_manual_claim_resumes_and_rejects_second_reviewer(self):
        self.stable({"10.1_old.pdf": item()})
        first = m.claim(self.path, "root", now=1100*S)
        m.checkpoint(self.path, "root", data={"page": 4}, now=1110*S)
        second = m.claim(self.path, "root", now=1200*S)
        self.assertTrue(second["resumed"])
        self.assertEqual(first["claimed_at"], second["claimed_at"])
        self.assertEqual(m.read_ledger(self.path)["groups"]["10.1_old"]["review"]["checkpoint"], {"page": 4})
        with self.assertRaisesRegex(RuntimeError, "Single reviewer"):
            m.claim(self.path, "other", now=1200*S)

    def test_changed_file_resets_stability_and_invalidates_fingerprint(self):
        observed = {"10.1_old.pdf": item()}
        self.stable(observed)
        self.ledger["files"]["10.1_old.pdf"]["sha256"] = "old"
        observed["10.1_old.pdf"] = item(size=13)
        m.scan_state(self.ledger, observed, 1200*S)
        self.assertFalse(m.eligible(self.ledger, "10.1_old", 1200*S))
        self.assertNotIn("sha256", self.ledger["files"]["10.1_old.pdf"])
        self.assertTrue(self.ledger["groups"]["10.1_old"]["needs_recheck"])

    def test_full_fingerprint_duplicate_detection_and_completion(self):
        (self.source / "10.1_old.pdf").write_bytes(b"%PDF-same-content")
        (self.source / "10.1_duplicate.pdf").write_bytes(b"%PDF-same-content")
        observed = m.inventory(self.source)
        now = max(x["birthtime_ns"] for x in observed.values()) + 121*S
        m.scan_state(self.ledger, observed, now)
        m.scan_state(self.ledger, observed, now+61*S)
        m.save_ledger(self.path, self.ledger)
        m.claim(self.path, "root", "10.1_old", now+61*S)
        first = m.fingerprint(self.path, "root", now+61*S)
        self.assertEqual(first["main_sha256"], [hashlib.sha256(b"%PDF-same-content").hexdigest()])
        self.assertEqual(first["duplicates"], [])
        m.checkpoint(self.path, "root", "complete", {"scientific_review": "manually performed"}, now=now+62*S)
        m.claim(self.path, "root", "10.1_duplicate", now+63*S)
        second = m.fingerprint(self.path, "root", now+63*S)
        self.assertEqual(second["duplicates"], [{"group_id": "10.1_old", "same_bundle": True, "same_main": True}])

    def test_hash_refuses_change_since_scan_and_never_completes_automatically(self):
        file = self.source / "10.1_old.pdf"
        file.write_bytes(b"before")
        observed = m.inventory(self.source)
        now = next(iter(observed.values()))["birthtime_ns"] + 121*S
        m.scan_state(self.ledger, observed, now)
        m.scan_state(self.ledger, observed, now+61*S)
        m.save_ledger(self.path, self.ledger)
        m.claim(self.path, "root", now=now+61*S)
        file.write_bytes(b"changed after scan")
        with self.assertRaisesRegex(RuntimeError, "changed since scan"):
            m.fingerprint(self.path, "root", now+61*S)
        self.assertEqual(m.read_ledger(self.path)["groups"]["10.1_old"]["review"]["status"], "in_progress")

    def test_source_inventory_excludes_logs_tests_and_tracks_unsupported(self):
        (self.source / "_test_out").mkdir()
        (self.source / "_test_out" / "10.1_test.pdf").write_bytes(b"PDF")
        for name in ["_log.jsonl", "_years.json", "10.1_a.pdf", "10.1_a_si_1.docx", "10.1_a_si_2.unusual", "10.1023_a"]:
            (self.source / name).write_bytes(b"content")
        observed = m.inventory(self.source)
        self.assertEqual(len(observed), 4)
        self.assertEqual(observed["10.1_a_si_2.unusual"]["role"], "si")
        self.assertEqual(observed["10.1_a_si_1.docx"]["group_id"], "10.1_a")
        self.assertEqual(observed["10.1023_a"]["role"], "unsupported")

    def test_lock_prevents_concurrent_mutation(self):
        self.path.parent.mkdir()
        self.path.with_suffix(".json.lock").write_text('{"pid": 123}')
        with self.assertRaisesRegex(RuntimeError, "Queue lock exists"):
            m.scan(self.path, self.source)
        self.assertFalse(self.path.exists())

    def test_checkpoint_requires_current_generation_fingerprint(self):
        self.stable({"10.1_old.pdf": item()})
        m.claim(self.path, "root", now=1100*S)
        with self.assertRaisesRegex(RuntimeError, "current file generation"):
            m.checkpoint(self.path, "root", "complete", now=1100*S)
        self.assertIsNotNone(m.read_ledger(self.path)["current_paper"])


if __name__ == "__main__":
    unittest.main()
