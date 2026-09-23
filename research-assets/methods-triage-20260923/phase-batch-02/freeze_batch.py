import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).resolve().parent;P=O/'private';A=O.parent/'phase-batch-01'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
d=load(P/'source-inputs.json');prior=load(A/'private/source-inputs.json');selection=load(O/'selection-manifest.json')
events=[json.loads(x) for x in (P/'read-events.jsonl').read_text(encoding='utf-8').splitlines()]
visual=[dict(rank=64,role='si',page=1,purpose='Resolve title/authors damaged in cached text'),dict(rank=66,role='si',page=7,purpose='Verify actual refined atom x/y/z and occupancy table'),dict(rank=79,role='main',page=4,purpose='Confirm HAADF layer-stacking image/profile evidence and its limits')]
save(O/'visual-events.json',visual)
reuse=[]
for target,source,batch in [(75,63,'02'),(76,64,'02'),(78,66,'02'),(81,67,'02'),(82,60,'01')]:
 srcdir=O if batch=='02' else A;srcd=d if batch=='02' else prior
 srcscope=next(s for s in srcd['scopes'] if s['rank']==source);targetscope=next(s for s in d['scopes'] if s['rank']==target)
 mapping={}
 for k in targetscope['file_keys']:
  f=d['files'][k];originals=[old for old in srcscope['file_keys'] if srcd['files'][old]['source_sha256']==f['source_sha256'] and srcd['files'][old]['historical_role']==f['historical_role']]
  assert len(originals)==1
  old=originals[0];assert srcd['files'][old]['cached_text_sha256']==f['cached_text_sha256']
  mapping[old]=k
 assert len(mapping)==len(srcscope['file_keys'])
 path=srcdir/f'scope-rank{source:03d}.json';r=load(path);r['rank']=target
 for field in ['group_id','source_generation','source_bindings','coverage']:r.pop(field,None)
 for field in ['method_receipts','structure_receipts']:
  for e in r[field]:
   if 'file_key' in e:e['file_key']=mapping[e['file_key']]
 r['exact_hash_evidence_reuse']=dict(source_batch=batch,source_rank=source,source_receipt_sha256=sha(path),source_and_cached_text_hashes_equal=True,file_key_mapping=mapping,not_a_new_source_read=True)
 save(O/f'scope-rank{target:03d}.json',r);reuse.append(dict(target_rank=target,**r['exact_hash_evidence_reuse']))
save(O/'exact-hash-reuse.json',reuse)
after={k:sha(f['source_path']) for k,f in d['files'].items()};assert all(after[k]==f['source_sha256'] for k,f in d['files'].items())
save(P/'source-hash-after.json',after)
receipts=[]
for s in d['scopes']:
 path=O/f"scope-rank{s['rank']:03d}.json";r=load(path);r['group_id']=s['group_id'];r['source_generation']=s['generation']
 r['source_bindings']=[dict(file_key=k,role=d['files'][k]['historical_role'],source_sha256=d['files'][k]['source_sha256'],cached_text_sha256=d['files'][k]['cached_text_sha256'],source_hash_before_after_equal=True,page_count=d['files'][k]['page_count'],identity_check='content title/authors or exact-source-and-cache-hash reuse',full_source_review_complete=False) for k in s['file_keys']]
 if s['rank'] in (66,78):r['source_pairing']='Main/SI title and author set match with one printed name variation: main Junkai Liu versus SI Junkai Lu. Exact source role/sample review remains partial.'
 for field in ['method_receipts','structure_receipts']:
  for e in r[field]:
   candidates=[f for f in r['source_bindings'] if (f['file_key']==e['file_key'] if 'file_key' in e else f['role']==e['role'])];assert len(candidates)==1
   f=candidates[0];e.update(file_key=f['file_key'],source_sha256=f['source_sha256'],cached_text_sha256=f['cached_text_sha256'],inspection_mode='cached_page_text; visual checks are separately listed; exact-hash reuse explicitly recorded when applicable')
 r['visual_pages']=[v for v in visual if v['rank']==s['rank']]
 r['coverage']=dict(new_full_cached_page_text_read={k:sorted({e['page'] for e in events if e['file_key']==k and e['kind']=='full_cached_page_text_displayed'}) for k in s['file_keys']},all_pages_read=False,unchecked_SI_not_synthesis_negative=True,exact_hash_reuse=r.get('exact_hash_evidence_reuse'),visual_pages=r['visual_pages'])
 r['followup']='focused_atomic_refinement_and_recipe_variant_link_review' if s['rank'] in (66,78) else 'eligible_for_complete_review_after_scope_and_duplicate_resolution'
 assert not r['scientific_admission'] and not r['training_admission'] and not r['full_source_review_complete']
 save(path,r);receipts.append(r)
