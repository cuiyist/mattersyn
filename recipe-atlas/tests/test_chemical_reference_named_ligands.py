"""Pure release checks for bounded named-ligand references; no RDKit/network."""
import copy,importlib.util,pathlib,sys,unittest
D=pathlib.Path(__file__).parent;S=D.parent/'scripts'
spec=importlib.util.spec_from_file_location('named_ligands',S/'h4_named_ligand_references.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def proof(inside=False):
 p={'schema':'MatterSyn-H4-named-ligand-reference/1','entry_id':h.IN_ID if inside else h.SN_ID,'source_CID':140056355 if inside else 16685263,'source_formula':'C48H93InO6'if inside else'C10H14Cl2O4Sn','reference_scope':h.REFERENCE_SCOPE,'referenceOnly':True,'trainingEligible':False,'free_ion_claim':False,'solution_speciation_claim':False,'metal_ligand_geometry_assigned':False,'relative_component_geometry_assigned':False,'ligand_formula':'C16H31O2-'if inside else'C5H7O2-','ligand_multiplicity':3 if inside else 2}
 if inside:p.update(removed_In_O_bonds=3,omitted_In_atoms=1,formerly_bound_O_charge=-1,metal_charge_not_assigned=True,ligand_atoms_preserved=True,ligand_bonds_preserved=True,hydrogens_preserved=True,composition_preserved=True)
 else:p.update(existing_component_id=h.ACAC_REFERENCE['id'],source_graph_not_cleaved=True)
 return p
class NamedLigandChecks(unittest.TestCase):
 def test_exact_existing_named_acac_model_and_count(self):
  p=proof();self.assertTrue(h.validate_named_ligand_components(p,[h.ACAC_REFERENCE]));self.assertFalse(p['free_ion_claim'])
  for key,value in [('model3dSha256','b'*64),('formula','C5H8O2'),('multiplicityInReferenceFormula',1)]:
   with self.subTest(key=key),self.assertRaises(ValueError):h.validate_named_ligand_components(p,[h.ACAC_REFERENCE|{key:value}])
 def test_exact_palmitate_formula_count_and_graph_preservation_proof(self):
  p=proof(True);ref={'formula':'C16H31O2-','model3dPath':'models/h-reader-example-3d.json','model3dSha256':'a'*64,'multiplicityInReferenceFormula':3};self.assertTrue(h.validate_named_ligand_components(p,[ref]))
  for key,value in [('composition_preserved',False),('hydrogens_preserved',False),('removed_In_O_bonds',2),('formerly_bound_O_charge',0),('source_CID',14016)]:
   with self.subTest(key=key),self.assertRaises(ValueError):h.validate_named_ligand_reference(p|{key:value})
 def test_counts_reject_booleans_and_integral_floats(self):
  for inside in[True,False]:
   p=proof(inside)
   for key in['source_CID','ligand_multiplicity']+(['removed_In_O_bonds','omitted_In_atoms','formerly_bound_O_charge']if inside else[]):
    for wrong in[True,float(p[key])]:
     with self.subTest(inside=inside,key=key,wrong=wrong),self.assertRaises(ValueError):h.validate_named_ligand_reference(p|{key:wrong})
 def test_no_general_metal_cleavage_or_sample_speciation_permission(self):
  for key,value in [('entry_id','different-salt'),('free_ion_claim',True),('relative_component_geometry_assigned',True),('solution_speciation_claim',True),('trainingEligible',True),('reference_scope','Whole salt geometry')]:
   with self.subTest(key=key),self.assertRaises(ValueError):h.validate_named_ligand_reference(proof()|{key:value})
if __name__=='__main__':unittest.main(verbosity=2)
