from pathlib import Path
import json,hashlib,re,sys
sys.stdout.reconfigure(encoding='utf-8')
B=Path(__file__).resolve().parent.parent;A=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(o,p):
 for k in p.strip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');o=o[int(k)] if isinstance(o,list) else o[k]
 return o
checks=[]
def ck(name,test,detail=None):checks.append({'name':name,'passed':bool(test),**({'detail':detail} if not test and detail is not None else {})})
C=B/'canonical-proposal/v1';P=B/'public-review-proposal/v1'
package=load(C/'package-manifest.json');s=load(B/'source-facts.json');inventory=load(B/'source-inventory.json');tables=load(B/'source-tables.json')['tables'];sourcefacts={x['id']:x for x in s['facts']}
records={p.stem:load(p) for p in C.glob('morrison-*.json')};reader=load(P/'morrison2017.json');cm=load(C/'source-to-field-coverage.json');rm=load(P/'source-item-coverage.json');bindings=load(P/'reader-bindings-proposal.json')
items=[i for section in reader['reader_sections'] for i in section['items']];imap={x['id']:x for x in items}
for path,h in package['bound_files'].items():
 p=Path(path)
 ck('frozen dependency '+path,p.exists() and sha(p)==h)
ck('expected source revision2',sha(B/'package-freeze.json')==package['source_freeze_sha256'])
ck('known source audit boundary',sha(B/'source-independent-audit/independent-audit-v2.json')==package['source_audit']['sha256'])
lossless=load(C/'lossless-source-map.json')
for key in ['facts','materials','stocks','protocols','samples','tables','figures','schemes','equations','references','contradictions','gaps']:
 ck('curated sidecar exact '+key,lossless[key]==s[key])
ck('source fact universe',set(x['source_fact_id'] for x in cm['facts'])==set(sourcefacts))
ck('source unit universe',set(x['source_unit_id'] for x in cm['source_units'])==set(x['id'] for x in inventory['source_units']))
ck('reader unit universe',set(rm['source_units'])==set(x['id'] for x in inventory['source_units']))
ck('reader fact universe',set(rm['source_facts'])==set(sourcefacts))
ck('unique reader items',len(imap)==len(items)==252)
def qcheck(source,target,label):
 if not isinstance(source,dict):
  ck(label+' scalar',target.get('value')==source,(target,source));return
 if source.get('status')=='reported_text' or source.get('unit')=='identifier':
  ck(label+' literal context',target.get('value')==source.get('raw_text'))
  ck(label+' context source evidence',bool(target.get('evidence')))
  return
 for key in ['raw_text','unit','approximate']:
  ck(label+' '+key,target.get(key)==source.get(key),(target.get(key),source.get(key)))
 value=source.get('value');lo=hi=None
 if source.get('range'):
  rg=source['range'];lo,hi=(rg if isinstance(rg,list) else (rg.get('min'),rg.get('max')));value=None
 if source.get('comparison') in ['<','<=','≤']:hi=value;value=None
 if source.get('comparison') in ['>','>=','≥']:lo=value;value=None
 ck(label+' scalar',target.get('value')==value,(target.get('value'),value))
 ck(label+' lower',target.get('minimum')==lo,(target.get('minimum'),lo))
 ck(label+' upper',target.get('maximum')==hi,(target.get('maximum'),hi))
 if source.get('comparison') in ['<','>']:ck(label+' exclusive bound',source['comparison'] in target.get('qualifier','') or target.get('minimum_exclusive') or target.get('maximum_exclusive'))
 if source.get('uncertainty') is not None:ck(label+' uncertainty preserved',str(source['uncertainty']) in target.get('qualifier',''))
 if source.get('printed_to_value_scale') is not None:ck(label+' scale preserved',str(source['printed_to_value_scale']) in target.get('basis',''))
 ck(label+' evidence present',bool(target.get('evidence')))
for f in cm['facts']:
 source=sourcefacts[f['source_fact_id']]
 ck('fact nonempty '+source['id'],bool(f['canonical_bindings']))
 for b in f['canonical_bindings']:
  r=records[b['record_id']];target=ptr(r,b['pointer']);original=ptr(source,b['source_pointer']);label=source['id']+b['source_pointer']
  qcheck(original,target,label)
  if b['pointer'].startswith('/measurements/'):
   measurement=ptr(r,b['pointer'].rsplit('/',1)[0]);expected=source['sample_scope']
   if expected.startswith('study-wide acquisition;'):expected='study-wide-acquisition-sample-specific-assignment-remains-in-figure-measurement-entries'
   ck(label+' specimen',measurement['sample_id']==expected,(measurement['sample_id'],expected))
cells={cell['id']:cell for table in tables for row in table['rows'] for cell in row['cells']}
ck('table cell universe',set(cells)==set(x['source_cell_id'] for x in cm['table_cells'])==set(rm['table_cells']))
for row in cm['table_cells']:
 source=cells[row['source_cell_id']]
 for b in row['canonical_bindings']:qcheck(source,ptr(records[b['record_id']],b['pointer']),row['source_cell_id'])
