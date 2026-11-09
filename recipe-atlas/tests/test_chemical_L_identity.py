"""Small synthetic tests only; no canonical record loop/assets/network/RDKit."""
import copy
import pathlib
import sys
import hashlib
import json
import tempfile
import unittest
from unittest import mock

D=pathlib.Path(__file__).parent
sys.path.insert(0,str(D.parent/'scripts'))
import chemical_L_identity as rules
from formula_equivalence import formula_equivalent


def source(name,**kw):
    return {'id':'source','name':name,'formula':None,'depictionKind':'formula','model3dPath':None,**kw}


def molecule(eid,name,formula,cid=None):
    return {'id':eid,'name':name,'formula':formula,'pubchemCid':cid,'model3dPath':'models/'+eid+'.json',
            'assetHashes':{'model3dPath':'a'*64},'caption':'Independent illustrative reference; not measured.',
            'sourceUrls':[]}


def component(eid,formula):
    return {'id':eid,'name':formula+' independent component','formula':formula,
            'model3dPath':'models/'+eid+'.json','model3dSha256':'b'*64,
            'caption':'Independent ion; no relative component geometry.'}


def proof_for(entry,groups):
    plan=rules.plan_identity(entry);ref=rules.compose_L_reference(entry,plan,groups)
    return ref,{'schema':rules.SCHEMA,'entry_id':entry['id'],'source_entry_sha256':rules.digest(entry),
                'plan':plan,'groups':groups,'reference_sha256':rules.digest(ref)}


class NormalizationTests(unittest.TestCase):
    def test_finite_qualifier_normalization_does_not_change_input(self):
        e=source('Anhydrous indium iii acetate (99.99%, Sigma-Aldrich)');before=copy.deepcopy(e)
        p=rules.plan_identity(e);self.assertEqual(p['ownerpart'],'L2');self.assertEqual(p['lookups'][0]['formula'],'C2H3O2-');self.assertEqual(e,before)

    def test_trailing_abbreviation_is_removed_but_stereo_and_oxidation_preserved(self):
        self.assertEqual(rules.clean_name('9-Borabicyclononane thiol (BBN-SH)')[0],'9-Borabicyclononane thiol')
        self.assertEqual(rules.clean_name('Indium (III) acetate')[0],'Indium (III) acetate')
        self.assertEqual(rules.clean_name('Compound (R)')[0],'Compound (R)')

    def test_concentration_and_supplier_are_not_a_formula_rewrite(self):
        e=source('0.1 M Copper nitrate, Alfa Aesar',formula='Cu(NO3)2');p=rules.plan_identity(e)
        self.assertEqual(p['lookups'][0]['name'],'Copper nitrate');self.assertEqual(e['formula'],'Cu(NO3)2')

    def test_fixed_unique_formula_names_only(self):
        for formula,name in [('InCl3','Indium(III) chloride'),('HAuCl4','Hydrogen tetrachloroaurate(III)'),('PbBr2','Lead(II) bromide')]:
            p=rules.plan_identity(source(formula,depictionKind='symbolic_context'))
            self.assertEqual(p['lookups'][0]['name'],name);self.assertEqual(p['lookups'][0]['formula'],formula)
        for value in ['SiOx','Cd(Ac)2','Co','CO']:
            self.assertEqual(rules.plan_identity(source(value))['kind'],'hold')

    def test_formula_name_conflict_remains_hold(self):
        self.assertEqual(rules.plan_identity(source('PbBr2',formula='PbCl2'))['kind'],'hold')

    def test_TOP_Se_is_an_exact_owner_alias_not_a_bond_inference(self):
        self.assertEqual(rules.plan_identity(source('TOP-Se'))['lookups'][0]['name'],'Trioctylphosphine selenide')
        self.assertEqual(rules.plan_identity(source('top-se'))['lookups'][0]['name'],'Trioctylphosphine selenide')
        separate=rules.plan_identity(source('TOP and selenium stock'))
        self.assertEqual([q['name']for q in separate['lookups']],['Trioctylphosphine','selenium'])
        self.assertNotIn('Trioctylphosphine selenide',[q['name']for q in separate['lookups']])

    def test_room_phase_or_specimen_is_not_normalized_away(self):
        for e in [source('CdSe cores'),source('Gold nanoparticles'),source('Wafer'),source('Precursor formulation not restated'),source('CdO',depictionKind='specimen')]:
            self.assertEqual(rules.plan_identity(e)['kind'],'hold')

    def test_original_unfixed_abbreviations_still_hold(self):
        for name in ['DDT','DDAB','TDPA','mixed isomers','hexanes']:
            self.assertEqual(rules.plan_identity(source(name))['kind'],'hold')

    def test_normalized_DTO_is_minimal_and_rejects_mutated_plan(self):
        e=source('Ethanol, as printed',formula='C2H6O');p=rules.plan_identity(e);q=rules.normalized_lookup_entry(e,p)
        self.assertEqual(q['name'],'Ethanol');self.assertIsNone(q['model3dPath']);self.assertEqual(q['formula'],'C2H6O')
        bad=copy.deepcopy(p);bad['lookups'][0]['name']='Methanol'
        with self.assertRaises(ValueError):rules.normalized_lookup_entry(e,bad)

    def test_L1_selection_is_lookup_failed_only(self):
        e=source('Ethanol (99%)')
        self.assertTrue(rules.eligible_owner_scope(e,{'route':'flat','reason':'lookup_failed'}))
        for old in [{'route':'flat','reason':'identity_conflict'},{'route':'flat','reason':'conformer_failed'},{'route':'molecule_reference'},None]:
            self.assertFalse(rules.eligible_owner_scope(e,old))
        self.assertTrue(rules.eligible_owner_scope(source('Octadecene'),{'route':'flat','reason':'ambiguous_isomer'}))
        self.assertFalse(rules.eligible_owner_scope(source('Squalane'),{'route':'flat','reason':'conformer_failed'}))


