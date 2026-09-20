"""Independent source boundary and current reader-consumer checks. No author builder."""
from pathlib import Path
import json,hashlib,sys,re
O=Path(__file__).resolve().parent;J=O.parent;C=J/'canonical-proposal/v1';S=J/'source-extraction-revision-2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ptr(x,p):
 for k in p.lstrip('/').split('/') if p else []:x=x[int(k)] if isinstance(x,list) else x[k.replace('~1','/').replace('~0','~')]
 return x
def walk(x,p=''):
 yield p,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
checks=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
sf=read(S/'source-facts.json');tables=read(J/'source-tables.json')['tables'];cov=read(C/'source-to-field-coverage.json');r=read(C/'reader/sasongko2025.json');records={x['record_id']:read(x['path']) for x in read(C/'record-manifest.json')['records']};items={x['id']:x for s in r['reader_sections'] for x in s['items']}
sys.path.insert(0,'[local path redacted]')
import build_paper_reviews as consumer
consumer.ROOT=C/'isolated-reader-fixture'
errors=consumer.validate(r);ck('actual current reader validator',not errors)
for rid,rec in records.items():
 allids={x['id'] for key in ['materials','stocks','material_states'] for x in rec[key]}
 prior=set()
 for op in rec['operations']:
  ck(rid+'/'+op['id']+' inputs outputs resolve',set(op['inputs']+op['outputs'])<=allids)
  ck(rid+'/'+op['id']+' dependencies precede',set(op['depends_on'])<=prior);prior.add(op['id'])
  if op['stage']=='characterization':
   states={x['id']:x for x in rec['material_states']}
   ck(rid+'/'+op['id']+' separate sample-set inputs',all(states[x]['kind']=='sample_set' for x in op['inputs']))
   ck(rid+'/'+op['id']+' acquisition data outputs',all(states[x]['kind']=='analysis_data' for x in op['outputs']))
   ck(rid+'/'+op['id']+' acquisition atmosphere not inherited',op['environment']['status']=='not_reported')
 for st in rec['material_states']:ck(rid+'/'+st['id']+' parents resolve',set(st['parent_ids'])<=allids)
 for m in rec['materials']:
  src=next(x for x in sf['materials'] if x['id']==m['id'])
  ck(rid+'/'+m['id']+' exact identity',m['name']==src['name'] and m['formula']==src['source_formula_or_abbreviation'])
 for link in rec['context_links']:
  if link['url'].startswith('/records/'):ck(rid+' context ID resolves',link['url'].removeprefix('/records/').removesuffix('.html') in records)
  else:ck(rid+' source reader link',link['url']=='/paper-review.html?id=sasongko2025')
 for st in rec['stocks']:
  src=next(x for x in sf['stocks'] if x['id']==st['id'])
  ck(rid+'/'+st['id']+' stock component identities', [x['material_id'] for x in st['components']]==[x['material_id'] for x in src['components']])
  ck(rid+'/'+st['id']+' no invented concentrations',st['concentrations']=={})
  for dst,sc in zip(st['components'],src['components']):
   srcqs=sc.get('amount_quantities',[sc['parts']] if 'parts' in sc else []);dstqs=list(dst['quantities'].values())
   ck(rid+'/'+st['id']+'/'+dst['material_id']+' exact quantities',len(srcqs)==len(dstqs) and all(a['value']==b['value'] and a['unit']==b['unit'] and a['raw_text']==b['raw_text'] for a,b in zip(srcqs,dstqs)))
