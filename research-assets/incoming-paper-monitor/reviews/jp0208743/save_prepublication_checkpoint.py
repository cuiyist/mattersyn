from pathlib import Path
from datetime import datetime, timezone
import json
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audits=['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json']
for f in audits[1:]+['public-review-proposal/proposal-validation.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']:
 assert read(B/f)['status'].startswith('passed'),f
inv=read(S/'data/inventory-summary.json'); row=next(x for x in inv['per_paper']if x['source_group']=='dantas2002')
records=[read(S/'data/records'/(k+'.json'))for k in row['record_ids']]
assert len(records)==16 and sum(len(r['operations'])for r in records)==48 and sum(len(r['measurements'])for r in records)==110
m=read(B/'milestones.json')
m['extract']={'status':'complete','evidence':[str(B/f)for f in ['canonical-record-manifest.json','public-review-proposal/proposal-validation.json','reader-assets/crop-manifest.json']],'note':'Six annealing variants, eight supporting procedures and two context observations retain 48 operations and 110 measurement entries. All 147 source units are mapped to the reader. Matching SI unverified.'}
m['audit']={'status':'complete','evidence':[str(B/f)for f in audits],'note':'Independent source, canonical, reader, eleven original-asset, molecular, binding and all 48 apparatus audits passed. Unknown sulfur reagent and glass proportions, literal vessel wording and source size/radius/height distinctions remain explicit.'}
m['integrate']={'status':'complete','evidence':[str(B/f)for f in ['integration-manifest.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']],'note':f"Same existing MatterSyn atlas: {inv['summary']['canonical_records']} records. Source-specific materials and six equal route cards integrated with periodic discovery, PbS component collection and complete original-figure reader. Build, independent integrated/runtime checks and representative browser review passed."}
for stage in m.values():
 for f in stage['evidence']: assert Path(f).exists(),f
write(B/'milestones.json',m)
c=read(B/'checkpoint.json');c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),website_published=False,current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Publish validated source on the existing Site; verify unchanged source bundle, close supplied-main scope and save memory/skills.');write(B/'checkpoint.json',c)
print('Read, extraction, audit and integration complete; native publication pending.')