class ComponentAndDefaultTests(unittest.TestCase):
    def test_hydrate_component_does_not_relax_general_formula_equality(self):
        self.assertFalse(formula_equivalent('Cd(C2H3O2)2·2H2O','Cd(C2H3O2)2'))
        for name,formula in [('Cadmium acetate','Cd(C2H3O2)2'),('Cadmium acetate dihydrate','Cd(C2H3O2)2·2H2O'),('Indium acetate hydrate','In(C2H3O2)3·4H2O')]:
            p=rules.plan_identity(source(name,formula=formula));self.assertEqual(p['kind'],'independent_components');self.assertEqual(p['lookups'][0]['reference_component_formula'],'C2H3O2-')
        self.assertEqual(rules.plan_identity(source('Cadmium acetate',formula='CdCl2'))['kind'],'hold')
        self.assertEqual(rules.plan_identity(source('Cadmium acetate',pubchemCid=962))['kind'],'hold')

    def test_default_line_and_existing_fixed_IDs(self):
        for name in ['ODE','Octadecene']:
            p=rules.plan_identity(source(name,depictionKind='symbolic_context'));self.assertEqual(p['ownerpart'],'L3');self.assertEqual(p['lookups'][0]['pubchemCid'],8217);self.assertEqual(p['default_disclaimer'],rules.DEFAULT_LINE)
        self.assertEqual(rules.plan_identity(source('Octadecene',formula='ODE'))['ownerpart'],'L3')
        for name in ['Technical-grade oleylamine','Oleylamine (70%)','Oleylamine; 70%, stereochemistry and mixture unresolved']:
            p=rules.plan_identity(source(name));self.assertEqual(p['ownerpart'],'L3');self.assertEqual(p['lookups'][0]['pubchemCid'],5356789)
        self.assertNotEqual(rules.plan_identity(source('Oleylamine; 70%, oxidized products'))['ownerpart'],'L3')

    def test_default_conflicting_real_CID_or_formula_holds(self):
        self.assertEqual(rules.plan_identity(source('ODE',pubchemCid=123))['kind'],'hold')
        self.assertEqual(rules.plan_identity(source('Octadecene',formula='C18H38'))['kind'],'hold')

    def test_stock_components_are_explicit_without_unknown_solvent(self):
        a=rules.plan_identity(source('Lead oleate stock',formula='C36H66O4Pb'))
        self.assertEqual(a['ownerpart'],'L5');self.assertEqual([x['formula']for x in a['lookups']],['C18H33O2-'])
        b=rules.plan_identity(source('Cadmium oleate in ODE; solution speciation unresolved'))
        self.assertEqual([x['formula']for x in b['lookups']],['C18H33O2-','C18H36']);self.assertEqual(b['default_disclaimer'],rules.DEFAULT_LINE)
        self.assertEqual(len(rules.plan_identity(source('Cadmium oleate IN ODE'))['lookups']),2)
        for name in ['Lead oleate stock with unknown ligand','Cadmium precursor stock','Cadmium oleate in solvent','Growth mixture','Knudsen cell']:
            self.assertEqual(rules.plan_identity(source(name))['kind'],'hold')
        self.assertEqual(rules.plan_identity(source('Lead oleate stock',pubchemCid=962))['kind'],'hold')
        self.assertEqual(rules.plan_identity(source('Lead oleate stock',pubchemCid=6435829))['ownerpart'],'L5')

    def test_squalane_single_compound_not_generic_context_bypass(self):
        e=source('Squalane',depictionKind='symbolic_context');self.assertEqual(rules.plan_identity(e)['ownerpart'],'L6')
        for x in [source('Squalane growth mixture'),source('Squalane',depictionKind='specimen'),source('Squalane',formula='C30H60')]:
            self.assertEqual(rules.plan_identity(x)['kind'],'hold')
        self.assertEqual(rules.plan_identity(source('Squalane stock'))['ownerpart'],'L5')
        self.assertEqual(rules.plan_identity(source('Squalane',limitations=['Mixture of squalane and mineral oil.']))['kind'],'hold')

    def test_named_stock_grammar_is_not_an_example_name_allowlist(self):
        for name,expected in [('Dodecanethiol stock',['Dodecanethiol']),('Tridecane solution',['Tridecane']),('Dodecanethiol in Dodecane',['Dodecanethiol','Dodecane'])]:
            p=rules.plan_identity(source(name));self.assertEqual(p['ownerpart'],'L5');self.assertEqual([q['name']for q in p['lookups']],expected)
        p=rules.plan_identity(source('Indium iii acetate in ethanol'));self.assertEqual(p['lookups'][0]['reference_component_formula'],'C2H3O2-')
        p=rules.plan_identity(source('Lead oleate stock and TOP in ODE'));self.assertEqual([q['name']for q in p['lookups']],['Oleate ion','Trioctylphosphine','1-Octadecene'])
        for name in ['Unknown reagent stock','Product in solvent','Unspecified mixture solution']:
            self.assertEqual(rules.plan_identity(source(name))['kind'],'hold')

    def test_other_single_compound_context_requires_exact_identity_resolution(self):
        e=source('Tridecane',depictionKind='symbolic_context',formula='C13H28');p=rules.plan_identity(e)
        self.assertEqual(p['ownerpart'],'L6');self.assertEqual(p['lookups'][0]['query'],'Tridecane')
        for x in [source('Growth mixture',depictionKind='symbolic_context'),source('Cd(Ac)2',depictionKind='symbolic_context'),source('Tridecane',depictionKind='symbolic_context',limitations=['Blend of tridecane and mineral oil.'])]:
            self.assertEqual(rules.plan_identity(x)['kind'],'hold')

    def test_existing_rotatable_default_gets_qualification_without_route_or_model_change(self):
        e=molecule('already-ode','ODE','C18H36',8217);before=copy.deepcopy(e);q=rules.field_default_qualification(e)
        self.assertEqual(q['qualification'],rules.DEFAULT_LINE)
        original={'entries':[e]};overlay={'entries':{},'lFieldQualifications':{e['id']:q}}
        view=rules.qualify_registry_for_reader(original,overlay);self.assertEqual(original,{'entries':[before]})
        expected={**before,'readerFieldDefaultQualification':rules.DEFAULT_LINE};self.assertEqual(view['entries'],[expected])
        self.assertIsNone(rules.field_default_qualification(molecule('explicit','1-Octadecene (ODE)','C18H36',8217)))
        self.assertIsNone(rules.field_default_qualification(source('Octadecene')))
        with self.assertRaises(ValueError):rules.qualify_registry_for_reader({'entries':[source('Octadecene')]},{'entries':{},'lFieldQualifications':{'source':None}})

    def test_normal_overlay_loader_retains_qualification_in_the_reader_view_only(self):
        from chemical_reference_overlay import enrich_registry
        e=molecule('already-ode','ODE','C18H36',8217);registry={'entries':[e]};before=copy.deepcopy(registry)
        overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':'a'*64,'originalBindingsSha256':'b'*64,'entries':{},'lFieldQualifications':{e['id']:rules.field_default_qualification(e)}}
        result=enrich_registry(registry,{},overlay,'a'*64,'b'*64)
        self.assertEqual(registry,before);self.assertEqual(result['entries'][0]['readerFieldDefaultQualification'],rules.DEFAULT_LINE)
        self.assertEqual(result['entries'][0]['model3dPath'],e['model3dPath'])

    def test_exact_acetate_component_excludes_water_and_other_targets(self):
        e=source('Cadmium acetate dihydrate',formula='Cd(C2H3O2)2·2H2O');p=rules.plan_identity(e)
        target={'id':'cadmium-acetate-dihydrate','name':'Cadmium acetate dihydrate','component3dModels':[component('acetate','C2H3O2-'),component('water','H2O')]}
        entries={target['id']:target};ref=rules.registry_group_reference(p['lookups'][0],target['id'],entries)
        self.assertEqual([x['id']for x in ref['component3dModels']],['acetate'])
        with self.assertRaises(ValueError):rules.registry_group_reference(p['lookups'][0],'arbitrary',entries|{'arbitrary':target})


