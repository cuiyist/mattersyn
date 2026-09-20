"""Independent Pati source/canonical/reader transport checks; no author file writes."""
from pathlib import Path
import sys,json,hashlib,re,collections
A=Path(__file__).resolve().parent;G=A.parent;C=G/'canonical-proposal/v1';P=G/'public-review-proposal/v1';S=Path('[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups
checks=collections.Counter();failures=[];bound={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def ck(ok,cat,detail):
 checks[cat]+=1
 if not ok:failures.append({'category':cat,'detail':detail})
def ptr(x,p):
 for k in p.lstrip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
def slug(x):return re.sub('[^a-z0-9]+','-',x.lower()).strip('-')
def quantity_sample(f,x):
 # Measurements retain broad source-fact context; a specific name remains in their property/conditions.
 return slug(f['sample_scope'])
def table_sample(t,row):return 'xps-fit-context'
def walk(x,p=''):
 yield p,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k.replace('~','~0').replace('/','~1'))
 if isinstance(x,list):
  for k,v in enumerate(x):yield from walk(v,p+'/'+str(k))
def evcheck(q,src,context):
 for ev in src:
  hay=' '.join(e.get('locator','') for e in q.get('evidence',[]))
  ck(ev['source_sha256'] in hay,'source_hash_locator',context)
  ck(ev['locator'] in hay and 'PDF p. '+str(ev['pdf_page']) in hay,'source_page_locator',context)
def qcheck(q,x,context):
 ck(q.get('raw_text',x['raw_text'])==x['raw_text'],'raw_token',context)
 comp=x.get('comparison');rng=x.get('range');v=x.get('value')
 if comp in ['>','>=','<','<=']:
  side='minimum' if comp.startswith('>') else 'maximum'
  ck(q.get('value') is None and q.get(side)==v,'quantity_bound',context)
  ck(bool(q.get(side+'_exclusive'))==(comp in ['>','<']),'bound_inclusivity',context)
 elif rng is not None:
  lo,hi=(rng['min'],rng['max']) if isinstance(rng,dict) else sorted(rng)
  ck(q.get('value') is None and q.get('minimum')==min(lo,hi) and q.get('maximum')==max(lo,hi),'quantity_range',context)
 elif x.get('components') is not None:
  ck(q.get('value')==x['raw_text'],'ratio_literal',context)
 elif isinstance(v,(int,float)):
  ck(q.get('value')==v,'quantity_value',context)
 else:
  ck(q.get('value') in [v,x['raw_text']],'text_value',context)
 if 'unit' in q:ck((q.get('unit') or None)==x.get('unit'),'quantity_unit',context)
 if 'approximate' in q:ck(q.get('approximate')==x.get('approximate',False),'quantity_approximation',context)
 if x.get('uncertainty') is not None:
  ck(str(x['uncertainty']) in json.dumps(q,ensure_ascii=False),'uncertainty_retained',context)
 evcheck(q,x.get('evidence',[]),context)
 for k in ['conflict_ids','gap_ids']:
  for identity in x.get(k,[]):
   ck(identity in json.dumps(q,ensure_ascii=False),'qualification_retained',context+' '+identity)
freeze=read(C/'package-manifest.json')
ck(sha(C/'package-manifest.json')=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281','expected_freeze','v1')
for path,hashvalue in freeze['bound_files'].items():
 p=Path(path);ck(p.exists() and sha(p)==hashvalue,'freeze_hash',str(p));bound[str(p)]=sha(p)
src=read(G/'source-facts.json');inv=read(G/'source-inventory.json');tables=read(G/'source-tables.json')['tables'];assets=read(G/'original-assets-manifest.json')['assets']
audit=read(G/'source-independent-audit/independent-audit-v1.json')
facts={x['id']:x for x in src['facts']};units={x['id']:x for x in inv['inventory_units']};cells={row['id']+'-'+c['column']:(c,t,row) for t in tables for row in t['rows'] for c in row['cells']}
records={p.stem:read(p) for p in sorted(C.glob('pati-2009-*.json'))};cov=read(C/'source-to-field-coverage.json');lossless=read(C/'lossless-source-map.json')
for key in src:
 ck(lossless['source_facts'][key]==src[key],'lossless_source',key)
ck(lossless['source_tables']['tables']==tables,'lossless_source','tables')
ck({x['source_fact_id'] for x in cov['facts']}==set(facts),'fact_complete','62')
for frow in cov['facts']:
 f=facts[frow['source_fact_id']];ck(bool(frow['canonical_bindings']),'fact_has_binding',f['id'])
 for b in frow['canonical_bindings']:
  q=ptr(records[b['record_id']],b['pointer']);sourcevalue=ptr(f,b['source_pointer']);label=f['id']+' '+b['record_id']+b['pointer']
  if b['source_pointer']=='/claim':ck(q['value']==sourcevalue,'source_claim',label);evcheck(q,f['evidence'],label)
  else:qcheck(q,sourcevalue,label)
  if b['pointer'].startswith('/measurements/'):
   m=ptr(records[b['record_id']],b['pointer'].rsplit('/',1)[0]);ck(m['sample_id']==quantity_sample(f,sourcevalue),'fact_sample',label)
ck({x['source_unit_id'] for x in cov['source_units']}==set(units),'unit_complete','353')
for row in cov['source_units']:
 ck(bool(row['canonical_bindings']),'unit_has_binding',row['source_unit_id'])
 for b in row['canonical_bindings']:ck(ptr(records[b['record_id']],b['pointer']) is not None,'unit_pointer',row['source_unit_id'])
ck({x['source_cell_id'] for x in cov['table_cells']}==set(cells),'table_cells_complete','321')
for row in cov['table_cells']:
 x,t,tr=cells[row['source_cell_id']]
 for b in row['canonical_bindings']:
  q=ptr(records[b['record_id']],b['pointer']);qcheck(q,x,row['source_cell_id'])
  m=ptr(records[b['record_id']],b['pointer'].rsplit('/',1)[0]);ck(m['sample_id']==table_sample(t,tr),'cell_sample',row['source_cell_id'])
for row in cov['table_definitions']:
 q=ptr(records[row['record_id']],row['pointer']);t=next(t for t in tables if t['id']==row['table_id']);ck(json.loads(q['value'])=={k:v for k,v in t.items() if k!='rows'},'table_definition_payload',row['table_id'])
for row in cov['source_objects']:ck(ptr(records[row['record_id']],row['pointer']) is not None,'source_object_pointer',row)
source_materials={m['id']:m for m in src['materials']}
source_stocks={s['id']:s for s in src['stocks']}
source_ops={o['id']:o for p in src['protocols'] for o in p['operations']}
for rid,r in records.items():
 for m in r['materials']:
  original=source_materials[m['id']]
  for k,sk in [('id','id'),('name','name'),('formula','source_formula_or_abbreviation'),('role','role')]:ck(m[k]==original[sk],'material_identity',rid+'/'+m['id']+'/'+k)
  ck(original['scope_note'] in m['notes'],'material_scope',rid+'/'+m['id']);evcheck(m,original['evidence'],m['id'])
 for st in r['stocks']:
  original=source_stocks[st['id']]
  ck([c['material_id'] for c in st['components']]==[c['material_id']for c in original['components']],'stock_components',st['id'])
  ck(all(not c['quantities']for c in st['components']),'unknown_component_charge',st['id'])
  ck(original['scope_note'] in st['scope'] and original['preparation'] in st['scope'],'stock_scope',st['id'])
  ck('final_volume' not in st or st['final_volume'].get('value') is None,'no_transfer_as_stockvolume',st['id'])
  ck(len(st['concentrations'])==1,'one_stock_concentration',st['id'])
  qcheck(next(iter(st['concentrations'].values())),original['quantities'][0],st['id'])
for oid,bindings_ in cov['operation_instances'].items():
 original=source_ops[oid]
 for b in bindings_:
  r=records[b['record_id']];actual=ptr(r,b['pointer']);label=b['record_id']+'/'+actual['id']
  ck(actual['label']==original['action'],'operation_action',label);evcheck(actual,original['evidence'],label)
  retained_ids={'filter':'precipitate','alcohol-wash':'washed-precipitate','acetone-wash':'as-prepared-powder','diagnostic':'diagnostic-mixture'}
  ck(actual['retained_fraction']==retained_ids.get(oid,original['retained_fraction']),'retained_fraction',label)
  for key,qq in actual['parameters'].items():
   cand=[z for z in original['quantities']if slug(z['meaning']).replace('-','_')==key]
   ck(len(cand)==1,'operation_parameter_source',label+'/'+key)
   if cand:qcheck(qq,cand[0],label+'/'+key)
  for x in original['missing_fields']:ck(x in json.dumps(actual,ensure_ascii=False),'operation_missingness',label+'/'+x)
for row in cov['source_units']:
 unit=units[row['source_unit_id']]
 if unit['payload_path']!='source-facts.json':continue
 original=ptr(src,unit['json_pointer'])
 for b in row['canonical_bindings']:
  q=ptr(records[b['record_id']],b['pointer'])
  if b['pointer'].startswith('/measurements/') and unit['kind'] not in ['facts','sample_contexts']:
   value=q.get('value')
   if isinstance(value,str) and value.startswith('{'):ck(json.loads(value)==original,'complete_object_payload',unit['id'])
   elif unit['kind']=='references':ck(value==original['text'],'complete_reference_payload',unit['id'])
   elif unit['kind']=='conflicts':ck(value==original['description'],'complete_conflict_payload',unit['id'])
   elif unit['kind']=='missingness':ck(value==original['description'],'complete_gap_payload',unit['id'])
allq=set();measurements=set();ops=set()
for rid,r in records.items():
 ck(not validate_record(r),'current_schema',{'record_id':rid,'errors':validate_record(r)})
 ck(not any(v['eligible'] for v in eligibility(r).values()),'no_training',rid)
 ck(r['quality']['review_status']=='imported_unreviewed' and not r['quality']['requested_tasks'] and 'collection' not in r,'admission_metadata',rid)
 ck(not r['structure_assets'],'no_atomic_asset',rid)
 ck(r['lineage']['source_group']=='pati2009','single_source_group',rid)
 for ix,m in enumerate(r['measurements']):measurements.add((rid,'/measurements/'+str(ix)+'/value'))
 for o in r['operations']:ops.add((rid,o['id']))
 for p,x in walk(r):
  if isinstance(x,dict) and 'value' in x and 'status' in x and 'evidence' in x:allq.add((rid,p))
ck(len(set(build_groups(list(records.values())).values()))==1,'no_source_split_leakage','all21')
for p in [S/'scripts/dataset_lib.py',S/'scripts/schema_definition.py',S/'scripts/build_paper_reviews.py']:bound[str(p)]=sha(p)
reader=read(P/'pati2009.json');rcov=read(P/'source-item-coverage.json');bindings=read(P/'reader-bindings-proposal.json')
items=[i for s in reader['reader_sections'] for i in s['items']];itemmap={i['id']:i for i in items};rfields=set();rfmap=collections.defaultdict(list)
ck(len(items)==len(itemmap),'reader_unique','380')
for i in items:
 ck(i['training_eligible'] is False,'reader_no_training',i['id'])
 for b in i.get('canonical_links',[]):ck(ptr(records[b['record_id']],b['json_pointer']) is not None,'reader_link',i['id'])
 for b in i.get('sample_scope',{}).get('canonical_sample_links',[]):ck(ptr(records[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'],'reader_sample_link',i['id'])
 for f in i['facts']:
  key=(f['canonical_record_id'],f['json_pointer']);q=ptr(records[key[0]],key[1]);rfields.add(key);rfmap[key].append((i['id'],f['id']))
  ck(f['canonical_quantity']==q,'reader_exact_quantity',f['id'])
  display=f['value'];value=q.get('value')
  if value is not None:
   if f['presentation_kind']=='curated_source_inventory':expected=json.loads(value)
   else:expected=value
  elif q.get('minimum') is not None and q.get('maximum') is not None:expected=str(q['minimum'])+'–'+str(q['maximum'])
  elif q.get('minimum') is not None:expected=('> ' if q.get('minimum_exclusive') else '≥ ')+str(q['minimum'])
  elif q.get('maximum') is not None:expected=('< ' if q.get('maximum_exclusive') else '≤ ')+str(q['maximum'])
  else:expected='Not reported'
  ck(display==expected or isinstance(display,str) and isinstance(expected,str) and re.sub(r'\s+','',display)==re.sub(r'\s+','',expected),'reader_display',f['id'])
  for k in ['unit','status','approximate']:ck(f.get(k)==q.get(k,False if k=='approximate' else None),'reader_semantics',f['id']+' '+k)
  if key in measurements:
   m=ptr(records[key[0]],key[1].rsplit('/',1)[0]);ck(f['sample_id']==m['sample_id'],'reader_measurement_sample',f['id'])
ck(measurements<=rfields,'reader_measurements_complete',list(measurements-rfields))
ck({k for k in allq if not k[1].startswith('/intended_target/')}<=rfields,'reader_fields_complete',list({k for k in allq if not k[1].startswith('/intended_target/')}-rfields))
for row in rcov['canonical_field_map']:ck((row['reader_item_id'],row['reader_fact_id']) in rfmap[(row['record_id'],row['json_pointer'])],'reverse_field_map',row)
ck(set(rcov['source_units'])==set(units),'reader_units_complete','353')
for uid,ii in rcov['source_units'].items():
 for iid in ii:ck(uid in itemmap[iid]['source_audit_unit_ids'],'reverse_unit_map',uid+' '+iid)
ck(set(rcov['source_facts'])==set(facts),'reader_facts_complete','62')
for fid,bb in rcov['source_facts'].items():
 for b in bb:ck((b['reader_item_id'],b['reader_fact_id']) in rfmap[(b['record_id'],b['pointer'])],'reader_fact_map',fid)
assetmap={a['id']:a for a in assets};seenassets=set()
for p,x in walk(reader):
 if isinstance(x,dict) and 'public_asset' in x:
  name=x['public_asset'].split('/')[-1].rsplit('.',1)[0];seenassets.add(name);ck(name in assetmap,'public_asset_allowlist',p)
  if name in assetmap:
   a=assetmap[name];ck(x.get('sha256',x.get('public_asset_sha256'))==a['sha256'],'public_asset_hash',p);ck(x['public_asset']=='assets/figures/pati2009/'+name+'.png','public_asset_path',p)
 if isinstance(x,str):ck(not re.search(r'(?i)([A-Z]:[[local path redacted]
ck(seenassets==set(assetmap),'all_selected_assets','30')
for a in assets:
 p=Path(a['path']);bound[str(p)]=sha(p);ck(sha(p)==a['sha256'] and a['contains_complete_source_page'] is False,'original_crop_bytes',a['id'])
for rid,contexts in reader['route_evidence_contexts'].items():ck(isinstance(contexts,list) and set(contexts)<=set(records),'actual_route_record_refs',rid)
chars=reader['characterization_inventory'];ck(isinstance(chars,dict) and set(chars['reader_item_ids'])<=set(itemmap),'characterization_contract','items')
for d in reader['documents']:ck([p['page'] for p in d['pages']]==list(range(1,d['page_count']+1)) and all(p['text_read'] and p['visual_review'] for p in d['pages']),'reader_page_coverage',d.get('role'))
for k in ['molecular_apparatus_bindings_approved','publication_approved']:ck(bindings[k] is False,'pending_gates',k)
for k in ['training_eligible','source_review_promoted']:ck(reader[k] is False,'pending_gates',k)
# Reader figure/sample scope and equation/table value preservation are verified independently of author checks.
sourcefigs={f['id']:f for f in src['figures']}
for fig in reader['figures']:
 fid=fig['id'].replace('pati2009-','',1);source=sourcefigs.get(fid,sourcefigs['figure-1'])
 ck(fig['document_role']==source['evidence'][0]['document_role'] and fig['page']==source['evidence'][0]['pdf_page'],'figure_source_page',fig['id'])
 expected_scope=' / '.join(p['sample_id']for p in source['panels']) if fid in sourcefigs else next(p['sample_id']for p in source['panels']if p['label']==fid[-1])
 ck(fig['sample_scope']['label']==expected_scope,'figure_source_scope',fig['id'])
 ck(fig['sample_scope']['same_batch_verified'] is False and fig['training_eligible'] is False,'figure_gates',fig['id'])
for rid,r in records.items():
 for product in r['products']:
  ck(product['batch_id'] is None and product['parent_sample_id'] is None,'no_invented_batch',rid+'/'+product['sample_id'])
  if product['sample_id'].endswith('-as-prepared'):
   ck(product['composition']['value'] is None and product['phase']['value'] is None,'unresolved_whole_powder',rid+'/'+product['sample_id'])
ck('canonical/reader, visual, browser and publication gates remain separate' in reader['independent_audit'],'reader_pending_own_review','explicit boundary')
for key in ['publication_status','coverage_status']:ck('passed' not in json.dumps(reader[key]).lower(),'reader_pending_own_review',key)
import shutil,importlib.util
fixture=A/'reader-contract-fixture'
for rid in records:
 dest=fixture/'data/records'/(rid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/(rid+'.json'),dest)
for a in assets:
 dest=fixture/'dist/assets/figures/pati2009'/(a['id']+'.png');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['path'],dest)
spec=importlib.util.spec_from_file_location('actual_reader_validator',S/'scripts/build_paper_reviews.py');validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator);validator.ROOT=fixture
actual_reader_errors=validator.validate(reader);ck(not actual_reader_errors,'actual_reader_consumer',actual_reader_errors)
bound[str(S/'scripts/review_scope.py')]=sha(S/'scripts/review_scope.py')
result={'schema':'mattersyn-independent-canonical-reader-checks/1','reviewer':'/root/norberg2004_extract','author':'/root/backlog_eta','check_count':sum(checks.values()),'checks_by_category':dict(checks),'failures':failures,'counts':{'records':len(records),'operations':len(ops),'measurements':len(measurements),'source_facts':len(facts),'source_units':len(units),'table_cells':len(cells),'reader_items':len(items),'reader_fields':len(rfields),'original_crops':len(assets)},'bound_files':[{'path':p,'sha256':h} for p,h in sorted(bound.items())]}
(A/'mechanical-checks-v1.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['bound_files']},ensure_ascii=False,indent=2)[:12000])
