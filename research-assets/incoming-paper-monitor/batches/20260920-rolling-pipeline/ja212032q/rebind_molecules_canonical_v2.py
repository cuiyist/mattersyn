"""Canonical-v2 hash overlay, preserving every frozen molecule asset and mapping."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
G=Path(__file__).resolve().parent;O=G/'visuals/molecules';N=O/'canonical-v2-rebind'
C1=G/'canonical-proposal/v1';C2=G/'canonical-proposal/v2'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not N.exists();N.mkdir()
base=read(O/'package-freeze.json');checks=[]
def ck(ok,msg):
 assert ok,msg
 checks.append(msg)
for p,h in base['bound_files'].items():ck(sha(p)==h,'Original molecular bound file unchanged: '+p)
old=read(C1/'record-manifest.json');new=read(C2/'record-manifest.json')
hashes={sha(C1/n):sha(C2/n)for n in ['package-manifest.json','record-manifest.json']}
paths={str(C1/n):str(C2/n)for n in ['package-manifest.json','record-manifest.json']}
for a,b in zip(old['records'],new['records']):
 ck(a['record_id']==b['record_id'],'Stable record '+a['record_id'])
 ra,rb=read(a['path']),read(b['path'])
 for field in ['materials','stocks','operations','products','measurements','condition_options']:
  ck(ra[field]==rb[field],a['record_id']+' unchanged '+field)
 hashes[a['sha256']]=b['sha256'];paths[a['path']]=b['path']
mapping={**hashes,**paths};deltas=[]
def replace(x,path=''):
 if isinstance(x,dict):return {mapping.get(k,k):replace(v,path+'/'+k)for k,v in x.items()}
 if isinstance(x,list):return [replace(v,path+'/'+str(i))for i,v in enumerate(x)]
 if isinstance(x,str)and x in mapping and mapping[x]!=x:
  deltas.append({'pointer':path,'before':x,'after':mapping[x]});return mapping[x]
 return x
effective={};changed={}
names=['registry-additions.json','bindings-proposal.json','material-slot-map.json','stock-component-map.json','solution-components-proposal.json','reference-qualification.json','public-asset-proposal.json','input-bindings.json']
for n in names:
 before=read(O/n);deltas=[];after=replace(before)
 if before!=after:
  save(N/n,after);changed[n]={'changes':deltas,'before_sha256':sha(O/n),'after_sha256':sha(N/n)};p=N/n
 else:p=O/n
 effective[n]={'path':str(p),'sha256':sha(p)}
ck(read(effective['bindings-proposal.json']['path'])['recordBindings']==read(O/'bindings-proposal.json')['recordBindings'],'All 88 identity assignments unchanged')
ck(effective['registry-additions.json']['path']==str(O/'registry-additions.json'),'Registry bytes unchanged')
ck(effective['solution-components-proposal.json']['path']==str(O/'solution-components-proposal.json'),'Three selectors and eight components unchanged')
ck(effective['stock-component-map.json']['path']==str(O/'stock-component-map.json'),'Unchanged stock records retain byte-identical map')
for slot in read(N/'material-slot-map.json')['slots']:
 r=next(x for x in new['records']if x['record_id']==slot['record_id']);ck(slot['canonical_record_sha256']==r['sha256'],'Current slot hash '+slot['record_id']+'/'+slot['material_id'])
for p,h in read(N/'input-bindings.json').items():ck(sha(p)==h,'Effective input hash '+p)
save(N/'effective-file-map.json',effective)
save(N/'rebind-delta.json',{'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'scope':'Only canonical file paths and hashes are rebound to the five-state classification correction. Original molecule freeze and every asset/identity/amount/stock component/binding approval flag remain unchanged.','base_freeze_sha256':sha(O/'package-freeze.json'),'canonical_v2_sha256':sha(C2/'package-manifest.json'),'changed_files':changed,'check_count':len(checks),'checks':checks,'independent_approval':False})
(N/'README.md').write_text('Overlay only: use effective-file-map.json for the current private molecular proposal. Registry/assets remain in the immutable parent package. Three files carry current canonical-v2 paths/hashes; no chemical identity, assignment, quantity, stock, graph, coordinate or caption is changed. The base v1 freeze is preserved. Independent audit remains a separate gate.\n',encoding='utf-8')
bound=copy.deepcopy(base['bound_files']);bound[str(O/'package-freeze.json')]=sha(O/'package-freeze.json')
bound.update({str(p):sha(p)for p in N.iterdir()if p.is_file()});bound[str(Path(__file__))]=sha(__file__)
bound.update({p:h for p,h in read(N/'input-bindings.json').items()})
manifest={'schema':'mattersyn-private-molecular-rebind/1','author':'/root/backlog_eta','source_id':'ghosh2012','status':'author_rebind_checks_passed_independent_audit_pending','canonical_version':2,'canonical_package_sha256':sha(C2/'package-manifest.json'),'base_freeze_path':str(O/'package-freeze.json'),'base_freeze_sha256':sha(O/'package-freeze.json'),'counts':base['counts'],'effective_files':effective,'author_checks':len(checks),'bound_files':bound,'bound_file_count':len(bound),'independent_approval':False,'site_written':False}
save(N/'package-freeze.json',manifest)
print(json.dumps({'manifest':str(N/'package-freeze.json'),'sha256':sha(N/'package-freeze.json'),'checks':len(checks),'changed_files':list(changed)}))
