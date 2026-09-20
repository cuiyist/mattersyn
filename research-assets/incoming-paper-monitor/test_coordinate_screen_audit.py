"""Independent coordinate-ranking/cache checks with synthetic local fixtures."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import screen_corpus as s


TABLE = "Atomic coordinates\nx y z\nZn1 0.0123(4) 0.2345(6) 0.3456(7)"


class CoordinateScreenAuditTests(unittest.TestCase):
    def features(self, text, sha="a" * 64):
        return s.text_features(text, sha)

    def scope(self, texts):
        ledger = {"current_paper": None, "current_batch": None, "groups": {"paper": {
            "generation": 2, "queue_order": 7, "first_seen_at": "saved-arrival",
            "order_basis": "saved-order", "review": {"status": "queued"}, "needs_recheck": False}}}
        documents = []
        for index, text in enumerate(texts):
            digest = hashlib.sha256(text.encode()).hexdigest()
            features = self.features(text, digest)
            documents.append({"group_id": "paper", "sha256": digest, "features": features,
                              "status": "text_screened_candidate", "source_unchanged_from_snapshot": True,
                              "text_characters_screened": features["all_text_characters_examined"],
                              "file_key": "source-" + str(index), "role_candidate": "main" if index == 0 else "si",
                              "role_ambiguous": False, "manual_flags": []})
        return s.rank_scopes(ledger, documents)[0][0]

    def test_uncontextualized_numeric_table_gets_16_point_candidate_bonus(self):
        scope = self.scope([TABLE])
        self.assertEqual(scope["structure_score"], 16)
        self.assertEqual(scope["feature_counts"].get("coordinate_data"), 1)
        self.assertEqual(scope["sample_join_status"], "unverified_no_cross_source_or_cross_specimen_join")
        self.assertFalse(scope["terminal_review_status_assigned"])

    def test_optimized_cartesian_table_gets_3_point_contextual_bonus(self):
        text = TABLE.replace("Atomic coordinates", "Optimized Cartesian coordinates")
        scope = self.scope([text])
        self.assertEqual(scope["structure_score"], 3)
        self.assertEqual(scope["feature_counts"].get("contextual_coordinate_data"), 1)
        self.assertFalse(scope["feature_counts"].get("coordinate_data"))
        self.assertEqual(scope["feature_counts"].get("computed_or_reference_coordinate_context"), 1)

    def test_molecular_or_precursor_table_does_not_get_full_coordinate_bonus(self):
        for context in ("Molecular complex", "Precursor", "Reagent"):
            with self.subTest(context=context):
                scope = self.scope([context + "\n" + TABLE])
                self.assertEqual(scope["structure_score"], 3)
                self.assertEqual(scope["feature_counts"].get("molecular_or_precursor_context_product_link_unknown"), 1)
                self.assertFalse(scope["feature_counts"].get("coordinate_data"))

    def test_heo_positional_thermal_occupancy_heading_and_rows_detected(self):
        text = "\n\n--- PAGE 4 ---\n\nTABLE 2: Positional, Thermal, and Occupancy Parameters\natom x y z Ueq Occupancy\nIn1 0.0145(2) 0.2637(4) 0.5034(5) 0.027(3) 1.0"
        features = self.features(text)
        self.assertEqual(features["counts"].get("coordinate_data"), 1)
        snippet = features["coordinate_context_snippets"][0]
        self.assertEqual(snippet["page"], 4)
        self.assertIn("coordinate_numeric_table_candidate", snippet["categories"])
        self.assertIn("coordinate_product_sample_link_unverified", snippet["categories"])

    def test_coordinate_mention_without_axes_or_values_gets_only_2_points(self):
        for text in ("Atomic coordinates are reported in the supporting information.",
                     "Atomic coordinates\nx y z\nRefer to the deposited table.",
                     "Atomic coordinates were measured at 0.100 0.200 0.300 units."):
            with self.subTest(text=text):
                scope = self.scope([text])
                self.assertEqual(scope["structure_score"], 2)
                self.assertEqual(scope["feature_counts"].get("coordinate_mention"), 1)
                self.assertFalse(scope["feature_counts"].get("coordinate_data"))

    def test_numeric_table_requires_at_least_three_values(self):
        scope = self.scope(["Atomic coordinates\nx y z\nZn1 0.125 0.250"])
        self.assertEqual(scope["structure_score"], 2)
        self.assertFalse(scope["feature_counts"].get("coordinate_data"))

    def test_integer_cif_coordinates_are_valid_numeric_values(self):
        text = "loop_\n_atom_site_label\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\nZn1 0 0 0"
        scope = self.scope([text])
        self.assertEqual(scope["structure_score"], 16)
        self.assertEqual(scope["feature_counts"].get("coordinate_data"), 1)

    def test_same_source_named_precursor_warning_preserves_source_and_page(self):
        text = "\n\n--- PAGE 1 ---\n\nThe precursor Zn(SPh)2 was isolated.\n\n--- PAGE 8 ---\n\nZn(SPh)2\n" + TABLE
        features = self.features(text, "b" * 64)
        self.assertEqual(features["counts"].get("contextual_coordinate_data"), 1)
        self.assertEqual(features["counts"].get("same_source_named_precursor_context_association"), 1)
        snippet = features["coordinate_context_snippets"][0]
        self.assertEqual(snippet["page"], 8)
        association = snippet["context_associations"][0]
        self.assertEqual(association["name"], "Zn(SPh)2")
        self.assertEqual(association["source_sha256"], "b" * 64)
        self.assertEqual(association["text_block"], "PAGE 1")
        self.assertIn("not_verified_identity", association["association"])
        self.assertFalse(features["verified_sample_join"])

    def test_precursor_warning_does_not_cross_documents_in_same_group(self):
        scope = self.scope(["The precursor Zn(SPh)2 was isolated.", "Zn(SPh)2\n" + TABLE])
        self.assertEqual(scope["structure_score"], 16)
        self.assertFalse(scope["feature_counts"].get("same_source_named_precursor_context_association"))
        self.assertFalse(scope["feature_counts"].get("contextual_coordinate_data"))
        self.assertEqual(scope["sample_join_status"], "unverified_no_cross_source_or_cross_specimen_join")

    def test_precursor_formula_prefix_does_not_match_different_formula(self):
        text = "\n\n--- PAGE 1 ---\n\nThe precursor Zn(SPh)2 was isolated.\n\n--- PAGE 8 ---\n\nZn(SPh)20\n" + TABLE
        features = self.features(text)
        self.assertFalse(features["counts"].get("same_source_named_precursor_context_association"))
        self.assertEqual(features["counts"].get("coordinate_data"), 1)

    def test_old_feature_cache_recomputed_from_raw_text_without_source_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            source.write_bytes(b"source-byte-identity-fixture")
            source_bytes = source.read_bytes()
            digest = hashlib.sha256(source_bytes).hexdigest()
            raw_text = root / "cached-text.txt"
            raw_text.write_text(TABLE.replace("Atomic coordinates", "Optimized Cartesian coordinates"), encoding="utf-8")
            output = root / "screen"
            cache_path = output / "cache/content" / (digest + ".json")
            cache_path.parent.mkdir(parents=True)
            cache_path.write_text(json.dumps({"version": "corpus-priority-screen-1.0", "sha256": digest,
                "text_path": str(raw_text), "extraction": {"extraction_status": "extracted", "detected_format": "pdf", "page_results": []},
                "features": {"counts": {"coordinate_data": 999}, "all_text_characters_examined": 1}}), encoding="utf-8")
            s.initialize_worker({}, str(output))
            task = {"source_path": str(source), "snapshot_signature": s.signature(source),
                    "snapshot_sha256": digest, "role_ambiguous": False}
            with patch.object(s, "extract_source", side_effect=AssertionError("Source parser must not run")) as parser:
                result = s.screen_document(task)
            parser.assert_not_called()
            self.assertEqual(result["status"], "text_screened_candidate")
            self.assertEqual(result["cache_source"], "screen_raw_text_feature_recomputed")
            self.assertTrue(result["hash_computed"])
            self.assertEqual(result["features"]["counts"].get("contextual_coordinate_data"), 1)
            self.assertFalse(result["features"]["counts"].get("coordinate_data"))
            self.assertEqual(json.loads(cache_path.read_text(encoding="utf-8"))["version"], s.VERSION)
            self.assertEqual(source.read_bytes(), source_bytes)


if __name__ == "__main__":
    unittest.main()
