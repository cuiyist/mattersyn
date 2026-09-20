from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,sys
O=Path(__file__).resolve().parent;J=O.parent;S=J.parents[4]/'recipe-atlas'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
checks=[]
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
prior_review=read(O/'release-helper-review.json');draft=J/'release-draft/prepare_delivery_helpers.py';current=J/'prepare_delivery_helpers.py'
before=draft.read_text('utf8').replace("+assets+[p for rid in records","+c['new_material_data_paths']+assets+[p for rid in records")
ck('reconstructed previous helper matches reviewed bytes',hashlib.sha256(before.encode()).hexdigest()==prior_review['bound_files'][str(current)])
addition="['data/paper-reviews/'+SID+'.json','paper-review.mjs','paper-review.css','paper-review.html','data/inventory-summary.json']"
expected=before.replace("['data/paper-reviews/'+SID+'.json']",addition)
ck('exactly four explicit endpoints added',current.read_text('utf8')==expected)
for n in ['release_support.py','release_sasongko.py','finalize_reader_publication.py','sync_release_delta.py']:ck('other helper unchanged '+n,sha(J/n)==prior_review['bound_files'][str(J/n)])
load('release_support',J/'release_support.py');helper=load('endpoint_review_helper',current)
cfg=read(J/'release-config.json');P=J/'site-integration-proposal/v1';manifest=read(P/'promotion-manifest.json')
fp=J.parent/'acs.inorgchem.8b02945/site-integration-proposal/release-endpoints.json';prior=read(fp)
plan=helper.make_plan(prior,manifest,cfg)
ck('exact 547 prior endpoints',len(prior['paths'])==547)
ck('all 547 preserved in order',plan['paths'][:547]==prior['paths'])
ck('672 unique endpoint paths',plan['count']==len(plan['paths'])==len(set(plan['paths']))==cfg['expected_endpoint_count']==672)
ck('125 additional endpoints',plan['extra_endpoints']==125)
added=['paper-review.mjs','paper-review.css','paper-review.html','data/inventory-summary.json']
for p in added:
 ck('new endpoint not previously present '+p,p not in prior['paths'])
 ck('new endpoint appears once '+p,plan['paths'].count(p)==1)
 ck('new endpoint actual local file exists '+p,(S/'dist'/p).is_file())
for p in plan['paths']:
 ck('safe existing endpoint '+p,not Path(p).is_absolute() and '..' not in Path(p).parts and ':' not in p and '\\' not in p and (S/'dist'/p).is_file())
ck('20 unique withheld original-page probes',len(plan['additional_withheld_paths'])==len(set(plan['additional_withheld_paths']))==20)
ck('withheld paths never public endpoint candidates',not(set(plan['additional_withheld_paths'])&set(plan['paths'])))
source=(J/'release-draft/input-snapshots/verify_public_delivery.py').read_text('utf8')
extended=helper.extend_verifier(source,plan['paths'][547:]);ast.parse(extended);ck('extended verifier parses',True)
ck('all four new paths included in guarded extension',all(repr(p) in extended for p in added))
ck('extension source guard retained',extended.count("if (D/'data/paper-reviews/sasongko2025.json').exists():")==2)
wrong=copy.deepcopy(cfg);wrong['expected_endpoint_count']=668
try:helper.make_plan(prior,manifest,wrong);rejected=False
except AssertionError:rejected=True
ck('obsolete 668 count rejected',rejected)
bound={str(p):sha(p) for p in [current,draft,J/'release-config.json',J/'release_support.py',J/'release_sasongko.py',J/'finalize_reader_publication.py',J/'sync_release_delta.py',P/'promotion-manifest.json',fp,O/'release-helper-review.json']+[S/'dist'/p for p in added]}
r={'status':'passed_bounded_endpoint_extension_review','scope':'Only four added endpoint paths, exact helper delta and present local path/count checks. No publication, final configuration approval or anonymous network proof.','check_count':len(checks),'checks':checks,'open_findings':[],'previous_endpoint_count':668,'effective_endpoint_count':672,'prior_endpoint_count':547,'additional_endpoint_count':125,'withheld_count':20,'added_paths':added,'effective_helper_sha256':sha(current),'other_helpers_unchanged':True,'bound_files':bound,'shared_mutation_or_network_executed':False,'created_utc':datetime.now(timezone.utc).isoformat()}
(O/'release-endpoint-addendum.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'release-endpoint-addendum.md').write_text('Passed the four-endpoint extension review. The helper changes only by adding paper-review.mjs, paper-review.css, paper-review.html and data/inventory-summary.json. They are absent from the prior 547 endpoints, occur exactly once, and exist locally. All 672 endpoint paths are unique, safe relative paths and present. The 20 withheld original-page probes remain separate. The old 668 count fails the helper guard. All other release helper bytes are unchanged. No release, shared mutation or network verification was executed.\n','utf8')
print(json.dumps({'status':r['status'],'checks':len(checks),'sha256':sha(O/'release-endpoint-addendum.json'),'helper_sha256':sha(current)},indent=2))
