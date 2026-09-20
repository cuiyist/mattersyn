"""Audit the root finalizer and exercise its guards with in-memory I/O only."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,json,hashlib
A=Path(__file__).resolve().parent;N=A.parent;O=N/'site-integration-proposal';S=Path('[local path redacted]')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encoded(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
checks=[];bound={}
def bind(p):bound[str(p)]=sha(p);return read(p)if Path(p).suffix=='.json'else Path(p)
def ck(label,v):checks.append({'check':label,'passed':bool(v)});assert v,label
proposal=bind(O/'conditional-publication-rule-proposal.json');plan=bind(O/'release-endpoints.json');script=bind(N/'finalize_reader_publication.py');current=bind(S/'data/paper-reviews/matuhina2023.json');browser=bind(A/'browser-gate-delta-audit.json')
ck('Distinct root proposal author',proposal['author']=='/root')
ck('Current baseline exactly approved browser reader',sha(S/'data/paper-reviews/matuhina2023.json')==proposal['baseline_reader_sha256']==browser['after_reader_sha256'])
ck('Exact script and plan hashes',sha(script)==proposal['finalizer_script_sha256']and sha(O/'release-endpoints.json')==proposal['endpoint_plan_sha256'])
ck('219 unique endpoint plan',plan['dataset_version']=='0.30.0'and plan['source_id']=='matuhina2023'and len(plan['paths'])==len(set(plan['paths']))==plan['count']==219)
verifier=N.parents[3]/'verify_public_delivery.py'
if not verifier.exists():verifier=Path('[local path redacted]')
bind(verifier);ck('Exact underlying verifier',sha(verifier)==plan['verifier_sha256'])
tree=ast.parse(verifier.read_text(encoding='utf8'));paths=[]
for n in tree.body:
 if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='paths'for t in n.targets):paths=ast.literal_eval(n.value)
 elif isinstance(n,ast.AugAssign)and isinstance(n.target,ast.Name)and n.target.id=='paths':paths+=ast.literal_eval(n.value)
 elif isinstance(n,ast.If):
  for child in n.body:
   if isinstance(child,ast.AugAssign)and isinstance(child.target,ast.Name)and child.target.id=='paths':paths+=ast.literal_eval(child.value)
ck('Plan exactly matches current verifier endpoint order',paths==plan['paths'])
ck('Source endpoints included',sum('matuhina2023' in x or 'matuhina-2023' in x for x in paths)>21)
expected=[{'pointer':'/presentation_gates/publication','before':False,'after':True},{'pointer':'/publication_status','before':current['publication_status'],'after':'Published after independent source, data, illustration and integrated browser reviews; exact deployed GitHub Pages commit and anonymous public bytes verified. Complete supplied main and matched SI reviewed; source conflicts remain explicit.'}]
ck('Exactly two permitted leaves and values',proposal['exact_allowed_changes']==expected)
ck('No current publication or exact-structure promotion',current['presentation_gates']['publication']is False and current['presentation_gates']['exact_product_atomic_structure_binding']is False and current['presentation_gates']['browser_render']is True)
# Retain the root executable statements, replacing only filesystem adapter setup.
t=ast.parse(script.read_text(encoding='utf8'));body=[]
for n in t.body:
 if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id in {'N','O','S','read','sha'}for x in n.targets):continue
 if isinstance(n,ast.FunctionDef)and n.name=='save':continue
 body.append(n)
code=compile(ast.Module(body=body,type_ignores=[]),str(script),'exec')
withheld=[f'assets/figures/{s}/pages/{d}-01.png'for s in ['heo2003','evans2010','morrison2017','lian2021','ghosh2012','sommer2020','matuhina2023']for d in ['main','si']]
proof={'status':'passed','site_commit':'a'*40,'build':{'commit':'a'*40,'status':'built'},'expected_citation_count':38,'repositories':[{'name':x,'public':True,'commit_matches':True,'anonymous_status':200}for x in ['mattersyn','mattersyn-site']],'anonymous':{'authenticated':False,'cookies_used':False,'checks':[{'path':x,'http_status':200,'matches_checked_local_bytes':True,'redirect_stays_on_site':True,'sha256':sha(S/'dist'/x)}for x in paths],'additional_withheld_paths':[{'path':x,'http_status':404}for x in withheld],'excluded_complete_page_http_status':404,'readmes':[{'repository':x,'http_status':200,'bytes_match':True,'doi_links':38}for x in ['mattersyn','mattersyn-site']]}}
def run(v,rule_edits=None):
 writes={};rule=dict(copy.deepcopy(proposal),status='passed_conditionally')
 if rule_edits:rule_edits(rule)
 fixtures={str(A/'conditional-publication-rule-audit.json'):rule,str(O/'science-release-anonymous-verification.json'):v}
 def fread(p):return copy.deepcopy(fixtures[str(p)])if str(p)in fixtures else read(p)
 def fsha(p):
  if str(p)in writes:return hashlib.sha256(encoded(writes[str(p)])).hexdigest()
  if str(p)in fixtures:return hashlib.sha256(encoded(fixtures[str(p)])).hexdigest()
  return sha(p)
 def fsave(p,x):writes[str(p)]=copy.deepcopy(x)
 ns={'N':N,'O':O,'S':S,'read':fread,'sha':fsha,'save':fsave,'__file__':str(script),'print':lambda *a,**k:None}
 try:exec(code,ns);return True,writes
 except (AssertionError,KeyError,StopIteration):return False,writes
ok,writes=run(copy.deepcopy(proof));ck('Valid complete proof passes in-memory executable finalizer',ok and len(writes)==3)
after=writes[str(S/'data/paper-reviews/matuhina2023.json')];reversed_=copy.deepcopy(after)
for x in expected:
 node=reversed_;parts=x['pointer'].strip('/').split('/')
 for part in parts[:-1]:node=node[part]
 ck('Exact new value '+x['pointer'],node[parts[-1]]==x['after']);node[parts[-1]]=x['before']
ck('Executable finalizer preserves every other field',reversed_==current)
cases=[('missing repositories',lambda v:v.update(repositories=[])),('wrong repository',lambda v:v['repositories'][0].update(name='other')),('missing readmes',lambda v:v['anonymous'].update(readmes=[])),('authenticated requests',lambda v:v['anonymous'].update(authenticated=True)),('cookies used',lambda v:v['anonymous'].update(cookies_used=True)),('missing withheld paths',lambda v:v['anonymous'].update(additional_withheld_paths=[])),('withheld page available',lambda v:v['anonymous']['additional_withheld_paths'][0].update(http_status=200)),('pending proof',lambda v:v.update(status='pending')),('different deployed commit',lambda v:v['build'].update(commit='b'*40)),('build not complete',lambda v:v['build'].update(status='building')),('wrong citation count',lambda v:v.update(expected_citation_count=36)),('missing endpoint',lambda v:v['anonymous']['checks'].pop()),('duplicate endpoint',lambda v:v['anonymous']['checks'][-1].update(path=v['anonymous']['checks'][0]['path'])),('endpoint bytes mismatch',lambda v:v['anonymous']['checks'][0].update(matches_checked_local_bytes=False)),('off-site redirect',lambda v:v['anonymous']['checks'][0].update(redirect_stays_on_site=False)),('endpoint HTTP failure',lambda v:v['anonymous']['checks'][0].update(http_status=404)),('README citations missing',lambda v:v['anonymous']['readmes'][0].update(doi_links=36)),('repository not public',lambda v:v['repositories'][0].update(public=False)),('manifest different',lambda v:next(x for x in v['anonymous']['checks']if x['path']=='data/dataset-manifest.json').update(sha256='0'*64))]
for name,mutate in cases:
 v=copy.deepcopy(proof);mutate(v);ok,w=run(v);ck('Rejected before any write: '+name,not ok and not w)
for name,mutate in [('wrong script hash',lambda r:r.update(finalizer_script_sha256='0'*64)),('wrong baseline reader',lambda r:r.update(baseline_reader_sha256='0'*64)),('wrong endpoint plan',lambda r:r.update(endpoint_plan_sha256='0'*64)),('unreviewed rule',lambda r:r.update(status='pending')),('extra allowed leaf',lambda r:r['exact_allowed_changes'].append({'pointer':'/training_note','before':'x','after':'y'}))]:
 ok,w=run(copy.deepcopy(proof),mutate);ck('Rejected before any write: '+name,not ok and not w)
ck('Actual Site reader unchanged during tests',sha(S/'data/paper-reviews/matuhina2023.json')==proposal['baseline_reader_sha256'])
ck('No actual publication applied',not(O/'publication-label-delta.json').exists())
bound[str(Path(__file__))]=sha(Path(__file__))
out={**proposal,'schema':'mattersyn-conditional-publication-rule-audit/1','source_id':'matuhina2023','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed_conditionally','open_findings':[],'proposal_sha256':sha(O/'conditional-publication-rule-proposal.json'),'baseline_reader_file':str(S/'data/paper-reviews/matuhina2023.json'),'browser_gate_audit_sha256':sha(A/'browser-gate-delta-audit.json'),'required_proof':{'dataset_version':'0.30.0','source_id':'matuhina2023','endpoint_count':219,'exact_endpoint_plan_sha256':proposal['endpoint_plan_sha256'],'citations_per_readme':38,'repository_names':['mattersyn','mattersyn-site'],'readme_names':['mattersyn','mattersyn-site'],'withheld_path_count':14,'authenticated':False,'cookies_used':False,'all_http_and_byte_checks_passed':True,'site_and_built_commit_identical':True,'proof_must_be_immutable_and_hash_bound':True},'check_count':len(checks),'checks':checks,'test_scope':'Root finalizer executable statements tested with in-memory read/hash/save adapters only. One complete synthetic proof and 24 negative guard cases; no real deployment proof or public label claimed.','bound_files':bound,'publication_approved_now':False,'deployment_verified_by_this_rule':False,'site_changed':False,'training_or_atomic_approval':False}
(A/'conditional-publication-rule-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(A/'conditional-publication-rule-audit.md').write_text(f"# Matuhina conditional publication rule\n\nConditionally passed {len(checks)} checks. The root script is bound by its exact hash, along with the current reader and 219-path endpoint plan. One complete synthetic proof succeeds; 24 incomplete or contradictory proof/rule cases fail before any write.\n\nOnly publication false→true and the exact publication-status sentence may change after the required real proof. Browser approval, SI gaps, scientific fields, exact atomic-structure false and all other flags remain unchanged. No deployment verification or publication is claimed by this conditional audit.\n",encoding='utf8')
print(json.dumps({'status':'passed_conditionally','checks':len(checks),'sha256':sha(A/'conditional-publication-rule-audit.json')}))
