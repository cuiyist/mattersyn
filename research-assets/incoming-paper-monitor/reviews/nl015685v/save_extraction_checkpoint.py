from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ms=read(B/'milestones.json');ms['extract']={'status':'complete','evidence':[str(B/f)for f in ['canonical-record-manifest.json','records-validation.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':'12 records,36 operations,98 measurements,130 reader items,173 source units,157 typed reader facts and10 original crops extracted; explicit missingness and conflicts retained.'};ms['audit']={'status':'partial','evidence':[str(B/f)for f in ['source-audit.json','canonical-records-audit.json','molecular-source-audit.json','visual-source-audit.json']],'note':'Full source, canonical, molecular and apparatus audits passed; final reader/source-link and binding checks finishing.'}
for x in ms.values():
 for f in x['evidence']:assert Path(f).exists(),f
write(B/'milestones.json',ms);c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in ms.items()],next_action='Collect passed final reader/binding audits and exact hashes, run staged root integrate_review.py once, run_build.py, integrated/browser checks, publish existing Site, final source fingerprint and queue closure.');write(B/'checkpoint.json',c)
print('Extraction complete; final independent audit gates and publication remain separate.')
