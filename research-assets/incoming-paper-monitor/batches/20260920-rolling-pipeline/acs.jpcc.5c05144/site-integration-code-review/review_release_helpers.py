"""Read-only independent helper tests. Synthetic fixtures are not deployment proofs."""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,sys
O=Path(__file__).resolve().parent;J=O.parent;D=J/'release-draft';M=J.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
checks=[];bound={}
def ck(n,b):checks.append({'check':n,'passed':bool(b)});assert b,n
def rejects(fn):
 try:fn();return False
 except (AssertionError,KeyError,TypeError,ValueError):return True
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
names=['release_support.py','prepare_delivery_helpers.py','release_sasongko.py','finalize_reader_publication.py','sync_release_delta.py']
manifest=read(D/'package-manifest.json');bound[str(D/'package-manifest.json')]=sha(D/'package-manifest.json')
for rel,h in manifest['files'].items():ck('draft freeze '+rel,sha(D/rel)==h)
diffs={}
for name in names:
 a=(D/name).read_text('utf8');b=(J/name).read_text('utf8');ast.parse(b);ck(name+' syntax',True)
 bound[str(J/name)]=sha(J/name);bound[str(D/name)]=sha(D/name)
 if name=='prepare_delivery_helpers.py':ck('sole endpoint helper delta',a.replace("+assets+[p for rid in records","+c['new_material_data_paths']+assets+[p for rid in records")==b)
 elif name=='release_support.py':
  guard=" assert isinstance(c['new_material_data_paths'],list) and len(c['new_material_data_paths'])==1\n assert all(isinstance(p,str) and re.fullmatch(r'data/materials/fapbi3-[a-f0-9]{6}\\.json',p) for p in c['new_material_data_paths'])\n"
  ck('support only adds exact material path guards',a.replace('import copy, hashlib, json','import copy, hashlib, json, re').replace(" assert all(isinstance(v,int) for v in c['expected_summary'].values())",guard+" assert all(isinstance(v,int) for v in c['expected_summary'].values())")==b)
 else:ck(name+' exact draft adoption',a==b)
 diffs[name]={'draft_sha256':sha(D/name),'adopted_sha256':sha(J/name),'equal':a==b}
support=load('release_support',J/'release_support.py');helper=load('reviewed_delivery_helper',J/'prepare_delivery_helpers.py')
cfg=read(J/'release-config.json');bound[str(J/'release-config.json')]=sha(J/'release-config.json')
ck('execution disabled while placeholders remain',cfg['ready_for_root_execution'] is False and rejects(lambda:support.load_config(J)))
material_paths=cfg.get('new_material_data_paths')
ck('actual one built material path supplied',isinstance(material_paths,list) and len(material_paths)==1 and (M/'recipe-atlas/dist'/material_paths[0]).is_file())
ck('actual material hub is FAPbI3',read(M/'recipe-atlas/dist'/material_paths[0])['formula']=='FAPbI3')
bound[str(M/'recipe-atlas/dist'/material_paths[0])]=sha(M/'recipe-atlas/dist'/material_paths[0])
import re
guard_ast=[n for n in ast.walk(ast.parse((J/'release_support.py').read_text('utf8'))) if isinstance(n,ast.Assert) and 'new_material_data_paths' in ast.unparse(n)]
guard_code=compile(ast.Module(body=guard_ast,type_ignores=[]),'<isolated material path guards>','exec')
for name,value,valid in [('actual path',material_paths,True),('missing',None,False),('empty',[],False),('duplicate',material_paths*2,False),('source PDF',['data/materials/source.pdf'],False),('absolute',['C:/source.pdf'],False),('traversal',['data/materials/../source.json'],False),('other hub',['data/materials/inp-123456.json'],False)]:
 ck('material config guard '+name,(not rejects(lambda:exec(guard_code,{'c':{'new_material_data_paths':value},'re':re})))==valid)
ck('source identity, generation and original bytes still current',support.assert_source_current(J,cfg)['source_generation']==1)
identity=read(J/'intake-identity.json');bound[str(J/'intake-identity.json')]=sha(J/'intake-identity.json')
for f in identity['file_copies']:bound[f['source_path']]=f['sha256']

