import copy,importlib.util,json,pathlib,sys,unittest
D=pathlib.Path(__file__).parent
SCRIPTS=D if(D/'chemical_reference_overlay.proposed.py').exists()else D.parent/'scripts'
spec=importlib.util.spec_from_file_location('overlay',SCRIPTS/('chemical_reference_overlay.proposed.py'if SCRIPTS==D else'chemical_reference_overlay.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class OverlayTests(unittest.TestCase):
 def setUp(self):
  self.registry={'schemaVersion':'1','entries':[{'id':'water','name':'Printed water','depictionKind':'formula','caption':'Original scope','model3dPath':None}]};self.bindings={'recordBindings':{'r':{'m':'water'}},'sourceRecordSha256':{'r':'c'*64}}
  self.overlay={'schema':'MatterSyn-reader-chemical-reference-overlay/1','originalRegistrySha256':'a'*64,'originalBindingsSha256':'b'*64,'entries':{'water':{'route':'molecule_reference','referenceOnly':True,'trainingEligible':False,'model3dPath':'models/h-water.json','model3dSha256':'d'*64}}}
 def enrich(self):return m.enrich_registry(self.registry,self.bindings,self.overlay,'a'*64,'b'*64)
 def test_original_registry_bindings_classification_caption_unchanged(self):
  r,b=copy.deepcopy(self.registry),copy.deepcopy(self.bindings);enriched=self.enrich();self.assertEqual(self.registry,r);self.assertEqual(self.bindings,b);self.assertEqual(enriched['entries'][0]['depictionKind'],'formula');self.assertEqual(enriched['entries'][0]['caption'],'Original scope');self.assertIn('readerReference3d',enriched['entries'][0])
 def test_stale_input_hash_rejected(self):
  self.overlay['originalBindingsSha256']='e'*64
  with self.assertRaises(ValueError):self.enrich()
 def test_unknown_identity_rejected(self):
  self.overlay['entries']['other']=self.overlay['entries']['water']
  with self.assertRaises(ValueError):self.enrich()
 def test_missing_flat_reason_rejected(self):
  self.overlay['entries']['water']={'route':'flat'}
  with self.assertRaises(ValueError):self.enrich()
 def test_actual_pure_chemical_slice_contains_only_its_own_reference(self):
  scripts=SCRIPTS;sys.path.insert(0,str(scripts));spec=importlib.util.spec_from_file_location('shards',scripts/'build_reader_shards.py');shards=importlib.util.module_from_spec(spec);spec.loader.exec_module(shards)
  enriched=self.enrich();chem={'registry':enriched,'bindings':self.bindings,'solution_contexts':{},'product_bindings':{}}
  result=shards.chemical_slices({'records':{'r':{}}},chem);self.assertEqual(set(result),{'chemicals/r.json'});slice=json.loads(result['chemicals/r.json']);self.assertEqual(slice['registry']['entries'][0]['readerReference3d'],self.overlay['entries']['water']);self.assertEqual(slice['bindings']['recordBindings'],self.bindings['recordBindings'])
if __name__=='__main__':unittest.main(verbosity=2)
