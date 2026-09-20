from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
p={'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'browser':'Codex in-app browser, background local tab18','origin':'http://127.0.0.1:5187','scope':'Actual representative browser interactions and screenshots, plus separately recorded exhaustive private source/runtime audits. No all-device or all-control browser-coverage claim.','checks':[
'Material hub loads nominal formula, material name and six equal synthesis-route cards in existing atlas.',
'Switched illustrated method to the 800 °C route; main precursor quantity is visible.',
'Hydrothermal stage button updates source-specific autoclave diagram and adjacent180 °C/1 h/missing-pressure conditions; screenshot inspected.',
'Anneal stage updates furnace diagram and800 °C/5 h, with atmosphere explicitly unreported.',
'Verified-water modal opens; zoom and reset controls exercised; actual molecule screenshot inspected.',
'All-original-figures filter exposes all ten source figures on material page.',
'Complete-review link loads source reader; searching mass yields13 of115 evidence items.',
'Original Figure2 opens in enlarged dialog; both before/after TEM panels and300/100nm scale bars remain readable.',
'Periodic-table La+Mo+Er filter produces exactly this reviewed material hub.',
'No application console errors captured during these interactions.'
],'built_files':{str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [S/'dist/yi2002-protocol.mjs',S/'dist/data/paper-reviews/yi2002.json',S/'dist/data/materials/la2-moo4-3-yb-er-541bed.json']}}
(B/'browser-qa.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Saved observed browser checks.')
