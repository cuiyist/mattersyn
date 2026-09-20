"""Local syntax and isolated synthetic guard tests; no production mutation/network."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
D=Path(__file__).resolve().parent;J=D.parent;F=J.parent/'acs.inorgchem.8b02945';M=J.parents[4]
sys.dont_write_bytecode=True;sys.path.insert(0,str(D))
import release_support as support
import prepare_delivery_helpers as prep
read=support.read;sha=support.sha
checks=[]
def ck(label,value):
 checks.append({'check':label,'passed':bool(value)})
 assert value,label
def rejects(label,fn):
 try:fn()
 except (AssertionError,KeyError):ck(label,True)
 else:ck(label,False)
for p in D.glob('*.py'):ast.parse(p.read_text('utf8'));ck('Syntax '+p.name,True)
rejects('Unfilled release config fails before any candidate mutation',lambda:support.load_config(J))
prior=read(F/'site-integration-proposal/release-endpoints.json')
records=[x['record_id'] for x in read(J/'canonical-proposal/v1/record-manifest.json')['records']]
ck('Actual passed Sasongko IDs',len(records)==19 and len(set(records))==19)
pm={'records':[{'record_id':x} for x in records],'public_assets':[{'public_path':'sasongko2025-protocol.mjs'},{'public_path':'assets/figures/sasongko2025/figure-1.png'}]}
c={'dataset_version':'SYNTHETIC_TEST_ONLY','expected_public_asset_count':2,'expected_endpoint_count':len(prior['paths'])+41,'expected_additional_withheld_count':20,'expected_citation_count':41,'promotion_manifest':{'sha256':'a'*64},'promotion_freeze':{'sha256':'b'*64}}
plan=prep.make_plan(prior,pm,c)
ck('All prior endpoint order retained',plan['paths'][:547]==prior['paths'])
ck('All 19 record HTML/JSON pairs added',all(p in plan['paths'] for r in records for p in ['records/'+r+'.html','data/records/'+r+'.json']))
ck('Two new withheld probes and all old exclusions retained',plan['additional_withheld_paths'][:18]==prior['additional_withheld_paths'] and len(plan['additional_withheld_paths'])==20)
for name,mutate in [('duplicate assets',lambda x:x['public_assets'].append(x['public_assets'][0])),('whole page',lambda x:x['public_assets'][0].update(public_path='assets/figures/sasongko2025/pages/main-01.png')),('PDF',lambda x:x['public_assets'][0].update(public_path='source.pdf')),('path escape',lambda x:x['public_assets'][0].update(public_path='../source.json')),('missing record',lambda x:x['records'].pop())]:
 bad=copy.deepcopy(pm);mutate(bad);rejects('Reject '+name,lambda:support.read if False else prep.make_plan(prior,bad,c))
original=(D/'input-snapshots/verify_public_delivery.py').read_text('utf8');new=prep.extend_verifier(original,plan['paths'][547:]);ast.parse(new)
ck('Verifier only adds exact endpoint and withheld branches',new.count("if (D/'data/paper-reviews/sasongko2025.json').exists():")==2)
source={'paper_id':'sasongko2025','review_scope':'supplied_main_and_matched_si','presentation_gates':{'publication':False},'scientific_payload':{'quantity':.51}}
derived=copy.deepcopy(source);derived['review_scope_label']='Complete supplied main + matched SI review'
ck('Known builder display label accepted',support.projected_reader_equal(source,derived,derived['review_scope_label']))
bad=copy.deepcopy(derived);bad['scientific_payload']['quantity']=.52;ck('Scientific drift rejected',not support.projected_reader_equal(source,bad,derived['review_scope_label']))
bad=copy.deepcopy(derived);bad['presentation_gates']['publication']=True;ck('Unbound publication drift rejected',not support.projected_reader_equal(source,bad,derived['review_scope_label']))
bad=copy.deepcopy(derived);bad['other']='ignored?';ck('Unrelated derived field rejected',not support.projected_reader_equal(source,bad,derived['review_scope_label']))
v={'status':'passed','build':{'status':'built','commit':'site-test'},'site_commit':'site-test','expected_citation_count':41,'repositories':[{'name':n,'public':True,'commit_matches':True,'anonymous_status':200} for n in ['mattersyn','mattersyn-site']],'anonymous':{'authenticated':False,'cookies_used':False,'checks':[{'path':p,'http_status':200,'matches_checked_local_bytes':True,'redirect_stays_on_site':True,'sha256':'c'*64} for p in plan['paths']],'additional_withheld_paths':[{'path':p,'http_status':404} for p in plan['additional_withheld_paths']],'excluded_complete_page_http_status':404,'readmes':[{'repository':n,'http_status':200,'bytes_match':True,'doi_links':41} for n in ['mattersyn','mattersyn-site']]}}
ck('Synthetic complete proof passes field contract',support.validate_proof_fields(v,plan,c)==v)
mutations=[('failed status',lambda x:x.update(status='pending')),('pending build',lambda x:x['build'].update(status='building')),('different commit',lambda x:x['build'].update(commit='other')),('wrong citations',lambda x:x.update(expected_citation_count=40)),('authenticated',lambda x:x['anonymous'].update(authenticated=True)),('cookies',lambda x:x['anonymous'].update(cookies_used=True)),('missing endpoint',lambda x:x['anonymous']['checks'].pop()),('duplicate endpoint',lambda x:x['anonymous']['checks'].__setitem__(0,copy.deepcopy(x['anonymous']['checks'][1]))),('bad HTTP',lambda x:x['anonymous']['checks'][0].update(http_status=404)),('byte mismatch',lambda x:x['anonymous']['checks'][0].update(matches_checked_local_bytes=False)),('redirect away',lambda x:x['anonymous']['checks'][0].update(redirect_stays_on_site=False)),('exposed full page',lambda x:x['anonymous']['additional_withheld_paths'][0].update(http_status=200)),('missing exclusion',lambda x:x['anonymous']['additional_withheld_paths'].pop()),('private repository',lambda x:x['repositories'][0].update(public=False)),('repository commit mismatch',lambda x:x['repositories'][0].update(commit_matches=False)),('missing README',lambda x:x['anonymous']['readmes'].pop()),('README byte mismatch',lambda x:x['anonymous']['readmes'][0].update(bytes_match=False)),('README citation mismatch',lambda x:x['anonymous']['readmes'][0].update(doi_links=40))]
for name,mutate in mutations:
 bad=copy.deepcopy(v);mutate(bad);rejects('Reject synthetic '+name,lambda:support.validate_proof_fields(bad,plan,c))
# AST-only guards for mutators; none of these functions is executed.
for name in ['release_sasongko.py','finalize_reader_publication.py','sync_release_delta.py','prepare_delivery_helpers.py']:
 text=(D/name).read_text('utf8');ck(name+' explicit root apply guard',"'--apply'" in text);ck(name+' import safe',"if __name__=='__main__':main()" in text)
text=(D/'release_sasongko.py').read_text('utf8')
ck('No unrelated claim closure',"{x['group_id'] for x in active}<={GID}" in text)
ck('Zero active claims required',text.count('assert not monitor.active_claims')==2)
ck('Pause status explicit',"status='paused_for_joint_review'" in text and 'resume_requires_user_instruction=True' in text)
ck('Actual tool pause evidence required',"pause['actual_tool_receipt'] is True" in text and "pause['status']=='PAUSED'" in text)
text=(D/'sync_release_delta.py').read_text('utf8')
for term in ['public_projection_policy','policy.project_bytes','policy.exclude_path','io_path','followlinks=False','is_symlink','review-control.json',"M/'skills'","M/'recipe-atlas'","MON/'deadline-20260920'",'acs.inorgchem.8b02945']:ck('Backup retains '+term,term in text)
out={'status':'passed_bounded_draft_validation_not_release_approval','check_count':len(checks),'checks':checks,'fixtures':'Synthetic endpoint/proof values, clearly not actual delivery. Current canonical IDs and prior endpoint plan read only.','executed_production_mutators':False,'network_calls':0,'shared_files_changed':False,'final_counts_or_pending_gates_validated':False,'input_hashes':{str(p):sha(p) for p in [F/'release_support.py',F/'release_friedfeld.py',F/'finalize_reader_publication.py',F/'sync_release_delta.py',F/'site-integration-proposal/release-endpoints.json',M/'research-assets/verify_public_delivery.py',M/'research-assets/public_projection_policy.py',M/'research-assets/sync_github_public.py',J/'canonical-proposal/v1/record-manifest.json']}}
(D/'author-validation.json').write_text(json.dumps(out,indent=2)+'\n','utf8')
files={str(p.relative_to(D)).replace('\\','/'):sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='package-manifest.json' and '__pycache__' not in p.parts}
(D/'package-manifest.json').write_text(json.dumps({'status':'frozen_draft_requires_root_final_inputs_and_review','author':'/root/norberg2004_extract','files':files,'validation_sha256':sha(D/'author-validation.json'),'scope':'Private release-helper drafts only. No shared state, network, Git, automation or publication action executed.','ready_to_execute':False},indent=2)+'\n','utf8')
print(json.dumps({'checks':len(checks),'files':len(files),'manifest_sha256':sha(D/'package-manifest.json')}))
