"""Focused regressions for scoped audit and status-promotion compatibility."""
from __future__ import annotations

import copy
import importlib.util
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


class ScopedUrbanGuardTests(unittest.TestCase):
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