class ProofTests(unittest.TestCase):
    def test_registry_default_proof_and_originals_preserved(self):
        e=source('Octadecene');target=molecule('1-octadecene','1-Octadecene','C18H36',8217);entries={target['id']:target};p=rules.plan_identity(e)
        groups=[{'basis':'existing_registry','lookup':p['lookups'][0],'registry_id':target['id'],'reference':rules.registry_group_reference(p['lookups'][0],target['id'],entries)}]
        before=copy.deepcopy((e,entries));ref,proof=proof_for(e,groups)
        self.assertEqual(rules.validate_L_reference(e,ref,proof,entries),[]);self.assertIn(rules.DEFAULT_LINE,ref['caption']);self.assertEqual((e,entries),before)
        for field,value in [('source_entry_sha256','c'*64),('reference_sha256','d'*64),('entry_id','wrong')]:
            bad=copy.deepcopy(proof);bad[field]=value;self.assertTrue(rules.validate_L_reference(e,ref,bad,entries))
        index=rules.identity.ReferenceIndex(entries.values())
        with mock.patch.object(rules.identity,'ReferenceIndex',side_effect=AssertionError('Index rebuilt')):
            self.assertEqual(rules.validate_L_reference(e,ref,proof,entries,reference_index=index),[])

    def test_component_proof_and_no_aggregate_geometry(self):
        e=source('Indium acetate',formula='In(C2H3O2)3');p=rules.plan_identity(e)
        t={'id':'friedfeld2019-indium-acetate-reference','name':'Indium acetate','component3dModels':[component('acetate','C2H3O2-')]};entries={t['id']:t}
        groups=[{'basis':'existing_registry','lookup':p['lookups'][0],'registry_id':t['id'],'reference':rules.registry_group_reference(p['lookups'][0],t['id'],entries)}]
        ref,proof=proof_for(e,groups);self.assertEqual(rules.validate_L_reference(e,ref,proof,entries),[])
        self.assertEqual(ref['route'],'independent_component_references');self.assertNotIn('atoms',ref);self.assertIn('No geometry between ions',ref['component3dScope'])
        bad=copy.deepcopy(ref);bad['component3dModels'].append(component('water','H2O'));self.assertTrue(rules.validate_L_reference(e,bad,proof,entries))

    def test_cross_parent_component_never_carries_another_formula_multiplicity(self):
        e=source('Indium acetate',formula='In(C2H3O2)3');p=rules.plan_identity(e)
        c={**component('acetate','C2H3O2-'),'multiplicityInReferenceFormula':2}
        t={'id':'cadmium-acetate-dihydrate','name':'Cadmium acetate dihydrate','component3dModels':[c]};entries={t['id']:t};before=copy.deepcopy(entries)
        group={'basis':'existing_registry','lookup':p['lookups'][0],'registry_id':t['id'],'reference':rules.registry_group_reference(p['lookups'][0],t['id'],entries)}
        ref,proof=proof_for(e,[group]);self.assertNotIn('multiplicityInReferenceFormula',ref['component3dModels'][0]);self.assertEqual(entries,before)
        self.assertEqual(rules.validate_L_reference(e,ref,proof,entries),[])

    def test_metadata_reference_is_bound_to_exact_query_CID_and_formula(self):
        e=source('Ethanol (99%)',formula='C2H6O');p=rules.plan_identity(e)
        reference={'route':'molecule_reference','reason':'validated_connectivity_computed_conformer','referenceOnly':True,'trainingEligible':False,'id':'ethanol','formula':'C2H6O','model3dPath':'models/ethanol.json','model3dSha256':'a'*64,'caption':'Illustrative conformer; not measured.','sourceUrls':[]}
        evidence={'query_type':'name','query':'Ethanol','status':'UNIQUE_CID_CONNECTIVITY_CANDIDATE','cid':702,'formula':'C2H6O','cache_sha256':'b'*64,'source_url':'https://pubchem.ncbi.nlm.nih.gov/compound/702'}
        groups=[{'lookup':p['lookups'][0],'basis':'pubchem_metadata','evidence':evidence,'reference':reference}]
        ref,proof=proof_for(e,groups);self.assertEqual(rules.validate_L_reference(e,ref,proof,{}),[])
        for field,value in [('query','Methanol'),('formula','CH4O'),('status','AMBIGUOUS_OR_NO_CID'),('cache_sha256','missing')]:
            bad=copy.deepcopy(proof);bad['groups'][0]['evidence'][field]=value;self.assertTrue(rules.validate_L_reference(e,ref,bad,{}))
        bad=copy.deepcopy(proof);bad['groups'][0]['reference']['formula']='CH4O';self.assertTrue(rules.validate_L_reference(e,ref,bad,{}))

    def test_model_pin_and_reference_scope_cannot_change(self):
        e=source('Octadecene');t=molecule('1-octadecene','1-Octadecene','C18H36',8217);p=rules.plan_identity(e);entries={t['id']:t}
        groups=[{'basis':'existing_registry','lookup':p['lookups'][0],'registry_id':t['id'],'reference':rules.registry_group_reference(p['lookups'][0],t['id'],entries)}];ref,proof=proof_for(e,groups)
        for key,value in [('model3dSha256','c'*64),('trainingEligible',True),('caption','Measured sample')]:
            bad=copy.deepcopy(ref);bad[key]=value;self.assertTrue(rules.validate_L_reference(e,bad,proof,entries))


