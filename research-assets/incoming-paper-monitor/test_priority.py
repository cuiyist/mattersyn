"""Evidence priority and stale-source gates use isolated temporary ledgers only."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

import monitor as m
import test_batch as fixtures


class PriorityTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.BatchTests()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.report = self.f.root / "corpus-screening.json"
        self.report.write_text('{"scope":"fixture source screening; no scientific audit"}', encoding="utf-8")

    def policy(self, scores=None):
        ledger = m.read_ledger(self.f.path)
        scores = scores if scores is not None else [(key, index) for index, key in enumerate(self.f.order)]
        return {"mode": "evidence_richness", "source_report": str(self.report.resolve()),
                "source_report_sha256": hashlib.sha256(self.report.read_bytes()).hexdigest(),
                "screened_at": "2026-09-19T12:00:00+00:00", "require_screened": True,
                "rankings": [{"group_id": key, "score": score,
                              "source_generation": ledger["groups"][key]["generation"]}
                             for key, score in scores]}

    def apply(self, policy=None):
        return m.set_priority(self.f.path, policy if policy is not None else self.policy(), self.f.now)

    def test_default_arrival_order_is_unchanged_until_explicit_activation(self):
        ledger = m.read_ledger(self.f.path)
        self.assertNotIn("selection_policy", ledger)
        self.assertEqual(m.queued(ledger), self.f.order)
        self.assertEqual(m.summary(ledger, self.f.now)["next_eligible_group"], self.f.order[0])
        state = m.priority_state(ledger, self.f.order[0])
        self.assertEqual(state["status"], "arrival_order")
        self.assertTrue(state["eligible_for_selection"])
        self.assertFalse(state["screened"])

    def test_scores_descending_ties_use_unchanged_arrival_order_and_statuses(self):
        before = m.read_ledger(self.f.path)
        first, second, third, fourth = self.f.order[:4]
        self.apply(self.policy([(third, 20), (second, 20), (first, -5), (fourth, 0)]))
        ledger = m.read_ledger(self.f.path)
        self.assertEqual(ledger["groups"], before["groups"])
        self.assertEqual(ledger["files"], before["files"])
        self.assertEqual(m.queued(ledger), [second, third, fourth, first] + self.f.order[4:])
        summary = m.summary(ledger, self.f.now)
        self.assertEqual(summary["next_eligible_group"], second)
        self.assertEqual(summary["priority_pending_unscreened_scopes"], 3)
        self.assertEqual(summary["priority_status_counts"], {"screened": 4, "pending_unranked": 3})
        batch = self.f.claim()
        self.assertEqual([x["group_id"] for x in batch["papers"]], [second, third, fourth, first])
        self.assertEqual(len(batch["papers"]), 4)
        # A low/negative score is retained and never becomes a scientific skip.
        self.assertEqual(m.read_ledger(self.f.path)["groups"][first]["review"]["status"], "in_progress")

    def test_new_and_generation_changed_groups_stay_queued_but_cannot_be_claimed(self):
        self.apply()
        stale = self.f.order[-1]
        (self.f.source / f"{stale}_si_1.pdf").write_bytes(b"late supporting information")
        (self.f.source / "10.1000_new.pdf").write_bytes(b"later new paper")
        m.scan(self.f.path, self.f.source, self.f.now + m.SECOND)
        m.scan(self.f.path, self.f.source, self.f.now + 62 * m.SECOND)
        ledger = m.read_ledger(self.f.path)
        self.assertTrue(m.eligible(ledger, stale, self.f.now + 62 * m.SECOND))
        self.assertFalse(m.claimable(ledger, stale, self.f.now + 62 * m.SECOND))
        self.assertEqual(m.priority_state(ledger, stale)["status"], "pending_source_changed")
        self.assertEqual(m.priority_state(ledger, "10.1000_new")["status"], "pending_unranked")
        self.assertIn(stale, m.queued(ledger))
        self.assertIn("10.1000_new", m.queued(ledger))
        self.assertEqual(m.summary(ledger, self.f.now)["priority_pending_unscreened_scopes"], 2)
        with self.assertRaisesRegex(RuntimeError, "current source screening"):
            m.claim(self.f.path, "root", stale, now=self.f.now + 62 * m.SECOND)
        batch = self.f.claim()
        self.assertNotIn(stale, [x["group_id"] for x in batch["papers"]])
        self.assertNotIn("10.1000_new", [x["group_id"] for x in batch["papers"]])

    def test_stale_policy_rejected_atomically_then_refreshed_generation_selects(self):
        policy = self.policy()
        stale = self.f.order[-1]
        (self.f.source / f"{stale}.pdf").write_bytes(b"replacement source changes generation")
        m.scan(self.f.path, self.f.source, self.f.now + m.SECOND)
        before = self.f.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "source_generation is stale"):
            self.apply(policy)
        self.assertEqual(self.f.path.read_bytes(), before)
        self.apply()  # Fixture simulates a newly issued screening at the new generation.
        m.scan(self.f.path, self.f.source, self.f.now + 62 * m.SECOND)
        self.assertEqual(m.priority_state(m.read_ledger(self.f.path), stale)["status"], "screened")
        self.assertEqual(self.f.claim()["papers"][0]["group_id"], stale)

    def test_fixed_batch_checkpoint_and_fingerprint_continue_when_policy_changes(self):
        batch = self.f.claim()
        key = self.f.order[0]
        m.fingerprint(self.f.path, "root", self.f.now, group_id=key)
        m.checkpoint(self.f.path, "root", data={"page": 2}, group_id=key, now=self.f.now)
        before = m.read_ledger(self.f.path)
        self.apply(self.policy([(self.f.order[-1], 99)]))
        after = m.read_ledger(self.f.path)
        for field in ("current_batch", "current_paper", "groups", "files"):
            self.assertEqual(after[field], before[field])
        self.assertEqual(m.priority_state(after, key)["status"], "pending_unranked")
        resumed = self.f.claim()
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["papers"], batch["papers"])
        m.fingerprint(self.f.path, "root", self.f.now, group_id=key)
        m.checkpoint(self.f.path, "root", data={"page": 3}, group_id=key, now=self.f.now)
        self.assertEqual(m.read_ledger(self.f.path)["groups"][key]["review"]["checkpoint"]["page"], 3)

    def test_existing_single_claim_can_resume_and_be_adopted_even_if_unranked(self):
        key = self.f.order[0]
        old = m.claim(self.f.path, "root", key, self.f.now)
        self.apply(self.policy([]))
        self.assertTrue(m.claim(self.f.path, "root", now=self.f.now)["resumed"])
        batch = self.f.claim()
        self.assertEqual(len(batch["papers"]), 1)
        self.assertEqual(batch["papers"][0]["claimed_at"], old["claimed_at"])

    def test_explicit_arrival_mode_restores_order_without_claim_changes(self):
        self.apply()
        batch = self.f.claim(size=2)
        before = m.read_ledger(self.f.path)
        self.apply({"mode": "arrival_order"})
        after = m.read_ledger(self.f.path)
        self.assertEqual(m.queued(after), self.f.order)
        self.assertEqual(after["groups"], before["groups"])
        self.assertEqual(after["current_batch"]["papers"], batch["papers"])
        self.assertEqual(m.summary(after, self.f.now)["priority_pending_unscreened_scopes"], 0)

    def test_orphan_and_unsupported_sources_are_preserved_for_scoped_review(self):
        orphan = "10.1000_orphan"
        (self.f.source / f"{orphan}_si_1.docx").write_bytes(b"unparsed supplemental document")
        m.scan(self.f.path, self.f.source, self.f.now + m.SECOND)
        m.scan(self.f.path, self.f.source, self.f.now + 62 * m.SECOND)
        self.apply(self.policy([(orphan, 200)]))
        ledger = m.read_ledger(self.f.path)
        self.assertIn(orphan, m.queued(ledger))
        self.assertFalse(m.claimable(ledger, orphan, self.f.now + 62 * m.SECOND))
        self.assertTrue(m.claimable(ledger, orphan, self.f.now + 62 * m.SECOND, require_main=False))
        result = m.claim(self.f.path, "root", orphan, now=self.f.now + 62 * m.SECOND, allow_incomplete_bundle=True)
        self.assertTrue(result["allow_incomplete_bundle"])

    def test_empty_rankings_block_new_claims_without_dropping_queue(self):
        self.apply(self.policy([]))
        ledger = m.read_ledger(self.f.path)
        self.assertEqual(m.queued(ledger), self.f.order)
        self.assertIsNone(m.summary(ledger, self.f.now)["next_eligible_group"])
        with self.assertRaisesRegex(RuntimeError, "current screening"):
            self.f.claim()
        self.assertEqual(len(m.read_ledger(self.f.path)["groups"]), 7)

    def test_invalid_policies_never_modify_saved_state(self):
        variants = [None, {}, {"mode": "bogus"}]
        for field, value in [("source_report", "relative.json"), ("source_report", str(self.f.root / "missing.json")),
                             ("source_report_sha256", "a" * 64), ("source_report_sha256", "bad"),
                             ("require_screened", False), ("require_screened", 1),
                             ("screened_at", "2026-09-19"), ("screened_at", None), ("rankings", {})]:
            p = self.policy(); p[field] = value; variants.append(p)
        for field, values in {"score": [float("nan"), float("inf"), float("-inf"), True, "10", 10**500],
                              "source_generation": [0, 2, True, "1"],
                              "group_id": ["unknown-group", None]}.items():
            for value in values:
                p = self.policy(); p["rankings"][0][field] = value; variants.append(p)
        p = self.policy(); p["rankings"].append(copy.deepcopy(p["rankings"][0])); variants.append(p)
        p = self.policy(); p["rankings"].append(None); variants.append(p)
        before = self.f.path.read_bytes()
        for value in variants:
            with self.subTest(policy=value):
                with self.assertRaises(ValueError):
                    m.set_priority(self.f.path, value, self.f.now)
                self.assertEqual(self.f.path.read_bytes(), before)

    def test_alias_ids_are_rejected_instead_of_redirecting_a_screening_generation(self):
        ledger = m.read_ledger(self.f.path)
        alias, target = self.f.order[-2:]
        ledger["group_aliases"][alias] = target
        ledger["groups"][alias]["alias_of"] = target
        m.save_ledger(self.f.path, ledger)
        before = self.f.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "nonalias canonical"):
            self.apply(self.policy([(alias, 5)]))
        self.assertEqual(self.f.path.read_bytes(), before)

    def test_policy_write_uses_exclusive_lock_and_atomic_save(self):
        before = self.f.path.read_bytes()
        with m.locked_ledger(self.f.path):
            with self.assertRaisesRegex(RuntimeError, "Queue lock exists"):
                self.apply()
        self.assertEqual(self.f.path.read_bytes(), before)
        self.apply()
        self.assertFalse(self.f.path.with_suffix(".json.lock").exists())
        self.assertEqual(list(self.f.path.parent.glob("ledger.json.*.tmp")), [])

    def test_cli_accepts_policy_file_and_rejects_modified_report_digest(self):
        data = self.f.root / "policy.json"
        data.write_text(json.dumps(self.policy()), encoding="utf-8")
        cmd = [sys.executable, str(Path(m.__file__)), "--ledger", str(self.f.path), "set-priority", "--data", str(data)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["selection_policy"]["mode"], "evidence_richness")
        before = self.f.path.read_bytes()
        self.report.write_text('{"changed":true}', encoding="utf-8")
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA256 does not match", result.stderr)
        self.assertEqual(self.f.path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
