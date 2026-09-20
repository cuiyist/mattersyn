"""Root independent source/specimen/context review. Never mutates proposals."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
A=Path(__file__).resolve().parent; N=A.parent; P=N/'visuals/product-context'; C=N/'canonical-proposal/v1'
def read(p): return json.loads(p.read_text('utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def objsha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def ptr(o,s):
 for t in s.strip('/').split('/'): o=o[int(t)] if isinstance(o,list) else o[t.replace('~1','/').replace('~0','~')]
 return o
checks=[]
def ck(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
 assert ok,name
freeze=read(P/'package-freeze.json')
ck('Distinct proposal author',freeze['author']=='/root/peng1998_reader_assets')
for name,h in freeze['bound_files'].items(): ck('Immutable '+name,sha(Path(name))==h)
ck('Source audit passed',read(N/'source-independent-audit/independent-audit-v2.json')['status']=='passed')
records={p.stem:read(p) for p in C.glob('matuhina-*.json')}
sf=read(N/'source-facts.json'); ctx=read(P/'product-contexts-additions.json'); bind=read(P/'bindings.json'); reg=read(P/'registry-additions.json')
entries={x['id']:x for x in reg['entries']}; pairs={}; seen=set()
# Root's source comparisons: main2/3 apparatus and specimens; main4/5 diffraction;
# main8/9/10 optical, device and aging; SI6/7 coordinate-table limitations; SI13 aged mixture.
for rid,rows in ctx['recordContexts'].items():
 ck(rid+' actual source',records[rid]['lineage']['source_group']=='matuhina2023')
 for row in rows:
  sid=row['sample_id']; key=(rid,sid,row['registry_id']); label='/'.join(key)
  ck(label+' unique',key not in seen); seen.add(key); pairs.setdefault((rid,sid),[]).append(row)
  product=ptr(records[rid],row['canonical_product_pointer'])
  ck(label+' exact original product',product==row['canonical_product_snapshot'] and product['sample_id']==sid)
  ck(label+' illustrative only',row['projection_kind']=='source_scoped_symbolic_context' and row['training_eligible'] is False and row['atomic_model'] is False and row['same_physical_batch_asserted'] is False)
  ck(label+' visible qualification','symbolic source-context' in row['caption'] and 'training-pair admission' in row['caption'])
  factids=[]
  for link in row['source_fact_links']:
   ck(label+' source file',Path(link['path']).resolve()==(N/'source-facts.json').resolve())
   fact=ptr(sf,link['json_pointer']); factids.append(fact['id'])
   ck(label+' source fact exact',objsha(fact)==link['sha256'])
  ck(label+' exact source ID set',factids==row['source_fact_ids'])
  for link in row['canonical_claim_links']:
   claim=ptr(records[link['record_id']],link['json_pointer'])
   ck(label+' canonical file bound',sha(C/(link['record_id']+'.json'))==link['record_sha256'])
   ck(label+' exact canonical claim',claim==link['canonical_measurement'] and claim['id']==link['measurement_id'])
  ck(label+' supported claim linkage',bool(row['source_fact_links']) and bool(row['canonical_claim_links']))
  ck(label+' symbolic asset registered',row['registry_id'] in entries)
  if sid.startswith('nc150'):
   ck(label+' cubic source-preparation scope','cubic' in row['caption'] and 'named preparation condition' in row['caption'] and 'identical physical aliquot' in row['caption'])
  if sid.endswith('-icp'):
   ck(label+' digestion is not diffraction','digested analytical specimen' in row['caption'] and 'not the crystal phase' in row['caption'])
  if sid=='ltpl-nc180-05': ck(label+' silica film distinct','on silica' in row['caption'] and 'glass-supported LSC' in row['caption'])
  if sid.startswith('lsc-'):
   ck(label+' glass unencapsulated and no invented batch','on glass' in row['caption'] and 'unencapsulated' in row['caption'] and 'not assigned' in row['caption'])
  if sid=='lsc-aged': ck(label+' same aged device film','same device film' in row['caption'] and 'eleven weeks' in row['caption'])
  if sid=='cubic-film': ck(label+' aging phase transition','does not assert that the aged film remains cubic' in row['caption'])
  if sid=='rhombohedral-dispersion': ck(label+' optical aging ambiguity','hexane-dispersion' in row['caption'] and 'normalized integrated PL' in row['caption'] and 'not harmonized' in row['caption'])
  if sid=='aged-rhombohedral': ck(label+' unassigned variant and age','Exact loading variant and age are not specified' in row['caption'])
  if sid=='aged-nc150': ck(label+' component not whole or new route',row['phase_component_formula'] in {'CsCl','Cs3MnCl5','CsMn4Cl9'} and 'neither the whole-specimen formula nor a new independently synthesized product' in row['caption'])
  else: ck(label+' no new component composition',row['phase_component_formula'] is None)
ck('Expected projection counts',len(seen)==47 and len(pairs)==45 and len(ctx['recordContexts'])==11)
ck('Aged three-component refinement',set(r['phase_component_formula'] for r in pairs[('matuhina-2023-stability-results','aged-nc150')])=={'CsCl','Cs3MnCl5','CsMn4Cl9'})
ck('Five reported conditions only',set(r['sample_id'] for r in ctx['recordContexts']['matuhina-2023-hot-injection-series'])=={'nc150','nc180-07','nc180-05','nc180-035','nc200'})
excluded={(r['record_id'],r['sample_id']) for r in bind['excluded_contexts']}
ck('66 explicit exclusion scopes',len(excluded)==66)
for rid,r in records.items():
 for product in r['products']:
  key=(rid,product['sample_id']); ck('/'.join(key)+' included XOR excluded',(key in pairs)^(key in excluded))
for x in bind['excluded_contexts']:
 ck(x['record_id']+'/'+x['sample_id']+' exact excluded product',ptr(records[x['record_id']],x['canonical_product_pointer'])==x['canonical_product_snapshot'])
ck('No inferred measured DFT or unisolated outcome',not any('dft' in rid or 'unisolated' in rid for rid,sid in pairs))
for e in entries.values():
 ck(e['id']+' exact SVG',sha(P/e['svgPath'])==e['assetHashes']['svgPath'])
 ck(e['id']+' no atomic model',e['depictionKind']=='symbolic_context' and e['model2dPath'] is None and e['model3dPath'] is None and e['eligible_training'] is False)
ck('Seven source-context illustrations',len(entries)==7)
out={'schema':'mattersyn-independent-product-context-audit/1','status':'passed','author':'/root','proposal_author':freeze['author'],'at':datetime.now(timezone.utc).isoformat(),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'checks':len(checks),'counts':{'component_cards':47,'record_sample_pairs':45,'records':11,'exclusions':66,'symbols':7,'atomic_models':0},'manual_scope':'Root read original main pages 2,3,4,5,8,9,10 and SI pages 6,7,13, viewed all seven symbolic previews in three contact sheets, and compared every context caption and source/canonical pointer. This is a projection audit, not a replacement full-paper source or canonical audit.','reviewed_source_pages':{'main':[2,3,4,5,8,9,10],'si':[6,7,13]},'scientific_values_changed':False,'open_findings':[],'limitations':['SI supplies coordinate tables with qualification conflicts; coordinates are not absent, but these cards are not atomic reconstructions.','Canonical independent audit and integrated browser/publication gates remain separate.','No new exact structure-recipe or training-pair admission.'],'bound_files':{str(P/'package-freeze.json'):sha(P/'package-freeze.json'),str(C/'package-manifest.json'):sha(C/'package-manifest.json')},'check_results':checks}
(A/'independent-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'sha256':sha(A/'independent-audit.json')}))
