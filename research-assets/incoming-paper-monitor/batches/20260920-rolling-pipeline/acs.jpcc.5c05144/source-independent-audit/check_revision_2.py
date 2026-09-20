import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).parent;P=O.parent;V=P/'source-extraction-revision-2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def ck(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),**({'detail':detail} if detail is not None else {})})
def diff(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'old':a,'new':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a:out.append({'path':path+'/'+k,'added':b[k]})
   elif k not in b:out.append({'path':path+'/'+k,'removed':a[k]})
   else:out+=diff(a[k],b[k],path+'/'+k)
  return out
 if isinstance(a,list):
  out=[]
  for i in range(max(len(a),len(b))):
   if i>=len(a):out.append({'path':path+'/'+str(i),'added':b[i]})
   elif i>=len(b):out.append({'path':path+'/'+str(i),'removed':a[i]})
   else:out+=diff(a[i],b[i],path+'/'+str(i))
  return out
 return [] if a==b else [{'path':path,'old':a,'new':b}]
def omit_evidence(v):
 if isinstance(v,dict):return {k:omit_evidence(x) for k,x in v.items() if k!='evidence'}
 if isinstance(v,list):return [omit_evidence(x) for x in v]
 return v
prior=read(O/'independent-audit-v1.json');base=read(P/'package-freeze.json');z=read(V/'package-freeze.json');fm=read(V/'effective-file-map.json');replacement=fm['replacements']
ck('base freeze immutable',sha(P/'package-freeze.json')==prior['source_freeze_sha256'])
for n,d in base['bound_files'].items():ck('base file preserved '+n,sha(P/n)==d['sha256'])
for p,h in z['bound_files'].items():ck('new frozen file '+p,sha(p)==(h['sha256'] if isinstance(h,dict) else h))
for n,r in replacement.items():ck('effective file '+n,sha(r['path'])==r['sha256'])
ck('only intended replacement file types',set(replacement)<={'source-facts.json','source-inventory.json','page-coverage.json'})
diffs={}
for name,entry in replacement.items():diffs[name]=diff(read(P/name),read(entry['path']))
old=read(P/'source-facts.json');new=read(replacement['source-facts.json']['path'])
ck('all scientific source leaves identical after removing evidence only',omit_evidence(old)==omit_evidence(new))
for d in diffs['source-facts.json']:
 e=d.get('added',{});ck('fact delta only added exact p5 evidence '+d['path'],'/evidence/' in d['path'] and isinstance(e,dict) and e.get('document_role')=='si' and e.get('pdf_page')==5 and e.get('source_sha256')=='d0e6fc7676c629e3f4a621b53495fb43716985d3018d60e99de192e2788ae38e',d)
f=next(x for x in new['facts'] if x['id']=='sasongko2025-raman-range');q=next(x for x in f['quantities'] if x['meaning']=='displayed temperature interval')
for name,e in [('fact',f),('displayed range',q)]:ck('SAS-SRC-01 resolved '+name,any(x['document_role']=='si' and x['pdf_page']==5 and 'S2' in x['locator'] for x in e['evidence']))
ck('p6 and p4 fact evidence retained',{4,6}<={x['pdf_page'] for x in f['evidence'] if x['document_role']=='si'})
ops=[o for p in new['protocols'] for o in p['operations']]
oq=next(q for o in ops if o['id']=='temperature-raman-acquire' for q in o['quantities'] if q['meaning']=='displayed temperature interval')
ck('displayed operation range exact p5 retained',any(x['document_role']=='si' and x['pdf_page']==5 for x in oq['evidence']))
tables=read(P/'source-tables.json');s1=next(t for t in tables['tables'] if t['id']=='table-s1')['rows']
expected={'s1-7':[.85,.15],'s1-8':[13.3],'s1-9':[15.6],'s1-10':[40],'s1-11':[10]}
for r in s1:
 if r['id'] in expected:ck('independent embedded sample quantities '+r['id'],[q['value'] for q in r['additional_quantities']]==expected[r['id']])
for name,changes in diffs.items():
 if name=='source-facts.json':continue
 for d in changes:
  allowed=(name=='source-inventory.json' and ('/evidence/' in d['path'] or '/source_payload_ids/' in d['path'])) or (name=='page-coverage.json' and '/source_unit_ids/' in d['path'])
  ck('only locator/coverage delta '+name+d['path'],allowed,d)
for p,h in prior['bound_files'].items():ck('prior audit-bound input preserved '+p,sha(p)==h)
result={'author':'/root/peng1998_reader_assets','auditor':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'effective_freeze_sha256':sha(V/'package-freeze.json'),'checks':checks,'exact_deltas':diffs,'summary':{'executed':len(checks),'passed':sum(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']]},'manual_scope':'Targeted exact caption-locator/propagation recheck; prior complete20page/17crop scientific review inherited through unchanged science/crop/source hashes.'}
(O/'bounded-revision-2-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
