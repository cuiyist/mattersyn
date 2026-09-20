from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,ast
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';M=N.parents[4];S=M/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'browser-validation.json').exists()
bindings=read(N/'visuals/apparatus/canonical-bindings.json')['bindings']
save(O/'browser-validation.json',{'status':'passed','author':'/root','at':datetime.now(timezone.utc).isoformat(),'scope':'Actual CUA browser review of the built local Site; not publication verification.','origin':'http://127.0.0.1:5193','stages':[{'record_id':b['record_id'],'operation_id':b['operation_id'],'selected_correct_scene':True} for b in bindings],'stage_count':31,'condition_rows':168,'all_stage_selectors_tested':True,'desktop_no_document_overflow':True,'original_figure_modal_count':14,'original_figures_loaded':True,'selected_original_tem_enlargement_visually_inspected':True,'table_and_equation_crop_links_observed':6,'sample_phase_check':'A4 selector shows only AlOOH, explicit absence of ZnAl2O4 and source conflicts. Product enlargement opens the same qualified phase card.','chemical_check':'SCF water reference title/caption preserve SCF scope and14.5mL/min source quantity. Free-water3D reference renders; zoom/reset tested; no product atomic geometry claimed.','mobile':{'viewport':{'width':390,'height':844},'document_width':375,'scroll_width':375,'visually_inspected':['microwave-stage-and-enlargement','aqueous-SCF-water-viewer'],'reset_after_check':True},'console_errors':0,'console_warnings':0,'limitations':['Whole-gallery browser loading is not a second scientific rereading; original page/crop and sample audits remain separate.','SI remains unlocated/unverified.','Water rotation was not separately tested in this check; existing viewer controls retained.'],'bound_files':{str(O/'build-check-output.json'):sha(O/'build-check-output.json'),str(N/'site-integration-independent-audit/integration-transport-audit.json'):sha(N/'site-integration-independent-audit/integration-transport-audit.json'),str(S/'dist/sommer2020-protocol.mjs'):sha(S/'dist/sommer2020-protocol.mjs'),str(S/'dist/protocol-visuals.mjs'):sha(S/'dist/protocol-visuals.mjs')}})
p=S/'data/paper-reviews/sommer2020.json';before=read(p);after=copy.deepcopy(before);assert after['presentation_gates']['browser_render'] is False;after['presentation_gates']['browser_render']=True
save(O/'reader-pre-browser-gate.json',before);save(p,after)
save(O/'browser-gate-delta.json',{'before_sha256':sha(O/'reader-pre-browser-gate.json'),'after_sha256':sha(p),'receipt_sha256':sha(O/'browser-validation.json'),'changes':[{'pointer':'/presentation_gates/browser_render','before':False,'after':True}],'all_other_fields_unchanged':True})
# Build the exact endpoint allowlist without running the network verifier.
tree=ast.parse((M/'research-assets/verify_public_delivery.py').read_text('utf8'));paths=[]
def collect(nodes):
 for node in nodes:
  if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='paths' for t in node.targets):paths[:]=ast.literal_eval(node.value)
  if isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='paths':paths.extend(ast.literal_eval(node.value))
  if isinstance(node,ast.If):collect(node.body)
collect(tree.body)
assert len(paths)==94 and len(set(paths))==94
assert all((S/'dist'/p).exists() for p in paths)
save(O/'release-endpoints.json',{'dataset_version':'0.29.0','source_id':'sommer2020','paths':paths,'count':len(paths),'verifier_sha256':sha(M/'research-assets/verify_public_delivery.py')})
print(json.dumps({'browser':'passed','reader_delta_leaves':1,'endpoints':len(paths),'receipt_sha256':sha(O/'browser-validation.json')}))
