from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib
L=Path(__file__).resolve().parent;O=L/'site-integration-proposal';S=Path(r'[local path redacted]')
p=S/'data/paper-reviews/lian2021.json';before=json.loads(p.read_text(encoding='utf8'));after=copy.deepcopy(before)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if (O/'reader-pre-final-status.json').exists():assert json.loads((O/'reader-pre-final-status.json').read_text(encoding='utf8'))==before
else:save(O/'reader-pre-final-status.json',before)
after['presentation_gates']['browser_render']=True
after['presentation_gates']['qualified_partial_bulk_display']=True
assert after['presentation_gates']['publication'] is False
assert after['presentation_gates']['exact_product_atomic_structure_binding'] is False
after['route_evidence_scope_notes']['bulk_structure']='Printed non-hydrogen coordinates and displacement parameters apply to bulk A and B. Separately audited partial table reconstructions are displayed for four explicit bulk compound contexts. Hydrogen positions, occupancies and the cited crystal ZIP remain unavailable. This display does not establish a complete model, the identity of a physical synthesis aliquot, or any nanocrystal/film/DFT/training structure.'
old='Source, canonical/reader, molecular and apparatus audits passed. Bulk-coordinate display qualification, integrated browser and publication gates remain separate.'
new='Source, canonical/reader, molecular, apparatus, partial bulk-coordinate display, integration and browser audits passed. Public deployment verification is tracked separately. No complete atomic model or exact structure–recipe training pair is admitted.'
assert old in after['remaining_gaps'];after['remaining_gaps']=[new if x==old else x for x in after['remaining_gaps']]
after['audit_details']['qualified_bulk_model_audit_sha256']=sha(L/'visuals/bulk-structure-independent-audit/independent-audit.json')
after['audit_details']['integration_audit_sha256']=sha(L/'site-integration-independent-audit/integration-transport-audit.json')
after['audit_details']['browser_validation_sha256']=sha(O/'browser-validation.json')
save(O/'reader-final-status-proposal.json',after)
save(O/'reader-final-status-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'pending_independent_delta_audit','author':'/root','before_file':str(O/'reader-pre-final-status.json'),'after_file':str(O/'reader-final-status-proposal.json'),'before_sha256':sha(O/'reader-pre-final-status.json'),'after_sha256':sha(O/'reader-final-status-proposal.json'),'allowed_top_level_changes':['presentation_gates','route_evidence_scope_notes','remaining_gaps','audit_details'],'science_arrays_unchanged':True,'publication_claim':False})
print('Prepared bounded reader status overlay; not applied before independent audit.')
