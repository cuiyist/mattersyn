from pathlib import Path
from collections import Counter
import json,hashlib,math
B=Path(__file__).resolve().parent;V=B/'visuals';SITE=Path('[local path redacted]');OLD=SITE/'dist/assets/chemical-registry';load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
R={p.stem:load(p)for p in(B/'canonical-drafts').glob('*.json')};rh={p.stem:sha(p)for p in(B/'canonical-drafts').glob('*.json')};b=load(V/'bindings-additions.json');pr=load(V/'product-reference-proposal.json');reuse=load(V/'reused-reference-audit-input.json')['entries'];new={x['id']:x for x in load(V/'registry-additions.json')['entries']};old={k:v['entry']for k,v in reuse.items()};entries=new|old
ck('Binding final record hashes',b['sourceRecordSha256']==rh);ck('Canonical independently audited hashes',load(B/'canonical-records-audit.json')['record_hashes']==rh)
mapping={'lead-chxbu':'identity-sashchiuk-lead-chxbu','selenium':'selenium-element','tbp':'tbp','topo-reagent':'identity-sashchiuk-topo-reagent','topo-component':'topo','argon':'argon','methanol':'methanol','butanol':'identity-butanol-unspecified-isomer','pbse-individual':'identity-sashchiuk-pbse-individual','pbse-spheres':'identity-sashchiuk-pbse-spheres','pbse-wires':'identity-sashchiuk-pbse-wires','formvar-grid':'identity-sashchiuk-formvar-grid','silicon-substrate':'identity-sashchiuk-silicon-substrate','silica-layer':'identity-sashchiuk-silica-layer','trimethylsilane':'trimethylsilane','pmma':'identity-sashchiuk-pmma','titanium':'identity-sashchiuk-titanium','gold':'identity-sashchiuk-gold'}
count=0
for rid,r in R.items():
 ck(rid+'/all slots',set(b['recordBindings'][rid])=={x['id']for x in r['materials']})
 for m in r['materials']:
  aid=b['recordBindings'][rid][m['id']];ck(rid+'/'+m['id']+'/source identity',aid==mapping[m['id']]);ck(rid+'/'+m['id']+'/formula',m['formula']==entries[aid]['formula']);count+=1
ck('42 exact material bindings',count==42);ck('15 record mappings',len(b['recordBindings'])==15)
for k,f in [('methanol','CH4O'),('identity-butanol-unspecified-isomer','C4H10O'),('selenium-element','Se'),('tbp','C12H27P'),('topo','C24H51OP'),('argon','Ar')]:ck(k+'/formula',old[k]['formula']==f)
for i,r in reuse.items():
 e=r['entry'];ck(i+'/source-neutral display',not any(t in (e.get('caption','')+' '.join(e.get('limitations',[]))).lower()for t in ['veinot','qdoh','gamelin']))
 for path,h in r['assetHashes'].items():ck(i+'/asset/'+path,sha(OLD/path)==h)
 for typ in ['model2dPath','model3dPath']:
  path=e.get(typ)
  if not path:continue
  m=load(OLD/path);a=m['atoms'];bs=m.get('bonds',[]);ck(i+'/'+typ+'/coordinates',all(all(math.isfinite(x.get(k,0))for k in ['x','y','z'])for x in a));ck(i+'/'+typ+'/valid indices',all(0<=x['a']<len(a)and 0<=x['b']<len(a)for x in bs))
  heavy=Counter(x['element']for x in a if x['element']!='H');expected={'methanol':{'C':1,'O':1},'tbp':{'C':12,'P':1},'topo':{'C':24,'P':1,'O':1}}.get(i)
  if expected:ck(i+'/'+typ+'/heavy composition',heavy==expected)
  if i in ['tbp','topo']:
   pi=next(j for j,x in enumerate(a)if x['element']=='P');neighbors=[];graph={j:set()for j,x in enumerate(a)if x['element']=='C'}
   for bb in bs:
    x,y=bb['a'],bb['b']
    if x==pi:neighbors.append(y)
    if y==pi:neighbors.append(x)
    if x in graph and y in graph:graph[x].add(y);graph[y].add(x)
   starts=[j for j in neighbors if a[j]['element']=='C'];ck(i+'/'+typ+'/three alkyl arms',len(starts)==3)
   for start in starts:
    todo=[start];seen=set()
    while todo:
     z=todo.pop()
     if z in seen:continue
     seen.add(z);todo.extend(graph[z]-seen)
    ck(i+'/'+typ+'/linear arm '+str(start),len(seen)==(4 if i=='tbp' else 8)and all(len(graph[z])<=2 for z in seen))
  if i=='methanol':ck('Methanol C–O bond/'+typ,any({a[x['a']]['element'],a[x['b']]['element']}=={'C','O'}and x['order']==1 for x in bs))
