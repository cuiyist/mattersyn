"""Validate private metadata transport, coverage, scope and retained source hashes."""
from pathlib import Path
from collections import Counter
import hashlib,json
P=Path(__file__).resolve().parent
S=Path('[local path redacted]')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
d=read(P/'reader-presentation.json');inputs=read(P/'input-manifest.json')['files']
cache={};checks=0;findings=[]
def check(test,note):
 global checks
 checks+=1
 if not test:findings.append(note)
def obj(ref):
 path=ref['data_path']
 if path not in cache:cache[path]=read(S/path)
 val=cache[path]
 for part in ref['json_pointer'].split('/')[1:]:
  part=part.replace('~1','/').replace('~0','~')
  val=val[int(part)] if isinstance(val,list) else val[part]
 check(sha(S/path)==ref['input_sha256'],f'Source digest {path}')
 return val
for row in inputs:check(sha(S/row['path'])==row['sha256'],f'Input changed: {row["path"]}')
check(len(d['materials'])==50,'50 hubs')
check(len(d['records'])==123,'123 routes')
expected={rid for p in (S/'dist/data/materials').glob('*.json') for rid in read(p)['record_ids']}
check(set(d['records'])==expected,'Exact route universe')
for hid,h in d['materials'].items():
 original=obj(h['source'])
 check(h['record_ids']==original['record_ids'],f'{hid}: original route associations')
 check(h['component_only']==original['component_only'],f'{hid}: component scope')
for rid,r in d['records'].items():
 original=obj(r['source']);sample_ids={p['sample_id'] for p in original['products']}
 check(r['source_id']==original['lineage']['source_group'],f'{rid}: source group')
 for ctx in r['primary_product']['samples']:
  p=obj(ctx['source']);check(ctx['sample_id']==p['sample_id'],f'{rid}: sample id')
  check(ctx['recipe_link']==p['recipe_link'],f'{rid}: sample linkage unchanged')
 for fact in r['productFacts']:
  v=obj(fact['source']);check(fact['value']==v['value'],f'{rid}: exact product value')
  check(fact['status']==v['status'],f'{rid}: exact product status')
  check(fact['sample_id'] in sample_ids,f'{rid}: supported sample id')
  check(fact['source_locator']==v['evidence'],f'{rid}: evidence preserved')
 for fig in r['figures']:
  check(fig['source_id']==r['source_id'],f'{rid}: figure paper boundary')
  check(fig['category'] in ['structure','property','other'],f'{rid}: figure category')
  check(fig['same_batch_asserted'] is False,f'{rid}: no new same-batch assertion')
  if fig['record_link']:check(fig['record_link'] in fig['record_links'],f'{rid}: explicit figure-link basis')
  if fig['relationship']=='same_source_study_context':check('not established' in fig['scope'],f'{rid}: unassigned study scope')
 for x in r['intuition']:check(x['source_id']==r['source_id'],f'{rid}: intuition paper boundary');obj(x['source'])
 check(obj(r['nominalTarget']['source']).get('value')==r['nominalTarget']['value'],f'{rid}: target not product')
asset_manifest=[];classification_rows=[]
for sid,figs in d['figures_by_source'].items():
 for f in figs:
  original=obj(f['source'])
  check(f['summary']!='' and f['title']!='',f'{sid}: nonempty reviewed caption/title')
  if f['public_asset']:
   p=S/'dist'/f['public_asset'];check(p.is_file(),f'{sid}: figure file exists')
   check(sha(p)==f['public_asset_sha256'],f'{sid}: exact figure pixels')
   source_hash=original.get('public_asset_sha256') or original.get('original_figure_asset',{}).get('sha256')
   if source_hash:check(source_hash==f['public_asset_sha256'],f'{sid}: previously recorded original-asset hash')
   asset_manifest.append({'path':f['public_asset'],'sha256':f['public_asset_sha256']})
  else:check(sid=='peng2000' and 'asset_status' in f,'Only known text-only legacy figure entries')
  if 'caption_paraphrase' in original:check(f['summary']==original['caption_paraphrase'],'Complete reviewed source caption retained')
  if 'summary' in original:check(f['summary']==original['summary'],'Selected-evidence summary retained')
  classification_rows.append({'source_id':sid,'id':f['id'],'categories':f['categories'],'title':f['title'],'summary':f['summary'],'source':f['source']})
fap=d['records']['sasongko-2025-hot-injection']
for suffix in ['figure-1','figure-2','figure-3','figure-4','figure-5','figure-s2','figure-s3']:
 check(any(f['id'].endswith(suffix) and f['category']=='property' for f in fap['figures']),f'FAPbI3 property evidence: {suffix}')
for suffix in ['figure-1','figure-2','figure-3']:
 check(any(f['id'].endswith(suffix) and f['category']=='structure' for f in fap['figures']),f'FAPbI3 structural evidence: {suffix}')
check(len(d['figures_by_source']['murray1993'])==15,'All 15 Murray figures')
check(len(d['figures_by_source']['peng2000'])==4,'All four Peng 2000 figure evidence descriptions')
check(not any(not r['intuition'] for r in d['records'].values()),'Every route has existing scientific rationale')
# Public projection contains relative source identifiers, not private Windows paths.
raw=(P/'reader-presentation.json').read_text('utf8')
check('C:/' not in raw and 'C:\\\\' not in raw,'No private absolute Windows path')
report={'status':'passed' if not findings else 'open_findings','scope':'Author transport and presentation validation; no new scientific review or browser approval.',
 'checks':checks,'findings':findings,'metadata_sha256':sha(P/'reader-presentation.json'),
 'counts':d['counts'],'category_memberships':dict(Counter(c for fs in d['figures_by_source'].values() for f in fs for c in f['categories'])),
 'canonical_input_hashes_unchanged':all(sha(S/x['path'])==x['sha256'] for x in inputs if x['path'].startswith('data/records/')),
 'known_gaps':['Four Peng2000 source figures have reviewed descriptions but no public original figure-image assets.',
  'Unknown product composition/phase/morphology remains null in canonical data; metadata retains named contexts without fabricating values.',
  'Study-level figures do not assert exact recipe, physical specimen or same-batch identity.',
  'Editorial gallery category does not turn an author model or reference into an experimental measurement.'],
 'read_only_input_count':len(inputs),'public_original_asset_count':len(asset_manifest)}
for name,value in [('validation-report.json',report),('original-assets-manifest.json',asset_manifest),('figure-classification-review.json',classification_rows)]:
 (P/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps(report,indent=2,ensure_ascii=False))
assert not findings,findings