allfields={}
for i in items:
 links=i.get('sample_scope',{}).get('canonical_sample_links',[])
 ck('unique specimen links '+i['id'],len(links)==len({(x['record_id'],x['sample_id']) for x in links}))
 for x in links:
  r=records[x['record_id']];p=ptr(r,x['json_pointer']);ck('sample link '+i['id']+x['sample_id'],p['sample_id']==x['sample_id'])
 for f in i.get('facts',[]):
  r=records[f['canonical_record_id']];v=ptr(r,f['json_pointer']);allfields[(r['record_id'],f['json_pointer'])]=f
  ck('reader canonical payload '+f['id'],f.get('canonical_quantity')==v)
  for k in ['value','unit','status','approximate']:
   if k in v:
    expected=v[k]
    if k=='value' and expected is None:
     if v.get('minimum') is not None and v.get('maximum') is not None:expected=str(v['minimum'])+'–'+str(v['maximum'])
     elif v.get('minimum') is not None:expected=('> ' if v.get('minimum_exclusive') else '≥ ')+str(v['minimum'])
     elif v.get('maximum') is not None:expected=('< ' if v.get('maximum_exclusive') else '≤ ')+str(v['maximum'])
     else:expected='Not reported'
    if k=='value' and isinstance(expected,str) and expected.startswith('{'):
     try:expected=json.loads(expected)
     except ValueError:pass
    ck('reader display '+f['id']+' '+k,f.get(k)==expected,(f.get(k),expected))
  ck('reader fact no training '+f['id'],f.get('training_eligible') is False)
 for l in i.get('canonical_links',[]):
  try:ptr(records[l['record_id']],l['json_pointer']);valid=True
  except (KeyError,IndexError,ValueError):valid=False
  ck('item pointer '+i['id']+l['record_id']+l['json_pointer'],valid)
ck('typed field cardinality',len(allfields)==1170)
for field in rm['canonical_field_map']:
 f=allfields[(field['record_id'],field['json_pointer'])];item=imap[field['reader_item_id']]
 ck('field index '+field['reader_fact_id'],f['id']==field['reader_fact_id'] and f in item['facts'])
for unit,ids in rm['source_units'].items():ck('source item reachability '+unit,bool(ids) and all(x in imap for x in ids))
for f,bs in rm['source_facts'].items():
 for b in bs:ck('source fact link '+f+b['source_pointer'],any(x['id']==b['reader_fact_id'] for x in imap[b['reader_item_id']]['facts']))
for rid,r in records.items():
 ck('unreviewed '+rid,r['quality']['review_status']=='imported_unreviewed')
 ck('no tasks '+rid,r['quality']['requested_tasks']==[])
 ck('no atomistic asset '+rid,r['structure_assets']==[])
 ids={x['id'] for x in r['materials']+r['stocks']+r['material_states']}
 ops={o['id'] for o in r['operations']};samples={p['sample_id'] for p in r['products']}
 for o in r['operations']:
  ck('operation pointer coverage '+rid+o['id'],rid+'::'+o['id'] in bindings['operation_to_reader_item'])
  ck('operation I/O '+rid+o['id'],all(x in ids for x in o['inputs']+o['outputs']))
  ck('operation dependencies '+rid+o['id'],all(x in ops for x in o['depends_on']))
  ck('retained output '+rid+o['id'],not o.get('retained_fraction') or o['retained_fraction'] in o['outputs'])
 for st in r['material_states']:ck('state lineage '+rid+st['id'],all(x in ids for x in st['parent_ids']))
 for m in r['measurements']:
  ck('measurement scope '+rid+m['id'],m['sample_id'] in samples)
  ck('measurement reader '+rid+m['id'],rid+'::'+m['id'] in rm['measurement_to_reader_item'])
 for k,slotkey,ident in [('material_to_reader_item','materials','id'),('stock_to_reader_item','stocks','id'),('product_to_reader_item','products','sample_id')]:
  for x in r[slotkey]:ck('slot reader '+rid+x[ident],rid+'::'+x[ident] in bindings[k])
assets=[a for a in reader['figures']+reader['tables']+reader['schemes']+reader['equations']+reader['source_notes'] if a.get('public_asset')];sourceassets={x['id']:x for x in inventory['assets']}
ck('asset count',len(assets)==30)
for asset in assets:
 source=sourceassets[asset['id'].removeprefix('morrison2017-')]
 ck('asset exact '+asset['id'],sha(Path(source['path']))==source['sha256']==asset['public_asset_sha256'])
 ck('asset document scope '+asset['id'],asset['document_role']==source['evidence'][0]['document_role'] and asset['page']==source['evidence'][0]['pdf_page'])
 ck('selected-only public path '+asset['id'],asset['public_asset'].startswith('assets/figures/morrison2017/') and not re.search(r'(?:main|si)-page',asset['public_asset']))
 ck('asset scope links '+asset['id'],all(x in records for x in asset['sample_links']))
text=json.dumps(reader,ensure_ascii=False)
ck('no absolute local source paths',not re.search(r'[A-Z]:[\\/]|file://',text))
ck('no full-page source payload keys',all(x not in text for x in ['firstPagePreviewPrivate','complete-source-payloads','text_cache','render_cache']))
ck('no publication approval',reader['publication_status']!='published' and reader['training_eligible'] is False)
report={'schema':'mattersyn.independent-canonical-reader-mechanical.v1','auditor':'/root/peng1998_reader_assets','checks':checks,'check_count':len(checks),'failures':[x for x in checks if not x['passed']],'status':'passed' if all(x['passed'] for x in checks) else 'findings','scope':'Independent transport, bounds, indices, source tables, sample links, assets and private publication gates; manual scientific review is separate.'}
(A/'mechanical-checks-v1.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'check_count':len(checks),'failure_count':len(report['failures']),'failures':report['failures'][:35]},ensure_ascii=False,indent=2))
