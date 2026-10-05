"""Receipted continuation preserves an incomplete version without inventing a second audit."""
import copy
from datetime import timedelta
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("baseline_tests", Path(__file__).with_name("test_full_audit_plan.py"))
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
w = base.w


def fixture(complete=False):
    log = base.Ledger(); log.claim(); log.freeze()
    log.audit(findings=base.s2("original-s2"), accepted=False)
    log.freeze(h="b")
    old_check = dict(tool="check_records.py", exit_code=0, at=log.at(), primary_source_id="p1",
                     package_sha256="b"*64, report_sha256="1"*64, record_count=1,
                     flag_count=1, source_resolutions={})
    start = log.add("full_audit_started", "p1", package_sha256="b"*64,
                    auditor_id="auditor", check_receipt=old_check)
    frozen = log.freeze(h="c")
    state = w.replay(log.events)["c1"]["papers"]["p1"]
    check = dict(old_check, at=log.at(), package_sha256="c"*64, report_sha256="2"*64)
    event = log.add("full_audit_continued", "p1", package_sha256="c"*64,
        auditor_id="auditor", audit_started_event_id=start["event_id"],
        superseded_package_sha256="b"*64, superseded_active_audit_sha256=w.digest(state["active_audit"]),
        successor_freeze_event_id=frozen["event_id"], prior_findings_sha256=w.digest(state["findings"]),
        superseded_audit_completed=False, exact_supersession_at=None,
        timing_qualification="Observed corrected-package review; exact retirement instant was not recorded.",
        continuation_receipt_sha256="3"*64, supersession_receipt_sha256="4"*64,
        check_receipt=check)
    event["supersession_acknowledged_at"] = log.at(); event["recorded_at"] = log.at()
    if complete:
        resolved = copy.deepcopy(check)
        resolved["source_resolutions"]={"0":{"disposition":"confirmed_source","source_locator":"main p2","note":"Source checked."}}
        log.add("full_audit", "p1", package_sha256="c"*64, auditor_id="auditor",
                audit_started_event_id=start["event_id"], check_receipt=resolved,
                source_pages_read={"main":[1,2]}, audit_receipt_sha256="5"*64,
                findings=[], accepted=True)
    return log, event, start, frozen


