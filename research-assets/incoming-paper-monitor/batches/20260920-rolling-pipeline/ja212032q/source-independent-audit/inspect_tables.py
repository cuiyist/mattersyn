from pathlib import Path
import json
G=Path(__file__).resolve().parent.parent
for t in json.loads((G/'source-tables.json').read_text(encoding='utf-8'))['tables']:
 print(t['id'],t['columns'])
 for r in t['rows']:
  print(r['row_label'],r['sample_id'],[(c.get('raw_text'),c.get('value'),c.get('unit'),c.get('status'),c.get('asset_id')) for c in r['cells']])
 print('metadata',json.dumps({k:v for k,v in t.items() if k not in ['rows','columns']},ensure_ascii=False))
