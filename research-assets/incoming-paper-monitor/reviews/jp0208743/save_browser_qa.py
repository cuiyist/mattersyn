from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[
 'PbS/glass hub displays six equal source-reviewed annealing-variant cards and complete shared five-stage preparation on each illustrated route.',
 'AFM1 melt stage shows source-specific furnace/crucible,1400 C and2 h with inherited provenance, unknown atmosphere/pressure and unresolved vessel wording. Screenshot inspected; no layout clipping observed.',
 'Switching to SG4 and its final stage updates the apparatus and conditions to600 C for12 h, optical specimen and whole PbS/glass product.',
 'All-figures scope exposes all seven originals, preserving author-model and AFM specimen distinctions. Original AFM figure enlargement opened and visually inspected; zoom/reset exercised.',
 'Sodium-carbonate precursor viewer opens with ionic connectivity and carbonate highlight. Its2D representation and formula-layout scope are explicit; no3D atomic model implied.',
 'Complete reader shows5 reviewed main pages, SI-unverified scope and101 source items. Searching0.86 returns2 relevant items.',
 'Selecting Pb and S in periodic table reveals PbS/glass and PbS component collections. PbS page explicitly labels heterostructures and retains all six composite routes without standalone synthesis claim.',
 'No browser console warnings or errors observed during representative local QA.'
]
r={'status':'passed','at':datetime.now(timezone.utc).isoformat(),'browser':'Codex in-app browser; temporary local tab17 closed after QA','origin':'http://127.0.0.1:5187','checks':checks,'limitations':['Representative desktop interactions; no mobile QA or interactive inspection of every asset claimed. All eleven original crops and48 apparatus scenes separately audited.','Matching SI not located or verified.'],'module_hashes':{f:sha(S/'dist'/f)for f in ['dantas2002-protocol.mjs','protocol-visuals.mjs','material-hub.mjs','crystal-viewer.mjs']},'reader_sha256':sha(S/'data/paper-reviews/dantas2002.json')}
(B/'browser-qa.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Representative browser QA saved.')
