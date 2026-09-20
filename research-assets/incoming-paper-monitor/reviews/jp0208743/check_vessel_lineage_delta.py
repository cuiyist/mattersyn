"""Exact bounded delta: a crucible is equipment, not matter inherited by the glass."""
from pathlib import Path
import json,sys,hashlib
B=Path(__file__).resolve().parent;D=B/'canonical-drafts';BASE=B/'vessel-lineage-baseline'
sha=lambda b:hashlib.sha256(b).hexdigest()
if '--baseline'in sys.argv:
 BASE.mkdir(exist_ok=True)
 for p in D.glob('*.json'):
  dest=BASE/p.name
  if dest.exists():assert dest.read_bytes()==p.read_bytes()
  else:dest.write_bytes(p.read_bytes())
 print('Preserved exact 16-record baseline.');raise SystemExit()
def diffs(a,b,path=''):
 if isinstance(a,dict)and isinstance(b,dict):
  assert set(a)==set(b)
  return [x for k in a for x in diffs(a[k],b[k],path+'/'+k)]
 if isinstance(a,list)and isinstance(b,list):
  if len(a)!=len(b):return [{'path':path,'before':a,'after':b}]
  return [x for i,(v,w)in enumerate(zip(a,b))for x in diffs(v,w,path+'/'+str(i))]
 return []if a==b else[{'path':path,'before':a,'after':b}]
changes=[];unchanged={}
expected={'dantas-2002-'+k for k in ['glass-host','sg1','sg2','sg3','sg4','afm1','afm2']}
for p in sorted(D.glob('*.json')):
 old=(BASE/p.name).read_bytes();new=p.read_bytes();a=json.loads(old);b=json.loads(new);delta=diffs(a,b)
 if delta:
  assert p.stem in expected and len(delta)==1
  d=delta[0];assert d=={'path':'/material_states/1/parent_ids','before':['powder-mixture','aluminum-crucible'],'after':['powder-mixture']}
  assert a['operations']==b['operations']and a['measurements']==b['measurements']and a['materials']==b['materials']
  changes.append({'record_id':p.stem,'before_sha256':sha(old),'after_sha256':sha(new),'changes':delta})
 else:unchanged[p.stem]=sha(new)
assert {x['record_id']for x in changes}==expected and len(unchanged)==9
report={'status':'passed','scope':'Equipment remains an operation input but is removed as an ancestor of the glass material state. No source fact, quantity, measurement or operation changed.','changed_records':changes,'unchanged_record_hashes':unchanged,'changed_field_count':7}
(B/'vessel-lineage-delta.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','changed_records':7,'changed_fields':7,'unchanged_records':9}))
