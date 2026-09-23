"""Bind authored source-triage notes to exact inspected artifacts; no promotion."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
O=Path(__file__).resolve().parent;P=O/'private'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf8'))
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert not(O/'author-freeze.json').exists(),'Freeze already exists; revise through a separate correction.'
s=read(O/'selection.json'); d=read(P/'sources.json'); notes=read(O/'notes.json'); renders=read(P/'render-manifest.json')
assert len(notes)==10 and {n['case'] for n in notes}==set(range(1,11))
at=datetime.now(timezone.utc); elapsed=(at-datetime.fromisoformat(s['started_at'])).total_seconds()
readset=set();viewset={(r['source_sha256'],r['pdf_page']) for r in renders};receipts=[]
for c,n in zip(d['inputs'],notes):
    assert c['case']==n['case']
    sourcehashes={f['sha256'] for f in c['files']}
    for f in c['files']: assert sha(f['path'])==f['sha256']
    readloc=[]
    for pre,pages in n['read_pages'].items():
        h=next(h for h in sourcehashes if h.startswith(pre))
        for pn in pages:
            f=next(x for x in d['files'][h]['pages'] if x['pdf_page']==pn)
            assert sha(f['text_path'])==f['text_sha256']
            readloc.append({'source_sha256':h,'pdf_page':pn,'text_sha256':f['text_sha256'],'read_as':'full_page_text_for_targeted_screen_not_full_paper_curation'})
            readset.add((h,pn))
    xml=[]
    for pre in n.get('read_ooxml',[]):
        h=next(h for h in sourcehashes if h.startswith(pre));f=d['files'][h]['ooxml_text'];assert sha(f['text_path'])==f['text_sha256']
        xml.append({'source_sha256':h,**f,'coverage':'document.xml text inspected; embedded figures/layout not visually audited'})
    receipts.append({**c,**n,'source_hashes':sorted(sourcehashes),'full_pdf_text_pages_read':readloc,'ooxml_text_read':xml,'original_pdf_pages_visually_inspected':[{'source_sha256':h,'pdf_page':pn}for h,pn in sorted(viewset)if h in sourcehashes],'identity_headers':'See per-scope pairing note; header excerpts not counted as full-page reading','independent_audit':'pending','full_extraction_complete':False,'training_admission':False})
for r in renders:assert sha(r['image_path'])==r['sha256']
summary={'started_at':s['started_at'],'ended_at':at.isoformat(),'author':'/root','status':'author_source_triage_complete_independent_check_pending','selected_scopes':10,'newly_triaged_scopes':10,'reused_existing_terminal_scope':0,'new_underlying_studies':10,'outcomes':dict(Counter(n['outcome']for n in notes)),'preparation_seconds':d['preparation_seconds'],'elapsed_seconds_including_coordination_and_receipt_writing':elapsed,'elapsed_minutes_per_new_scope':elapsed/60/10,'timing_limits':['One purposive ten-position R/U sample; not corpus-representative and not a capacity forecast.','Elapsed includes coordination and author note writing; not measured GPU/model active time.','Independent checking and all detailed extraction/integration remain outside this author timing.'],'coverage':{'freshly_hashed_document_copies':sum(len(c['files'])for c in d['inputs']),'distinct_source_hashes':len(d['files']),'full_pdf_text_pages_read':len(readset),'original_pdf_pages_viewed':len(viewset),'ooxml_documents_text_read':0,'full_papers_completed':0},'new_scientific_records':0,'new_approved_structure_recipe_pairs':0,'source_closures':0,'notes':['Seven target-preparation/surface-modification positives; two theory-oriented deferrals and one wrong-main source-role hold.','No source exclusions or full curation approvals issued.','The ZnSe source-role hold preserves SI process information; main-labelled file is a Peer Review File.','No local atomic-coordinate dataset was established; this does not prove absence in all uninspected sources.'],'receipts':receipts}
save(O/'batch-summary.json',summary)
freeze={'frozen_at':at.isoformat(),'status':summary['status'],'bound_files':[{'path':str(f.relative_to(O)),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(O.rglob('*'))if f.is_file() and f.name!='author-freeze.json'],'source_files':[{'path':f['path'],'sha256':f['sha256']}for c in d['inputs']for f in c['files']],'no_publication_or_training_approval':True}
save(O/'author-freeze.json',freeze)
print(json.dumps({k:v for k,v in summary.items()if k!='receipts'},indent=2))
