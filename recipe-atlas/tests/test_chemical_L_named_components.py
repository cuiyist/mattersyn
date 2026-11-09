"""Synthetic pure tests: no Source writes, network, assets or model generation."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import chemical_L_identity as rules


def entry(name,**kw):
    return {'id':'target','name':name,'formula':None,'pubchemCid':None,
            'depictionKind':'formula',**kw}


def proof(entry,groups):
    plan=rules.plan_identity(entry);ref=rules.compose_L_reference(entry,plan,groups)
    return ref,{'schema':rules.SCHEMA,'entry_id':entry['id'],
                'source_entry_sha256':rules.digest(entry),'plan':plan,'groups':groups,
                'reference_sha256':rules.digest(ref)}


def sources():
    return {rules.EXISTING_OLEATE_SOURCE['id']:copy.deepcopy(rules.EXISTING_OLEATE_SOURCE)}


class NamedAcetateTests(unittest.TestCase):
    def test_exact_named_aliases_and_reported_bytes_preserved(self):
        for name,forms in [('cadmium acetate',['CdOAc2','Cd(Ac)2','Cd(OAc)2','CdAc2']),
                           ('Indium acetate',['In(Ac)3','InOAc3','In(OAc)3','InAc3'])]:
            for formula in forms:
                with self.subTest(name=name,formula=formula):
                    e=entry(name,formula=formula);before=copy.deepcopy(e)
                    p=rules.plan_identity(e)
                    self.assertEqual(p['ownerpart'],'L2')
                    self.assertEqual(p['reported_formula'],formula)
                    self.assertEqual(p['lookups'][0]['reference_component_formula'],'C2H3O2-')
                    self.assertEqual(e,before)

    def test_hydrate_is_component_scope_only(self):
        e=entry('Cadmium acetate dihydrate',formula='CdOAc2·2H2O')
        self.assertEqual(rules.plan_identity(e)['ownerpart'],'L2')
        self.assertFalse(rules._formula_ok(e,'Cd(C2H3O2)2',hydrate=False))
        self.assertFalse(rules.formula_equivalent('CdOAc2','Cd(C2H3O2)2'))

    def test_wrong_metal_count_and_cid_remain_held(self):
        for formula in ['CdOAc3','In(Ac)3','Ca(Ac)2','Cd(Ac)2Cl','CdCl2']:
            self.assertEqual(rules.plan_identity(entry('Cadmium acetate',formula=formula))['kind'],'hold')
        self.assertEqual(rules.plan_identity(entry('Indium acetate',formula='Cd(Ac)2'))['kind'],'hold')
        self.assertEqual(rules.plan_identity(entry('Cadmium acetate',formula='CdOAc2',pubchemCid=123))['kind'],'hold')

    def test_formula_alias_without_named_identity_is_not_acetate(self):
        for name in ['CdOAc2','In(Ac)3','unknown acetate','Cadmium chloride']:
            p=rules.plan_identity(entry(name,formula='CdOAc2'))
            self.assertNotEqual(p.get('ownerpart'),'L2')

    def test_existing_acetate_group_omits_parent_multiplicity_and_water(self):
        e=entry('Indium acetate',formula='In(Ac)3');lookup=rules.plan_identity(e)['lookups'][0]
        parent={'id':'cadmium-acetate-dihydrate','name':'Cadmium acetate dihydrate',
                'component3dModels':[{'id':'acetate','formula':'C2H3O2-',
                    'model3dPath':'models/acetate.json','model3dSha256':'a'*64,
                    'caption':'Existing independent acetate reference.',
                    'multiplicityInReferenceFormula':2},
                    {'id':'water','formula':'H2O','model3dPath':'models/water.json',
                     'model3dSha256':'b'*64,'caption':'Water reference.'}]}
        entries={parent['id']:parent}
        g={'lookup':lookup,'basis':'existing_registry','registry_id':parent['id'],
           'reference':rules.registry_group_reference(lookup,parent['id'],entries)}
        ref,p=proof(e,[g]);self.assertEqual(rules.validate_L_reference(e,ref,p,entries),[])
        self.assertEqual(len(ref['component3dModels']),1)
        self.assertNotIn('multiplicityInReferenceFormula',ref['component3dModels'][0])
        self.assertEqual(ref['component3dModels'][0]['formula'],'C2H3O2-')


class ExistingOleateTests(unittest.TestCase):
    def stock(self,name='Lead oleate stock',**kw):
        return entry(name,**kw)

    def test_exact_existing_group_and_normal_validation(self):
        e=self.stock(formula='C36H66O4Pb',pubchemCid=6435829)
        q=rules.plan_identity(e)['lookups'][0];g=rules.existing_named_component_group(q,sources())
        self.assertEqual(g['basis'],'existing_named_component')
        ref,p=proof(e,[g]);self.assertEqual(rules.validate_L_reference(e,ref,p,sources()),[])
        self.assertEqual(len(ref['component3dModels']),1)
        c=ref['component3dModels'][0]
        self.assertEqual(c['model3dSha256'],'9ca1e70d48a3aca580ebe0dfc4805712db856707e10b2d64627b4b763b28b0b2')
        self.assertEqual(c['formula'],'C18H33O2-')
        self.assertNotIn('multiplicityInReferenceFormula',c)
        self.assertNotIn('pubchemCid',c)
        self.assertIn('solution speciation',ref['component3dScope'])

    def test_stock_with_ode_reuses_two_independent_groups(self):
        e=self.stock('Cadmium oleate in ODE; solution speciation unresolved')
        p=rules.plan_identity(e);self.assertEqual(p['ownerpart'],'L5')
        self.assertEqual([q['name']for q in p['lookups']],['Oleate ion','1-Octadecene'])
        group=rules.existing_named_component_group(p['lookups'][0],sources())
        solvent={'lookup':p['lookups'][1],'basis':'fixture',
                 'reference':{'route':'molecule_reference','id':'1-octadecene',
                 'formula':'C18H36','model3dPath':'models/ode.json',
                 'model3dSha256':'c'*64,'caption':'Independent solvent reference.',
                 'referenceOnly':True,'trainingEligible':False,'sourceUrls':[]}}
        ref=rules.compose_L_reference(e,p,[group,solvent])
        self.assertEqual([c['formula']for c in ref['component3dModels']],['C18H33O2-','C18H36'])
        self.assertTrue(ref['referenceOnly']);self.assertFalse(ref['trainingEligible'])

    def test_other_ions_formula_cid_and_source_constraints_cannot_use_pin(self):
        q=rules.plan_identity(self.stock())['lookups'][0]
        for field,value in [('name','Oleic acid'),('formula','C18H34O2'),
                            ('reference_component_formula','C18H33O2'),('pubchemCid',123),
                            ('preferred_reference_ids',['another-parent']),('source_cid_constraint',123)]:
            bad=copy.deepcopy(q);bad[field]=value
            self.assertIsNone(rules.existing_named_component_group(bad,sources()))
        self.assertIsNone(rules.existing_named_component_group(None,sources()))

    def test_source_identity_change_missing_or_conflicting_rejected(self):
        q=rules.plan_identity(self.stock())['lookups'][0]
        with self.assertRaises(ValueError):rules.existing_named_component_group(q,{})
        for key,value in [('name','Cadmium oleate nanoparticles'),('formula','C18H34O2'),('pubchemCid',123)]:
            entries=sources();entries[rules.EXISTING_OLEATE_SOURCE['id']][key]=value
            with self.assertRaises(ValueError):rules.existing_named_component_group(q,entries)

    def test_modified_model_evidence_or_composed_scope_rejected(self):
        e=self.stock();q=rules.plan_identity(e)['lookups'][0]
        for mutate in [lambda g:g['reference']['component3dModels'][0].update(model3dSha256='d'*64),
                       lambda g:g['reference']['component3dModels'][0].update(formula='Pb'),
                       lambda g:g['evidence'].update(model_bytes=1)]:
            g=rules.existing_named_component_group(q,sources());mutate(g)
            if g['reference']['component3dModels'][0]['formula']=='Pb':
                with self.assertRaises(ValueError):proof(e,[g])
            else:
                ref,p=proof(e,[g]);self.assertTrue(rules.validate_L_reference(e,ref,p,sources()))

    def test_each_call_returns_independent_values(self):
        q=rules.plan_identity(self.stock())['lookups'][0]
        one=rules.existing_named_component_group(q,sources());one['reference']['component3dModels'][0]['formula']='wrong'
        two=rules.existing_named_component_group(q,sources())
        self.assertEqual(two['reference']['component3dModels'][0]['formula'],'C18H33O2-')

    def test_existing_stock_and_specimen_holds_preserved(self):
        for e in [self.stock('Cadmium oleate nanoparticles in ODE'),
                  self.stock('Unspecified lead stock'),
                  self.stock(formula='PbCl2')]:
            self.assertEqual(rules.plan_identity(e)['kind'],'hold')




class ExistingAuCl4Tests(unittest.TestCase):
    def target(self):
        return entry('HAuCl4',id='wang2005-lss-nature03968-metal-salt-au',formula='HAuCl4')

    def parent(self):
        return {rules.EXISTING_AUCL4_SOURCE['id']:copy.deepcopy(rules.EXISTING_AUCL4_SOURCE)}

    def test_literal_plan_uses_one_existing_component_without_proton_water_or_count(self):
        e=self.target();q=rules.plan_identity(e)['lookups'][0]
        self.assertEqual(q['query'],'HAuCl4')
        g=rules.existing_named_component_group(q,self.parent());ref,p=proof(e,[g])
        self.assertEqual(rules.validate_L_reference(e,ref,p,self.parent()),[])
        self.assertEqual(g['evidence']['accepted_reference_sha256'],'11b7a611c48dfff525cf47ef714043ef112b2a42a0fb4f7720912198fa842631')
        self.assertEqual(g['evidence']['model_bytes'],2930)
        self.assertEqual(len(ref['component3dModels']),1)
        c=ref['component3dModels'][0]
        self.assertEqual(c['formula'],'AuCl4-')
        self.assertEqual(c['model3dSha256'],'06f986fadfb4f7363cb1c87bf2eb305f078cd791adfe5be738db37191a3327e5')
        self.assertNotIn('multiplicityInReferenceFormula',c)
        self.assertNotIn('pubchemCid',c)
        self.assertIn('No proton, water',ref['component3dScope'])
        self.assertTrue(ref['referenceOnly']);self.assertFalse(ref['trainingEligible'])

    def test_conflicting_query_formula_cid_and_allowed_route_rejected(self):
        q=rules.plan_identity(self.target())['lookups'][0]
        for key,value in [('name','Gold chloride'),('formula','AuCl3'),('query','Gold trichloride'),
                          ('pubchemCid',123),('source_cid_constraint',123),
                          ('allowed_routes',['molecule_reference']),('id','a-different-component')]:
            bad=copy.deepcopy(q);bad[key]=value
            self.assertIsNone(rules.existing_named_component_group(bad,self.parent()))

    def test_missing_conflicting_parent_identity_cannot_supply_group(self):
        q=rules.plan_identity(self.target())['lookups'][0]
        with self.assertRaises(ValueError):rules.existing_named_component_group(q,{})
        for key,value in [('name','Gold chloride'),('formula','AuCl3'),('pubchemCid',21863413),('depictionKind','specimen')]:
            p=self.parent();p[rules.EXISTING_AUCL4_SOURCE['id']][key]=value
            with self.assertRaises(ValueError):rules.existing_named_component_group(q,p)

    def test_water_model_changed_hash_and_count_cannot_be_imported_via_valid_digest(self):
        e=self.target();q=rules.plan_identity(e)['lookups'][0]
        for mutate in [lambda g:g['reference']['component3dModels'].append({'formula':'H2O'}),
                       lambda g:g['reference']['component3dModels'][0].update(multiplicityInReferenceFormula=1),
                       lambda g:g['reference']['component3dModels'][0].update(model3dSha256='e'*64),
                       lambda g:g['evidence'].update(accepted_reference_sha256='e'*64)]:
            g=rules.existing_named_component_group(q,self.parent());mutate(g)
            ref,p=proof(e,[g])
            self.assertTrue(rules.validate_L_reference(e,ref,p,self.parent()))

    def test_own_target_and_protected_inputs_stay_unchanged(self):
        e=self.target();p=rules.plan_identity(e);before=copy.deepcopy([e,p,self.parent()])
        rules.existing_named_component_group(p['lookups'][0],self.parent())
        self.assertEqual([e,p,self.parent()],before)
        for bad in [entry('HAuCl4',formula='AuCl3'),entry('HAuCl4',formula='HAuCl4',depictionKind='specimen')]:
            self.assertEqual(rules.plan_identity(bad)['kind'],'hold')

    def test_oleate_group_is_byte_equal_to_frozen_pre_au_successor(self):
        # Frozen pre-Au helper output, retained as a portable regression pin.
        q=rules.plan_identity(entry('Lead oleate stock'))['lookups'][0]
        self.assertEqual(rules.digest(rules.existing_named_component_group(q,sources())),
                         '1b2a38325924ea81a7df4c1f495afe7a14e2997792a6e200bba17e6f8850ec84')

    def test_normalized_full_name_and_formula_query_both_use_same_exact_component(self):
        formula=self.target()
        normalized=entry('Hydrogen tetrachloroaurate(III)',id='henkel-gold',formula='HAuCl4')
        groups=[]
        for e,query in [(formula,'HAuCl4'),(normalized,'Hydrogen tetrachloroaurate(III)')]:
            q=rules.plan_identity(e)['lookups'][0];self.assertEqual(q['query'],query)
            g=rules.existing_named_component_group(q,self.parent());ref,p=proof(e,[g])
            self.assertEqual(rules.validate_L_reference(e,ref,p,self.parent()),[])
            groups.append(g)
        self.assertEqual(groups[0]['reference'],groups[1]['reference'])
        self.assertEqual(groups[0]['evidence'],groups[1]['evidence'])



class HexaneWordingTests(unittest.TestCase):
    def test_only_H6_alias_loses_L3_default_disclaimer(self):
        e=entry('Hexane: source isomer unspecified',formula='C6H14')
        plan=rules.plan_identity(e)
        self.assertEqual(plan['ownerpart'],'L6')
        self.assertEqual(plan['default_disclaimer'],'')
        self.assertIsNone(rules.field_default_qualification(e))
        group={'lookup':plan['lookups'][0],'reference':{'route':'molecule_reference',
               'referenceOnly':True,'trainingEligible':False,'formula':'C6H14',
               'caption':'Existing fixed H6 n-hexane reference.',
               'model3dPath':'models/hexane.json','model3dSha256':'a'*64}}
        ref=rules.compose_L_reference(e,plan,[group])
        self.assertNotIn(rules.DEFAULT_LINE,ref.get('caption',''))
        self.assertNotIn(rules.DEFAULT_LINE,ref.get('limitations',[]))
        self.assertEqual(rules.plan_identity(entry('ODE',formula='C18H36'))['default_disclaimer'],rules.DEFAULT_LINE)


if __name__=='__main__':unittest.main()
