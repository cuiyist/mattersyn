"""Record actual root CUA observations and a bounded reader-display overlay."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json
A=Path(__file__).resolve().parent; O=A/'site-integration-proposal'; S=A.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'browser-validation.json').exists()
bindings=read(A/'visuals/apparatus/canonical-bindings.json')['bindings']
assert len(bindings)==58 and len({b['record_id'] for b in bindings})==19
receipt={'status':'passed','author':'/root','at':datetime.now(timezone.utc).isoformat(),
 'origin':'http://127.0.0.1:5197','scope':'Actual CUA browser interactions with the integrated local Site, separate from scientific audits.',
 'stage_count':58,'procedure_records':19,'all_stage_selectors_tested':True,
 'stages':[{'record_id':b['record_id'],'operation_id':b['operation_id'],'scene_label_present_after_selection':True} for b in bindings],
 'chemical_check':'1-Octadecene conformer rendered; group checkbox, zoom, reset and mouse drag exercised. Stock component selector switched to 1-octadecene solvent. Reference/conformer qualifications remain visible.',
 'product_check':'Structural-results selector exposes six separate source contexts. Selected 250 degC TEM context and enlarged its symbolic card;2.6 +/-0.5nm,315particles,undefined uncertainty statistic and no exact aliquot join remain explicit. Lazy product image loaded after entering viewport.',
 'figure_check':'Original Figure3 enlargement visually inspected: absorption/time traces, XRD and TEM panels/scales readable. Original gallery images loaded. Full crop scientific review is the separate source audit.',
 'discovery_check':'Periodic table In+P filter exposes the existing InP hub. Hub retains Tessier2015 and four Friedfeld routes with equal cards and selector entries. Selecting Friedfeld loads its own chemicals and eight stages.',
 'concentration_check':'Varied-concentration injection explicitly excludes representative20mg/0.00121mmol charge and distinguishes inherited1mLODE from reaction concentration.',
 'desktop':{'viewport':{'width':1280,'height':900},'client_width':1265,'scroll_width':1265,'hub_and_heating_scene_visually_inspected':True},
 'mobile':{'viewport':{'width':390,'height':844},'client_width':375,'scroll_width':375,'injection_enlargement_visually_inspected':True,'display_correction':'Readable spaces in Friedfeld context-relation labels remove28px of body overflow without changing canonical data.','viewport_reset':True},
 'console_errors':0,
 'limitations':['Each stage was selected and its live SVG label checked; individual full-screen visual inspection of all58scenes is recorded separately in the apparatus audit.','Selected original Figure3 was enlarged; browser testing does not repeat full scientific reading of all source figures.','One tab debugger synchronization timed out; recovered in a fresh tab and completed desktop/mobile checks.'],
 'bound_files':{p.relative_to(S if p.is_relative_to(S) else A).as_posix():sha(p) for p in [O/'build-check-output.json',A/'site-integration-independent-audit/integration-audit.json',S/'dist/friedfeld2019-protocol.mjs',S/'dist/protocol-visuals.mjs',S/'scripts/build_dataset.py']}}
save(O/'browser-validation.json',receipt)
p=S/'data/paper-reviews/friedfeld2019.json';before=read(p);after=copy.deepcopy(before)
assert after['presentation_gates']['browser_render'] is False
after['presentation_gates']['browser_render']=True
old='Completeoriginalpageincludingcaptions,notes,plotsandtables; finalsmallfitboxesreadfromnativecrops.'
new='Complete original page reviewed, including captions, notes, plots and tables; small fit labels checked in native crops.'
raw=json.dumps(after,ensure_ascii=False);assert raw.count(old)==33
after=json.loads(raw.replace(old,new))
save(O/'reader-pre-browser-gate.json',before);save(p,after)
save(O/'browser-gate-delta.json',{'before_sha256':sha(O/'reader-pre-browser-gate.json'),'after_sha256':sha(p),'receipt_sha256':sha(O/'browser-validation.json'),'changes':['presentation_gates.browser_render false to true','33 page-review notes spaced for readability','Friedfeld-only generated relation labels display spaces instead of underscores'],'canonical_record_changes':0,'scientific_field_changes':0,'publication_still_false':after['presentation_gates']['publication'] is False})
print('Actual browser receipt saved. Reader display/browser gate updated; publication still false.')
