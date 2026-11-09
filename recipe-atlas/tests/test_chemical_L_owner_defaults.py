"""Finite late owner defaults; pure metadata, no lookup or coordinate I/O."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import chemical_L_identity as rules
import chemical_l4_reference as late


def entry(name,**fields):
    return {'id':'source','name':name,'formula':'','pubchemCid':None,
            'depictionKind':'formula',**fields}


def admitted_se():
    refid,sg,_=late.FIXED['Se']
    ref={'id':refid,'formula':'Se','spaceGroupNumber':sg,'referenceOnly':True,
         'trainingEligible':False,'defaultForSample':False,'modelPath':'models/Se.json',
         'modelSha256':'a'*64,'cifPath':'Se.cif','cifSha256':'b'*64}
    proof={'schema':'MatterSyn-L4-admitted-fixed-ambient-proof/1','formulas':{'Se':{
        'reference_id':refid,'formula':'Se','space_group_number':sg,
        'owner_authorized_ambient_default':True,'referenceOnly':True,'trainingEligible':False,
        'registry_path':late.REGISTRY,'registry_sha256':'c'*64,'registry_bytes':100,
        'model_path':late.PREFIX+ref['modelPath'],'model_sha256':'a'*64,'model_bytes':101,
        'cif_path':late.PREFIX+ref['cifPath'],'cif_sha256':'b'*64,'cif_bytes':102}}}
    return proof,[ref]


class OwnerDefaultTests(unittest.TestCase):
    def test_annotated_ODE_is_only_a_qualified_existing_reference(self):
        e=entry('Octadecene (ODE; positional isomer unspecified)',formula='C18H36')
        before=copy.deepcopy(e);plan=rules.plan_identity(e)
        self.assertEqual((plan['kind'],plan['ownerpart']),('single_compound','L3'))
        self.assertEqual(plan['lookups'][0]['preferred_reference_ids'],['1-octadecene'])
        self.assertEqual(plan['lookups'][0]['pubchemCid'],8217)
        self.assertEqual(plan['default_disclaimer'],rules.DEFAULT_LINE)
        self.assertTrue(rules.eligible_owner_scope(e,{'route':'flat','reason':'undefined_identity'},plan))
        self.assertEqual(e,before)

    def test_annotated_ODE_formula_CID_and_specimen_conflicts_stay_held(self):
        name='Octadecene (ODE; positional isomer unspecified)'
        for fields in [{'formula':'C18H38'},{'formula':'C18H36','pubchemCid':8058},
                       {'formula':'C18H36','depictionKind':'specimen'}]:
            with self.subTest(fields=fields):self.assertEqual(rules.plan_identity(entry(name,**fields))['kind'],'hold')
        for name in ['Octadecene (ODE; mixed isomers)','2-Octadecene','Octadecenes mixture']:
            self.assertNotEqual(rules.plan_identity(entry(name,formula='C18H36')).get('ownerpart'),'L3')

    def test_annotated_ODE_reuses_exact_model_and_preserves_default_qualification(self):
        e=entry('Octadecene (ODE; positional isomer unspecified)',formula='C18H36');plan=rules.plan_identity(e)
        target={'id':'1-octadecene','name':'1-Octadecene','formula':'C18H36','pubchemCid':8217,
                'model3dPath':'models/existing-ode.json','assetHashes':{'model3dPath':'a'*64},'caption':'Independent reference.','sourceUrls':[]}
        entries={target['id']:target};lookup=plan['lookups'][0]
        group={'lookup':lookup,'basis':'existing_registry','registry_id':target['id'],
               'reference':rules.registry_group_reference(lookup,target['id'],entries)}
        ref=rules.compose_L_reference(e,plan,[group]);proof={'schema':rules.SCHEMA,'entry_id':e['id'],
             'source_entry_sha256':rules.digest(e),'plan':plan,'groups':[group],'reference_sha256':rules.digest(ref)}
        self.assertEqual(rules.validate_L_reference(e,ref,proof,entries),[])
        self.assertEqual(ref['model3dPath'],target['model3dPath'])
        self.assertIn(rules.DEFAULT_LINE,ref['caption'])
        self.assertEqual(rules.field_default_qualification(e,ref)['qualification'],rules.DEFAULT_LINE)

    def test_exact_hexane_reader_annotation_uses_existing_H_identity(self):
        e=entry('Hexane: source isomer unspecified',formula='C6H14',depictionKind='symbolic_context')
        before=copy.deepcopy(e);p=rules.plan_identity(e)
        self.assertEqual((p['kind'],p['ownerpart']),('single_compound','L6'))
        self.assertEqual(p['lookups'][0]['preferred_reference_ids'],['hexane'])
        self.assertEqual(p['lookups'][0]['pubchemCid'],8058)
        self.assertEqual(p['default_disclaimer'],'')
        self.assertIsNone(rules.field_default_qualification(e,{}))
        self.assertTrue(rules.eligible_owner_scope(e,{'route':'flat','reason':'whole_context'},p))
        self.assertEqual(e,before)

    def test_actual_hexanes_isomer_and_mixture_evidence_are_not_fixed_aliases(self):
        for name in ['Hexanes: source isomer unspecified','Hexane isomer mixture',
                     'Hexane: source isomer unspecified; mixed isomers','2-methylpentane']:
            self.assertNotEqual(rules.plan_identity(entry(name,formula='C6H14')).get('reason'),'fixed_H_hexane_reference')
        for fields in [{'formula':'C6H12'},{'formula':'C6H14','pubchemCid':8217},
                       {'formula':'C6H14','caption':'A mixture of branched isomers.'},
                       {'formula':'C6H14','depictionKind':'mixture'}]:
            self.assertEqual(rules.plan_identity(entry('Hexane: source isomer unspecified',**fields))['kind'],'hold')

    def test_hexane_reuses_one_exact_model_without_coordinate_generation(self):
        e=entry('Hexane: source isomer unspecified',formula='C6H14',depictionKind='symbolic_context')
        p=rules.plan_identity(e);q=p['lookups'][0]
        target={'id':'hexane','name':'n-Hexane','formula':'C6H14','pubchemCid':8058,
                'model3dPath':'models/existing-hexane.json','assetHashes':{'model3dPath':'d'*64},'caption':'Independent reference.','sourceUrls':[]}
        g={'lookup':q,'basis':'existing_registry','registry_id':'hexane',
           'reference':rules.registry_group_reference(q,'hexane',{'hexane':target})}
        ref=rules.compose_L_reference(e,p,[g]);self.assertEqual(ref['model3dPath'],target['model3dPath'])
        self.assertNotIn(rules.DEFAULT_LINE,ref.get('caption',''))
        self.assertNotIn(rules.DEFAULT_LINE,ref.get('limitations',[]))

    def test_Se_powder_uses_the_same_admitted_ambient_elemental_reference(self):
        p,rows=admitted_se();e=entry('Se powder');before=copy.deepcopy(e)
        ref=late.l4_reference_for_entry(e,p,rows)
        self.assertEqual(ref['id'],'se-trigonal-cod-9012501')
        self.assertEqual(late.l4_name_proof(e,ref['id'])['source_entry_sha256'],rules.digest(e))
        self.assertTrue(late.validate_l4_reference_binding(e,ref['id'],p,rows))
        self.assertEqual(e,before)

    def test_Se_powder_does_not_bypass_context_phase_formula_or_admission(self):
        p,rows=admitted_se()
        for e in [entry('Se powder',formula='SeO2'),entry('Se powder',depictionKind='specimen'),
                  entry('Red Se powder'),entry('Black Se powder'),entry('Se powder stock'),
                  entry('Se powder',allotrope={'status':'reported','value':'red'})]:
            self.assertIsNone(late.l4_reference_for_entry(e,p,rows))
        self.assertIsNone(late.l4_reference_for_entry(entry('Se powder'),{},rows))

    def test_HAuCl4_uses_a_distinct_bounded_formula_as_name_query(self):
        e=entry('HAuCl4',formula='HAuCl4');before=copy.deepcopy(e);p=rules.plan_identity(e)
        self.assertEqual(p['ownerpart'],'L1');self.assertEqual(len(p['lookups']),1)
        q=p['lookups'][0];self.assertEqual((q['query_kind'],q['query_field'],q['query']),('name','chemical_name','HAuCl4'))
        self.assertIsNone(q['pubchemCid']);self.assertEqual(q['formula'],'HAuCl4')
        self.assertEqual(rules.normalized_lookup_entry(e,p)['name'],'Hydrogen tetrachloroaurate(III)')
        self.assertEqual(e,before)

    def test_HAuCl4_failed_or_conflicting_identity_does_not_become_a_reference(self):
        self.assertEqual(rules.plan_identity(entry('HAuCl4',formula='AuCl3'))['kind'],'hold')
        e=entry('HAuCl4',formula='HAuCl4');p=rules.plan_identity(e)
        self.assertTrue(rules.validate_L_reference(e,{},None,{}))
        self.assertFalse(rules.eligible_owner_scope(e,{'route':'flat','reason':'existing_chemistry_exclusion'},p))

    def test_dimethylcadmium_existing_disconnected_exclusion_is_untouched(self):
        e=entry('Dimethylcadmium',formula='C2H6Cd',pubchemCid=10479)
        self.assertTrue(rules.identity.requires_connected_molecule_reference(e))
        self.assertFalse(rules.eligible_owner_scope(e,{'route':'flat','reason':'existing_chemistry_exclusion'}))


    def test_exact_technical_oleylamine_annotation_uses_only_qualified_fixed_reference(self):
        name='Oleylamine; stereochemistry and technical composition unspecified'
        e=entry(name,formula='C18H37N');before=copy.deepcopy(e);p=rules.plan_identity(e)
        self.assertEqual((p['kind'],p['ownerpart']),('single_compound','L3'))
        self.assertEqual(p['lookups'][0]['preferred_reference_ids'],['oleylamine'])
        self.assertEqual(p['lookups'][0]['pubchemCid'],5356789)
        self.assertEqual(p['default_disclaimer'],rules.DEFAULT_LINE)
        self.assertEqual(e,before)
        for fields in [{'formula':'C18H39N'},{'formula':'C18H37N','pubchemCid':8058},
                       {'formula':'C18H37N','depictionKind':'mixture'},
                       {'formula':'C18H37N','depictionKind':'specimen'}]:
            with self.subTest(fields=fields):self.assertEqual(rules.plan_identity(entry(name,**fields))['kind'],'hold')
        self.assertNotEqual(rules.plan_identity(entry(name+' in TOP',formula='C18H37N')).get('ownerpart'),'L3')

if __name__=='__main__':unittest.main()
