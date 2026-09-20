from pathlib import Path
import json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).resolve().parent;B=A.parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def delta(a,b,path=''):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append((path+'/'+k,a.get(k),b.get(k)))
   else:out+=delta(a[k],b[k],path+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [(path,a,b)]
  return [x for i,(v,w) in enumerate(zip(a,b)) for x in delta(v,w,path+'/'+str(i))]
 return [] if a==b else [(path,a,b)]
checks=[]
def ck(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
old=B/'canonical-proposal/v1';new=B/'canonical-proposal/v2'
manifest=load(new/'package-manifest.json')
for name,h in manifest['bound_files'].items():
 p=Path(name);ck('v2 frozen dependency '+name,p.exists() and sha(p)==h)
record_deltas={}
for p in sorted(old.glob('morrison-*.json')):
 q=new/p.name;d=delta(load(p),load(q));record_deltas[p.stem]=d
 if p.stem!='morrison-2017-single-crystal-acquisition':ck('unchanged canonical bytes '+p.name,sha(p)==sha(q))
 else:
  ck('analytical-result kind',load(q)['material_states'][0]['kind']=='analysis_data')
  ck('only result-kind or name changes',all(x[0] in ['/material_states/0/kind','/material_states/0/name'] for x in d),d)
  ck('no product coordinate assets',load(q)['structure_assets']==[])
  ck('no task admission',load(q)['quality']['requested_tasks']==[])
oldreader=B/'public-review-proposal/v1/morrison2017.json';newreader=B/'public-review-proposal/v2/morrison2017.json'
rd=delta(load(oldreader),load(newreader));ck('reader payload unchanged',not rd,rd)
ck('source freeze unchanged',sha(B/'package-freeze.json')=='3b261b2f0aec35ab5fd9452fa8a9fee87ece32d87ef9ef2b29e617d70a74ccc8')
v1audit=load(A/'independent-audit-v1.json')
for p,h in v1audit['bound_files'].items():
 if str(old) in p or str(B/'public-review-proposal/v1') in p or p.endswith('source-facts.json') or '/reader-assets/' in p.replace('\\','/'):
  ck('v1/source frozen history '+p,sha(Path(p))==h)
report={'schema':'mattersyn.independent-canonical-reader-delta.v1','auditor':'/root/peng1998_reader_assets','status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'checks':checks,'record_deltas':record_deltas,'reader_deltas':rd,'v2_package_sha256':sha(new/'package-manifest.json'),'scope':'Bounded independent recheck of MCR1 classification fix against the preserved v1 scientific audit.'}
(A/'delta-check-v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':[x for x in checks if not x['passed']],'record_deltas':{k:v for k,v in record_deltas.items() if v}},ensure_ascii=False,indent=2))