assert len(receipts)==20 and {r['rank'] for r in receipts}==set(range(63,83))
for item in reuse:
 srcdir=O if item['source_batch']=='02' else A
 source_path=srcdir/f"scope-rank{item['source_rank']:03d}.json"
 item['source_receipt_path']=str(source_path)
 item['source_receipt_sha256']=sha(source_path)
 r=next(r for r in receipts if r['rank']==item['target_rank'])
 r['exact_hash_evidence_reuse']={k:v for k,v in item.items() if k!='target_rank'}
 r['coverage']['exact_hash_reuse']=r['exact_hash_evidence_reuse']
 save(O/f"scope-rank{r['rank']:03d}.json",r)
save(O/'exact-hash-reuse.json',reuse)
now=datetime.now(timezone.utc);start=datetime.fromisoformat(selection['started_utc']);full=[e for e in events if e['kind']=='full_cached_page_text_displayed'];ids=[e for e in events if e['kind']=='identity_excerpt_displayed'];idx=[e for e in events if e['kind']=='machine_search_index_only']
summary=dict(status='frozen_partial_methods_first_triage',started_utc=start.isoformat(),finished_utc=now.isoformat(),elapsed_seconds=(now-start).total_seconds(),timing_scope='Includes selection, current source hashing, identity checks, targeted reading/viewing, receipt preparation and context overhead; selected ranked positives, not a corpus throughput estimate.',scopes=20,scope_ranks=list(range(63,83)),file_copies=37,unique_source_hashes=30,unique_source_hashes_new_to_this_pass=28,distinct_DOI_identities=16,new_DOI_identities_after_batch01=15,exact_hash_scope_reuses=5,explicit_target_synthesis_positive_scopes=20,atomic_table_followup_scopes=[66,78],atomic_table_followup_distinct_papers=1,other_phase_morphology_structure_candidates=18,verified_atomic_coordinate_pairs=0,scientific_admissions=0,training_admissions=0,automatic_exclusions=0,original_hashes_before_after_equal=True,
 counts=dict(full_cached_page_text_read_events=len(full),unique_full_cached_pages_read=len({(e['source_sha256'],e['page']) for e in full}),identity_excerpt_events=len(ids),unique_new_identity_sources=len({e['source_sha256'] for e in ids}),machine_index_page_events=sum(e['indexed_pages'] for e in idx),machine_index_is_not_human_read=True,new_rendered_pages_viewed=len(visual),exact_hash_reuse_not_counted_as_new_read=True),
 missing_local_si_scope_ranks=[s['rank'] for s in d['scopes'] if not any(d['files'][k]['historical_role']=='si' for k in s['file_keys'])],
 scope_results=[dict(rank=r['rank'],group_id=r['group_id'],title=r['title'],synthesis_presence=r['synthesis_presence'],structure_level=r['structure_level'],coordinates=r['coordinates'],followup=r['followup'],reused_evidence=bool(r.get('exact_hash_evidence_reuse'))) for r in receipts],
 limitations=['Partial Methods-first triage only; full sources/variants, exact aliquot joins and scientific/training readiness are unclaimed.','Ranks66/78 are one exact-source duplicate paper with a present source-refined average/disordered atomic table; exact recipe variant and refinement constraints remain unresolved.','Rank80 has explicit external Materials Project coordinate models, not current-product measured atom positions.','Rank79 layer-stacking images and rank74 disordered carbon evidence are separate from complete atom datasets.','Historical cached text is bound to historically recorded source hashes; current original source and cached-text hashes verified. Only listed original pages were visually inspected.','Missing and unchecked SI never treated as synthesis-negative; distinct scopes preserved, duplicate paper evidence is not a new scientific pair.'])
save(O/'summary.json',summary);save(O/'progress.json',dict(phase='frozen',receipts_completed=20,started_utc=start.isoformat(),finished_utc=now.isoformat()))
(O/'README.md').write_text('# Phase batch 02: partial Methods-first triage\n\nTwenty eligible scopes, ranks63–82, retain explicit target-synthesis evidence after targeted checking. These represent16 DOI identities,15 new to the Methods triage; five scope receipts reuse exact source and cache hashes. All37 original copies remain unchanged.\n\nOne distinct paper (ranks66/78) contains an actual Rietveld-refined atom-position table and merits focused recipe-variant/refinement follow-up. It is an average, partially occupied crystal model; no verified atomic pair or admission is made. Other scopes support phase, morphology or layer/disordered structure evidence. Explicit Materials Project models at rank80 remain external.\n\nSee summary.json for elapsed timing and actual new read/view counts. Selection/skips, source-bound concise receipts and exact-hash reuse are saved separately. Raw page renders and source paths/cache bindings stay private. Missing/unchecked SI is unresolved, never synthesis-negative. No full scientific review, training admission, exclusion or shared-state mutation.\n',encoding='utf-8')
save(O/'author-freeze.json',dict(frozen_utc=now.isoformat(),scope='author freeze; partial source triage only',files={str(p.relative_to(O)).replace('\\','/'):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='author-freeze.json'},scientific_admission=False,training_admission=False))
print(json.dumps({k:v for k,v in summary.items() if k not in ('scope_results','limitations')},indent=2));print('FREEZE',sha(O/'author-freeze.json'));print('SUMMARY',sha(O/'summary.json'))
