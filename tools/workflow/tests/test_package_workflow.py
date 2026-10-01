import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import package_workflow as w

def fixture(root):
    root=Path(root); (root/'records').mkdir()
    record={'record_id':'sample-1','revision':1,'lineage':{'source_group':'paper-a'},
            'operations':[{'temperature':150}],'quality':{'review_status':'draft','missing_fields':['duration']},
            'sources':[{'id':'paper-a','doi':'10.example/a','main_status':'scoped','si_status':'not reviewed'}]}
    path=root/'records'/'sample-1.json'; path.write_text(json.dumps(record))
    pkg={'schema_version':w.VERSION,'package_id':'paper-a','revision':1,
         'source':{'primary_source_id':'paper-a','identity_status':'verified','doi':'10.example/a','title':'Synthetic test only'},
         'documents':[{'document_id':'main-a','role':'main','sha256':'1'*64,'screened_pass_receipt_id':'screen-a',
                       'coverage':{'status':'reviewed_scoped','reviewed_pages':[2],'page_count':5,'exclusions':['SI not reviewed']}}],
         'records':[{'record_id':'sample-1','path':'records/sample-1.json','sha256':w.sha(path)}],
         'locators':[{'id':'loc-1','document_id':'main-a','record_id':'sample-1','field_pointer':'/operations/0/temperature',
                      'source_locator':'Methods page 2','page':2,'quote_check':{'status':'passed','receipt_id':'quote-a'}}],
         'assets':[],'reagent_bindings':[],
         'scope':{'unit':'main_text','omissions':['SI has not been checked'],'companion_required':False},
         'audit':{'author_id':'author-a','reviewer_id':'reviewer-b','status':'pending','scientific_sha256':None,
                  'base_scientific_sha256':None,'scope':'entire_scoped_package','checklist':{},'receipt_id':None},
         'presentation':{'state':'pending','missing_components':['molecules']},'derived_files':[]}
    return pkg

