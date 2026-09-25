from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mattersyn_importer", ROOT / "importer.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ImporterUnitTests(unittest.TestCase):
    def test_relative_paths_reject_unnormalized_escapes(self):
        for value in ("", "/absolute", "a//b", "a/./b", "a/../b", "C:/private", "a\\b"):
            with self.subTest(value=value), self.assertRaises(IMPORTER.ImportRejected):
                IMPORTER.posix_relative(value)
        self.assertEqual(IMPORTER.posix_relative("recipe-atlas/data/records/x.json").as_posix(), "recipe-atlas/data/records/x.json")

    def test_figure_summary_deduplicates_gallery_and_record_cards(self):
        shared = {"id": "figure-1", "source_id": "doi-source", "public_asset": "assets/figure-1.png"}
        private = {"id": "figure-2", "source_id": "doi-source"}
        payload = {
            "figures_by_source": {"doi-source": [shared, private]},
            "records": {"record": {"figures": [dict(shared), dict(private)]}},
        }
        self.assertEqual(IMPORTER.reader_figure_counts(payload), (2, 1))

    def test_router_registration_updates_both_condition_gates(self):
        router = (
            "import {buildYu1998Scene,createYu1998Art} from './yu1998-protocol.mjs?v=0.39.1';\n"
            "function x(){const sourceArt=createYu1998Art(o,r)||fallback;"
            "const yu=buildYu1998Scene(o,r),costanzo=buildCostanzo2016Scene(o,r);"
            "el('p',yu?.caption||costanzo?.caption||'x');"
            "if(yu||costanzo||true){} if(yu||costanzo||false){}}"
        ).encode()
        module = b"export function buildThomson2010Scene(o,r){} export function createThomson2010Art(o,r){}"
        registration = {
            "scene_builder": "buildThomson2010Scene",
            "art_builder": "createThomson2010Art",
            "import_line": "import {buildThomson2010Scene,createThomson2010Art} from './thomson2010-protocol.mjs?v=0.39.1';",
            "import_anchor": "import {buildYu1998Scene,createYu1998Art} from './yu1998-protocol.mjs?v=0.39.1';",
        }
        result = IMPORTER.patch_protocol_router(router, module, registration).decode()
        self.assertIn("const thomson=buildThomson2010Scene(o,r),yu=buildYu1998Scene(o,r)", result)
        self.assertEqual(result.count("if(thomson||yu||costanzo||"), 2)
        with self.assertRaises(IMPORTER.ImportRejected):
            IMPORTER.patch_protocol_router(result.encode(), module, registration)

    def test_binding_merge_rejects_stale_registry_digest_and_duplicate_record(self):
        record = {"record_id": "record-a"}
        chemistry = {
            "source_record_sha256": "a" * 64,
            "current_registry_sha256": "b" * 64,
            "material_bindings": {"m": "molecule-a"},
            "candidate_registry_ids_added": {},
        }
        base = {"recordBindings": {}, "bindingNotes": {}, "sourceRecordSha256": {}}
        with self.assertRaises(IMPORTER.ImportRejected):
            IMPORTER.merge_chemical_bindings(base, chemistry, record, "a" * 64, "c" * 64, {"molecule-a"})
        chemistry["current_registry_sha256"] = "c" * 64
        merged, _ = IMPORTER.merge_chemical_bindings(base, chemistry, record, "a" * 64, "c" * 64, {"molecule-a"})
        self.assertIn("record-a", merged["recordBindings"])
        with self.assertRaises(IMPORTER.ImportRejected):
            IMPORTER.merge_chemical_bindings(merged, chemistry, record, "a" * 64, "c" * 64, {"molecule-a"})

    def test_stage_is_private_create_only_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "first"
            plan = {"status": "private_staged_overlay; not applied or published"}
            manifest_sha, count = IMPORTER.stage_overlay(target, root, {"recipe-atlas/data/x.json": b"{}\n", "integration-metadata/x.json": b"{}\n"}, plan)
            self.assertEqual(len(manifest_sha), 64)
            self.assertGreaterEqual(count, 4)
            self.assertTrue((target / "repo/recipe-atlas/data/x.json").is_file())
            self.assertTrue((target / "control/integration-metadata/x.json").is_file())
            self.assertFalse((target / "repo/integration-metadata/x.json").exists())
            with self.assertRaises(IMPORTER.ImportRejected):
                IMPORTER.stage_overlay(target, root, {}, plan)

    def test_staged_overlay_verification_rejects_unlisted_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            manifest_sha, _ = IMPORTER.stage_overlay(
                stage, root, {"recipe-atlas/data/x.json": b"{}\n"},
                {"status": "private_staged_overlay; not applied or published",
                 "operations": [{"target_repo_path": "recipe-atlas/data/x.json", "operation": "create_only"}]},
            )
            result = IMPORTER.verify_staged_overlay(stage, manifest_sha)
            self.assertEqual(result["repo_payload_files"], 1)
            self.assertEqual(result["status"], "staged_private_overlay_not_applied_or_published")
            (stage / "repo" / "unlisted.json").write_bytes(b"{}\n")
            with self.assertRaises(IMPORTER.ImportRejected):
                IMPORTER.verify_staged_overlay(stage, manifest_sha)

    def test_bundle_verification_detects_tamper_and_extra_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "input.json").write_bytes(b"{}\n")
            payload = {"files": [{"path": "input.json", "bytes": 3, "sha256": IMPORTER.digest_file(root / "input.json")}]} 
            manifest = json.dumps(payload, separators=(",", ":")).encode()
            (root / "bundle-manifest.json").write_bytes(manifest)
            contract = {"paths": {"bundle_manifest": "bundle-manifest.json"}, "package": {"bundle_manifest_sha256": IMPORTER.digest_bytes(manifest)}}
            _, files = IMPORTER.verify_bundle(root, contract)
            self.assertEqual(set(files), {"input.json"})
            (root / "input.json").write_bytes(b"tampered")
            with self.assertRaises(IMPORTER.ImportRejected):
                IMPORTER.verify_bundle(root, contract)

    def test_existing_repository_target_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "existing.json").write_text("keep", encoding="utf-8")
            with self.assertRaises(IMPORTER.ImportRejected):
                IMPORTER.require_absent(root, ["existing.json"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
