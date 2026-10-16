"""Invented metadata fixtures only; no builder, dataset or filesystem mutation."""
import ast, copy, json, re, sys, unicodedata, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def converter():
    tree=ast.parse((HERE.parents[1]/'tools/simple-pipeline/to_site.py').read_bytes())
    nodes=[x for x in tree.body if isinstance(x,(ast.Assign,ast.FunctionDef,ast.ClassDef))]
    env=dict(json=json,re=re,sys=sys,unicodedata=unicodedata,Path=Path)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'candidate pure converter AST','exec'),env)
    return env

def quality():
    tree=ast.parse((HERE.parent/'scripts/check_quality.py').read_bytes())
    names={'primary_doi','hub_publication_status_matches','material_membership_errors','germanium_reviewed_regression_checks'}
    nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
    nodes += [x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HEATH_GE_SI_ROUTES' for t in x.targets)]
    env={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'candidate pure quality AST','exec'),env)
    return env
C=converter();Q=quality();HEATH=Q['HEATH_GE_SI_ROUTES'];NEW='synthetic-source-extracted-embedded-ge'

def pair(label='nanocrystalline Ge embedded in SiO2'):
    return {'product':label,'structure':{},'recipe':{'steps':[{'action':'heat'}]}}

def converted(p):
    doc={'id':'fixture','doi':'10.fixture/embedded','authors':'Fixture Author','year':'2000'}
    return C['Builder'](doc).record(p,1)

def record(rid,formula,components,architecture,status='source_reviewed'):
    return {'record_id':rid,'collection':'reviewed_literature','record_type':'literature_protocol','reader_role':'synthesis_route',
            'quality':{'review_status':status,'requested_tasks':[]},'operations':[{'stage':'synthesis'}],
            'material':{'formula':formula,'components':components,'architecture':architecture},
            'lineage':{'source_group':rid},'sources':[{'id':rid,'doi':'10.1021/jp951903v' if rid in HEATH else '10.fixture/embedded'}]}

def fixtures(extra=True):
    rows=[record(r,'Ge/Si',['Ge','Si'],'heterostructure') for r in sorted(HEATH)]
    if extra:rows.append(record(NEW,'Ge/SiO2',['Ge','SiO2'],'composite','source_extracted'))
    hub={'formula':'Ge','component_only':True,'record_ids':[x['record_id'] for x in rows],'direct_record_ids':[],
         'paper_dois':sorted({x['sources'][0]['doi'] for x in rows}),'publication_status':'verified_synthesis_contribution'}
    return rows,hub

class ProductEmbedding(unittest.TestCase):
    def test_named_missing_composition_is_material_composite(self):
        p=pair();before=copy.deepcopy(p);r=converted(p)
        self.assertEqual(r['material'],{'formula':'Ge/SiO2','family':'Ge/SiO2 nanocrystals','elements':['Ge','Si','O'],'components':['Ge','SiO2'],'architecture':'composite'})
        self.assertEqual(p,before)
    def test_no_reported_fact_filled(self):
        p=pair();r=converted(p)
        self.assertIsNone(r['products'][0]['composition']['value']);self.assertEqual(r['products'][0]['composition']['status'],'not_reported')
        self.assertIsNone(r['intended_target']['composition']['value']);self.assertEqual(r['products'][0]['source_sample_label'],p['product'])
        self.assertEqual(r['quality']['review_status'],'source_extracted');self.assertEqual(r['structure_assets'],[])
    def test_bare_ge_is_not_reclassified(self):
        r=converted(pair('nanocrystalline Ge'));self.assertEqual(r['material']['formula'],'Ge');self.assertEqual(r['material']['architecture'],'single_material')
    def test_unknown_host_not_guessed(self):
        self.assertIsNone(C['_embedded_product_formula'](pair('nanocrystalline Ge embedded in unknown glass')))
    def test_other_chemistry_not_covered(self):
        for s in ['nanocrystalline GeO2 embedded in SiO2','Ge embedded in Si','Ge implanted in SiO2','SiO2 embedded in Ge']:
            self.assertIsNone(C['_embedded_product_formula'](pair(s)))
    def test_explicit_component_fact_preserved_during_named_navigation(self):
        p=pair();p['structure']['composition']={'value':'Ge','page':1};before=copy.deepcopy(p);r=converted(p)
        self.assertEqual(r['material']['formula'],'Ge/SiO2')
        self.assertEqual(r['products'][0]['composition']['value'],'Ge')
        self.assertEqual(r['intended_target']['composition']['value'],'Ge')
        self.assertEqual(p,before)
    def test_formula_case_is_exact(self):
        self.assertIsNone(C['_embedded_product_formula'](pair('nanocrystalline ge embedded in SiO2')))
    def test_word_case_only_is_flexible(self):
        self.assertEqual(C['_embedded_product_formula'](pair('Nanocrystalline Ge Embedded In SiO2')),'Ge/SiO2')
    def test_unrelated_grouped_formula_unchanged(self):
        self.assertEqual(C['_composition_from']({'product':'sample','structure':{'composition':{'value':'Ti(BO3)2'}}}),'Ti(BO3)2')

    def test_named_dutta_variant_with_explicit_component_fact(self):
        p=pair('Ge nanocrystal embedded in SiO2 matrix');p['structure']['composition']={'value':'Ge','page':1};before=copy.deepcopy(p);r=converted(p)
        self.assertEqual(r['material'],{'formula':'Ge/SiO2','family':'Ge/SiO2 nanocrystals','elements':['Ge','Si','O'],'components':['Ge','SiO2'],'architecture':'composite'})
        self.assertEqual(r['products'][0]['source_sample_label'],p['product'])
        self.assertEqual(r['products'][0]['composition']['value'],'Ge');self.assertEqual(p,before)
    def test_other_explicit_composition_not_overridden_by_label(self):
        for value in ['GeO2','Ge/Si','SiO2']:
            p=pair('Ge nanocrystal embedded in SiO2 matrix');p['structure']['composition']={'value':value,'page':1}
            self.assertIsNone(C['_embedded_product_formula'](p));self.assertEqual(converted(p)['material']['formula'],value)
    def test_generic_device_label_does_not_guess_a_host(self):
        p=pair('Ge quantum dot tunneling diode');r=converted(p)
        self.assertEqual(r['material']['formula'],'Ge');self.assertEqual(r['material']['components'],['Ge'])
        self.assertIsNone(C['_embedded_product_formula'](p))
    def test_word_variants_do_not_make_formula_case_insensitive(self):
        self.assertEqual(C['_embedded_product_formula'](pair('Ge nanocrystals embedded in SiO2 matrix')),'Ge/SiO2')
        self.assertIsNone(C['_embedded_product_formula'](pair('Ge nanocrystal embedded in sio2 matrix')))

