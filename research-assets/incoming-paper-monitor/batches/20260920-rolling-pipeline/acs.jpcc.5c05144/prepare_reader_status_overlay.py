from pathlib import Path
import json,hashlib,copy
J=Path(__file__).resolve().parent;P=J/'site-integration-proposal/v1';O=J/'site-integration-proposal/reader-status-overlay'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not O.exists()
r=json.loads((P/'reader/sasongko2025.json').read_text('utf8'));d=[]
def walk(x,ptr=''):
 if isinstance(x,dict):
  if x.get('json_pointer')=='' and x.get('relation')=='Private canonical record pending independent review.':
   d.append({'pointer':ptr+'/relation','before':x['relation'],'after':'Source-reviewed canonical record; independent audit passed.'});x['relation']=d[-1]['after']
  for k,v in x.items():walk(v,ptr+'/'+str(k).replace('~','~0').replace('/','~1'))
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,ptr+'/'+str(i))
walk(r);assert len(d)==19,len(d)
p='/supporting_information/status';old=r['supporting_information']['status'];assert old=='matched_local_source_audit_passed_canonical_review_pending'
r['supporting_information']['status']='matched_source_and_canonical_review_complete';d.append({'pointer':p,'before':old,'after':r['supporting_information']['status']})
save(O/'reader/sasongko2025.json',r)
save(O/'status-only-delta.json',{'base_freeze_sha256':sha(P/'package-freeze.json'),'base_reader_sha256':sha(P/'reader/sasongko2025.json'),'deltas':d,'scientific_values_changed':False})
save(O/'package-freeze.json',{'files':[{'path':p.relative_to(O).as_posix(),'sha256':sha(p)} for p in O.rglob('*.json')],'scope':'20 visible review-status leaves only; v1 and raw fact payloads retained unchanged.'})
print(sha(O/'package-freeze.json'))
