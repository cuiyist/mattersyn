"""Focused synthetic release-gate tests. No real assets, build or network."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from collections import Counter

D = Path(__file__).parent
SCRIPTS = D.parent / 'scripts'
sys.path.insert(0,str(SCRIPTS))
for name in ('chemical_reference_identity', 'chemical_reference_overlay', 'chemical_reference_quality'):
    suffix = ('.owner-examples.proposed'if name=='chemical_reference_quality'else'.h7-context.proposed') if SCRIPTS == D and name in {'chemical_reference_quality','chemical_reference_identity'} else '.proposed' if SCRIPTS == D else ''
    filename = SCRIPTS / (name + suffix + '.py')
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec);sys.modules[name] = module;spec.loader.exec_module(module)
quality = sys.modules['chemical_reference_quality']


def encode(value):
    return json.dumps(value, sort_keys=True).encode()


class MemoryPath:
    def __init__(self, files, path):self.files,self.path = files,path
    def __truediv__(self, other):return MemoryPath(self.files, self.path + '/' + str(other))
    @property
    def parent(self):return MemoryPath(self.files, self.path.rsplit('/',1)[0])
    @property
    def name(self):return self.path.rsplit('/',1)[-1]
    def read_bytes(self):return self.files[self.path]
    def read_text(self, encoding='utf-8'):return self.read_bytes().decode(encoding)
    def glob(self, pattern):
        return [MemoryPath(self.files,p) for p in self.files if p.startswith(self.path+'/h-reader-') and p.endswith('-3d.json') and '/' not in p[len(self.path)+1:]]
    def __hash__(self):return hash(self.path)
    def __eq__(self, other):return isinstance(other,MemoryPath) and self.path==other.path


class SyntheticAudit:
    def __init__(self):self.errors=[];self.counts=Counter()
    def check(self, value, message):
        if not value:self.errors.append(message)
        return bool(value)
    def asset(self, base, path, digest, label):
        if not self.check(isinstance(path,str) and not path.startswith('/') and '..' not in path.split('/'),label+': unsafe asset'):return None
        target=base/path
        if not self.check(target.path in target.files,label+': absent asset'):return None
        self.check(hashlib.sha256(target.read_bytes()).hexdigest()==digest,label+': asset hash mismatch')
        return target


class OverlayQualityTests(unittest.TestCase):
    def setUp(self):
        self.entry={'id':'chemical','name':'Hydrogen chloride','formula':'HCl','depictionKind':'formula','caption':'Original identity scope'}
        self.registry={'entries':[self.entry]};self.bindings={'recordBindings':{'r':{'m':'chemical'}}}
        self.model={'representation':'3d','coordinateUnits':'angstrom','allowRotation':True,'referenceOnly':True,'trainingEligible':False,'measuredCoordinates':False,'conformerGeneration':{'embeddingMethod':'ETKDGv3'},'atoms':[{'element':'H','x':0,'y':0,'z':0},{'element':'Cl','x':1.2,'y':0,'z':0}],'bonds':[{'a':0,'b':1,'order':1}],'functionalGroups':[]}
        self.ref={'route':'molecule_reference','reason':'validated_connectivity_computed_conformer','referenceOnly':True,'trainingEligible':False,'model3dPath':'models/h-reader-test-3d.json','caption':'Computed illustrative reference, not measured.','chemicalUseCount':1,'buttonLabel':'Rotate 3D ↗'}
        self.files={'assets/chemical-registry/registry.json':encode(self.registry),'assets/chemical-registry/bindings.json':encode(self.bindings)}
        self.base=MemoryPath(self.files,'assets/chemical-registry')
        self.overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':hashlib.sha256(encode(self.registry)).hexdigest(),'originalBindingsSha256':hashlib.sha256(encode(self.bindings)).hexdigest(),'entries':{'chemical':self.ref}}
        self.proof={}
    def run_check(self, refresh_hash=True):
        raw=encode(self.model);self.files['assets/chemical-registry/models/h-reader-test-3d.json']=raw
        if refresh_hash:self.ref['model3dSha256']=hashlib.sha256(raw).hexdigest()
        audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);return audit.errors
    def test_valid_overlay_and_original_formula_classification_unchanged(self):
        original=copy.deepcopy((self.registry,self.bindings));self.assertEqual(self.run_check(),[]);self.assertEqual((self.registry,self.bindings),original);self.assertEqual(self.entry['depictionKind'],'formula');self.assertNotIn('model3dPath',self.entry)
    def test_stale_input_and_unknown_target_rejected(self):
        self.overlay['originalRegistrySha256']='0'*64;self.assertTrue(self.run_check());self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.overlay['entries']['invented']=self.ref;self.assertTrue(self.run_check())
    def test_missing_formerly_flat_target_rejected(self):self.overlay['entries']={};self.assertTrue(self.run_check())
    def test_whole_mixture_specimen_and_support_cannot_receive_one_structure(self):
        for kind in ('mixture','specimen','support'):
            with self.subTest(kind=kind):
                self.entry['depictionKind']=kind;self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.assertTrue(any('whole context'in error for error in self.run_check()))
    def test_owner_fixed_identity_can_override_only_old_unresolved_presentation_kind(self):
        self.entry.update(name='ODE',depictionKind='unresolved-identity');self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.assertEqual(self.run_check(),[])
        self.entry.update(name='Octadecene');self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.assertTrue(any('context/isomer'in error for error in self.run_check()))
    def test_claimed_reuse_requires_exact_original_identity_model_path_and_hash(self):
        known={'id':'known','name':'Hydrogen chloride','formula':'HCl','pubchemCid':313,'depictionKind':'molecule','model3dPath':'models/h-reader-test-3d.json','assetHashes':{'model3dPath':hashlib.sha256(encode(self.model)).hexdigest()},'caption':'Exact original reference.'}
        self.registry['entries'].append(known);self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest()
        self.ref=sys.modules['chemical_reference_identity'].reference_from_existing(known,'unique_exact_compound_name')|{'chemicalUseCount':1,'buttonLabel':'Rotate 3D ↗'};self.overlay['entries']['chemical']=self.ref
        self.assertEqual(self.run_check(),[]);self.ref['referenceRegistryId']='wrong';self.assertTrue(any('referenceRegistryId'in error for error in self.run_check()));self.ref['referenceRegistryId']='known';self.ref['model3dSha256']='0'*64;self.assertTrue(any('model3dSha256'in error for error in self.run_check(False)))
    def test_resolved_name_CID_uses_separate_proof_without_mutating_accepted_row(self):
        self.run_check();known={'id':'known','name':'Different exact PubChem synonym','formula':'HCl','pubchemCid':313,'depictionKind':'molecule','model3dPath':'models/h-reader-test-3d.json','assetHashes':{'model3dPath':hashlib.sha256(encode(self.model)).hexdigest()},'caption':'Exact original reference.'};self.registry['entries'].append(known);self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.ref=sys.modules['chemical_reference_identity'].reference_from_existing(known,'resolved_exact_name_identical_CID')|{'chemicalUseCount':1,'buttonLabel':'Rotate 3D ↗'};self.overlay['entries']['chemical']=self.ref
        proof={'schema':'MatterSyn-H-exact-reported-name-CID-proof/1','originalRegistrySha256':self.overlay['originalRegistrySha256'],'entries':{'chemical':{'entry_id':'chemical','query_field':'chemical_name','query':'Hydrogen chloride','cid':313,'status':'UNIQUE_CID_CONNECTIVITY_CANDIDATE','cache_sha256':'a'*64,'source_url':'https://pubchem.ncbi.nlm.nih.gov/compound/313'}}};before=copy.deepcopy(self.ref);audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof,proof);self.assertEqual(audit.errors,[]);self.assertEqual(self.ref,before);proof['entries']['chemical']['query']='Neighboring precursor';audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof,proof);self.assertTrue(any('proof absent or stale'in x for x in audit.errors))
    def test_named_ligand_proof_must_match_original_entry_and_scope(self):
        import h4_named_ligand_references as h4
        self.run_check();proof={'schema':'MatterSyn-H4-named-ligand-reference/1','entry_id':h4.SN_ID,'source_CID':16685263,'source_formula':'C10H14Cl2O4Sn','reference_scope':h4.REFERENCE_SCOPE,'referenceOnly':True,'trainingEligible':False,'free_ion_claim':False,'solution_speciation_claim':False,'metal_ligand_geometry_assigned':False,'relative_component_geometry_assigned':False,'ligand_formula':'C5H7O2-','ligand_multiplicity':2,'existing_component_id':h4.ACAC_REFERENCE['id'],'source_graph_not_cleaved':True};self.ref.pop('model3dPath');self.ref.update(route='independent_component_references',component3dModels=[h4.ACAC_REFERENCE|{'caption':'Independent known named acetylacetonate reference.'}],component3dScope=h4.REFERENCE_SCOPE+' No geometry between ions is assigned.',namedLigandReference=proof);self.files['assets/chemical-registry/'+h4.ACAC_REFERENCE['model3dPath']]=encode(self.model);self.assertTrue(any('named ligand proof and original identity differ'in x for x in self.run_check(False)))
    def test_disconnected_dimethylcadmium_exclusion_covers_Owen_ID(self):
        self.entry.update(id='owen2008-cdse-ja804414f-cdme2',name='Dimethylcadmium',formula='C2H6Cd',pubchemCid=10479);eid=self.entry['id'];self.bindings['recordBindings']['r']['m']=eid;self.overlay['entries']={eid:self.ref};self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.files['assets/chemical-registry/bindings.json']=encode(self.bindings);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();self.overlay['originalBindingsSha256']=hashlib.sha256(encode(self.bindings)).hexdigest();self.run_check();component={k:self.ref[k]for k in['model3dPath','model3dSha256','caption']};component['id']='methyl';self.ref.pop('model3dPath');self.ref.update(route='independent_component_references',component3dModels=[component],component3dScope='No geometry between ions is assigned.');self.assertTrue(any('excluded disconnected CdMe2'in error for error in self.run_check()))
    def test_use_count_button_and_flags_rejected(self):
        for field,value in [('chemicalUseCount',2),('buttonLabel','Explore structure'),('trainingEligible',True),('referenceOnly',False)]:
            with self.subTest(field=field):old=self.ref[field];self.ref[field]=value;self.assertTrue(self.run_check());self.ref[field]=old
    def test_model_hash_and_path_rejected(self):
        self.ref['model3dSha256']='0'*64;self.assertTrue(self.run_check(False));self.ref['model3dPath']='models/../private.json';self.assertTrue(self.run_check())
    def test_nonfinite_boolean_coordinates_bad_endpoints_and_groups_rejected(self):
        for change in (lambda m:m['atoms'][0].update(x=float('nan')),lambda m:m['atoms'][0].update(z=True),lambda m:m['bonds'][0].update(a=2),lambda m:m.update(functionalGroups=[{'atomIndices':[2]}])):
            with self.subTest(change=change):old=copy.deepcopy(self.model);change(self.model);self.assertTrue(self.run_check());self.model=old
    def test_disconnected_ions_cannot_be_one_coordinate_model(self):self.model['bonds']=[];self.assertTrue(any('disconnected' in error for error in self.run_check()))
    def test_resolved_neutral_binary_solid_cannot_use_molecular_route(self):
        self.model['formula']='O3W';self.assertTrue(any('neutral binary solid'in error for error in self.run_check()))
        self.assertFalse(quality._simple_bulk_formula('O4W-2'));self.assertFalse(quality._simple_bulk_formula('H2O'));self.assertFalse(quality._simple_bulk_formula('CO2'))
    def test_new_model_scope_and_method_flags_required(self):
        for field in ('referenceOnly','trainingEligible','measuredCoordinates','conformerGeneration'):
            with self.subTest(field=field):value=self.model.pop(field);self.assertTrue(self.run_check());self.model[field]=value
    def test_independent_components_require_scope_and_no_parent_geometry(self):
        self.run_check();component={key:self.ref[key] for key in ('model3dPath','model3dSha256','caption')};component['id']='hcl'
        self.ref.pop('model3dPath');self.ref.update(route='independent_component_references',component3dModels=[component],component3dScope='Independent molecular components; no geometry between ions is assigned.')
        self.assertEqual(self.run_check(),[]);component['translation']=[1,2,3];self.assertTrue(self.run_check());component.pop('translation');self.ref['atoms']=[];self.assertEqual(self.run_check(),[]);self.ref['atoms']=[{}];self.assertTrue(self.run_check());self.ref.pop('atoms');self.ref['component3dScope']='Salt assembly';self.assertTrue(self.run_check())
    def test_flat_reason_has_no_geometry_and_stays_one_line(self):
        self.files.pop('assets/chemical-registry/models/h-reader-test-3d.json',None)
        self.overlay['entries']['chemical']={'route':'flat','reason':'ambiguous_isomer','whyNo3d':'The reported isomer is unspecified.','chemicalUseCount':1,'buttonLabel':'View formula ↗'}
        audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);self.assertEqual(audit.errors,[])
        self.overlay['entries']['chemical']['whyNo3d']+='\nextra';audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);self.assertTrue(audit.errors)
    def test_ambient_reference_must_be_identical_existing_and_explicitly_admitted(self):
        self.entry.update(name='InAs',formula='InAs');self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest()
        crystal={'id':'inas-existing','name':'InAs reference','formula':'InAs','modelPath':'models/inas.json','modelSha256':'a'*64,'cifPath':'inas.cif','cifSha256':'b'*64,'spaceGroupNumber':216,'referenceOnly':True,'trainingEligible':False}
        crystal_raw=encode({'entries':[crystal]});self.files['assets/crystal-references/registry.json']=crystal_raw
        self.files['assets/crystal-references/models/inas.json']=b'{}';self.files['assets/crystal-references/inas.cif']=b'CIF'
        crystal['modelSha256']=hashlib.sha256(b'{}').hexdigest();crystal['cifSha256']=hashlib.sha256(b'CIF').hexdigest();crystal_raw=encode({'entries':[crystal]});self.files['assets/crystal-references/registry.json']=crystal_raw
        self.ref={key:value for key,value in self.ref.items()if key not in ('model3dPath','model3dSha256')};self.overlay['entries']['chemical']=self.ref
        self.ref.update(route='ambient_crystal_reference',referenceId=crystal['id'],crystalReference=copy.deepcopy(crystal),**{key:crystal[key]for key in ('modelPath','modelSha256','cifPath','cifSha256')})
        self.proof={'formulas':{'InAs':{'reference_id':crystal['id'],'ambient_structure_unique':True,'basis':'Fixed unique ambient zinc-blende family.','registry_sha256':hashlib.sha256(crystal_raw).hexdigest(),'existing_reference_ids':[crystal['id']],'space_group_number':216}}}
        audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);self.assertEqual(audit.errors,[])
        self.entry['name']='As-synthesized InAs film';self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest();audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);self.assertTrue(any('context/isomer'in error for error in audit.errors));self.entry['name']='InAs';self.files['assets/chemical-registry/registry.json']=encode(self.registry);self.overlay['originalRegistrySha256']=hashlib.sha256(encode(self.registry)).hexdigest()
        self.proof['formulas']={};audit=SyntheticAudit();quality.check_chemical_reference_overlay(audit,self.base,self.registry,self.bindings,self.overlay,self.proof);self.assertTrue(any('not explicitly admitted'in error for error in audit.errors))
    def test_original_quality_classification_guard_and_ci_build_entrypoint_remain(self):
        source=D.parents[1]
        text=(source/'recipe-atlas/scripts/check_quality.py').read_text(encoding='utf-8')
        self.assertIn('uncertain mixture/formula/specimen has invented molecular geometry',text)
        self.assertIn("'check_quality.py'",(source/'recipe-atlas/scripts/build_release.py').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main(verbosity=2)
