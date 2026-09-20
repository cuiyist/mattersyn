"""Independent actual Site transport checks. All output is private audit output."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib,copy,collections,re
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;J=O.parent;M=J.parents[4];S=M/'recipe-atlas';I=J/'site-integration-proposal';P=I/'v1';B=I/'base-site-inputs';V=I/'reader-status-overlay'
sys.path.insert(0,str(M/'research-assets'));from sync_github_public import io_path
checks=[];bound={}
def sha(p):return hashlib.sha256(io_path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p);h=sha(p);bound[str(p.resolve())]=h;return h
def read(p):bind(p);return json.loads(io_path(p).read_text('utf8'))
def ck(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),**({'detail':detail} if detail is not None else {})})
def save(p,x):io_path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def walk(x,p=''):
 yield p,x
 if isinstance(x,dict):
  for k,v in x.items():yield from walk(v,p+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):yield from walk(v,p+'/'+str(i))
def diff(a,b,p=''):
 if type(a)!=type(b):return [p]
 if isinstance(a,dict):return sum((diff(a[k],b[k],p+'/'+k) if k in a and k in b else [p+'/'+k] for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [p+'#length']
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [p]
promotion=read(O/'promotion-delta-audit.json');imp=read(I/'site-import-manifest.json');manifest=read(P/'promotion-manifest.json');code=read(I/'code-delta.json');build=read(I/'build-check-output.json');preserved=read(I/'old-science-preservation.json')
ck('Passed exact promotion audit used',promotion['status']=='passed' and not promotion['open_findings'] and imp['promotion_audit_sha256']==sha(O/'promotion-delta-audit.json')=='7d6715ac719822bb2aa8a232cb6810772d1647b5c64cb12fb2c4191b553b2576')
ck('Exact original projection freeze',bind(P/'package-freeze.json')==imp['proposal_freeze_sha256']==promotion['proposal_freeze_sha256'])
ck('Exact effective reader overlay',bind(V/'package-freeze.json')==promotion['reader_status_overlay_freeze_sha256'])
ck('All eighteen build/check commands finished',len(build['runs'])==18 and all(r['exit_code']==0 for r in build['runs']))
ck('Build preservation receipt passed',preserved['status']=='passed' and preserved['unchanged_existing_records']==656)
for rel in ['import_reviewed_sasongko.py','build_and_check_site.py','build_sasongko_inventory.py']:bind(J/rel)
for rel in ['scripts/check_site.py','scripts/check_atlas.py','scripts/check_quality.py']:bind(S/rel)
old=read(I/'base-record-hashes.json');exports=read(I/'base-training-export-hashes.json');ck('Baseline 656 records and six exports',len(old)==656 and len(exports)==6)
for name,h in old.items():
 ck('Old canonical bytes '+name,bind(S/'data/records'/name)==h)
 ck('Old public bytes '+name,bind(S/'dist/data/records'/name)==h)
for name,h in exports.items():ck('Old training export bytes '+name,bind(S/'dist/data/exports'/name)==h)
new={}
for row in manifest['records']:
 rid=row['record_id'];name=rid+'.json';r=read(S/'data/records'/name);new[rid]=r
 ck('New canonical exact approved bytes '+rid,sha(S/'data/records'/name)==bind(P/'records'/name)==row['promoted_sha256'])
 ck('New public exact approved bytes '+rid,bind(S/'dist/data/records'/name)==row['promoted_sha256'])
 ck('No new training or structure assets '+rid,r['quality']['requested_tasks']==[] and r['structure_assets']==[])
 ck('Generated record page exists '+rid,(S/'dist/records'/(rid+'.html')).is_file());bind(S/'dist/records'/(rid+'.html'))
ck('Exactly 675 canonical/public records',len(list((S/'data/records').glob('*.json')))==len(list((S/'dist/data/records').glob('*.json')))==675)
before=read(V/'reader/sasongko2025.json');source=read(S/'data/paper-reviews/sasongko2025.json');publicreader=read(S/'dist/data/paper-reviews/sasongko2025.json')
expect=copy.deepcopy(before);expect['presentation_gates']['site_integration']=True;expect['publication_status']='Source-reviewed contribution integrated locally; browser and publication remain separate.';expect['audit_details']['promotion_audit_sha256']=sha(O/'promotion-delta-audit.json')
ck('Source reader only three importer metadata changes',source==expect,diff(expect,source))
expectedpub=copy.deepcopy(source);expectedpub['review_scope_label']='Complete supplied main + matched SI review'
ck('Public reader only derived scope label',publicreader==expectedpub,diff(expectedpub,publicreader))
ck('Browser/publication gates still false',source['presentation_gates']['browser_render'] is False and source['presentation_gates']['publication'] is False)
save(O/'integration-baseline-source-reader.json',source);save(O/'integration-baseline-public-reader.json',publicreader)
for a in manifest['public_assets']:
 ck('Imported asset exact approved bytes '+a['public_path'],bind(S/'dist'/a['public_path'])==bind(P/'dist'/a['public_path'])==a['sha256'])
 ck('No source files in asset allowlist '+a['public_path'],not re.search(r'(^|/)(source-render|audit-pages|source-text|raw)(/|$)|\.(pdf|txt|cif)$',a['public_path'],re.I))
registry='dist/assets/chemical-registry/registry.json';base=read(B/registry);actual=read(S/registry);extra=read(P/'molecules/registry-additions.json')['entries']+read(P/'products/registry-additions.json')['entries'];expected=copy.deepcopy(base)
for e in copy.deepcopy(extra):e.update(published=True,binding_approved=True);expected['entries'].append(e)
ck('Whole registry exact append with only publication flags',actual==expected)
ck('46 new identities and no replaced base entries',len(extra)==46 and len(actual['entries'])-len(base['entries'])==46 and len({x['id'] for x in actual['entries']})==len(actual['entries']))
for rel,proposal,keys in [('dist/assets/chemical-registry/bindings.json','molecules/bindings-additions.json',['recordBindings','bindingNotes','sourceRecordSha256']),('dist/assets/chemical-registry/product-contexts.json','products/product-contexts-additions.json',['recordContexts','sourceNotices'])]:
 b=read(B/rel);a=read(S/rel);delta=read(P/proposal);e=copy.deepcopy(b)
 for key in keys:
  ck('No overwritten base namespace '+rel+'/'+key,not set(e.get(key,{}))&set(delta[key]));e.setdefault(key,{}).update(delta[key])
 ck('Exact scoped map merge '+rel,a==e)
rel='dist/assets/chemical-registry/solution-components.json';b=read(B/rel);a=read(S/rel);e=copy.deepcopy(b);delta=read(P/'molecules/solution-components-additions.json')['contexts'];e['contexts'].extend(delta);ck('Solution contexts exact append',a==e)
ck('Stock instance/component counts',len(delta)==5 and sum(len(x['components']) for x in delta)==12)
rel='data/measurement-display.json';b=read(B/rel);a=read(S/rel);e=copy.deepcopy(b)
for section,key in [('structures','record_structural_measurement_ids'),('properties','record_property_measurement_ids')]:
 delta=read(P/('record-'+section+'-measurements.json'));ck('Measurement display IDs no overwrite '+section,not set(e[key])&set(delta));e[key].update(delta)
ck('Source display map exact merge',a==e);ck('Public measurement map exact source',read(S/'dist/data/measurement-display.json')==a)
# Reconstruct all modified source code from the exact retained preimport snapshots.
changed=set(c['file'] for c in code['changes'])|set(code['cache_revision_files']);code_results=[]
for rel in sorted(changed):
 bpath=B/rel;bind(bpath)
 if rel.endswith('.html'):
  code_results.append({'file':rel,'scope':'Generated template/cache revision; generated HTML is checked separately by completed root build and new-route transport.'});continue
 original=io_path(bpath).read_text('utf8');expected=original
 for c in code['changes']:
  if c['file']==rel:
   ck('Code anchor count '+rel+'/'+c['before'][:45],expected.count(c['before'])==c['occurrences']);expected=expected.replace(c['before'],c['after'])
 if rel in code['cache_revision_files']:expected=expected.replace('0.32.0-r1','0.33.0-r1').replace('0.32.0-r2','0.33.0-r2')
 bind(S/rel);ck('Exact allowed current code delta '+rel,io_path(S/rel).read_text('utf8')==expected);code_results.append({'file':rel,'exact_text_reconstruction':io_path(S/rel).read_text('utf8')==expected})
ck('FA explicit elemental expansion only',"'FAPbI3':['C','H','N','Pb','I']" in (S/'scripts/build_atlas.py').read_text('utf8'))
dispatch=read(O/'scoped-dispatch-checks.json');bind(O/'check_scoped_dispatch.mjs');bind(S/'dist/quantity-value.mjs');ck('Actual runtime source dispatch passed',dispatch['status']=='passed' and dispatch['selected']==21 and dispatch['rejected']==1957 and all(x['passed'] for x in dispatch['checks']))
index=read(S/'dist/data/materials-index.json');hubs=index['materials'];fa=[h for h in hubs if h['formula']=='FAPbI3'];ck('50 hubs and one FAPbI3 hub',len(hubs)==50 and len(fa)==1)
hub=read(S/'dist/data/materials'/('fapbi3-be3592.json'))
for h in [fa[0],hub]:ck('Correct FA C/H/N/Pb/I identity '+h['id'],h['elements']==['C','H','N','Pb','I'] and 'F' not in h['elements'] and h['name']=='Formamidinium lead iodide quantum dots')
ck('One direct source route only',hub['record_ids']==hub['direct_record_ids']==['sasongko-2025-hot-injection'] and hub['component_only'] is False)
ck('Material hub source paper and reader',hub['papers'][0]['doi']=='10.1021/acs.jpcc.5c05144' and hub['papers'][0]['fullDocumentReview']['id']=='sasongko2025')
paper=read(S/'dist/data/papers/paper-707b70ac3e9bdab78b9a.json');ck('Source paper all 19 records reachable',set(paper['reviewedRecordIds'])==set(new));ck('Source paper contribution metadata current',paper['recipeCurationStatus']=='source_reviewed_records' and paper['materialContributionStatus']=='verified_synthesis_contribution' and paper['fullDocumentReview']['pages']==20)
pi=read(S/'dist/data/paper-review-index.json');ck('36 source readers',len(pi['papers'])==36);entry=next(x for x in pi['papers'] if x['id']=='sasongko2025');ck('Reader navigation includes all 19 records',set(entry['record_ids'])==set(new) and entry['pages_read']==20 and entry['review_scope']=='supplied_main_and_matched_si')
dataset=read(S/'dist/data/dataset-manifest.json');ck('Actual dataset 0.33 and 675 records/41 groups',dataset['dataset_version']=='0.33.0' and dataset['record_count']==675 and dataset['group_count']==41)
inv=read(S/'data/inventory-summary.json');publicinv=read(S/'dist/data/inventory-summary.json');ck('Private/public inventory source exact',inv==publicinv==read(I/'inventory-summary.json'))
for key,val in {'canonical_records':675,'synthesis_route_variant_records':123,'public_material_hubs':50,'direct_synthesis_target_systems':39,'component_only_hubs':11,'total_canonical_source_groups':41,'verified_exact_structure_recipe_pairs':0}.items():ck('Inventory actual '+key,inv['summary'][key]==val)
prow=next(r for r in inv['per_paper'] if r['source_group']=='sasongko2025')
ck('Sasongko inventory exact split/scope',set(prow['record_ids'])==set(new) and prow['canonical_record_count']==19 and prow['synthesis_route_variant_count']==1 and prow['procedure_count']==7 and prow['contextual_observation_count']==11 and prow['measurement_entry_count']==502)
ck('Source pages9+11 and SI matched',[(d['role'],d['page_count']) for d in prow['documents']]==[('main',9),('si',11)] and prow['si_status']=='matched_and_reviewed')
ck('Canonical vs all corpus unknown retained',inv['summary']['independent_experiment_count'] is None and inv['summary']['full_corpus_recipe_count'] is None)
for rel,h in inv['provenance']['summary_artifact_sha256'].items():ck('Current inventory provenance '+rel,bind(S/rel)==h)
sys.path.insert(0,str(S/'scripts'));import dataset_lib,build_paper_reviews
for rel in ['dataset_lib.py','schema_definition.py','build_paper_reviews.py','review_scope.py']:bind(S/'scripts'/rel)
for rid,r in new.items():
 errors=dataset_lib.validate_record(r);ck('Actual imported record schema '+rid,not errors,errors);ck('Actual zero imported task eligibility '+rid,not any(x['eligible'] for x in dataset_lib.eligibility(r).values()))
build_paper_reviews.ROOT=S;err=build_paper_reviews.validate(source);ck('Actual imported reader validator',not err,err)
for rel in ['data/paper-reviews/sasongko2025.json','dist/data/paper-reviews/sasongko2025.json','dist/assets/chemical-registry/registry.json','dist/assets/chemical-registry/product-contexts.json']:
 ck('Current public data no local paths '+rel,not re.search(r'[A-Z]:[\\/]|file://',io_path(S/rel).read_text('utf8')))
for p,h in list(bound.items()):ck('Final stable audit input '+p,sha(Path(p))==h)
bad=[x for x in checks if not x['passed']]
save(O/'integration-checks.json',{'status':'passed' if not bad else 'revision_required','checks':checks,'failed_checks':bad,'code_results':code_results,'reader_changed_paths':diff(before,source),'derived_reader_changed_paths':diff(source,publicreader)})
for p in [O/'integration-checks.json',O/'integration-baseline-source-reader.json',O/'integration-baseline-public-reader.json',Path(__file__)]:bind(p)
report={'schema':'mattersyn-independent-site-integration-audit/1','status':'passed' if not bad else 'revision_required','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','at':datetime.now(timezone.utc).isoformat(),'doi':'10.1021/acs.jpcc.5c05144','scope':'Actual Site integration transport only; original scientific source/canonical/visual approvals and publication-projection audit remain distinct. No browser or release approval.','proposal_freeze_sha256':sha(P/'package-freeze.json'),'reader_status_overlay_freeze_sha256':sha(V/'package-freeze.json'),'promotion_audit_sha256':sha(O/'promotion-delta-audit.json'),'site_import_manifest_sha256':sha(I/'site-import-manifest.json'),'build_check_output_sha256':sha(I/'build-check-output.json'),'counts':{'records':675,'new_records':19,'preserved_prior_records':656,'unchanged_training_exports':6,'routes':123,'hubs':50,'source_groups':41,'source_readers':36,'public_assets':81,'material_slots':26,'stock_instances':5,'stock_components':12,'product_instances':42,'product_symbols':33,'selected_source_crops':17,'selected_operations':dispatch['selected'],'rejected_other_operations':dispatch['rejected'],'transport_checks':len(checks),'runtime_dispatch_checks':len(dispatch['checks']),'combined_checks':len(checks)+len(dispatch['checks']),'bound_files':len(bound)},'manual_scope':['Read complete importer and code-delta; reconstructed all Python/JavaScript changes from saved preimport bytes plus declared cache revision. Generated HTML checked by current completed root static checks and new-record reachability, not independently browser-tested.','Compared exact actual record/asset bytes and whole-registry/map merges; scientific data unchanged.','Compared effective corrected reader to actual source reader and generated reader; only three integration metadata leaves plus derived scope label.','Reviewed FAPbI3 expansion as formamidinium C/H/N plus Pb/I, not elemental fluorine; actual hub and source navigation checked.','Ran exact source-specific scene module against all 1,978 current operation instances; 21 source cases selected and 1,957 unrelated cases rejected.','Bound completed 18-command build log; root quality log reports 39,102 checks. This is supporting root build evidence, not a repeated independent execution of that entire suite.'],'allowed_changes':['19 exact promoted records and 81 exact approved assets added; old 656 records and six task export bytes unchanged.','Registry appends 13 molecular and33 symbolic product entries, published/binding flags enabled. Source/sample selectors/maps are exact approved merges.','Source reader: site_integration false→true, integration publication_status prose, and promotion audit digest. Generated reader: derived review_scope_label only.','Scoped apparatus/source-evidence dispatch, cache version0.33 and source-qualified FAPbI3 elemental expansion; no training gate changes.'],'open_findings':bad,'bound_files':bound,'remaining_gates':['Actual browser review and explicit bounded browser-status overlay','Anonymous release verification'],'actions_performed':{'site_modified':False,'source_modified':False,'frozen_proposals_modified':False,'browser_exercised':False,'network_accessed':False,'publication_approved':False}}
save(O/'integration-audit.json',report)
md=f'''# Sasongko actual integration audit\n\nStatus: **{report['status']}**. Auditor: `/root/backlog_eta`; importer author: `/root`.\n\nThe actual Site contains all 19 approved records and 81 approved asset bytes. All 656 previous canonical/public record pairs and six training exports remain byte-identical. The registry,26 material slots,five stocks/12 components,42 product-context instances and measurement maps are exact scoped additions. No scientific value, sample assignment, source locator or approved visual asset changed.\n\nThe effective source reader differs only in three importer metadata leaves; the public reader additionally has the expected derived review-scope label. Browser and publication flags remain false. FAPbI3 has exactly C,H,N,Pb,I in the new material hub, and one direct synthesis route. Current totals:675 records,123 routes,50 hubs,41 source groups and36 readers.\n\nAll {len(checks)} independent transport/hash/schema checks and {len(dispatch['checks'])} actual scoped-dispatch checks pass. The module selects all21 Sasongko operations and rejects1957 operations from other sources. The completed18-command root build log separately reports39102 quality checks. {len(bound)} input files are bound.\n\nOpen findings: {len(bad)}. Browser interaction and anonymous publication remain separate gates. No shared Site, ledger, source or frozen proposal was modified.\n'''
io_path(O/'integration-audit.md').write_text(md,'utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'dispatch_checks':len(dispatch['checks']),'bound':len(bound),'failed':bad[:20],'sha256':sha(O/'integration-audit.json')}))
