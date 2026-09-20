"""Reader publication must not accidentally admit training data or contextual records."""
import copy,json,unittest
from pathlib import Path
from build_atlas import synthesis_route
from dataset_lib import eligibility,validate_record
ROOT=Path(__file__).resolve().parents[1]
class ReaderRoleTests(unittest.TestCase):
 def setUp(self):
  self.route=json.loads((ROOT/'data/records/heo-2003-in66-route.json').read_bytes())
 def test_reviewed_conflicted_route_can_be_visible_without_training(self):
  self.assertTrue(synthesis_route(self.route))
  self.assertEqual(self.route['quality']['requested_tasks'],[])
  self.assertFalse(any(v['eligible'] for v in eligibility(self.route).values()))
  self.assertEqual(validate_record(self.route),[])
 def test_role_does_not_override_other_review_and_synthesis_gates(self):
  for field,value in [('collection','published_benchmark'),('record_type','procedure')]:
   r=copy.deepcopy(self.route);r[field]=value;self.assertFalse(synthesis_route(r))
  r=copy.deepcopy(self.route);r['quality']['review_status']='imported_unreviewed';self.assertFalse(synthesis_route(r))
  r=copy.deepcopy(self.route);r['operations']=[];self.assertFalse(synthesis_route(r))
 def test_unadmitted_context_is_not_a_reader_route(self):
  r=copy.deepcopy(self.route);r.pop('reader_role');self.assertFalse(synthesis_route(r))
  for p in (ROOT/'data/records').glob('heo-2003-*.json'):
   r=json.loads(p.read_bytes())
   self.assertEqual(synthesis_route(r),r['record_id']=='heo-2003-in66-route')
 def test_legacy_classifications_unchanged(self):
  records=[json.loads(p.read_bytes()) for p in (ROOT/'data/records').glob('*.json')]
  # Future separately reviewed reader admissions are intentional; exercise the
  # unchanged fallback only for legacy records without that explicit field.
  records=[r for r in records if 'reader_role' not in r and not r['record_id'].startswith('heo-2003-')]
  self.assertGreaterEqual(len(records),470)
  for r in records:
   old=(r['collection']=='reviewed_literature' and r['record_type']!='procedure' and r['quality']['review_status']=='source_reviewed' and 'precursor_selection' in r['quality']['requested_tasks'] and any(o['stage']=='synthesis' for o in r['operations']))
   self.assertEqual(synthesis_route(r),old,r['record_id'])
if __name__=='__main__':unittest.main()
