"""Read-only source preparation for ten bounded nomination screens."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
import pypdfium2 as pdfium
O=Path(__file__).resolve().parent;P=O/'private';P.mkdir(exist_ok=True)
PAIR=O.parents[1];RUN=PAIR/'ranker-proposal/final-run-v2'
DOC=PAIR.parent/'incoming-paper-monitor/deadline-20260920/workflow-20260920T0412/screen/documents.jsonl'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ranked=[json.loads(x)for x in (RUN/'ranked-scopes.jsonl').open(encoding='utf-8')]
bench=json.loads((PAIR/'rubric-audit/verified-benchmark-rows.json').read_text(encoding='utf-8'))
benchdois={x['doi'].split('/')[-1]for x in bench['rows']}
selected=[];skips=[]
ledger_path=PAIR.parent/'incoming-paper-monitor/ledger.json'
ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
save(O/'timing-start.json',{'started_at':'2026-09-23T13:02:44+00:00','basis':'Actual clock tool before first batch read','mode':'timed_methods_first_triage','no_paid_processing':True})
current=[]
for x in ranked:
    if x['candidate_inspection_rank']<=23:continue
    if not x['priority_band'].startswith(('A_','B_')):continue
    g=ledger['groups'].get(x['group_id'],{});reason=None
    if any(n in x['group_id']for n in benchdois):reason='existing_audited_benchmark'
    elif g.get('review',{}).get('status')=='complete' or x['review_status_in_partition']=='complete':reason='existing_completed_source_scope'
    elif x['source_hold']:reason='source_identity_or_role_hold'
    elif g.get('generation')!=x['source_generation_in_partition'] or g.get('needs_recheck'):reason='generation_or_recheck_hold'
    current.append({'rank':x['candidate_inspection_rank'],'group_id':x['group_id'],'generation':g.get('generation'),'review_status':g.get('review',{}).get('status'),'needs_recheck':g.get('needs_recheck'),'reason':reason})
    if reason:skips.append({**x,'skip_reason':reason});continue
    selected.append(x)
    if len(selected)==10:break
documents={d['file_key']:d for d in map(json.loads,DOC.open(encoding='utf-8'))}
files={};scopes=[]
for s in selected:
    scope={'selection':s,'files':[]}
    for key in s['file_keys']:
        d=documents[key];path=Path(d['source_path']);h=sha(path);assert h==d['sha256'],(path,h,d['sha256'])
        fid=h[:12];f={'file_key':key,'path':str(path),'sha256':h,'bytes':path.stat().st_size,'historical_role':d['role_candidate'],'detected_format':d['detected_format']}
        if h not in files:
            if d['detected_format']!='pdf':
                files[h]={**f,'pdf_page_count':None,'prepared_pages':[],'inspection_pending':True}
                scope['files'].append(f)
                continue
            pdf=pdfium.PdfDocument(str(path));n=len(pdf)
            pages={1}|{e['locator']['page']for e in s['candidate_evidence']+s['procedure_evidence']if e['source_sha256']==h and e['locator']['page']}
            paths=[]
            for pno in sorted(pages):
                assert 1<=pno<=n
                page=pdf[pno-1];text=page.get_textpage().get_text_range();tp=P/f'{fid}-p{pno:03d}.txt';ip=P/f'{fid}-p{pno:03d}.png'
                tp.write_text(text,encoding='utf-8');page.render(scale=2).to_pil().save(ip)
                paths.append({'pdf_page':pno,'text':str(tp),'text_sha256':sha(tp),'render':str(ip),'render_sha256':sha(ip)})
            files[h]={**f,'pdf_page_count':n,'prepared_pages':paths,'renderer':'pypdfium2 scale2 (144dpi)','visual_inspection_claimed':False}
            pdf.close()
        scope['files'].append(f)
    scopes.append(scope)
save(P/'source-preparation.json',{'created_at':datetime.now(timezone.utc).isoformat(),'source_files':files,'scope_inputs':scopes})
save(O/'skip-and-current-state.json',{'captured_at':datetime.now(timezone.utc).isoformat(),'ledger_sha256_at_read':sha(ledger_path),'group_states':current,'skips':[{'rank':x['candidate_inspection_rank'],'group_id':x['group_id'],'reason':x['skip_reason']}for x in skips]})
save(O/'selection-manifest.json',{'status':'bounded_source_role_screening_in_progress_independent_audit_pending','author':'/root/backlog_eta','selected_scope_count':len(scopes),'selected_ranks':[x['selection']['candidate_inspection_rank']for x in scopes],'skipped_existing_benchmarks':[{'rank':x['candidate_inspection_rank'],'group_id':x['group_id'],'qualification_source':str(PAIR/'rubric-audit/verified-benchmark-rows.json')}for x in skips],'scopes':[{'rank':x['selection']['candidate_inspection_rank'],'group_id':x['selection']['group_id'],'source_sha256s':x['selection']['source_hashes']}for x in scopes],'bound_files':{str(RUN/'summary.json'):sha(RUN/'summary.json'),str(RUN/'ranked-scopes.jsonl'):sha(RUN/'ranked-scopes.jsonl'),str(DOC):sha(DOC),str(PAIR/'rubric-audit/verified-benchmark-rows.json'):sha(PAIR/'rubric-audit/verified-benchmark-rows.json'),str(P/'source-preparation.json'):sha(P/'source-preparation.json')}})
print(json.dumps({'selected':[(x['selection']['candidate_inspection_rank'],x['selection']['group_id'])for x in scopes],'unique_sources':len(files),'prepared_page_count':sum(len(f['prepared_pages'])for f in files.values())},indent=2))
