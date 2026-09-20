from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
checks=[
 'CdS/SiO2 hub presents two equal method cards; switching CTAB and copolymer routes updates the illustrated guide.',
 'Gas-treatment illustration shows the retained film and symbolic P(H2S)=P(atm) endpoint; unreported numerical pressure and duration remain missing.',
 'CTAB repeat stage displays nine total cycles. Copolymer six-cycle association remains explicitly inferred in the evidence.',
 'All-figures scope exposes all four original figures. Figure 3 enlargement shows original HRTEM and image Fourier power, with legible original scale bars.',
 'Silica-host route displays 60 C for 1 h aging, 3000 rpm coating, and 450 C air calcination with duration and ramp unreported. Calcination layout visually inspected.',
 'TEOS C8H20O4Si computed molecular reference opens. Zoom, mouse rotation and functional-group highlight toggle exercised and visually inspected.',
 'Complete source reader shows 130 items and main-only/SI-unverified scope. Searching 640 returns three items; unresolved Figure 4 caption/body conflict remains exposed.',
 'Selecting Cd and Si in the periodic table exposes the CdS/SiO2 material. Existing CdS collection contains both Besson composite routes.',
 'No browser console warnings or errors observed during representative local QA.'
]
write(B/'browser-qa.json',{'status':'passed','at':datetime.now(timezone.utc).isoformat(),'browser':'Codex in-app browser, temporary local tab 16 (closed after QA)','origin':'http://127.0.0.1:5187','checks':checks,'limitations':['Representative desktop interactions; no mobile QA or interactive inspection of every asset claimed. All ten source crops and 36 apparatus scenes were separately audited.','Matching SI not located or verified.'],'module_hashes':{f:sha(S/'dist'/f) for f in ['besson2002-protocol.mjs','protocol-visuals.mjs','material-hub.mjs','crystal-viewer.mjs']},'reader_sha256':sha(S/'data/paper-reviews/besson2002.json')})
for f in ['canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json','reader-assets/integrated-presentation-audit.json']:
 assert read(B/f)['status'].startswith('passed'), f
m=read(B/'milestones.json')
m['audit']={'status':'complete','evidence':[str(B/f)for f in ['source-audit.json','canonical-records-audit.json','reader-source-audit.json','molecular-source-audit.json','bindings-source-audit.json','visual-source-audit.json']],'note':'Independent source, canonical, reader, ten original-crop, molecular, binding and all 36 apparatus audits passed. Supplied-main-only/SI-unverified scope retained.'}
m['integrate']={'status':'complete','evidence':[str(B/f)for f in ['integration-manifest.json','build-validation.json','browser-qa.json','reader-assets/integrated-presentation-audit.json','reader-assets/reader-runtime-check.json']],'note':'Same existing MatterSyn atlas: 321 records,29 hubs,72 routes. Build passed;2869 independent integrated and1461 mounted-runtime checks passed. New material discoverable from periodic table and existing CdS collection.'}
for stage in m.values():
 for f in stage['evidence']: assert Path(f).exists(),f
write(B/'milestones.json',m)
c=read(B/'checkpoint.json'); c.update(checkpoint_at=datetime.now(timezone.utc).isoformat(),website_published=False,current_work_items=[{'label':k.capitalize(),'status':v['status'],'scope':v['note']}for k,v in m.items()],next_action='Publish validated source on the same Site, verify unchanged source bundle, close supplied-main scope and save memory/skills.');write(B/'checkpoint.json',c)
print('Read, extraction, audit and integration complete; native publication pending.')
