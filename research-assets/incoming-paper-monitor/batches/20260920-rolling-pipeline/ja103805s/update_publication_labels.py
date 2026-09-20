"""Mark completed browser/publication gates from the immutable first release proof."""
from pathlib import Path
import json,hashlib,shutil
E=Path(__file__).resolve().parent;S=E.parents[4]/'recipe-atlas';O=E/'site-integration-proposal'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v=read(O/'science-release-anonymous-verification.json');assert v['status']=='passed' and v['site_commit']=='1727559a0bc66149a86e33ef26c01599e34feb9e'
p=S/'data/paper-reviews/evans2010.json';before=O/'reader-before-publication-labels.json';assert not before.exists();shutil.copy2(p,before);d=read(p)
d['publication_status']='Published on the public MatterSyn GitHub Pages atlas; independent scientific, integration and actual browser checks passed. Exact release verification is recorded separately.'
d['presentation_gates']['browser_render']=True;d['presentation_gates']['publication']=True
d['audit_details']['integration_audit_sha256']=sha(E/'site-integration-independent-audit/integration-code-audit.json')
d['audit_details']['browser_validation_sha256']=sha(O/'browser-validation.json')
d['audit_details']['first_verified_public_release']={'dataset_version':'0.25.0','site_commit':v['site_commit'],'built_at':v['build']['updated_at'],'anonymous_checks':36,'scope':'Scientific contribution before this publication-status metadata update; scientific values are unchanged.'}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'publication-label-delta.json').write_text(json.dumps({'status':'root_metadata_update_pending_independent_delta_check','before_sha256':sha(before),'after_sha256':sha(p),'first_release_proof_sha256':sha(O/'science-release-anonymous-verification.json'),'changed_paths':['publication_status','presentation_gates.browser_render','presentation_gates.publication','audit_details.integration_audit_sha256','audit_details.browser_validation_sha256','audit_details.first_verified_public_release'],'scientific_values_unchanged':True},indent=2)+'\n',encoding='utf8')
print('Updated completed browser/publication labels only; scientific content unchanged.')
