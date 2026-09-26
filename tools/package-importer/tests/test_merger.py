from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("private_additive_merger", HERE / "merger.py")
merger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merger)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def importer_path() -> Path:
    return Path(os.environ.get("MATTERSYN_IMPORTER_PATH", HERE / "importer.py"))


class AdditiveMergerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.checkout = self.root / "checkout"
        self.payload = self.root / "payload"
        self.checkout.mkdir()
        self.payload.mkdir()
        self.base_path = self.checkout / "recipe-atlas" / "data" / "materials.json"
        self.base_path.parent.mkdir(parents=True)
        self.base_bytes = json.dumps(
            {"materials": {"SiO2": {"route_ids": ["old"], "routes": [{"id": "old", "route": "kept"}], "existing": "keep"}}},
            separators=(",", ":"),
        ).encode()
        self.base_path.write_bytes(self.base_bytes)
        self.checkout_only = self.checkout / "README.md"
        self.checkout_only.write_text("untouched", encoding="utf-8")
        self.payload_file = self.payload / "reader" / "card.json"
        self.payload_file.parent.mkdir()
        self.payload_bytes = b'{"id":"card-1"}\n'
        self.payload_file.write_bytes(self.payload_bytes)
        self.contract = {
            "schema_version": "mattersyn-declarative-additive-merge/1",
            "base_commit": None,
            "base_files": {"recipe-atlas/data/materials.json": digest(self.base_bytes)},
            "create_files": [{
                "source": "reader/card.json", "target": "recipe-atlas/data/reader/card.json",
                "sha256": digest(self.payload_bytes), "bytes": len(self.payload_bytes),
            }],
            "json_operations": [],
        }

    def tearDown(self):
        self.temp.cleanup()

    def run_merge(self, contract=None, *, output_name="stage"):
        return merger.merge_plan(
            self.checkout, self.payload, contract or self.contract,
            self.root / output_name, importer_path(),
        )

    def op(self, kind, pointer, items, **extra):
        operation = {
            "op": kind, "target": "recipe-atlas/data/materials.json",
            "base_sha256": digest(self.base_bytes), "pointer": pointer, "items": items,
        }
        operation.update(extra)
        return operation

    def test_additive_existing_hub_and_create_only_file_preserve_prior_keys(self):
        before = self.base_path.read_bytes()
        contract = dict(self.contract)
        contract["json_operations"] = [
            self.op("add_keys", "/materials/SiO2", {"new_reader_ids": ["reader-1"]}),
            self.op("append_unique", "/materials/SiO2/routes", [{"id": "new", "route": "added"}], identity_keys=["id"]),
        ]
        result = self.run_merge(contract)
        merged_path = self.root / "stage" / "overlay" / "recipe-atlas" / "data" / "materials.json"
        merged = json.loads(merged_path.read_text(encoding="utf-8"))
        hub = merged["materials"]["SiO2"]
        self.assertEqual(hub["existing"], "keep")
        self.assertEqual(hub["route_ids"], ["old"])
        self.assertEqual(hub["routes"], [{"id": "old", "route": "kept"}, {"id": "new", "route": "added"}])
        self.assertEqual(hub["new_reader_ids"], ["reader-1"])
        self.assertEqual((self.root / "stage" / "overlay" / "recipe-atlas/data/reader/card.json").read_bytes(), self.payload_bytes)
        self.assertEqual(self.base_path.read_bytes(), before)
        self.assertFalse(result["publication_approved"])

    def test_identical_prior_item_is_idempotent(self):
        contract = dict(self.contract)
        contract["json_operations"] = [self.op("append_unique", "/materials/SiO2/routes", [{"id": "old", "route": "kept"}], identity_keys=["id"])]
        result = self.run_merge(contract)
        merged = json.loads((self.root / "stage/overlay/recipe-atlas/data/materials.json").read_text())
        self.assertEqual(len(merged["materials"]["SiO2"]["routes"]), 1)
        self.assertEqual(result["operations"][0]["identical_prior_items"], 1)

    def test_add_keys_collision_rejected(self):
        contract = dict(self.contract)
        contract["json_operations"] = [self.op("add_keys", "/materials/SiO2", {"existing": "overwrite"})]
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_append_unique_identity_collision_rejected(self):
        contract = dict(self.contract)
        contract["json_operations"] = [self.op("append_unique", "/materials/SiO2/routes", [{"id": "old", "route": "different"}], identity_keys=["id"])]
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_append_unique_distinguishes_boolean_from_integer(self):
        self.base_bytes = json.dumps(
            {"materials": {"SiO2": {"routes": [{"id": "typed", "value": True}]}}},
            separators=(",", ":"),
        ).encode()
        self.base_path.write_bytes(self.base_bytes)
        contract = dict(self.contract)
        contract["base_files"] = {"recipe-atlas/data/materials.json": digest(self.base_bytes)}
        contract["json_operations"] = [self.op("append_unique", "/materials/SiO2/routes", [{"id": "typed", "value": 1}], identity_keys=["id"])]
        contract["json_operations"][0]["base_sha256"] = digest(self.base_bytes)
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_append_unique_accepts_object_key_order_only_difference(self):
        self.base_bytes = json.dumps(
            {"materials": {"SiO2": {"routes": [{"id": "ordered", "metadata": {"a": 1, "b": 2}}]}}},
            separators=(",", ":"),
        ).encode()
        self.base_path.write_bytes(self.base_bytes)
        contract = dict(self.contract)
        contract["base_files"] = {"recipe-atlas/data/materials.json": digest(self.base_bytes)}
        contract["json_operations"] = [self.op("append_unique", "/materials/SiO2/routes", [{"id": "ordered", "metadata": {"b": 2, "a": 1}}], identity_keys=["id"])]
        contract["json_operations"][0]["base_sha256"] = digest(self.base_bytes)
        result = self.run_merge(contract)
        self.assertEqual(result["operations"][0]["identical_prior_items"], 1)

    def test_bad_pointer_rejected(self):
        contract = dict(self.contract)
        contract["json_operations"] = [self.op("add_keys", "/materials/missing", {"x": 1})]
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_stale_base_hash_rejected(self):
        contract = dict(self.contract)
        contract["base_files"] = {"recipe-atlas/data/materials.json": "0" * 64}
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_stale_git_commit_rejected(self):
        subprocess.run(["git", "init", str(self.checkout)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "commit", "-m", "base"], check=True, capture_output=True)
        contract = dict(self.contract)
        contract["base_commit"] = "0" * 40
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_tampered_payload_rejected(self):
        self.payload_file.write_bytes(b"tampered")
        with self.assertRaises(merger.MergeRejected):
            self.run_merge()

    def test_unlisted_payload_rejected(self):
        (self.payload / "unlisted.txt").write_text("extra", encoding="utf-8")
        with self.assertRaises(merger.MergeRejected):
            self.run_merge()

    def test_traversal_rejected(self):
        contract = dict(self.contract)
        contract["create_files"] = [dict(self.contract["create_files"][0], source="../escape.json")]
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_release_registry_is_not_automatically_merged(self):
        contract = dict(self.contract)
        contract["create_files"] = [dict(self.contract["create_files"][0], target="publication/asset-rights-registry.json")]
        with self.assertRaises(merger.MergeRejected):
            self.run_merge(contract)

    def test_output_inside_checkout_rejected(self):
        with self.assertRaises(merger.MergeRejected):
            merger.merge_plan(self.checkout, self.payload, self.contract, self.checkout / "stage", importer_path())


if __name__ == "__main__":
    unittest.main()
