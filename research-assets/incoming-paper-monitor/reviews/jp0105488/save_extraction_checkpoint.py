from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/'canonical-record-manifest.json'),str(B/'source-audit.json'),str(B/'public-review-proposal/proposal-validation.json')],'note':'Eleven supplied main pages extracted into28records,82operations and186measurements, with139readeritems covering251sourceunits,329typedfacts and17originalassets. Formatting and final audits are being reconciled; announced SI remains unavailable.'}
m['audit']={'status':'partial','evidence':[str(B/'molecular-source-audit.json'),str(B/'crop-source-audit.json')],'note':'Independent source and molecular review completed; canonical/reader/binding final hashes and all82source-specific apparatus scenes under final independent audit.'}
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Finish independent audits, integrate into existing MatterSyn, validate reader and method interactions, publish and fingerprint before closure.');write(B/'checkpoint.json',c)
print('Extraction checkpoint saved; no publication claimed')
