"""Root-only durable batch checkpoint, preserving all publication gates."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import sys

B=Path(__file__).resolve().parent
MON=B.parents[1]
sys.path.insert(0,str(MON))
import monitor
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
now=dt.datetime.now(dt.timezone.utc).isoformat()
state=read(B/'workflow-state.json')
audit_map={'jp0473669':'author_file_hashes','ja0496423':'bound_files','la036034c':'author_artifact_sha256','ja048427j':'audited_artifacts'}
figure_counts={'jp0219348':7,'ja0496423':7,'la036034c':8,'jp0473669':7,'ja048427j':13}
table_counts={'jp0219348':5,'ja0496423':0,'la036034c':0,'jp0473669':0,'ja048427j':4}
rows=[]
for paper in state['papers']:
 key=paper['group_id'].split('_')[-1];P=B/key
 docs=read(P/'intake-manifest.json')['documents']
 for d in docs:assert sha(Path(d['path']))==d['sha256'],d['path']
 inventory=read(P/'source-inventory.json');facts=read(P/'source-facts.json')
 assert isinstance(facts['facts'],list)
 count=len(facts['facts'])
 audit_path=P/'source-scientific-audit.json'
 audit=read(audit_path) if audit_path.exists() else None
 source_pass=key in audit_map
 main_audit_pass=bool(audit and audit.get('status','').startswith('passed'))
 audit_binding_checks=[]
 if source_pass:
  assert audit['status'].startswith('passed'),key
  for rel,expected in audit[audit_map[key]].items():
   if isinstance(expected,str) and len(expected)==64:
    target=P/rel
    assert target.exists() and sha(target)==expected,(key,rel)
    audit_binding_checks.append(rel)
  assert 'source-facts.json' in audit_binding_checks and 'source-inventory.json' in audit_binding_checks
 if key=='jp0219348' and main_audit_pass:
  assert audit['overall_source_extraction_complete'] is False
  assert audit['si_numerical_audit_complete'] is False
  for artifact in audit['audited_artifacts']:
   target=Path(artifact['path'])
   assert target.is_relative_to(P) and sha(target)==artifact['sha256'],str(target)
   audit_binding_checks.append(str(target.relative_to(P)))
  assert {'source-facts.json','source-inventory.json','main-tables.json'}.issubset(audit_binding_checks)
 page_note=(f"All {paper['main_pages']} supplied main pages and {paper['si_pages']} matched SI pages text-read and visually inspected." if paper['si_pages'] else 'All 6 supplied main pages text-read and visually inspected; SI not located/verified, existence remains unverified.')
 if key=='jp0219348':page_note='All 9 main pages read/viewed. All 14 scanned SI pages inspected for identity, continuity and reflection-table scope; every numerical cell has NOT been individually transcribed/audited.'
 source_note=(f'{count} typed source facts extracted and independently audited; all supplied-source items inventoried. Canonical and reader completion gates remain separate.' if source_pass else f'{count} main narrative facts and five transcribed main tables available. '+('Independent main narrative/table audit passed; ' if main_audit_pass else 'Independent audit in progress; ')+'SI reflection numerical transcription remains pending.')
 canonical_dir=P/'canonical-drafts'
 drafts=list(canonical_dir.glob('*.json')) if canonical_dir.exists() else []
 canonical_manifest_path=P/'canonical-record-manifest.json'
 canonical_manifest=read(canonical_manifest_path) if canonical_manifest_path.exists() else None
 if canonical_manifest:
  assert not canonical_manifest['published'] and not canonical_manifest['training_eligible']
  assert len(drafts)==canonical_manifest['counts']['records']
  assert canonical_manifest['source_inventory_sha256']==sha(P/'source-inventory.json')
  assert canonical_manifest['source_facts_sha256']==sha(P/'source-facts.json')
  assert canonical_manifest['source_extraction_audit_sha256']==sha(audit_path)
  for record in canonical_manifest['records']:
   target=Path(record['path'])
   assert target.is_relative_to(canonical_dir) and sha(target)==record['sha256'],str(target)
 canonical_audit_path=P/'canonical-records-audit.json'
 canonical_audit=read(canonical_audit_path) if canonical_audit_path.exists() else None
 canonical_pass=bool(canonical_audit and canonical_audit['status']=='passed')
 canonical_binding_checks=[]
 if canonical_pass:
  assert canonical_audit['auditor']!=canonical_audit['canonical_author']
  assert not canonical_audit['open_findings']
  assert not canonical_audit['publication_approved'] and not canonical_audit['training_eligibility_approved']
  for rel,expected in canonical_audit['bound_files'].items():
   assert sha(P/rel)==expected,(key,rel)
   canonical_binding_checks.append(rel)
  assert len(canonical_audit['bound_record_files'])==len(drafts)
  for name,expected in canonical_audit['bound_record_files'].items():
   assert sha(canonical_dir/name)==expected,(key,name)
   canonical_binding_checks.append('canonical-drafts/'+name)
 canonical_note=(f"{len(drafts)} private drafts are schema-valid: {canonical_manifest['counts']['record_types']['literature_protocol']} synthesis route, {canonical_manifest['counts']['record_types']['procedure']} procedures and {canonical_manifest['counts']['record_types']['observation']} context records. " if canonical_manifest else f'{len(drafts)} private draft files currently present. ')
 canonical_note+=('Independent canonical scientific audit passed; exact artifact hashes verified. ' if canonical_pass else 'Independent canonical audit has unresolved findings. ' if canonical_audit else 'Independent canonical audit remains pending. ')
 canonical_note+='No public canonical imports or training admission.'
 audit_scope=audit['scope'] if audit else 'Independent nine-page narrative/table audit in progress; no full SI numerical audit claimed.'
 if isinstance(audit_scope,dict):audit_scope=' '.join(str(value) for value in audit_scope.values())
 reuse_path=P/'visual-reuse-audit.json'
 reuse=read(reuse_path) if reuse_path.exists() else None
 if reuse:
  assert not reuse['published'] and not reuse['all_binding_approvals']
  for rel,field in [('visual-reuse-plan.json','plan_sha256'),('source-facts.json','source_facts_sha256'),('source-inventory.json','source_inventory_sha256')]:
   assert sha(P/rel)==reuse[field],(key,rel)
  reuse_plan=read(P/'visual-reuse-plan.json')
  assert sha(Path(reuse_plan['registry_path']))==reuse['registry_sha256']
  for path,expected in reuse['inspected_asset_hashes'].items():assert sha(Path(path))==expected,path
  for preview in reuse['previews']:assert sha(Path(preview['path']))==preview['sha256'],preview['path']
  assert sha(Path(reuse['contact_sheet']['path']))==reuse['contact_sheet']['sha256']
  assert len(reuse['results'])==reuse['checked_candidates']
 visual_note='Five academic sections, molecular/crystal context, operation-specific scenes, independent binding/visual checks and browser review still required before release.'
 if reuse:visual_note='Nine existing molecular candidates inspected: four named references qualified; four require source-specific labels; nitrogen 3D held for geometry correction. Eight new depictions remain pending. '+visual_note
 work=[
  {'label':'Source reading and extraction','status':'complete' if source_pass else 'partial','scope':page_note+' '+source_note},
  {'label':'Independent source audit','status':'complete' if source_pass else 'partial' if main_audit_pass else 'in_progress','scope':audit_scope},
  {'label':'Canonical records and training labels','status':'in_progress' if drafts else 'pending','scope':canonical_note},
  {'label':'Reader visuals, integration and publication','status':'in_progress' if reuse else 'pending','scope':visual_note}
 ]
 cp={'title':paper['title'],'review_package':str(P),'si_status':page_note,
  'main_pages_text_reviewed':list(range(1,paper['main_pages']+1)),
  'main_pages_visually_reviewed':list(range(1,paper['main_pages']+1)),
  'si_pages_visually_inspected':list(range(1,paper['si_pages']+1)),
  'source_typed_facts':count,'private_typed_draft_records':len(drafts),'canonical_records_created':0,
  'original_figures':figure_counts[key],'original_tables':table_counts[key],
  'current_work_items':work,'source_extraction_status':'passed_independent_source_audit' if source_pass else 'partial_main_tables_available_si_numeric_pending',
  'source_scientific_audit_status':audit['status'] if audit else 'pending',
  'canonical_scientific_audit_status':canonical_audit['status'] if canonical_audit else 'pending',
  'private_canonical_drafts_audited':len(drafts) if canonical_pass else 0,
  'visual_reuse_qualification_status':reuse['status'] if reuse else 'pending',
  'next_action':('Prepare the Gu five-section reader, missing molecule models, stage-specific apparatus and scoped crystal presentation; then independently verify bindings and browser behavior before publication.' if canonical_pass else 'Resolve and verify the independent Gu canonical audit; prepare the five-section reader and molecule/apparatus/crystal presentation.' if key=='ja0496423' else 'Finish explicitly tracked scanned-SI numerical work and structure validation; preserve source-condition conflicts before full review promotion.' if key=='jp0219348' and main_audit_pass else 'Complete independent main narrative/table audit and explicitly tracked scanned-SI numerical work before full review promotion.' if key=='jp0219348' else 'Prepare canonical records and five-section reader with source figures, molecular/apparatus/crystal visuals; then independently validate and publish with other ready contributions.'),
  'last_substantive_checkpoint_at':now,'publication_status':'pending; existing public Site unchanged by this batch',
  'source_review_checkpoint':str(P/'source-review-checkpoint.json')}
 evs=[str(P/'source-facts.json'),str(P/'source-inventory.json')]
 if (P/'main-tables.json').exists():evs.append(str(P/'main-tables.json'))
 milestones={
  'read':{'status':'complete' if source_pass else 'partial','evidence':[str(P/'page-coverage.json')],'note':page_note},
  'extract':{'status':'partial','evidence':evs,'note':source_note+' Canonical/reader integration not complete.'},
  'audit':{'status':'partial','evidence':[str(audit_path)] if audit else [str(P/'screening-audit.json')],'note':('Independent supplied-source audit passed; canonical, visuals, integration and training checks remain pending.' if source_pass else 'Main narrative/table audit passed; full SI numerical and downstream audits not complete.' if main_audit_pass else 'Main narrative/table scientific audit in progress; full SI numerical and downstream audits not complete.')},
  'integrate':{'status':'pending','evidence':[],'note':'No current-batch contribution imported into the Site.'},
  'publish':{'status':'pending','evidence':[],'note':'No current-batch contribution published. Existing public Site remains version28/dataset0.21.0.'}}
 if canonical_pass:
  milestones['audit']['evidence'].append(str(canonical_audit_path))
  milestones['audit']['note']='Independent source and canonical scientific audits passed. Reader, molecular/crystal/apparatus, binding, browser and training-admission checks remain pending.'
 package={'at':now,'group_id':paper['group_id'],'checkpoint':cp,'milestones':milestones,'bound_files':{n:sha(P/n) for n in ['source-facts.json','source-inventory.json','page-coverage.json']},'audit_binding_files_verified':audit_binding_checks,'canonical_audit_binding_files_verified':canonical_binding_checks,'full_paper_curation_complete':False}
 save(P/'source-review-checkpoint.json',package)
 out=monitor.checkpoint(MON/'ledger.json','mattersyn-primary',data=cp,milestones=milestones,group_id=paper['group_id'],note='Substantive full-source extraction progress and separate independent audit checkpoints; canonical, visual and publication gates retained.')
 assert out['claim_retained'] and out['active_review_claims']==5
 paper.update(full_extraction='source_extraction_audited_canonical_pending' if source_pass else 'main_narrative_and_tables_extracted_si_numeric_pending',full_scientific_audit='source_audit_passed_downstream_audits_pending' if source_pass else 'main_narrative_table_audit_passed_si_numeric_pending' if main_audit_pass else 'partial_source_scope_audit_in_progress',publication='pending',typed_source_facts=count,checkpoint=str(P/'source-review-checkpoint.json'))
 if canonical_pass:paper.update(full_extraction='canonical_audited_reader_pending',full_scientific_audit='source_and_canonical_passed_reader_visual_training_pending')
 rows.append({'group_id':paper['group_id'],'title':paper['title'],'source_fact_count':count,'source_audit':audit['status'] if audit else 'pending','passed_supplied_source_audit':source_pass,'private_canonical_draft_files':len(drafts),'files':{n:{'path':str(P/n),'sha256':sha(P/n)} for n in ['source-facts.json','source-inventory.json','page-coverage.json','source-review-checkpoint.json']},'canonical_imports':0,'published':False})
state.update(updated_at=now,status='four_supplied_source_extractions_audited; Heo_main_and_tables_with_SI_numeric_gap; canonical_and_site_work_pending')
state['source_review_summary']={'papers_with_passed_supplied_source_extraction_audit':sum(r['passed_supplied_source_audit'] for r in rows),'papers_with_partial_source_numeric_scope':sum(not r['passed_supplied_source_audit'] for r in rows),'papers_with_passed_main_scope_audit':sum(r['source_audit'].startswith('passed') for r in rows),'total_typed_source_facts':sum(r['source_fact_count'] for r in rows),'private_canonical_draft_files':sum(r['private_canonical_draft_files'] for r in rows),'new_public_contributions':0,'no_recipe_skips_in_batch':0,'exact_structure_recipe_pairs_created':0,'queue_batch_preserved':True}
save(B/'workflow-state.json',state)
save(B/'source-review-index.json',{'at':now,'batch_id':state['batch_id'],'scope':'private source extraction/audit checkpoint; not a canonical training export or public-release manifest','papers':rows,'summary':state['source_review_summary']})
print(json.dumps(state['source_review_summary']))