def accept(pkg,root):
    pkg['audit'].update(status='accepted',scientific_sha256=w.digest(w.science_payload(pkg,root)),
                        checklist={k:'passed' for k in w.CHECKLIST},receipt_id='synthetic-test-audit')

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.p=fixture(self.root)
    def tearDown(self): self.tmp.cleanup()
    def check(self): return w.validate(self.p,self.root,lambda r:[])
    def test_pending_does_not_create_audit(self):
        r=self.check(); self.assertTrue(r['passed']); self.assertFalse(r['scientific_package_ready_for_existing_integration_gates'])
    def test_accepted_science_can_have_presentation_pending(self):
        accept(self.p,self.root); r=self.check(); self.assertTrue(r['passed']); self.assertTrue(r['scientific_package_ready_for_existing_integration_gates']); self.assertFalse(r['publication_authorized'])
    def test_accepted_needs_independent_reviewer(self):
        accept(self.p,self.root); self.p['audit']['reviewer_id']='author-a'; self.assertFalse(self.check()['passed'])
    def test_hash_tamper_rejected(self):
        (self.root/'records/sample-1.json').write_text('{}'); self.assertFalse(self.check()['passed'])
    def test_changed_science_requires_new_audit(self):
        accept(self.p,self.root); r=w.load(self.root/'records/sample-1.json'); r['operations'][0]['temperature']=250
        (self.root/'records/sample-1.json').write_text(json.dumps(r)); self.p['records'][0]['sha256']=w.sha(self.root/'records/sample-1.json')
        self.assertFalse(self.check()['passed'])
    def test_administrative_record_change_reuses_audit(self):
        accept(self.p,self.root); r=w.load(self.root/'records/sample-1.json'); r['revision']=2; r['quality']['reviewed_at']='2026-09-26'
        (self.root/'records/sample-1.json').write_text(json.dumps(r)); self.p['records'][0]['sha256']=w.sha(self.root/'records/sample-1.json')
        self.assertTrue(self.check()['passed'])
    def test_document_coverage_change_requires_audit(self):
        accept(self.p,self.root); self.p['documents'][0]['coverage']['reviewed_pages'].append(3); self.assertFalse(self.check()['passed'])
    def test_receipt_id_only_change_preserves_science(self):
        accept(self.p,self.root); self.p['locators'][0]['quote_check']['receipt_id']='new-receipt'; self.assertTrue(self.check()['passed'])
    def test_si_standalone_allowed(self):
        self.p['documents'][0]['role']='si'; self.p['scope']['unit']='si_standalone'; self.assertTrue(self.check()['passed'])
    def test_missing_pair_not_required(self):
        self.assertTrue(self.check()['passed']); self.p['scope']['companion_required']=True; self.assertFalse(self.check()['passed'])
    def test_locator_outside_scope_rejected(self):
        self.p['locators'][0]['page']=3; self.assertFalse(self.check()['passed'])
    def test_bad_pointer_rejected(self):
        self.p['locators'][0]['field_pointer']='/operations/10/temperature'; self.assertFalse(self.check()['passed'])
    def test_no_locators_rejected(self):
        self.p['locators']=[]; self.assertFalse(self.check()['passed'])
    def test_path_traversal_rejected(self):
        self.p['records'][0]['path']='../secret.json'; self.assertFalse(self.check()['passed'])
    def test_unknown_file_rejected(self):
        (self.root/'paper.pdf').write_text('private'); self.assertFalse(self.check()['passed'])
    def test_unaccepted_quote_check_rejected(self):
        self.p['locators'][0]['quote_check']['status']='pending'; self.assertFalse(self.check()['passed'])
    def test_empty_checklist_rejected(self):
        accept(self.p,self.root); self.p['audit']['checklist']={}; self.assertFalse(self.check()['passed'])
    def test_na_requires_reason(self):
        accept(self.p,self.root); self.p['audit']['checklist']['asset_provenance']='not_applicable'; self.assertFalse(self.check()['passed'])
    def test_missingness_is_science(self):
        a=w.canonical_science(w.load(self.root/'records/sample-1.json')); b=copy.deepcopy(a); b['quality']['missing_fields']=[]
        self.assertNotEqual(w.digest(a),w.digest(b))
    def test_presentation_diff_does_not_require_science_audit(self):
        accept(self.p,self.root)
        b=copy.deepcopy(self.p); b['presentation']={'state':'complete','missing_components':[]}
        d=w.diff_packages(self.p,self.root,b,self.root); self.assertFalse(d['scientific_review_required']); self.assertTrue(d['presentation_changed'])
    def test_changed_locator_diff_requires_science_audit(self):
        b=copy.deepcopy(self.p); b['locators'][0]['source_locator']='Wrong figure'
        d=w.diff_packages(self.p,self.root,b,self.root); self.assertTrue(d['scientific_review_required'])
    def test_canonical_errors_not_suppressed(self):
        result=w.validate(self.p,self.root,lambda r:['invalid sample lineage']); self.assertFalse(result['passed'])
    def test_missing_current_validator_not_integration_ready(self):
        accept(self.p,self.root); result=w.validate(self.p,self.root); self.assertTrue(result['passed']); self.assertFalse(result['scientific_package_ready_for_existing_integration_gates'])
    def test_pending_prior_cannot_skip_audit(self):
        d=w.diff_packages(self.p,self.root,self.p,self.root); self.assertTrue(d['scientific_review_required'])
    def test_diff_audit_cannot_claim_unknown_base(self):
        accept(self.p,self.root); self.p['audit']['scope']='scientific_diff'; self.p['audit']['base_scientific_sha256']='f'*64
        self.assertFalse(self.check()['passed'])
    def test_identity_adapter_does_not_promote_missing_receipt(self):
        review={'source_review_promoted':False,'source_group':'paper-a','documents':[{'sha256':'1'*64,'role':'main'}]}
        (self.root/'unreviewed.json').write_text(json.dumps(review)); ids,report=w.identities_from_reviews(self.root)
        self.assertEqual(ids,{})
    def test_collection_change_is_bound(self):
        r=w.load(self.root/'records/sample-1.json'); a=w.canonical_science(r); r['collection']='machine_extracted'; self.assertNotEqual(a,w.canonical_science(r))
    def test_review_status_change_is_bound(self):
        r=w.load(self.root/'records/sample-1.json'); a=w.canonical_science(r); r['quality']['review_status']='source_reviewed'; self.assertNotEqual(a,w.canonical_science(r))
    def test_requested_training_tasks_are_bound(self):
        r=w.load(self.root/'records/sample-1.json'); a=w.canonical_science(r); r['quality']['requested_tasks']=['training']; self.assertNotEqual(a,w.canonical_science(r))
    def test_source_review_and_reuse_claims_bound(self):
        for key in ('main_status','si_status','reuse_status'):
            r=w.load(self.root/'records/sample-1.json'); a=w.canonical_science(r); r['sources'][0][key]='changed claim'; self.assertNotEqual(a,w.canonical_science(r))
    def test_noncanonical_double_separator_rejected(self):
        with self.assertRaises(ValueError): w.safe_file(self.root,'records//sample-1.json')
    def test_bad_pointer_escape_rejected(self):
        with self.assertRaises(ValueError): w.pointer({'~2':'x'},'/~2')
    def test_invalid_prior_identity_cannot_skip_audit(self):
        accept(self.p,self.root); self.p['audit']['author_id']=None
        self.assertTrue(w.diff_packages(self.p,self.root,self.p,self.root)['scientific_review_required'])
    def test_invalid_prior_checklist_cannot_skip_audit(self):
        accept(self.p,self.root); self.p['audit']['checklist']={}
        self.assertTrue(w.diff_packages(self.p,self.root,self.p,self.root)['scientific_review_required'])
    def test_noncanonical_array_pointer_rejected(self):
        for ptr in ('/a/-1','/a/01','/a/+1'):
            with self.assertRaises(ValueError): w.pointer({'a':[0,1]},ptr)
    def test_derived_flag_cannot_hide_unaudited_input(self):
        path=self.root/'false-display.json'; path.write_text('{"temperature":999}')
        self.p['derived_files']=[{'path':'false-display.json','sha256':w.sha(path),'derived_from_science':True}]
        self.assertFalse(self.check()['passed'])
    def test_whitespace_identity_does_not_make_second_reviewer(self):
        accept(self.p,self.root); self.p['audit']['reviewer_id']='author-a '
        self.assertFalse(self.check()['passed'])