# A deliberately small, synthetic proof exercises gates without network or shared writes.
c={'dataset_version':'0.33.0','expected_endpoint_count':2,'expected_citation_count':41,'expected_additional_withheld_count':2}
plan={'source_id':'sasongko2025','dataset_version':'0.33.0','count':2,'paths':['data/dataset-manifest.json','data/paper-reviews/sasongko2025.json'],'expected_citation_count':41,'additional_withheld_paths':['main-page.png','si-page.png']}
v={'status':'passed','build':{'status':'built','commit':'synthetic'},'site_commit':'synthetic','expected_citation_count':41,'repositories':[{'name':n,'public':True,'commit_matches':True,'anonymous_status':200} for n in ['mattersyn','mattersyn-site']],'anonymous':{'authenticated':False,'cookies_used':False,'checks':[{'path':p,'http_status':200,'matches_checked_local_bytes':True,'redirect_stays_on_site':True} for p in plan['paths']],'additional_withheld_paths':[{'path':p,'http_status':404} for p in plan['additional_withheld_paths']],'excluded_complete_page_http_status':404,'readmes':[{'repository':n,'http_status':200,'bytes_match':True,'doi_links':41} for n in ['mattersyn','mattersyn-site']]}}
ck('synthetic exact proof accepted',support.validate_proof_fields(v,plan,c)==v)
cases=[('not passed',lambda x:x.update(status='pending')),('unbuilt',lambda x:x['build'].update(status='building')),('commit mismatch',lambda x:x['build'].update(commit='stale')),('authenticated',lambda x:x['anonymous'].update(authenticated=True)),('cookies',lambda x:x['anonymous'].update(cookies_used=True)),('missing endpoint',lambda x:x['anonymous']['checks'].pop()),('duplicate endpoint',lambda x:x['anonymous']['checks'].__setitem__(1,copy.deepcopy(x['anonymous']['checks'][0]))),('different endpoint',lambda x:x['anonymous']['checks'][0].update(path='elsewhere')),('changed bytes',lambda x:x['anonymous']['checks'][0].update(matches_checked_local_bytes=False)),('offsite redirect',lambda x:x['anonymous']['checks'][0].update(redirect_stays_on_site=False)),('not 200',lambda x:x['anonymous']['checks'][0].update(http_status=404)),('source page public',lambda x:x['anonymous']['additional_withheld_paths'][0].update(http_status=200)),('missing withheld check',lambda x:x['anonymous']['additional_withheld_paths'].pop()),('complete page public',lambda x:x['anonymous'].update(excluded_complete_page_http_status=200)),('wrong repository',lambda x:x['repositories'][0].update(name='other')),('private repository',lambda x:x['repositories'][0].update(public=False)),('repo commit mismatch',lambda x:x['repositories'][0].update(commit_matches=False)),('README bytes wrong',lambda x:x['anonymous']['readmes'][0].update(bytes_match=False)),('wrong citations',lambda x:x['anonymous']['readmes'][0].update(doi_links=40)),('missing README',lambda x:x['anonymous']['readmes'].pop())]
for name,mutate in cases:
 bad=copy.deepcopy(v);mutate(bad);ck('reject '+name,rejects(lambda:support.validate_proof_fields(bad,plan,c)))
source={'id':'x','q':{'value':1},'presentation_gates':{'publication':False}};derived={**copy.deepcopy(source),'review_scope_label':'label'}
ck('reader only builder label allowed',support.projected_reader_equal(source,derived,'label'))
derived['q']['value']=2;ck('changed scientific reader rejected',not support.projected_reader_equal(source,derived,'label'))
support_text=(J/'release_support.py').read_text('utf8')
for phrase in ["x['sha256']==sha(D/x['path'])","['data/dataset-manifest.json','data/paper-reviews/'+SID+'.json']","c['prior_record_count']==656","c['prior_training_export_count']==6","for rel,h in pm['source_audits'].items()","assert_source_current(J,c)"]:ck('retained exact-source/delivery gate '+phrase,phrase in support_text)

prior=read(J.parent/'acs.inorgchem.8b02945/site-integration-proposal/release-endpoints.json');pm=read(J/'site-integration-proposal/v1/promotion-manifest.json')
fictional_material='data/materials/test-fapbi3-fixture.json'
pc={'expected_public_asset_count':len(pm['public_assets']),'new_material_data_paths':[fictional_material],'expected_endpoint_count':len(prior['paths'])+1+1+len(pm['public_assets'])+2*len(pm['records']),'expected_additional_withheld_count':len(prior['additional_withheld_paths'])+2,'dataset_version':'0.33.0','expected_citation_count':41,'promotion_manifest':{'sha256':'fixture'},'promotion_freeze':{'sha256':'fixture'}}
newplan=helper.make_plan(prior,pm,pc)
ck('prior endpoint order unchanged',newplan['paths'][:len(prior['paths'])]==prior['paths'])
ck('new material data included exactly once',newplan['paths'].count(fictional_material)==1)
ck('all 19 record HTML/JSON pairs included',all('records/'+r['record_id']+'.html' in newplan['paths'] and 'data/records/'+r['record_id']+'.json' in newplan['paths'] for r in pm['records']))
original=(D/'input-snapshots/verify_public_delivery.py').read_text('utf8');extended=helper.extend_verifier(original,newplan['paths'][len(prior['paths']):]);ast.parse(extended);ck('extended verifier syntax',True)
ck('verifier extended only on Sasongko reader availability',extended.count("if (D/'data/paper-reviews/sasongko2025.json').exists():")==2)

