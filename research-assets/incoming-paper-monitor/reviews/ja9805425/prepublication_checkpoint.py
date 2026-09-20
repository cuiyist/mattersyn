from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
stages=read(B/'milestones.json')
evidence={'extract':['canonical-records-audit.json'],'audit':['source-audit.json','canonical-records-audit.json','reader-source-audit.json','crop-source-audit.json','visual-source-audit.json','reader-assets/canonical-to-reader-audit.json','reader-assets/final-presentation-check.json'],'integrate':['build-validation.json','browser-qa.json','reader-assets/reader-runtime-check.json']}
for stage,files in evidence.items():
 for f in files:assert (B/f).is_file(),f
 stages[stage]={'status':'complete','evidence':[str(B/f)for f in files],'note':'All six main/SI PDF pages accounted for in audited canonical records and reader; supplied source limitations remain explicit.'}
write(B/'milestones.json',stages)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in stages.items()],next_action='Publish audited Peng1998 InAs and CdSe contributions to the existing MatterSyn Site; final unchanged-source check and closure remain.')
write(B/'checkpoint.json',c)
print('Saved prepublication checkpoint; publish remains pending.')
