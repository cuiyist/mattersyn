"""Save the actual root CUA observations and a one-field browser-gate delta."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy,ast
A=Path(__file__).resolve().parent;O=A/'site-integration-proposal';M=A.parents[4];S=M/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert not (O/'browser-validation.json').exists()
bindings=read(A/'visuals/apparatus/canonical-bindings.json')['bindings']
assert len(bindings)==39
save(O/'browser-validation.json',{'status':'passed','author':'/root','at':datetime.now(timezone.utc).isoformat(),'scope':'Actual CUA browser review of the built local Site; publication remains separate.','origin':'http://127.0.0.1:5194','stages':[{'record_id':b['record_id'],'operation_id':b['operation_id'],'selected_correct_scene':True} for b in bindings],'stage_count':39,'condition_rows':168,'all_stage_selectors_tested':True,'desktop_no_document_overflow':True,'original_figure_modal_count':20,'original_figures_loaded':True,'original_tem_saed_enlargement_visually_inspected':True,'table_and_equation_link_occurrences_observed':22,'sample_phase_check':'All seven aging context options exercised. Aged150 CsMn4Cl9 enlargement retains phase-component-only scope; cubic film aging, dispersion PL and three aged components remain separate.','chemical_check':'Oleic-acid conformer actually rendered; source90% and whole-stock1.74mL qualifier visible. Zoom/reset and functional-group toggle tested.','mobile':{'viewport':{'width':390,'height':844},'document_width':375,'scroll_width':375,'visually_inspected':['hot-injection-hold-quench-stage','oleic-acid-conformer-dialog'],'operation_enlargement_checked':True,'reset_after_check':True},'console_errors':0,'console_warnings':0,'limitations':['Whole-gallery loading is not a second scientific rereading; source page/crop and sample audits remain separate.','Drag rotation was not separately tested; existing viewer implementation retained.','This browser receipt does not admit an atomic product model or training pair.'],'bound_files':{str(O/'build-check-output.json'):sha(O/'build-check-output.json'),str(A/'site-integration-independent-audit/integration-transport-audit.json'):sha(A/'site-integration-independent-audit/integration-transport-audit.json'),str(S/'dist/matuhina2023-protocol.mjs'):sha(S/'dist/matuhina2023-protocol.mjs'),str(S/'dist/protocol-visuals.mjs'):sha(S/'dist/protocol-visuals.mjs')}})
p=S/'data/paper-reviews/matuhina2023.json';before=read(p);after=copy.deepcopy(before)
assert after['presentation_gates']['browser_render'] is False;after['presentation_gates']['browser_render']=True
save(O/'reader-pre-browser-gate.json',before);save(p,after)
save(O/'browser-gate-delta.json',{'before_sha256':sha(O/'reader-pre-browser-gate.json'),'after_sha256':sha(p),'receipt_sha256':sha(O/'browser-validation.json'),'changes':[{'pointer':'/presentation_gates/browser_render','before':False,'after':True}],'all_other_fields_unchanged':True})
tree=ast.parse((M/'research-assets/verify_public_delivery.py').read_text('utf8'));paths=[]
def collect(nodes):
 for n in nodes:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='paths' for t in n.targets):paths[:]=ast.literal_eval(n.value)
  if isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and n.target.id=='paths':paths.extend(ast.literal_eval(n.value))
  if isinstance(n,ast.If):collect(n.body)
collect(tree.body)
assert len(paths)==219 and len(set(paths))==219 and all((S/'dist'/p).exists() for p in paths)
save(O/'release-endpoints.json',{'dataset_version':'0.30.0','source_id':'matuhina2023','paths':paths,'count':len(paths),'verifier_sha256':sha(M/'research-assets/verify_public_delivery.py')})
print(json.dumps({'browser':'passed','reader_delta_leaves':1,'endpoints':len(paths),'receipt_sha256':sha(O/'browser-validation.json')}))
