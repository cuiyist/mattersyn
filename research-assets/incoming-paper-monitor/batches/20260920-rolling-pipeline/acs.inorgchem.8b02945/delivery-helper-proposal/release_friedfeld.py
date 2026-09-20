"""Root-only prepare/verified-science/verified-progress receipts for Friedfeld."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
A=Path(__file__).resolve().parent
if A.name=='delivery-helper-proposal':A=A.parent
O=A/'site-integration-proposal';MON=A.parents[2];M=A.parents[4];S=M/'recipe-atlas'
sys.dont_write_bytecode=True;sys.path.insert(0,str(MON))
import monitor
from release_support import read,sha,assert_local_candidate,validate_delivery,GID,VERSION,SID
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def memory(text):
 p=M/'MEMORY.md';p.write_text(text+'\n\n'+p.read_text('utf8'),'utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);stage=ap.parse_args().stage;now=datetime.now(timezone.utc).isoformat()
ia=A/'site-integration-independent-audit/integration-audit.json';ba=O/'browser-validation.json'
assert all(read(p)['status']=='passed'for p in[ia,ba])
summary=assert_local_candidate(A);plan=read(O/'release-endpoints.json')
assert plan['source_id']==SID and plan['dataset_version']==VERSION and plan['count']==547
pm=read(O/'v1/promotion-manifest.json')
assert sha(O/'v1/promotion-manifest.json')==plan['source_projection_manifest_sha256']
for rel,h in pm['source_audits'].items():assert sha(A/rel)==h and read(A/rel)['status']=='passed'
assert all(x['exit_code']==0 for x in read(O/'build-check-output.json')['runs'])
reader=read(S/'data/paper-reviews/friedfeld2019.json');assert reader['presentation_gates']['browser_render']is True
assert reader['presentation_gates']['exact_product_atomic_structure_binding']is False
if stage=='prepare':
 assert read(A/'site-integration-independent-audit/browser-gate-delta-audit.json')['status']=='passed'
 assert reader['presentation_gates']['publication']is False
 prior=O/'prior-latest-publication.json';assert not prior.exists();save(prior,read(MON/'latest-publication.json'))
 prep=O/'release-preparation.json';assert not prep.exists()
 save(prep,{'status':'prepared_unpublished','at':now,'dataset_version':VERSION,'source_id':SID,'reader_sha256':sha(S/'data/paper-reviews/friedfeld2019.json'),'endpoint_plan_sha256':sha(O/'release-endpoints.json'),'finalizer_script_sha256':sha(A/'finalize_reader_publication.py'),'release_support_sha256':sha(A/'release_support.py'),'integration_audit_sha256':sha(ia),'browser_audit_sha256':sha(A/'site-integration-independent-audit/browser-gate-delta-audit.json'),'publication_gate':False})
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=GID,note='Friedfeld supplied main/SI integrated after distinct source, canonical and visual reviews and integrated browser checks. Anonymous public delivery remains pending.',data={'current_step':'Publishing reviewed Friedfeld contribution','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones={'audit':{'status':'complete','evidence':[str(ia),str(A/'source-independent-audit/independent-audit-v2.json')],'note':'Distinct source, canonical, molecule/binding, apparatus, product and integrated transport reviews passed.'},'integrate':{'status':'complete','evidence':[str(ia),str(ba),str(O/'build-check-output.json')],'note':'30 records and 58 stage illustrations integrated. All 626 prior records and six training-export files retain their exact bytes.'}})
 memory(f'''## 2026-09-20 — Friedfeld integrated; anonymous publication pending

Saved {now}. Candidate dataset 0.32.0 contains 656 records, 122 routes/variants, 49 material/component hubs (38 direct and 11 component), 40 source groups and 35 readers. Friedfeld adds 30 records: four conversion routes, 15 supporting procedures and 11 observations; 58 illustrated operation instances, 51 selected original crops, 39 chemical references, 77 material bindings, eight stock instances and 88 symbolic product contexts. Its supplied main 8 + SI 25 pages passed distinct scientific reviews. InP cluster and QD contexts, labeled ligand preparation, conversion variants, negative controls, fitted kinetics and source conflicts remain separated. No new training admission or exact atomic pair; all 626 prior record bytes and six training exports unchanged. Scientific public release remains 0.31.0 until anonymous verification passes. Continue Sasongko from its current immutable private checkpoint; its publication is not implied. Fixed-cutoff work takes priority and genuinely new arrivals remain separate. Original papers, SI, full text and complete-page renders stay local. No downloads or paid runs.''')
 print('Friedfeld prepared; public verification pending.');raise SystemExit
v=validate_delivery(A,read(M/'research-assets/github-public-delivery-verification.json'),plan)
proof=O/('science-release-anonymous-verification.json'if stage=='verify'else'progress-release-anonymous-verification.json')
if proof.exists():assert read(proof)==v,'A different immutable receipt already exists; preserve it and version the new proof.'
else:save(proof,v)
if stage=='verify':
 assert not reader['presentation_gates']['publication'],'Science receipt must precede publication-label mutation.'
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=GID,status='complete',note='Friedfeld complete supplied main/SI contribution independently reviewed and published; exact anonymous endpoint bytes, deployed commit and 40-citation READMEs verified.',data={'current_step':'Published and anonymously verified within supplied main/SI scope','publication':{'dataset_version':VERSION,'site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Verified deployed commit/public bytes. Changed source evidence reopens this scope.'}})
 release=read(O/'prior-latest-publication.json')
 release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.32.0',published_at=v['build']['updated_at'],dataset_version=VERSION,record_count=656,synthesis_route_count=122,material_hub_count=49,direct_material_hub_count=38,component_material_hub_count=11,public_source_group_count=40,formal_source_reader_count=35,exact_structure_recipe_count=0,new_source_ids=[SID],scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Friedfeld supplied main8 + SI25: 30 records, 58 stage illustrations, 51 selected original crops, 39 chemical identities and 88 source-scoped symbolic product contexts. All 626 prior records and six training-export bytes unchanged.',progress_only_update=False)
 release.pop('publication_status_delta_audit',None)
 editorial=read(MON/'public-progress-editorial.json');editorial['current_work']=[x for x in editorial['current_work']if x.get('short_label')!='Friedfeld et al. (2019)']
 editorial['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Friedfeld InP cluster-to-QD contribution published and anonymously verified: four conversion routes, 58 illustrated operations and 51 selected original crops. Labeled ligand synthesis, kinetics and source conflicts retain their own scope. Dataset 0.32.0 has 656 records and 122 routes/variants; no new training admission or exact atomic pair.'})
 editorial['estimate']['current_batch']='Friedfeld supplied main/SI contribution is published. Continue the immutable Sasongko DOI 10.1021/acs.jpcc.5c05144 checkpoint and fixed-cutoff queue. Whole-corpus throughput and completion date remain unvalidated.'
 save(MON/'public-progress-editorial.json',editorial)
else:
 release=read(MON/'latest-publication.json');assert release['dataset_version']==VERSION and release['scientific_dataset_commit']
 assert reader['presentation_gates']['publication']is True and read(O/'publication-label-delta.json')['status']=='applied_after_verified_release'
 release.update(progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Verified Friedfeld publication labels and current review progress; scientific dataset 0.32.0 unchanged.')
release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous'];release['integration_checks']={p.relative_to(M).as_posix():sha(p)for p in[ia,ba,O/'build-check-output.json']}
for p in[MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
memory(f'''## 2026-09-20 — Friedfeld {'science'if stage=='verify'else'progress'} release verified

Saved {now}. Public website commit {v['site_commit']}, built {v['build']['updated_at']}. All 547 anonymous public endpoints, 18 additional withheld source-page paths and both 40-source citation READMEs passed verification. Dataset 0.32.0 contains 656 records, 122 routes/variants, 49 hubs (38 direct + 11 component), 40 source groups and 35 formal readers. Scientific commit {release['scientific_dataset_commit']} is separate from progress-only delivery. Reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=friedfeld2019 . Prior 626 records and six training-export bytes unchanged; exact structure–recipe pairs remain zero.

Friedfeld is closed within supplied main8 + SI25 after distinct reviews and verified publication. No new InP QD atomic-coordinate pairing is asserted; current QDs, cited cluster/precursor structures, ligand preparation, kinetic fits and source conflicts retain distinct roles. Resume Sasongko DOI10.1021/acs.jpcc.5c05144 from its actual saved private audit status. Fixed-cutoff priority and separate later arrivals remain in effect. Original source documents/full text/full-page images stay local. No paid pilot or source download was run. Later project commits may record this proof without changing scientific site content.''')
print(json.dumps({'stage':stage,'status':'published_verified','dataset':VERSION,'site_commit':v['site_commit'],'science_commit':release['scientific_dataset_commit']}))