release=(J/'release_sasongko.py').read_text('utf8');final=(J/'finalize_reader_publication.py').read_text('utf8');sync=(J/'sync_release_delta.py').read_text('utf8')
for phrase in ["control['new_paper_admission_allowed'] is False","control['resume_requires_user_instruction'] is True","assert {x['group_id'] for x in active}<={GID}","assert not monitor.active_claims","pause['automation_id']==c['automation_id']","pause['status']=='PAUSED'","pause['actual_tool_receipt'] is True"]:ck('pause/admission gate '+phrase,phrase in release)
ck('actual heartbeat pause receipt only required before finish mutation',release.index("pause=read(J/c['automation_pause_receipt'])")<release.index("if not args.apply:print('Exact delivery"))
ck('prepare cannot mark publication true',"assert reader['presentation_gates']['publication'] is False" in release and "'publication_gate':False" in release)
ck('verification precedes completion mutation',release.index('proof=validate_delivery')<release.index("group_id=GID,status='complete'"))
ck('finalizer enforces exact prep bindings and actual proof',all(x in final for x in ["prep['config_sha256']==sha(J/'release-config.json')","prep['endpoint_plan_sha256']==sha(O/'release-endpoints.json')","v=validate_delivery(J,read(proof),plan,c)","sha(p)==prep['reader_sha256']","assert check==before"]))
after_targets=[ast.unparse(t) for n in ast.walk(ast.parse(final)) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Subscript) and ast.unparse(t).startswith("after[")]
ck('exactly two publication leaves assigned',set(after_targets)=={"after['presentation_gates']['publication']","after['publication_status']"} and len(after_targets)==2)
ck('finalizer default cannot mutate',final.index('if not args.apply:')<final.index("save(O/'reader-pre-publication-label.json'"))
ck('sync defaults dry-run and no Git/network/delete calls',"if args.apply:target.parent.mkdir" in sync and 'subprocess' not in sync and 'requests' not in sync and '.unlink(' not in sync and 'rmtree' not in sync)
ck('source projection policy applied before copy',sync.index('policy.exclude_path(rel)')<sync.index('policy.project_bytes(rel')<sync.index('target.write_bytes(raw)'))
policy=load('reviewed_public_policy',M/'research-assets/public_projection_policy.py');bound[str(M/'research-assets/public_projection_policy.py')]=sha(M/'research-assets/public_projection_policy.py')
for rel in ['research-assets/x/source-render/page.png','research-assets/x/source-render/main.txt','research-assets/x/source-render/complete-source-payloads.json','downloaded_papers/p.pdf','.git/config']:ck('source equivalent withheld '+rel,policy.exclude_path(rel) is not None)
raw=b'{"keep":1,"firstPagePreviewPrivate":"PRIVATE"}';out,_=policy.project_bytes('research-assets/test-metadata.json',raw);ck('private raw-text field stripped',b'PRIVATE' not in out)

issue=[]
if 'new_material_data_paths' not in cfg:issue.append({'id':'SAS-RELEASE-CONFIG-01','finding':'Adopted endpoint helper requires new_material_data_paths, absent from current config. Enabled execution would raise KeyError.','resolution_required':'Add the actual built FAPbI3 hub JSON path list, and validate its type and path scope before enabling execution.'})
r={'status':'revision_required' if issue else 'passed_bounded_release_helper_review','scope':'Read-only comparison with frozen author release draft and prior Friedfeld helper; pure synthetic proof/endpoint tests only. No actual release or configuration counts certified.','checks':checks,'check_count':len(checks),'open_findings':issue,'resolved_findings':[{'id':'SAS-RELEASE-CONFIG-01','resolution':'Root supplied the actual built FAPbI3 hub path and exact one-item list/relative-path regex guards; both independently tested.'}] if not issue else [],'adopted_deltas':diffs,'synthetic_fixture_warning':'All test proof objects and the material path test-fapbi3-fixture.json are invented fixtures only, never saved as delivery receipts or actual configuration.','config_execution_enabled':cfg['ready_for_root_execution'],'pending':['Actual final root configuration and exact counts/hashes','Distinct integration/browser audits','Actual anonymous deployed proof','Actual automation-tool PAUSED receipt before final finish'],'source_current':{'generation':identity['source_generation'],'bundle_sha256':identity['bundle_sha256']},'bound_files':bound,'network_or_shared_mutation_executed':False,'created_utc':datetime.now(timezone.utc).isoformat()}
(O/'release-helper-review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'release-helper-review.md').write_text('Read-only helper review completed. Proof gates reject stale deployment, missing endpoints, changed bytes, authenticated/cookie requests, publicly reachable full pages, repository mismatches and citation errors. Publication finalization changes exactly two leaves after matching preparation and actual proof. Existing 656 records/six exports and source generation are rechecked; active claims must close before finish, which requires the actual matching heartbeat PAUSED receipt. Source-equivalent files are withheld by the existing projection policy. No release, sync, network, ledger, memory or automation mutation was executed.\n\n'+('Open: add and validate the actual new_material_data_paths configuration field before enabling execution.\n' if issue else 'No open implementation finding; actual configuration/deployment receipts remain separate gates.\n'),'utf8')
print(json.dumps({'status':r['status'],'checks':len(checks),'open_findings':issue,'sha256':sha(O/'release-helper-review.json')},indent=2))
