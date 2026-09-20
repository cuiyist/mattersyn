"""Save verified release/progress without rerunning or relabeling source audits."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,sys,shutil
B=Path(__file__).resolve().parent;MON=B.parents[1];G=B/'ja0496423'
sys.path.insert(0,str(MON));import monitor
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
now=datetime.now(timezone.utc).isoformat()
publication=read(G/'publication-checkpoint.json')
assert publication['deployment']['status']=='succeeded' and publication['anonymous_verification']['status']=='passed'
publication.update(status='published_and_anonymously_verified',public_live_version=publication['version']['version_number'],published_at=publication['deployment']['updated_at'],public_url=publication['deployment']['url'])
save(G/'publication-checkpoint.json',publication)
save(MON/'latest-publication.json',publication)
ledger_path=MON/'ledger.json'
old=read(ledger_path)
gu=old['groups']['10.1021_ja0496423']
assert gu['generation']==2
data=dict(gu['review']['checkpoint'])
data.update(canonical_records_created=10,private_typed_draft_records=10,reader_items=138,original_figures=7,original_tables=1,source_original_assets=12,source_units_covered=126,protocol_scenes=33,material_viewer_bindings=28,publication_status='Published to existing public Site version 29; anonymous access verified',last_substantive_checkpoint_at=now,next_action='Current retained Gu main/SI scope complete. Reopen if source content or matching SI changes; continue other four batch members.',visual_reuse_qualification_status='Final corrected/scoped bindings independently audited; new Gu N2 reference replaces blocked reuse',canonical_scientific_audit_status='passed',reader_scientific_audit_status='passed',visual_audit_status='passed',browser_validation_status='passed',publication_checkpoint=str(G/'publication-checkpoint.json'),training_rows={'precursor_selection':1,'partial_protocol':2,'exact_structure_recipe':0})
data['current_work_items']=[{'label':label,'status':'complete','scope':scope} for label,scope in [('Source reading and extraction','All 2 main and 3 matched SI pages, 95 facts and 126 source units retained.'),('Independent scientific and visual audits','Source, canonical, reader, molecular, apparatus, product, promotion and integration scopes passed; original source conflicts retained.'),('Interactive reader and machine records','10 canonical records: 1 route, 6 procedures, 3 contexts; 138 reader items, 33 scenes, 28 viewers, 12 original assets.'),('Publication','Existing public Site version 29 succeeded; five anonymous routes verified.')]]
milestones={
 'read':{'status':'complete','evidence':[str(G/'page-coverage.json'),str(G/'source-scientific-audit.json')],'note':'Complete supplied 2 main + 3 matched SI source scope.'},
 'extract':{'status':'complete','evidence':[str(G/'source-inventory.json'),str(G/'canonical-record-manifest.json'),str(G/'reader-source-audit.json')],'note':'All source units retained and mapped; 10 record types do not mean 10 synthesis recipes.'},
 'audit':{'status':'complete','evidence':[str(G/name) for name in ['source-scientific-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','apparatus-source-audit.json','product-source-audit.json','promotion-source-audit.json','integration-source-audit.json','integration-source-audit-addendum.json']],'note':'Independent audits passed for exact frozen scientific/artifact content.'},
 'integrate':{'status':'complete','evidence':[str(G/'integration-manifest.json'),str(G/'browser-validation.json'),str(G/'build-check-output.json')],'note':'Existing atlas plus dataset integrated; source-specific interactive visual behavior checked.'},
 'publish':{'status':'complete','evidence':[str(G/'publication-checkpoint.json')],'note':'Native public deployment succeeded and actual source/data anonymous delivery verified.'}}
if gu['review']['status']!='complete':
 result=monitor.checkpoint(ledger_path,'mattersyn-primary',status='complete',group_id='10.1021_ja0496423',data=data,milestones=milestones,note='Gu complete retained-source review, independent audits, illustrated reader and public v29 release.')
 save(G/'release-ledger-checkpoint.json',{'at':now,'data':data,'milestones':milestones,'result':result})

# Fresh private progress does not promote record review_status or training gates.
packages={'la036034c':16,'jp0473669':11,'ja048427j':19}
progress={}
for suffix,n in packages.items():
 P=B/suffix;manifest=read(P/'canonical-record-manifest.json');drafts=list((P/'canonical-drafts').glob('*.json'))
 assert len(drafts)==n
 audit_path=P/'canonical-records-audit.json'
 audit=read(audit_path) if audit_path.exists() else None
 passed=bool(audit and str(audit.get('status','')).startswith('passed'))
 if passed:
  bindings=audit.get('bound_files',audit.get('file_hashes',{}))
  if isinstance(bindings,dict):
   for name,h in bindings.items():
    if isinstance(h,str) and len(h)==64:assert sha(name)==h,name
 package={'private_canonical_drafts':n,'canonical_audit':'passed' if passed else 'pending','manifest_sha256':sha(P/'canonical-record-manifest.json'),'audit_path':str(audit_path) if audit else None,'audit_sha256':sha(audit_path) if audit else None,'reader_visuals_integration_publication':'pending','public_imports':0,'at':now}
 progress[suffix]=package
 grp=read(ledger_path)['groups']['10.1021_'+suffix];d=dict(grp['review']['checkpoint'])
 d.update(private_typed_draft_records=n,canonical_scientific_audit_status=package['canonical_audit'],canonical_records_created=0,publication_status='pending; private canonical package only',last_substantive_checkpoint_at=now,next_action=('Prepare full source reader and chemical/protocol/product visuals, independently audit and integrate.' if passed else 'Complete independent canonical audit, then prepare reader and scientific visuals.'))
 d['current_work_items']=[{'label':'Source extraction','status':'complete','scope':'Passed audit of retained supplied source scope; missing SI remains a source gap where applicable.'},{'label':'Canonical scientific audit','status':'complete' if passed else 'in_progress','scope':f'{n} private canonical drafts; '+('independent audit passed' if passed else 'independent audit pending')+'; no public imports or training admission.'},{'label':'Reader, illustrations and publication','status':'in_progress','scope':d['next_action']}]
 ms={'extract':{'status':'partial','evidence':[str(P/'canonical-record-manifest.json')],'note':'Canonical drafts mapped; reader and visualization coverage still required.'},'audit':{'status':'partial','evidence':[str(audit_path if passed else P/'source-scientific-audit.json')],'note':'Source'+(' and canonical' if passed else '')+' audit passed; downstream reader/visual/integration audits remain pending.'}}
 monitor.checkpoint(ledger_path,'mattersyn-primary',group_id='10.1021_'+suffix,data=d,milestones=ms,note='Saved private canonical package and precise independent-audit status.')
 save(P/'canonical-progress-checkpoint.json',package)

H=B/'jp0219348';hc=read(H/'si-numerical-verification-checkpoint.json')
ha=H/'si-pages-1-2-independent-audit.json';hap=read(ha) if ha.exists() else None
hp={'at':now,'transcribed_si_pages':[1,2],'transcribed_rows':170,'numeric_cells':1020,'markers':170,'remaining_si_pages':list(range(3,15)),'independent_numeric_audit':'passed' if hap and str(hap.get('status','')).startswith('passed') else 'pending','checkpoint_sha256':sha(H/'si-numerical-verification-checkpoint.json')}
progress['jp0219348']=hp
grp=read(ledger_path)['groups']['10.1021_jp0219348'];d=dict(grp['review']['checkpoint']);d.update(si_numerical_progress=hp,last_substantive_checkpoint_at=now,next_action='Continue SI pages 3–14 numerical transcription and independent cell audit. Pages 1–2 are a bounded subset, not a completed supplement.')
d['current_work_items']=[{'label':'Main paper and tables','status':'complete','scope':'All 9 main pages and 5 main tables have separate source-scientific review.'},{'label':'SI numerical transcription','status':'in_progress','scope':'Pages 1–2: 170 rows, 1,020 numeric cells, 170 markers. Independent numerical audit '+hp['independent_numeric_audit']+'. Pages 3–14 remain pending.'},{'label':'Canonical, reader and publication','status':'in_progress','scope':'Retain source conflicts and average-structure limits; no CIF or exact coordinate–recipe pair admitted.'}]
monitor.checkpoint(ledger_path,'mattersyn-primary',group_id='10.1021_jp0219348',data=d,note='Saved bounded SI pages 1–2 transcription; remaining numerical scope explicit.')
save(B/'presentation-progress.json',{'at':now,'gu_publication':publication,'private_packages':progress,'batch_complete':False})
wf=read(B/'workflow-state.json');wf['updated_at']=now;wf['status']='Gu_published_v29; other_four_active_with_frozen_canonical_or_partial_SI_work'
for paper in wf['papers']:
 suffix=paper['group_id'].split('_',1)[1]
 if suffix=='ja0496423':paper.update(publication='published_v29',full_extraction='complete_supplied_main_and_matched_SI',full_scientific_audit='passed_all_source_canonical_reader_visual_integration_scopes',publication_checkpoint=str(G/'publication-checkpoint.json'))
 elif suffix in packages:paper.update(full_extraction='canonical_drafts_frozen_reader_pending',full_scientific_audit='source_and_canonical_passed_reader_visual_pending' if progress[suffix]['canonical_audit']=='passed' else 'source_passed_canonical_audit_pending',canonical_progress=progress[suffix])
 else:paper['si_numerical_progress']=hp
wf['source_review_summary'].update(private_canonical_draft_files=56,new_public_contributions=1,canonical_records_imported=10,exact_structure_recipe_pairs_created=0)
wf['latest_queue_snapshot']={'at':'2026-09-19T21:57:00Z','source_copies':13555,'waiting':9245,'active_after_release':4,'historically_closed_after_release':19,'scope':'Latest scanned corpus snapshot; no new full scan at release.'}
save(B/'workflow-state.json',wf)
idx=read(B/'source-review-index.json');idx['updated_at']=now
idx['summary'].update(private_canonical_draft_files=56,new_public_contributions=1,canonical_records_imported=10)
for item in idx['papers']:
 suffix=item['group_id'].split('_',1)[1]
 if suffix=='ja0496423':item.update(private_canonical_draft_files=10,canonical_imports=10,published=True,publication_checkpoint=str(G/'publication-checkpoint.json'))
 elif suffix in packages:item.update(private_canonical_draft_files=packages[suffix],canonical_progress=progress[suffix])
 else:item['si_numerical_progress']=hp
save(B/'source-review-index.json',idx)
print(json.dumps({'gu_published':True,'active_claims':len(monitor.active_claims(read(ledger_path))),'private_packages':progress},ensure_ascii=False))
