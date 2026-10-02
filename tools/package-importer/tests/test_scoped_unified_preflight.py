"""Focused regressions for scoped audit and status-promotion compatibility."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


PREFLIGHT_PATH = Path(os.environ.get(
    "MATTERSYN_PREFLIGHT_UNDER_TEST",
    Path(__file__).resolve().parents[1] / "preflight.py"))
SPEC = importlib.util.spec_from_file_location("unified_scoped_preflight", PREFLIGHT_PATH)
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


class ScopedStatusPromotionTests(unittest.TestCase):
    def test_metadata_only_and_imported_unreviewed_accept_incremented_revision(self):
        after = {"revision": 3, "quality": {"review_status": "source_reviewed"}}
        for old_status in ("metadata_only", "imported_unreviewed"):
            before = {"revision": 2, "quality": {"review_status": old_status}}
            self.assertTrue(PREFLIGHT.valid_scoped_status_promotion(before, after))

    def test_same_revision_is_only_for_checked_imported_link_removal(self):
        after = {"revision": 2, "quality": {"review_status": "source_reviewed"}}
        changes = {"/context_links", "/quality/review_status"}
        imported = {"revision": 2, "quality": {"review_status": "imported_unreviewed"}}
        metadata = {"revision": 2, "quality": {"review_status": "metadata_only"}}
        self.assertTrue(PREFLIGHT.valid_scoped_status_promotion(imported, after, changes, True))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(imported, after, changes, False))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(imported, after, set(), True))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(metadata, after, changes, True))

    def test_other_statuses_and_revisions_remain_rejected(self):
        after = {"revision": 3, "quality": {"review_status": "source_reviewed"}}
        for old_status in ("draft", "source_reviewed", "structured_data_verified"):
            before = {"revision": 2, "quality": {"review_status": old_status}}
            self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(before, after))
        before = {"revision": 2, "quality": {"review_status": "metadata_only"}}
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(
            before, {"revision": 4, "quality": {"review_status": "source_reviewed"}}))

    def test_already_reviewed_admin_correction_requires_exact_delta(self):
        before = {"revision": 1, "quality": {"review_status": "source_reviewed"}}
        after = {"revision": 2, "quality": {"review_status": "source_reviewed"}}
        changes = {"/revision", "/sources/0/main_status", "/quality/review_scope"}
        self.assertTrue(PREFLIGHT.valid_scoped_status_promotion(before, after, changes, True))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(before, after, changes, False))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(before, after,
            changes | {"/operations/0/action"}, True))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(before, after,
            {"/revision"}, True))
        self.assertFalse(PREFLIGHT.valid_scoped_status_promotion(before,
            {**after, "revision": 3}, changes, True))


class ScopedUrbanGuardTests(unittest.TestCase):
    def test_scoped_audit_paper_id_alias_must_match_package_and_revision(self):
        package = {"package_id": "paper-a", "revision": 2}
        self.assertTrue(PREFLIGHT.scoped_audit_identity_matches(
            {"paper_id": "paper-a", "package_revision": 2}, package))
        self.assertTrue(PREFLIGHT.scoped_audit_identity_matches(
            {"package_id": "paper-a", "paper_id": "paper-a", "package_revision": 2}, package))
        self.assertFalse(PREFLIGHT.scoped_audit_identity_matches(
            {"package_id": "paper-a", "paper_id": "paper-b", "package_revision": 2}, package))
        self.assertFalse(PREFLIGHT.scoped_audit_identity_matches(
            {"paper_id": "paper-a", "package_revision": 1}, package))

    def test_normalized_quick_audit_requires_pinned_original(self):
        science = "a" * 64
        package = {"package_id": "paper-a", "revision": 1}
        package_audit = {"author_id": "author", "reviewer_id": "reviewer",
                         "receipt_id": "paper-a-original.json"}
        original = {"schema": "mattersyn-independent-quick-audit/1",
                    "decision": "accepted", "package_id": "paper-a",
                    "scientific_sha256": science, "author_id": "author",
                    "reviewer_id": "reviewer", "accepted_package_manifest_sha256": "b" * 64}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            original_path = root / package_audit["receipt_id"]
            original_path.write_text(json.dumps(original), encoding="utf-8")
            addendum_path = root / "paper-a-addendum.json"
            addendum = {"schema": "mattersyn-independent-scoped-acceptance-addendum/1",
                        "package_id": "paper-a", "package_revision": 1,
                        "scientific_sha256": science, "author_id": "author",
                        "reviewer_id": "reviewer",
                        "original_audit_receipt": "receipts/paper-a-original.json",
                        "original_audit_receipt_sha256": PREFLIGHT.sha(original_path),
                        "frozen_package_manifest_sha256": "b" * 64}
            self.assertTrue(PREFLIGHT.scoped_audit_receipt_matches(
                addendum, package_audit, addendum_path, package, science))
            self.assertFalse(PREFLIGHT.scoped_audit_receipt_matches(
                {**addendum, "original_audit_receipt_sha256": "0" * 64},
                package_audit, addendum_path, package, science))
            original["decision"] = "changes_requested"
            original_path.write_text(json.dumps(original), encoding="utf-8")
            addendum["original_audit_receipt_sha256"] = PREFLIGHT.sha(original_path)
            self.assertFalse(PREFLIGHT.scoped_audit_receipt_matches(
                addendum, package_audit, addendum_path, package, science))

    def test_reviewer_aliases_must_agree_and_cannot_self_review(self):
        package_audit = {"author_id": "author", "reviewer_id": "reviewer"}
        audit = {"author_id": "author", "reviewer_id": "reviewer", "auditor_id": "reviewer"}
        self.assertTrue(PREFLIGHT.scoped_audit_reviewer_matches(audit, package_audit))
        self.assertTrue(PREFLIGHT.scoped_audit_reviewer_matches(
            {"author_id": "author", "auditor_id": "reviewer"}, package_audit))
        self.assertFalse(PREFLIGHT.scoped_audit_reviewer_matches(
            {**audit, "auditor_id": "someone-else"}, package_audit))
        self.assertFalse(PREFLIGHT.scoped_audit_reviewer_matches(
            {"author_id": "author"}, package_audit))
        self.assertFalse(PREFLIGHT.scoped_audit_reviewer_matches(
            audit, {"author_id": "reviewer", "reviewer_id": "reviewer"}))

    def test_decision_aliases_must_agree(self):
        accepted = "ACCEPTED_SCOPED_CONTENT"
        self.assertTrue(PREFLIGHT.scoped_audit_decision_accepted({"decision": accepted}))
        self.assertTrue(PREFLIGHT.scoped_audit_decision_accepted(
            {"decision": accepted, "verdict": accepted}))
        self.assertFalse(PREFLIGHT.scoped_audit_decision_accepted(
            {"decision": accepted, "verdict": "REJECTED"}))

    def test_only_exact_fictitious_reader_link_can_be_removed(self):
        source_id = "paper-id"
        doi = "10.1234/paper"
        primary = {"label": "DOI", "url": "https://doi.org/10.1234/paper",
                   "relation": "primary_source"}
        fictitious = {"label": "Source review", "url": "paper-review.html?id=paper-id",
                      "relation": "source_review"}
        before = {"revision": 2, "quality": {"review_status": "imported_unreviewed"},
                  "context_links": [primary, fictitious]}
        after = {"revision": 2, "quality": {"review_status": "source_reviewed"},
                 "context_links": [primary]}
        with TemporaryDirectory() as temp:
            candidate = Path(temp)
            changes, allowed = PREFLIGHT.scoped_record_changes_allowed(
                before, after, source_id, doi, candidate)
            self.assertTrue(allowed)
            self.assertIn("/context_links", changes)
            self.assertTrue(PREFLIGHT.valid_scoped_status_promotion(
                before, after, changes, allowed))

            mutated = copy.deepcopy(after)
            mutated["context_links"][0]["url"] = "https://doi.org/10.1234/other"
            self.assertFalse(PREFLIGHT.scoped_record_changes_allowed(
                before, mutated, source_id, doi, candidate)[1])

            with_extra_change = copy.deepcopy(after)
            with_extra_change["science"] = "unreviewed"
            self.assertFalse(PREFLIGHT.scoped_record_changes_allowed(
                before, with_extra_change, source_id, doi, candidate)[1])

            formal_reader = candidate / "recipe-atlas/data/paper-reviews/paper-id.json"
            formal_reader.parent.mkdir(parents=True)
            formal_reader.write_text("{}", encoding="utf-8")
            self.assertFalse(PREFLIGHT.scoped_record_changes_allowed(
                before, after, source_id, doi, candidate)[1])


if __name__ == "__main__":
    unittest.main()
