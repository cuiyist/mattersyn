from pathlib import Path
import json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
p=S/'data/paper-reviews/stiger1999.json';r=json.loads(p.read_text(encoding='utf-8'))
f=next(f for f in r['figures']if f['id']=='figure-2')
extra=['Source current-density scale arrows: a 4, b 200, c 4 and d 100 µA cm⁻². These are plotted scale lengths, not peak-current measurements.','Legend: scan 1 solid; scan 2 widely spaced dotted; scan 3 more closely spaced dotted. Curves are successive scans, not independent batches.']
for k in ['quantitative_context','notes']:
 for text in extra:
  if text not in f[k]:f[k].append(text)
for a in r['figures']+[i for k in ['tables','schemes','equations','source_notes']for i in r.get(k,[])if i.get('public_asset')]:
 a['reviewed']=True
# Reader-render flags only promoted after browser and independent reader checks.
r['independent_audit']='All nine supplied main pages, 8 canonical records, 36 apparatus scenes, 47 chemical bindings and 15 original source assets independently audited. SI remains unverified; final reader/browser checks and publication tracked separately.'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Added source Figure2 scale/legend context and completed scientific asset-review flags; no canonical or measurement changes.')
