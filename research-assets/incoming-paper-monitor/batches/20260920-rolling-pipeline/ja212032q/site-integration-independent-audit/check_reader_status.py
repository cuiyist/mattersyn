"""Bounded independent metadata delta and conditional publication rule only."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json
A=Path(__file__).resolve().parent;G=A.parent;O=G/'site-integration-proposal';S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
bound={};checks=[]
def bind(p):
 p=Path(p);bound[str(p)]=sha(p);return load(p) if p.suffix=='.json' else p
def same(a,b,label):
 checks.append({'passed':a==b,'check':label})
 if a!=b:print('FAILED '+label)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
delta=bind(O/'reader-final-status-delta.json');before=bind(delta['before_file']);after=bind(delta['after_file'])
same(sha(delta['before_file']),delta['before_sha256'],'exact before bytes');same(sha(delta['after_file']),delta['after_sha256'],'exact after bytes')
same(delta['after_sha256'],'09f29524dd8ed089b89e0643d1bc489a649944566e5647a1a0948f9ed55e3bee','assigned proposal hash')
same(delta['allowed_top_level_changes'],['presentation_gates','remaining_gaps','audit_details'],'exact top-level scope')
same(sha(S/'data/paper-reviews/ghosh2012.json'),delta['before_sha256'],'before is current integrated reader')
browser=bind(O/'browser-validation.json');same(sha(O/'browser-validation.json'),'aecad9ae390fec9e9e5f98de199eb452209ea44e49da2c2dfe5b0c9ab3ababb9','exact browser receipt')
same(browser['status'],'passed','browser receipt passed');same(browser['pending'],[],'browser no pending');same(browser['actual_stage_controls_clicked'],33,'33 controls');same(browser['actual_visible_condition_note_rows'],183,'183 rows')
same(sum(x['operation_count'] for x in browser['stage_controls']),33,'stage record counts sum');same(all(x['actual_buttons_clicked'] for x in browser['stage_controls']),True,'all controls actually clicked')
same(browser['mobile']['document_client_width'],browser['mobile']['document_scroll_width'],'mobile no overflow')
for rel,digest in browser['bound_files'].items():bind(S/rel);same(sha(S/rel),digest,'browser binding current '+rel)
integration=bind(A/'integration-transport-audit.json');same(integration['status'],'passed','independent integration passed')
same(integration['bound_files'][str(S/'data/paper-reviews/ghosh2012.json')],delta['before_sha256'],'before reader is exact transport-audited bytes')
for rel,digest in before['audit_details']['audit_sha256'].items():audit=bind(G/rel);same(audit['status'],'passed','dependency passed '+rel);same(sha(G/rel),digest,'dependency digest '+rel)
for name,key in [('promotion-delta-audit.json','promotion_audit_sha256'),('product-context-audit.json','symbolic_product_context_audit_sha256')]:
 audit=bind(A/name);same(audit['status'],'passed','separate overlay passed '+name);same(sha(A/name),after['audit_details'][key],'overlay receipt '+name)
expected=copy.deepcopy(before)
expected['presentation_gates']['browser_render']=True;expected['presentation_gates']['symbolic_product_context_binding']=True
old='Source, canonical/reader, molecular and apparatus audits passed. Symbolic product-context binding, integrated browser and publication gates remain separate.'
new='Source, canonical/reader, molecular, apparatus, symbolic product-context and browser audits passed. Public deployment verification is tracked separately. No atomic product model or exact structure–recipe training pair is admitted.'
same(before['remaining_gaps'].count(old),1,'single historical gate sentence')
expected['remaining_gaps']=[new if x==old else x for x in before['remaining_gaps']]
expected['audit_details']['browser_validation_sha256']=sha(O/'browser-validation.json')
same(after,expected,'EXACT four allowed leaf changes; all science deep-equal')
same(after['remaining_gaps'][:-1],before['remaining_gaps'][:-1],'all eight scientific gaps unchanged')
same(after['presentation_gates']['publication'],False,'publication remains false');same(after['presentation_gates']['exact_product_atomic_structure_binding'],False,'atomic structure remains false')
same(after['audit_details']['training_promotions'],0,'no training promotion');same(after['audit_details']['source_conflicts_resolved'],False,'source conflicts retained')
same(after['publication_status'],before['publication_status'],'publication text unchanged')
changed_top={k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)};same(changed_top,set(delta['allowed_top_level_changes']),'only exact three metadata fields')
bind(Path(__file__));findings=[x for x in checks if not x['passed']]
out={'schema':'mattersyn-reader-final-status-audit/1','source_id':'ghosh2012','author':'/root','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not findings else 'open_findings','proposal_sha256':sha(delta['after_file']),'before_sha256':sha(delta['before_file']),'browser_receipt_sha256':sha(O/'browser-validation.json'),'integration_receipt_sha256':sha(A/'integration-transport-audit.json'),'check_count':len(checks),'open_findings':findings,'allowed_changes':[{'pointer':'/presentation_gates/browser_render','before':False,'after':True},{'pointer':'/presentation_gates/symbolic_product_context_binding','before_absent':True,'after':True},{'pointer':'/remaining_gaps/8','before':old,'after':new},{'pointer':'/audit_details/browser_validation_sha256','before_absent':True,'after':sha(O/'browser-validation.json')}],'scientific_deep_equality':not findings,'scope':'Receipt and exact metadata-delta review. No repeated PDF/integration audit or independent claim to have performed root browser interactions. Publication remains false.','bound_files':dict(sorted(bound.items())),'site_changed':False,'publication_approved':False}
save(A/'reader-final-status-audit.json',out);save(A/'reader-final-status-checks.json',{'checks':checks})
(A/'reader-final-status-audit.md').write_text(f"# Ghosh final reader status audit\n\nStatus: **{out['status']}**; {len(checks)} checks, {len(findings)} open findings. Exact proposal `{out['proposal_sha256']}`.\n\nFour declared leaf changes within three metadata fields are supported by the exact passed browser, product-context and integration receipts. All scientific content and eight scientific gaps are deeply unchanged. Publication and exact atomic structure approval remain false; training promotion remains zero. No Site edits or repeated browser claim.\n",encoding='utf8')
assert not findings,'Cannot qualify publication rule until final status passes'
pubtext='Published on GitHub Pages after independent source, data, visual and browser review; anonymous byte verification passed. Current deployment status is tracked on the review progress page.'
rule={'schema':'mattersyn-conditional-publication-rule-audit/1','source_id':'ghosh2012','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_conditionally','baseline_reader_sha256':sha(delta['after_file']),'baseline_reader_file':str(delta['after_file']),'status_audit_sha256':sha(A/'reader-final-status-audit.json'),'exact_allowed_changes':[{'pointer':'/presentation_gates/publication','before':False,'after':True},{'pointer':'/publication_status','before':after['publication_status'],'after':pubtext}],'required_proof':{'status':'passed','anonymous':True,'exact_endpoint_count':77,'all_endpoint_bytes_verified':True,'dataset_version':'0.28.0','source_id':'ghosh2012','proof_must_be_immutable_and_hash_bound':True,'proof_must_identify_exact_release_commit_and_deployment':True,'all_failed_or_pending_checks':0,'actual_reader_before_update_must_match_baseline':True},'application_validation':['Verify an immutable anonymous release proof against the exact deployed release; all77 endpoints and dataset0.28.0 must pass.','Apply only the two exact leaves after that proof; all other metadata and scientific values must be deeply equal to the frozen baseline.','Keep source conflict, training, model and exact atomic structure gates unchanged.','Save proof hash, before/after reader hashes and exact applied delta in a separate receipt.'],'publication_approved_now':False,'deployment_verified_by_this_rule':False,'site_changed':False,'bound_files':{str(A/'reader-final-status-audit.json'):sha(A/'reader-final-status-audit.json'),str(delta['after_file']):sha(delta['after_file'])}}
save(A/'conditional-publication-rule-audit.json',rule)
(A/'conditional-publication-rule-audit.md').write_text(f"# Ghosh conditional publication metadata rule\n\nStatus: **passed conditionally**. Baseline `{rule['baseline_reader_sha256']}`.\n\nOnly publication false→true and the exact stored publication-status sentence are permitted after immutable, hash-bound anonymous byte verification passes all77 endpoints for dataset0.28.0 and identifies the exact deployed release. Every other field must remain deeply equal. This rule does not assert that deployment has occurred or passed.\n",encoding='utf8')
print(json.dumps({'status':out['status'],'checks':len(checks),'audit_sha256':sha(A/'reader-final-status-audit.json'),'conditional_rule_sha256':sha(A/'conditional-publication-rule-audit.json')}))
