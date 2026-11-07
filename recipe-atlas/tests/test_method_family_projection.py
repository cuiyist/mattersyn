"""Focused projection tests; no files from the corpus are read."""
import copy,importlib.util,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import method_family_projection as m

class ProjectionTest(unittest.TestCase):
 def test_compact_projection_retains_every_variant_without_diagnostics_or_duplicate_lists(self):
  original={'record_count':3,'default_record_id':'r1','diagnostics_record_counts':{'private_build_only':2},'families':[{'id':'f','kind':'synthesis','label':'Own route - own sources','paper_count':2,'record_ids':['r1','r2','r3'],'papers':[{'citation':'Alpha et al. (2000)','record_ids':['r1','r2'],'paper_key':'doi:one'},{'citation':'Beta (2001)','record_ids':['r3'],'paper_key':'doi:two'}]}]}
  before=copy.deepcopy(original);out=m.compact_method_families(original)
  self.assertEqual(out['families'][0]['papers'][0]['record_ids'],['r1','r2']);self.assertEqual(original,before)
  self.assertNotIn('diagnostics_record_counts',out);self.assertNotIn('record_ids',out['families'][0]);self.assertNotIn('paper_key',out['families'][0]['papers'][0])
 def test_duplicate_variant_rejected(self):
  with self.assertRaises(AssertionError):m.compact_method_families({'record_count':2,'default_record_id':'r1','families':[{'id':'f','kind':'other','label':'Other methods','paper_count':1,'papers':[{'citation':'Alpha','record_ids':['r1','r1']}]}]})
 def test_empty_material_has_null_default(self):
  self.assertEqual(m.compact_method_families({'record_count':0,'default_record_id':None,'families':[]})['families'],[])

class ProcessingLabelTest(unittest.TestCase):
 def test_processing_names_the_material_without_changing_classification_or_membership(self):
  original={'material_formula':'CdSe','record_count':1,'default_record_id':'r1','families':[{'id':'p','kind':'processing','label':'Processing of material','paper_count':1,'papers':[{'citation':'Own author','record_ids':['r1']}]}]};before=copy.deepcopy(original)
  result=m.compact_method_families(original);self.assertEqual(result['families'][0]['label'],'Processing of CdSe');self.assertEqual(original,before);self.assertEqual(result['families'][0]['kind'],'processing')
if __name__=='__main__':unittest.main(verbosity=2)
