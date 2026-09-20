"""Root-executed Pati release checkpoint; no live claim before exact proof."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
A=Path(__file__).resolve().parent
if A.name=='delivery-helper-proposal':A=A.parent
O=A/'site-integration-proposal';MON=A.parents[2];M=A.parents[4];S=M/'recipe-atlas'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def memory(text):
 p=M/'MEMORY.md';p.write_text(text+'\n\n'+p.read_text('utf8'),'utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);stage=ap.parse_args().stage;now=datetime.now(timezone.utc).isoformat()
ia=A/'site-integration-independent-audit/integration-transport-audit.json';ba=O/'browser-validation.json'
assert all(read(p)['status']=='passed'for p in [ia,ba])
assert read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.31.0'
summary=read(S/'data/inventory-summary.json')['summary']
assert summary['canonical_records']==626 and summary['synthesis_route_variant_records']==118 and summary['total_canonical_source_groups']==39 and summary['verified_exact_structure_recipe_pairs']==0
gid='10.1021_la8031286';plan=read(O/'release-endpoints.json')
assert plan['source_id']=='pati2009'and plan['dataset_version']=='0.31.0'and plan['count']==len(plan['paths'])==324
if stage=='prepare':
 assert read(A/'site-integration-independent-audit/browser-gate-delta-audit.json')['status']=='passed'
 assert read(A/'site-integration-independent-audit/conditional-publication-rule-audit.json')['status']=='passed_conditionally'
 prior=O/'prior-latest-publication.json';assert not prior.exists();save(prior,read(MON/'latest-publication.json'))
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=gid,note='Pati supplied main/SI contribution integrated after separate source, data and visual audits and actual browser checks; anonymous release remains pending.',data={'current_step':'Publishing independently reviewed Pati contribution','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones={'audit':{'status':'complete','evidence':[str(ia),str(A/'source-independent-audit/independent-audit-v1.json')],'note':'Separate source, canonical, molecular, apparatus, product-context and transport audits passed.'},'integrate':{'status':'complete','evidence':[str(ia),str(ba),str(O/'build-check-output.json')],'note':'35 operation instances and source-specific specimens/figures integrated. Existing607records and six training exports preserved.'}})
 memory(f'''## 2026-09-20 — Pati integrated; anonymous publication pending

Saved {now}. Candidate dataset0.31.0 contains626records and118routes/variants. Pati2009 adds19records: three alcohol-specific precipitation routes, eleven procedures and five observations;35illustrated operation instances,20original selected crops,20chemical identities/sixstocks and39symbolic product contexts. Supplied main4+SI4 and separate source/data/visual/transport/browser audits passed. As-prepared whole composition remains unresolved despite local CeO2 microscopy. DLS size-metric and XPS exposure histories remain distinct; source conflicts preserved. No atomic pair or new training admission. Prior607record bytes and six training-export files are unchanged. Scientific public release remains0.30.0 until exact anonymous verification. Next admitted source is Friedfeld DOI10.1021/acs.inorgchem.8b02945; resume its current immutable checkpoint rather than assume a completion status. Original PDFs/SI/full text/full pages remain local. No download or paid API run.''')
 print('Pati release prepared; no live-publication claim.');raise SystemExit
v=read(M/'research-assets/github-public-delivery-verification.json')
assert v['status']=='passed'and v['build']['status']=='built'and v['site_commit']==v['build']['commit']and v['expected_citation_count']==39
assert v['anonymous']['authenticated']is False and v['anonymous']['cookies_used']is False
checks=v['anonymous']['checks'];assert len(checks)==324 and {x['path']for x in checks}==set(plan['paths'])
assert all(x['http_status']==200 and x['matches_checked_local_bytes']and x['redirect_stays_on_site']for x in checks)
assert len(v['anonymous']['additional_withheld_paths'])==16 and {x['path']for x in v['anonymous']['additional_withheld_paths']}==set(plan['additional_withheld_paths'])
assert all(x['http_status']==404 for x in v['anonymous']['additional_withheld_paths'])and v['anonymous']['excluded_complete_page_http_status']==404
assert len(v['repositories'])==2 and {x['name']for x in v['repositories']}=={'mattersyn','mattersyn-site'}and all(x['public']and x['commit_matches']and x['anonymous_status']==200 for x in v['repositories'])
assert len(v['anonymous']['readmes'])==2 and {x['repository']for x in v['anonymous']['readmes']}=={'mattersyn','mattersyn-site'}and all(x['http_status']==200 and x['bytes_match']and x['doi_links']==39 for x in v['anonymous']['readmes'])
assert next(x['sha256']for x in checks if x['path']=='data/dataset-manifest.json')==sha(S/'dist/data/dataset-manifest.json')
proof=O/('science-release-anonymous-verification.json'if stage=='verify'else'progress-release-anonymous-verification.json')
if proof.exists():assert read(proof)==v
else:save(proof,v)
if stage=='verify':
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=gid,status='complete',note='Pati complete supplied main/SI contribution independently reviewed and published; exact anonymous public bytes and39-citation READMEs verified.',data={'current_step':'Published and anonymously verified within supplied main/SI scope','publication':{'dataset_version':'0.31.0','site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Exact deployed commit/public bytes verified; changed source generation reopens this scope.'}})
 release=read(O/'prior-latest-publication.json');reviews=read(S/'dist/data/paper-review-index.json')['papers']
 release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.31.0',published_at=v['build']['updated_at'],dataset_version='0.31.0',record_count=626,synthesis_route_count=118,material_hub_count=summary['public_material_hubs'],direct_material_hub_count=summary['direct_synthesis_target_systems'],component_material_hub_count=summary['component_only_hubs'],public_source_group_count=39,formal_source_reader_count=len(reviews),exact_structure_recipe_count=0,new_source_ids=['pati2009'],scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Pati complete supplied main4+SI4 contribution:19records,35stage illustrations,20selected original crops and39source-scoped symbolic product contexts. Prior607records and six training export files unchanged.',progress_only_update=False)
 release.pop('publication_status_delta_audit',None)
 editorial=read(MON/'public-progress-editorial.json');editorial['current_work']=[x for x in editorial['current_work']if x.get('short_label')!='Pati et al. (2009)']
 editorial['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Pati CeO2-related precipitation contribution published and anonymously verified: three separate alcohol routes,35illustrated operation instances and20original source crops. Local CeO2 microscopy, unresolved as-prepared bulk composition, calcined powder and XPS exposure contexts remain distinct. Dataset0.31.0 contains626records and118routes/variants; no new training admission or exact atomic pair.'})
 editorial['estimate']['current_batch']='Pati supplied main/SI contribution is published. Continue the separate Friedfeld DOI10.1021/acs.inorgchem.8b02945 checkpoint and current fixed-cutoff queue. Whole-corpus throughput and finish date remain unvalidated.'
 save(MON/'public-progress-editorial.json',editorial)
else:
 release=read(MON/'latest-publication.json');assert release['dataset_version']=='0.31.0'
 release.update(progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Pati verified-publication labels and current review progress; scientific dataset0.31.0 unchanged.')
release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous'];release['integration_checks']={p.relative_to(M).as_posix():sha(p)for p in [ia,ba,O/'build-check-output.json']}
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
memory(f'''## 2026-09-20 — Pati {'science'if stage=='verify'else'progress'} release verified

Saved {now}. Public website commit {v['site_commit']}, built {v['build']['updated_at']};324anonymous endpoints,16additional withheld source-page paths and both39-source README citation lists verified. Dataset0.31.0 has626records,118routes/variants,{summary['public_material_hubs']}material/component hubs and39sourcegroups. Scientific commit {release['scientific_dataset_commit']} remains separate from progress-only delivery. Reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=pati2009 . Prior607records and six training-export bytes unchanged; exact structure-recipe pairs0.

Pati closed within supplied main4+SI4 scope after separate audits and verified publication. Whole as-prepared composition, beam-history surface fits, missing atomic coordinates and source formula/size-label conflicts remain explicit. Next admitted source Friedfeld DOI10.1021/acs.inorgchem.8b02945 has a separate rolling-pipeline folder and intake/admission20260920T133256Z; resume its actual saved status. Fixed-cutoff evidence priority, separate new arrivals, source-excluding public projection and no paid pilot/downloads persist. A subsequent project commit may record this proof without changing the scientific site.''')
print(json.dumps({'stage':stage,'status':'published_verified','dataset':'0.31.0','site_commit':v['site_commit'],'science_commit':release['scientific_dataset_commit']}))