class ContinuationTests(unittest.TestCase):
    def test_same_start_preserves_original_findings_and_version_checks(self):
        log,e,start,frozen=fixture(True); original=copy.deepcopy(log.events)
        p=w.replay(log.events)["c1"]["papers"]["p1"]
        self.assertTrue(p["full_accepted"]); self.assertTrue(p["full_s1_s2_ever"])
        self.assertEqual([f["finding_id"] for f in p["findings"]],["original-s2"])
        h=p["full_audit_continuations"][0]
        self.assertEqual(h["superseded_active_audit"]["event_id"],start["event_id"])
        self.assertEqual(h["superseded_active_audit"]["at"],start["at"])
        self.assertEqual(h["superseded_active_audit"]["check_receipt"],start["check_receipt"])
        self.assertEqual(h["successor_freeze"],frozen); self.assertIsNone(h["event"]["exact_supersession_at"])
        self.assertEqual(log.events,original)

    def test_observation_does_not_grant_acceptance_integration_or_third_credit(self):
        log,e,start,frozen=fixture();p=w.replay(log.events)["c1"]["papers"]["p1"]
        self.assertEqual(p["active_audit"]["event_id"],start["event_id"])
        self.assertEqual(p["active_audit"]["at"],start["at"])
        self.assertEqual(p["active_audit"]["check_before_at"],e["at"])
        self.assertFalse(p["full_accepted"]);self.assertFalse(p["deep_accepted"])
        self.assertFalse(p["integrated"]);self.assertNotIn("deep_completed_at",p)
        log.add("integrated","p1",package_sha256="c"*64,integration_receipt_sha256="6"*64)
        with self.assertRaisesRegex(ValueError,"audit gates incomplete"):w.replay(log.events)

    def test_corrected_completion_then_distinct_third_uses_normal_gate(self):
        log,*_=fixture(True);log.audit(kind="deep",h="c")
        p=w.replay(log.events)["c1"]["papers"]["p1"]
        self.assertTrue(p["deep_accepted"]);self.assertFalse(p["deep_s1_s2_ever"])
        self.assertTrue(p["full_s1_s2_ever"]);self.assertEqual(len(w.sample_results(w.replay(log.events)["c1"])),1)

    def test_continuation_does_not_allow_second_scientific_start(self):
        log,*_=fixture();log.add("full_audit_started","p1",package_sha256="c"*64,auditor_id="auditor",check_receipt={})
        with self.assertRaisesRegex(ValueError,"already has an active audit"):w.replay(log.events)

    def reject(self, mutate, pattern):
        log,e,start,frozen=fixture();mutate(log,e,start,frozen)
        with self.assertRaisesRegex(ValueError,pattern):w.replay(log.events)

    def test_different_auditor_rejected(self):self.reject(lambda l,e,s,f:e.update(auditor_id="other"),"same independent")
    def test_scientific_author_cannot_continue(self):self.reject(lambda l,e,s,f:f.update(scientific_author_ids=["extractor","auditor"]),"same independent")
    def test_missing_predecessor_start_rejected(self):self.reject(lambda l,e,s,f:e.pop("audit_started_event_id"),"original active")
    def test_missing_superseded_package_rejected(self):self.reject(lambda l,e,s,f:e.pop("superseded_package_sha256"),"exact superseded")
    def test_changed_predecessor_snapshot_rejected(self):self.reject(lambda l,e,s,f:e.update(superseded_active_audit_sha256="e"*64),"exact superseded")
    def test_unknown_freeze_rejected(self):self.reject(lambda l,e,s,f:e.update(successor_freeze_event_id="missing"),"latest exact")
    def test_skipping_real_successor_freeze_rejected(self):self.reject(lambda l,e,s,f:l.events.remove(f),"already-frozen")
    def test_wrong_successor_rejected(self):self.reject(lambda l,e,s,f:e.update(package_sha256="d"*64),"already-frozen")
    def test_original_findings_erasure_rejected(self):self.reject(lambda l,e,s,f:e.update(prior_findings_sha256=w.digest([])),"cannot erase")
    def test_result_injected_at_continuation_rejected(self):
        for field,value in [("findings",[]),("accepted",True),("full_accepted",True),("deep_accepted",False)]:
            with self.subTest(field=field):self.reject(lambda l,e,s,f:e.update({field:value}),"cannot erase")
    def test_fabricated_old_completion_rejected(self):self.reject(lambda l,e,s,f:e.update(superseded_audit_completed=True),"incomplete superseded")
    def test_invented_retirement_instant_rejected(self):self.reject(lambda l,e,s,f:e.update(exact_supersession_at=e["at"]),"uncaptured transition")
    def test_acknowledgment_backdating_rejected(self):self.reject(lambda l,e,s,f:e.update(supersession_acknowledged_at=s["at"]),"chronology")
    def test_acknowledgment_after_recording_rejected(self):self.reject(lambda l,e,s,f:e.update(supersession_acknowledged_at="2027-01-01T00:00:00Z"),"chronology")
    def test_missing_evidence_rejected(self):self.reject(lambda l,e,s,f:e.pop("supersession_receipt_sha256"),"SHA-256")
    def test_stale_checker_rejected(self):self.reject(lambda l,e,s,f:e.update(check_receipt=copy.deepcopy(s["check_receipt"])),"stale")
    def test_failed_checker_rejected(self):self.reject(lambda l,e,s,f:e["check_receipt"].update(exit_code=1),"successful check")
    def test_check_before_freeze_rejected(self):self.reject(lambda l,e,s,f:e["check_receipt"].update(at=s["at"]),"after freeze")
    def test_check_after_observed_review_rejected(self):self.reject(lambda l,e,s,f:e["check_receipt"].update(at=e["at"]),"BEFORE")
    def test_incomplete_checker_coverage_rejected(self):self.reject(lambda l,e,s,f:e["check_receipt"].update(record_count=0),"count mismatch")
    def test_unresolved_flags_at_completion_rejected(self):
        log,*_=fixture(True);log.events[-1]["check_receipt"]["source_resolutions"]={}
        with self.assertRaisesRegex(ValueError,"unresolved checker"):w.replay(log.events)
    def test_completed_successor_cannot_precede_observed_comparison(self):
        log,e,*_=fixture(True);log.events[-1]["recorded_at"]=log.events[-1]["at"];log.events[-1]["at"]=e["check_receipt"]["at"]
        with self.assertRaisesRegex(ValueError,"completion precedes"):w.replay(log.events)
    def test_completion_still_requires_all_source_pages(self):
        log,*_=fixture(True);log.events[-1]["source_pages_read"]={"main":[1]}
        with self.assertRaisesRegex(ValueError,"all scoped"):w.replay(log.events)
    def test_late_acknowledgment_does_not_fake_retirement_or_break_historical_report(self):
        log,e,*_=fixture(True);completion=log.events[-1]
        e["supersession_acknowledged_at"]=log.at();e["recorded_at"]=log.at();completion["recorded_at"]=e["recorded_at"]
        cutoff=(w.stamp(completion["at"])+timedelta(microseconds=1)).isoformat()
        report=w.report(log.events,"c1",log.events[0]["at"],cutoff)
        self.assertEqual(report["distinct_papers_by_stage"]["full_audit_accepted"],1)
        self.assertEqual(w.replay(log.events)["c1"]["papers"]["p1"]["full_audit_continuations"][0]["event"]["exact_supersession_at"],None)

if __name__=="__main__":unittest.main()