route=records['sasongko-2025-hot-injection'];opts=route['condition_options'];ck('exact nine paired options',len(opts)==9)
expected={**{f'ligand-1-{n}':(100,v,0.2,1,20) for n,v in [(2,.4),(3,.6),(4,.8)]},**{f'wash-1-{n}':(100,.6,.2,1,n) for n in [1,10,20]},**{f'growth-{n}':(n,.6,.2,1,20) for n in [25,50,100]}}
keys=['growth_temperature','oa_volume','oam_volume','wash_acetonitrile_parts','wash_toluene_parts']
for opt in opts:ck(opt['id']+' exact paired choices',tuple(opt['parameters'][k]['value'] for k in keys)==expected[opt['id']])
ops={x['id']:x for x in route['operations']}
ck('first spin retains precipitate',ops['first-spin']['retained_fraction']=='first-precipitate' and ops['redisperse-hexane']['inputs']==['first-precipitate','hexane'])
ck('second spin retains supernatant',ops['second-spin']['retained_fraction']=='final-supernatant' and ops['store-supernatant']['inputs']==['final-supernatant'])
ck('wash alternatives not all pooled',ops['add-wash']['inputs']==['crude','selected-wash'] and 'not pooled' in ops['add-wash']['description'])
ck('0.51 mL is injection aliquot',ops['inject-fa']['parameters']['fa_precursor_aliquot']['value']==.51 and ops['inject-fa']['parameters']['fa_precursor_aliquot']['unit']=='mL')
ck('one route seven procedures eleven observations',sum(x['record_type']=='literature_protocol' for x in records.values())==1 and sum(x['record_type']=='procedure' for x in records.values())==7 and sum(x['record_type']=='observation' for x in records.values())==11)
ck('all source operation IDs mapped exactly once',{x['id'] for p in sf['protocols'] for x in p['operations']}=={x['source_operation_id'] for x in cov['operations']} and len(cov['operations'])==21)
for row in cov['operations']:
 src=ptr(sf,row['source_pointer']);dst=ptr(records[row['record_id']],row['pointer']);ck(row['source_operation_id']+' exact operation identity',src['id']==dst['id'])
for row in cov['facts']:
 src=next(x for x in sf['facts'] if x['id']==row['source_fact_id'])
 ck(src['id']+' every quantity and claim represented',{b['source_pointer'] for b in row['canonical_bindings']}=={'/claim'}|{'/quantities/'+str(i) for i in range(len(src['quantities']))})
expected_cells=set()
for ti,t in enumerate(tables):
 for ri,row in enumerate(t['rows']):
  for key in ['cells','additional_quantities']:
   for qi,q in enumerate(row.get(key,[])):expected_cells.add(f'/tables/{ti}/rows/{ri}/{key}/{qi}')
ck('complete numeric and text table-cell universe',expected_cells=={x['source_pointer'] for x in cov['table_cells']} and len(expected_cells)==127)
for row in cov['table_cells']:
 st=next(x for x in tables if x['id']==row['table_id']);sr=next(x for x in st['rows'] if x['id']==row['row_id']);meas=ptr(records[row['record_id']],row['pointer'].rsplit('/',1)[0]);ck(row['source_pointer']+' exact specimen context',meas['sample_id']==sr['sample_context'])
for context in sf['sample_contexts']:
 item=items['source-sample_contexts-'+context['id']]
 ck(context['id']+' named sample reader link',any(x['sample_id']==context['id'] for x in item['sample_scope']['canonical_sample_links']))
for fig in sf['figures']:
 item=items['source-figures-'+fig['id']];named={x['sample_id'] for x in item['sample_scope']['canonical_sample_links']}
 ck(fig['id']+' all source specimen links',set(fig['sample_context_ids'])<=named)
 for asset in item['original_assets']:
  meta=next(x for x in r['figures'] if x['id']==asset['id']);ck(asset['id']+' source role/page',meta['document_role']==fig['role'] and meta['page']==fig['page'])
for rid,ids in r['route_evidence_contexts'].items():ck(rid+' current evidence context IDs',rid in records and set(ids)<=set(records))
for ref in sf['references']:
 it=items['source-references-'+ref['id']];ck(ref['id']+' reference scope note','not claimed' in it['text'])
for a in read(J/'original-assets-manifest.json')['assets']:
 fp=C/'isolated-reader-fixture/dist/assets/figures/sasongko2025'/Path(a['path']).name
 ck(a['id']+' unchanged selected original',sha(a['path'])==a['sha256']==sha(fp) and a['contains_complete_source_page'] is False)
for p,x in walk(r):
 if isinstance(x,dict):
  ck(p+' no private raw page fields',not any(k in x for k in ['firstPagePreviewPrivate','full_page_text','page_text','complete_source_payloads']))
  if 'public_asset' in x:ck(p+' public asset selected crop only',str(x['public_asset']).startswith('assets/figures/sasongko2025/') and not str(x['public_asset']).endswith('.pdf'))
text=json.dumps(r,ensure_ascii=False)
ck('literal source Pm3m retained','Pm3m' in text and 'without silently adding an overbar' in text)
ck('reader atomic and public gates closed',r['training_eligible'] is False if 'training_eligible' in r else all(not x['training_eligible'] for x in items.values()))
out={'status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'reader_validator_errors':errors,'failures':[x for x in checks if not x['passed']],'checks':checks,'reader_validator_sha256':sha(consumer.__file__)}
(O/'scope-and-reader-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='checks'},ensure_ascii=False))
