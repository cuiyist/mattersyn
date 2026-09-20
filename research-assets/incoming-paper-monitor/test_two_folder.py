import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

import monitor as m


class TwoFolderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.incoming = self.root / "incoming"
        self.legacy = self.root / "legacy"
        self.incoming.mkdir()
        self.legacy.mkdir()
        self.path = self.root / "private" / "ledger.json"
        self.manifest = self.root / "document-manifest.json"
        self.inventory = self.root / "inventory.json"
        self.now = time.time_ns() + 200*m.SECOND

    def tearDown(self):
        self.temp.cleanup()

    def put(self, folder, name, content=b"%PDF-main"):
        (folder / name).write_bytes(content)

    def initialize(self, claim=True):
        m.scan(self.path, self.incoming, self.now)
        m.scan(self.path, self.incoming, self.now + 61*m.SECOND)
        if claim:
            m.claim(self.path, "root", now=self.now + 61*m.SECOND)
            m.fingerprint(self.path, "root", self.now + 61*m.SECOND)
            m.checkpoint(self.path, "root", data={"main_pages_read": [1, 2], "next_action": "finish evidence"}, now=self.now + 61*m.SECOND)

    def manifests(self, stale=None):
        docs, indexed = [], []
        for name, item in m.inventory(self.legacy).items():
            fp = self.legacy / name
            digest = hashlib.sha256(fp.read_bytes()).hexdigest()
            docs.append({"id": "doc-" + name, "sourceRelativeFilename": name,
                         "fingerprint": {"bytes": item["size"] + (1 if name == stale else 0), "mtimeNs": item["mtime_ns"]},
                         "sha256": digest, "detectedFormat": "zip" if name.endswith(".docx") else "pdf"})
            indexed.append({"relativeFilename": name, "associations": [{"doi": m.filename_doi(item["group_id"]),
                            "roleCandidates": ["supporting_candidate" if item["role"] == "si" else "main_candidate"]}]})
        self.manifest.write_text(json.dumps({"documents": docs}))
        self.inventory.write_text(json.dumps({"documents": indexed}))

    def migrate(self):
        return m.upgrade_two_sources(self.path, self.legacy, self.manifest, self.inventory, self.now + 62*m.SECOND)

    def test_identical_main_alias_keeps_active_claim_checkpoint_and_all_extra_si(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old_si_1.docx", b"PK-misnamed-zip")
        self.initialize()
        before = m.read_ledger(self.path)
        self.manifests()
        result = self.migrate()
        ledger = m.read_ledger(self.path)
        self.assertEqual(ledger["current_paper"], before["current_paper"])
        group = ledger["groups"]["10.1000_old"]
        self.assertEqual(group["queue_order"], before["groups"]["10.1000_old"]["queue_order"])
        self.assertEqual(group["review"]["checkpoint"], before["groups"]["10.1000_old"]["review"]["checkpoint"])
        self.assertEqual(len(group["files"]), 3)
        self.assertEqual(ledger["group_aliases"], {"legacy::10.1000_old": "10.1000_old"})
        self.assertEqual(result["canonical_review_units"], 1)
        self.assertEqual(result["known_unique_document_hashes"], 2)
        self.assertEqual(result["confirmed_duplicate_document_copies"], 1)
        self.assertEqual(ledger["files"]["legacy::10.1000_old_si_1.docx"]["detected_format"], "zip")
        self.assertTrue(group["needs_recheck"])
        self.assertTrue(all(x["status"] == "pending" for x in group["review"]["milestones"].values()))

    def test_legacy_only_backlog_precedes_future_arrivals_and_published_not_skipped(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_legacy.pdf", b"legacy-only")
        self.initialize()
        self.manifests()
        self.migrate()
        self.put(self.incoming, "10.1000_new.pdf", b"new")
        m.scan(self.path, self.incoming, self.now + 130*m.SECOND)
        ledger = m.read_ledger(self.path)
        self.assertEqual(m.queued(ledger), ["10.1000_old", "legacy::10.1000_legacy", "10.1000_new"])
        self.assertEqual(ledger["groups"]["legacy::10.1000_legacy"]["review"]["status"], "queued")

    def test_same_doi_different_hash_never_merges(self):
        self.put(self.incoming, "10.1000_old.pdf", b"version-one")
        self.put(self.legacy, "10.1000_old.pdf", b"version-two")
        self.initialize()
        self.manifests()
        result = self.migrate()
        ledger = m.read_ledger(self.path)
        self.assertFalse(ledger["group_aliases"])
        self.assertEqual(result["canonical_review_units"], 2)
        self.assertEqual(result["normalized_doi_candidates"], 1)
        self.assertIsNone(result["distinct_paper_total"])
        self.assertEqual(ledger["groups"]["10.1000_old"]["same_doi_differing_main_hash"], ["legacy::10.1000_old"])

    def test_unhashed_same_doi_is_only_candidate_until_actual_hash(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize(claim=False)
        self.manifests()
        result = self.migrate()
        self.assertEqual(result["canonical_review_units"], 2)
        self.assertEqual(result["document_copies_not_yet_hashed"], 1)
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        m.claim(self.path, "root", now=self.now+130*m.SECOND)
        stamp = m.fingerprint(self.path, "root", self.now+130*m.SECOND)
        self.assertTrue(stamp["reconciliation_requires_refingerprint"])
        self.assertEqual(m.summary(m.read_ledger(self.path))["canonical_review_units"], 1)

    def test_stale_legacy_manifest_hash_not_reused(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize()
        self.manifests(stale="10.1000_old.pdf")
        result = self.migrate()
        self.assertEqual(result["cached_hashes_reused"], 0)
        self.assertEqual(result["canonical_review_units"], 2)

    def test_late_legacy_si_reopens_canonical_scope_and_keeps_main_claim(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize()
        self.manifests()
        self.migrate()
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        m.fingerprint(self.path, "root", self.now+130*m.SECOND)
        self.put(self.legacy, "10.1000_old_si_2.xls", b"spreadsheet")
        m.scan(self.path, self.incoming, self.now+131*m.SECOND)
        ledger = m.read_ledger(self.path)
        self.assertEqual(ledger["current_paper"]["group_id"], "10.1000_old")
        self.assertIn("legacy::10.1000_old_si_2.xls", ledger["groups"]["10.1000_old"]["files"])
        self.assertTrue(ledger["groups"]["10.1000_old"]["needs_recheck"])
        self.assertFalse(m.eligible(ledger, "10.1000_old", self.now+131*m.SECOND))

    def test_completion_requires_actual_selected_hash_and_all_evidence_milestones(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize()
        self.manifests()
        self.migrate()
        with self.assertRaisesRegex(RuntimeError, "current file generation"):
            m.checkpoint(self.path, "root", "complete", now=self.now+130*m.SECOND)
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        m.fingerprint(self.path, "root", self.now+130*m.SECOND)
        with self.assertRaisesRegex(RuntimeError, "milestones incomplete"):
            m.checkpoint(self.path, "root", "complete", now=self.now+130*m.SECOND)
        with self.assertRaisesRegex(ValueError, "require evidence"):
            m.checkpoint(self.path, "root", milestones={"read": {"status": "complete", "evidence": []}})
        stages = {stage: {"status": "complete", "evidence": [f"review/{stage}.json"]} for stage in m.MILESTONES}
        done = m.checkpoint(self.path, "root", "complete", now=self.now+130*m.SECOND, milestones=stages)
        self.assertFalse(done["claim_retained"])
        self.assertEqual(m.summary(m.read_ledger(self.path))["pending_groups"], 0)

    def test_repeated_migration_is_idempotent(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize()
        self.manifests()
        self.migrate()
        before = self.path.read_bytes()
        result = self.migrate()
        self.assertTrue(result["already_migrated"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_changed_aliased_main_splits_back_to_unresolved_version(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old.pdf")
        self.initialize()
        self.manifests()
        self.migrate()
        self.put(self.legacy, "10.1000_old.pdf", b"new version")
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        ledger = m.read_ledger(self.path)
        self.assertFalse(ledger["group_aliases"])
        self.assertEqual(ledger["current_paper"]["group_id"], "10.1000_old")
        self.assertEqual(ledger["groups"]["legacy::10.1000_old"]["files"], ["legacy::10.1000_old.pdf"])
        self.assertEqual(m.summary(ledger)["canonical_review_units"], 2)

    def test_same_si_bytes_have_one_content_unit_but_all_paths(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.incoming, "10.1000_old_si_1.pdf", b"SI-content")
        self.put(self.legacy, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_old_si_1.pdf", b"SI-content")
        self.initialize()
        self.manifests()
        self.migrate()
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        stamp = m.fingerprint(self.path, "root", self.now+130*m.SECOND)
        self.assertEqual(len(stamp["files"]), 4)
        self.assertEqual(len(stamp["unique_content_files"]), 2)
        self.assertTrue(all(len(paths) == 2 for paths in stamp["unique_content_files"].values()))

    def test_main_missing_legacy_group_can_be_explicitly_audited(self):
        self.put(self.incoming, "10.1000_old.pdf")
        self.put(self.legacy, "10.1000_orphan_si_1.docx", b"PK-source-only")
        self.initialize(claim=False)
        self.manifests()
        self.migrate()
        m.scan(self.path, self.incoming, self.now+130*m.SECOND)
        with self.assertRaisesRegex(RuntimeError, "No eligible"):
            m.claim(self.path, "root", "legacy::10.1000_orphan", self.now+130*m.SECOND)
        current = m.claim(self.path, "root", "legacy::10.1000_orphan", self.now+130*m.SECOND, allow_incomplete_bundle=True)
        self.assertTrue(current["allow_incomplete_bundle"])
        self.assertEqual(len(m.fingerprint(self.path, "root", self.now+130*m.SECOND)["files"]), 1)


if __name__ == "__main__":
    unittest.main()
