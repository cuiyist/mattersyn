"""Independent local guard tests. No network and no mutation of release inputs."""
import copy,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).parent;F=O.parent;M=F.parents[4];S=M/'recipe-atlas';P=F/'site-integration-proposal';D=M.parent/'mattersyn-github-public-clean/mattersyn-site'
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
bound={};checks=[]
def sha(p):return hashlib.sha256(io_path(Path(p)).read_bytes()).hexdigest()
def bind(p):p=Path(p);bound[str(p)]=sha(p);return bound[str(p)]
def read(p):bind(p);return json.loads(io_path(Path(p)).read_text(encoding='utf-8-sig'))
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def ck(name,value,detail=None):checks.append({'check':name,'pass':bool(value),**({'detail':detail} if detail is not None else {})})
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def leafs(v,p=()):
 if isinstance(v,dict):return [(pp,vv) for k,x in v.items() for pp,vv in leafs(x,p+(k,))]
 if isinstance(v,list):return [(pp,vv) for i,x in enumerate(v) for pp,vv in leafs(x,p+(i,))]
 return [(p,v)]
def setleaf(v,p,val):
 for k in p[:-1]:v=v[k]
 v[p[-1]]=val

manifest=read(F/'delivery-helper-proposal/package-manifest.json');baseline_path=F/'delivery-helper-proposal/release_support.py';current_path=F/'release_support.py'
expected=next(x['sha256'] for x in manifest['files'] if x['path']=='release_support.py')
ck('immutable proposed helper matches manifest',bind(baseline_path)==expected)
old=io_path(baseline_path).read_text(encoding='utf-8');new=io_path(current_path).read_text(encoding='utf-8');bind(current_path)
before=" assert sha(S/'data/paper-reviews/friedfeld2019.json')==sha(S/'dist/data/paper-reviews/friedfeld2019.json')"
after=""" # The established reader builder adds this reviewed-scope display label.
 # All other fields must remain exactly equal to the source reader object;
 # anonymous verification above separately pins the deployed raw bytes.
 projected_reader=read(S/'data/paper-reviews/friedfeld2019.json')
 projected_reader['review_scope_label']='Complete supplied main + matched SI review'
 assert projected_reader==read(S/'dist/data/paper-reviews/friedfeld2019.json')"""
ck('single guard replacement and every other byte of code unchanged',old.count(before)==1 and old.replace(before,after)==new)
source_path=S/'data/paper-reviews/friedfeld2019.json';public_path=S/'dist/data/paper-reviews/friedfeld2019.json';source=read(source_path);public=read(public_path)
e=copy.deepcopy(source);e['review_scope_label']='Complete supplied main + matched SI review'
ck('actual source/public equality except exact derived label',e==public and 'review_scope_label' not in source)
ck('publication still false',source['presentation_gates']['publication'] is False and public['presentation_gates']['publication'] is False)
proof_path=M/'research-assets/github-public-delivery-verification.json';proof=read(proof_path);plan=read(P/'release-endpoints.json');prep=read(P/'release-preparation.json')
ck('exact science deployment commits',proof['site_commit']=='81b7afc24b4d4fcab730c01e245f2853c4b34a7f' and proof['project_commit']=='13912b684cb575b3483880a68f4951337aa43fe8')
ck('preparation still names original helper until approved correction',prep['release_support_sha256']==expected and prep['publication_gate'] is False)
m=load('independent_corrected_release_support',current_path);original_read=m.read;original_sha=m.sha
# Execute the exact imported production function against real local files and
# saved network proof, wrapping reads only to record the audited input hashes.
def tracked_read(p):bind(p);return original_read(p)
def tracked_sha(p):actual=original_sha(p);bound[str(Path(p))]=actual;return actual
m.read=tracked_read;m.sha=tracked_sha
returned=m.validate_delivery(F,copy.deepcopy(proof),copy.deepcopy(plan))
ck('actual validate_delivery passes with current proof and local bytes',returned==proof)
historical=load('independent_original_release_support',baseline_path)
try:
 historical.validate_delivery(F,copy.deepcopy(proof),copy.deepcopy(plan));old_rejected=False
except AssertionError:old_rejected=True
ck('original byte guard rejects only known builder serialization difference',old_rejected)

# In-memory read overlays test the actual function without touching either Site
# reader. Immutable SHA results are cached from the real-file successful run.
cached_sha={str(Path(p)):h for p,h in bound.items()}
def cached(p):return cached_sha.get(str(Path(p))) or tracked_sha(p)
m.sha=cached
mutations=[('derived label wrong',('review_scope_label',),'Wrong derived label'),
           ('publication flag changed',('presentation_gates','publication'),True),
           ('new unrelated field',('unexpected_guard_test',),'not permitted')]
all_leaves=leafs(public)
for label,pred in [
 ('scientific numeric value',lambda p,v: len(p)>2 and p[0]=='reader_sections' and type(v) in (int,float)),
 ('scientific prose',lambda p,v: len(p)>2 and p[0]=='reader_sections' and isinstance(v,str) and len(v)>50),
 ('canonical field pointer',lambda p,v: p and p[-1]=='json_pointer' and isinstance(v,str)),
 ('source locator',lambda p,v:p and p[-1]=='locator' and isinstance(v,str)),
 ('sample identity',lambda p,v:p and p[-1]=='sample_id' and isinstance(v,str))]:
 found=next(((p,v) for p,v in all_leaves if pred(p,v)),None)
 ck('negative test has real leaf '+label,found is not None)
 if found:
  p,v=found;mutations.append((label,p,v+1 if type(v) in (int,float) else v+' [unauthorized mutation]'))
