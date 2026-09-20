"""Check emitted Sasongko mappings and rendered evidence without running builder."""
from pathlib import Path
import json,hashlib,sys,re
O=Path(__file__).resolve().parent;J=O.parents[1];M=J.parents[4]
sys.path[:0]=[str(M/'research-assets/rdkit-runtime'),str(M/'research-assets/corpus-20260917/runtime')]
import pymupdf
from PIL import Image
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ptr(v,p):
 for k in p.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k]
 return v
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
inp=read(O/'input-bindings.json')
for p,h in inp['files'].items():ck('unchanged input '+p,sha(p)==h)
records={x['record_id']:read(x['path']) for x in read(J/'canonical-proposal/v1/record-manifest.json')['records']};sf=read(J/'source-extraction-revision-2/source-facts.json');sc={x['id']:x for x in sf['sample_contexts']};facts={x['id']:x for x in sf['facts']}
b=read(O/'bindings.json');ctx=read(O/'product-contexts-additions.json')['recordContexts'];pub=read(O/'public-product-contexts-proposal.json');reg=read(O/'registry-additions.json');entries={x['id']:x for x in reg['entries']};assets={x['id']:x for x in read(J/'original-assets-manifest.json')['assets']};tables=read(J/'source-tables.json');allmeasurements={m['id']:(rid,i,m) for rid,r in records.items() for i,m in enumerate(r['measurements'])}
universe={(rid,f'/products/{i}') for rid,r in records.items() for i,_ in enumerate(r['products'])};covered=set();links=0;cells=0
for x in b['bindings']+b['excluded_contexts']:
 rid=x['record_id'];p=x['canonical_product_pointer'];product=ptr(records[rid],p);ck('exact product '+rid+p,product==x['canonical_product_snapshot'] and jsha(product)==x['canonical_product_sha256']);covered.add((rid,p))
 if 'registry_id' in x:
  ck('only named source contexts',x['sample_id'] in sc);ck('entry hash',jsha(entries[x['registry_id']])==x['entry_sha256'])
 else:ck('only bookkeeping exclusions',x['sample_id'] not in sc and bool(x['reason']))
ck('all 117 product slots exact',covered==universe and len(covered)==117)
ck('all 33 contexts',set(x['sample_id'] for x in b['bindings'])==set(sc) and len(entries)==33 and len(b['bindings'])==42 and len(b['excluded_contexts'])==75)
for rid,rows in ctx.items():
 for row,pr in zip(rows,pub['recordContexts'][rid]):
  sid=row['sample_id'];ck('context snapshot '+sid,row['source_context_snapshot']==sc[sid]);ck('phase/sample gates '+sid,not row['atomic_model'] and not row['training_eligible'] and not row['same_physical_batch_asserted'] and not row['binding_approved']);ck('public descriptive equality '+sid,all(row[k]==v for k,v in pr.items() if k!='original_evidence_links'))
  for x in row['canonical_claim_links']+row['canonical_quantity_links']:
   m=ptr(records[x['record_id']],x['json_pointer']);ck('exact measurement '+x['measurement_id'],m==x['canonical_measurement']);links+=1
  for x in row['canonical_quantity_links']:ck('numeric sample isolation '+sid,x['canonical_measurement']['sample_id']==sid)
  for x in row['canonical_claim_links']:ck('claim is scoped source fact',x['measurement_id'][:-6] in row['source_fact_ids'] and x['canonical_measurement']['value']['value']==facts[x['measurement_id'][:-6]]['claim'])
  for x in row['source_table_rows']:
   r=ptr(tables,x['json_pointer']);ck('table row snapshot '+sid,r==x['row'] and jsha(r)==x['sha256']);ck('table sample exact '+sid,r['sample_context']==sid)
  for x in pr['original_evidence_links']:
   a=assets[x['asset_id']];ck('original bytes and sample scope '+sid,x['sha256']==a['sha256'] and sid in a['sample_context_ids'] and sha(a['path'])==a['sha256']);ck('public path allowlist',x['public_asset']=='assets/figures/sasongko2025/'+Path(a['path']).name and re.fullmatch(r'assets/figures/sasongko2025/[a-z0-9-]+\.png',x['public_asset']) is not None)
  ck('literature does not assign current phase '+sid,not sid.startswith(('table-s1','alpha-ref','beta-ref','gamma-ref')) or row['phase']['value'] is None)
for t in tables['tables']:
 for row in t['rows']:
  if row['sample_context'] not in sc:continue
  for i,c in enumerate(row['cells']):
   mid=f"{t['id']}-{row['id']}-cells{i}";ck('canonical cell exists '+mid,mid in allmeasurements);rid,mi,m=allmeasurements[mid];q=m['value'];raw=q.get('raw_text',q.get('value'))
   ck('card source cell exact '+mid,raw==c['raw_text'] and m['sample_id']==row['sample_context']);cells+=1
for e in entries.values():
 p=O/e['svgPath'];ck('no atomic/whole-composition model',e['formula']=='' and e['model2dPath'] is None and e['model3dPath'] is None and not e['functionalGroups']);ck('SVG digest '+e['id'],sha(p)==e['assetHashes']['svgPath'])
 d=pymupdf.open(stream=p.read_bytes(),filetype='svg');pix=d[0].get_pixmap(alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);old=Image.open(O/'previews'/(p.stem+'.png')).convert('RGB');ck('pixel replay '+p.name,im.size==old.size and im.tobytes()==old.tobytes())
 for span in d[0].get_text('dict')['blocks']:
  if 'lines' not in span:continue
  for line in span['lines']:
   for s in line['spans']:
    x0,y0,x1,y1=s['bbox'];ck('visible text bounds '+p.name,0<=x0<x1<=d[0].rect.width and 0<=y0<y1<=d[0].rect.height)
ck('literal Pm3m remains',any('Pm3m' in e['displayFormula'] for e in entries.values()) and not any('Pm-3m' in e['displayFormula'] for e in entries.values()))
result={'status':'passed_author_output_validation','independent_approval':False,'check_count':len(checks),'exact_measurement_links':links,'exact_table_cells':cells,'checks':checks}
(O/'output-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