ck('Butanol no guessed isomer',old['identity-butanol-unspecified-isomer']['model2dPath']is None and old['identity-butanol-unspecified-isomer']['model3dPath']is None)
ck('Se no allotrope geometry',old['selenium-element'].get('model3dPath')is None)
expected={}
for x in ['individual-low','individual-structure']:expected['sashchiuk-2004-'+x]='identity-sashchiuk-pbse-individual'
for x in ['sphere-intermediate','sphere-structure','absorption']:expected['sashchiuk-2004-'+x]='identity-sashchiuk-pbse-spheres'
for x in ['wire-high','wire-intermediate','wire-structure','device-fabrication','electrical']:expected['sashchiuk-2004-'+x]='identity-sashchiuk-pbse-wires'
ck('Ten specific product references; no generic/context mixture',pr['recordBindings']==expected)
cr=load(B/'crystal-source-audit.json');ck('Crystal independent exact current proposal',cr['status'].startswith('passed')and cr['crystal_reference_sha256']==sha(V/'crystal-reference-proposal.json'))
mo=load(B/'molecular-source-audit.json');ck('Molecular independent exact current registry',mo['status'].startswith('passed')and mo['registry_sha256']==sha(V/'registry-additions.json'))
failed=[c for c in C if not c['passed']];report={'status':'failed'if failed else'passed_independent_bindings_and_reuse_source_audit','source_id':'sashchiuk2004','bindings_sha256':sha(V/'bindings-additions.json'),'product_reference_sha256':sha(V/'product-reference-proposal.json'),'crystal_reference_sha256':sha(V/'crystal-reference-proposal.json'),'registry_sha256':sha(V/'registry-additions.json'),'reused_reference_input_sha256':sha(V/'reused-reference-audit-input.json'),'record_hashes':rh,'check_count':len(C),'checks':C,'failed_checks':failed,'material_slot_count':count,'product_reference_count':len(expected),'reused_reference_count':6,'scope':'All42materialslots/15records independently checked against source-named ingredients and finalcanonicalhashes. Six reusedreference identities/assets/graphs reviewed read-only; no old source-specific treatment conditions imported. Ten illustrativeproductreferences match population scopes. IdealPbSeCIF/block binds separate independent referenceaudit; no measuredatomic labels implied.','site_mutated':False}
(B/'bindings-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(B/'bindings-source-audit.md').write_text('# Independent bindings audit\n\n'+('Passed'if not failed else'Failed')+' '+str(len(C))+' checks: 42 material bindings across15records, six reused references and ten product-reference mappings. Butanol keeps unspecified-isomer identity; selenium has no invented allotrope; pure TOPO is a named component of the source reagent. TBP has three linear butyl arms, TOPO three octyl arms. Device materials remain supports/contact ingredients.\n\nExact canonical, registry, binding, product and ideal-crystal hashes are bound in JSON. No Site edits.\n',encoding='utf8');print(json.dumps({'status':report['status'],'checks':len(C),'failed':failed}))
if failed:raise SystemExit(1)
