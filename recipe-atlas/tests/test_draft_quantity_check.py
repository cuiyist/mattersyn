from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from draft_quantity_check import check_scalar_quote

class DraftQuantityChecks(unittest.TestCase):
 def test_volume_must_not_become_molar_amount(self):
  quote='Add 1.8 mL (5 mmol) of reagent.'
  self.assertEqual('numeric_unit_span_not_supported',check_scalar_quote(1.8,'mmol',quote,quote)['status'])
  self.assertEqual('numeric_unit_span_supported',check_scalar_quote(5,'mmol',quote,quote)['status'])
 def test_fabricated_quote_is_rejected(self):
  self.assertEqual('quote_not_in_page',check_scalar_quote(1.8,'mmol','1.8 mmol','1.8 mL (5 mmol)')['status'])
 def test_numeric_substrings_do_not_match(self):
  self.assertEqual('numeric_unit_span_not_supported',check_scalar_quote(1,'mmol','11 mmol','11 mmol')['status'])
 def test_unit_case_and_prefix_remain_meaningful(self):
  self.assertEqual('numeric_unit_span_not_supported',check_scalar_quote(2,'L','2 mL','2 mL')['status'])
  self.assertEqual('unit_not_supported',check_scalar_quote(2,'M','2 m','2 m')['status'])
 def test_string_null_is_not_numeric(self):
  self.assertEqual('invalid_numeric_type',check_scalar_quote('null','min','','')['status'])
  result=check_scalar_quote(None,'min','','')
  self.assertEqual('missing_value_unverified',result['status'])
  self.assertFalse(result['source_absence_verified'])
 def test_unicode_micro_and_degree_are_supported(self):
  self.assertEqual('numeric_unit_span_supported',check_scalar_quote(20,'uL','20 µL','20 μL')['status'])
  self.assertEqual('numeric_unit_span_supported',check_scalar_quote(200,'degC','200 °C','200 °C')['status'])
 def test_success_does_not_approve_context(self):
  result=check_scalar_quote(5,'mmol','5 mmol','5 mmol')
  self.assertFalse(result['scientific_approval'])
