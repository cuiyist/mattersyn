"""Inventory display categories must account for the complete canonical set."""
from pathlib import Path
import json,unittest
class InventoryCategoryTotals(unittest.TestCase):
 def test_displayed_categories_partition_records(self):
  data=json.loads((Path(__file__).resolve().parents[1]/'data/inventory-summary.json').read_bytes());s=data['summary']
  keys=['synthesis_route_variant_records','contextual_control_variant_records','shared_preparation_workup_characterization_assay_procedures','contextual_observation_records','reviewed_literature_experimental_rows','published_benchmark_rows']
  self.assertEqual(s['canonical_records'],sum(s[k] for k in keys),'Displayed inventory categories omit or duplicate records')
  self.assertEqual(s['contextual_control_variant_records'],sum(p['contextual_control_count'] for p in data['per_paper']))
