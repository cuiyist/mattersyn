"""Narrow independent validation of the canonical-v2 molecular overlay."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
A=Path(__file__).resolve().parent;G=A.parent.parent;M=G/'visuals/molecules';R=M/'canonical-v2-rebind'
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def ck(k,v):checks.append({'check':k,'passed':bool(v)})
def ptr(x,p):
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):
  if set(a)!=set(b):return [(p,a,b)]
  return [x for k in a for x in diff(a[k],b[k],p+'/'+k.replace('~','~0').replace('/','~1'))]
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return [x for i,(v,w) in enumerate(zip(a,b)) for x in diff(v,w,p+'/'+str(i))]
 return [] if a==b else [(p,a,b)]
fr=read(R/'package-freeze.json');fm=read(R/'effective-file-map.json');delta=read(R/'rebind-delta.json')
ck('exact overlay freeze',sha(R/'package-freeze.json')=='fca7a26e33f67fd4f4f0a6899eb5c89776439909bfaf6b54866ebec7e550cf73')
ck('exact effective map',fr['effective_files']==fm)
for fn,d in fr['bound_files'].items():
 p=Path(fn);ck('overlay bound '+fn,p.is_file() and sha(p)==d)
 if p.is_file():bound[str(p)]=sha(p)
effective={}
for name,row in fm.items():
 ck('effective hash '+name,sha(row['path'])==row['sha256']);effective[name]=read(row['path'])
ck('only three replaced files',{n for n,x in fm.items() if Path(x['path']).parent==R}=={'bindings-proposal.json','material-slot-map.json','input-bindings.json'})
for name in ['bindings-proposal.json','material-slot-map.json']:
 changes=diff(read(M/name),effective[name]);ck('twenty hash leaves '+name,len(changes)==20 and all(p.endswith('/canonical_record_sha256') for p,a,b in changes))
 ck('exact declared changes '+name,changes==[(x['pointer'],x['before'],x['after']) for x in delta['changed_files'][name]['changes']])
oldinputs=read(M/'input-bindings.json');newinputs=effective['input-bindings.json']
for p,d in newinputs.items():ck('effective input hash '+p,Path(p).is_file() and sha(p)==d)
normalized={p.replace('canonical-proposal\\v2\\','canonical-proposal\\v1\\'):v for p,v in newinputs.items()}
ck('input key mapping only v1 to v2',set(normalized)==set(oldinputs))
ck('six input hash changes',sum(normalized[p]!=v for p,v in oldinputs.items())==6)
records={};hashes={};canonical_changes=[]
rm=read(G/'canonical-proposal/v2/record-manifest.json')
for row in rm['records']:
 rid=row['record_id'];records[rid]=read(row['path']);hashes[rid]=sha(row['path'])
 ck('effective record hash '+rid,hashes[rid]==row['sha256'])
 old=read(G/'canonical-proposal/v1'/f'{rid}.json')
 for p,a,b in diff(old,records[rid]):canonical_changes.append({'record_id':rid,'pointer':p,'before':a,'after':b})
declared_canonical=read(G/'canonical-proposal/v2/revision-2-delta.json')
declared_changes=[dict(record_id=r['record_id'],**x) for r in declared_canonical['canonical_changes'] for x in r['changes']]
ck('only five kind changes and precise FTIR specimen label',canonical_changes==declared_changes and len(canonical_changes)==6 and sum(x['pointer'].endswith('/kind') and x['after']=='sample_set' for x in canonical_changes)==5 and [x for x in canonical_changes if x['pointer'].endswith('/name')]==[{'record_id':'ghosh-2012-ftir-procedure','pointer':'/material_states/0/name','before':'ftir film','after':'Separate particle and pure-ligand FTIR specimens'}])
ck('effective canonical package',sha(G/'canonical-proposal/v2/package-manifest.json')==fr['canonical_package_sha256']=='7b71cd4d861328b057adefab344b0bb1029152cf981e569ccfacf06f1672316d')
slots=effective['material-slot-map.json']['slots'];bindings=effective['bindings-proposal.json']
for x in slots:
 rid=x['record_id'];label=rid+'/'+x['material_id']
 ck('v2 exact material '+label,ptr(records[rid],x['json_pointer'])==x['canonical_identity'])
 ck('v2 hash '+label,hashes[rid]==x['canonical_record_sha256'])
 ck('v2 mirrored binding '+label,bindings['bindingNotes'][rid][x['material_id']]==x)
def walk(x):
 if isinstance(x,dict):
  if {'record_id','json_pointer','quantity'}<=x.keys():ck('v2 exact field '+x['record_id']+x['json_pointer'],ptr(records[x['record_id']],x['json_pointer'])==x['quantity'])
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(slots);walk(effective['stock-component-map.json'])
for x in effective['stock-component-map.json']['stocks']:
 ck('stock v2 hash '+x['stock_id'],hashes[x['record_id']]==x['canonical_record_sha256'])
 for c in x['components']:ck('stock v2 component '+x['stock_id']+c['material_id'],ptr(records[x['record_id']],c['json_pointer'])['quantities']==c['source_quantities'])
out={'schema':'mattersyn.independent_molecular_rebind_checks/1','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'checks':checks,'failures':[x for x in checks if not x['passed']],'canonical_delta':canonical_changes,'bound_files':bound,'effective_files':fm}
(A/'rebind-v2-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failures':out['failures']}))
