"""Independent Norberg reader audit: source/canonical pointer and scope checks.
Only private audit output is written. Author proposals, source and Site are read-only.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,re
B=Path(__file__).resolve().parent;O=B/'public-review-proposal';SID='norberg2004'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(v,p):
 for t in p.strip('/').split('/') if p else []:
  t=t.replace('~1','/').replace('~0','~');v=v[int(t)]if isinstance(v,list)else v[t]
 return v
def display(q):
 if q.get('value') is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
 if lo is not None:return ('> 'if q.get('minimum_exclusive')else '≥ ')+f'{lo:g}'
 if hi is not None:return ('< 'if q.get('maximum_exclusive')else '≤ ')+f'{hi:g}'
 return 'Not reported' if q.get('status')=='not_reported'else q.get('raw_text')or q.get('status','Unspecified')
r=read(O/'norberg2004.json');mc=read(O/'canonical-measurement-coverage.json');sc=read(O/'source-item-coverage.json');pm=read(O/'reader-package-manifest.json');bp=read(O/'reader-bindings-proposal.json')
I=read(B/'source-inventory.json');F=read(B/'source-facts.json');C=read(B/'canonical-source-coverage.json');A=read(B/'canonical-records-audit.json');R={p.stem:read(p)for p in (B/'canonical-drafts').glob('*.json')};AM=read(B/'reader-assets/asset-manifest.json')
items={i['id']:i for s in r['reader_sections']for i in s['items']};checks=[];bound={}
def ck(ok,msg):checks.append({'passed':bool(ok),'check':msg})
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def resolve_ok(rid,p):
 try:ptr(R[rid],p);return True
 except (KeyError,IndexError,ValueError,TypeError):return False
for name,h in pm['files'].items():ck(bind(O/name)==h,'Frozen author file: '+name)
for name,h in pm['frozen_input_hashes'].items():
 p=Path(name);p=p if p.is_absolute()else B/p
 ck(bind(p)==h,'Frozen author input: '+name)
for n in ['canonical-records-audit.json','source-scientific-audit.json','canonical-source-coverage.json','source-inventory.json','source-facts.json','reader-assets/asset-manifest.json']:bind(B/n)
for x in AM['sources']:
 ck(bind(x['path'])==x['sha256'] and bind(x['identical_copy'])==x['sha256'],'Actual main/SI source copies unchanged: '+x['role'])
ck(A['status'].startswith('passed'),'Prior separate canonical audit passed')
for rid in R:ck(bind(B/'canonical-drafts'/f'{rid}.json')==A['record_hashes'][rid]==mc['draft_sha256'][rid],'Exact audited canonical record: '+rid)
ck(len(R)==19 and len(items)==288 and sum(len(s['items'])for s in r['reader_sections'])==288,'Expected unique record and reader-item universe')
ck(r['doi']==I['doi'] and r['title']==I['title'] and r['paper_id']==SID,'Source identity preserved')
ck([s['title']for s in r['reader_sections']]==['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'],'Academic reader sections')
ck({d['role']:d['page_count']for d in r['documents']}=={'main':12,'si':4},'Complete retained main and SI page scope')
ck(not r['training_eligible'] and not r['source_review_promoted'] and not bp['publication_approved'] and not bp['molecular_or_apparatus_bindings_approved'],'No downstream approval inferred')
ck(bp['reader_sha256']==sha(O/'norberg2004.json'),'Binding proposal names exact reader')
units={u['source_unit_id']for u in C['source_units']}
ck(set(sc['unit_to_reader_items'])==units and len(units)==180 and not sc['unmapped_units'],'Full 180-unit canonical coverage universe represented')
for u,keys in sc['unit_to_reader_items'].items():ck(bool(keys)and all(k in items and u in items[k]['source_audit_unit_ids']for k in keys),'Bidirectional source-unit map: '+u)
for key,n in [('source_inventory_sha256','source-inventory.json'),('source_facts_sha256','source-facts.json'),('canonical_coverage_sha256','canonical-source-coverage.json')]:ck(sc[key]==sha(B/n),'Source map hash: '+n)

# Independently enumerate only schema fields displayed by this reader. Stop at a
# complete value/status object so a stored source payload is not counted twice.
Q={};Eop={};Emeas={};Eslots={};Estocks={};Eproducts={}
def collect(rid,p,v):
 if isinstance(v,dict):
  if 'status'in v and 'value'in v:Q[(rid,p)]=v;return
  for k,w in v.items():collect(rid,p+'/'+k.replace('~','~0').replace('/','~1'),w)
 elif isinstance(v,list):
  for n,w in enumerate(v):collect(rid,p+'/'+str(n),w)
for rid,d in R.items():
 for n,o in enumerate(d['operations']):
  p=f'/operations/{n}';Eop[rid+'::'+o['id']]=(rid,p)
  for k in ['parameters','environment','endpoint','condition_options']:collect(rid,p+'/'+k,o.get(k,{}))
 for n,m in enumerate(d['measurements']):
  p=f'/measurements/{n}/value';Q[(rid,p)]=m['value'];Emeas[rid+'::'+m['id']]=(rid,p)
 for n,m in enumerate(d['materials']):
  p=f'/materials/{n}';Eslots[rid+'::'+m['id']]=(rid,p);collect(rid,p+'/quantities',m.get('quantities',{}))
 for n,s in enumerate(d.get('stocks',[])):
  p=f'/stocks/{n}';Estocks[rid+'::'+s['id']]=(rid,p);collect(rid,p,s)
 for n,s in enumerate(d['products']):
  p=f'/products/{n}';Eproducts[rid+'::'+s['sample_id']]=(rid,p)
  for k in ['composition','phase','morphology','surface']:collect(rid,p+'/'+k,s.get(k,{}))
 collect(rid,'/condition_options',d.get('condition_options',[]))
ck((len(Eop),len(Emeas),len(Eslots),len(Estocks),len(Eproducts),len(Q))==(47,590,73,7,105,1218),'Independently enumerated schema field counts')
facts={};seen=[];summaries=[]
for iid,it in items.items():
 ck(bool(it['title'])and bool(it['text'])and bool(it['evidence']),'Nonempty evidenced prose: '+iid)
 ck(it['training_eligible']is False and it['sample_scope']['physical_batch_id']is None,'No training or physical-batch promotion: '+iid)
 for l in it['canonical_links']:ck(resolve_ok(l['record_id'],l['json_pointer']),'Canonical link resolves: '+iid+' / '+l['record_id']+l['json_pointer'])
 for f in it['facts']:
  key=(f['canonical_record_id'],f['json_pointer']);seen.append(key)
  ck(f['id']not in facts,'Unique reader fact: '+f['id']);facts[f['id']]=(iid,f)
  ck(key in Q and f['canonical_quantity']==Q.get(key),'Exact canonical typed payload: '+f['id'])
  q=f['canonical_quantity'];ck(f['status']==q['status']and f['approximate']==bool(q.get('approximate'))and f['unit']==q.get('unit'),'Exact status/unit/approximation: '+f['id'])
  if f['presentation_kind']=='exact_quantity':ck(f['value']==display(q),'Exact display of value or bound: '+f['id'])
  else:
   summaries.append((iid,f));ck(f['presentation_kind']=='academic_inventory_summary' and bool(f['value']),'Explicit source-inventory summary kind: '+f['id'])
  ck(f['training_eligible']is False,'Typed fact not approved for training: '+f['id'])
  for k in ['basis','qualifier','note']:
   if q.get(k):ck(str(q[k])in f['qualifier'] or str(q[k])in str(f['basis']),'Source qualification retained: '+f['id']+' / '+k)
  if f.get('canonical_measurement_id'):
   m=ptr(R[f['canonical_record_id']],f['json_pointer'].removesuffix('/value'))
   ck(m['id']==f['canonical_measurement_id']and m['sample_id']==f['sample_id'],'Exact measurement/sample association: '+f['id'])
  if f.get('sample_id'):ck(f['sample_id']in {s['sample_id']for s in R[f['canonical_record_id']]['products']},'Record-scoped specimen exists: '+f['id'])
 for s in it['sample_scope']['canonical_sample_links']:ck(ptr(R[s['record_id']],s['json_pointer'])['sample_id']==s['sample_id'],'Readable item specimen link: '+iid+' / '+s['sample_id'])
ck(Counter(seen)==Counter(Q.keys()),'Every declared canonical field displayed once, without extra quantities')
ck(len(summaries)==174,'Exactly 174 source-object summaries with unchanged underlying payloads')
for key,expected in [('operation_to_reader_item',Eop),('measurement_to_reader_item',Emeas),('material_to_reader_item',Eslots),('stock_to_reader_item',Estocks),('product_to_reader_item',Eproducts)]:
 ck(set(mc[key])==set(expected),'Exact mapping universe: '+key)
 for k,(rid,p)in expected.items():
  iid=mc[key][k];ck(iid in items and any(x['record_id']==rid and x['json_pointer']==p for x in items[iid]['canonical_links']),'Direct pointer map: '+k)
for x in mc['displayed_field_map']:
 iid,f=facts[x['reader_fact_id']];ck(iid==x['reader_item_id']and f['canonical_record_id']==x['record_id']and f['json_pointer']==x['json_pointer'],'Displayed-field map exact: '+x['reader_fact_id'])
ck(len(mc['displayed_field_map'])==len(Q),'Displayed-field map includes all quantities')
for fid,d in sc['fact_to_reader'].items():
 source=next(x for x in C['facts']if x['source_fact_id']==fid)
 ck(any(x['id']==fid for x in F['facts']),'Source fact exists: '+fid)
 ck(len(d['canonical_bindings'])==len(source['canonical_bindings']),'All source-fact canonical destinations: '+fid)
 for old,x in zip(source['canonical_bindings'],d['canonical_bindings']):
  ck(all(x[k]==v for k,v in old.items()),'Source-fact original pointer preserved: '+fid)
  iid,f=facts[x['reader_fact_id']];ck(iid==x['reader_item_id']and f['canonical_record_id']==x['record_id']and f['json_pointer']==x['pointer']and fid in f['source_fact_ids'],'Source-fact readable pointer exact: '+fid)
ck(set(sc['fact_to_reader'])=={x['id']for x in F['facts']}and len(sc['fact_to_reader'])==201,'All 201 original source facts reachable')
obj_seen=[]
for x in sc['source_objects']:
 iid=x['reader_item_id'];ck(iid in items,'Source object prose item exists: '+x['source_object_id'])
 source=ptr(I,x['source_pointer']);ck(bool(source),'Original inventory pointer resolves: '+x['source_object_id'])
 for z in x['canonical_bindings']:
  obj_seen.append(z);ck(z in C['source_objects'],'Source-object canonical binding preserved: '+x['source_object_id'])
  ck(any(l['record_id']==z['record_id']and l['json_pointer']==z['pointer']for l in items[iid]['canonical_links']),'Readable source-object pointer: '+x['source_object_id'])
ck(Counter(json.dumps(x,sort_keys=True)for x in obj_seen)==Counter(json.dumps(x,sort_keys=True)for x in C['source_objects']),'All original source-object bindings preserved')
for x in sc['lossless_inventory_payload_map']:
 iid,f=facts[x['reader_fact_id']];ck(iid==x['reader_item_id']and f['canonical_record_id']==x['record_id']and f['json_pointer']==x['json_pointer'],'Complete source-payload summary map: '+x['source_object_id'])
 ck(f['canonical_quantity']==ptr(R[x['record_id']],x['json_pointer']),'Exact full source payload remains attached: '+x['source_object_id'])

# Public figures can have multiple semantic aliases for one original image.
pub=[a for g in ['figures','tables','schemes','equations','source_notes']for a in r[g]];unique={a['public_asset']:a for a in pub};byid={a['id']:a for a in pub};source_assets={a['id']:a for a in AM['assets']};boundassets={a['public_asset']:a for a in bp['original_assets']}
ck(len(unique)==40 and len(boundassets)==40,'All forty unique original pages/crops reachable')
for path,a in unique.items():
 z=boundassets[path];ck(bind(z['private_path'])==z['sha256']==a['public_asset_sha256'],'Original asset bound bytes: '+path)
 ck(a['asset_provenance']['source_sha256']in {x['sha256']for x in AM['sources']},'Original source hash retained: '+path)
 ck(not a['reviewed']and not a['reader_render_verified']and not a['training_eligible'],'Presentation status remains pending: '+path)
 ck(path.startswith('assets/figures/norberg2004/')and '..'not in path,'Safe proposed public path: '+path)
 ck(any(path==z['public_asset']for i in items.values()for z in i['original_assets']),'Reader asset link is reachable: '+path)
for a in pub:
 for s in a.get('canonical_sample_links',[]):ck(resolve_ok(s['record_id'],s['json_pointer'])and ptr(R[s['record_id']],s['json_pointer'])['sample_id']==s['sample_id'],'Original asset sample pointer: '+a['id']+' / '+s['record_id']+' / '+s['sample_id'])
 for iid in a.get('source_unit_ids',[]):ck(iid in units,'Original asset source-unit mapping: '+a['id']+' / '+iid)
for fig in I['figures_tables_schemes']:
 aid=SID+'-'+fig['id'];a=byid[aid]
 source_samples=set(fig.get('sample_ids',[]));actual={s['sample_id']for s in a['canonical_sample_links']}
 ck(actual<=source_samples,'Original figure has no invented sample label: '+aid)
for item in items.values():
 for a in item['original_assets']:ck(a['id']in byid and a['public_asset_sha256']==byid[a['id']]['public_asset_sha256'],'Item asset ID/hash agreement: '+item['id']+' / '+a['id'])
for formula,rids in r['material_evidence_records'].items():ck(set(rids)<=set(R),'Material evidence record scope resolves: '+formula)
for formula,aids in r['material_original_asset_ids'].items():ck(set(aids)<=set(byid),'Material original-gallery scope resolves: '+formula)
for rid,rids in r['route_evidence_contexts'].items():ck(rid in R and set(rids)<=set(R),'Route evidence scope resolves: '+rid)
ck(len(r['referenced_methods'])==68,'All main and SI reference groups included')
ck(Counter(x['record_type']for x in r['recipe_inventory'])==Counter(x['record_type']for x in R.values()),'Preparation/observation counts remain canonical')
domains=[f for _,f in facts.values()if f['canonical_quantity'].get('minimum')==800]
ck(len(domains)==1 and domains[0]['value']=='> 800'and domains[0]['sample_id']=='films-a-b-c-collective'and domains[0]['status']=='author_derived','Collective effective domain spin remains a strict model-derived bound')
ck('D > E > F'in items['gap-g-si-curve-table']['text']and 'D = 0.038'in items['gap-g-si-curve-table']['text']and 'F = 0.076'in items['gap-g-si-curve-table']['text'],'D/F curve-versus-table discrepancy preserved')
ck('not silently repair'in items['gap-g-poisson']['text'],'Printed statistical notation remains unresolved')
ck('No experimental CIF'in items['gap-g-structure']['text']and 'SAED'in items['gap-g-structure']['text'],'No invented coordinate or SAED availability')
ck('Carrier polarity, density, nitrogen incorporation'in items['intuition-carrier-hypothesis']['text'],'Carrier/nitrogen mechanism remains an unverified hypothesis')
ck('does not receive'in items['u-protocol-surface-control']['text'],'Surface control not assigned stripping treatment')
ck('reference 32'in items['u-protocol-topo']['text']and 'not restated'in items['u-protocol-topo']['text'],'TOPO method incompleteness remains explicit')
ck(not re.search(r'(?<![A-Za-z])[A-Za-z]:[\\/]|file://',json.dumps(r,ensure_ascii=False)),'Public reader avoids private local paths')
failures=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-independent-reader-link-checks/1','source_id':SID,'auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed'if not failures else 'findings','reader_sha256':sha(O/'norberg2004.json'),'counts':r['counts'],'check_count':len(checks),'failure_count':len(failures),'failures':failures,'checks':checks,'bound_files':bound,'scope':'Independent actual-reader/source/canonical pointer, payload, status, bound, original-byte and specimen-map checks. Scientific prose and figure inspection are recorded separately in reader-source-audit. No Site or browser execution.'}
(B/'reader-link-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'failure_count':len(failures),'first_failures':failures[:15]},ensure_ascii=False));raise SystemExit(bool(failures))
