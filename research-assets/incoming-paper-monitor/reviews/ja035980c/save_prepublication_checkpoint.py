from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audits=['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json']
for f in audits[1:]+['public-review-proposal/proposal-validation.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']:
 assert read(B/f)['status'].startswith('passed'),f
inv=read(S/'data/inventory-summary.json');row=next(x for x in inv['per_paper']if x['source_group']=='banerjee2003');records=[read(S/'data/records'/(k+'.json'))for k in row['record_ids']]
assert len(records)==14 and sum(len(r['operations'])for r in records)==39 and sum(len(r['measurements'])for r in records)==97
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/f)for f in ['canonical-record-manifest.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':'One synthesis route, nine supporting procedures and four contextual observations retain 39 operations and 97 measurement entries. All 176 source units mapped to the reader. All nine main pages and matched one-page SI reviewed.'}
m['audit']={'status':'complete','evidence':[str(B/f)for f in audits],'note':'Independent source, canonical, reader, fifteen original assets, molecular, binding and 39 apparatus-scene audits passed. Missing doses and Te stock identity, separate particle populations, precursor-only SI infrared scope and the printed EDS unit discrepancy remain explicit.'}
m['integrate']={'status':'complete','evidence':[str(B/f)for f in ['integration-manifest.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']],'note':f"Integrated into the same existing MatterSyn atlas with {inv['summary']['canonical_records']} canonical records. A new CdTe–MWNT material hub, explicit component-only CdTe and MWNT discovery, the reviewed synthesis route and all original figures. Build, independent runtime checks and representative browser inspection passed."}
for stage in m.values():
 for f in stage['evidence']:assert Path(f).exists(),f
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),website_published=False,current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Publish validated source on the existing Site, verify unchanged source bundle, close supplied main and matched SI scope and save memory/skills.');write(B/'checkpoint.json',c)
print('Read/extract/audit/integrate complete; publication pending.')
