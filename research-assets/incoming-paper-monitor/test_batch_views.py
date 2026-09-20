"""Independent checks of batch reports and hash-bound intake manifests."""
import copy
import json
import os
from pathlib import Path
import unittest

import build_batch_manifest as manifest
import build_queue_report as report
import monitor as m
import test_batch as fixtures


class BatchViewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BatchTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.output = self.fixture.root / "batch-views"
        self.pairing_paths = {}

    def prepare(self):
        f = self.fixture
        f.claim()
        for claim in m.active_claims(m.read_ledger(f.path)):
            key = claim["group_id"]
            m.fingerprint(f.path, "root", f.now, group_id=key)
            m.checkpoint(f.path, "root", data={"title": "Fixture " + key}, group_id=key, now=f.now)
        data = manifest.build(m.read_ledger(f.path), self.output)
        self.pairing_paths = {paper["paper_id"]: Path(paper["review_directory"]) / "pairing-review.json" for paper in data["papers"]}
        return data

    def pairing(self, key):
        f = self.fixture
        ledger = m.read_ledger(f.path)
        group = ledger["groups"][key]
        docs = {}
        for name in group["files"]:
            item = ledger["files"][name]
            docs.setdefault(item["sha256"], {"sha256": item["sha256"], "role": item["role"],
                                            "basis": "Inspected title, DOI and main/SI content against the parent source."})
        return {"status": "passed", "group_id": key, "source_generation": group["generation"],
                "bundle_sha256": group["fingerprint"]["bundle_sha256"],
                "documents": list(docs.values()), "reviewer": "pairing-author", "evidence": [str(f.evidence)],
                "independent_audit": {"status": "passed", "reviewer": "pairing-auditor", "evidence": [str(f.evidence)]}}

    def save_pairing(self, key, review):
        path = self.pairing_paths[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(review), encoding="utf-8")

    def pairing_state(self, key):
        result = manifest.build(m.read_ledger(self.fixture.path), self.output)
        return next(paper["main_si_pairing"] for paper in result["papers"] if paper["paper_id"] == key)

    def assert_not_passed(self, key):
        try:
            status = self.pairing_state(key)["status"]
        except ValueError:
            return
        self.assertNotEqual(status, "passed")

    def test_report_shows_every_active_paper_and_excludes_all_five_from_waiting(self):
        self.prepare()
        f = self.fixture
        before = f.path.read_bytes()
        snapshot = report.build_snapshot(m.read_ledger(f.path), {}, {}, {}, now=f.now)
        self.assertEqual(snapshot["counts"]["active_review_claims"], 5)
        self.assertEqual(snapshot["counts"]["waiting_review_scopes"], 2)
        self.assertEqual([paper["group_id"] for paper in snapshot["active_papers"]], f.order[:5])
        self.assertEqual([paper["group_id"] for paper in snapshot["next_12_waiting"]], f.order[5:])
        html = report.render_html(snapshot, self.output)
        markdown = report.render_markdown(snapshot)
        self.assertEqual(html.count("CURRENT PAPER · QUEUE #"), 5)
        self.assertEqual(markdown.count("## Current paper"), 5)
        for key in f.order[:5]:
            self.assertIn("Fixture " + key, html)
            self.assertIn("Fixture " + key, markdown)
        self.assertEqual(f.path.read_bytes(), before)

    def test_screening_exclusion_is_counted_separately_and_reopening_removes_closure(self):
        self.prepare()
        f = self.fixture
        full, skipped = f.order[:2]
        f.complete(full)
        m.checkpoint(f.path, "root", "no_synthesis_recipe", data=f.screening(skipped),
                     milestones=f.screening_stages(), group_id=skipped, now=f.now)
        snapshot = report.build_snapshot(m.read_ledger(f.path), {}, {}, {}, now=f.now)
        self.assertEqual(snapshot["counts"]["evidence_closed_new_queue_scopes"], 2)
        self.assertEqual(snapshot["counts"]["fully_curated_queue_scopes"], 1)
        self.assertEqual(snapshot["counts"]["screened_no_recipe_scopes"], 1)
        self.assertEqual(snapshot["counts"]["active_review_claims"], 3)
        self.assertEqual(snapshot["counts"]["waiting_review_scopes"], 2)
        (f.source / f"{skipped}_si_1.pdf").write_bytes(b"new SI outside the prior screening scope")
        m.scan(f.path, f.source, f.now + m.SECOND)
        snapshot = report.build_snapshot(m.read_ledger(f.path), {}, {}, {}, now=f.now)
        self.assertEqual(snapshot["counts"]["fully_curated_queue_scopes"], 1)
        self.assertEqual(snapshot["counts"]["screened_no_recipe_scopes"], 0)
        self.assertEqual(snapshot["counts"]["active_review_claims"], 4)
        self.assertEqual(snapshot["counts"]["waiting_review_scopes"], 2)

    def test_manifest_preserves_original_paths_names_and_unique_document_hashes(self):
        f = self.fixture
        key = f.order[0]
        for number in (1, 2):
            (f.source / f"{key}_si_{number}.pdf").write_bytes(b"identical SI copy")
        m.scan(f.path, f.source, f.now + m.SECOND)
        f.now += 62 * m.SECOND
        m.scan(f.path, f.source, f.now)
        sources_before = {path.name: path.read_bytes() for path in f.source.iterdir()}
        result = self.prepare()
        paper = next(paper for paper in result["papers"] if paper["paper_id"] == key)
        self.assertEqual(len(paper["file_copies"]), 3)
        self.assertEqual(paper["unique_document_count"], 2)
        for item in paper["file_copies"]:
            self.assertEqual(item["source_path"], str(f.source / item["original_filename"]))
            self.assertEqual(item["original_filename"], item["file_key"])
            self.assertEqual(item["document_id"], "sha256:" + item["sha256"])
        self.assertEqual({path.name: path.read_bytes() for path in f.source.iterdir()}, sources_before)

    def test_pairing_pending_stale_and_passed_are_distinct(self):
        self.prepare()
        key = self.fixture.order[0]
        self.assertEqual(self.pairing_state(key)["status"], "pending")
        for field, value in (("source_generation", -1), ("group_id", "another-paper"), ("bundle_sha256", "0" * 64)):
            review = self.pairing(key)
            review[field] = value
            self.save_pairing(key, review)
            self.assertEqual(self.pairing_state(key)["status"], "stale")
        review = self.pairing(key)
        review["documents"][0]["sha256"] = "1" * 64
        self.save_pairing(key, review)
        self.assertEqual(self.pairing_state(key)["status"], "stale")
        self.save_pairing(key, self.pairing(key))
        self.assertEqual(self.pairing_state(key)["status"], "passed")

    def test_pairing_cannot_pass_with_same_author_and_auditor_or_absent_evidence(self):
        self.prepare()
        key = self.fixture.order[0]
        review = self.pairing(key)
        review["independent_audit"]["reviewer"] = review["reviewer"]
        self.save_pairing(key, review)
        self.assert_not_passed(key)
        review = self.pairing(key)
        review["independent_audit"]["evidence"] = [str(self.output / "absent.json")]
        self.save_pairing(key, review)
        self.assert_not_passed(key)

    def test_unresolved_or_conflicting_duplicate_roles_cannot_be_verified_pairings(self):
        self.prepare()
        key = self.fixture.order[0]
        review = self.pairing(key)
        review["documents"][0]["role"] = "unresolved"
        self.save_pairing(key, review)
        self.assert_not_passed(key)
        review = self.pairing(key)
        duplicate = copy.deepcopy(review["documents"][0])
        duplicate["role"] = "si"
        review["documents"].append(duplicate)
        self.save_pairing(key, review)
        self.assert_not_passed(key)

    def test_blank_pairing_identity_or_basis_cannot_be_verified(self):
        self.prepare()
        key = self.fixture.order[0]
        for field in ("reviewer", "basis"):
            review = self.pairing(key)
            if field == "reviewer":
                review["reviewer"] = "  "
            else:
                review["documents"][0]["basis"] = "  "
            self.save_pairing(key, review)
            self.assert_not_passed(key)

    def test_changed_source_metadata_refuses_manifest(self):
        self.prepare()
        f = self.fixture
        (f.source / f"{f.order[0]}.pdf").write_bytes(b"changed source content and length")
        with self.assertRaises((ValueError, RuntimeError)):
            manifest.build(m.read_ledger(f.path), self.output)

    def test_new_unscanned_si_refuses_existing_verified_manifest(self):
        self.prepare()
        f = self.fixture
        key = f.order[0]
        self.save_pairing(key, self.pairing(key))
        (f.source / f"{key}_si_1.pdf").write_bytes(b"late SI with previously unseen source scope")
        with self.assertRaises((ValueError, RuntimeError)):
            manifest.build(m.read_ledger(f.path), self.output)

    def test_changed_source_bytes_with_preserved_metadata_refuse_manifest(self):
        self.prepare()
        f = self.fixture
        path = f.source / f"{f.order[0]}.pdf"
        before = path.stat()
        original = path.read_bytes()
        path.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaises((ValueError, RuntimeError)):
            manifest.build(m.read_ledger(f.path), self.output)

    def test_distinct_unmerged_source_groups_have_distinct_review_directories(self):
        f = self.fixture
        key = f.order[0]
        legacy = f.root / "legacy"
        legacy.mkdir()
        (legacy / f"{key}.pdf").write_bytes(b"different version, same DOI candidate")
        ledger = m.read_ledger(f.path)
        ledger["source_paths"]["legacy"] = str(legacy)
        m.save_ledger(f.path, ledger)
        m.scan(f.path, f.source, f.now + m.SECOND)
        f.now += 62 * m.SECOND
        m.scan(f.path, f.source, f.now)
        ledger = m.read_ledger(f.path)
        # Insert both independent versions in this isolated fixture's next batch.
        for group in ledger["groups"].values():
            if group["queue_order"] > 1:
                group["queue_order"] += 1
        ledger["groups"]["legacy::" + key]["queue_order"] = 2
        m.save_ledger(f.path, ledger)
        result = self.prepare()
        paths = [paper["review_directory"] for paper in result["papers"]]
        self.assertEqual(len(paths), len(set(paths)))


if __name__ == "__main__":
    unittest.main()
