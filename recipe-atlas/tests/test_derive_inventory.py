"""Synthetic inventory derivation regressions; no paper text or scientific labels."""
import copy
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from derive_inventory import derive,reviewed_seed,hashed,MAIN_SI,MAIN_ONLY,SI_ONLY


def fixture():
    def record(rid,sid,formula,components,kind='literature_protocol'):
        return {'record_id':rid,'collection':'reviewed_literature','record_type':kind,
            'lineage':{'source_group':sid,'recipe_family':rid+'-family'},
            'material':{'formula':formula,'components':components},
            'quality':{'review_status':'source_reviewed','requested_tasks':['precursor_selection']},
            'operations':[{'stage':'synthesis'}] if kind=='literature_protocol' else [],
            'measurements':[],
            'sources':[{'id':sid,'doi':'10.fixture/'+sid,'url':'https://example.org/'+sid,'title':'Synthetic '+sid}]}
    records=[record('route-a','paper-a','CdSe',['CdSe']),
        record('context-a','paper-a','CdSe',['CdSe'],'observation'),
        record('route-b','paper-b','CdSe/ZnS',['CdSe','ZnS'])]
    def metadata(sid,status,documents):
        return {'source_group':sid,'doi':'10.fixture/'+sid,'title':'Synthetic '+sid,
            'review_status':status,'review_scope':'Authored scope; retained verbatim.',
            'documents':documents,'notes':['Authored qualification.']}
    seed={'schema':'mattersyn-inventory-evidence/1','baseline_inventory_sha256':'a'*64,
        'scope':'Synthetic software fixture only','count_definitions':{'source':'Distinct primary source'},
        'corpus_snapshot':{'local_document_files_indexed':3,'local_paper_groups_indexed':2,
            'paper_candidate_groups_total':2,'candidate_groups_without_local_documents':0,'unique_document_content_hashes':3},
        'corpus_candidate_metadata':{'frozen_note':'Historical metadata, not inferred outcomes'},
        'benchmark_scope':{'note':'No benchmark in synthetic fixture'},
        'review_priority_constraints':['Keep supplied source scopes explicit.'],
        'per_paper':[metadata('paper-a','full_supplied_main_and_matched_si_review',[{'role':'main','page_count':4},{'role':'si','page_count':2}]),
            metadata('paper-b','full_supplied_main_review_si_unverified',[{'role':'main','page_count':5}])],
        'material_notes':{'CdSe':['Fixture note']},'excluded_precursor_procedure_identities':[]}
    hubs=[{'id':'cdse','formula':'CdSe','url':'material.html?id=cdse','record_ids':['route-a','route-b'],'direct_record_ids':['route-a'],'component_only':False},
        {'id':'zns','formula':'ZnS','url':'material.html?id=zns','record_ids':['route-b'],'direct_record_ids':[],'component_only':True},
        {'id':'cdse-zns','formula':'CdSe/ZnS','url':'material.html?id=cdse-zns','record_ids':['route-b'],'direct_record_ids':['route-b'],'component_only':False}]
    reviews=[{'id':'paper-a','doi':'10.fixture/paper-a','review_scope':MAIN_SI,'pages_read':6,'record_ids':['route-a']},
        {'id':'paper-b','doi':'10.fixture/paper-b','review_scope':MAIN_ONLY,'pages_read':5,'record_ids':['route-b']}]
    manifest={'record_count':3,'dataset_version':'test-only','records':[{'record_id':r['record_id'],'eligibility':{'partial_protocol':{'eligible':r['record_type']=='literature_protocol'},'exact_structure_recipe':{'eligible':False}}} for r in records]}
    pairs={'rows':[{'pair_row_id':'route-a::sample','record_id':'route-a','source_group':'paper-a'},
        {'pair_row_id':'route-b::sample','record_id':'route-b','source_group':'paper-b'}]}
    corpus_source={'papers':[{'doi':'10.fixture/paper-a','coverage':{'localDocumentCount':2}},
        {'doi':'10.fixture/paper-b','coverage':{'localDocumentCount':1}}],
        'summary':{'sourceDocumentCount':3,'paperCandidateCount':2,'papersWithLocalDocuments':2,'uniqueContentHashes':3}}
    seed['corpus_source_binding']={'canonical_json_sha256':hashed(corpus_source),'local_paper_groups':2,'historical_augmented_library_groups':2}
    return dict(seed=seed,records=records,hubs=hubs,reviews=reviews,
        library={'papers':[{'doi':'10.fixture/paper-a'},{'doi':'10.fixture/paper-b'}],'summary':copy.deepcopy(corpus_source['summary'])},manifest=manifest,pairs=pairs,corpus_source=corpus_source)


