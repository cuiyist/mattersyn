"""Separate local readiness, anonymous science publication, and progress delivery."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';MON=N.parents[2];M=N.parents[4];S=M/'recipe-atlas'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text('utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def memory(t):
 p=M/'MEMORY.md';p.write_text(t+'\n\n'+p.read_text('utf8'),'utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);stage=ap.parse_args().stage;now=datetime.now(timezone.utc).isoformat()
ia=N/'site-integration-independent-audit/integration-transport-audit.json';ba=O/'browser-validation.json'
assert all(read(p)['status']=='passed' for p in [ia,ba])
assert read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.29.0'
inv=read(S/'data/inventory-summary.json')['summary'];assert inv['canonical_records']==586 and inv['synthesis_route_variant_records']==114 and inv['verified_exact_structure_recipe_pairs']==0
if stage=='prepare':
 assert read(N/'site-integration-independent-audit/browser-gate-delta-audit.json')['status']=='passed'
 assert read(N/'site-integration-independent-audit/conditional-publication-rule-audit.json')['status']=='passed_conditionally'
 prior=O/'prior-latest-publication.json';assert not prior.exists();save(prior,read(MON/'latest-publication.json'))
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.cgd.9b01519',note='Complete supplied-main contribution integrated after separate source/data/visual audits and actual browser checks. Declared SI remains unverified. Anonymous publication pending.',data={'current_step':'Publishing independently passed Sommer contribution','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones={'audit':{'status':'complete','evidence':[str(ia),str(N/'source-independent-audit/independent-audit-v2.json')],'note':'Separate source, canonical, molecular, apparatus, product and transport audits passed; SI remains unlocated/unverified.'},'integrate':{'status':'complete','evidence':[str(ia),str(ba),str(O/'build-check-output.json')],'note':'31 stage controls,168 condition rows,14figure enlargement controls and narrow layouts checked. Prior567records/training exports preserved.'}})
 memory(f'''## 2026-09-20 — Sommer integrated; anonymous publication pending

Saved {now}. Candidate dataset0.29.0:586records,114routes/variants,47hubs(36direct11component),37sourcegroups32formalreaders. Sommer contributes19records(3routes,9procedures,7observations),31illustrated stages,20selected source crops,28chemical identities/sevenstocks and77symbolic phase-component mappings. Independent transport audit {sha(ia)}; actual browser receipt {sha(ba)}. All567older records and training exports unchanged. The11-page supplied main is fully reviewed; declared SI remains locally unlocated/unverified. No exact atomic structure–recipe pair is admitted.

Public science remains0.28.0 until exact anonymous verification. Matuhina2023 CsMnCl3 main13+SI13 extraction and independent audit continue in parallel. Publication batches only passed contributions; no downloads or paid processing. Original PDFs/SI/raw text/full pages remain local. Reuse frozen reviews rather than restarting them.''')
 print('Release prepared; no live-publication claim.')
else:
 v=read(M/'research-assets/github-public-delivery-verification.json');plan=read(O/'release-endpoints.json')
 assert v['status']=='passed' and v['build']['status']=='built' and v['site_commit']==v['build']['commit'] and v['expected_citation_count']==37
 assert len(v['anonymous']['checks'])==94 and {c['path'] for c in v['anonymous']['checks']}==set(plan['paths']) and all(c['matches_checked_local_bytes'] for c in v['anonymous']['checks'])
 proof=O/('science-release-anonymous-verification.json' if stage=='verify' else 'progress-release-anonymous-verification.json')
 if proof.exists():assert read(proof)==v,'Never replace immutable delivery proof'
 else:save(proof,v)
 if stage=='verify':
  assert read(N/'source-independent-audit/independent-audit-v2.json')['status']=='passed' and read(N/'canonical-reader-independent-audit/independent-audit-v2.json')['status']=='passed'
  monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.cgd.9b01519',note='Bind the completed supplied-main reading and extraction to the current generation before terminal closure.',milestones={'read':{'status':'complete','evidence':[str(N/'source-independent-audit/independent-audit-v2.json'),str(N/'package-freeze.json')],'note':'All 11 supplied main pages read and independently checked; SI remains locally unlocated/unverified.'},'extract':{'status':'complete','evidence':[str(N/'canonical-reader-independent-audit/independent-audit-v2.json'),str(N/'canonical-proposal/v2/package-manifest.json')],'note':'Separate passed source/canonical reviews cover 19 records,357 reader items and222 table cells; unresolved claims remain explicit.'}})
  monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.cgd.9b01519',status='complete',note='Supplied-main contribution published after separate audits/browser review; all94anonymous endpoints and both37-citation READMEs match. SI remains explicitly unverified.',data={'current_step':'Published and anonymously verified within supplied-main scope','publication':{'dataset_version':'0.29.0','site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Exact deployed commit/public bytes verified; missing SI stays unverified and future SI changes reopen scope.'}})
  release=read(O/'prior-latest-publication.json')
  release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.29.0',published_at=v['build']['updated_at'],dataset_version='0.29.0',record_count=586,synthesis_route_count=114,material_hub_count=47,direct_material_hub_count=36,component_material_hub_count=11,public_source_group_count=37,formal_source_reader_count=32,exact_structure_recipe_count=0,new_source_ids=['sommer2020'],scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Sommer complete supplied-main contribution, SI unverified:3routes,9procedures,7observations,31stage illustrations,20selected original crops and77sample-bound symbolic phase components. Previous567records/training unchanged.',progress_only_update=False)
  release.pop('publication_status_delta_audit',None)
  ed=read(MON/'public-progress-editorial.json');ed['current_work']=[x for x in ed['current_work'] if x['short_label']!='Sommer et al. (2020)']
  ed['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Sommer ZnAl₂O₄ contribution published and anonymously verified: three laboratory routes, 31 illustrated stages, 20 selected original crops and sample-specific phase outcomes. Complete supplied main reviewed; SI unverified. Dataset 0.29.0 contains 586 records and 114 routes/variants. Matuhina CsMnCl₃ main/SI extraction and independent audit continue.'})
  ed['estimate']['current_batch']='Sommer supplied-main contribution published; its declared SI remains unverified. Matuhina CsMnCl₃ main/SI extraction and separate independent audit continue. Whole-corpus throughput and finish date remain unvalidated.'
  save(MON/'public-progress-editorial.json',ed)
 else:
  release=read(MON/'latest-publication.json');assert release['dataset_version']=='0.29.0'
  release.update(progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Sommer verified-publication labels and current review progress; scientific dataset0.29.0 unchanged.')
 release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
 release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous'];release['integration_checks']={p.relative_to(M).as_posix():sha(p) for p in [ia,ba,O/'build-check-output.json']}
 for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
 memory(f'''## 2026-09-20 — Sommer {'science release' if stage=='verify' else 'progress release'} verified

Saved {now}. Website commit {v['site_commit']}, built {v['build']['updated_at']}:94anonymous endpoints and both37-source README citation lists verified. Dataset0.29.0 has586records,114synthesis routes/variants,47material/component hubs,37sourcegroups and32formal readers. Scientific dataset commit {release['scientific_dataset_commit']} remains separate from progress-only releases. Source reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=sommer2020 . All prior567records/training exports unchanged; exact structure–recipe pairs0.

Sommer is closed within complete supplied-main scope after reading, extraction, separate audits, browser review and verified publication. Declared SI remains unlocated/unverified; new SI reopens scope. Source conflicts, unknown compositions and non-digitized figures stay explicit. Matuhina2023 CsMnCl3 main/SI review continues at batches/20260920-rolling-pipeline/acsanm.2c04342, Backlog author and Norberg independent auditor. Existing fixed-cutoff evidence priority, separate later arrivals, one heartbeat, public filtered project/site, no new downloads and deferred API pilot persist. A subsequent project commit stores this proof and memory; it does not alter the verified scientific site.''')
 print(json.dumps({'stage':stage,'dataset':'0.29.0','site_commit':v['site_commit'],'science_commit':release['scientific_dataset_commit'],'status':'published_verified'}))
