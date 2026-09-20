"""Document bounded source-audit corrections against preserved canonical bytes."""
from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def diff(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':path+'/'+k,'before':a.get(k),'after':b.get(k)})
   else:out+=diff(a[k],b[k],path+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':path,'before':a,'after':b}]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in diff(x,y,path+'/'+str(i))]
 return [] if a==b else [{'path':path,'before':a,'after':b}]
rows=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 q=B/'canonical-delta-baseline'/p.name
 changes=diff(json.loads(q.read_text(encoding='utf8')),json.loads(p.read_text(encoding='utf8')))
 if changes:rows.append({'file':p.name,'before_sha256':sha(q),'after_sha256':sha(p),'changes':changes})
data={'status':'bounded_source_audit_correction','source_id':'schwartz2003','record_count':30,'operation_count':95,'measurement_count':277,'changed_records':rows,'change_scope':['Mutually exclusive precipitation/redispersion alternatives; particle-state ancestry excludes unresolved solvent choice.','Separate pure, Co and Ni comparison stocks; preparation retains sample_set kind.','Undoped ZnO TOPO cleaning measurement explicitly relates only to doped examples.']}
(B/'canonical-bounded-delta.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'changed_records':len(rows),'changed_paths':sum(len(r['changes'])for r in rows)}))
