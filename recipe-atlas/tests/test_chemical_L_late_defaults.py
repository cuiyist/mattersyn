"""Finite own-name/default regressions. Synthetic inputs only; no network/models."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import chemical_l4_reference as late
import chemical_L_identity as rules
from formula_equivalence import formula_equivalent


def entry(name='Sulfur',**kw):return {'id':'source','name':name,'formula':'S','depictionKind':'formula',**kw}
def admitted(formula='CdO'):
    rid,sg,_=late.FIXED[formula]
    c={'id':rid,'formula':formula,'spaceGroupNumber':sg,'referenceOnly':True,'trainingEligible':False,'defaultForSample':False,'modelPath':'models/reference.json','modelSha256':'a'*64,'cifPath':'cif/reference.cif','cifSha256':'b'*64}
    p={'schema':'MatterSyn-L4-admitted-fixed-ambient-proof/1','formulas':{formula:{'reference_id':rid,'formula':formula,'space_group_number':sg,'owner_authorized_ambient_default':True,'referenceOnly':True,'trainingEligible':False,'registry_path':late.REGISTRY,'registry_sha256':'c'*64,'registry_bytes':100,'model_path':late.PREFIX+c['modelPath'],'model_sha256':c['modelSha256'],'model_bytes':101,'cif_path':late.PREFIX+c['cifPath'],'cif_sha256':c['cifSha256'],'cif_bytes':102}}}
    return p,[c]


def s8_group(e):
    p=late.s8_plan_for_entry(e)
    ref={'route':'molecule_reference','reason':'validated_connectivity_computed_conformer','id':'s8-reference','name':'Cyclooctasulfur','formula':'S8','model3dPath':'models/s8-reference.json','model3dSha256':'a'*64,'caption':'Computed illustrative conformer, not measured and not PubChem3D.','referenceOnly':True,'trainingEligible':False,'sourceUrls':[]}
    g={'lookup':p['lookups'][0],'basis':'pubchem_metadata','reference':ref,'evidence':{'query_type':'name','query':'Cyclooctasulfur','status':'UNIQUE_CID_CONNECTIVITY_CANDIDATE','cid':12345,'formula':'S8','connectivity_smiles':'S1SSSSSSS1','cache_sha256':'b'*64,'source_url':'https://pubchem.ncbi.nlm.nih.gov/compound/12345'}}
    result=late.compose_s8_reference(e,p,[g]);proof={'schema':late.S8_SCHEMA,'entry_id':e['id'],'source_entry_sha256':rules.digest(e),'plan':p,'groups':[g],'reference_sha256':rules.digest(result)}
    return result,proof


class CleanedAmbientTests(unittest.TestCase):
    def test_purity_supplier_and_roman_cleanup_preserves_originals(self):
        for name,formula in [('Cadmium ii oxide (99%, Sigma-Aldrich)','CdO'),('Selenium, 99.99%','Se'),('Selenium99.99%','Se')]:
            e=entry(name,formula=formula);before=copy.deepcopy(e);p,rows=admitted(formula)
            result=late.l4_reference_for_entry(e,p,rows);self.assertIsNotNone(result);self.assertEqual(e,before)
            proof=late.l4_name_proof(e,result['id']);self.assertEqual(proof['source_entry_sha256'],rules.digest(e));self.assertEqual(proof['reported_name'],name);self.assertTrue(proof['transformations'])
            self.assertTrue(late.validate_l4_reference_binding(e,result['id'],p,rows))
    def test_original_context_and_phase_guard_precedes_cleanup(self):
        p,rows=admitted()
        for e in [entry('Cadmium oxide, 99%, nanoparticle specimen',formula='CdO'),entry('Cadmium oxide stock (99%)',formula='CdO'),entry('Cadmium oxide (99%)',formula='CdO',depictionKind='mixture'),entry('Cadmium oxide (99%)',formula='CdO',phase={'status':'reported','value':'other form'})]:
            self.assertIsNone(late.l4_reference_for_entry(e,p,rows))
    def test_formula_conflict_and_common_polymorphs_stay_held(self):
        p,rows=admitted()
        self.assertIsNone(late.l4_reference_for_entry(entry('Cadmium oxide99%',formula='CdSe'),p,rows))
        for name,formula in [('Lead oxide, 99%','PbO'),('Titanium dioxide, 99%','TiO2'),('Zinc sulfide, 99%','ZnS')]:self.assertIsNone(late.l4_reference_for_entry(entry(name,formula=formula),p,rows))
    def test_name_proof_is_exact_not_a_substitute_for_admission(self):
        p,rows=admitted();e=entry('Cadmium oxide (99%)',formula='CdO');proof=late.l4_name_proof(e,rows[0]['id']);self.assertIsNotNone(proof)
        self.assertIsNone(late.l4_name_proof(e,'wrong-reference'));self.assertIsNone(late.l4_reference_for_entry(e,{},rows))


class SulfurReferenceTests(unittest.TestCase):
    def test_owner_S8_reference_preserves_atomic_source_formula_and_CID(self):
        e=entry('Sulfur (99.99%)',pubchemCid=5362482);before=copy.deepcopy(e);p=late.s8_plan_for_entry(e);dto=late.s8_lookup_entry(e,p)
        self.assertEqual(dto['formula'],'S8');self.assertIsNone(dto['pubchemCid']);self.assertEqual(e,before)
        self.assertFalse(formula_equivalent('S','S8'));self.assertEqual(p['reported_formula'],'S')
        ref,proof=s8_group(e);self.assertEqual(late.validate_s8_reference(e,ref,proof,{}),[]);self.assertIn('not a measured sample',ref['caption']);self.assertFalse(ref['trainingEligible'])
    def test_only_literal_unqualified_elemental_names_are_selected(self):
        for name in ['S','S8','Sulfur','Sulphur powder','Elemental sulfur, 99%']:self.assertIsNotNone(late.s8_plan_for_entry(entry(name)))
        for e in [entry('Sulfur in TOP'),entry('Sulfur stock'),entry('Sulfur nanoparticles'),entry('Sulfur',depictionKind='specimen'),entry('Polymeric sulfur'),entry('Sulfur',formula='SO4'),entry('Sulfur',allotrope={'status':'reported','value':'polymeric'})]:self.assertIsNone(late.s8_plan_for_entry(e))
    def test_metadata_must_be_one_neutral_eight_sulfur_ring(self):
        e=entry();ref,proof=s8_group(e)
        for key,value in [('formula','S'),('connectivity_smiles','SSSSSSSS'),('connectivity_smiles','S.S.S.S.S.S.S.S'),('connectivity_smiles','[S+]1SSSSSSS1'),('query','Sulfur'),('status','AMBIGUOUS_OR_NO_CID')]:
            bad=copy.deepcopy(proof);bad['groups'][0]['evidence'][key]=value;self.assertTrue(late.validate_s8_reference(e,ref,bad,{}))
    def test_source_and_reference_pins_cannot_change(self):
        e=entry();ref,proof=s8_group(e)
        for key,value in [('source_entry_sha256','f'*64),('reference_sha256','e'*64)]:
            bad=copy.deepcopy(proof);bad[key]=value;self.assertTrue(late.validate_s8_reference(e,ref,bad,{}))
        for key,value in [('trainingEligible',True),('model3dSha256','c'*64),('caption','Measured structure')]:
            bad=copy.deepcopy(ref);bad[key]=value;self.assertTrue(late.validate_s8_reference(e,bad,proof,{}))
    def test_exact_existing_S8_reference_reuses_model_bytes_by_pin(self):
        e=entry();p=late.s8_plan_for_entry(e);t={'id':'S8-reference','name':'Cyclooctasulfur','formula':'S8','pubchemCid':12345,'model3dPath':'models/existing-S8.json','assetHashes':{'model3dPath':'a'*64},'caption':'Existing independent reference.','sourceUrls':[]};entries={t['id']:t}
        group={'lookup':p['lookups'][0],'basis':'existing_registry','registry_id':t['id'],'reference':rules.registry_group_reference(p['lookups'][0],t['id'],entries)}
        ref=late.compose_s8_reference(e,p,[group]);proof={'schema':late.S8_SCHEMA,'entry_id':e['id'],'source_entry_sha256':rules.digest(e),'plan':p,'groups':[group],'reference_sha256':rules.digest(ref)}
        self.assertEqual(late.validate_s8_reference(e,ref,proof,entries),[]);self.assertEqual(ref['model3dPath'],t['model3dPath']);self.assertEqual(t['formula'],'S8')


class SulfurQualityHookTests(unittest.TestCase):
    def exercise(self,mutate=None):
        from chemical_reference_quality import check_chemical_reference_overlay
        e=entry();ref,proof=s8_group(e);ref.update(chemicalUseCount=1,buttonLabel='Rotate 3D ↗');registry={'entries':[e]};bindings={'recordBindings':{'fixture':{'m':e['id']}}}
        class Audit:
            def __init__(self):self.checked=[];self.counts={};self.assets=[]
            def check(self,ok,label):self.checked.append((bool(ok),label));return bool(ok)
            def asset(self,base,path,digest,label):self.assets.append(path);return None
        with tempfile.TemporaryDirectory(prefix='S8-proof-',dir=Path(__file__).parent)as tmp:
            base=Path(tmp)
            for name,value in [('registry.json',registry),('bindings.json',bindings)]: (base/name).write_text(json.dumps(value),encoding='utf-8')
            sha=lambda name:hashlib.sha256((base/name).read_bytes()).hexdigest()
            overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':sha('registry.json'),'originalBindingsSha256':sha('bindings.json'),'entries':{e['id']:ref}}
            overlay['lSulfurProofs']={'schema':late.S8_SCHEMA,'originalRegistrySha256':overlay['originalRegistrySha256'],'originalBindingsSha256':overlay['originalBindingsSha256'],'entries':{e['id']:proof}}
            if mutate:mutate(overlay)
            a=Audit();check_chemical_reference_overlay(a,base,registry,bindings,overlay);return a
    def test_explicit_S8_proof_keeps_all_normal_model_asset_gates(self):
        a=self.exercise();self.assertEqual([x for ok,x in a.checked if not ok],[]);self.assertEqual(a.assets,['models/s8-reference.json'])
    def test_missing_S8_proof_retains_the_original_unqualified_form_hold(self):
        a=self.exercise(lambda o:o.pop('lSulfurProofs'));self.assertTrue(any('unqualified form requires'in text for ok,text in a.checked if not ok))
    def test_S8_proof_does_not_weaken_other_model_flags(self):
        a=self.exercise(lambda o:o['entries']['source'].update(trainingEligible=True));self.assertTrue([x for ok,x in a.checked if not ok])


if __name__=='__main__':unittest.main()