class QualityHookTests(unittest.TestCase):
    def exercise(self, mutate=None):
        from chemical_reference_quality import check_chemical_reference_overlay
        e=source('Octadecene',depictionKind='symbolic_context');t=molecule('1-octadecene','1-Octadecene','C18H36',8217);entries={t['id']:t};p=rules.plan_identity(e)
        groups=[{'basis':'existing_registry','lookup':p['lookups'][0],'registry_id':t['id'],'reference':rules.registry_group_reference(p['lookups'][0],t['id'],entries)}]
        ref,proof=proof_for(e,groups);ref.update(chemicalUseCount=1,buttonLabel='Rotate 3D ↗')
        registry={'entries':[e,t]};bindings={'recordBindings':{'fixture':{'material':'source'}}}
        class Audit:
            def __init__(self):self.checked=[];self.counts={};self.assets=[]
            def check(self,ok,label):self.checked.append((bool(ok),label));return bool(ok)
            def asset(self,base,path,digest,label):self.assets.append((path,digest));return None
        with tempfile.TemporaryDirectory(prefix='L-identity-',dir=D)as tmp:
            base=pathlib.Path(tmp)
            for name,value in [('registry.json',registry),('bindings.json',bindings)]:
                (base/name).write_text(json.dumps(value),encoding='utf-8')
            sha=lambda name:hashlib.sha256((base/name).read_bytes()).hexdigest()
            overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':sha('registry.json'),'originalBindingsSha256':sha('bindings.json'),'entries':{'source':ref}}
            pins={'schema':rules.SCHEMA,'originalRegistrySha256':overlay['originalRegistrySha256'],'originalBindingsSha256':overlay['originalBindingsSha256'],'entries':{'source':proof}}
            if mutate:mutate(overlay,pins)
            a=Audit();check_chemical_reference_overlay(a,base,registry,bindings,overlay,l_identity_proof=pins)
            return a

    def test_normal_quality_hook_accepts_only_the_exact_proof(self):
        a=self.exercise();self.assertEqual([label for ok,label in a.checked if not ok],[])
        self.assertTrue(a.assets,'Existing ordinary asset verifier is still called')

    def test_stale_header_does_not_bypass_original_context_gate(self):
        a=self.exercise(lambda overlay,pins:pins.update(originalRegistrySha256='f'*64))
        labels=[label for ok,label in a.checked if not ok]
        self.assertTrue(any('stale L original-input'in label for label in labels))
        self.assertTrue(any('original context/isomer'in label for label in labels))

    def test_corrupt_reference_still_hits_ordinary_model_scope_checks(self):
        a=self.exercise(lambda overlay,pins:overlay['entries']['source'].update(component3dModels=[component('injected','H2O')]))
        labels=[label for ok,label in a.checked if not ok]
        self.assertTrue(any('L reference differs'in label for label in labels))
        self.assertTrue(any('mixed viewer routes'in label for label in labels))


