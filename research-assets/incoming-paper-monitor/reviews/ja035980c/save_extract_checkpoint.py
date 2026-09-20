from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/x) for x in ['canonical-record-manifest.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':'All nine main pages and matched SI extracted into 14 canonical records, 39 operations, 97 measurements and a 143-item reader covering 176 source units. Fifteen original crops retained.'}
m['audit']={'status':'partial','evidence':[str(B/x) for x in ['source-audit.json','canonical-records-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json','training-compatibility-check.json']],'note':'Canonical, chemical, binding, apparatus and training exporter audits passed. Independent reader/figure audit pending; no source promotion yet.'}
for x in m.values():
 for p in x['evidence']:assert Path(p).exists(),p
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']} for k,v in m.items()],next_action='Complete independent reader audit; integrate and check the same MatterSyn Site, then publish and verify source bundle.');write(B/'checkpoint.json',c)
print('Extraction complete; independent reader audit remains active.')
