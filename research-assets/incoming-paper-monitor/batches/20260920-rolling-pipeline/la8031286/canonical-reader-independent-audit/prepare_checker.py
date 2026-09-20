from pathlib import Path
A=Path(__file__).resolve().parent;T=A.parent.parent/'acsanm.2c04342/canonical-reader-independent-audit/check_proposal.py'
s=T.read_text('utf8').replace('Matuhina','Pati').replace('matuhina2023','pati2009').replace('matuhina-2023','pati-2009').replace('958771dbb0d0f001e345a78f91da7f7d76d87fed90388f6c9e0b0dc65c5515a3','5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281').replace('independent-audit-v2.json','independent-audit-v1.json')
start=s.index('def table_sample');end=s.index('def walk',start)
s=s[:start]+"def table_sample(t,row):return 'xps-fit-context'\n"+s[end:]
s=s.replace("cells={c['id']:(c,t,row) for t in tables for row in t['rows'] for c in row['cells']}","cells={row['id']+'-'+c['column']:(c,t,row) for t in tables for row in t['rows'] for c in row['cells']}")
s=s.replace("unit['path']","unit['payload_path']")
start=s.index('source_materials=');end=s.index('allq=set();',start)
s=s[:start]+'''source_materials={m['id']:m for m in src['materials']}
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
  ck(actual['retained_fraction']==original['retained_fraction'],'retained_fraction',label)
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
''' +s[end:]
start=s.index('for rid,r in records.items():\n for product in r[\'products\']:',s.index('sourcefigs='));end=s.index("ck('canonical and reader",start)
s=s[:start]+'''for rid,r in records.items():
 for product in r['products']:
  ck(product['batch_id'] is None and product['parent_sample_id'] is None,'no_invented_batch',rid+'/'+product['sample_id'])
  if product['sample_id'].endswith('-as-prepared'):
   ck(product['composition']['value'] is None and product['phase']['value'] is None,'unresolved_whole_powder',rid+'/'+product['sample_id'])
''' +s[end:]
# Invoke the actual reader validator with only its root redirected to a private fixture.
needle="result={'schema':'mattersyn-independent-canonical-reader-checks/1'"
start=s.index(needle)
s=s[:start]+'''import shutil,importlib.util
fixture=A/'reader-contract-fixture'
for rid in records:
 dest=fixture/'data/records'/(rid+'.json');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/(rid+'.json'),dest)
for a in assets:
 dest=fixture/'dist/assets/figures/pati2009'/(a['id']+'.png');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['path'],dest)
spec=importlib.util.spec_from_file_location('actual_reader_validator',S/'scripts/build_paper_reviews.py');validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator);validator.ROOT=fixture
actual_reader_errors=validator.validate(reader);ck(not actual_reader_errors,'actual_reader_consumer',actual_reader_errors)
bound[str(S/'scripts/review_scope.py')]=sha(S/'scripts/review_scope.py')
''' +s[start:]
(A/'check_proposal.py').write_text(s,'utf8')