class GermaniumScope(unittest.TestCase):
    def setUp(self):self.rows,self.hub=fixtures();self.byid={x['record_id']:x for x in self.rows}
    def checks(self):return [ok for ok,_ in Q['germanium_reviewed_regression_checks'](self.hub,self.byid)]
    def test_embedded_component_passes(self):self.assertTrue(all(self.checks()))
    def test_original_reviewed_only_hub_passes(self):
        rows,hub=fixtures(False);self.assertTrue(all(ok for ok,_ in Q['germanium_reviewed_regression_checks'](hub,{x['record_id']:x for x in rows})))
    def test_complete_independent_membership_passes(self):self.assertEqual(Q['material_membership_errors'](self.hub,self.rows),[])
    def test_other_named_extracted_component_allowed(self):
        self.byid[NEW]['material']={'formula':'Ge/ZnS','components':['Ge','ZnS'],'architecture':'unresolved'};self.assertTrue(all(self.checks()))
    def test_isolated_extracted_ge_rejected(self):
        self.byid[NEW]['material']={'formula':'Ge','components':['Ge'],'architecture':'single_material'};self.hub['direct_record_ids']=[NEW];self.hub['component_only']=False
        self.assertFalse(self.checks()[0]);self.assertFalse(self.checks()[3]);self.assertTrue(Q['material_membership_errors'](self.hub,self.rows)==[])
    def test_falsely_hiding_isolated_direct_ge_rejected(self):
        self.byid[NEW]['material']={'formula':'Ge','components':['Ge'],'architecture':'single_material'};self.assertFalse(self.checks()[3]);self.assertTrue(Q['material_membership_errors'](self.hub,self.rows))
    def test_heath_cannot_become_direct(self):self.hub['direct_record_ids']=[sorted(HEATH)[0]];self.assertFalse(self.checks()[0])
    def test_missing_heath_rejected(self):self.hub['record_ids'].remove(sorted(HEATH)[0]);self.assertFalse(self.checks()[1])
    def test_heath_review_status_cannot_degrade(self):self.byid[sorted(HEATH)[0]]['quality']['review_status']='source_extracted';self.assertFalse(self.checks()[1])
    def test_new_extracted_route_cannot_become_reviewed(self):self.byid[NEW]['quality']['review_status']='source_reviewed';self.assertFalse(self.checks()[1])
    def test_unknown_route_rejected(self):self.hub['record_ids'].append('unknown');self.assertFalse(self.checks()[2])
    def test_draft_route_rejected(self):self.byid[NEW]['quality']['review_status']='draft';self.assertFalse(self.checks()[2])
    def test_component_must_have_host(self):self.byid[NEW]['material']['components']=['Ge'];self.assertFalse(self.checks()[3])
    def test_component_must_not_be_single_material(self):self.byid[NEW]['material']['architecture']='single_material';self.assertFalse(self.checks()[3])
    def test_cannot_hide_new_component_from_hub(self):self.hub['record_ids'].remove(NEW);self.assertTrue(Q['material_membership_errors'](self.hub,self.rows))
    def test_legacy_formula_erasure_still_rejected(self):
        self.byid[sorted(HEATH)[0]]['material']['formula']='Ge';self.assertTrue(Q['material_membership_errors'](self.hub,self.rows))
    def test_unknown_review_status_never_looks_reviewed(self):
        self.byid[NEW]['quality']['review_status']='structured_data_verified';self.assertFalse(self.checks()[2])

if __name__=='__main__':unittest.main(verbosity=2)
