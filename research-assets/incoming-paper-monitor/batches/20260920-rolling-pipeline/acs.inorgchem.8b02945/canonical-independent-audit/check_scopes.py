from pathlib import Path
import json,hashlib,sys
O=Path(__file__).resolve().parent;F=O.parent;C=F/'canonical-proposal/draft-v2';S=F/'source-extraction-revision-2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def walk(x,p=''):
 yield p,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k)
 if isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
sf=read(S/'source-facts.json');r=read(C/'reader/friedfeld2019.json');records={x['record_id']:read(x['path']) for x in read(C/'record-manifest.json')['records']};assets=read(S/'original-assets-manifest.json')['assets'];checks=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)})
sys.path.insert(0,'[local path redacted]')
import build_paper_reviews as consumer
consumer.ROOT=C/'isolated-reader-fixture'
errors=consumer.validate(r);ck('actual current reader validator on private fixture',not errors)
mat={x['id']:x for x in sf['materials']}
for rid,rec in records.items():
 for m in rec['materials']:
  src=mat[m['id']]
  ck(rid+'/'+m['id']+' identity formula exact',m['name']==src['name'] and m['formula']==src['source_formula_or_abbreviation'])
 for opt in rec['condition_options']:
  ck(rid+'/'+opt['id']+' source qualified independent alternative',all('Source-defined alternative' in v['basis'] for v in opt['parameters'].values()))
 for state in rec['material_states']:
  ck(rid+'/'+state['id']+' parents resolve',set(state['parent_ids'])<={x['id'] for k in ['materials','stocks','material_states'] for x in rec[k]})
 for link in rec.get('context_links',[]):
  if isinstance(link,dict) and link.get('record_id'):ck(rid+' context resolves '+link['record_id'],link['record_id'] in records)
for rid,ids in r['route_evidence_contexts'].items():ck(rid+' context array actual IDs',rid in records and set(ids)<=set(records))
items={x['id']:x for sec in r['reader_sections'] for x in sec['items']}
for fig in sf['figures']:
 item=items['source-figures-'+fig['id']];named={x['sample_id'] for x in item['sample_scope']['canonical_sample_links']}
 ck(fig['id']+' complete source sample mapping',set(fig['sample_context_ids'])<=named)
 for a in item['original_assets']:
  meta=next(x for x in r['figures'] if x['id']==a['id'])
  ck(fig['id']+' source role/page',meta['document_role']==fig['role'] and meta['page']==fig['page'])
for a in assets:
 ck(a['id']+' not whole source page',a.get('contains_complete_source_page') is False)
 p=C/'isolated-reader-fixture/dist/assets/figures/friedfeld2019'/Path(a['path']).name
 ck(a['id']+' actual public projection crop exact',p.is_file() and sha(p)==a['sha256'])
for p,x in walk(r):
 if isinstance(x,dict):
  ck(p+' no raw private page text field',not any(k in x for k in ['firstPagePreviewPrivate','full_page_text','page_text','complete_source_payloads']))
  if 'public_asset' in x:ck(p+' public asset selected excerpt only',str(x['public_asset']).startswith('assets/figures/friedfeld2019/') and not str(x['public_asset']).endswith('.pdf'))
v=records['friedfeld-2019-conversion-concentration'];s=v['stocks'][0]
ck('varied injection stock excludes representative solute charges',s['id']=='msc-injection-varied' and s['components'][0]['quantities']['condition_specific_mass']['value'] is None and len(s['components'][0]['quantities'])==1)
ck('varied 1 mL solvent volume marked inherited',next(iter(s['components'][1]['quantities'].values()))['status']=='inherited')
ck('30 records, 39 condition alternatives',len(records)==30 and sum(len(x['condition_options']) for x in records.values())==39)
result={'status':'passed' if all(x['passed'] for x in checks) else 'findings','check_count':len(checks),'failures':[x for x in checks if not x['passed']],'reader_validator_errors':errors,'checks':checks}
(O/'scope-and-public-projection-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