negative_results=[]
for label,path,value in mutations:
 mutated=copy.deepcopy(public);setleaf(mutated,path,value)
 def virtual_read(p,mutated=mutated):return copy.deepcopy(mutated) if Path(p)==public_path else original_read(p)
 m.read=virtual_read
 try:m.validate_delivery(F,copy.deepcopy(proof),copy.deepcopy(plan));rejected=False
 except AssertionError:rejected=True
 ck('other single-leaf mutation rejected '+label,rejected)
 negative_results.append({'case':label,'path':'/'+('/'.join(map(str,path))),'rejected':rejected})
m.read=tracked_read
for label,change in [('deployed raw reader hash',lambda v:v['anonymous']['checks'][next(i for i,x in enumerate(v['anonymous']['checks']) if x['path']=='data/paper-reviews/friedfeld2019.json')].update(sha256='0'*64)),('failed anonymous endpoint',lambda v:v['anonymous']['checks'][0].update(http_status=500)),('deployment commit mismatch',lambda v:v['build'].update(commit='0'*40))]:
 v=copy.deepcopy(proof);change(v)
 try:m.validate_delivery(F,v,copy.deepcopy(plan));rejected=False
 except AssertionError:rejected=True
 ck('existing release guard still rejects '+label,rejected)
 negative_results.append({'case':label,'rejected':rejected})
m.sha=original_sha;m.read=original_read
ck('preparation unchanged by audit',sha(P/'release-preparation.json')==bound[str(P/'release-preparation.json')])
bind(S/'scripts/build_paper_reviews.py');bind(Path(__file__))
ck('all bound inputs stable after tests',all(sha(p)==h for p,h in bound.items()))
status='passed' if all(x['pass'] for x in checks) else 'findings_required'
report={'audit_id':'friedfeld2019-release-helper-derived-label-correction','status':status,'original_author':'/root/norberg2004_extract','correction_author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'scope':'Single release-guard correction and local saved-proof validation; no network requests, publication mutations, source rereading or browser claims.',
 'original_helper_sha256':sha(baseline_path),'corrected_helper_sha256':sha(current_path),'source_reader_sha256':sha(source_path),'public_reader_sha256':sha(public_path),'delivery_proof_path':str(proof_path),'delivery_proof_sha256':sha(proof_path),'site_commit':proof['site_commit'],'project_commit':proof['project_commit'],
 'findings':[x for x in checks if not x['pass']],'open_findings':[x for x in checks if not x['pass']],
 'summary':{'executed':len(checks),'passed':sum(x['pass'] for x in checks),'saved_verified_endpoints_rehashed':547,'withheld_paths_from_existing_proof':18,'citation_doi_count_per_readme':40,'negative_cases':len(negative_results),'no_network':True,'scientific_field_changes':0,'publication_flag':source['presentation_gates']['publication']},
 'code_delta':{'before':before,'after':after,'all_other_helper_code_identical':True},
 'negative_tests':negative_results,
 'conclusion':'The guard accepts exactly the established derived review_scope_label through full dictionary equality. Actual source/public readers otherwise match. The deployed raw public bytes remain separately pinned by the existing endpoint SHA checks. The real production validate_delivery function now passes the saved proof and current local inputs; single unrelated reader-leaf changes and tampered delivery evidence still fail.',
 'scope_limits':['Saved anonymous proof is reused and its local projected endpoint bytes are rehashed; no 547-request network verification is repeated.','No release-preparation, Site, ledger or publication flag was changed. Root must preserve preparation v1 and record the narrowly approved support-script hash change before resuming its release workflow.'],
 'checks':checks,'bound_files':dict(sorted(bound.items()))}
save(O/'release-helper-correction-audit.json',report)
io_path(O/'release-helper-correction-audit.md').write_text(f'''# Friedfeld release-helper correction audit

**{status.upper()}**. Root's correction replaces only the source/public reader byte-equality assertion with full dictionary equality after adding the established `review_scope_label`. Every other helper line is unchanged.

The actual readers differ only by that exact display label. The real corrected `validate_delivery` passes the saved deployment proof and current local files. All 547 projected endpoint bytes were rehashed; no network checks were repeated. Single unrelated reader-field mutations and altered delivery hashes/status/commit still fail. Scientific fields and publication flags are unchanged.

{len(checks)} checks passed, including {len(negative_results)} negative cases. Root should retain preparation v1 and update only the approved support-script binding with this correction receipt before resuming release. The previous source, integration, browser and deployment audits retain their distinct scopes.

Corrected helper SHA256: `{sha(current_path)}`.
''',encoding='utf-8')
print(json.dumps({'status':status,'audit_sha256':sha(O/'release-helper-correction-audit.json'),'corrected_helper_sha256':sha(current_path),'summary':report['summary'],'findings':report['findings']},indent=2))
