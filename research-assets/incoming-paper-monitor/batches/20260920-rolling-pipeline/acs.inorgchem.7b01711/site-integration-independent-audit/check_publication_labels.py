"""Independent six-field publication-label delta; no Site writes or network requests."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys,datetime
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).resolve().parent;B=A.parent;O=B/'site-integration-proposal'
S=Path(r'[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before_path=O/'reader-before-publication-labels.json';after_path=S/'data/paper-reviews/morrison2017.json'
before=read(before_path);after=read(after_path);delta=read(O/'publication-label-delta.json')
proof=read(O/'science-release-anonymous-verification.json');browser=read(O/'browser-validation.json');integration=read(A/'integration-code-audit.json')
expected=['publication_status','presentation_gates.browser_render','presentation_gates.publication','audit_details.integration_audit_sha256','audit_details.browser_validation_sha256','audit_details.first_verified_public_release']
checks=[]
def ck(n,x):checks.append({'check':n,'passed':bool(x)})
def remove(obj,path):
    keys=path.split('.');node=obj
    for k in keys[:-1]:node=node[k]
    node.pop(keys[-1],None)
ck('exact declared allowlist',set(delta['changed_paths'])==set(expected) and len(delta['changed_paths'])==6)
ck('before hash',sha(before_path)==delta['before_sha256'])
ck('after hash',sha(after_path)==delta['after_sha256'])
ck('immutable release proof hash',sha(O/'science-release-anonymous-verification.json')==delta['first_release_proof_sha256'])
old,new=deepcopy(before),deepcopy(after)
for path in expected:remove(old,path);remove(new,path)
ck('deep scientific equality excluding exact six metadata paths',old==new)
ck('browser gate completed',after['presentation_gates']['browser_render'] is True)
ck('publication gate completed',after['presentation_gates']['publication'] is True)
ck('browser proof hash and status',after['audit_details']['browser_validation_sha256']==sha(O/'browser-validation.json') and browser['status']=='passed')
ck('integration proof hash and status',after['audit_details']['integration_audit_sha256']==sha(A/'integration-code-audit.json') and integration['status']=='passed' and integration['open_findings']==[])
ck('browser reviewer is root actual CUA report',browser['reviewer']=='/root' and 'CUA' in browser['mechanism'])
ck('browser actual stage and runtime checks',browser['pages_and_controls']['all24buttons_clicked'] is True and browser['pages_and_controls']['runtime_errors']==[])
ck('public proof passed with explicit anonymous mode',proof['status']=='passed' and proof['anonymous']['authenticated'] is False and proof['anonymous']['cookies_used'] is False)
ck('expected science commit',proof['site_commit']=='22e894390eae26cfcf4eb84c4c69157f49cf617b' and proof['build']['commit']==proof['site_commit'])
ck('successful Pages build',proof['build']['status']=='built' and proof['pages']['status']=='built' and proof['build']['updated_at']=='2026-09-20T08:10:47Z')
ck('47 distinct anonymous endpoints',len(proof['anonymous']['checks'])==47 and len({x['path'] for x in proof['anonymous']['checks']})==47)
for endpoint in proof['anonymous']['checks']:
    ck('recorded anonymous success '+endpoint['path'],endpoint['http_status']==200 and endpoint['matches_checked_local_bytes'] is True and endpoint['redirect_stays_on_site'] is True)
for repo in proof['repositories']:ck('public repository proof '+repo['name'],repo['public'] is True and repo['anonymous_status']==200 and repo['commit_matches'] is True and repo['expected_commit']==repo['remote_commit'])
for readme in proof['anonymous']['readmes']:ck('34 citation README '+readme['repository'],readme['http_status']==200 and readme['bytes_match'] is True and readme['doi_links']==34)
ck('withheld source pages',proof['anonymous']['excluded_complete_page_http_status']==404 and all(x['http_status']==404 for x in proof['anonymous']['additional_withheld_paths']))
release=after['audit_details']['first_verified_public_release']
ck('metadata matches first science release',release['dataset_version']=='0.26.0' and release['site_commit']==proof['site_commit'] and release['built_at']==proof['build']['updated_at'] and release['anonymous_checks']==47)
# Reconstruct the generated reader associated with the first-release browser/hash proof.
sys.path.insert(0,str(S/'scripts'))
from review_scope import source_review_scope
prior_generated=deepcopy(before);prior_generated['review_scope_label']=source_review_scope(before)['label']
serialized=json.dumps(prior_generated,ensure_ascii=False,indent=2)+'\n'
generated_hashes={hashlib.sha256(serialized.encode()).hexdigest(),hashlib.sha256(serialized.replace('\n','\r\n').encode()).hexdigest()}
endpoint=next(x for x in proof['anonymous']['checks'] if x['path']=='data/paper-reviews/morrison2017.json')
ck('anonymous released reader is generated pre-label snapshot',endpoint['sha256'] in generated_hashes)
ck('browser reviewed same generated reader',browser['bound_files']['dist/data/paper-reviews/morrison2017.json']==endpoint['sha256'])
for rel,h in browser['bound_files'].items():
    if rel=='dist/data/paper-reviews/morrison2017.json':continue
    ck('browser-science dependency unchanged '+rel,sha(S/rel)==h)
record_paths=[]
for path,h in integration['bound_files'].items():
    p=Path(path)
    if p.parent==S/'data/records' and p.name.startswith('morrison-'):
        ck('canonical bytes unchanged '+p.name,sha(p)==h);record_paths.append(p)
ck('18 promoted canonical records unchanged',len(record_paths)==18)
boundpaths=[before_path,after_path,O/'publication-label-delta.json',O/'science-release-anonymous-verification.json',O/'browser-validation.json',A/'integration-code-audit.json',B/'update_publication_labels.py',Path(__file__),S/'scripts/review_scope.py']+record_paths
out={'schema':'mattersyn.independent-publication-label-audit/1','source_id':'morrison2017','auditor':'/root/peng1998_reader_assets','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if all(x['passed'] for x in checks) else 'findings','scope':'Exactly six declared reader publication/browser metadata paths and their existing root browser, independent integration and root anonymous-release proof bindings; no new browser session or anonymous HTTP request was performed by this auditor.','before_sha256':sha(before_path),'after_sha256':sha(after_path),'release_proof_sha256':sha(O/'science-release-anonymous-verification.json'),'site_commit':proof['site_commit'],'declared_changed_paths':expected,'scientific_deep_equality':old==new,'canonical_records_unchanged':len(record_paths),'checks':checks,'check_count':len(checks),'open_findings':[x for x in checks if not x['passed']],'bound_files':{str(p):sha(p) for p in boundpaths},'site_modified':False,'training_admission_changed':False}
dest=A/'publication-label-audit.json';dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'publication-label-audit.md').write_text('# Morrison publication metadata delta\n\n'+out['status'].capitalize()+'. Exactly the six declared metadata paths change; the complete reader is deeply equal after excluding those paths. All 18 promoted canonical record bytes remain unchanged.\n\nThe before-snapshot reproduces the generated reader hash in both the recorded browser proof and the first anonymous scientific release. The recorded proof covers commit `'+proof['site_commit']+'`, 47 anonymous endpoints and 34 citations in each README. This audit verifies those saved proof bindings; it does not claim a new browser or HTTP check.\n\nAudit SHA256: `'+sha(dest)+'`. No Site or training changes were made by the auditor.\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'checks':len(checks),'open_findings':out['open_findings'],'sha256':sha(dest)},indent=2))
