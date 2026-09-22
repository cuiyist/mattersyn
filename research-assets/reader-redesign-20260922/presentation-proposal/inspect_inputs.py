from pathlib import Path
import json,collections
S=Path('[local path redacted]');D=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
hubs=[read(p) for p in (S/'dist/data/materials').glob('*.json')]
ids=sorted({i for h in hubs for i in h['record_ids']});records={i:read(S/'data/records'/f'{i}.json') for i in ids}
reviews={p.stem:read(p) for p in (S/'data/paper-reviews').glob('*.json')}
out={'hub_count':len(hubs),'route_records':len(ids),'sources':collections.Counter(r.get('lineage',{}).get('source_group') for r in records.values()),'review_count':len(reviews),'review_shapes':{},'product_field_shapes':collections.Counter(),'figure_shapes':collections.Counter(),'hub_rows':[]}
for r in records.values():
 for p in r.get('products',[]):
  for k,v in p.items():out['product_field_shapes'][k+':'+type(v).__name__]+=1
for k,r in reviews.items():
 out['review_shapes'][k]={'figures':len(r.get('figures',[])),'sections':[s.get('id') for s in r.get('reader_sections',[])],'intuition_type':type(r.get('chemical_intuition')).__name__,'routes':r.get('route_evidence_contexts',{}),'figure_labels':[f.get('label',f.get('id')) for f in r.get('figures',[])]}
 for f in r.get('figures',[]):out['figure_shapes'][','.join(sorted(f))]+=1
for h in hubs:out['hub_rows'].append({'id':h['id'],'formula':h['formula'],'component_only':h['component_only'],'routes':h['record_ids']})
(D/'input-inventory.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n','utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['review_shapes','hub_rows']},ensure_ascii=False,indent=2))
for i in [ids[0],'sasongko-2025-hot-injection','murray-1993-cdse','banerjee-2003-growth']:
 if i in records:
  r=records[i];print(i,json.dumps({'keys':list(r),'products':r.get('products',[])[:1],'interpretations':r.get('interpretations'),'intuition':r.get('chemical_intuition')},ensure_ascii=False)[:2400])
for n in ['cdse','csPbBr3','peng1998','sasongko2025','tessier2015']:
 if n in reviews:
  r=reviews[n];print('REVIEW',n,json.dumps({'chemical_intuition':r.get('chemical_intuition'),'firstfig':r.get('figures',[None])[0]},ensure_ascii=False)[:2800])
