"""Synthetic receipts exercise governance, identity, sampling and measurement gates."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("full_audit_plan", Path(__file__).parents[1] / "full_audit_plan.py")
w = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(w)


class Ledger:
    def __init__(self, seed="mattersyn-full-independent-20261002"):
        self.events = []; self.counter = 0
        self.add("cohort_started", sampling_seed=seed, owner_resume_receipt="owner-message-123",
                 baseline_live_source_ids=[])

    def at(self):
        self.counter += 1
        return (datetime(2026, 10, 2, tzinfo=timezone.utc) + timedelta(seconds=self.counter)).isoformat()

    def add(self, stage, source=None, **fields):
        e = dict(event_id="e" + str(len(self.events)), at=self.at(), cohort_id="c1", stage=stage, **fields)
        if source:
            e.update(primary_source_id=source, claim_id="claim-" + source)
        self.events.append(e)
        return e

    def claim(self, source="p1"):
        return self.add("claimed", source, extractor_id="extractor")

    def freeze(self, source="p1", h="a"):
        return self.add("extraction_frozen", source, extractor_id="extractor", package_sha256=h * 64,
                        scoped_pages={"main": [1, 2]}, record_ids=[source + ":1"])

    def audit(self, source="p1", kind="full", findings=None, accepted=True, h="a", flags=0):
        check = dict(tool="check_records.py", exit_code=0, at=self.at(), primary_source_id=source,
                     package_sha256=h * 64, report_sha256="b" * 64, record_count=1, flag_count=flags,
                     source_resolutions={})
        start = self.add(kind + "_audit_started", source, package_sha256=h * 64,
                         auditor_id="auditor" if kind == "full" else "third-agent", check_receipt=copy.deepcopy(check))
        check["source_resolutions"] = {str(n): {"disposition": "confirmed_source", "source_locator": "main p2",
                                              "note": "Confirmed reported rounded values against source."} for n in range(flags)}
        return self.add(kind + "_audit", source, package_sha256=h * 64,
                        auditor_id=start["auditor_id"], audit_started_event_id=start["event_id"],
                        source_pages_read={"main": [1, 2]}, check_receipt=check,
                        audit_receipt_sha256="c" * 64, findings=findings or [], accepted=accepted)

    def complete(self, source="p1", findings=None):
        self.claim(source); self.freeze(source); self.audit(source)
        if w.replay(self.events)["c1"]["papers"][source]["sample_required"]:
            self.audit(source, "deep", findings=findings)
        self.add("integrated", source, package_sha256="a" * 64, integration_receipt_sha256="d" * 64)

    def live(self, source="p1"):
        return self.add("live_verified", source, package_sha256="a" * 64,
                        site_commit="e" * 40, url="https://example.org/material",
                        verification={"anonymous": True, "passed": True, "receipt_sha256": "f" * 64})


def s2(fid="s2"):
    return [{"finding_id": fid, "severity": "S2", "error_type": "sample-condition-assignment",
             "resolution_status": "corrected_verified", "resolution_receipt": "source-correction-checked"}]


class SamplingTests(unittest.TestCase):
    def test_exact_ten_precommitted_across_ten_blocks(self):
        slots = w.first_forty_slots("mattersyn-full-independent-20261002")
        self.assertEqual(slots, [1, 5, 12, 13, 19, 22, 28, 31, 35, 38])
        self.assertEqual([int((n - 1) / 4) for n in slots], list(range(10)))

    def test_hash_revision_cannot_redraw_sample_or_ordinal(self):
        log = Ledger(); log.claim(); log.freeze()
        before = copy.deepcopy(w.replay(log.events)["c1"]["papers"]["p1"])
        log.freeze(h="f")
        after = w.replay(log.events)["c1"]["papers"]["p1"]
        self.assertEqual(before["ordinal"], after["ordinal"])
        self.assertEqual(before["sample_required"], after["sample_required"])

    def test_skips_and_holds_never_fill_first40(self):
        log = Ledger()
        for n in range(45):
            source = "s" + str(n); log.claim(source)
            log.add("skipped", source, reason="No preparation within checked scope", receipt_id="skip-source-receipt",
                    source_locator="main experimental section")
        status = w.first_forty(w.replay(log.events)["c1"])
        self.assertEqual(status["cohort_papers"], 0)
        self.assertFalse(status["report_ready"])

    def test_eligible_cannot_escape_sample_by_skip(self):
        log = Ledger(); log.claim(); log.freeze()
        log.add("skipped", "p1", reason="Changed mind", source_locator="p2", receipt_id="skip")
        with self.assertRaisesRegex(ValueError, "cannot escape"):
            w.replay(log.events)

    def test_first40_reduction_requires_all_integrated_and_samples(self):
        log = Ledger()
        for n in range(40):
            log.complete("p" + str(n), s2() if n == 0 else [])
        cohort = w.replay(log.events)["c1"]
        self.assertTrue(w.first_forty(cohort)["may_reduce_to_ten_percent"])
        log.add("reduce_sampling")
        self.assertEqual(w.replay(log.events)["c1"]["reduced_at_ordinal"], 41)

    def test_two_sample_errors_block_reduction_even_after_fixes(self):
        log = Ledger()
        for n in range(40):
            log.complete("p" + str(n), s2() if n in (0, 4) else [])
        cohort = w.replay(log.events)["c1"]
        self.assertEqual(w.first_forty(cohort)["deep_s1_s2_papers"], 2)
        log.add("reduce_sampling")
        with self.assertRaisesRegex(ValueError, "reduction gate"):
            w.replay(log.events)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.log = Ledger(); self.log.claim(); self.log.freeze()

    def test_flags_may_be_open_at_start_but_resolved_at_acceptance(self):
        self.log.audit(flags=2)
        self.assertTrue(w.replay(self.log.events)["c1"]["papers"]["p1"]["full_accepted"])
        self.log.events[-1]["check_receipt"]["source_resolutions"].pop("1")
        with self.assertRaisesRegex(ValueError, "unresolved checker"):
            w.replay(self.log.events)

    def test_self_audit_and_unread_source_pages_rejected(self):
        self.log.audit()
        self.log.events[-2]["auditor_id"] = "extractor "
        with self.assertRaisesRegex(ValueError, "differ from extractor"):
            w.replay(self.log.events)
        self.log.events[-2]["auditor_id"] = "auditor"
        self.log.events[-1]["source_pages_read"]["main"] = [2]
        with self.assertRaisesRegex(ValueError, "all scoped"):
            w.replay(self.log.events)

    def test_deep_auditor_must_be_third_and_run_checker_again(self):
        self.log.audit(); self.log.audit(kind="deep")
        self.log.events[-2]["auditor_id"] = "auditor"
        with self.assertRaisesRegex(ValueError, "third distinct"):
            w.replay(self.log.events)
        self.log.events[-2]["auditor_id"] = "third-agent"
        self.log.events[-2]["check_receipt"] = copy.deepcopy(self.log.events[-4]["check_receipt"])
        with self.assertRaisesRegex(ValueError, "before EACH audit"):
            w.replay(self.log.events)

    def test_stale_checker_and_checker_after_audit_start_rejected(self):
        self.log.audit()
        self.log.events[-2]["check_receipt"]["package_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "stale"):
            w.replay(self.log.events)
        self.log.events[-2]["check_receipt"]["package_sha256"] = "a" * 64
        self.log.events[-2]["check_receipt"]["at"] = self.log.events[-1]["at"]
        with self.assertRaisesRegex(ValueError, "BEFORE"):
            w.replay(self.log.events)

    def test_old_acceptance_cannot_cover_new_science(self):
        self.log.audit(); self.log.audit(kind="deep"); self.log.freeze(h="f")
        self.log.add("integrated", "p1", package_sha256="f" * 64, integration_receipt_sha256="d" * 64)
        with self.assertRaisesRegex(ValueError, "audit gates incomplete"):
            w.replay(self.log.events)

    def test_original_findings_survive_corrected_reaudits(self):
        self.log.audit(); self.log.audit(kind="deep", findings=s2(), accepted=False)
        self.log.freeze(h="f"); self.log.audit(h="f"); self.log.audit(kind="deep", h="f")
        p = w.replay(self.log.events)["c1"]["papers"]["p1"]
        self.assertTrue(p["deep_s1_s2_ever"])
        self.assertTrue(p["deep_accepted"])
        self.assertEqual(len(p["findings"]), 1)

    def test_duplicate_claim_rejected_and_exact_event_retry_idempotent(self):
        self.log.events.append(copy.deepcopy(self.log.events[-1]))
        self.assertEqual(len(w.replay(self.log.events)["c1"]["papers"]), 1)
        self.log.claim()
        with self.assertRaisesRegex(ValueError, "already claimed"):
            w.replay(self.log.events)

    def test_unresolved_severe_findings_cannot_be_accepted(self):
        bad = s2(); bad[0].pop("resolution_status")
        self.log.audit(findings=bad)
        with self.assertRaisesRegex(ValueError, "unresolved S1/S2"):
            w.replay(self.log.events)

    def test_other_scientific_authors_cannot_audit(self):
        self.log.events[1]["scientific_author_ids"] = ["extractor", "auditor"]
        self.log.audit()
        with self.assertRaisesRegex(ValueError, "every scientific author"):
            w.replay(self.log.events)

    def test_revisions_cannot_remove_scientific_author_history(self):
        self.log.events[1]["scientific_author_ids"] = ["extractor", "prior-scientific-editor"]
        self.log.events[-1]["scientific_author_ids"] = ["extractor"]
        with self.assertRaisesRegex(ValueError, "authors cannot be removed"):
            w.replay(self.log.events)


class CarriedInTests(unittest.TestCase):
    def make_carried(self):
        log = Ledger()
        claim = log.claim()
        prior = {"receipt_sha256": "1" * 64, "package_sha256": "a" * 64,
                 "frozen_at": "2026-10-01T23:58:00Z", "check_at": "2026-10-01T23:59:00Z",
                 "check_report_sha256": "b" * 64, "audit_started_at": "2026-10-01T23:59:30Z",
                 "auditor_id": "auditor"}
        claim["carried_in"] = prior
        freeze = log.freeze(); freeze["recorded_at"] = freeze["at"]; freeze["at"] = prior["frozen_at"]
        log.audit()
        started, completed = log.events[-2:]
        started["recorded_at"] = started["at"]; started["at"] = prior["audit_started_at"]
        started["check_receipt"]["at"] = completed["check_receipt"]["at"] = prior["check_at"]
        return log

    def test_real_pre_admission_checker_and_dispatch_do_not_need_repeating(self):
        log = self.make_carried()
        paper = w.replay(log.events)["c1"]["papers"]["p1"]
        self.assertTrue(paper["full_accepted"])
        self.assertEqual(paper["frozen_at"], "2026-10-01T23:58:00Z")
        result = w.report(log.events, "c1", "2026-10-02T00:00:01Z", "2026-10-02T01:00:01Z")
        self.assertEqual(result["distinct_papers_by_stage"]["extraction_frozen"], 0)
        self.assertEqual(result["distinct_papers_by_stage"]["full_audit_accepted"], 1)
        self.assertEqual(result["carried_in_primary_source_ids"], ["p1"])

    def test_unreceipted_earlier_event_or_changed_actual_time_rejected(self):
        log = self.make_carried(); log.events[1].pop("carried_in")
        with self.assertRaisesRegex(ValueError, "explicit carried-in"):
            w.replay(log.events)
        log = self.make_carried(); log.events[2]["at"] = "2026-10-01T23:57:00Z"
        with self.assertRaisesRegex(ValueError, "original time and package"):
            w.replay(log.events)

    def test_checker_or_auditor_dispatch_cannot_be_substituted(self):
        log = self.make_carried(); log.events[-2]["check_receipt"]["report_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "original checker"):
            w.replay(log.events)
        log = self.make_carried(); log.events[-2]["auditor_id"] = "someone-else"
        with self.assertRaisesRegex(ValueError, "original checker"):
            w.replay(log.events)

    def test_published_baseline_cannot_enter_first40(self):
        log = Ledger(); log.events[0]["baseline_live_source_ids"] = ["p1"]
        log.claim(); log.freeze()
        with self.assertRaisesRegex(ValueError, "separate reassessment"):
            w.replay(log.events)


class GatesAndMetricsTests(unittest.TestCase):
    def test_stop_counts_distinct_papers_and_retains_historical_cohorts(self):
        log = Ledger(); log.claim(); log.freeze(); c = w.replay(log.events)["c1"]
        c["papers"] = {str(i): {"primary_source_id": str(i), "deep_completed_at": f"2026-10-02T01:{i:02d}:00Z",
                               "deep_s1_s2_ever": i < 6, "pair_step": 4} for i in range(50)}
        self.assertTrue(w.stopped(c))
        c["papers"]["50"] = {"primary_source_id": "50", "deep_completed_at": "2026-10-02T02:00:00Z",
                              "deep_s1_s2_ever": False, "pair_step": 4}
        self.assertFalse(w.stopped(c))  # Oldest positive leaves last 50.
        log.add("cohort_started", cohort_id_unused="none", sampling_seed="new", owner_resume_receipt="new-owner")
        with self.assertRaisesRegex(ValueError, "cannot be restarted"):
            w.replay(log.events)
        log.events[-1]["cohort_id"] = "c2"
        self.assertEqual(set(w.replay(log.events)), {"c1", "c2"})

    def test_ramp_respects_measured_capacity_backlog_and_four_agent_limit(self):
        c = {"pair_step": 4, "collisions": {}, "papers": {
            str(i): {"primary_source_id": str(i), "deep_completed_at": f"2026-10-02T01:{i:02d}:00Z",
                     "deep_s1_s2_ever": False, "pair_step": 4} for i in range(10)}}
        capacity = {"observed_at": "2026-10-02T02:00:00Z", "runtime_worker_limit": 4,
                    "active_workers": 1, "machine_spare_capacity": True, "measurement_receipt": "observed-cpu-ram"}
        gate = w.ramp_gate(c, 8, capacity, 0, {"qd": 100, "metal": 20}, "2026-10-02T02:01:00Z")
        self.assertFalse(gate["allowed"])
        self.assertTrue(any("runtime worker quota" in r for r in gate["reasons"]))
        capacity["runtime_worker_limit"] = 99
        gate = w.ramp_gate(c, 8, capacity, 3, {"qd": 100, "metal": 20}, "2026-10-02T02:01:00Z")
        self.assertTrue(any("measurements" in r for r in gate["reasons"]))
        self.assertTrue(any("backlog" in r for r in gate["reasons"]))

    def test_only_first_anonymous_live_paper_counts_no_revisions_or_skips(self):
        log = Ledger(); log.complete(); log.live(); log.live()
        log.claim("skip"); log.add("skipped", "skip", reason="no preparation", receipt_id="s", source_locator="main methods")
        result = w.report(log.events, "c1", "2026-10-02T00:00:01Z", "2026-10-02T02:00:01Z")
        self.assertEqual(result["papers_per_elapsed_hour"], 0.5)
        self.assertEqual(result["new_live_papers"], ["p1"])
        self.assertEqual(result["distinct_papers_by_stage"]["skipped"], 1)
        result = w.report(log.events, "c1", log.events[-1]["at"], "2026-10-02T02:00:01Z")
        self.assertEqual(result["new_live_papers"], [])

    def test_integration_or_unsigned_publication_is_not_live_credit(self):
        log = Ledger(); log.complete()
        result = w.report(log.events, "c1", "2026-10-02T00:00:01Z", "2026-10-02T02:00:01Z")
        self.assertEqual(result["new_live_papers"], [])
        log.live()["verification"]["anonymous"] = False
        with self.assertRaisesRegex(ValueError, "anonymous"):
            w.replay(log.events)

    def test_later_rejected_audit_cannot_reuse_old_integration_credit(self):
        log = Ledger(); log.complete(); log.audit(accepted=False); log.live()
        with self.assertRaisesRegex(ValueError, "rejected science"):
            w.replay(log.events)

    def test_read_only_report_does_not_include_future_completion(self):
        log = Ledger(); log.claim(); freeze = log.freeze(); log.audit()
        result = w.report(log.events, "c1", "2026-10-02T00:00:01Z", freeze["at"])
        self.assertEqual(result["first40"]["cohort_papers"], 0)


class CheckReceiptTests(unittest.TestCase):
    def test_real_report_binding_and_failed_process(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "package.json"; r = Path(root) / "check.json"
            p.write_text(json.dumps({"source": {"primary_source_id": "p"}, "records": [{"record_id": "r"}]}))
            r.write_text(json.dumps({"summary": {"records": 1, "by_paper": {"p": {"records": 1}}}, "flags": [{}]}))
            receipt = w.check_receipt(p, r, 0, "2026-10-02T00:01:00Z")
            self.assertEqual(receipt["source_resolutions"], {})
            self.assertEqual(receipt["flag_count"], 1)
            with self.assertRaisesRegex(ValueError, "did not complete"):
                w.check_receipt(p, r, 1, "2026-10-02T00:01:00Z")


if __name__ == "__main__":
    unittest.main()
