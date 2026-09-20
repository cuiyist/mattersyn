from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
checks=[
 ('reviewed_route_loaded','Banerjee growth record opens with source main9+SI1 scope, all17 stages and source-reviewed status.'),
 ('heating_stage','Click07:320°C,argon,vigorous stirring; duration and pressure unspecified.'),
 ('injection_stage','Click09:Te solution in TOP at300°C; unreported volume/duration and no invented Te species or continuing gas.'),
 ('wash_stage','Click16:retained nanotube composite versus removed free CdTe;0.2µm membrane and qualitative toluene wash.'),
 ('apparatus_visual','Viewed actual browser screenshot of wash scene and adjacent conditions; distinct retained/filtrate particle depiction.'),
 ('product_modal','New composite identity opens; plus control changes image transform to scale1.2; source atom-coordinate limitation visible.'),
 ('all_figures','Figure scope control changes source gallery from3associated to9of9main/SIfigures.'),
 ('si_original','SI infrared original opens and renders in enlarged viewer; explicitly oxidized-MWNTprecursor.'),
 ('xps_xrd_original','Figure5XPS/XRD opens with its original figure title and caption.'),
 ('reader_scope','Linked complete paper reader reports10pages,9originalfigures and matchedSI.'),
 ('reader_search','Search infrared shows5of143sourceitems; SI and instrument/method evidence accessible.'),
 ('periodic_discovery','Cd+Teselection returns CdTecomponent and CdTe/MWNTcomposite; card opens actual composite materialhub.'),
 ('hub_content','Loaded CdTe/MWNT title,illustrated route selector,complete precursorcards,source2003 and reviewed main+SI contribution.'),
 ('molecular_view','TDPAinteractive reference renders actual3Dconformer with highlighted phosphonicacid group; highlight control toggles.'),
 ('rendering_errors','1280×720viewport; documentWidth1265; no broken loaded images and no captured browser console errors.')
]
files=['dist/banerjee2003-protocol.mjs','dist/protocol-visuals.mjs','dist/crystal-viewer.mjs','dist/data/paper-reviews/banerjee2003.json','dist/data/materials/cdte-mwnt-0279c6.json','dist/data/dataset-manifest.json']
result={'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'method':'Actual Codex in-app browser through CUA; local preview127.0.0.1:5187,agent tab19.','scope':'Representative changed controls,source-linked content,figure/molecule modals and periodic-table discovery. Static/integrated tests cover the remaining records; mobile and every possible interaction were not tested.','checks':[{'name':n,'passed':True,'observed':d} for n,d in checks],'artifact_sha256':{f:hashlib.sha256((S/f).read_bytes()).hexdigest() for f in files}}
(B/'browser-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Saved15actual browser observations; publication pending.')