def row(h='1',**kw):
    return dict(decision='pass',source_sha256=h*64,preparation_locator='p2',preparation_summary='source screen preparation',
                structure_locator='p3',structure_summary='screen structural evidence',material='CdSe',audit_flags=[],**kw)

class QueueTests(unittest.TestCase):
    def test_duplicate_copies_deduplicate(self):
        result=w.rank_queue([row(),row()]); self.assertEqual(result['unique_document_contents'],1)
    def test_nonpass_excluded(self):
        a=row(); a['decision']='hold'; self.assertEqual(w.rank_queue([a])['unique_document_contents'],0)
    def test_doi_filename_not_identity(self):
        result=w.rank_queue([row(filename='10.1_same.pdf'),row('2',filename='10.1_same_si.pdf')]); self.assertEqual(len(result['ranked_units']),2)
    def test_verified_main_si_grouped_not_blocked(self):
        ids={'1'*64:{'verified':True,'primary_source_id':'p','role':'main'},'2'*64:{'verified':True,'primary_source_id':'p','role':'si'}}
        result=w.rank_queue([row(),row('2')],ids); self.assertEqual(len(result['ranked_units']),1); self.assertEqual(result['unique_document_contents'],2)
    def test_si_alone_retained(self):
        ids={'1'*64:{'verified':True,'primary_source_id':'p','role':'si'}}; result=w.rank_queue([row()],ids); self.assertEqual(len(result['ranked_units']),1)
    def test_already_live_known_source_excluded(self):
        ids={'1'*64:{'verified':True,'primary_source_id':'p','role':'main'}}; self.assertEqual(w.rank_queue([row()],ids,['p'])['unique_document_contents'],0)
    def test_recipe_plus_structure_ranks_first(self):
        a=row(); a['structure_locator']=None; result=w.rank_queue([a,row('2')]); self.assertEqual(result['ranked_units'][0]['documents'][0]['document_sha256'],'2'*64)
    def test_unverified_identity_never_deduplicates(self):
        ids={h*64:{'verified':False,'primary_source_id':'p'} for h in ['1','2']}; self.assertEqual(len(w.rank_queue([row(),row('2')],ids)['ranked_units']),2)

