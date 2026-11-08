"""Pure H1/H6 identity regressions, usable by Python3.12 CI without RDKit."""
import copy
import importlib.util
from pathlib import Path
import unittest
import sys

D=Path(__file__).parent
SCRIPTS=D.parent/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('identity',SCRIPTS/'chemical_reference_identity.py');identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)


def molecule(eid,name,cid=None,formula=None,**extra):
    return {'id':eid,'name':name,'pubchemCid':cid,'formula':formula,'depictionKind':'molecule','model3dPath':'models/'+eid+'.json','assetHashes':{'model3dPath':'a'*64},'caption':'Independent reference, not measured sample coordinates.','sourceUrls':['https://pubchem.ncbi.nlm.nih.gov/compound/'+str(cid)],**extra}


def source(name='Printed compound',**extra):
    return {'id':'source','name':name,'depictionKind':'formula','model3dPath':None,**extra}


class IdentityTests(unittest.TestCase):
    def test_exact_CID_reuse_and_originals_unchanged(self):
        target=molecule('water','Water',962,'H2O');original=source('Different printed name',pubchemCid=962,formula='H2O');before=copy.deepcopy((target,original));index=identity.ReferenceIndex([target,original]);hit,reason=index.existing(original);self.assertEqual((hit['id'],reason),('water','identical_CID'));ref=identity.reference_from_existing(hit,reason);self.assertEqual(identity.reused_reference_errors(original,ref,index),[]);self.assertEqual((target,original),before)
    def test_unique_exact_name_is_not_fuzzy_and_formula_name_is_not_case_folded(self):
        target=molecule('ethanol','Ethanol',702,'C2H6O');index=identity.ReferenceIndex([target]);self.assertEqual(index.existing(source('Ethanol'))[0]['id'],'ethanol');self.assertIsNone(index.existing(source('Ethanol solution'))[0]);self.assertIsNone(identity.ReferenceIndex([molecule('carbon-monoxide','CO',281)]).existing(source('Co'))[0])
    def test_multiple_same_names_with_distinct_CIDs_stay_ambiguous(self):
        index=identity.ReferenceIndex([molecule('one','Ambiguous',1),molecule('two','Ambiguous',2)]);self.assertIsNone(index.existing(source('Ambiguous'))[0])
    def test_reported_formula_conflict_cannot_reuse_even_matching_CID(self):
        target=molecule('water','Water',962,'H2O');index=identity.ReferenceIndex([target]);original=source('Water',pubchemCid=962,formula='D2O');ref=identity.reference_from_existing(target,'identical_CID');self.assertTrue(any('formula conflict'in error for error in identity.reused_reference_errors(original,ref,index)))
    def test_all_owner_fixed_names_resolve_only_to_the_fixed_exact_identity(self):
        examples=[('ODE','1-octadecene',8217),('OA','oleic-acid',445639),('OLA','oleylamine',5356789),('TOP','top',20851),('TOPO','topo',65577),('Hexane','hexane',8058),('n-hexane','hexane',8058)]
        rows=[molecule(eid,eid,cid)for eid,cid in {(eid,cid)for name,eid,cid in examples}];index=identity.ReferenceIndex(rows)
        for name,eid,cid in examples:
            with self.subTest(name=name):
                original=source(name,depictionKind='unresolved-identity');hit,reason=index.existing(original);self.assertEqual(hit['id'],eid);self.assertEqual(reason,'owner_fixed_named_identity');self.assertIsNone(identity.context_reason(original));self.assertEqual(index.existing(source(name,pubchemCid=999))[1],'identity_conflict')
    def test_hexanes_octadecene_and_mixed_isomers_stay_flat(self):
        for name in ['Hexanes','Octadecene','mixed isomers','octadecene isomer mixture']:
            with self.subTest(name=name):self.assertEqual(identity.context_reason(source(name)),'ambiguous_isomer')
    def test_whole_contexts_hold_but_free_water_stock_component_is_preserved(self):
        for entry in [source('Lead oleate stock'),source('ITO substrate'),source('Unknown source'),source('Nanocrystal specimen')]:self.assertIsNotNone(identity.context_reason(entry))
        self.assertIsNone(identity.context_reason(source('Water in nitrate stock',pubchemCid=962,formula='H2O')))
    def test_reuse_target_id_path_hash_and_scientific_scope_must_match(self):
        target=molecule('ethanol','Ethanol',702,'C2H6O');index=identity.ReferenceIndex([target]);original=source('Ethanol',formula='C2H6O');ref=identity.reference_from_existing(target,'unique_exact_compound_name');self.assertEqual(identity.reused_reference_errors(original,ref,index),[])
        for field,value in [('referenceRegistryId','wrong'),('model3dPath','models/wrong.json'),('model3dSha256','b'*64),('caption','Measured sample structure')]:
            with self.subTest(field=field):changed={**ref,field:value};self.assertTrue(identity.reused_reference_errors(original,changed,index))
    def test_formula_equivalence_checks_stoichiometry_only_after_identity(self):
        target=molecule('zinc-acetate','Zinc acetate',11192,'C4H6O4Zn');index=identity.ReferenceIndex([target]);original=source('Zinc acetate',formula='Zn(CH3COO)2');ref=identity.reference_from_existing(target,'unique_exact_compound_name');self.assertEqual(identity.reused_reference_errors(original,ref,index),[])
        original['formula']='Zn(CH3COO)2·2H2O';self.assertTrue(any('formula conflict'in x for x in identity.reused_reference_errors(original,ref,index)))
        original=source('Different chemical',formula='Zn(CH3COO)2');self.assertTrue(any('no unique exact'in x for x in identity.reused_reference_errors(original,ref,index)))
    def test_systematic_octane_reuses_fixed_reference_but_plural_stock_mixture_hold(self):
        target=molecule('octane','Octane',None,'C8H18');index=identity.ReferenceIndex([target])
        for name in['Octane','n-octane']:
            original=source(name,depictionKind='symbolic_context');hit,reason=index.existing(original);self.assertEqual(hit['id'],'octane');self.assertEqual(reason,'owner_fixed_named_identity');self.assertIsNone(identity.context_reason(original))
        for original in[source('Octanes'),source('Octane stock'),source('Octane mixed isomers'),source('Octane',depictionKind='mixture')]:self.assertIsNotNone(identity.context_reason(original))
    def test_reused_component_scope_allows_only_exact_additive_uniform_qualifier(self):
        target={'id':'salt-reference','name':'Known salt','formula':'C2H3NaO2','depictionKind':'ionic_components','component3dModels':[{'id':'acetate','formula':'C2H3O2-','model3dPath':'models/acetate.json','model3dSha256':'a'*64}],'component3dScope':'Original independent component scope.','caption':'Reference only'};index=identity.ReferenceIndex([target]);original=source('Known salt',formula='C2H3NaO2');ref=identity.reference_from_existing(target,'unique_exact_compound_name');before=copy.deepcopy(target);ref['component3dScope']+=' '+identity.COMPONENT_SCOPE;self.assertEqual(identity.reused_reference_errors(original,ref,index),[]);self.assertEqual(target,before)
        for scope in[identity.COMPONENT_SCOPE,'Original independent component scope. Whole sample geometry assigned.']:
            self.assertTrue(identity.reused_reference_errors(original,ref|{'component3dScope':scope},index))
    def test_full_TDPA_name_with_its_abbreviation_reuses_only_exact_existing_identity(self):
        target=molecule('tetradecylphosphonic-acid','Tetradecylphosphonic acid',78401,'C14H31O3P');index=identity.ReferenceIndex([target])
        for name in['tetradecylphosphonic acid (TDPA)','1-Tetradecylphosphonic acid (TDPA)']:
            original=source(name);before=copy.deepcopy(original);hit,reason=index.existing(original);self.assertEqual(hit['id'],target['id']);ref=identity.reference_from_existing(hit,reason);self.assertEqual(identity.reused_reference_errors(original,ref,index),[]);self.assertEqual(original,before)
        for name in['TDPA','tetradecylphosphoric acid (TDPA)','tetradecylphosphoic acid (TDPA)','tetradecylphosphonic acid (TDPA) stock']:
            self.assertIsNone(index.existing(source(name))[0])
        self.assertIsNotNone(identity.context_reason(source('tetradecylphosphonic acid (TDPA)',depictionKind='mixture')))
    def test_lookup_only_bare_codes_cannot_become_first_PubChem_identity(self):
        for name in['TDPA','OAM','oam','DDT','MEH-PPV','TOPS','USY']:
            with self.subTest(name=name):self.assertTrue(identity.unresolved_lookup_abbreviation(source(name)));self.assertEqual(identity.context_reason(source(name)),'unresolved_abbreviation')
        for e in[source('NHS'),source('ODE'),source('OA'),source('OLA'),source('TOP'),source('TOPO'),source('H2O'),source('H2SO4'),source('DMF',model2dPath='models/own-verified.json'),source('DMSO',pubchemCid=679),source('EDTA',formula='C10H16N2O8'),source('DMSO',aliases=['Dimethyl sulfoxide'])]:
            with self.subTest(entry=e):self.assertFalse(identity.unresolved_lookup_abbreviation(e))
    def test_dimethylcadmium_disconnected_exclusion_is_compound_wide_not_record_id(self):
        for e in[source('Dimethylcadmium'),source('dimethylcadmium (CdMe2)'),source('dimethylcadmium (Me2Cd)'),source('CdMe2'),source('Another label',pubchemCid=10479)]:self.assertTrue(identity.requires_connected_molecule_reference(e))
        self.assertFalse(identity.requires_connected_molecule_reference(source('Cadmium acetate')))
    def test_H7_entity_context_precedes_ambient_formula_and_fixed_identity(self):
        for name,formula in [('As-synthesized InP film','InP'),('GaAs wafer','GaAs'),('InP substrate','InP'),('OLAM-capped InAs QDs','InAs'),('GSH-capped Au nanoclusters','Au'),('Au-catalyzed InP nanowire stem','InP'),('Gold electrode material','Au'),('Zinc oxide preformed NPs','ZnO'),('Nano-Al analytical feed','Al')]:
            e=source(name,formula=formula)
            with self.subTest(name=name):self.assertEqual(identity.material_context_reason(e),'whole_context');self.assertEqual(identity.context_reason(e),'whole_context')
        for e in[source('InP',formula='InP'),source('Indium phosphide',formula='InP'),source('Gold',formula='Au'),source('Zinc oxide powder',formula='ZnO'),source('Water in nitrate stock',pubchemCid=962,formula='H2O'),source('Water for colloidal synthesis',pubchemCid=962,formula='H2O'),source('NCS',model2dPath='models/own-ncs.json',formula='C4H4ClNO2')]:
            with self.subTest(entry=e):self.assertIsNone(identity.material_context_reason(e));self.assertIsNone(identity.context_reason(e))
        self.assertEqual(identity.context_reason(source('OA',depictionKind='mixture')),'whole_context')
    def test_whole_mixture_formulation_names_hold_without_demoting_named_components(self):
        for e in [source('SnSe growth mixture, formulation not restated',formula='SnSe'),source('Precursor formulation',formula='InP'),source('CdSe growth mixtures',formula='CdSe'),source('Cadmium precursor stock'),source('Sodium chloride solution')]:
            with self.subTest(entry=e):self.assertEqual(identity.context_reason(e),'whole_context')
        for e in [source('SnSe',formula='SnSe'),source('Water in nitrate mixture',pubchemCid=962,formula='H2O'),source('Water in nitrate stock',pubchemCid=962,formula='H2O'),source('Ethanol for precursor mixture',pubchemCid=702,formula='C2H6O'),source('Ethanol used in precursor mixture',pubchemCid=702,formula='C2H6O'),source('DMSO')]:
            with self.subTest(entry=e):self.assertIsNone(identity.context_reason(e))

    def test_resolved_exact_name_CID_requires_own_name_lookup_proof(self):
        target=molecule('known','Other accepted systematic name',702,'C2H6O');index=identity.ReferenceIndex([target]);original=source('Own exact reported name',formula='C2H6O');ref=identity.reference_from_existing(target,'resolved_exact_name_identical_CID');proof={'entry_id':original['id'],'query_field':'chemical_name','query':original['name'],'cid':702,'status':'UNIQUE_CID_CONNECTIVITY_CANDIDATE','cache_sha256':'a'*64,'source_url':'https://pubchem.ncbi.nlm.nih.gov/compound/702'}
        self.assertEqual(identity.reused_reference_errors(original,ref,index,proof),[]);self.assertTrue(identity.reused_reference_errors(original,ref,index))
        for key,value in [('query','Neighboring chemical'),('cid',962),('cache_sha256','bad')]:
            with self.subTest(key=key):self.assertTrue(identity.reused_reference_errors(original,ref,index,proof|{key:value}))


if __name__=='__main__':unittest.main(verbosity=2)
