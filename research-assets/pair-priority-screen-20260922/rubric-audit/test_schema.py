import unittest,json,copy
from pathlib import Path
from jsonschema import Draft202012Validator
P=Path(__file__).resolve().parent
S=json.loads((P/'pair-candidate.schema.json').read_text(encoding='utf-8'))
V=Draft202012Validator(S)
BASE={'id':'test-chen-host','paper_id':'10.1021/acsami.8b04556','bundle_sha256':'0'*64,'sample_label':'S1','phase_or_component':'Cs4PbBr6','target_role':'current_host_component','structure_origin':'current_experimental_refinement','structure_level':'atomic_coordinates','representation':'periodic_average','coordinate_availability':'local_atomic_table','recipe_link':'explicit_named_formulation','evidence':[{'source_sha256':'1'*64,'document_role':'si','pdf_page':8,'locator':'Table S1','signal_type':'structure'},{'source_sha256':'2'*64,'document_role':'main','pdf_page':4,'locator':'Table 1','signal_type':'linkage'}],'conflicts':['Rp/Rwp source inversion'],'missingness':['No task profile'],'priority_band':'A','verification_level':'cached_text_candidate','task_ready':False}
class Tests(unittest.TestCase):
 def valid(self,x):self.assertEqual(list(V.iter_errors(x)),[])
 def invalid(self,x):self.assertTrue(list(V.iter_errors(x)))
 def test_schema(self):Draft202012Validator.check_schema(S)
 def test_average_host_candidate_allowed_without_generated_asset(self):self.valid(BASE)
 def test_ranker_cannot_approve_training(self):
  x=copy.deepcopy(BASE);x.update(task_ready=True,task_profile_id='pretend');self.invalid(x)
 def test_fixed_component_cannot_inherit_top_band(self):
  x=copy.deepcopy(BASE);x['structure_origin']='fixed_or_borrowed_model';self.invalid(x)
 def test_precursor_cannot_inherit_target_band(self):
  x=copy.deepcopy(BASE);x['target_role']='precursor_or_byproduct';self.invalid(x)
 def test_unresolved_link_cannot_inherit_top_band(self):
  x=copy.deepcopy(BASE);x['recipe_link']='unknown';self.invalid(x)
 def test_cell_only_cannot_inherit_top_band(self):
  x=copy.deepcopy(BASE);x['structure_level']='unit_cell';self.invalid(x)
 def test_missing_coordinate_file_not_present(self):
  x=copy.deepcopy(BASE);x['coordinate_availability']='claimed_not_located';self.invalid(x)
 def test_missing_sample_and_evidence_rejected(self):
  x=copy.deepcopy(BASE);x['sample_label']=None;x['evidence']=[];self.invalid(x)
 def test_reference_channel_keeps_useful_context(self):
  x=copy.deepcopy(BASE);x.update(priority_band='E',target_role='external_reference',structure_origin='external_reference',recipe_link='none',structure_level='unit_cell',representation='no_atomic_representation',coordinate_availability='none_in_inspected_sources');self.valid(x)
if __name__=='__main__':unittest.main()
