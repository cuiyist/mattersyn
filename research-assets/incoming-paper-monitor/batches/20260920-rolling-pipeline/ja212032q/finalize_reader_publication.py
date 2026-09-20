from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib
L=Path(__file__).resolve().parent;O=L/'site-integration-proposal';S=Path(r'[local path redacted]')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
rule=L/'site-integration-independent-audit/conditional-publication-rule-audit.json';r=read(rule);assert r['status']=='passed_conditionally'
proof=O/'science-release-anonymous-verification.json';v=read(proof);assert v['status']=='passed' and v['site_commit']==v['build']['commit']
assert len(v['anonymous']['checks'])==77 and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
p=S/'data/paper-reviews/ghosh2012.json';assert sha(p)==r['baseline_reader_sha256'];before=read(p);after=copy.deepcopy(before)
for change in r['exact_allowed_changes']:
 parts=change['pointer'].strip('/').split('/');node=after
 for part in parts[:-1]:node=node[part]
 assert node[parts[-1]]==change['before'];node[parts[-1]]=change['after']
check=copy.deepcopy(after)
for change in r['exact_allowed_changes']:
 parts=change['pointer'].strip('/').split('/');node=check
 for part in parts[:-1]:node=node[part]
 node[parts[-1]]=change['before']
assert check==before and after['presentation_gates']['exact_product_atomic_structure_binding'] is False
save(O/'reader-pre-publication-label.json',before);save(p,after)
save(O/'publication-label-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'applied_after_verified_release','rule_audit_sha256':sha(rule),'anonymous_proof_sha256':sha(proof),'science_commit':v['site_commit'],'before_sha256':r['baseline_reader_sha256'],'after_sha256':sha(p),'exact_two_leaf_changes':True,'all_other_data_deep_equal':True,'changes':r['exact_allowed_changes']})
print('Applied only the independently approved two publication labels after exact anonymous proof.')
