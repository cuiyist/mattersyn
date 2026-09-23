import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
O=Path(__file__).resolve().parent;P=O/'private'
D=json.loads((P/'source-preparation.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rank=int(sys.argv[1]);notes=json.loads((O/f'notes-rank{rank:03d}.json').read_text(encoding='utf-8'))
s=next(s for s in D['scope_inputs']if s['selection']['candidate_inspection_rank']==rank)
bound={str(O/'selection-manifest.json'):sha(O/'selection-manifest.json')};originals=[]
for f in s['files']:
    assert sha(f['path'])==f['sha256'];bound[f['path']]=f['sha256']
    originals.append({**f,'page_count':D['source_files'][f['sha256']]['pdf_page_count'],'current_bytes_reverified_at':datetime.now(timezone.utc).isoformat()})
for item in notes['coverage']:
    h=next(h for h in D['source_files']if h.startswith(item['source_sha256_prefix']))
    item['source_sha256']=h
    for pno in set(item.get('pages_read',[])+item.get('pages_visually_inspected',[])):
        for ext in ['txt','png']:
            f=P/f'{h[:12]}-p{pno:03d}.{ext}'
            if f.exists():bound[str(f)]=sha(f)
    txt=P/f'{h[:12]}-all-source-text.txt'
    if txt.exists():bound[str(txt)]=sha(txt)
if notes.get('additional_nonpage_inspection',{}).get('path'):
    extra=O/notes['additional_nonpage_inspection']['path'];bound[str(extra)]=sha(extra)
out={'schema':'mattersyn-bounded-atomic-shortlist-screen/1','status':'author_screen_complete_independent_audit_pending','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'candidate_rank':rank,'group_id':s['selection']['group_id'],'automated_nomination':s['selection'],'original_files':originals,**notes,'full_paper_review_completed':False,'independent_audit_passed':False,'scientific_pair_approved':False,'training_task_admitted':False,'queue_completed':False,'bound_files':bound}
p=O/f'scope-rank{rank:03d}.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rank':rank,'path':str(p),'sha256':sha(p)},indent=2))
