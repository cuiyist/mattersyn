"""Root receipt for actual integrated browser observations; publication is separate."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json
P=Path(__file__).resolve().parent; O=P/'site-integration-proposal'; S=P.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'browser-validation.json').exists()
bindings=read(P/'visuals/apparatus/canonical-bindings.json')['bindings']; assert len(bindings)==35
save(O/'browser-validation.json',{
 'status':'passed','author':'/root','at':datetime.now(timezone.utc).isoformat(),
 'scope':'Actual CUA interaction with built local Site. Independent source, data and asset audits are separate.',
 'origin':'http://127.0.0.1:5194','stage_count':35,'condition_rows':167,
 'stages':[{'record_id':b['record_id'],'operation_id':b['operation_id'],'selected_correct_scene':True} for b in bindings],
 'all_stage_selectors_tested':True,'desktop_no_document_overflow':True,
 'original_figure_modal_count':9,'original_figures_loaded':True,
 'original_tem_saed_and_si_xps_enlargements_visually_inspected':True,
 'full_reader_original_asset_links':20,
 'full_reader_image_loading_note':'Images are lazy-loaded; the nine method-gallery enlargements were individually loaded and checked. Complete source/crop verification remains the independent source audit.',
 'chemical_check':'Cerium nitrate symbolic formula components visually inspected, with no invented Ce-O coordination. Ethanol conformer rendered; group toggle, zoom and reset tested. Four stock selectors switched between solute and solvent. Named TEA/printed formula distinction visible.',
 'sample_phase_check':'All four XPS specimen options exercised. Calcined long-exposure enlargement retains approximately45% Ce(III), no invented55% complement, unknown solvent and batch, and measurement-history boundary.',
 'mobile':{'viewport':{'width':390,'height':844},'document_width':375,'scroll_width':375,'visually_inspected':['calcination-stage','enlarged-calcination-diagram'],'reset_after_check':True},
 'console_errors':0,'console_warnings':0,
 'limitations':['Drag rotation was not separately exercised; existing viewer retained.','Browser validation does not qualify an atomic structure or training pair.'],
 'bound_files':{str(p):sha(p) for p in [O/'build-check-output.json',P/'site-integration-independent-audit/integration-transport-audit.json',S/'dist/pati2009-protocol.mjs',S/'dist/protocol-visuals.mjs']}})
p=S/'data/paper-reviews/pati2009.json'; before=read(p); after=copy.deepcopy(before)
assert after['presentation_gates']['browser_render'] is False
after['presentation_gates']['browser_render']=True
save(O/'reader-pre-browser-gate.json',before);save(p,after)
save(O/'browser-gate-delta.json',{'before_sha256':sha(O/'reader-pre-browser-gate.json'),'after_sha256':sha(p),'receipt_sha256':sha(O/'browser-validation.json'),'changes':[{'pointer':'/presentation_gates/browser_render','before':False,'after':True}],'all_other_fields_unchanged':True})
print('Actual browser receipt saved; only browser_render metadata changed. Publication remains false.')
