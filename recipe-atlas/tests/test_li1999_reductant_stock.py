"""Li 1999 reductant must be a typed input in each published route."""
import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "li1999-ag-dbs-jcis5879"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class Li1999ReductantStockTests(unittest.TestCase):
    def test_reductant_stock_is_prepared_and_consumed(self):
        reader = read(ROOT / "data/reader-presentation-reviewed.json")
        bindings = read(ROOT / "static/assets/chemical-registry/bindings.json")
        for suffix, dbs in [("no-dbs", False), ("dbs-fresh", True), ("dbs-aged-3mo", True)]:
            with self.subTest(suffix=suffix):
                rid = f"{SOURCE}-{suffix}"
                record_path = ROOT / "data/records" / f"{rid}.json"
                record = read(record_path)
                stock = next(s for s in record["stocks"] if s["id"] == "reductant-stock")
                operation = next(o for o in record["operations"] if o["id"] == "prepare-reductant-stock")
                reduction = next(o for o in record["operations"] if o["id"] == "reduce-silver")

                self.assertEqual(stock["preparation_operation_ids"], [operation["id"]])
                self.assertEqual(operation["outputs"], ["reductant-stock-state"])
                self.assertIn("reductant-stock-state", reduction["inputs"])
                self.assertIn(operation["id"], reduction["depends_on"])
                self.assertEqual(set(operation["inputs"]), {"hydrazine", "distilled-water"} | ({"dbs"} if dbs else set()))
                self.assertEqual(operation["parameters"]["hydrazine_concentration"]["value"], 1.0)
                self.assertEqual(operation["parameters"]["hydrazine_concentration"]["unit"], "M")
                self.assertEqual("dbs_concentration" in operation["parameters"], dbs)
                if dbs:
                    self.assertEqual(operation["parameters"]["dbs_concentration"]["value"], 0.01)
                    self.assertEqual(operation["parameters"]["dbs_concentration"]["unit"], "M")
                self.assertIn("charges, solution volume", operation["description"])
                self.assertEqual(operation["environment"]["status"], "not_reported")
                self.assertTrue(all(not component["quantities"] for component in stock["components"]))

                digest = hashlib.sha256(record_path.read_bytes()).hexdigest()
                self.assertEqual(bindings["sourceRecordSha256"][rid], digest)
                self.assertEqual(reader["records"][rid]["source"]["input_sha256"], digest)


if __name__ == "__main__":
    unittest.main()
