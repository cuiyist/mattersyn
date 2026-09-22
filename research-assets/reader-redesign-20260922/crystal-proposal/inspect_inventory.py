from pathlib import Path
import json
ROOT=Path(__file__).parent
SITE=ROOT.parents[2]/'recipe-atlas'/'dist'
if not SITE.exists(): SITE=Path(r'[local path redacted]')
for p in sorted((SITE/'data/materials').glob('*.json')):
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 print(d['id'],d['formula'],[(r['record_id'],r.get('is_synthesis_route'),r.get('page_url')) for r in d.get('records',[])])
