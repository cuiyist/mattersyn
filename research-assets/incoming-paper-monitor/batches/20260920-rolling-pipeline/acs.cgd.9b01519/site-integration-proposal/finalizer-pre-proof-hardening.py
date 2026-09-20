"""Apply only independently approved publication labels after exact delivery proof."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';S=N.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
rule=N/'site-integration-independent-audit/conditional-publication-rule-audit.json';r=read(rule)
assert r['status']=='passed_conditionally' and r['finalizer_script_sha256']==sha(Path(__file__))
plan=read(O/'release-endpoints.json');assert plan['dataset_version']=='0.29.0' and plan['source_id']=='sommer2020'
assert r['endpoint_plan_sha256']==sha(O/'release-endpoints.json')
proof=O/'science-release-anonymous-verification.json';v=read(proof)
assert v['status']=='passed' and v['site_commit']==v['build']['commit'] and v['build']['status']=='built'
assert v['expected_citation_count']==37
checks=v['anonymous']['checks'];assert len(checks)==plan['count']==94 and {c['path'] for c in checks}==set(plan['paths'])
assert all(c['http_status']==200 and c['matches_checked_local_bytes'] and c['redirect_stays_on_site'] for c in checks)
assert all(c['http_status']==404 for c in v['anonymous']['additional_withheld_paths']) and v['anonymous']['excluded_complete_page_http_status']==404
assert all(x['public'] and x['commit_matches'] and x['anonymous_status']==200 for x in v['repositories'])
assert all(x['http_status']==200 and x['bytes_match'] and x['doi_links']==37 for x in v['anonymous']['readmes'])
manifest=S/'dist/data/dataset-manifest.json';assert read(manifest)['dataset_version']=='0.29.0'
assert next(c['sha256'] for c in checks if c['path']=='data/dataset-manifest.json')==sha(manifest)
p=S/'data/paper-reviews/sommer2020.json';assert sha(p)==r['baseline_reader_sha256'];before=read(p);after=copy.deepcopy(before)
assert before['paper_id']=='sommer2020' and before['presentation_gates']['browser_render'] is True
assert len(r['exact_allowed_changes'])==2 and {x['pointer'] for x in r['exact_allowed_changes']}=={'/presentation_gates/publication','/publication_status'}
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
assert not (O/'publication-label-delta.json').exists()
save(O/'reader-pre-publication-label.json',before);save(p,after)
save(O/'publication-label-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'applied_after_verified_release','rule_audit_sha256':sha(rule),'anonymous_proof_sha256':sha(proof),'science_commit':v['site_commit'],'before_sha256':r['baseline_reader_sha256'],'after_sha256':sha(p),'exact_two_leaf_changes':True,'all_other_data_deep_equal':True,'changes':r['exact_allowed_changes']})
print('Applied only the independently approved two publication labels after exact anonymous proof.')