class QuantumDotScopeTests(unittest.TestCase):
    """Synthetic screen rows only; wording mirrors unnormalized screening labels."""
    @staticmethod
    def srow(h='1',**fields):
        r=row(h); r.update(fields); return r
    def scope(self,**kw): return w.quantum_dot_scope(self.srow(**kw))[0]
    def test_colloidal_wording_in(self):
        self.assertEqual(self.scope(preparation_summary='hot injection of TOP-Se into Cd oleate in octadecene'),'in')
    def test_qd_composition_in(self):
        self.assertEqual(self.scope(material='PbS',preparation_summary='precursor reaction'),'in')
    def test_bulk_ceramic_out(self):
        self.assertEqual(self.scope(material='BaTiO3',preparation_summary='solid-state reaction and sintering of ceramic pellets'),'out')
    def test_thin_film_out(self):
        self.assertEqual(self.scope(material='TiO2',preparation_summary='CVD thin film growth on a wafer'),'out')
    def test_mixed_wording_ambiguous(self):
        self.assertEqual(self.scope(material='CdS',preparation_summary='CdS nanocrystals embedded in a glass matrix'),'ambiguous')
    def test_no_wording_ambiguous(self):
        self.assertEqual(self.scope(material='Fe-S',preparation_summary='precursor reaction',structure_summary='XRD'),'ambiguous')
    def test_rank_scope_excludes_out_and_orders_ambiguous_last(self):
        a=self.srow('1',material='BaTiO3',preparation_summary='solid-state reaction, ceramic')
        b=self.srow('2',material='Fe-S',preparation_summary='precursor reaction',structure_summary='XRD')
        c=self.srow('3',material='CdSe',preparation_summary='hot injection')
        result=w.rank_queue([a,b,c],scope='quantum-dot')
        self.assertEqual(result['excluded']['outside_quantum_dot_scope'],1)
        self.assertEqual([u['documents'][0]['document_sha256'][0] for u in result['ranked_units']],['3','2'])
        self.assertEqual(result['scope_check_required_units'],1)
    def test_default_scope_unchanged(self):
        a=self.srow('1',material='BaTiO3',preparation_summary='solid-state reaction, ceramic')
        self.assertEqual(len(w.rank_queue([a])['ranked_units']),1)

class DeepAuditSampleTests(unittest.TestCase):
    def test_deterministic(self):
        h='ab'*32; self.assertEqual(w.deep_audit_selected(h),w.deep_audit_selected(h))
    def test_rate_close_to_ten_percent(self):
        import hashlib
        hits=sum(w.deep_audit_selected(hashlib.sha256(str(i).encode()).hexdigest()) for i in range(20000))
        self.assertTrue(1800<hits<2200, hits)
    def test_rejects_non_digest(self):
        with self.assertRaises(ValueError): w.deep_audit_selected('not-a-hash')
    def test_package_sample_uses_frozen_science(self):
        with tempfile.TemporaryDirectory() as d:
            pkg=fixture(d); first=w.audit_sample(pkg,Path(d)); again=w.audit_sample(copy.deepcopy(pkg),Path(d))
            self.assertEqual(first['deep_audit_required'],again['deep_audit_required'])
            self.assertEqual(first['scientific_sha256'],w.digest(w.science_payload(pkg,Path(d))))
            self.assertTrue(first['quick_audit_still_required'])

