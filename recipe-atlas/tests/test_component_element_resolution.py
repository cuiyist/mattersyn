"""Exact direct-material identities resolve acronym components without order dependence."""
from pathlib import Path
import contextlib,copy,io,json,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_atlas

def record(rid,formula,elements,components,role='synthesis_route'):
    return {'record_id':rid,'title':rid,'collection':'reviewed_literature','record_type':'literature_protocol',
            'reader_role':role,'method':'fixture','quality':{'review_status':'source_reviewed','requested_tasks':[]},
            'operations':[{'stage':'synthesis'}],'material':{'formula':formula,'elements':elements,'components':components,'architecture':'composite' if '/' in formula else 'single_material'},
            'lineage':{'source_group':'fixture-source'},'sources':[{'id':'fixture-source','doi':'10.fixture/component','url':'https://doi.org/10.fixture/component','title':'Synthetic fixture','year':2000}]}

def host(rid='host'):
    return record(rid,'Mg-Al-LDH',['Mg','Al','O','H','N'],['Mg-Al-LDH'])

def composite(rid='composite'):
    return record(rid,'CdTe/Mg-Al-LDH',['Cd','Te','Mg','Al','O','H','N'],['CdTe','Mg-Al-LDH'])

class ComponentElementResolution(unittest.TestCase):
    def capture(self,records):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);folder=root/'data/records';folder.mkdir(parents=True)
            for r in records:(folder/(r['record_id']+'.json')).write_text(json.dumps(r),encoding='utf-8')
            outputs={}
            with patch.object(build_atlas,'ROOT',root),patch.object(build_atlas,'write',lambda p,v:outputs.__setitem__(p.name,copy.deepcopy(v))),contextlib.redirect_stdout(io.StringIO()):
                build_atlas.main()
            return outputs

    def test_two_dong_composite_memberships_resolve(self):
        records=[host('nitrate-ldh'),composite('qd-dbs-ldh'),composite('qd-no3-ldh')]
        h=self.capture(records)[build_atlas.slug('Mg-Al-LDH')+'.json']
        self.assertEqual(['nitrate-ldh','qd-dbs-ldh','qd-no3-ldh'],h['record_ids'])
        self.assertEqual(['nitrate-ldh'],h['direct_record_ids'])
        self.assertFalse(h['component_only'])
        self.assertEqual(['component_of_product_system']*2,[r['contribution_role'] for r in h['records'] if r['record_id']!='nitrate-ldh'])

    def test_composite_filename_before_direct_material(self):
        h=self.capture([composite('aaa-composite'),host('zzz-direct')])[build_atlas.slug('Mg-Al-LDH')+'.json']
        self.assertEqual(['aaa-composite','zzz-direct'],h['record_ids'])
        self.assertEqual(['zzz-direct'],h['direct_record_ids'])
        self.assertEqual({'Mg','Al','O','H','N'},set(h['elements']))

    def test_element_index_is_order_independent(self):
        a=host('a');b=host('b');b['material']['elements']=['Mg','Al','O','H','C','S']
        forward=build_atlas.direct_material_element_index([a,b,composite()])
        backward=build_atlas.direct_material_element_index([composite(),b,a])
        self.assertEqual(forward,backward)
        self.assertEqual({'Mg','Al','O','H','N','C','S'},set(forward['Mg-Al-LDH']))

    def test_context_does_not_authorize_component_identity(self):
        r=host();r['reader_role']='contextual_observation'
        index=build_atlas.direct_material_element_index([r])
        self.assertEqual({},index)
        self.assertEqual([],build_atlas.component_elements('Mg-Al-LDH',index))

    def test_unknown_invalid_component_not_admitted(self):
        r=record('only-composite','CdTe/X-HOST',['Cd','Te'],['CdTe','X-HOST'])
        outputs=self.capture([r])
        self.assertNotIn(build_atlas.slug('X-HOST')+'.json',outputs)
        self.assertEqual([],build_atlas.component_elements('X-HOST',{}))

    def test_invalid_direct_elements_still_fail(self):
        r=host();r['material']['elements']=['Mg','Al','L','D','H']
        with self.assertRaisesRegex(ValueError,'needs an explicit valid element list'):
            build_atlas.direct_material_element_index([r])

    def test_existing_formula_and_named_reference_precedence(self):
        self.assertEqual(['Cd','Te'],build_atlas.component_elements('CdTe',{'CdTe':['C']}))
        self.assertEqual(['C'],build_atlas.component_elements('MWNT',{}))

if __name__=='__main__':unittest.main()
