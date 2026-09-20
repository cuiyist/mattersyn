"""Record actual root CUA observations; does not simulate browser testing."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,urllib.request
L=Path(__file__).resolve().parent;O=L/'site-integration-proposal';A=L/'visuals/bulk-structure-independent-audit';S=Path(r'[local path redacted]')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert read(L/'site-integration-independent-audit/integration-transport-audit.json')['status']=='passed'
ids=['bulk-a-route','bulk-b-route','bulk-characterization','composite-film-series','dft-calculation','film-beta-characterization','nc-a-route','nc-characterization','spincoat-film-route']
counts=[2,2,4,2,1,2,3,3,2]
steps=[]
for suffix,count in zip(ids,counts):
 r=read(S/'data/records'/('lian-2021-'+suffix+'.json'));assert len(r['operations'])==count
 steps.append({'record_id':r['record_id'],'operation_count':count,'actual_buttons_clicked':True})
assets=[]
for phase in ['a','b']:
 for ext in ['.json','-partial.cif']:
  rel='assets/crystal-references/lian2021-bulk-'+phase+'-non-h'+ext
  with urllib.request.urlopen('http://127.0.0.1:5193/'+rel) as response:body=response.read();status=response.status
  assert status==200 and body==(S/'dist'/rel).read_bytes();assets.append({'path':rel,'http_status':status,'exact_local_bytes':True})
now=datetime.now(timezone.utc).isoformat()
browser={'schema':'mattersyn.actual-browser-validation/1','status':'passed','auditor':'/root','at':now,'browser':'Codex in-app browser via CUA; existing temporary tab27','local_origin':'http://127.0.0.1:5193','stage_controls':steps,'total_actual_stage_controls':21,'adjacent_condition_rows':122,'checks':{'stage_titles_conditions_and_source_artwork':True,'dmf_stock_component_selection_rotation_zoom_highlight_reset':True,'product_context_selection_bulk_a_vs_b':True,'bulk_a_and_b_listed_and_expanded_views':True,'bulk_keyboard_rotation_mouse_drag_zoom_reset':True,'bulk_counts':[32,64,36,144],'figure_filter_selected_count':9,'figure_filter_full_count':48,'source_figure4_enlargement_inspected':True,'no_bulk_model_on_nc_record_or_nc_method_selection':True,'material_hub_has_equal_bulk_and_nc_method_cards':True,'stale_visual_pending_note_removed_from_display':True,'product_json_rendered_as_readable_provenance':True,'mobile_390px_nc_client_scroll':[375,375],'mobile_390px_bulk_client_scroll':[375,375],'final_mobile_initial_cell_framing_visually_inspected':True,'temporary_viewport_reset':True,'console_errors':[]},'local_download_checks':assets,'limitations':['The provider transiently reported no node after navigation on two clicks; fresh DOM state resolved it. No application error was observed.','Source-figure link target did not expose a new tab; its observed image URL was opened directly and inspected.','Atomic marker click-label behavior was not separately exercised by root.','This receipt is local browser validation, not public deployment verification.'],'changed_code_sha256':{n:sha(S/'dist'/n) for n in ['crystal-viewer.mjs','lian2021-bulk-viewer.mjs','lian2021-bulk-viewer.css','illustrated-guide.css','lian2021-protocol.mjs']}}
save(O/'browser-validation.json',browser)
math=read(A/'coordinate-math-audit.json');binding=read(A/'binding-audit.json');assert math['status']==binding['status']=='passed'
out={'schema':'mattersyn.independent_bulk_model_audit/1','status':'passed','at':now,'author':'/root/peng1998_reader_assets','auditor':'/root','author_package_freeze_sha256':sha(L/'visuals/bulk-structure-proposal/package-freeze.json'),'math_audit_sha256':sha(A/'coordinate-math-audit.json'),'binding_audit_sha256':sha(A/'binding-audit.json'),'browser_validation_sha256':sha(O/'browser-validation.json'),'mechanical_checks':math['check_count']+binding['check_count'],'scope':'Independently checked source coordinate scaling, uncertainties, Cartesian conversion, stated standard symmetry operations, published bonds/angles and partial CIF values; exact source/record/sample/formula/phase guards; actual integrated ASU and geometric expansion views. Source full-reading audit is separate.','model_role':'qualified_partial_non_hydrogen_bulk_table_reconstruction','physical_batch_join_verified':False,'full_model_eligible':False,'nanocrystal_or_film_model':False,'dft_ready':False,'exact_structure_recipe_eligible':False,'root_presentation_delta_independently_audited_by':'/root/peng1998_reader_assets','root_presentation_delta_audit_sha256':sha(L/'site-integration-independent-audit/integration-transport-audit.json'),'open_findings':[]}
save(A/'independent-audit.json',out);print(json.dumps({'browser_sha256':sha(O/'browser-validation.json'),'model_audit_sha256':sha(A/'independent-audit.json'),'status':'passed'},indent=2))
