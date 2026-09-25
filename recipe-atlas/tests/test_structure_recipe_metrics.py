"""Synthetic task profiles test decisions; they are not scientific approvals."""
import copy
import hashlib
import html
import json
import os
import tempfile
import unittest
from pathlib import Path
from test_dataset import fixture
from record_helpers import ev, qty, operation
from dataset_lib import eligibility, training_view
from structure_recipe_metrics import assess_structure_recipe, structure_recipe_coverage, recipe_structure_outcome_coverage, load_structure_policy, typed_fields, digest
from catalog_view import structure_coverage_html


class StructureRecipeMetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'sample.json').write_text('{"synthetic_coordinate_fixture":true}', encoding='utf8')
        self.asset_hash = hashlib.sha256((self.root/'sample.json').read_bytes()).hexdigest()

    def record(self):
        r = fixture()
        r['quality']['missing_fields'] = []
        r['structure_assets'] = [{'id':'sample-model','role':'measured_sample','sample_id':'sample-a','url':'/sample.json','description':'Synthetic coordinate fixture, not experimental data.','eligible_as_measured_label':True}]
        return r

    def policy(self, r):
        selection = {k:[x['id'] for x in r[k] if k!='operations' or (not x['optional'] and x['stage']!='characterization')] for k in ['materials','stocks','material_states','operations','condition_options']}
        fields=[]
        for key in selection:
            for i,x in enumerate(r[key]):
                if x['id'] in selection[key]:
                    fields += [{'pointer':p,'disposition':'required','reason':'Explicit synthetic test task requirement.'} for p,_ in typed_fields(x,'/'+key+'/'+str(i))]
        profile = {'id':'synthetic-audited-profile','task':'exact_structure_recipe','record_id':r['record_id'],'record_sha256':digest(r),'sample_id':'sample-a','structure_asset_ids':['sample-model'],'scope':'Synthetic recipe A, excluding independent optional/characterization branches.','required_field_inventory_complete':True,'selection':selection,'field_decisions':fields,'missing_fields_decisions':[{'index':i,'text':t,'disposition':'outside_task_scope','reason':'Synthetic fixture: this documented context is outside the selected task.'} for i,t in enumerate(r['quality']['missing_fields'])],'conflicts_decisions':[{'index':i,'text':t,'disposition':'outside_task_scope','reason':'Synthetic fixture context only.'} for i,t in enumerate(r['quality']['conflicts'])],'review':{'author':'fixture-author','reviewer':'distinct-fixture-reviewer','status':'independently_approved','audit_reference':'https://example.invalid/synthetic-audit','audit_sha256':'a'*64},'coordinate_validation':{'status':'passed_for_task','representation':'experimental_periodic_structure','asset_sha256':{'sample-model':self.asset_hash}}}
        return {'schema_version':'1.0','_asset_root':str(self.root),'task_profiles':{r['record_id']:profile},'asset_qualifications':{'synthetic-source::sample-model':{'url':'/sample.json','asset_sha256':self.asset_hash,'representation':'experimental_periodic_structure','label':'Synthetic sample A'}}}

    def profile(self,r,p):return p['task_profiles'][r['record_id']]
    def codes(self,r,p=None):return assess_structure_recipe(r,p)['reason_codes']

    def test_three_levels_do_not_collapse_into_training_count(self):
        r=self.record();r['structure_assets'][0]['eligible_as_measured_label']=False;r['quality']['requested_tasks']=[]
        p=self.policy(r);p['task_profiles']={}
        m=structure_recipe_coverage([r],p)
        self.assertEqual({'sample_coordinate_assets':1,'records_with_sample_coordinates':1,'source_verified_explicit_coordinate_links':1,'molecular_structure_assets':0,'molecular_structure_recipe_links':0,'exact_task_ready_records':0},m['counts'])
        self.assertIn('measured_label_not_approved',self.codes(r,p))
        self.assertIn('task_not_requested',self.codes(r,p))

    def test_unknown_availability_is_not_reported_as_zero(self):
        r=self.record();p=self.policy(r);p.pop('_asset_root')
        self.assertIsNone(structure_recipe_coverage([r],p)['counts']['sample_coordinate_assets'])
        self.assertFalse(eligibility(r,p)['exact_structure_recipe']['eligible'])

    def test_missing_asset_and_path_escape_are_not_available(self):
        for url in ['/not-present.json','/../outside.json','https://example.invalid/not-fetched.cif']:
            r=self.record();r['structure_assets'][0]['url']=url;p=self.policy(r)
            self.assertEqual(0,structure_recipe_coverage([r],p)['counts']['sample_coordinate_assets'])
            self.assertFalse(eligibility(r,p)['exact_structure_recipe']['eligible'])

    def test_reference_and_illustration_do_not_count_as_sample_coordinates(self):
        for role in ['external_reference','computed_reference','illustrative']:
            r=self.record();r['structure_assets'][0]['role']=role;p=self.policy(r)
            self.assertEqual(0,structure_recipe_coverage([r],p)['counts']['sample_coordinate_assets'])
            self.assertIn('no_sample_coordinate_asset',self.codes(r,p))

    def test_repeated_asset_is_not_two_distinct_coordinate_assets(self):
        a=self.record();b=copy.deepcopy(a);b['record_id']='test-b';b['products'][0]['recipe_link']='general_context'
        m=structure_recipe_coverage([a,b],self.policy(a))
        self.assertEqual(1,m['counts']['sample_coordinate_assets']);self.assertEqual(2,m['counts']['records_with_sample_coordinates']);self.assertEqual(1,m['counts']['source_verified_explicit_coordinate_links'])

    def test_unreviewed_or_unresolved_link_is_not_verified(self):
        for update in ['review','link','evidence']:
            r=self.record()
            if update=='review':r['quality']['review_status']='metadata_only'
            if update=='link':r['products'][0]['recipe_link']='general_context'
            if update=='evidence':r['products'][0]['link_evidence']=[]
            self.assertEqual(0,structure_recipe_coverage([r],self.policy(r))['counts']['source_verified_explicit_coordinate_links'])

    def test_wrong_coordinate_sample_cannot_borrow_an_explicit_recipe_link(self):
        r=self.record();r['structure_assets'][0]['sample_id']='missing-sample';p=self.policy(r)
        self.assertIn('explicit_sample_recipe_link_missing',self.codes(r,p));self.assertFalse(eligibility(r,p)['exact_structure_recipe']['eligible'])

    def test_asset_flag_alone_and_empty_missingness_do_not_admit(self):
        r=self.record();self.assertIn('audited_task_profile_missing',self.codes(r))
        with self.assertRaises(ValueError):training_view(r,'exact_structure_recipe')

    def test_explicit_valid_synthetic_profile_can_admit(self):
        r=self.record();p=self.policy(r)
        self.assertEqual([],assess_structure_recipe(r,p)['reasons'])
        self.assertTrue(eligibility(r,p)['exact_structure_recipe']['eligible'])
        self.assertEqual(1,structure_recipe_coverage([r],p)['counts']['exact_task_ready_records'])

    def test_selected_recipe_must_produce_the_coordinate_sample_state(self):
        r=self.record();r['products'][0]['material_state_id']=None
        self.assertIn('selected_sample_output_unresolved',self.codes(r,self.policy(r)))

    def test_exact_sample_does_not_inherit_broad_paper_host_or_surface(self):
        r=self.record();r['material']['formula']='CdSe/PbSe'
        r['intended_target']['host']={'value':'Unrelated broad-paper host'}
        r['intended_target']['surface']={'value':'Unrelated broad-paper surface'}
        exported=training_view(r,'exact_structure_recipe',self.policy(r))
        self.assertEqual('ZnO',exported['input']['composition'])
        self.assertNotIn('requested_host',exported['input'])
        self.assertNotIn('requested_surface',exported['input'])

    def test_optional_and_characterization_unknowns_are_not_global_blockers(self):
        r=self.record();e=ev('synthetic-source','Synthetic independent characterization')
        r['operations'].append(operation('optional-wash','wash','Optional wash',e,['product-state'],[],stage='workup',optional=True,parameters={'duration':qty(unit='min',evidence=e)}))
        r['operations'].append(operation('characterize','measure','Characterize',e,['product-state'],[],stage='characterization',parameters={'duration':qty(unit='min',evidence=e)}))
        r['quality']['missing_fields']=['Independent characterization duration unspecified.']
        p=self.policy(r);self.assertTrue(eligibility(r,p)['exact_structure_recipe']['eligible'])
        result=training_view(r,'exact_structure_recipe',p)
        self.assertEqual(['prepare-stock','react'],[x['id'] for x in result['output']['operations']])
        self.assertEqual(r['quality']['missing_fields'],result['output']['contextual_missing_fields'])

    def test_audited_required_missing_condition_remains_a_precise_blocker(self):
        r=self.record();r['operations'][1]['parameters']['temperature']=qty(unit='degC',evidence=ev('synthetic-source','Explicitly unreported'))
        p=self.policy(r);a=assess_structure_recipe(r,p)
        self.assertIn({'code':'required_field_unresolved','message':'A field required by this audited task profile is missing, inferred, conflicting, or lacks source evidence.','pointer':'/operations/1/parameters/temperature'},a['reasons'])

    def test_absent_declared_required_field_is_not_silently_ignored(self):
        r=self.record();p=self.policy(r);self.profile(r,p)['field_decisions'].append({'pointer':'/operations/1/parameters/missing-pressure','disposition':'required','reason':'Synthetic pressure-conditioned task explicitly requires this parameter.'})
        self.assertIn('required_field_absent',self.codes(r,p))

    def test_new_unclassified_recipe_field_blocks_after_record_rebind(self):
        r=self.record();p=self.policy(r);r['operations'][1]['parameters']['pressure']=qty(unit='bar',evidence=ev('synthetic-source','Unreported'));self.profile(r,p)['record_sha256']=digest(r)
        self.assertIn('unclassified_task_fields',self.codes(r,p))

    def test_explicit_not_required_field_decision_preserves_unknown(self):
        r=self.record();r['operations'][1]['parameters']['auxiliary']=qty(unit='mL',evidence=ev('synthetic-source','Synthetic optional context'));p=self.policy(r)
        d=next(x for x in self.profile(r,p)['field_decisions'] if x['pointer'].endswith('/auxiliary'));d.update(disposition='not_required',reason='Synthetic task auditor explicitly excludes this contextual field.')
        self.assertTrue(eligibility(r,p)['exact_structure_recipe']['eligible']);self.assertIsNone(training_view(r,'exact_structure_recipe',p)['output']['operations'][1]['parameters']['auxiliary']['value'])

    def test_all_summary_gaps_and_conflicts_need_task_dispositions(self):
        r=self.record();r['quality']['missing_fields']=['A synthesis gap'];r['quality']['conflicts']=['Two conflicting temperatures'];p=self.policy(r)
        self.profile(r,p)['missing_fields_decisions']=[];self.profile(r,p)['conflicts_decisions']=[]
        self.assertIn('unassessed_missing_fields',self.codes(r,p));self.assertIn('unassessed_conflicts',self.codes(r,p))

    def test_task_relevant_conflict_cannot_be_bypassed(self):
        r=self.record();r['quality']['conflicts']=['Two reaction temperatures'];p=self.policy(r);self.profile(r,p)['conflicts_decisions'][0]['disposition']='required_unresolved'
        self.assertIn('task_relevant_conflicts',self.codes(r,p))

    def test_record_revision_invalidates_profile(self):
        r=self.record();p=self.policy(r);r['operations'][1]['parameters']['temperature']['value']=81
        self.assertIn('stale_or_wrong_task_profile',self.codes(r,p))

    def test_coordinate_byte_change_invalidates_profile(self):
        r=self.record();p=self.policy(r);(self.root/'sample.json').write_text('changed coordinates','utf8')
        self.assertIn('coordinate_bytes_or_representation_unverified',self.codes(r,p))

    def test_representation_cannot_switch_from_molecule_to_nanocrystal(self):
        r=self.record();p=self.policy(r);p['asset_qualifications']['synthetic-source::sample-model']['representation']='molecular_structure'
        self.assertIn('profile_coordinate_link_not_approved',self.codes(r,p))

    def test_self_review_and_empty_requirements_cannot_admit(self):
        r=self.record();p=self.policy(r);self.profile(r,p)['review']['reviewer']='fixture-author'
        self.assertIn('independent_profile_audit_missing',self.codes(r,p))
        p=self.policy(r)
        for x in self.profile(r,p)['field_decisions']:x['disposition']='not_required'
        self.assertIn('empty_required_field_inventory',self.codes(r,p))

    def test_omitted_stock_dependency_cannot_admit(self):
        r=self.record();p=self.policy(r);self.profile(r,p)['selection']['operations']=['react']
        self.assertIn('incomplete_selected_recipe_graph',self.codes(r,p))

    def test_export_uses_selected_sample_identity_not_paper_material_label(self):
        r=self.record();r['material']['formula']='Unrelated broad paper label';p=self.policy(r);x=training_view(r,'exact_structure_recipe',p)
        self.assertEqual('ZnO',x['input']['composition']);self.assertEqual('experimental_periodic_structure',x['input']['structure_representation']);self.assertEqual('/sample.json',x['input']['measured_structures'][0]['url'])

    def test_malformed_profiles_fail_closed_without_guessing(self):
        r=self.record()
        for profile in [{}, {'selection':{'operations':[{}]}}, 'approved', None]:
            p={'task_profiles':{r['record_id']:profile}}
            self.assertFalse(eligibility(r,p)['exact_structure_recipe']['eligible'])

    def test_catalog_distinguishes_unavailable_from_zero(self):
        self.assertIn('not been generated',structure_coverage_html({},html.escape))
        m=structure_recipe_coverage([self.record()]);rendered=structure_coverage_html({'structure_recipe_coverage':m},html.escape)
        self.assertIn('—',rendered);self.assertIn('Exact-coordinate training-ready records',rendered)

    def test_catalog_labels_molecular_representation(self):
        r=self.record();p=self.policy(r);p['task_profiles']={};p['asset_qualifications']['synthetic-source::sample-model']['representation']='molecular_structure'
        m=structure_recipe_coverage([r],p)
        self.assertEqual(0,m['counts']['sample_coordinate_assets']);self.assertEqual(1,m['counts']['molecular_structure_assets'])
        self.assertEqual(0,m['counts']['exact_task_ready_records'])
        rendered=structure_coverage_html({'structure_recipe_coverage':m},html.escape)
        self.assertIn('1 molecular structures',rendered);self.assertIn('not included in measured-product coordinate',rendered)

    def test_one_sample_with_several_structural_measurements_is_one_pair_row(self):
        r=self.record()
        r['measurements'].append({'id':'diameter-spread','sample_id':'sample-a','property':'diameter_spread','value':r['measurements'][0]['value'],'technique':'TEM','conditions':'Synthetic fixture','evidence':r['measurements'][0]['evidence']})
        result=recipe_structure_outcome_coverage([r],{'measurement_properties':['diameter','diameter_spread']})
        self.assertEqual(1,result['counts']['recipe_structure_rows'])
        self.assertEqual(1,len(result['rows']))
        self.assertEqual(2,len(result['rows'][0]['structural_measurements']))
        descriptor=result['rows'][0]['structure_descriptor_v02']
        self.assertEqual('mattersyn.structure/0.2',descriptor['schema_version'])
        self.assertEqual('not_reported',descriptor['intended_target']['phase']['status'])
        self.assertEqual('wurtzite',descriptor['observed_product']['structure']['phase']['value'])
        self.assertEqual(2,len(descriptor['observed_product']['structure']['measurement_refs']))

    def test_optical_only_outcome_is_not_a_structure_pair(self):
        r=self.record();r['products'][0]['phase']={'status':'not_reported','value':None,'evidence':[]}
        r['measurements']=[{'id':'absorption','sample_id':'sample-a','property':'absorption_peak','value':r['quality'] and {'status':'reported','value':650,'evidence':[{'source_id':'synthetic-source','locator':'Synthetic optical result'}]},'technique':'Optical absorption','conditions':'Synthetic fixture','evidence':[{'source_id':'synthetic-source','locator':'Synthetic optical result'}]}]
        result=recipe_structure_outcome_coverage([r],{'measurement_properties':['diameter']})
        self.assertEqual(0,result['counts']['recipe_structure_rows'])

    def test_pair_requires_source_checked_explicit_recipe_link(self):
        r=self.record();r['products'][0]['recipe_link']='general_context'
        result=recipe_structure_outcome_coverage([r],{'measurement_properties':['diameter']})
        self.assertEqual(0,result['counts']['recipe_structure_rows'])

    def test_pair_count_exposes_source_locator_and_dedup_limit(self):
        r=self.record()
        result=recipe_structure_outcome_coverage([r],{'measurement_properties':['diameter']})
        row=result['rows'][0]
        self.assertEqual('not_assessed',row['cross_record_sample_deduplication'])
        self.assertTrue(row['recipe_link_evidence'][0]['locator'])
        self.assertEqual('sample-a',row['sample_id'])

    def test_current_collection_reports_auditable_broad_and_strict_counts_separately(self):
        root=Path(__file__).resolve().parents[1]
        records=[json.loads(p.read_text(encoding='utf-8-sig')) for p in sorted((root/'data/records').glob('*.json'))]
        policy=json.loads((root/'data/structure-outcome-policy.json').read_text(encoding='utf-8'))
        self.assertEqual(set(policy['measurement_properties']),set(policy['measurement_fields']))
        broad=recipe_structure_outcome_coverage(records,policy)
        strict_policy=load_structure_policy(root);strict_policy['_asset_root']=str(root/'static')
        strict=structure_recipe_coverage(records,strict_policy,root/'static')
        self.assertEqual({'recipe_structure_rows':87,'source_groups':28,'records':73,'physical_samples_deduplicated':None},broad['counts'])
        li_rows=[row for row in broad['rows'] if row['source_group']=='li1998znga2o4']
        self.assertEqual(2,len(li_rows))
        self.assertEqual({'li-1998-znga2o4-hydrothermal-150c'},{row['record_id'] for row in li_rows})
        self.assertFalse(any(row['source_group']=='williamson2021' for row in broad['rows']))
        tirosh_rows=[row for row in broad['rows'] if row['source_group']=='tirosh2006']
        self.assertEqual(['tirosh-2006-cofe2o4-method-a-270c'],[row['record_id'] for row in tirosh_rows])
        self.assertEqual(0,strict['counts']['exact_task_ready_records'])
        self.assertEqual(0,strict['counts']['sample_coordinate_assets'])
        self.assertEqual(1,strict['counts']['molecular_structure_assets'])
        page=structure_coverage_html({'structure_recipe_coverage':strict,'structure_outcome_coverage':broad},html.escape,broad['rows'])
        self.assertIn('Browse all 87 synthesis–structure rows',page)
        self.assertEqual(87,page.count('Evidence and source locators'))
        self.assertNotIn('voznyy2019',page)
        descriptor_rows={row['source_group']:row['structure_descriptor_v02'] for row in broad['rows'] if row['source_group'] in {'dabbousi1997','fu2007','saha2019'}}
        self.assertEqual({'dabbousi1997','fu2007','saha2019'},set(descriptor_rows))
        fu=next(row for row in broad['rows'] if row['record_id']=='fu-2007-zno-s1')
        self.assertTrue(all(m['descriptor_field']!='structure.unclassified_structural_observation' for m in fu['structural_measurements']))
        refs={ref['property']:ref['field'] for ref in fu['structure_descriptor_v02']['observed_product']['structure']['measurement_refs']}
        self.assertEqual({'diameter':'morphology.dimensions','diameter_spread':'morphology.distribution'},refs)


if __name__=='__main__':unittest.main()
