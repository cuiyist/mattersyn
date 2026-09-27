"""Synthetic contract tests, not scientific audit results."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import monitor as m


def window():
    return {"schema": m.VERSION + "/window", "window_id": "pilot-01", "pipeline_id": "local-pipeline-1",
            "pipeline_sha256": "a" * 64, "baseline_calibration_sha256": "b" * 64,
            "seed": "1" * 64, "registered_at": "2026-09-26T12:00:00Z",
            "start": "2026-09-27T00:00:00Z", "end_exclusive": "2026-10-04T00:00:00Z",
            "sampling_fraction": .05, "thresholds": m.BANDS.copy(),
            "scope": "first_verified_silver_release_per_primary_source",
            "cells": [{"band": "high", "field": "reaction_temperature"}, {"band": "high", "field": "duration"}]}


def release(source, day="2026-09-27", count=1, suffix="", tier="silver"):
    claims = [{"claim_id": f"{field}-{i}", "band": "high", "field": field, "tier": tier,
               "state": "accepted_auto_checked", "claim_sha256": m.digest([source, field, i])}
              for field in ("reaction_temperature", "duration") for i in range(count)]
    base = {"package_id": "package-" + source + suffix, "primary_source_id": source, "source_identity_verified": True,
            "commit": "c" * 40, "manifest_sha256": m.digest(claims), "pipeline_id": "local-pipeline-1",
            "pipeline_sha256": "a" * 64, "tier": tier}
    deployed = dict(base, event_id="deployed-" + source + suffix, stage="deployed", at=day + "T09:00:00Z")
    verified = dict(base, event_id="verified-" + source + suffix, stage="live_verified", at=day + "T10:00:00Z",
                    published_claims=claims, verification={"anonymous": True, "passed": True, "receipt_sha256": "d" * 64})
    return [deployed, verified]


def ledger(n=40, count=1):
    return {"schema": m.VERSION + "/deployment-ledger", "complete_lifetime_history": True,
            "complete_through": "2026-10-04T00:00:00Z",
            "events": [event for i in range(n) for event in release(f"source-{i:03d}", count=count)]}


def sample(n=40, count=1, final=False):
    return m.plan(window(), ledger(n, count), "2026-10-04T00:00:00Z" if final else "2026-09-28T00:00:00Z")


def audits(plan):
    out = []
    for day in plan["days"]:
        for source in day["selected"]:
            for claim in source["claims"]:
                out.append({"schema": m.VERSION + "/audit-event", "event_id": f"audit-{len(out):05d}",
                            "at": "2026-09-28T12:00:00Z", "window_sha256": plan["window_sha256"], "tier": "silver",
                            "source_id": source["source_id"], "manifest_sha256": source["manifest_sha256"],
                            "claim_id": claim["claim_id"], "claim_sha256": claim["claim_sha256"], "judgment": "correct",
                            "independent_scientific_audit": True, "auditor_id": "reviewer", "extractor_ids": ["extractor"],
                            "truth_receipt_sha256": m.digest([source["source_id"], claim["claim_id"], "truth"])})
    return out


def metric(report, field="reaction_temperature"):
    return next(r for r in report["metrics"] if r["field"] == field)


class SamplingTests(unittest.TestCase):
    def test_seeded_five_percent_reorder_and_duplicate_source(self):
        data = ledger(40)
        original = m.plan(window(), data, "2026-09-28T00:00:00Z")
        data["events"] += copy.deepcopy(data["events"][:2])
        data["events"] += release("source-000", suffix="-si")
        data["events"].reverse()
        updated = m.plan(window(), data, "2026-09-28T00:00:00Z")
        self.assertEqual(original["days"], updated["days"])
        self.assertEqual(updated["days"][0]["sample_size"], 2)
        self.assertEqual(updated["days"][0]["deployed_distinct_silver_sources"], 40)

    def test_round_up_and_empty_cohorts(self):
        p = sample(50)
        self.assertEqual(p["days"][0]["sample_size"], 3)
        self.assertEqual(p["days"][0]["effective_sampling_fraction"], .06)
        self.assertEqual(sample(0)["days"][0]["selected"], [])

    def test_seed_changes_and_cherry_picking_rejected(self):
        data = ledger()
        prior = m.plan(window(), data, "2026-09-28T00:00:00Z")
        changed = window()
        changed["seed"] = "2" * 64
        with self.assertRaisesRegex(ValueError, "seed changed"):
            m.plan(changed, data, "2026-09-29T00:00:00Z", prior)
        selected = prior["days"][0]["selected"][0]["source_id"]
        data["events"] = [e for e in data["events"] if e["primary_source_id"] != selected]
        with self.assertRaisesRegex(ValueError, "ledger was changed"):
            m.plan(window(), data, "2026-09-29T00:00:00Z", prior)

    def test_tampered_selection_rejected(self):
        p = sample()
        chosen = {s["source_id"] for s in p["days"][0]["selected"]}
        p["days"][0]["selected"][0] = next(s for s in p["days"][0]["population"] if s["source_id"] not in chosen)
        with self.assertRaisesRegex(ValueError, "selection changed"):
            m.evaluate(p, [])

    def test_claim_omission_or_field_changes_cannot_rewrite_audit_denominator(self):
        for mutation in ("omit", "field", "published-manifest"):
            p = sample(20)
            chosen = p["days"][0]["selected"][0]["source_id"]
            source = next(s for s in p["days"][0]["population"] if s["source_id"] == chosen)
            if mutation == "omit":
                source["claims"].pop()
            elif mutation == "field":
                source["claims"][0]["field"] = "reaction_temperature"
            else:
                source["verification_event"]["published_claims"].pop()
            p["days"][0]["population_sha256"] = m.digest(p["days"][0]["population"])
            p["days"][0]["selected"] = [source]
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "differs from frozen"):
                m.evaluate(p, [])

    def test_complete_source_omission_cannot_rewrite_population(self):
        p = sample(40)
        day = p["days"][0]
        removed = day["selected"][0]["source_id"]
        day["population"] = [s for s in day["population"] if s["source_id"] != removed]
        day["population_sha256"] = m.digest(day["population"])
        day["deployed_distinct_silver_sources"] -= 1
        day["selected"] = day["population"][:2]
        with self.assertRaisesRegex(ValueError, "differs from frozen"):
            m.evaluate(p, [])

    def test_undeployed_unverified_candidate_and_gold_are_not_population(self):
        data = ledger(0)
        data["events"] += release("draft")[0:1]
        invalid = release("unverified")
        invalid[1]["verification"]["anonymous"] = False
        data["events"] += invalid
        data["events"] += release("gold-source", tier="gold")
        candidate = release("candidate")[1]
        candidate["stage"] = "candidate"
        data["events"].append(candidate)
        self.assertEqual(m.plan(window(), data, "2026-09-28T00:00:00Z")["days"][0]["sample_size"], 0)
        data["events"].append(release("orphan")[1])
        with self.assertRaisesRegex(ValueError, "matching deployment"):
            m.plan(window(), data, "2026-09-28T00:00:00Z")

    def test_prior_sources_and_later_si_do_not_count_again(self):
        data = ledger(1)
        data["events"] += release("prior", day="2026-09-25") + release("prior", suffix="-si")
        p = m.plan(window(), data, "2026-09-28T00:00:00Z")
        self.assertEqual(p["days"][0]["deployed_distinct_silver_sources"], 1)

    def test_append_only_second_day_is_cumulative(self):
        data = ledger(20)
        p = m.plan(window(), data, "2026-09-28T00:00:00Z")
        data["events"] += release("new-source", day="2026-09-28")
        p2 = m.plan(window(), data, "2026-09-29T00:00:00Z", p)
        self.assertEqual(p2["days"][0], p["days"][0])
        self.assertEqual(p2["days"][1]["sample_size"], 1)

    def test_no_window_registration_after_start(self):
        w = window()
        w["registered_at"] = w["start"]
        with self.assertRaises(ValueError):
            m.plan(w, ledger(), "2026-09-28T00:00:00Z")


class AuditTests(unittest.TestCase):
    def test_idempotent_events_and_claim_source_dedup(self):
        p = sample(20)
        events = audits(p)
        once = m.evaluate(p, events)
        again = m.evaluate(p, events + copy.deepcopy(events))
        self.assertEqual(once, again)
        repeat = copy.deepcopy(events[0])
        repeat["event_id"] = "another-receipt-same-claim"
        more = m.evaluate(p, events + [repeat])
        self.assertEqual(once["metrics"], more["metrics"])
        self.assertEqual(metric(more)["reviewed_known_instances"], 1)

    def test_conflicting_audit_and_audit_removal_rejected(self):
        p = sample(20)
        events = audits(p)
        prior = m.evaluate(p, events)
        with self.assertRaisesRegex(ValueError, "removed or changed"):
            m.evaluate(p, events[:1], prior)
        repeat = copy.deepcopy(events[0])
        repeat.update(event_id="changed-judgment", judgment="incorrect")
        with self.assertRaisesRegex(ValueError, "Conflicting audit"):
            m.evaluate(p, events + [repeat])

    def test_unknown_and_missing_truth_never_become_correct(self):
        p = sample(40, final=True)
        events = audits(p)
        events[0]["judgment"] = "unknown"
        report = m.evaluate(p, events[:-1])
        self.assertEqual(sum(r["unknown_truth_instances"] for r in report["metrics"]), 1)
        self.assertEqual(sum(r["missing_truth_instances"] for r in report["metrics"]), 1)
        self.assertEqual(sum(r["reviewed_known_instances"] for r in report["metrics"]), 2)
        self.assertEqual(report["status"], "SUSPEND_AFFECTED_FIELDS")

    def test_small_daily_sample_does_not_reprove_precision(self):
        p = sample(20)
        report = m.evaluate(p, audits(p))
        r = metric(report)
        self.assertAlmostEqual(r["nominal_instance_precision_lower95"], .05)
        self.assertEqual(r["status"], "MONITORING_ONLY")
        self.assertFalse(r["publication_suspended"])
        self.assertFalse(m.projection(report, p, audits(p))["new_admissions_authorized"])
        final = sample(20, final=True)
        stopped = metric(m.evaluate(final, audits(final)))
        self.assertTrue(stopped["publication_suspended"])
        self.assertIn("insufficient_cumulative_precision_evidence_at_window_end", stopped["stop_reasons"])

    def test_failed_field_suspended_masked_and_revocation_only_proposed(self):
        p = sample(20)
        events = audits(p)
        next(e for e in events if e["claim_id"].startswith("reaction_temperature"))["judgment"] = "incorrect"
        report = m.evaluate(p, events)
        self.assertTrue(metric(report)["publication_suspended"])
        self.assertFalse(metric(report, "duration")["publication_suspended"])
        public = m.projection(report, p, events)
        failed = metric(public)
        self.assertTrue(failed["training_masked"])
        self.assertEqual(failed["training_weight"], 0)
        self.assertEqual(failed["existing_publication_action"], "propose_versioned_revocation")
        self.assertFalse(public["publication_enabled"])
        self.assertFalse(public["scientific_values_modified"])

    def test_stops_remain_latched_when_later_successes_dilute_error(self):
        p = sample(20, count=100)
        events = audits(p)
        early = next(e for e in events if e["claim_id"].startswith("reaction_temperature"))
        early.update(judgment="incorrect", at="2026-09-27T12:00:00Z")
        report = m.evaluate(p, events)
        self.assertEqual(metric(report)["observed_error_rate"], .01)
        self.assertTrue(metric(report)["publication_suspended"])

    def test_error_threshold_equality_is_not_exceedance(self):
        p = sample(20, count=100)
        events = audits(p)
        temperature = [e for e in events if e["claim_id"].startswith("reaction_temperature")]
        for e in temperature[-2:]:
            e.update(judgment="incorrect", at="2026-09-28T13:00:00Z")
        report = m.evaluate(p, events)
        self.assertEqual(metric(report)["observed_error_rate"], .02)
        self.assertFalse(metric(report)["publication_suspended"])

    def test_gold_unknown_source_and_changed_version_rejected(self):
        p = sample(20)
        original = audits(p)
        for field, value in (("tier", "gold"), ("source_id", "not-sampled"), ("claim_sha256", "f" * 64),
                             ("auditor_id", "extractor"), ("manifest_sha256", "e" * 64)):
            events = copy.deepcopy(original)
            events[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                m.evaluate(p, events)

    def test_nominal_pass_still_requires_independent_review(self):
        p = sample(20, count=149, final=True)
        report = m.evaluate(p, audits(p))
        r = metric(report)
        self.assertGreaterEqual(r["nominal_instance_precision_lower95"], .98)
        self.assertAlmostEqual(r["nominal_source_cluster_lower95"], .05)
        self.assertEqual(r["status"], "INDEPENDENT_REVIEW_REQUIRED")
        self.assertFalse(m.projection(report, p, audits(p))["new_admissions_authorized"])

    def test_projection_recomputes_and_rejects_false_metrics_or_controls(self):
        p = sample(20, final=True)
        events = audits(p)
        baseline = m.evaluate(p, events)
        for mutation in ("flag", "fake-bound", "count"):
            report = copy.deepcopy(baseline)
            row = metric(report)
            if mutation == "flag":
                row["publication_suspended"] = False
            elif mutation == "fake-bound":
                row.update(nominal_instance_precision_lower95=.999, publication_suspended=False,
                           status="INDEPENDENT_REVIEW_REQUIRED", stop_reasons=[])
            else:
                row["reviewed_known_instances"] = 1000
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "recomputed audit"):
                m.projection(report, p, events)


class PrivacyTests(unittest.TestCase):
    def test_private_quotes_paths_and_people_never_projected(self):
        p = sample(20)
        events = audits(p)
        for event in events:
            event.update(quote="SECRET VERBATIM EVIDENCE", private_path="C:\\private\\source.pdf", private_notes="private reviewer prose")
        report = m.evaluate(p, events)
        report.update(quote="SECRET VERBATIM EVIDENCE", private_path="C:\\private\\source.pdf")
        encoded = json.dumps(m.projection(report, p, events))
        for private in ("SECRET", "C:\\", "private reviewer prose", "auditor_id", "truth_receipt", "source_id", "quote"):
            self.assertNotIn(private, encoded)

    def test_malicious_public_metadata_fails_closed(self):
        p = sample(20)
        report = m.evaluate(p, audits(p))
        report["metrics"][0]["status"] = "SECRET PRIVATE QUOTE"
        with self.assertRaises(ValueError):
            m.projection(report, p, audits(p))

    def test_existing_receipt_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            m.write_new(path, {"initial": True})
            with self.assertRaises(FileExistsError):
                m.write_new(path, {"initial": False})
            self.assertEqual(json.loads(path.read_text()), {"initial": True})


if __name__ == "__main__":
    unittest.main()
