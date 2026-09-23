import json,hashlib,re,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=O/'private';P.mkdir(exist_ok=True)
ASSETS=O.parents[1];PAIR=ASSETS/'pair-priority-screen-20260922'
RANK=PAIR/'ranker-proposal/final-run-v2/ranked-scopes.jsonl'
DOC=ASSETS/'incoming-paper-monitor/deadline-20260920/workflow-20260920T0412/screen/documents.jsonl'
LEDGER=ASSETS/'incoming-paper-monitor/ledger.json'
BENCH=PAIR/'rubric-audit/verified-benchmark-rows.json'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ranked=[json.loads(x) for x in RANK.open(encoding='utf-8')]
ledger=json.loads(LEDGER.read_text(encoding='utf-8'))
bench=json.loads(BENCH.read_text(encoding='utf-8'))
bench_suffixes={x['doi'].split('/')[-1] for x in bench['rows']}
selected=[];skips=[]
for s in ranked:
    if s['priority_band']!='C_phase_with_local_link_candidate':continue
    group=ledger['groups'].get(s['group_id'])
    reasons=[]
    if not group:reasons.append('current_ledger_identity_missing')
    else:
        if group['generation']!=s['source_generation_in_partition'] or group.get('needs_recheck'):reasons.append('source_generation_or_recheck_hold')
        if group.get('review',{}).get('status') not in ('queued','pending'):reasons.append('already_reviewed_or_active_current_status')
    if s['review_status_in_partition']=='complete':reasons.append('complete_at_partition')
    if any(n in s['group_id'] for n in bench_suffixes):reasons.append('existing_benchmark_scope')
    if s['source_hold']:reasons.append('known_source_hold')
    if s['manual_text_hold']:reasons.append('manual_text_hold')
    if reasons:skips.append({'rank':s['candidate_inspection_rank'],'group_id':s['group_id'],'reasons':reasons});continue
    selected.append(s)
    if len(selected)==10:break
assert len(selected)==10
keys={k for s in selected for k in s['file_keys']}
docs={d['file_key']:d for d in map(json.loads,DOC.open(encoding='utf-8')) if d['file_key'] in keys}
assert set(docs)==keys
files={};scopes=[]
for s in selected:
    scope={'rank':s['candidate_inspection_rank'],'group_id':s['group_id'],'generation':s['source_generation_in_partition'],'file_keys':s['file_keys'],'ranker_source_gaps':s['source_gaps'],'procedure_evidence':s['procedure_evidence'],'candidate_evidence':s['candidate_evidence']}
    for k in s['file_keys']:
        d=docs[k];path=Path(d['source_path']);st=path.stat();h=sha(path);assert h==d['sha256'],k
        textpath=Path(d['text_path']);assert textpath.exists(),k
        stat_after=path.stat();assert (st.st_size,st.st_mtime_ns)==(stat_after.st_size,stat_after.st_mtime_ns)
        files[k]={'file_key':k,'source_path':str(path),'source_sha256':h,'source_bytes':st.st_size,'source_mtime_ns':st.st_mtime_ns,'current_original_hash_verified':True,'historical_role':d['role_candidate'],'detected_format':d['detected_format'],'page_count':d.get('page_count'),'cached_text_path':str(textpath),'cached_text_sha256':sha(textpath),'historical_cache_binding':'historical_source_sha256_bound_current_text_sha256_captured','role_and_identity_verified':False}
    scopes.append(scope)
save(O/'selection-manifest.json',{'started_utc':'2026-09-23T13:02:58+00:00','prepared_utc':datetime.now(timezone.utc).isoformat(),'priority_band_exact':'C_phase_with_local_link_candidate','selection':'first10 eligible in frozen inspection-rank order; no shared claims','selected':scopes,'skips':skips,'bound_inputs':{str(p):sha(p) for p in (RANK,DOC,LEDGER,BENCH)},'scientific_or_training_admission':False})
save(P/'source-inputs.json',{'files':files,'scopes':scopes})
save(O/'progress.json',{'phase':'source_preparation_complete','selected_scopes':10,'receipts_completed':0,'started_utc':'2026-09-23T13:02:58+00:00'})
print(json.dumps({'scopes':[(s['rank'],s['group_id']) for s in scopes],'file_copies':len(files),'unique_hashes':len({x['source_sha256'] for x in files.values()}),'skips':skips},indent=2))
