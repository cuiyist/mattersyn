from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
checks=[
('source_route','Co-doped route renders reviewed scope, hydrated precursors, inherited stock values and six synthesis/workup stages.'),
('addition_stage','Stage 03 shows dropwise hydroxide feed, stirring, approximate 2 mL/min and qualitative room temperature; unknown duration and pressure remain explicit.'),
('heating_stage','TOPO stage 07 shows heater schematic, 180 °C, at least 30 minutes and unreported atmosphere; actual screenshot inspected.'),
('chemical_viewer','Dodecylamine opens a computed 3D molecule; functional-group toggle and zoom controls respond; primary amine highlighted and source limitation visible.'),
('crystal_viewer','Unit cell and 2 × 2 × 2 buttons visibly switch between four atoms and the extended ZnO host reference; screenshots inspected. CIF link and independent-reference limitation visible.'),
('figure_scope','Co route shows 15 contextual figures/tables; All option changes count to 19 of 19.'),
('original_main_diffraction','Figure 5 opens TEM, size histogram and electron-diffraction original; zoom-out changes image width to 64 percent and exposes diffraction panel.'),
('periodic_table','Zn plus O shows both new doped-material cards; adding Co selects only ZnO:Co. Open material navigates to its correct populated hub.'),
('material_hub','Co hub renders academic sections, illustrated synthesis selector, full precursor cards and source-backed method.'),
('ni_material_scope','Ni hub uses nickel perchlorate hexahydrate and shows 8 of 19 selected original figures/tables, preserving shared panel labels.'),
('si_diffraction','Ni hub Figure S3 opens the actual TEM and electron-diffraction image together with its original caption; screenshot inspected.'),
('paper_reader','Full source reader reports 18 pages, 17 original figures, two tables and matched SI; search for electron diffraction returns 2 of 184 source items and clearing restores the list.'),
('console','No browser console errors observed through representative changed routes and controls.')]
v={'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'method':'Actual Codex in-app browser through CUA, local preview 127.0.0.1:5187, temporary tab20.','scope':'Representative changed controls and same-site discovery. Independent runtime and integration checks cover all records and original assets. Mobile layouts and every possible interaction were not tested.','checks':[{'name':n,'passed':True,'observed':d}for n,d in checks],'artifact_sha256':{str(p.relative_to(S)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()for p in [S/'dist/material-guide.mjs',S/'dist/schwartz2003-protocol.mjs',S/'dist/data/paper-reviews/schwartz2003.json',S/'dist/data/materials-index.json']}}
(B/'browser-qa.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Saved actual browser evidence:',len(checks),'representative checks.')
