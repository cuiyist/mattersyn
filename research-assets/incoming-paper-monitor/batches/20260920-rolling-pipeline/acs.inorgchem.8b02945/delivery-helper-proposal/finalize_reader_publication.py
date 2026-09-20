"""Root applies exactly two reader labels after actual anonymous science proof."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json
from release_support import read,sha,validate_delivery,SID,VERSION
F=Path(__file__).resolve().parent
if F.name=='delivery-helper-proposal':F=F.parent
O=F/'site-integration-proposal';S=F.parents[4]/'recipe-atlas'
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
prep=read(O/'release-preparation.json');plan=read(O/'release-endpoints.json')
assert prep['status']=='prepared_unpublished'and prep['dataset_version']==VERSION and prep['source_id']==SID
assert prep['finalizer_script_sha256']==sha(Path(__file__))and prep['release_support_sha256']==sha(F/'release_support.py')
assert prep['endpoint_plan_sha256']==sha(O/'release-endpoints.json')
ia=F/'site-integration-independent-audit/integration-audit.json';ba=F/'site-integration-independent-audit/browser-gate-delta-audit.json'
assert read(ia)['status']=='passed'and sha(ia)==prep['integration_audit_sha256']
assert read(ba)['status']=='passed'and sha(ba)==prep['browser_audit_sha256']
proof=O/'science-release-anonymous-verification.json';v=validate_delivery(F,read(proof),plan)
p=S/'data/paper-reviews/friedfeld2019.json';assert sha(p)==prep['reader_sha256'];before=read(p)
assert before['paper_id']==SID and before['presentation_gates']['browser_render']is True and before['presentation_gates']['publication']is False
assert before['presentation_gates']['exact_product_atomic_structure_binding']is False
after=copy.deepcopy(before);after['presentation_gates']['publication']=True
after['publication_status']='Published after independent source, canonical, illustration and integrated browser reviews; exact deployed GitHub Pages commit and anonymous public bytes verified. Complete supplied main and matched SI reviewed; source conflicts remain explicit.'
check=copy.deepcopy(after);check['presentation_gates']['publication']=before['presentation_gates']['publication'];check['publication_status']=before['publication_status'];assert check==before
assert not(O/'publication-label-delta.json').exists()
save(O/'reader-pre-publication-label.json',before);save(p,after)
save(O/'publication-label-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'applied_after_verified_release','preparation_sha256':sha(O/'release-preparation.json'),'anonymous_proof_sha256':sha(proof),'science_commit':v['site_commit'],'before_sha256':prep['reader_sha256'],'after_sha256':sha(p),'exact_two_leaf_changes':True,'all_other_data_deep_equal':True,'changes':[{'pointer':'/presentation_gates/publication','before':False,'after':True},{'pointer':'/publication_status','before':before['publication_status'],'after':after['publication_status']}]})
print('Applied two publication labels after actual verified delivery; regenerate and separately verify the progress release.')
