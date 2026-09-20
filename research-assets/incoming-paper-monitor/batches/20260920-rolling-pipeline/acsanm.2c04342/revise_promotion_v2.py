"""Preserve v1 and normalize only the reader's downstream scope enum."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
A=Path(__file__).resolve().parent;V=A/'site-integration-proposal/v1';W=V.parent/'v2'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not W.exists();freeze=read(V/'package-freeze.json')
for f in freeze['files']:assert sha(V/f['path'])==f['sha256']
shutil.copytree(V,W)
p=W/'reader/matuhina2023.json';before=read(p);after=copy.deepcopy(before)
assert before['review_scope']=='complete_supplied_main_and_matched_si'
after['review_scope']='supplied_main_and_matched_si';save(p,after)
assert {k:v for k,v in before.items() if k!='review_scope'}=={k:v for k,v in after.items() if k!='review_scope'}
files=[{'path':p.relative_to(W).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(W.rglob('*')) if p.is_file() and p.name!='package-freeze.json']
freeze.update(at=datetime.now(timezone.utc).isoformat(),files=files,revision=2,prior_freeze_sha256=sha(V/'package-freeze.json'),author_script_sha256=sha(Path(__file__)))
save(W/'package-freeze.json',freeze)
save(W.parent/'promotion-v2-delta.json',{'prior_freeze_sha256':sha(V/'package-freeze.json'),'revised_freeze_sha256':sha(W/'package-freeze.json'),'exact_scientific_payload_unchanged':True,'reader_changes':[{'pointer':'/review_scope','before':before['review_scope'],'after':after['review_scope']}],'changed_relative_files':['reader/matuhina2023.json','package-freeze.json']})
for name in ['import_reviewed_matuhina.py','prepare_delivery_helpers.py']:
 p=A/name;t=p.read_text('utf8');t=t.replace("P=O/'v1'","P=O/'v2'").replace('site-integration-proposal/v1/promotion-manifest.json','site-integration-proposal/v2/promotion-manifest.json');p.write_text(t,'utf8')
print(json.dumps({'revision':2,'freeze_sha256':sha(W/'package-freeze.json'),'reader_sha256':sha(W/'reader/matuhina2023.json')}))
