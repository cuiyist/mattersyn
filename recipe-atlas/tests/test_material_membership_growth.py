"""Growing material collections still require exact canonical scientific membership."""
from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_quality import material_membership_errors

def row(rid,formula='PbS',components=None,collection='reviewed_literature'):
    return {'record_id':rid,'collection':collection,'record_type':'literature_protocol','reader_role':'synthesis_route',
            'quality':{'review_status':'source_reviewed','requested_tasks':[]},'operations':[{'stage':'synthesis'}],
            'material':{'formula':formula,'components':components or []},'lineage':{'source_group':rid},
            'sources':[{'id':rid,'doi':'10.fixture/'+rid}]}

def hub(rows):
    return {'formula':'PbS','record_ids':[r['record_id'] for r in rows],
            'direct_record_ids':[r['record_id'] for r in rows if r['material']['formula']=='PbS'],
            'paper_dois':['10.fixture/'+r['record_id'] for r in rows]}

class ExactCanonicalMembership(unittest.TestCase):
    def test_new_source_and_component_are_allowed_only_as_canonical(self):
        rr=[row('old'),row('new'),row('glass','PbS/glass',['PbS','glass'])]
        self.assertEqual([],material_membership_errors(hub(rr),rr))

    def test_missing_or_extra_route_is_rejected(self):
        rr=[row('old'),row('new')];h=hub(rr)
        for ids in [['old'],['old','new','invented']]:
            with self.subTest(ids=ids):
                bad=copy.deepcopy(h);bad['record_ids']=ids
                self.assertIn('PbS: complete canonical record_ids membership mismatch',material_membership_errors(bad,rr))

    def test_benchmark_context_unreviewed_and_nonsynthesis_cannot_enter(self):
        valid=row('valid')
        for field,value in [('collection','published_benchmark'),('reader_role','contextual_observation'),('record_type','observation'),('review_status','draft'),('operations',[{'stage':'analysis'}])]:
            bad=row('bad')
            if field=='review_status':bad['quality'][field]=value
            else:bad[field]=value
            with self.subTest(field=field):
                self.assertEqual([],material_membership_errors(hub([valid]),[valid,bad]))
                self.assertTrue(material_membership_errors(hub([valid,bad]),[valid,bad]))

    def test_component_cannot_become_direct(self):
        rr=[row('old'),row('glass','PbS/glass',['PbS'])];h=hub(rr);h['direct_record_ids'].append('glass')
        self.assertIn('PbS: complete canonical direct_record_ids membership mismatch',material_membership_errors(h,rr))

    def test_source_list_must_match_primary_dois_exactly(self):
        rr=[row('old')]
        for dois in [[],['10.fixture/old','10.fixture/unreviewed']]:
            h=hub(rr);h['paper_dois']=dois
            self.assertIn('PbS: complete canonical paper_dois membership mismatch',material_membership_errors(h,rr))

if __name__=='__main__':unittest.main()
