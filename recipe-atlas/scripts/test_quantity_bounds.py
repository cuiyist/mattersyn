import unittest
from copy import deepcopy
from record_helpers import qty,record,source,ev,operation
from dataset_lib import validate_record,fmt,training_view,chemical_signature

class QuantityBounds(unittest.TestCase):
 def make(self,q):
  r=record('bounds-test','Bound test','CdSe','test','test',source('s','10.0/test','test','test',2000),'p1')
  r['schema_version']='1.3.0';r['operations']=[operation('inject','inject','Inject',ev('s','p1'),[],[],parameters={'duration':q})]
  return r
 def test_strict_upper_bound_roundtrip(self):
  q=qty(unit='s',maximum=.1,maximum_exclusive=True,evidence=ev('s','p1'))
  r=self.make(q)
  self.assertEqual(validate_record(r),[]);self.assertEqual(fmt(q),'<0.1 s')
  self.assertIsNone(q['value']);self.assertEqual(q['status'],'reported')
  exported=training_view(r,'partial_protocol')['output']['operations'][0]['parameters']['duration']
  self.assertTrue(exported['maximum_exclusive']);self.assertEqual(exported['maximum'],.1);self.assertIsNone(exported['value'])
 def test_lower_bound_and_closed_range(self):
  q=qty(unit='min',minimum=1,evidence=ev('s','p1'))
  self.assertEqual(validate_record(self.make(q)),[]);self.assertEqual(fmt(q),'≥1 min')
  self.assertEqual(fmt(qty(unit='s',minimum=1,maximum=2,evidence=ev('s','p1'))),'1–2 s')
 def test_ambiguous_empty_and_dangling_bounds_rejected(self):
  for kw in [dict(value=1,maximum=2),dict(minimum=2,maximum=1),dict(minimum=1,maximum=1,maximum_exclusive=True),dict(value=1,maximum_exclusive=True)]:
   self.assertTrue(validate_record(self.make(qty(unit='s',evidence=ev('s','p1'),**kw))))
 def test_bounds_distinguish_recipe_signatures(self):
  r=self.make(qty(unit='s',maximum=.1,maximum_exclusive=True,evidence=ev('s','p1')))
  closed=deepcopy(r);closed['operations'][0]['parameters']['duration']['maximum_exclusive']=False
  self.assertNotEqual(chemical_signature(r),chemical_signature(closed))

if __name__=='__main__':unittest.main()
