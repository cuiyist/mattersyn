from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, re, hashlib
P=Path(__file__).resolve().parent
S=P.parents[2]/'recipe-atlas'; D=S/'dist'
bound={}
def read(rel):
 p=D/rel;bound[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text('utf8'))
idx=read('data/materials-index.json');pres=read('data/reader-presentation.json')
contexts=read('assets/chemical-registry/solution-components.json')['contexts']
refs=read('assets/crystal-references/registry.json')['entries']
reviews={p.stem for p in (D/'data/paper-reviews').glob('*.json')}
normal=lambda v:re.sub('[^a-z0-9]','',str(v or '').lower())
routes={};hubs=[];sources=[];figures=[];stock_rows=[];products=[];hidden_facts=[]
for h in idx['materials']:
 shard=read('data/materials/'+h['id']+'.json')
 rows=[x for x in shard['records'] if x.get('is_synthesis_route') and x.get('collection')=='reviewed_literature']
 hubs.append({'id':h['id'],'url':h['url'],'routes':[x['record_id'] for x in rows], 'presentation_record_ids':pres['materials'].get(h['id'],{}).get('record_ids',[]), 'missing_presentation':[x['record_id'] for x in rows if x['record_id'] not in pres['records']], 'page_exists':(D/h['url'].split('?')[0]).exists()})
 routes.update({x['record_id']:x for x in rows})
for rid in routes:
 r=read('data/records/'+rid+'.json');p=pres['records'].get(rid,{})
 for src in r['sources']:
  if src['id'] not in reviews:sources.append({'record_id':rid,'source_id':src['id'],'generated_review_url':'paper-review.html?id='+src['id'],'available_presentation_target':p.get('data_links',{}).get('full_review')})
 for f in p.get('figures',[]):
  asset=f.get('public_asset') or f.get('asset')
  if not asset or f.get('reader_url')!=('paper-review.html?id='+str(f.get('source_id') or r['lineage']['source_group'])):
   figures.append({'record_id':rid,'figure_id':f['id'],'asset':asset,'reader_url':f.get('reader_url'),'hardcoded_reader_exists':(f.get('source_id') or r['lineage']['source_group']) in reviews,'category':f['category'],'summary':f['summary']})
  if asset:bound[str(D/asset)]=hashlib.sha256((D/asset).read_bytes()).hexdigest()
 cc=[c for c in contexts if c['record_id']==rid];used=[]
 for stock in r['stocks']:
  context=next((c for c in cc if c['id']==stock['id'] or normal(c['label'])==normal(stock['name'])),None)
  if context:used.append(context)
  stock_rows.append({'record_id':rid,'stock_id':stock['id'],'name':stock['name'],'matched_context_id':context['id'] if context else None,'candidate_ids':[c['id'] for c in cc if c['id'].endswith('-'+stock['id'])]})
 for f in p.get('allProductFacts',p.get('productFacts',[])):
  if f['kind']=='composition' and f['value']!=r['material']['formula']:
   products.append({'record_id':rid,'sample_id':f['sample_id'],'selected_composition':f['value'],'hardcoded_heading':r['material']['formula'],'scope':f.get('scope')})
 grouped={}
 for f in p.get('allProductFacts',p.get('productFacts',[])):
  key=(f.get('record_id',rid),f.get('sample_id','context'));grouped.setdefault(key,[]).append(f)
 for key,ff in grouped.items():
  if len(ff)>5:hidden_facts.append({'record_id':rid,'sample_key':key,'count':len(ff),'hidden':[{'kind':x['kind'],'label':x['label'],'value':x['value']} for x in ff[5:]]})
source_groups=Counter(x['source_id'] for x in sources)
unmatched=[s for s in stock_rows if not s['matched_context_id']]
string_overrides=[{'record_id':c['record_id'],'context_id':c['id'],'material_id':x.get('material_id'),'limitations':x['viewOverrides']['limitations']} for c in contexts if c['record_id'] in routes for x in c.get('components',[]) if isinstance(x.get('viewOverrides',{}).get('limitations'),str)]
for rel in ['reader-app.mjs','reader-structures.mjs','protocol-references.mjs','reader-utils.mjs','quantity-value.mjs','chemical-viewer.mjs','protocol-visuals.mjs','source-evidence.mjs','material.html','cdse.html','murray-1993-method-1.html','murray-1993-method-2.html','alivisatos-2000.html']:
 bound[str(D/rel)]=hashlib.sha256((D/rel).read_bytes()).hexdigest()
out={'at':datetime.now(timezone.utc).isoformat(),'summary':{'hubs':len(hubs),'routes':len(routes),'empty_hubs':sum(not x['routes'] for x in hubs),'hubs_missing_presentation':sum(bool(x['missing_presentation']) for x in hubs),'broken_generated_source_links':len(sources),'broken_source_groups':dict(source_groups),'stock_count':len(stock_rows),'unmatched_stocks':len(unmatched),'unmatched_with_explicit_suffix_candidate':sum(bool(x['candidate_ids']) for x in unmatched),'string_limitations_context_components':len(string_overrides),'sample_composition_differs_from_heading':len(products),'specimen_groups_with_more_than_five_facts':len(hidden_facts)},'hubs':hubs,'broken_source_links':sources,'figure_handling':figures,'stock_matches':stock_rows,'string_override_examples':string_overrides,'wrong_product_heading_candidates':products,'hidden_product_facts':hidden_facts,'bound_files':bound}
(P/'static-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(out['summary'],ensure_ascii=False))
print('Examples',json.dumps({'unmatched_stocks':unmatched[:8],'product_headings':products[:6],'figures':figures[:3]},ensure_ascii=False))
