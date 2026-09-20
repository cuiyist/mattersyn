"""Batch reservation and source-generation tests use isolated temporary ledgers."""
import concurrent.futures
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest

import monitor as m


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "papers"
        self.source.mkdir()
        self.path = self.root / "private" / "ledger.json"
        for index in range(7):
            (self.source / f"10.1000_p{index}.pdf").write_bytes(f"main paper {index}".encode())
        self.now = time.time_ns() + 240 * m.SECOND
        m.scan(self.path, self.source, self.now)
        m.scan(self.path, self.source, self.now + 61 * m.SECOND)
        self.now += 61 * m.SECOND
        ledger = m.read_ledger(self.path)
        # Exercise schema 2 without importing any real corpus or live state.
        ledger.update(schema_version=2, source_paths={"incoming": str(self.source)}, group_aliases={})
        for name, item in ledger["files"].items():
            item.update(source_id="incoming", relative_filename=name, origin_group_id=item["group_id"],
                        doi_candidates=[m.filename_doi(item["group_id"])])
        m.save_ledger(self.path, ledger)
        self.order = m.queued(ledger)
        self.evidence = self.path.parent / "evidence.json"
        self.evidence.write_text('{"fixture": "isolated scientific evidence reference"}')

    def tearDown(self):
        self.temp.cleanup()

    def claim(self, size=5, reviewer="root"):
        return m.claim_batch(self.path, reviewer, size=size, now=self.now)

    def stages(self):
        return {stage: {"status": "complete", "evidence": [str(self.evidence)]} for stage in m.MILESTONES}

    def complete(self, key):
        m.fingerprint(self.path, "root", self.now, group_id=key)
        return m.checkpoint(self.path, "root", "complete", data={"reviewed_source": key},
                            milestones=self.stages(), group_id=key, now=self.now)

    def screening(self, key):
        generation = m.read_ledger(self.path)["groups"][key]["generation"]
        return {"screening": {"outcome": "no_synthesis_recipe", "source_generation": generation,
                "scope": "Supplied main and all matched local SI; missing future SI is outside this scope.",
                "reason": "Inspected methods and experimental sections describe measurements only.",
                "evidence": [str(self.evidence)], "reviewer": "primary-screener",
                "independent_audit": {"status": "passed", "reviewer": "independent-auditor",
                                      "evidence": [str(self.evidence)]}}}

    def screening_stages(self):
        stages = self.stages()
        for stage in ("read", "extract", "integrate", "publish"):
            stages[stage].update(status="not_applicable", note="Scoped screening found no recipe; full curation is not applicable.")
        return stages

    def test_claims_five_oldest_saved_scopes_and_keeps_independent_checkpoints(self):
        batch = self.claim()
        self.assertEqual([claim["group_id"] for claim in batch["papers"]], self.order[:5])
        for key in self.order[:5]:
            m.checkpoint(self.path, "root", data={"source": key}, group_id=key, now=self.now)
        ledger = m.read_ledger(self.path)
        self.assertEqual(ledger["schema_version"], 2)
        self.assertEqual(m.summary(ledger)["active_review_claims"], 5)
        self.assertEqual(m.summary(ledger)["waiting_review_scopes"], 2)
        self.assertTrue(all(ledger["groups"][key]["review"]["checkpoint"] == {"source": key} for key in self.order[:5]))

    def test_resume_never_replenishes_until_every_original_member_closes(self):
        first = self.claim()
        result = self.complete(self.order[2])
        self.assertFalse(result["claim_retained"])
        self.assertTrue(result["batch_retained"])
        (self.source / "10.1000_new.pdf").write_bytes(b"later arrival")
        m.scan(self.path, self.source, self.now + 1)
        resumed = self.claim(size=3)
        self.assertTrue(resumed["resumed"])
        self.assertEqual(resumed["batch_id"], first["batch_id"])
        self.assertEqual(resumed["papers"], first["papers"])
        self.assertEqual(resumed["active_review_claims"], 4)
        for key in self.order[:5]:
            if key != self.order[2]:
                self.complete(key)
        ledger = m.read_ledger(self.path)
        self.assertIsNone(ledger["current_batch"])
        self.assertIsNone(ledger["current_paper"])
        self.assertEqual(ledger["batch_history"][0]["papers"], first["papers"])
        following = self.claim()
        self.assertNotEqual(following["batch_id"], first["batch_id"])
        self.assertEqual([claim["group_id"] for claim in following["papers"]], self.order[5:])

    def test_requires_explicit_owned_member_and_failed_actions_do_not_write(self):
        self.claim()
        before = self.path.read_bytes()
        actions = [lambda: m.fingerprint(self.path, "root", self.now),
                   lambda: m.checkpoint(self.path, "root", data={"bad": True}),
                   lambda: m.fingerprint(self.path, "other", self.now, group_id=self.order[0]),
                   lambda: m.checkpoint(self.path, "root", data={"bad": True}, group_id=self.order[5]),
                   lambda: self.claim(reviewer="other"),
                   lambda: m.claim(self.path, "root", now=self.now)]
        for action in actions:
            with self.assertRaises(RuntimeError):
                action()
            self.assertEqual(self.path.read_bytes(), before)

    def test_existing_single_claim_adopts_without_adding_more_papers(self):
        old = m.claim(self.path, "root", self.order[0], self.now)
        m.fingerprint(self.path, "root", self.now)
        m.checkpoint(self.path, "root", data={"page": 7}, now=self.now)
        before = m.read_ledger(self.path)
        batch = self.claim()
        self.assertTrue(batch["resumed"])
        self.assertEqual(len(batch["papers"]), 1)
        self.assertEqual(batch["papers"][0]["claimed_at"], old["claimed_at"])
        after = m.read_ledger(self.path)
        self.assertEqual(after["groups"], before["groups"])
        self.complete(self.order[0])
        self.assertEqual([claim["group_id"] for claim in self.claim()["papers"]], self.order[1:6])

    def test_late_si_reopens_closed_member_without_losing_its_prior_evidence(self):
        original = self.claim()
        key = self.order[0]
        self.complete(key)
        before = m.read_ledger(self.path)
        other = self.order[1]
        m.fingerprint(self.path, "root", self.now, group_id=other)
        other_stamp = m.read_ledger(self.path)["groups"][other]["fingerprint"]
        (self.source / f"{key}_si_1.pdf").write_bytes(b"new matched SI")
        m.scan(self.path, self.source, self.now + m.SECOND)
        changed = m.read_ledger(self.path)
        self.assertEqual(changed["groups"][key]["review"], before["groups"][key]["review"])
        self.assertTrue(changed["groups"][key]["needs_recheck"])
        self.assertEqual(changed["groups"][other]["fingerprint"], other_stamp)
        self.assertEqual(self.claim()["papers"], original["papers"])
        self.assertEqual(m.summary(changed)["active_review_claims"], 5)
        self.assertEqual(changed["current_paper"]["group_id"], key)
        with self.assertRaisesRegex(RuntimeError, "stability"):
            m.fingerprint(self.path, "root", self.now, group_id=key)
        with self.assertRaisesRegex(RuntimeError, "current file generation"):
            m.checkpoint(self.path, "root", "complete", group_id=key, now=self.now)

    def test_batch_alias_reconciliation_never_empties_a_member_even_after_it_closes(self):
        first, second = self.order[:2]
        (self.source / f"{second}.pdf").write_bytes((self.source / f"{first}.pdf").read_bytes())
        m.scan(self.path, self.source, self.now + m.SECOND)
        self.now += 62 * m.SECOND
        m.scan(self.path, self.source, self.now)
        self.claim(size=2)
        self.complete(first)
        stamp = m.fingerprint(self.path, "root", self.now, group_id=second)
        self.assertTrue(any(row["group_id"] == first and row["same_main"] for row in stamp["duplicates"]))
        ledger = m.read_ledger(self.path)
        self.assertFalse(ledger["group_aliases"])
        self.assertTrue(ledger["groups"][first]["files"])
        self.assertTrue(ledger["groups"][second]["files"])
        self.complete(second)
        m.scan(self.path, self.source, self.now + m.SECOND)
        ledger = m.read_ledger(self.path)
        self.assertEqual(m.canonical_group(ledger, second), first)
        self.assertEqual(ledger["groups"][second]["review"]["checkpoint"]["reviewed_source"], second)
        self.assertTrue(ledger["groups"][first]["needs_recheck"])

    def test_unclaimed_duplicate_merges_into_claim_and_requires_refingerprint(self):
        first, second = self.order[:2]
        content = (self.source / f"{first}.pdf").read_bytes()
        (self.source / f"{second}.pdf").write_bytes(content)
        m.scan(self.path, self.source, self.now + m.SECOND)
        self.now += 62 * m.SECOND
        m.scan(self.path, self.source, self.now)
        ledger = m.read_ledger(self.path)
        ledger["files"][f"{second}.pdf"]["sha256"] = hashlib.sha256(content).hexdigest()
        m.save_ledger(self.path, ledger)
        self.claim(size=1)
        stamp = m.fingerprint(self.path, "root", self.now, group_id=first)
        self.assertTrue(stamp["reconciliation_requires_refingerprint"])
        with self.assertRaisesRegex(RuntimeError, "current file generation"):
            m.checkpoint(self.path, "root", "complete", group_id=first, milestones=self.stages(), now=self.now)
        stamp = m.fingerprint(self.path, "root", self.now, group_id=first)
        self.assertEqual(len(stamp["files"]), 2)
        self.complete(first)

    def test_stability_order_and_batch_size_limits(self):
        key = self.order[0]
        (self.source / f"{key}_si_1.pdf").write_bytes(b"new SI still settling")
        m.scan(self.path, self.source, self.now + 1)
        batch = self.claim()
        self.assertEqual([claim["group_id"] for claim in batch["papers"]], self.order[1:6])
        before = self.path.read_bytes()
        for size in (0, 6, -1, 2.5, True):
            with self.assertRaises(ValueError):
                self.claim(size=size)
            self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_owners_never_duplicate_reservations(self):
        gate = threading.Barrier(2)
        def reserve(owner):
            gate.wait()
            try:
                return m.claim_batch(self.path, owner, now=self.now)
            except RuntimeError as exc:
                return str(exc)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, ["owner-a", "owner-b"]))
        winners = [result for result in results if isinstance(result, dict)]
        self.assertEqual(len(winners), 1)
        ledger = m.read_ledger(self.path)
        self.assertEqual(len(m.active_claims(ledger)), 5)
        self.assertEqual({claim["reviewer"] for claim in m.active_claims(ledger)}, {winners[0]["reviewer"]})

    def test_scan_and_all_batch_mutations_respect_exclusive_ledger_lock(self):
        self.claim()
        before = self.path.read_bytes()
        with m.locked_ledger(self.path):
            actions = [lambda: m.scan(self.path, self.source, self.now), lambda: self.claim(),
                       lambda: m.fingerprint(self.path, "root", self.now, group_id=self.order[0]),
                       lambda: m.checkpoint(self.path, "root", data={"bad": True}, group_id=self.order[0])]
            for action in actions:
                with self.assertRaisesRegex(RuntimeError, "Queue lock exists"):
                    action()
                self.assertEqual(self.path.read_bytes(), before)

    def test_no_recipe_screening_requires_independent_audit_and_scoped_generation(self):
        self.claim()
        key = self.order[0]
        m.fingerprint(self.path, "root", self.now, group_id=key)
        before = self.path.read_bytes()
        bad_records = []
        record = self.screening(key)
        record["screening"]["source_generation"] -= 1
        bad_records.append(record)
        record = self.screening(key)
        record["screening"]["independent_audit"]["reviewer"] = "primary-screener"
        bad_records.append(record)
        record = self.screening(key)
        record["screening"]["independent_audit"]["evidence"] = ["missing-audit.json"]
        bad_records.append(record)
        record = self.screening(key)
        record["screening"]["scope"] = " "
        bad_records.append(record)
        for data in bad_records:
            with self.assertRaises(ValueError):
                m.checkpoint(self.path, "root", "no_synthesis_recipe", data=data,
                             milestones=self.screening_stages(), group_id=key, now=self.now)
            self.assertEqual(self.path.read_bytes(), before)
        result = m.checkpoint(self.path, "root", "no_synthesis_recipe", data=self.screening(key),
                              milestones=self.screening_stages(), group_id=key, now=self.now)
        self.assertFalse(result["claim_retained"])
        self.assertTrue(result["batch_retained"])
        self.assertEqual(m.read_ledger(self.path)["groups"][key]["review"]["status"], "no_synthesis_recipe")

    def test_screening_cannot_close_without_fingerprint_or_five_existing_evidence_files(self):
        self.claim(size=1)
        key = self.order[0]
        data = self.screening(key)
        with self.assertRaisesRegex(RuntimeError, "current file generation"):
            m.checkpoint(self.path, "root", "no_synthesis_recipe", data=data,
                         milestones=self.screening_stages(), group_id=key, now=self.now)
        m.fingerprint(self.path, "root", self.now, group_id=key)
        stages = self.screening_stages()
        stages["publish"]["evidence"] = ["absent-publication-disposition.json"]
        with self.assertRaisesRegex(ValueError, "does not exist"):
            m.checkpoint(self.path, "root", "no_synthesis_recipe", data=data, milestones=stages, group_id=key, now=self.now)
        stages = self.screening_stages()
        stages["read"]["note"] = "  "
        with self.assertRaisesRegex(ValueError, "require a reason"):
            m.checkpoint(self.path, "root", "no_synthesis_recipe", data=data, milestones=stages, group_id=key, now=self.now)
        self.assertEqual(m.read_ledger(self.path)["groups"][key]["review"]["status"], "in_progress")

    def test_source_change_after_screening_hash_rejects_closure(self):
        self.claim(size=1)
        key = self.order[0]
        m.fingerprint(self.path, "root", self.now, group_id=key)
        (self.source / f"{key}_si_1.pdf").write_bytes(b"late SI not yet scanned")
        with self.assertRaisesRegex(RuntimeError, "Source changed"):
            m.checkpoint(self.path, "root", "no_synthesis_recipe", data=self.screening(key),
                         milestones=self.screening_stages(), group_id=key, now=self.now)

    def test_screened_member_reopens_for_later_si_and_stale_screening_cannot_reclose(self):
        self.claim()
        key = self.order[0]
        m.fingerprint(self.path, "root", self.now, group_id=key)
        original = self.screening(key)
        m.checkpoint(self.path, "root", "no_synthesis_recipe", data=original,
                     milestones=self.screening_stages(), group_id=key, now=self.now)
        (self.source / f"{key}_si_1.pdf").write_bytes(b"new synthesis supporting information")
        m.scan(self.path, self.source, self.now + m.SECOND)
        self.now += 62 * m.SECOND
        m.scan(self.path, self.source, self.now)
        m.fingerprint(self.path, "root", self.now, group_id=key)
        with self.assertRaisesRegex(ValueError, "source_generation"):
            m.checkpoint(self.path, "root", "no_synthesis_recipe", data=original,
                         milestones=self.screening_stages(), group_id=key, now=self.now)
        self.assertIn(key, [claim["group_id"] for claim in m.active_claims(m.read_ledger(self.path))])


if __name__ == "__main__":
    unittest.main()