class HelperCommandTests(unittest.TestCase):
    def test_log_event_appends_valid_lines(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/'ledger.jsonl'
            w.log_event(ledger,'claimed','paper-a',at='2026-10-01T00:00:00Z')
            w.log_event(ledger,'extraction_frozen','paper-a',at='2026-10-01T00:30:00Z')
            rows=[json.loads(x) for x in ledger.read_text().splitlines()]
            self.assertEqual([r['stage'] for r in rows],['claimed','extraction_frozen'])
            result=w.event_metrics(rows,'2026-10-01T00:00:00Z','2026-10-01T01:00:00Z')
            self.assertEqual(result['new_distinct_source_papers'],0, 'stage events never count as published papers')
    def test_log_event_rejects_live_unknown_and_naive_time(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/'ledger.jsonl'
            for args in (('live_verified','p'),('published','p'),('claimed',' ')):
                with self.assertRaises(ValueError): w.log_event(ledger,*args,at='2026-10-01T00:00:00Z')
            with self.assertRaises(ValueError): w.log_event(ledger,'claimed','p',at='2026-10-01T00:00:00')
    def test_live_sources_from_site_records(self):
        with tempfile.TemporaryDirectory() as d:
            rec=Path(d)/'data'/'records'; rec.mkdir(parents=True)
            (rec/'a.json').write_text(json.dumps({'record_id':'a','lineage':{'source_group':'paper-a'}}))
            (rec/'b.json').write_text(json.dumps({'record_id':'b','lineage':{'source_group':'paper-a'}}))
            (rec/'c.json').write_text(json.dumps({'record_id':'c','lineage':{'source_group':'paper-c'}}))
            self.assertEqual(w.live_sources(d),['paper-a','paper-c'])
            ids={'1'*64:{'verified':True,'primary_source_id':'paper-a','role':'main'}}
            self.assertEqual(w.rank_queue([row()],ids,w.live_sources(d))['excluded']['already_live_verified_source'],1)

def event(eid='e1',source='p1',at='2026-09-26T02:00:00Z',**updates):
    result={'event_id':eid,'at':at,'stage':'live_verified','package_id':source+'-package','primary_source_id':source,
            'source_identity_verified':True,'tier':'gold','record_ids':['r1','r2'],'commit':'a'*40,'url':'https://example.test/material',
            'verification':{'anonymous':True,'passed':True,'receipt_sha256':'b'*64}}
    result.update(updates); return result

class EventTests(unittest.TestCase):
    def calc(self,events): return w.event_metrics(events,'2026-09-26T01:00:00Z','2026-09-26T03:00:00Z')
    def test_variants_one_paper(self):
        r=self.calc([event()]); self.assertEqual(r['new_distinct_source_papers'],1); self.assertEqual(r['new_record_count'],2); self.assertEqual(r['papers_per_elapsed_hour'],0.5)
    def test_duplicate_event_id_idempotent(self):
        self.assertEqual(self.calc([event(),event()])['new_distinct_source_papers'],1)
    def test_conflicting_event_id_rejected(self):
        with self.assertRaises(ValueError): self.calc([event(),event(record_ids=['r9'])])
    def test_republication_not_new_paper(self):
        r=self.calc([event(at='2026-09-26T00:00:00Z'),event('e2',record_ids=['r1','r2','r3'])]); self.assertEqual(r['new_distinct_source_papers'],0); self.assertEqual(r['new_record_count'],1)
    def test_unverified_deploy_not_counted(self):
        r=self.calc([event(stage='deployed')]); self.assertEqual(r['new_distinct_source_papers'],0)
    def test_bad_anon_receipt_not_counted(self):
        r=self.calc([event(verification={'anonymous':False,'passed':True,'receipt_sha256':'b'*64})]); self.assertEqual(r['new_distinct_source_papers'],0)
    def test_gold_silver_separate_promotion_not_new_source(self):
        r=self.calc([event(at='2026-09-26T00:00:00Z',tier='silver'),event('e2',tier='gold')]); self.assertEqual(r['new_distinct_source_papers'],0); self.assertEqual(r['new_gold_source_contributions'],1); self.assertEqual(r['new_silver_source_contributions'],0)
    def test_boundary_end_exclusive(self):
        self.assertEqual(self.calc([event(at='2026-09-26T03:00:00Z')])['new_distinct_source_papers'],0)
    def test_inherited_work_not_new_draft_metric(self):
        r=self.calc([event(stage='extraction_frozen',at='2026-09-26T00:00:00Z'),event('e2')]); self.assertNotIn('extraction_frozen',r['stage_event_counts'])
    def test_unresolved_document_never_paper_credit(self):
        self.assertEqual(self.calc([event(source_identity_verified=False)])['new_distinct_source_papers'],0)
    def test_pr_single_package(self):
        with self.assertRaises(ValueError): self.calc([event(pull_request='pr1'),event('e2','p2',pull_request='pr1')])
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError): self.calc([event(at='2026-09-26T02:00:00')])
    def test_invalid_time_interval_rejected(self):
        with self.assertRaises(ValueError): w.event_metrics([],'2026-09-26T02:00:00Z','2026-09-26T02:00:00Z')
    def test_invalid_git_hash_length_not_live(self):
        self.assertEqual(self.calc([event(commit='a'*41)])['new_distinct_source_papers'],0)
    def test_record_id_string_not_counted_as_characters(self):
        self.assertEqual(self.calc([event(record_ids='not-a-list')])['new_distinct_source_papers'],0)

if __name__=='__main__': unittest.main()