class L4QualityHookTests(unittest.TestCase):
    def exercise(self, mutate=None):
        from chemical_reference_quality import check_chemical_reference_overlay
        import chemical_l4_reference as l4
        e=source('CdO',formula='CdO');registry={'entries':[e]};bindings={'recordBindings':{'fixture':{'material':'source'}}}
        class Audit:
            def __init__(self):self.checked=[];self.counts={};self.assets=[]
            def check(self,ok,label):self.checked.append((bool(ok),label));return bool(ok)
            def asset(self,base,path,digest,label):
                p=base/path;self.assets.append(path);self.check(p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==digest,label+': ordinary asset SHA');return p
        with tempfile.TemporaryDirectory(prefix='L4-admission-',dir=D)as tmp:
            root=pathlib.Path(tmp);base=root/'chemical-registry';crystals=root/'crystal-references';base.mkdir();crystals.mkdir();(crystals/'models').mkdir();(crystals/'cif').mkdir()
            model=b'{"synthetic_fixture_only":true}\n';cif=b'# synthetic test receipt, no real crystal model\n'
            (crystals/'models/cdo.json').write_bytes(model);(crystals/'cif/cdo.cif').write_bytes(cif)
            c={'id':'cdo-rocksalt-cod-9006671','name':'CdO ambient bulk reference','formula':'CdO','spaceGroupNumber':225,'referenceOnly':True,'trainingEligible':False,'defaultForSample':False,'modelPath':'models/cdo.json','modelSha256':hashlib.sha256(model).hexdigest(),'cifPath':'cif/cdo.cif','cifSha256':hashlib.sha256(cif).hexdigest()}
            raw=json.dumps({'entries':[c]}).encode();(crystals/'registry.json').write_bytes(raw)
            admitted={'schema':'MatterSyn-L4-admitted-fixed-ambient-proof/1','formulas':{'CdO':{'reference_id':c['id'],'formula':'CdO','space_group_number':225,'owner_authorized_ambient_default':True,'referenceOnly':True,'trainingEligible':False,'registry_path':l4.REGISTRY,'registry_sha256':hashlib.sha256(raw).hexdigest(),'registry_bytes':len(raw),'cif_path':l4.PREFIX+c['cifPath'],'cif_sha256':c['cifSha256'],'cif_bytes':len(cif),'model_path':l4.PREFIX+c['modelPath'],'model_sha256':c['modelSha256'],'model_bytes':len(model)}}}
            crystal={k:v for k,v in c.items()if k!='defaultForSample'}
            ref={'route':'ambient_crystal_reference','reason':'L_owner_fixed_ambient_default','referenceId':c['id'],'referenceOnly':True,'trainingEligible':False,'crystalReference':crystal,'chemicalUseCount':1,'buttonLabel':'Rotate 3D ↗',**{k:c[k]for k in ['modelPath','modelSha256','cifPath','cifSha256']}}
            ref['l4OwnNameProof']=l4.l4_name_proof(e,c['id'])
            for name,value in [('registry.json',registry),('bindings.json',bindings)]:
                (base/name).write_text(json.dumps(value),encoding='utf-8')
            sha=lambda name:hashlib.sha256((base/name).read_bytes()).hexdigest()
            overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':sha('registry.json'),'originalBindingsSha256':sha('bindings.json'),'entries':{'source':ref},'lAmbientProofs':admitted}
            if mutate:mutate(e,overlay,c)
            # Entry mutation is synthetic fixture setup, not a Source record edit.
            if mutate:
                (base/'registry.json').write_text(json.dumps(registry),encoding='utf-8');overlay['originalRegistrySha256']=sha('registry.json')
            a=Audit();check_chemical_reference_overlay(a,base,registry,bindings,overlay);return a

    def test_exact_L4_admission_retains_all_ordinary_crystal_asset_checks(self):
        a=self.exercise();self.assertEqual([label for ok,label in a.checked if not ok],[]);self.assertEqual(set(a.assets),{'models/cdo.json','cif/cdo.cif'})

    def test_L4_registry_and_asset_size_pins_are_not_only_shape_checks(self):
        for key in ['registry_sha256','registry_bytes','model_bytes','cif_bytes']:
            a=self.exercise(lambda e,o,c:o['lAmbientProofs']['formulas']['CdO'].update({key:'f'*64 if key.endswith('sha256') else 1}))
            self.assertTrue([label for ok,label in a.checked if not ok],key)

    def test_L4_never_promotes_specimens_or_other_phase_and_preserves_sample_binding_guard(self):
        a=self.exercise(lambda e,o,c:e.update(name='CdO nanocrystal specimen'));self.assertTrue(any('L4 fixed own-identity'in label for ok,label in a.checked if not ok))
        a=self.exercise(lambda e,o,c:e.update(phase={'status':'reported','value':'another phase'}));self.assertTrue([label for ok,label in a.checked if not ok])
        a=self.exercise(lambda e,o,c:o['entries']['source']['crystalReference'].update(defaultForSample=False));self.assertTrue(any('source/sample binding'in label for ok,label in a.checked if not ok))

    def test_L4_normal_quality_recomputes_the_purity_name_proof(self):
        import chemical_l4_reference as l4
        def decorate(e,o,c):
            e['name']='Cadmium oxide (99%)'
            o['entries']['source']['l4OwnNameProof']=l4.l4_name_proof(e,c['id'])
        a=self.exercise(decorate);self.assertEqual([label for ok,label in a.checked if not ok],[])

    def test_L4_missing_or_fabricated_name_proof_is_rejected(self):
        a=self.exercise(lambda e,o,c:o['entries']['source'].pop('l4OwnNameProof'))
        self.assertTrue(any('L4 fixed own-identity'in label for ok,label in a.checked if not ok))
        a=self.exercise(lambda e,o,c:o['entries']['source']['l4OwnNameProof'].update(transformations=['invented']))
        self.assertTrue(any('L4 fixed own-identity'in label for ok,label in a.checked if not ok))


if __name__=='__main__':unittest.main()
