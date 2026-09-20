"""Isolated end-to-end and priority-contract checks; never use live corpus data."""
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import monitor
import screen_corpus as screen


class CorpusScreenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.source = self.root / "source"
        self.source.mkdir()
        self.output = self.root / "screen"
        self.snapshot = self.root / "snapshot.json"
        self.now = time.time_ns() + 240 * monitor.SECOND

    def fixture(self):
        text = "Experimental synthesis\nDissolved 20 mg in 4 mL ethanol and heated for 2 h.\nX-ray diffraction shows wurtzite with lattice parameters. Sample A."
        (self.source / "10.1000_method.txt").write_text(text, encoding="utf-8")
        (self.source / "10.1000_unreadable.doc").write_bytes(bytes.fromhex("D0CF11E0A1B11AE1") + b"binary-content")
        ledger = monitor.new_ledger(self.source, self.now)
        observed = monitor.inventory(self.source)
        monitor.scan_state(ledger, observed, self.now)
        monitor.scan_state(ledger, observed, self.now + 61 * monitor.SECOND)
        ledger.update(schema_version=2, source_paths={"incoming": str(self.source)}, group_aliases={})
        for name, item in ledger["files"].items():
            item.update(source_id="incoming", relative_filename=name, origin_group_id=item["group_id"])
        for group in ledger["groups"].values():
            group["doi_candidates"] = []
        monitor.save_ledger(self.snapshot, ledger)
        return ledger

    def test_full_small_snapshot_accounts_for_every_file_without_mutating_sources_or_ledger(self):
        ledger = self.fixture()
        before = self.snapshot.read_bytes()
        source_bytes = {path.name: path.read_bytes() for path in self.source.iterdir()}
        result = screen.run(self.snapshot, self.output, self.root / "missing-legacy-manifest.json", workers=1)
        self.assertEqual(result["counts"]["snapshot_present_files"], 2)
        self.assertEqual(result["counts"]["per_file_dispositions"], 2)
        self.assertEqual(result["counts"]["actual_source_hashes_computed"], 2)
        self.assertFalse(result["review_state_changed"])
        self.assertFalse(result["scientific_review_performed"])
        self.assertTrue(result["require_screened"])
        self.assertEqual(len(result["rankings"]), 2)
        self.assertTrue(all(set(("group_id", "score", "source_generation")) <= set(item) for item in result["rankings"]))
        self.assertEqual(self.snapshot.read_bytes(), before)
        self.assertEqual({path.name: path.read_bytes() for path in self.source.iterdir()}, source_bytes)
        self.assertEqual(json.loads((self.output / "progress.json").read_text())["state"], "complete")
        self.assertTrue(all(scope["saved_review_status"] == "queued" and not scope["terminal_review_status_assigned"] for scope in result["scopes"]))

    def test_signal_score_has_native_locator_and_never_verified_sample_join(self):
        features = screen.text_features("\n\n--- PAGE 7 ---\n\nDissolved 20 mg and injected 2 mL. Heated for 2 h. Sample A.\nAtomic coordinates and structure refinement are reported.", "a" * 64)
        self.assertGreater(features["counts"]["recipe_windows"], 0)
        self.assertGreater(features["counts"]["coordinate_mention"], 0)
        self.assertNotIn("coordinate_data", features["counts"])
        self.assertEqual(features["snippets"][0]["page"], 7)
        self.assertIn("A", features["sample_identifier_mentions"])
        self.assertFalse(features["verified_sample_join"])
        self.assertFalse(features["verified_structure"])

    def test_no_signal_and_failure_outcomes_remain_candidates(self):
        empty = screen.text_features("No relevant keywords occur here.", "a" * 64)
        self.assertEqual(empty["counts"], {})
        failed = screen.text_features("\n\n--- PAGE 2 ---\n\nHeated 20 mg and stirred in 5 mL ethanol for 3 h; no particles were formed and aggregation occurred.", "b" * 64)
        self.assertGreater(failed["counts"]["failure_or_nonideal_outcome"], 0)
        self.assertGreater(failed["counts"]["recipe_windows"], 0)

    def test_stale_source_remains_accounted_but_cannot_receive_applicable_priority(self):
        ledger = self.fixture()
        path = self.source / "10.1000_method.txt"
        path.write_text("Changed source after frozen snapshot", encoding="utf-8")
        screen.initialize_worker({}, str(self.output))
        results = [screen.screen_document(task) for task in screen.tasks_from_ledger(ledger)]
        self.assertTrue(all(item["hash_computed"] for item in results))
        changed = next(item for item in results if item["file_key"] == path.name)
        self.assertEqual(changed["status"], "changed_since_snapshot")
        scopes, _ = screen.rank_scopes(ledger, results)
        self.assertFalse(next(scope for scope in scopes if scope["group_id"] == changed["group_id"])["priority_applicable"])

    def test_private_atomic_replace_retries_transient_windows_reader_conflict(self):
        temporary = self.root / "cache.tmp"
        target = self.root / "cache.json"
        temporary.write_text("new cache", encoding="utf-8")
        actual_replace = screen.os.replace
        calls = []
        def transient(source, destination):
            calls.append((source, destination))
            if len(calls) < 3:
                raise PermissionError("simulated transient Windows sharing violation")
            return actual_replace(source, destination)
        with patch.object(screen.os, "replace", side_effect=transient), patch.object(screen.time, "sleep"):
            screen.replace_with_retry(temporary, target)
        self.assertEqual(len(calls), 3)
        self.assertEqual(target.read_text(encoding="utf-8"), "new cache")

    def test_private_cache_read_retries_transient_windows_replacement_conflict(self):
        target = self.root / "cache.json"
        target.write_text('{"version": "fixture"}', encoding="utf-8")
        actual_read = Path.read_text
        calls = []
        def transient(path, *args, **kwargs):
            calls.append(path)
            if len(calls) < 3:
                raise PermissionError("simulated private-cache replacement conflict")
            return actual_read(path, *args, **kwargs)
        with patch.object(Path, "read_text", autospec=True, side_effect=transient), patch.object(screen.time, "sleep"):
            result = screen.read_cache_json(target)
        self.assertEqual(len(calls), 3)
        self.assertEqual(result, {"version": "fixture"})


if __name__ == "__main__":
    unittest.main()
