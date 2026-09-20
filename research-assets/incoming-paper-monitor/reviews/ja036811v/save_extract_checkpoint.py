from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
records=[read(p)for p in(B/'canonical-drafts').glob('*.json')];assert len(records)==30
assert read(B/'canonical-records-audit.json')['status'].startswith('passed')
ms=read(B/'milestones.json');ms['extract']={'status':'complete','evidence':[str(B/f)for f in['canonical-record-manifest.json','source-audit.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':'30 records:3 synthesis routes,20 procedures,7 contextual observations,95 operations and277 measurement rows. Original figures/tables/scheme/equations and reader coverage prepared; independent reader/binding/apparatus final checks underway.'}
for f in ms['extract']['evidence']:assert Path(f).exists(),f
ms['audit']={'status':'partial','evidence':[str(B/f)for f in['source-audit.json','canonical-records-audit.json','molecular-source-audit.json']],'note':'Full-source, all30canonical records and12newchemicalreferences passed independent audits. Final reader, binding/host-reference and apparatus review pending.'};write(B/'milestones.json',ms)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),canonical_records=30,operations=95,measurement_entries=277,source_audit_units=read(B/'source-audit.json')['unit_count'],current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in ms.items()],next_action='Finish remaining independent gates, integrate reviewed records into existing MatterSyn, run browser checks, publish and verify unchanged source bundle.');write(B/'checkpoint.json',c)
print('Saved extraction and partial-audit checkpoint; no publication claimed.')
