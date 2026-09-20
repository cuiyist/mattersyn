from pathlib import Path
import json
S=Path('[local path redacted]')
for rel in ['dist/data/materials-index.json','dist/data/paper-review-index.json','dist/data/inventory-summary.json','dist/data/dataset-manifest.json','data/measurement-display.json']:
 d=json.loads((S/rel).read_text('utf8'));print(rel,'keys',list(d)[:30])
 if rel.endswith('materials-index.json'):
  print(json.dumps(d,ensure_ascii=False)[:1000])
  for k,v in d.items():
   if isinstance(v,list):
    for x in v:
     if isinstance(x,dict) and ('FAPbI3' in json.dumps(x) or 'sasongko2025' in json.dumps(x)):print('match',json.dumps(x,ensure_ascii=False))
 if rel.endswith('inventory-summary.json'):print('summary',json.dumps({k:v for k,v in d.items() if k not in ['provenance','materials']},ensure_ascii=False)[:3500])
for p in (S/'dist/data/materials').glob('*fapbi*'):
 d=json.loads(p.read_text('utf8'));print('material',str(p),list(d));print(json.dumps(d,ensure_ascii=False)[:6000])
for p in (S/'dist/data/papers').glob('*'):
 d=json.loads(p.read_text('utf8'))
 if d.get('doi')=='10.1021/acs.jpcc.5c05144':print('source',str(p),json.dumps(d,ensure_ascii=False)[:6500])