class InventoryDerivationTests(unittest.TestCase):
    def test_counts_are_derived_without_mutation_or_scope_promotion(self):
        data=fixture();before=copy.deepcopy(data);result=derive(**data)
        self.assertEqual(data,before)
        self.assertEqual(result,derive(**data))
        self.assertEqual(result['summary']['canonical_records'],3)
        self.assertEqual(result['summary']['synthesis_route_variant_records'],2)
        self.assertEqual(result['summary']['formal_full_main_and_matched_si_reviews'],1)
        self.assertEqual(result['summary']['formal_full_review_pages'],6)
        self.assertEqual(result['summary']['formal_full_main_reviews_si_unverified'],1)
        self.assertEqual(result['summary']['formal_full_main_only_review_pages'],5)
        self.assertEqual(result['summary']['source_checked_synthesis_structure_rows'],2)
        self.assertEqual(result['training_eligibility']['partial_protocol'],2)
        self.assertEqual(result['training_eligibility']['exact_structure_recipe'],0)
        self.assertIsNone(result['summary']['full_corpus_recipe_count'])
        self.assertIsNone(result['summary']['deduplicated_physical_sample_outcomes'])
        # Source A's formal index intentionally covers a scoped subset.
        self.assertEqual(data['reviews'][0]['record_ids'],['route-a'])
        self.assertEqual(result['per_paper'][0]['review_scope'],data['seed']['per_paper'][0]['review_scope'])
        self.assertEqual(result['per_paper'][0]['notes'],['Authored qualification.'])
        zns=next(row for row in result['per_material'] if row['material_system']=='ZnS')
        self.assertEqual(zns['direct_synthesis_route_variant_count'],0)
        self.assertEqual(zns['component_route_record_ids'],['route-b'])

    def test_si_only_is_separately_counted_without_main_promotion(self):
        data=fixture()
        data['seed']['per_paper'][1]['review_status']='full_supplied_si_review_main_unverified'
        data['seed']['per_paper'][1]['documents']=[{'role':'si','page_count':5}]
        data['reviews'][1]['review_scope']=SI_ONLY
        result=derive(**data)
        self.assertEqual(result['summary']['formal_full_si_reviews_main_unverified'],1)
        self.assertEqual(result['summary']['formal_full_si_only_review_pages'],5)
        self.assertEqual(result['summary']['formal_full_main_reviews_si_unverified'],0)
        self.assertEqual(result['summary']['formal_full_main_and_matched_si_reviews'],1)
        self.assertEqual(result['summary']['formal_full_review_pages'],6)
        self.assertEqual(result['per_paper'][1]['documents'],[{'role':'si','page_count':5}])

    def test_inventory_si_scope_rejects_main_document_even_if_counts_match(self):
        data=fixture()
        data['seed']['per_paper'][1]['review_status']='full_supplied_si_review_main_unverified'
        data['reviews'][1]['review_scope']=SI_ONLY
        with self.assertRaisesRegex(ValueError,'SI-only scope'):derive(**data)

    def test_legacy_si_role_is_normalized_only_for_inventory_validation(self):
        data=fixture();data['seed']['per_paper'][0]['documents'][1]['role']='supporting_information'
        before=copy.deepcopy(data);result=derive(**data)
        self.assertEqual(data,before)
        self.assertEqual(result['per_paper'][0]['documents'][1]['role'],'supporting_information')
        self.assertEqual(result['summary']['formal_full_main_and_matched_si_reviews'],1)
        self.assertEqual(result['summary']['formal_full_review_pages'],6)

    def test_unknown_inventory_role_cannot_claim_any_formal_scope(self):
        for scope,status,roles in [(MAIN_ONLY,'full_supplied_main_review_si_unverified',['main','unknown']),(MAIN_SI,'full_supplied_main_and_matched_si_review',['main','si','unknown']),(SI_ONLY,'full_supplied_si_review_main_unverified',['si','unknown'])]:
            with self.subTest(scope=scope):
                data=fixture();p=data['seed']['per_paper'][1];p['review_status']=status
                p['documents']=[{'role':r,'page_count':1} for r in roles]
                data['reviews'][1]['review_scope']=scope;data['reviews'][1]['pages_read']=len(roles)
                with self.assertRaises(ValueError):derive(**data)

    def test_seed_retains_authored_evidence_and_historical_metadata_not_cached_counts(self):
        data=fixture();inventory=derive(**data);before=copy.deepcopy(inventory)
        seed=reviewed_seed(inventory,'b'*64)
        self.assertEqual(inventory,before)
        self.assertNotIn('record_ids',seed['per_paper'][0])
        self.assertNotIn('canonical_record_count',seed['per_paper'][0])
        self.assertEqual(seed['per_paper'][0]['notes'],['Authored qualification.'])
        self.assertEqual(seed['corpus_snapshot'],data['seed']['corpus_snapshot'])
        self.assertEqual(seed['corpus_candidate_metadata'],data['seed']['corpus_candidate_metadata'])
        seed['per_paper'][0]['notes'].append('Changed privately')
        self.assertEqual(inventory['per_paper'][0]['notes'],['Authored qualification.'])

    def test_formal_review_scope_doi_and_pages_must_match_authored_evidence(self):
        for key,value in [('review_scope',MAIN_ONLY),('review_scope','unknown'),('doi','10.fixture/wrong'),('pages_read',7),('pages_read',True)]:
            with self.subTest(key=key,value=value):
                data=fixture();data['reviews'][0][key]=value
                with self.assertRaises(ValueError):derive(**data)

    def test_formal_review_record_membership_rejects_unknown_duplicate_and_wrong_source(self):
        for ids in [['missing'],['route-a','route-a'],['route-b']]:
            with self.subTest(ids=ids):
                data=fixture();data['reviews'][0]['record_ids']=ids
                with self.assertRaisesRegex(ValueError,'Formal review record/source'):derive(**data)

    def test_formal_review_ids_and_metadata_cannot_be_unknown_or_ambiguous(self):
        data=fixture();data['reviews'].append(copy.deepcopy(data['reviews'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate formal'):derive(**data)
        data=fixture();data['reviews'][0]['id']='unknown'
        with self.assertRaisesRegex(ValueError,'Formal review membership'):derive(**data)
        data=fixture();data['seed']['per_paper'][0]['paper_id']='paper-b'
        with self.assertRaisesRegex(ValueError,'Ambiguous authored formal'):derive(**data)

    def test_hub_formula_cannot_create_an_unrelated_material(self):
        data=fixture();data['hubs'][0]['formula']='UnknownFormula'
        with self.assertRaisesRegex(ValueError,'Atlas direct material|Atlas material/component'):derive(**data)

    def test_direct_and_component_hub_memberships_and_component_only_state_are_checked(self):
        for change in ['missing_direct','duplicate_direct','foreign_direct','missing_component','wrong_component_only','non_boolean_component_only']:
            with self.subTest(change=change):
                data=fixture();hub=data['hubs'][0]
                if change=='missing_direct':hub['direct_record_ids']=[]
                elif change=='duplicate_direct':hub['direct_record_ids']=['route-a','route-a']
                elif change=='foreign_direct':hub['direct_record_ids']=['route-b']
                elif change=='missing_component':hub['record_ids']=['route-a']
                elif change=='wrong_component_only':hub['component_only']=True
                else:hub['component_only']=0
                with self.assertRaisesRegex(ValueError,'Atlas'):derive(**data)

    def test_manifest_duplicate_membership_and_stale_record_count_are_rejected(self):
        data=fixture();data['manifest']['records'].append(copy.deepcopy(data['manifest']['records'][0]))
        with self.assertRaisesRegex(ValueError,'Manifest record membership'):derive(**data)
        data=fixture();data['manifest']['record_count']=4
        with self.assertRaisesRegex(ValueError,'Manifest record count'):derive(**data)

    def test_pair_duplicate_unknown_and_wrong_source_joins_are_rejected(self):
        data=fixture();data['pairs']['rows'].append(copy.deepcopy(data['pairs']['rows'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate structure pair'):derive(**data)
        for key,value in [('record_id','unknown'),('source_group','paper-b')]:
            data=fixture();data['pairs']['rows'][0][key]=value
            with self.assertRaisesRegex(ValueError,'Structure pair record/source'):derive(**data)

    def test_missing_authored_scope_and_new_corpus_counts_are_not_auto_admitted(self):
        data=fixture();data['seed']['per_paper'].pop()
        with self.assertRaisesRegex(ValueError,'no automatic review promotion'):derive(**data)
        data=fixture();data['library']['summary']['sourceDocumentCount']+=1
        with self.assertRaisesRegex(ValueError,'Corpus snapshot changed'):derive(**data)



    def test_curated_primary_addition_extends_library_not_frozen_intake(self):
        data=fixture();old=derive(**data)
        for r in data['records']:
            if r['lineage']['source_group']=='paper-b':r['sources'][0]['doi']='10.fixture/curated-new'
        data['seed']['per_paper'][1]['doi']='10.fixture/curated-new'
        data['reviews'][1]['doi']='10.fixture/curated-new'
        data['library']['papers'].append({'doi':'10.fixture/curated-new'})
        before=copy.deepcopy(data);result=derive(**data)
        self.assertEqual(data,before)
        self.assertEqual(result['summary']['historical_augmented_library_groups'],2)
        self.assertEqual(result['summary']['frozen_intake_local_paper_groups'],2)
        self.assertEqual(result['summary']['local_paper_groups_indexed'],3)
        self.assertEqual(result['summary']['curated_library_additions'],1)
        self.assertEqual(result['summary']['local_groups_without_canonical_records'],1)
        self.assertEqual(result['summary']['local_document_files_indexed'],3)
        self.assertEqual(result['training_eligibility'],old['training_eligibility'])
        self.assertEqual(result['summary']['source_checked_synthesis_structure_rows'],old['summary']['source_checked_synthesis_structure_rows'])

    def test_extra_missing_wrong_and_duplicate_library_dois_rejected(self):
        for change in ('extra','missing','wrong','duplicate'):
            with self.subTest(change=change):
                data=fixture();papers=data['library']['papers']
                if change=='extra':papers.append({'doi':'10.fixture/not-canonical'})
                elif change=='missing':papers.pop()
                elif change=='wrong':papers[0]['doi']='10.fixture/wrong'
                else:papers.append({'doi':papers[0]['doi'].upper()})
                with self.assertRaisesRegex(ValueError,'Library source membership'):derive(**data)

    def test_library_doi_case_is_identity_equivalent(self):
        data=fixture();before=derive(**data)
        data['library']['papers'][0]['doi']=data['library']['papers'][0]['doi'].upper()
        self.assertEqual(derive(**data),before)

    def test_frozen_intake_content_and_missing_binding_fail_closed(self):
        for change in ('content','binding'):
            data=fixture()
            if change=='content':data['corpus_source']['papers'][0]['doi']='10.fixture/new-intake'
            else:data['seed'].pop('corpus_source_binding')
            with self.assertRaisesRegex(ValueError,'Corpus snapshot changed'):derive(**data)

    def test_rebinding_hash_cannot_hide_intake_count_or_document_drift(self):
        for change in ('document','candidate','local','duplicate'):
            data=fixture();source=data['corpus_source']
            if change=='document':source['summary']['sourceDocumentCount']+=1
            elif change=='candidate':source['summary']['paperCandidateCount']+=1
            elif change=='local':source['papers'][0]['coverage']['localDocumentCount']=0
            else:source['papers'][1]['doi']=source['papers'][0]['doi']
            data['seed']['corpus_source_binding']['canonical_json_sha256']=hashed(source)
            data['library']['summary']=copy.deepcopy(source['summary'])
            with self.assertRaisesRegex(ValueError,'Corpus snapshot changed'):derive(**data)

    def test_cited_nonprimary_doi_cannot_admit_a_library_addition(self):
        data=fixture();data['records'][0]['sources'].append({'id':'cited-only','doi':'10.fixture/cited'})
        data['library']['papers'].append({'doi':'10.fixture/cited'})
        with self.assertRaisesRegex(ValueError,'Library source membership'):derive(**data)

if __name__=='__main__':unittest.main()
