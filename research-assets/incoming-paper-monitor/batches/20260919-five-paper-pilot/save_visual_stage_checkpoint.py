"""Root-only checkpoint of frozen visuals and Heo SI1-8. No source/Site edits."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
B=Path(__file__).resolve().parent;MON=B.parents[1];M=MON.parents[1]
sys.path.insert(0,str(MON));import monitor
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def verify(m,base):
 n=0
 if isinstance(m,list):m={a['path']:a['sha256'] for a in m}
 for p,h in m.items():
  assert isinstance(h,str) and len(h)==64,(p,h)
  p=Path(p);p=p if p.is_absolute() else base/p
  assert sha(p)==h,str(p);n+=1
 return n
def ref(p):return {'path':str(p),'sha256':sha(p)}
now=datetime.now(timezone.utc).isoformat();lp=MON/'ledger.json';ledger=read(lp)
assert len(monitor.active_claims(ledger))==4
pub=read(MON/'latest-publication.json');assert pub['public_live_version']==29 and pub['deployment']['status']=='succeeded'
scan=read(B/'visual-assets-resume-20260920.json')['counts']
skill=M/'skills/mattersyn-paper-to-site/references/full-paper-review.md';installed=Path(r'[local path redacted]')
assert sha(skill)==sha(installed)
progress={};H=B/'jp0219348';chunks=[]
for pages,tn,an in [([1,2],'si-reflections-transcription.json','si-pages-1-2-independent-audit.json'),([3,4],'si-pages03-04-transcription.json','si-pages-3-4-independent-audit.json'),([5,6],'si-pages05-06-transcription.json','si-pages-5-6-independent-audit.json'),([7,8],'si-pages07-08-transcription.json','si-pages-7-8-independent-audit.json')]:
 t=read(H/tn);a=read(H/an);assert a['status'].startswith('passed')
 verified=verify(a['bound_files'],H);auditor=a.get('auditor',a.get('reviewer'));assert auditor and auditor!=a.get('transcription_author',a.get('author','/root'))
 rows=t['rows'];cells=[c for r in rows for c in r['cells']]
 chunks.append({'pages':pages,'transcription':ref(H/tn),'audit':ref(H/an),'audit_status':a['status'],'rows':len(rows),'numeric_cells':sum(c['evidence']['column_key']!='marker' for c in cells),'markers':sum(c['evidence']['column_key']=='marker' for c in cells),'negative_Fobs2':sum(c['evidence']['column_key']=='Fobs2' and c['numeric_value']<0 for c in cells),'hash_bindings_verified':verified})
hp={'schema':'mattersyn-si-numerical-progress-index/1','at':now,'source_id':'heo2003','source_generation':2,'transcribed_and_independently_audited_pages':list(range(1,9)),'chunks':chunks,'remaining_untranscribed_and_unaudited_pages':list(range(9,15)),'remaining_row_count':None,'complete_SI_numerical_review':False,'exact_structure_pair_created':False,'progress_note':'Aggregates separately audited immutable chunks. Historical pending author statuses are retained; passing external audits bind the corrected artifacts. Pages9-14 still require cell transcription and independent review.','latest_correction_history':ref(H/'si-pages07-08-correction-history.json')}
for k in ['rows','numeric_cells','markers','negative_Fobs2']:hp[k]=sum(c[k] for c in chunks)
assert (hp['rows'],hp['numeric_cells'],hp['markers'],hp['negative_Fobs2'])==(710,4260,710,54)
save(H/'si-numerical-progress-index.json',hp);progress['jp0219348']=hp
g=read(lp)['groups']['10.1021_jp0219348'];d=dict(g['review']['checkpoint']);assert g['generation']==2
d.update(si_numerical_progress=hp,last_substantive_checkpoint_at=now,next_action='Transcribe and independently audit SI pages9-14 from the native scanned table. Preserve all source conflicts and average/disordered structure limitations. Then create canonical records and the illustrated reader; no exact structure-recipe pair yet.')
d['current_work_items']=[{'label':'Main paper and tables','status':'complete','scope':'9 main pages and5main tables independently reviewed.'},{'label':'SI numerical review','status':'in_progress','scope':'SI1-8:710rows/4260numericcells/710markers independently audited;54negative observations preserved. Pages9-14 pending.'},{'label':'Canonical, illustrated reader and publication','status':'in_progress','scope':'Pending; no exact structure pair or training admission.'}]
monitor.checkpoint(lp,'mattersyn-primary',group_id='10.1021_jp0219348',data=d,note='Added independently passed SI5-8 numerical chunks and two preserved/corrected source digits; six SI pages remain pending.')

configs={'la036034c':('nagasaki2004',[('visuals/components/package-freeze.json',['scientific_input_hashes','bound_files']),('visuals/apparatus/author-visual-check.json',['bound_files']),('visuals/products/package-freeze.json',['bound_inputs','output_files'])],['component-source-audit.json','apparatus-source-audit.json','product-source-audit.json']),
 'jp0473669':('ribeiro2004',[('visuals/visual-author-manifest.json',['files','source_inputs'])],['visual-source-audit.json']),
 'ja048427j':('norberg2004',[('visuals/visual-package-manifest.json',['files','upstream'])],['visual-source-audit.json'])}
for suffix,(sid,packages,audits) in configs.items():
 P=B/suffix;cp={'at':now,'source_id':sid,'source_generation':2,'packages':[],'audits':[],'site_integration':'not_performed','browser_validation':'not_performed','publication':'pending','training_admission':False,'public_imports':0}
 for path,maps in packages:
  f=P/path;o=read(f);base=P if suffix=='jp0473669' else f.parent;n=sum(verify(o[k],base) for k in maps)
  cp['packages'].append({**ref(f),'status':o['status'],'counts':o.get('counts',{}),'hash_bindings_verified':n})
 for path in audits:
  f=P/path
  if f.exists():
   a=read(f);binding=a.get('bound_files',a.get('bound_files_sha256',{}));assert binding
   auditor=a.get('auditor',a.get('reviewer'));author=a.get('author',a.get('proposal_author'))
   if not author and suffix=='la036034c' and path=='apparatus-source-audit.json':author=read(P/'visuals/apparatus/author-visual-check.json')['author']
   assert auditor and author and auditor!=author,'Distinct author/auditor identities required: '+str(f)
   n=verify(binding,P);cp['audits'].append({**ref(f),'status':a['status'],'counts':a.get('counts',{}),'hash_bindings_verified':n})
  else:cp['audits'].append({'path':str(f),'status':'pending'})
 passed=all(a['status'].startswith('passed') for a in cp['audits'])
 cp['status']='scoped_visual_audits_passed_integration_pending' if passed else 'visual_author_packages_frozen_independent_review_in_progress'
 cp['remaining_work']='Review product/structure availability and any remaining findings; promote approved scoped bindings into the SAME Site, validate generated data and exercise all affected browser controls, then publish. No publication approval from these private checks.'
 save(P/'visual-progress-checkpoint.json',cp);progress[suffix]=cp
 g=read(lp)['groups']['10.1021_'+suffix];assert g['generation']==2;d=dict(g['review']['checkpoint'])
 d.update(visual_progress=cp,last_substantive_checkpoint_at=now,next_action=cp['remaining_work'],publication_status='pending; private visual proposals only')
 if 'reader_progress' in d:d['reader_progress']['molecular_apparatus_product_visuals']=cp['status']
 d['current_work_items']=[{'label':'Source, canonical and academic reader','status':'complete','scope':'Previously passed separate source/canonical/reader audits; original figures and reported gaps retained.'},{'label':'Molecular, apparatus and product visuals','status':'in_progress','scope':cp['status']},{'label':'Integration, browser and publication','status':'in_progress','scope':cp['remaining_work']}]
 monitor.checkpoint(lp,'mattersyn-primary',group_id='10.1021_'+suffix,data=d,milestones={'extract':{'status':'partial','evidence':[x['path'] for x in cp['packages']],'note':'Frozen private visual proposals prepared; final product bindings and integration pending.'},'audit':{'status':'partial','evidence':[x['path'] for x in cp['audits'] if x['status'].startswith('passed')],'note':'Scope-specific independent audit status retained; integration/browser/publication gates remain.'}},note='Saved frozen private visual packages and exact current independent audit status. No source edit, public import or training admission.')
wf=read(B/'workflow-state.json');idx=read(B/'source-review-index.json')
for target in [wf,idx]:
 target['updated_at']=now
 for paper in target['papers']:
  suffix=paper['group_id'].split('_',1)[1]
  if suffix=='jp0219348':paper['si_numerical_progress']=hp
  elif suffix in configs:
   paper['visual_progress']=progress[suffix];paper['full_extraction']='canonical_reader_and_visual_proposals_prepared_integration_pending';paper['full_scientific_audit']='source_canonical_reader_passed_visual_scope_status_separate'
wf['status']='Gu_published_v29;three_private_visual_packages;Heo_SI1_8_audited_9_14_pending'
wf['latest_queue_snapshot']={'at':scan['last_scan_at'],'source_copies':scan['present_files'],'incoming_copies':scan['source_document_copies']['incoming'],'legacy_copies':scan['source_document_copies']['legacy'],'waiting':scan['waiting_review_scopes'],'active':4,'pending_unscreened_scopes':scan['priority_pending_unscreened_scopes'],'scope':'Dated metadata scan, not a full-paper review or verified unique-paper total.'}
save(B/'workflow-state.json',wf);save(B/'source-review-index.json',idx)
checkpoint={'at':now,'batch_id':wf['batch_id'],'source_priority':'synthesis_and_structure_evidence_richness','latest_scan':wf['latest_queue_snapshot'],'progress':progress,'published_version_unchanged':29,'site_changed_this_stage':False,'active_claims':4,'skill_reference_sha256':sha(skill),'skill_validation':'Project and installed quick_validate both passed.'}
save(B/'visual-stage-progress.json',checkpoint)
heading='## 2026-09-20 — Evidence-priority visual review; Heo SI pages 1–8 audited'
lines=[heading,'',f'Saved {now}. The selected synthesis/structure evidence priority is active in the ledger and existing single heartbeat. Preserve the original five-paper batch; Gu is published and four claims remain active. Runtime capacity is four agents including root, not five simultaneous paper workers. CdSe standards, local-paper-only policy and independent per-paper audits remain. No paper was downloaded or renamed; no Site files changed or new contribution published during this stage. Live Site remains version29/dataset0.22.0.','',f'Latest dated scan {scan["last_scan_at"]}: {scan["present_files"]:,} document copies ({scan["source_document_copies"]["incoming"]:,} incoming + {scan["source_document_copies"]["legacy"]:,} legacy), {scan["waiting_review_scopes"]:,} waiting provisional review scopes and190new/unranked scopes. All four active generation2 bundles matched prior source hashes. Reuse existing corpus screening; refresh new/changed scopes before choosing the next batch. These are not verified unique-paper/material/recipe counts.','',
 'Heo: SI pages1–8 now have four separately frozen, independently passed numerical chunks:710rows,4260numericcells,710uninterpreted markers and54negative Fobs² values. Pages9–14 still need transcription and cell audit; complete SI/CIF/exact structure-recipe eligibility remains false. New pages5–6 passed without correction. Pages7–8 audit found two digits: p7leftrow43,(14,14,22),Fcal²70796.77→79796.77; p7rightrow35,(16,22,22),sigma14787.45→14797.45. Root reopened native crops, preserved earlier versions, corrected only those tokens and obtained a passed recheck. Do not rewrite immutable historical pending author statuses; use current independent audit bindings and si-numerical-progress-index.json.','']
for suffix in configs:
 cp=progress[suffix];lines.extend([f'{cp["source_id"]}: {cp["status"]}. Details: research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/{suffix}/visual-progress-checkpoint.json. Packages: '+ '; '.join(x['path'].split(suffix)[-1]+' SHA256 '+x['sha256'] for x in cp['packages'])+'. Independent audits: '+'; '.join(Path(a['path']).name+' '+a['status']+(' SHA256 '+a['sha256'] if 'sha256' in a else '') for a in cp['audits'])+'.',''])
lines.extend(['Nagasaki:42source-scoped component entries,61material slots,2stocks,14connectivity and8free-molecule conformers independently checked, plus36distinct apparatus scenes. Control audit added two missing PAMA precursor concentration rows and explicit unresolved stock/final basis in three control captions. Source unknown hydration/protonating reagent, symbolic polymers/proteins, pre-dialysis branch, C1–C4 and unresolved TEM/XRD specimen joins remain. Product coordinate availability is a separate proposal; do not substitute a CdSe or ZnO lattice for CdS.','',
 'Ribeiro:13operation scenes,13material-slot proposals,6new and2qualified reused references. Keep water grade, SnCl2 dihydrate, hydroxide counterion, acid-set/post-base pH, model versus measured Sn speciation and main-only SI gap. Norberg:47scenes,73material slots,10qualified cached identities plus9scoped entries,30specimen/context cards and external undoped ZnO cell/192atom illustrative crop. The reference is not measured Mn:ZnO coordinates. Distinct audit corrects inherited labels and the old N2 geometry; use final scoped assets and preserve A–F/D–F source conflicts. See per-package audits for what has actually passed.','',
 f'Project and installed skill synchronized/validated; full-paper-review.md SHA256 {sha(skill)}. Added reference bond-metric checks and per-control concentration/basis visibility. Current checkpoint helper: save_visual_stage_checkpoint.py. Old save_reader_stage_checkpoint.py hardcodes SI1–4 and older intake and must not be rerun. Next: finish outstanding visual/product audits, integrate approved contributions into the SAME MatterSyn Site, browser-check and publish ready papers together; continue Heo9–14 separately. Do not close retained papers before publication. No whole-corpus ETA recalibration until measured pilot throughput supports it.',''])
mem=M/'MEMORY.md';old=mem.read_text(encoding='utf8')
if old.startswith(heading):
 pos=old.find('\n## ',len(heading));old=old[pos+1:] if pos>=0 else ''
mem.write_text('\n'.join(lines)+'\n'+old,encoding='utf8')
print(json.dumps({'at':now,'Heo_audited_rows':hp['rows'],'visual_status':{k:progress[k]['status'] for k in configs},'public_version_unchanged':29,'memory_saved':True}))
