from pathlib import Path
import json
G=Path(__file__).resolve().parent.parent
for p in sorted((G/'canonical-proposal/v1').glob('ghosh-*.json')):
 r=json.loads(p.read_text(encoding='utf-8'));print('\n'+r['record_id'])
 for i,o in enumerate(r['operations']):print(i,o['id'],'PARAMETERS',json.dumps({k:{a:v for a,v in q.items() if a in ['value','minimum','maximum','unit','raw_text','approximate'] and v is not None} for k,q in o['parameters'].items()},ensure_ascii=False))
