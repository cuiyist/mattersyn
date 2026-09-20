from pathlib import Path
import json
J=Path(__file__).resolve().parent
rs=[json.loads(p.read_text('utf8'))for p in (J/'site-integration-proposal/v1/records').glob('*.json')]
print(json.dumps([{'id':r['record_id'],'ops':[{'id':o['id'],'type':o.get('action',o.get('name'))}for o in r['operations']]}for r in rs if r['operations']],indent=2))

