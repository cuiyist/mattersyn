"""Independent screening invariants; uses only isolated temporary fixtures."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import screen_corpus as s


RECIPE = "Synthesis: dissolve 2 mmol salt in 10 ml solvent and stir for 30 min.\nXRD shows a wurtzite crystal phase."


class ScreenCorpusAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "sources"
        self.source.mkdir()
        self.output = self.root / "screen"
        s.initialize_worker({}, str(self.output))
        self.ledger = {"schema_version": 2, "source_path": str(self.source),
                       "source_paths": {"incoming": str(self.source)}, "files": {},
                       "groups": {}, "group_aliases": {}, "current_paper": None,
                       "current_batch": None}

    def add(self, filename, data, group="g", role="main", status="queued"):
        path = self.source / filename
        path.write_bytes(data)
        stat = path.stat()
        self.ledger["files"][filename] = {
            "exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "source_id": "incoming", "relative_filename": filename,
            "group_id": group, "origin_group_id": group, "role": role,
            "role_ambiguous": False, "first_seen_at": "saved-file-arrival"}
        item = self.ledger["groups"].setdefault(group, {
            "generation": 3, "files": [], "queue_order": len(self.ledger["groups"]) + 1,
            "first_seen_at": "saved-group-arrival", "order_basis": "saved-order-basis",
            "needs_recheck": False, "review": {"status": status}})
        item["files"].append(filename)
        return path

    def task(self, filename):
        return next(item for item in s.tasks_from_ledger(self.ledger) if item["file_key"] == filename)

    def old_text(self, path, text, pages=None):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        text_path = self.root / (digest + ".txt")
        text_path.write_text(text, encoding="utf-8")
        s.LEGACY[digest] = {"sha256": digest, "text_path": str(text_path),
                            "extraction_status": "extracted", "detected_format": "pdf",
                            "page_count": len(pages or []), "page_results": pages or []}
        return digest

    def test_hash_every_actual_duplicate_and_reuse_only_exact_content(self):
        first = self.add("one.pdf", b"identical source")
        second = self.add("two.pdf", b"identical source", role="si")
        self.old_text(first, "\n\n--- PAGE 1 ---\n\n" + RECIPE)
        with patch.object(s, "sha_file", wraps=s.sha_file) as hashing, patch.object(s, "extract_source") as extracting:
            documents = [s.screen_document(self.task(name)) for name in ("one.pdf", "two.pdf")]
        self.assertTrue(all(item["hash_computed"] for item in documents))
        self.assertEqual({call.args[0] for call in hashing.call_args_list}, {first, second})
        extracting.assert_not_called()
        self.assertEqual(documents[0]["sha256"], documents[1]["sha256"])
        scopes, _ = s.rank_scopes(self.ledger, documents)
        self.assertEqual(scopes[0]["unique_text_contents"], 1)
        self.assertEqual(len(scopes[0]["file_keys"]), 2)
        self.assertEqual(scopes[0]["feature_counts"]["recipe_windows"], 1)

    def test_changed_bytes_with_restored_size_and_mtime_reject_old_hash(self):
        path = self.add("stale.pdf", b"old content")
        old_hash = self.old_text(path, "\n\n--- PAGE 1 ---\n\n" + RECIPE)
        self.ledger["files"][path.name]["sha256"] = old_hash
        task = self.task(path.name)
        original = path.stat()
        path.write_bytes(b"new content")
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
        result = s.screen_document(task)
        self.assertEqual(result["status"], "changed_since_snapshot")
        self.assertTrue(result["hash_computed"])
        self.assertNotEqual(result["sha256"], old_hash)
        self.assertIsNone(result["features"])
        self.assertFalse(s.rank_scopes(self.ledger, [result])[0][0]["priority_applicable"])

    def test_alias_terminal_and_batch_copies_are_all_preserved_without_mutation(self):
        self.add("active.txt", RECIPE.encode(), "active")
        self.add("closed.txt", b"closed source", "closed", status="complete")
        self.add("alias.unknown", b"alias bytes", "alias")
        self.ledger["groups"]["alias"]["alias_of"] = "active"
        self.ledger["group_aliases"]["alias"] = "active"
        self.ledger["current_batch"] = {"batch_id": "saved-batch", "papers": [
            {"group_id": "active", "reviewer": "owner", "claimed_at": "saved-claim"}]}
        before = copy.deepcopy(self.ledger)
        tasks = s.tasks_from_ledger(self.ledger)
        self.assertEqual({task["file_key"] for task in tasks}, {"active.txt", "closed.txt", "alias.unknown"})
        alias = next(task for task in tasks if task["file_key"] == "alias.unknown")
        self.assertEqual((alias["group_id"], alias["origin_group_id"]), ("active", "alias"))
        documents = [s.screen_document(task) for task in tasks]
        scopes, _ = s.rank_scopes(self.ledger, documents)
        self.assertEqual({scope["group_id"] for scope in scopes}, {"active", "closed"})
        active = next(scope for scope in scopes if scope["group_id"] == "active")
        self.assertTrue(active["current_batch_member"])
        self.assertEqual(active["first_seen_at"], "saved-group-arrival")
        self.assertEqual(active["order_basis"], "saved-order-basis")
        self.assertEqual(self.ledger, before)

    def test_unreadable_si_stays_manual_despite_strong_main(self):
        self.add("main.txt", RECIPE.encode())
        self.add("supplement.doc", bytes.fromhex("D0CF11E0A1B11AE1") + b"binary", role="si")
        documents = [s.screen_document(task) for task in s.tasks_from_ledger(self.ledger)]
        scopes, _ = s.rank_scopes(self.ledger, documents)
        self.assertEqual(scopes[0]["priority_tier"], "B_recipe_and_crystalline_evidence_candidates")
        self.assertIn("no_usable_text_is_not_evidence_of_no_recipe", scopes[0]["manual_flags"])
        self.assertFalse(scopes[0]["terminal_review_status_assigned"])

    def test_missing_source_retained_and_never_gets_applicable_priority(self):
        path = self.add("gone.txt", RECIPE.encode())
        task = self.task(path.name)
        path.unlink()
        document = s.screen_document(task)
        self.assertEqual(document["status"], "source_or_cache_missing")
        scopes, _ = s.rank_scopes(self.ledger, [document])
        self.assertFalse(scopes[0]["priority_applicable"])
        self.assertEqual(scopes[0]["file_keys"], [path.name])

    def test_same_size_same_mtime_change_during_extraction_invalidates_evidence(self):
        path = self.add("race.txt", b"old content")
        original = path.stat()
        def changed_reader(source, head):
            source.write_bytes(b"new content")
            os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
            return {"extraction_status": "extracted", "detected_format": "txt"}, RECIPE
        with patch.object(s, "extract_source", side_effect=changed_reader):
            result = s.screen_document(self.task(path.name))
        self.assertEqual(result["status"], "changed_during_extraction")
        self.assertIsNone(result["features"])
        self.assertFalse(s.rank_scopes(self.ledger, [result])[0][0]["priority_applicable"])

    def test_blank_pdf_markers_are_not_usable_text_or_low_signal_scope(self):
        path = self.add("blank.pdf", b"image-only fixture")
        self.old_text(path, "\n\n--- PAGE 1 ---\n\n\n\n--- PAGE 2 ---\n\n",
                      [{"page": 1, "characters": 0, "status": "no_extractable_text"},
                       {"page": 2, "characters": 0, "status": "no_extractable_text"}])
        result = s.screen_document(self.task(path.name))
        self.assertEqual(result["text_characters_screened"], 0)
        self.assertEqual(result["status"], "manual_format_or_text_review_required")
        self.assertIn("no_usable_text_is_not_evidence_of_no_recipe", result["manual_flags"])
        self.assertEqual(s.rank_scopes(self.ledger, [result])[0][0]["priority_tier"], "U_manual_or_unreadable_scope")

    def test_empty_docx_remains_no_extractable_text(self):
        path = self.add("empty.docx", b"")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:drawing/></w:r></w:p></w:body></w:document>')
        self.ledger["files"][path.name].update(size=path.stat().st_size, mtime_ns=path.stat().st_mtime_ns)
        result = s.screen_document(self.task(path.name))
        self.assertEqual(result["extraction_status"], "no_extractable_text")
        self.assertEqual(result["text_characters_screened"], 0)
        self.assertEqual(result["status"], "manual_format_or_text_review_required")

    def test_document_locators_and_sample_links_remain_unverified(self):
        features = s.text_features("\n\n--- PAGE 7 ---\n\n" + RECIPE +
                                   "\n\n--- OOXML PART word/document.xml ---\n\nFractional atomic coordinates for sample A", "f" * 64)
        self.assertEqual({snippet["page"] for snippet in features["snippets"] if snippet["page"]}, {7})
        self.assertIn("word/document.xml", {snippet["ooxml_part"] for snippet in features["snippets"]})
        self.assertTrue(all(snippet["source_sha256"] == "f" * 64 for snippet in features["snippets"] ))
        self.assertFalse(features["verified_recipe"])
        self.assertFalse(features["verified_structure"])
        self.assertFalse(features["verified_sample_join"])

    def test_archive_size_limit_preserves_manual_disposition(self):
        path = self.add("oversized.docx", b"")
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", "x" * 32)
        self.ledger["files"][path.name].update(size=path.stat().st_size, mtime_ns=path.stat().st_mtime_ns)
        with patch.object(s, "MAX_MEMBER_BYTES", 16):
            document = s.screen_document(self.task(path.name))
        self.assertEqual(document["status"], "manual_format_or_text_review_required")
        self.assertTrue(document["hash_computed"])
        self.assertEqual(document["features"]["all_text_characters_examined"], 0)
        self.assertEqual(document["detected_format"], "docx")
        self.assertEqual(document["reader_limit_details"]["uncompressed_bytes"], 32)
        self.assertIn("bounded_reader_limit_requires_manual_inspection", document["manual_flags"])
        self.assertTrue(s.rank_scopes(self.ledger, [document])[0][0]["priority_applicable"])


if __name__ == "__main__":
    unittest.main()
