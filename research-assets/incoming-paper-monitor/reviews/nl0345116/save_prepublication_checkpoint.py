from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audits=['canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','crystal-source-audit.json','bindings-source-audit.json','visual-source-audit.json']
runtime=['build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json','public-review-proposal/proposal-validation.json','training-compatibility-check.json']
for f in audits+runtime:assert read(B/f)['status'].startswith('passed'),f
records=[read(p)for p in (B/'canonical-drafts').glob('*.json')];ops=sum(len(r['operations'])for r in records);meas=sum(len(r['measurements'])for r in records)
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/f)for f in ['canonical-record-manifest.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':f'{len(records)} records, four synthesis routes, {ops} operations and {meas} measurement entries; complete supplied main-paper source coverage mapped to reader.'}
m['audit']={'status':'complete','evidence':[str(B/f)for f in audits]+[str(B/'source-audit.json')],'note':'Independent canonical, reader, 13 original-asset, molecular, crystal, binding and apparatus audits passed. Unknown SI, missing parameters, conflicting ratios and model/measurement boundaries explicit.'}
m['integrate']={'status':'complete','evidence':[str(B/f)for f in runtime]+[str(B/'integration-manifest.json')],'note':'Existing MatterSyn atlas includes PbSe hub, four equal routes, chemicals, stage-specific protocols, original figures and separately labeled ideal crystal downloads. Actual build/runtime and representative browser checks passed.'}
write(B/'milestones.json',m);c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),canonical_records=len(records),operations=ops,measurement_entries=meas,current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Publish validated PbSe contribution on the existing Site, check source fingerprint and close this supplied-main review.');write(B/'checkpoint.json',c)
print('Read/extract/audit/integrate complete; publication pending.')
