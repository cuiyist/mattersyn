from pathlib import Path
from datetime import datetime,timezone
import json
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audits=['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json']
for f in audits[1:]+['public-review-proposal/proposal-validation.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']:assert read(B/f)['status'].startswith('passed'),f
inv=read(S/'data/inventory-summary.json');row=next(x for x in inv['per_paper']if x['source_group']=='schwartz2003');records=[read(S/'data/records'/(k+'.json'))for k in row['record_ids']]
assert len(records)==30 and row['synthesis_route_variant_count']==3
ops=sum(len(r['operations'])for r in records);meas=sum(len(r['measurements'])for r in records);units=read(B/'source-audit.json')['unit_count'];assets=len(read(B/'reader-assets/crop-manifest.json')['assets'])
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/f)for f in ['canonical-record-manifest.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':f'30 records distinguish3 synthesis routes, supporting procedures and contextual analyses; {ops} operations and{meas} measurement entries. All{units} audited source units mapped to the reader. All14 main+4 matched SI pages reviewed.'}
m['audit']={'status':'complete','evidence':[str(B/f)for f in audits],'note':f'Independent source, canonical, reader, {assets} original assets, chemical identity, binding, host-crystal reference and{ops} apparatus-scene audits passed. Source discrepancies, variable dopant content and model/measurement boundaries remain explicit.'}
m['integrate']={'status':'complete','evidence':[str(B/f)for f in ['integration-manifest.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']],'note':f"Same existing MatterSyn atlas now has{inv['summary']['canonical_records']} canonical records. ZnO and new Co/Ni-doped ZnO hubs expose reviewed recipes, chemical structures, source-specific protocols, original characterization and independent undoped-host crystal reference. Build, independent runtime and representative browser checks passed."}
for st in m.values():
 for f in st['evidence']:assert Path(f).exists(),f
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),website_published=False,current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Publish validated contribution on the existing Site, verify unchanged source bundle, close supplied main/SI scope and save memory/skills.');write(B/'checkpoint.json',c)
print('Read/extract/audit/integrate complete; publication pending.')
