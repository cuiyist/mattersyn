"""Private author tests: read-only Site/policy and synthetic receipt guards only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[4];S=M/'recipe-atlas';P=F.parent/'la8031286'
sys.path.insert(0,str(M/'research-assets'));import public_projection_policy as policy
sys.path.insert(0,str(D));import release_support as support
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
for p in D.glob('*.py'):ast.parse(p.read_text('utf8'));ck('Syntax '+p.name,True)
plan=read(D/'release-endpoints.json');base=read(P/'site-integration-proposal/release-endpoints.json');pm=read(F/'site-integration-proposal/v1/promotion-manifest.json')
ck('547 unique endpoints',plan['count']==len(plan['paths'])==len(set(plan['paths']))==547)
ck('Prior324 preserved',plan['paths'][:324]==base['paths'])
extra=['data/paper-reviews/friedfeld2019.json']+[x['public_path']for x in pm['public_assets']]+[pre+x['record_id']+post for x in pm['records']for pre,post in[('records/','.html'),('data/records/','.json')]]
ck('Exact223 new endpoints',plan['paths'][324:]==extra and len(extra)==223)
for p in plan['paths']:ck('Endpoint exists '+p,(S/'dist'/p).is_file())
ck('18 withheld',len(plan['additional_withheld_paths'])==len(set(plan['additional_withheld_paths']))==18)
for p in plan['additional_withheld_paths']:ck('Withheld absent '+p,not(S/'dist'/p).exists()and p not in plan['paths'])
tree=ast.parse((D/'verify_public_delivery-proposed.py').read_text('utf8'));nodes=[]
def target(n):return isinstance(n,ast.Name)and n.id in['paths','withheld']
for n in tree.body:
 if isinstance(n,ast.Assign)and any(target(t)for t in n.targets):nodes.append(n)
 elif isinstance(n,ast.AugAssign)and target(n.target):nodes.append(n)
 elif isinstance(n,ast.If)and any(isinstance(x,ast.AugAssign)and target(x.target)for x in n.body):nodes.append(n)
ns={'D':S/'dist'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure endpoint selection>','exec'),ns)
ck('Executed verifier endpoint selector matches plan',ns['paths']==plan['paths'])
ck('Executed verifier withholding selector matches plan',ns['withheld']==plan['additional_withheld_paths'])
old=(D/'input-snapshots/verify_public_delivery.py').read_text('utf8');new=(D/'verify_public_delivery-proposed.py').read_text('utf8')
insert="if (D/'data/paper-reviews/friedfeld2019.json').exists():\n paths += "+repr(extra)+"\n"
hold="if (D/'data/paper-reviews/friedfeld2019.json').exists():withheld += ['assets/figures/friedfeld2019/pages/main-01.png','assets/figures/friedfeld2019/pages/si-01.png']\n"
ck('Only two verifier extensions',new.replace(insert,'').replace(hold,'')==old)
ck('No shared verifier edit',sha(M/'research-assets/verify_public_delivery.py')==sha(D/'input-snapshots/verify_public_delivery.py'))
summary=support.assert_local_candidate(F)
ck('Actual candidate/source/626old/sixexports checks passed',summary['canonical_records']==656)
ck('Actual40 source groups',read(S/'dist/data/dataset-manifest.json')['group_count']==40)
for x in read(D/'inputs.json').values():ck('Draft input hash '+Path(x['path']).name,sha(Path(x['path']))==x['sha256'])
release=(D/'release_friedfeld.py').read_text('utf8');finalizer=(D/'finalize_reader_publication.py').read_text('utf8');sync=(D/'sync_release_delta.py').read_text('utf8')
ck('No stale delivery saver','save_verified_parallel_delivery'not in release+finalizer+sync)
ck('Verify before complete',release.index('v=validate_delivery')<release.index("status='complete'"))
ck('Prepare exits without completion',release.index('raise SystemExit')<release.index("status='complete'"))
ck('No extra conditional approval cycle','conditional-publication-rule'not in release+finalizer)
ck('Finalizer proof before modification',finalizer.index('v=validate_delivery')<finalizer.index('after=copy.deepcopy'))
ck('Finalizer hashes frozen reader',"sha(p)==prep['reader_sha256']"in finalizer)
ck('Finalizer helper dependency bound',"prep['release_support_sha256']==sha(F/'release_support.py')"in finalizer)
ck('Finalizer exact scientific equality','assert check==before'in finalizer)
ck('Exact group token',support.GID=='legacy::10.1021_acs.inorgchem.8b02945')
for token in["acs.jpcc.5c05144","M/'skills'","M/'recipe-atlas'","MON/'deadline-20260920'",'intake-20260920T133256Z','intake-20260920T141934Z','policy.exclude_path(rel)','policy.project_bytes(rel','io_path(source).is_symlink()','os.walk(walkroot,followlinks=False)']:
 ck('Projection scope/policy '+token,token in sync)
for rel in['downloaded_papers/a.pdf','downloaded_papers/a_si_1.pdf','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.jpcc.5c05144/source-render/main-01.png','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.8b02945/source-render/text/si-01.txt','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.inorgchem.8b02945/complete-source-payloads.json']:
 ck('Source excluded '+rel,bool(policy.exclude_path(rel)))
for rel in['MEMORY.md','skills/mattersyn-paper-to-site/SKILL.md','research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.jpcc.5c05144/canonical-proposal/v1/records/sasongko-2025-hot-injection.json','recipe-atlas/dist/assets/figures/friedfeld2019/figure-1.png']:
 ck('Intended content retained '+rel,policy.exclude_path(rel)is None)
# Execute only the import-safe proof-validation function with synthetic metadata.
# sha/assert_local_candidate are substituted to isolate metadata guard behavior;
# actual local candidate integrity was checked separately above. No proof is saved.
fake={'status':'passed','site_commit':'x','project_commit':'y','build':{'status':'built','commit':'x'},'expected_citation_count':40,'repositories':[{'name':n,'public':True,'commit_matches':True,'anonymous_status':200}for n in['mattersyn','mattersyn-site']],'anonymous':{'authenticated':False,'cookies_used':False,'checks':[{'path':p,'http_status':200,'matches_checked_local_bytes':True,'redirect_stays_on_site':True,'sha256':'synthetic'}for p in plan['paths']],'additional_withheld_paths':[{'path':p,'http_status':404}for p in plan['additional_withheld_paths']],'excluded_complete_page_http_status':404,'readmes':[{'repository':n,'http_status':200,'bytes_match':True,'doi_links':40}for n in['mattersyn','mattersyn-site']]}}
oldsha,oldlocal=support.sha,support.assert_local_candidate;support.sha=lambda p:'synthetic';support.assert_local_candidate=lambda p:None
def setfield(o,keys,v):
 for k in keys[:-1]:o=o[k]
 o[keys[-1]]=v
cases=[(['status'],'pending'),(['site_commit'],'wrong'),(['build','status'],'building'),(['expected_citation_count'],39),(['anonymous','authenticated'],True),(['anonymous','cookies_used'],True),(['anonymous','checks',0,'http_status'],404),(['anonymous','checks',0,'sha256'],'wrong'),(['anonymous','checks',0,'matches_checked_local_bytes'],False),(['anonymous','checks',0,'redirect_stays_on_site'],False),(['anonymous','checks',0,'path'],'unknown'),(['anonymous','additional_withheld_paths',0,'http_status'],200),(['anonymous','excluded_complete_page_http_status'],200),(['repositories',0,'public'],False),(['repositories',0,'commit_matches'],False),(['repositories',0,'anonymous_status'],403),(['anonymous','readmes',0,'doi_links'],39),(['anonymous','readmes',0,'bytes_match'],False)]
try:
 ck('Synthetic valid metadata reaches return',support.validate_delivery(F,fake,plan)is fake)
 for keys,v in cases:
  bad=deepcopy(fake);setfield(bad,keys,v);rejected=False
  try:support.validate_delivery(F,bad,plan)
  except AssertionError:rejected=True
  ck('Reject invalid receipt '+str(keys),rejected)
finally:support.sha, support.assert_local_candidate=oldsha,oldlocal
out={'schema':'mattersyn-delivery-helper-author-validation/1','status':'passed','author':'/root/norberg2004_extract','at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'actual_local_candidate_guard_executed':True,'receipt_metadata_negative_cases':len(cases),'method':'Executed only read-only candidate/source/hash guards, AST-selected local endpoint statements and synthetic metadata guard tests; no mutation helper, network verifier, credential access, Site write or ledger write executed. Synthetic receipt test is not publication evidence.','network_calls':False,'site_changed':False,'independent_approval':False}
(D/'author-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'status':'passed','checks':len(checks),'endpoints':547,'candidate_records':656,'negative_receipt_cases':len(cases)}))
