from pathlib import Path
import json
B=Path(__file__).resolve().parents[1]
for p in sorted((B/'canonical-drafts').glob('*.json')):
 d=json.loads(p.read_text(encoding='utf8'));print('\n'+p.stem)
 print('ops:',[(o['id'],list(o['parameters'])) for o in d['operations']])
 print('measurements:',[(m['id'],m['property'],m['sample_id']) for m in d['measurements']])
 print('materials:',[(m['id'],list(m['quantities'])) for m in d['materials']])
 print('stocks:',[(s['id'],list(s['concentrations'])) for s in d['stocks']])
