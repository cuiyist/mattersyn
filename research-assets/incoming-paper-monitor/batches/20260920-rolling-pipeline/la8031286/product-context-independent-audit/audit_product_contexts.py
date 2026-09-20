"""Distinct root review of the immutable Pati symbolic product proposal."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
A=Path(__file__).resolve().parent;N=A.parent;P=N/'visuals/product-context';C=N/'canonical-proposal/v1';V=N/'canonical-proposal/v2'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def ptr(o,s):
 for k in s.strip('/').split('/'):o=o[int(k)] if isinstance(o,list) else o[k.replace('~1','/').replace('~0','~')]
 return o
checks=[]
def ck(n,v):
 checks.append({'check':n,'passed':bool(v)})
 assert v,n
freeze=read(P/'package-freeze.json')
ck('Distinct proposal author',freeze['author']=='/root/backlog_eta')
for p,h in freeze['bound_files'].items():ck('Immutable '+p,sha(Path(p))==h)
ck('Source independent audit passed',read(N/'source-independent-audit/independent-audit-v1.json')['status']=='passed')
ck('Canonical v2 independent audit passed',read(N/'canonical-reader-independent-audit/independent-audit-v2.json')['status']=='passed')
records={p.stem:read(p) for p in C.glob('pati-*.json')}
ck('19 records',len(records)==19)
for rid in records:ck(rid+' preserved in v2',sha(C/(rid+'.json'))==sha(V/(rid+'.json')))
sf=read(N/'source-facts.json');ctx=read(P/'product-contexts-additions.json');pub=read(P/'public-product-contexts-proposal.json');b=read(P/'bindings.json');reg=read(P/'registry-additions.json')
entries={x['id']:x for x in reg['entries']};pairs={}
allowed={'sample_id','label','registry_id','caption','phase','morphology','conflict_ids','reported_parent_context','same_physical_batch_asserted','projection_kind','training_eligible','atomic_model','binding_approved'}
for rid,rows in ctx['recordContexts'].items():
 ck(rid+' source identity',records[rid]['lineage']['source_group']=='pati2009')
 for i,row in enumerate(rows):
  key=(rid,row['sample_id']);label='/'.join(key);ck(label+' unique',key not in pairs);pairs[key]=row
  p=ptr(records[rid],row['canonical_product_pointer'])
  ck(label+' exact canonical product',p==row['canonical_product_snapshot'] and p['sample_id']==row['sample_id'])
  ck(label+' explicitly symbolic',row['projection_kind']=='source_scoped_symbolic_context' and row['training_eligible'] is False and row['atomic_model'] is False and row['same_physical_batch_asserted'] is False)
  ck(label+' visible scope','illustration is symbolic' in row['caption'] and 'no atomic coordinates' in row['caption'])
  ck(label+' registered reference',row['registry_id'] in entries)
  ids=[]
  for link in row['source_fact_links']:
   ck(label+' source file',Path(link['path']).resolve()==(N/'source-facts.json').resolve())
   fact=ptr(sf,link['json_pointer']);ids.append(fact['id']);ck(label+' exact source fact',digest(fact)==link['sha256'])
  ck(label+' fact identities',ids==row['source_fact_ids'] and bool(ids))
  for link in row['canonical_claim_links']+row['canonical_measurement_links']:
   claim=ptr(records[link['record_id']],link['json_pointer'])
   ck(label+' unchanged claim record',sha(C/(link['record_id']+'.json'))==link['record_sha256'])
   ck(label+' exact claim or quantity',claim==link['canonical_measurement'] and claim['id']==link['measurement_id'])
  ck(label+' claim support',bool(row['canonical_claim_links']))
  ck(label+' public projection exact',pub['recordContexts'][rid][i]=={k:v for k,v in row.items() if k in allowed})
  ck(label+' no private paths in public projection','C:\\' not in json.dumps(pub['recordContexts'][rid][i],ensure_ascii=False))
  sid=row['sample_id'];text=row['caption']
  if rid.endswith('-route'):
   ck(label+' unresolved whole powder',p['composition']['value'] is None and row['phase']['value'] is None and 'does not establish bulk purity' in text)
  if row['registry_id']=='pati2009-local-ceo2-product-symbol':
   ck(label+' local microscopy qualification','local CeO2 interpretation' in text and '0.267' in text and '0.271' in text and 'pure CeO2 powder label' in text)
  if 'solution-dls' in sid:
   ck(label+' DLS conflict preserved','hydrodynamic radius' in text and 'diameter' in text and 'no factor-of-two correction' in text and row['phase']['value'] is None)
  if 'xps-' in row['registry_id']:
   ck(label+' no XPS composition or phase',entries[row['registry_id']]['formula']=='' and row['phase']['value'] is None)
   if row['registry_id'].endswith('as-short-product-symbol'):ck(label+' short asprep fit','81%' in text and '19%' in text and 'less than 15 min' in text and 'approximately 15 min' in text)
   if row['registry_id'].endswith('calcined-short-product-symbol'):ck(label+' short calcined fit','33%' in text and '67%' in text and 'not Ce/O stoichiometry' in text)
   if row['registry_id'].endswith('as-long-product-symbol'):ck(label+' long asprep non-detection','more than 5 h' in text and 'not a measured exact zero' in text)
   if row['registry_id'].endswith('calcined-long-product-symbol'):ck(label+' long calcined approximate fit','approximately 45%' in text and 'No unreported 55%' in text)
  if 'tga' in sid or sid=='source-unit-pati2009-figure-3-a':ck(label+' thermal analysis scope','TGA in air' in text and 'do not redefine the 200' in text)
  if sid in {'calcined-powders-for-reported-areas','three-calcined-solvent-powders'}:ck(label+' BET comparison not pool','not a pooled specimen' in text and all(n in text for n in ['78','80','84','9.8','9.3']) and 'spherical-particle assumption' in text)
excluded={(x['record_id'],x['sample_id']):x for x in b['excluded_contexts']}
ck('39 mappings/14 records/117 exclusions',len(pairs)==39 and len(ctx['recordContexts'])==14 and len(excluded)==117)
for rid,r in records.items():
 for p in r['products']:ck(rid+'/'+p['sample_id']+' included xor excluded',((rid,p['sample_id']) in pairs)^((rid,p['sample_id']) in excluded))
ck('156 context slots fully accounted',sum(len(r['products']) for r in records.values())==len(pairs)+len(excluded)==156)
for key,x in excluded.items():
 ck('/'.join(key)+' exact exclusion',ptr(records[key[0]],x['canonical_product_pointer'])==x['canonical_product_snapshot'] and bool(x['reason']))
for x in b['bindings']:
 key=(x['record_id'],x['sample_id']);row=pairs[key]
 ck('/'.join(key)+' exact map binding',sha(Path(x['canonical_record_path']))==x['canonical_record_sha256'] and digest(ptr(records[key[0]],x['product_pointer']))==x['product_sha256'] and digest(entries[x['registry_id']])==x['entry_sha256'])
ck('Three separate solvent route mappings',all(len(ctx['recordContexts']['pati-2009-'+s+'-route'])==1 for s in ['ethanol','propanol','butanol']))
for e in entries.values():
 ck(e['id']+' immutable symbol',sha(P/e['svgPath'])==e['assetHashes']['svgPath'])
 ck(e['id']+' no atom model',e['depictionKind']=='symbolic_context' and e['model2dPath'] is None and e['model3dPath'] is None and e['eligible_training'] is False)
 if e['id'] not in ['pati2009-calcined-product-symbol','pati2009-local-ceo2-product-symbol']:ck(e['id']+' no invented composition',e['formula']=='')
 text=(P/e['svgPath']).read_text('utf8').lower();ck(e['id']+' inert SVG','<script' not in text and 'javascript:' not in text)
assets=read(P/'public-asset-proposal.json')['assets'];ck('11 allowlisted symbols only',len(entries)==len(assets)==11)
for x in assets:ck(x['entry_id']+' asset allowlist',sha(Path(x['path']))==x['sha256'] and x['public_path'].startswith('assets/chemical-registry/pati2009-products/') and x['public_path'].endswith('.svg'))
ck('Source notice retained',pub['sourceNotices']==ctx['sourceNotices'])
out={'schema':'mattersyn-independent-product-context-audit/1','status':'passed','author':'/root','proposal_author':freeze['author'],'at':datetime.now(timezone.utc).isoformat(),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'checks':len(checks),'counts':{'mappings':39,'records':14,'exclusions':117,'total_context_slots':156,'symbols':11,'atomic_models':0},'manual_scope':'Root visually read all four original main and four SI pages in this turn, reopened main2/3 and SI2/3 during this audit, viewed all eleven symbolic cards on four contact sheets, and read every proposed context caption. Separate source/canonical audits remain their own approvals.','reviewed_source_pages':{'main':[1,2,3,4],'si':[1,2,3,4]},'scientific_values_changed':False,'open_findings':[],'limitations':['Illustrations are symbolic source contexts, not measured geometry or exact training pairs.','Mounted-browser, Site integration and publication checks remain pending.','Source DLS size-metric, XPS labels and calibration conflicts remain unresolved.'],'bound_files':{str(p):sha(p) for p in [P/'package-freeze.json',C/'package-manifest.json',V/'package-manifest.json',N/'source-independent-audit/independent-audit-v1.json',N/'canonical-reader-independent-audit/independent-audit-v2.json']},'check_results':checks}
(A/'independent-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'status':'passed','checks':len(checks),'sha256':sha(A/'independent-audit.json')}))
