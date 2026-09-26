"""Regressions from actual paper handoff failures, independent of chemistry."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('batch_preflight',Path(__file__).resolve().parents[1]/'preflight.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.record={'record_id':'r','collection':'reviewed_literature','quality':{'review_status':'source_reviewed'},'materials':[{'id':'salt'}],'condition_options':[{'chemical_material_id':'solvent'}],'material_states':[{'id':'crude'}],'material':{'formula':'A+B','components':['A','B']},'sources':[{'doi':'10.example/paper'}]}
        self.bindings={'recordBindings':{'r':{'salt':'salt-card','solvent':'solvent-card'}},'recordStateBindings':{'r':{'crude':'product-card'}},'sourceRecordSha256':{'r':'a'*64}}
        self.registry={'salt-card','solvent-card','product-card'}
        self.review={'paper_id':'paper','doi':'10.example/paper','reader_sections':[{'items':[{'id':'tem'}]}],'recipe_inventory':[{'record_ids':['r']}],'characterization_inventory':[{'reader_item_ids':['tem'],'record_ids':['r']}]}
    def test_collection_is_required_even_when_generic_schema_allows_omission(self):
        self.assertEqual([],P.record_contract_errors(self.record))
        self.record.pop('collection')
        self.assertIn('collection',P.record_contract_errors(self.record)[0])
    def test_a_draft_is_not_accepted_science(self):
        self.record['quality']['review_status']='draft'
        self.assertTrue(P.record_contract_errors(self.record))
    def test_process_states_are_separate_from_reagents(self):
        self.assertEqual([],P.chemical_errors(self.record,self.bindings,self.registry,'a'*64))
        self.bindings['recordBindings']['r']['crude']='product-card'
        self.assertTrue(P.chemical_errors(self.record,self.bindings,self.registry,'a'*64))
    def test_wrong_state_id_rejected(self):
        self.bindings['recordStateBindings']['r']['salt']='salt-card'
        self.assertTrue(P.chemical_errors(self.record,self.bindings,self.registry,'a'*64))
    def test_late_record_edits_invalidate_binding_digest(self):
        self.assertTrue(P.chemical_errors(self.record,self.bindings,self.registry,'b'*64))
    def test_missing_identity_is_not_hidden_by_complete_id_set(self):
        self.assertTrue(P.chemical_errors(self.record,self.bindings,{'salt-card','product-card'},'a'*64))
    def test_list_characterization_links_are_checked(self):
        self.assertEqual([],P.review_link_errors(self.review,{'r':self.record}))
        self.review['characterization_inventory'][0]['reader_item_ids']=['measurement-not-reader-item']
        self.assertTrue(P.review_link_errors(self.review,{'r':self.record}))
    def test_cross_paper_record_reference_is_rejected(self):
        other=copy.deepcopy(self.record);other['sources'][0]['doi']='10.example/other'
        self.assertTrue(P.review_link_errors(self.review,{'r':other}))
    def test_observation_is_not_a_route_even_in_the_same_material(self):
        hubs={'A+B':{'record_ids':['r']}}
        self.assertTrue(P.route_membership_errors(self.record,hubs,lambda r:False,lambda s:s))
        self.assertEqual([],P.route_membership_errors(self.record,{},lambda r:False,lambda s:s))
    def test_route_requires_whole_product_and_component_hubs(self):
        hubs={name:{'record_ids':['r']} for name in ('A+B','A','B')}
        self.assertEqual([],P.route_membership_errors(self.record,hubs,lambda r:True,lambda s:s))
        del hubs['B']
        self.assertTrue(P.route_membership_errors(self.record,hubs,lambda r:True,lambda s:s))

if __name__=='__main__':unittest.main()
