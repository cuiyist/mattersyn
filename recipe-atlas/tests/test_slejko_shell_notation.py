"""Slejko shell counts are monolayers, never chemical subscripts."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_atlas import material_alias_ids, slug

SOURCE = "chemmater2017-cdse-cald-7b01873"
VARIANTS = {
    "cds4-3p3": ("CdSe/CdS4", "CdSe/CdS", [("CdS", 4)]),
    "cds-zns-cds-zns-3p3": ("CdSe/CdS/ZnS/CdS/ZnS", "CdSe/CdS/ZnS", [("CdS", 1), ("ZnS", 1), ("CdS", 1), ("ZnS", 1)]),
    "cds2-zns2-3p3": ("CdSe/CdS2/ZnS2", "CdSe/CdS/ZnS", [("CdS", 2), ("ZnS", 2)]),
    "cds3-zns-3p8": ("CdSe/CdS3/ZnS", "CdSe/CdS/ZnS", [("CdS", 3), ("ZnS", 1)]),
    "zns-cds3-3p8": ("CdSe/ZnS/CdS3", "CdSe/ZnS/CdS", [("ZnS", 1), ("CdS", 3)]),
    "zns4-3p8": ("CdSe/ZnS4", "CdSe/ZnS", [("ZnS", 4)]),
    "cds2-zns-cds-3p8": ("CdSe/CdS2/ZnS/CdS", "CdSe/CdS/ZnS", [("CdS", 2), ("ZnS", 1), ("CdS", 1)]),
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class SlejkoShellNotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = load(ROOT / "data/reader-presentation-reviewed.json")
        cls.registry_dir = ROOT / "static/assets/chemical-registry"
        cls.registry = load(cls.registry_dir / "registry.json")
        cls.bindings = load(cls.registry_dir / "bindings.json")
        cls.contexts = load(cls.registry_dir / "product-contexts.json")

    def test_phase_formulas_and_ordered_monolayers(self):
        for suffix, (source, formula, layers) in VARIANTS.items():
            with self.subTest(suffix=suffix):
                rid = f"{SOURCE}-{suffix}"
                record = load(ROOT / "data/records" / f"{rid}.json")
                self.assertEqual(record["record_id"], rid)
                self.assertEqual(record["material"]["formula"], formula)
                self.assertNotRegex(formula, r"/(?:CdS|ZnS)\d")
                self.assertEqual(record["material"]["source_notation"], source)
                self.assertEqual(
                    record["material"]["shell_layers"],
                    [{"phase": phase, "monolayers": count} for phase, count in layers],
                )
                self.assertEqual(sum(count for _, count in layers), 4)
                self.assertEqual([p["sample_id"] for p in record["products"]], [suffix])
                self.assertEqual(record["products"][0]["composition"]["value"], formula)
                self.assertIn(source, record["products"][0]["source_sample_label"])
                self.assertIn("ML", record["title"])
                self.assertEqual(self.reader["records"][rid]["material_formula"], formula)
                self.assertIn("ML", self.reader["records"][rid]["title"])

    def test_registry_artwork_and_historical_urls(self):
        entries = {item["id"]: item for item in self.registry["entries"]}
        for suffix, (source, formula, layers) in VARIANTS.items():
            with self.subTest(suffix=suffix):
                rid = f"{SOURCE}-{suffix}"
                entry = entries[f"{SOURCE}-product-{suffix}"]
                self.assertEqual(entry["formula"], formula)
                self.assertIn(source, entry["aliases"])
                self.assertIn("ML", entry["name"])
                self.assertEqual(len(self.contexts["recordContexts"][rid]), 1)
                self.assertIn(source, self.contexts["recordContexts"][rid][0]["label"])
                record_path = ROOT / "data/records" / f"{rid}.json"
                self.assertEqual(
                    self.bindings["sourceRecordSha256"][rid],
                    hashlib.sha256(record_path.read_bytes()).hexdigest(),
                )
                asset = self.registry_dir / entry["svgPath"]
                svg = asset.read_text(encoding="utf-8")
                self.assertIn(source, svg)
                self.assertIn("source-named layers", svg)
                self.assertIn("ML", entry["caption"])
                self.assertEqual(entry["assetHashes"]["svgPath"], hashlib.sha256(asset.read_bytes()).hexdigest())
                self.assertIn(slug(source), material_alias_ids(formula))
                self.assertNotIn(slug(source), self.reader["materials"])
                self.assertIn(rid, self.reader["materials"][slug(formula)]["record_ids"])

    def test_figure_3b_remains_unassigned(self):
        review = load(ROOT / "data/paper-reviews" / f"{SOURCE}.json")
        figure = next(f for f in review["figures"] if f["id"] == "figure-3")
        self.assertIn("caption/prose shell identity conflict", figure["source_locators"][0])
        self.assertEqual(figure["record_links"], [f"{SOURCE}-cdse-core-3p8"])
        self.assertTrue(any("Figure 3B shell composition differs" in x for x in review["evidence_conflicts"]))
        for suffix in VARIANTS:
            rid = f"{SOURCE}-{suffix}"
            self.assertNotIn("figure-3", {f["id"] for f in self.reader["records"][rid]["figures"]})


if __name__ == "__main__":
    unittest.main()
