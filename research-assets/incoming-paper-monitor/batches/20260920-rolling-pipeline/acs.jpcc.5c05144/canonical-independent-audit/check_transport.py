"""Independent transport tests; does not execute the author builder or change its inputs."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys
O=Path(__file__).resolve().parent;F=O.parent;C=F/'canonical-proposal/v1';S=F/'source-extraction-revision-2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(x,p):
 if not p:return x
 for k in p.lstrip('/').split('/'):x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
def walk(x,p=''):
 if isinstance(x,dict):
  yield p,x
  for k,v in x.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
checks=[]
def ck(k,v,detail=None):
 row={'check':k,'passed':bool(v)}
 if not v and detail is not None:row['detail']=detail
 checks.append(row)
freeze=read(C/'package-freeze.json');m=read(C/'record-manifest.json');rcov=read(C/'reader/source-item-coverage.json');cov=read(C/'source-to-field-coverage.json');r=read(C/'reader/sasongko2025.json')
source={'source-facts.json':read(S/'source-facts.json'),'source-inventory.json':read(S/'source-inventory.json'),'source-tables.json':read(F/'source-tables.json'),'original-assets-manifest.json':read(F/'original-assets-manifest.json'),'page-coverage.json':read(S/'page-coverage.json')}
sf=source['source-facts.json'];facts={x['id']:x for x in sf['facts']};inv=source['source-inventory.json'];units={x['id']:x for x in inv['units']}
records={x['record_id']:read(x['path']) for x in m['records']};files={x['record_id']:x['path'] for x in m['records']}
ck('canonical exact frozen package',sha(C/'package-freeze.json')=='3cab2fe6181dbf2149b2a0ac59f4a80d99c05cab4870342e141815c904549fb5')
for category in ['bound_files','external_inputs']:
 for p,h in freeze.get(category,{}).items():
  fp=Path(p) if Path(p).is_absolute() else C/p
  ck('frozen '+p,fp.exists() and sha(fp)==(h.get('sha256') if isinstance(h,dict) else h))
for x in m['records']:ck('record manifest hash '+x['record_id'],sha(x['path'])==x['sha256'])
def quantity(label,src,dst):
 if src.get('status')=='reported_text':
  text_fact=dst.get('value')==src['raw_text'] and dst.get('status')=='reported' and 'unit' not in dst
  unknown_numeric=dst.get('value') is None and dst.get('minimum') is None and dst.get('maximum') is None and dst.get('raw_text')==src['raw_text'] and dst.get('status')=='not_reported' and dst.get('unit')=='time_text' and src['raw_text'] in dst.get('qualifier','')
  ck(label+' qualitative text preserved',text_fact or unknown_numeric)
  return
 ck(label+' raw exact',dst.get('raw_text')==src.get('raw_text'),[src,dst])
 ck(label+' unit exact',dst.get('unit')==src.get('unit'),[src.get('unit'),dst.get('unit')])
 ck(label+' approximate exact',dst.get('approximate',False)==src.get('approximate',False))
 bounds=src.get('range');comp=src.get('comparison');endpoints=src.get('ordered_endpoints')
 if bounds:
  lo,hi=(bounds['min'],bounds['max']) if isinstance(bounds,dict) else sorted(bounds)
  ck(label+' bounds exact',dst.get('minimum')==lo and dst.get('maximum')==hi and dst.get('value') is None,[bounds,dst])
 elif comp:
  op=comp if isinstance(comp,str) else comp.get('operator');val=src.get('value')
  side='minimum' if op in ['>','>=','≥'] else 'maximum'
  ck(label+' comparator exact',dst.get(side)==val and dst.get('value') is None,[src,dst])
  ck(label+' comparator exclusivity',dst.get(side+'_exclusive',False)==(op in ['>','<']),[src,dst])
 elif endpoints:
  ck(label+' descending endpoint preservation',str(endpoints[0]) in str(dst) and str(endpoints[1]) in str(dst),[src,dst])
 else:ck(label+' scalar exact',dst.get('value')==src.get('value'),[src.get('value'),dst.get('value')])
 for ev in src.get('evidence',[]):
  evtext=json.dumps(dst.get('evidence',[]),ensure_ascii=False)
  ck(label+' evidence '+str(ev.get('pdf_page')),ev['source_sha256'] in evtext and ('PDF p. '+str(ev['pdf_page'])) in evtext,[ev,dst.get('evidence')])
ck('all source facts covered',set(x['source_fact_id'] for x in cov['facts'])==set(facts))
for row in cov['facts']:
 f=facts[row['source_fact_id']]
 for b in row['canonical_bindings']:
  a=ptr(f,b['source_pointer']);v=ptr(records[b['record_id']],b['pointer']);label=f['id']+b['source_pointer']
  if b['source_pointer']=='/claim':ck(label+' verbatim claim',v['value']==a)
  else:quantity(label,a,v)
ck('all semantic units covered',set(x['source_unit_id'] for x in cov['source_units'])==set(units))
for row in cov['source_units']:
 unit=units[row['source_unit_id']];targets=[]
 for t in unit['extraction_targets']:
  if 'json_pointer' in t:targets.append(ptr(source[t['file']],t['json_pointer']))
  elif 'asset_id' in t:targets.append(next(x for x in source[t['file']]['assets'] if x['id']==t['asset_id']))
  elif 'private_payload_id' in t:targets.append(unit)
 for b in row['canonical_bindings']:
  v=ptr(records[b['record_id']],b['pointer'])['value']
  try:obj=json.loads(v)
  except Exception:obj=v
  if unit['id'] in ['sasongko2025-unit-graphical-abstract','sasongko2025-unit-si-index','sasongko2025-unit-publisher-ad']:
   ck(unit['id']+' safe provenance subset',all(obj.get(k)==unit[k] for k in ['id','kind','title','summary','source_payload_ids']) and obj.get('public_source_text_included') is False)
  else:ck(row['source_unit_id']+' lossless object',obj in targets or obj==unit,[obj,targets] if obj not in targets and obj!=unit else None)
for row in cov['table_cells']:
 a=ptr(source[row['source_file']],row['source_pointer']);v=ptr(records[row['record_id']],row['pointer']);quantity(row['table_id']+'/'+row['row_id']+'/'+str(row['column_index']),a,v)
for row in cov['operation_quantities']:
 a=ptr(source[row['source_file']],row['source_pointer']);v=ptr(records[row['record_id']],row['pointer']);quantity(row['record_id']+row['pointer'],a,v)

items=[x for s in r['reader_sections'] for x in s['items']];itemmap={x['id']:x for x in items};readerfacts=[(x,f) for x in items for f in x['facts']]
ck('273 reader items',len(items)==len(itemmap)==273)
expected={(rid,p) for rid,rec in records.items() for p,x in walk(rec) if 'value' in x and 'status' in x}
actual=[];measurements=set()
for it,f in readerfacts:
 rid=f['canonical_record_id'];p=f['json_pointer'];actual.append((rid,p));v=ptr(records[rid],p)
 ck(it['id']+'/'+f['id']+' exact canonical quantity',v==f['canonical_quantity'])
 ck(it['id']+'/'+f['id']+' status exact',v['status']==f['status'])
 ck(it['id']+'/'+f['id']+' approximate exact',v.get('approximate',False)==f.get('approximate',False))
 if f['presentation_kind']=='curated_source_inventory':
  ck(it['id']+'/'+f['id']+' structured display exact',f['value']==json.loads(v['value']))
 else:
  expected_value=v['value']
  if expected_value is None:
   lo,hi=v.get('minimum'),v.get('maximum')
   if lo is not None and hi is not None:expected_value=f'{lo}–{hi}'
   elif lo is not None:expected_value=('> ' if v.get('minimum_exclusive') else '≥ ')+str(lo)
   elif hi is not None:expected_value=('< ' if v.get('maximum_exclusive') else '≤ ')+str(hi)
   else:expected_value='Not reported'
  ck(it['id']+'/'+f['id']+' displayed scalar or bound exact',f['value']==expected_value)
 if 'unit' in v:ck(it['id']+'/'+f['id']+' unit exact',v['unit']==f['unit'])
 if re.fullmatch(r'/measurements/\d+/value',p):
  meas=ptr(records[rid],p.rsplit('/',1)[0]);measurements.add((rid,meas['id']))
  ck(it['id']+'/'+f['id']+' exact measurement context',f.get('sample_id')==meas['sample_id'])
 ck(it['id']+'/'+f['id']+' training false',f.get('training_eligible') is False)
ck('independent all typed-field universe covered exactly',set(actual)==expected and len(actual)==len(expected)==1197,{'expected':len(expected),'actual':len(actual),'missing':list(expected-set(actual)),'extra':list(set(actual)-expected)})
ck('all 502 measurements linked',measurements=={(rid,x['id']) for rid,rec in records.items() for x in rec['measurements']} and len(measurements)==502)
for row in rcov['canonical_field_map']:
 it=itemmap[row['reader_item_id']];matches=[x for x in it['facts'] if x['id']==row['reader_fact_id']]
 ck('coverage field '+row['reader_fact_id'],len(matches)==1 and matches[0]['canonical_record_id']==row['record_id'] and matches[0]['json_pointer']==row['json_pointer'])
ck('reader units universe exact',set(rcov['source_units'])==set(units))
for uid,itemids in rcov['source_units'].items():
 for iid in itemids:ck(uid+' reader unit binding',iid in itemmap and uid in itemmap[iid]['source_audit_unit_ids'])
for it in items:
 ck(it['id']+' unapproved',it.get('reviewed') is False and it.get('training_eligible') is False)
 links=it.get('sample_scope',{}).get('canonical_sample_links',[]);seen=set()
 for link in links:
  rid=link['record_id'];p=link['json_pointer'];x=ptr(records[rid],p);key=(rid,link['sample_id'])
  ck(it['id']+' exact sample '+str(key),x['sample_id']==link['sample_id'])
  ck(it['id']+' no repeated sample '+str(key),key not in seen);seen.add(key)
 for link in it['canonical_links']:ck(it['id']+' canonical link resolves',ptr(records[link['record_id']],link['json_pointer']) is not None)

assets=read(F/'original-assets-manifest.json');assetrows=assets.get('assets',assets.get('original_assets',[]));assetbyid={x['id']:x for x in assetrows};used=set();asset_keys=[]
for it in items:
 for a in it['original_assets']:
  used.add(a['id']);orig=assetbyid.get(a['id']);ck(it['id']+' asset ID exists',orig is not None)
  if orig is not None:
   asset_keys=list(orig)
   digest=orig.get('sha256') or orig.get('public_asset_sha256') or orig.get('asset_sha256')
   ck(it['id']+' original image exact',a['public_asset_sha256']==digest,[digest,a['public_asset_sha256']])
ck('all 17 crops reachable',used==set(assetbyid) and len(used)==17,{'used':len(used),'original':len(assetbyid),'keys':asset_keys})
for rid,rec in records.items():
 ck(rid+' no training tasks',rec['quality']['requested_tasks']==[])
 ck(rid+' unreviewed gate',rec['quality']['review_status']=='imported_unreviewed')
 ck(rid+' no atomic assets',rec['structure_assets']==[])
 ck(rid+' unique sample IDs',len({x['sample_id'] for x in rec['products']})==len(rec['products']))
 ck(rid+' unknown batch identity',all(x['batch_id'] is None for x in rec['products']))
 for meas in rec['measurements']:ck(rid+'/'+meas['id']+' sample resolves',meas['sample_id'] in {x['sample_id'] for x in rec['products']})
 for stock in rec['stocks']:
  ck(rid+'/'+stock['id']+' components resolve',all(x['material_id'] in {m['id'] for m in rec['materials']} for x in stock['components']))
result={'status':'supporting_checks_only_manual_review_pending','check_count':len(checks),'failures':[x for x in checks if not x['passed']],'checks':checks,'actual_counts':{'records':len(records),'materials':sum(len(x['materials']) for x in records.values()),'stocks':sum(len(x['stocks']) for x in records.values()),'operations':sum(len(x['operations']) for x in records.values()),'measurements':len(measurements),'typed_fields':len(expected),'reader_items':len(items)}}
(O/'transport-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2)[:14000])
