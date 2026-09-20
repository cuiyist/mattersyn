"""Record the individually audited contribution; never infer live publication."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
G=Path(__file__).resolve().parent;O=G/'site-integration-proposal';MON=G.parents[2];M=G.parents[4];S=M/'recipe-atlas'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def memory(t):
 p=M/'MEMORY.md';p.write_text(t+'\n\n'+p.read_text(encoding='utf8'),encoding='utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);args=ap.parse_args();now=datetime.now(timezone.utc).isoformat()
ia=G/'site-integration-independent-audit/integration-transport-audit.json';ba=O/'browser-validation.json'
assert all(read(p)['status']=='passed' for p in [ia,ba])
assert read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.28.0'
inv=read(S/'data/inventory-summary.json')['summary']
assert inv['canonical_records']==567 and inv['synthesis_route_variant_records']==111 and inv['verified_exact_structure_recipe_pairs']==0
if args.stage=='prepare':
 prior=O/'prior-latest-publication.json';assert not prior.exists();save(prior,read(MON/'latest-publication.json'))
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_ja212032q',note='Complete supplied main/SI contribution integrated after separate scientific and browser audits; anonymous publication verification pending.',data={'current_step':'Publishing independently passed Ghosh contribution','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones={
  'audit':{'status':'complete','evidence':[str(ia),str(G/'source-independent-audit/independent-audit-v2.json')],'note':'Separate source, canonical, molecular, apparatus, metadata, product-context and transport audits passed.'},
  'integrate':{'status':'complete','evidence':[str(ia),str(ba),str(O/'build-check-output.json')],'note':'All 33 stage controls, 183 condition/note rows, selected source figures, chemical/stock references and responsive rendering checked. Previous 546 records and training eligibility preserved.'}})
 memory(f'''## 2026-09-20 — Ghosh integrated; public verification pending

Saved {now}. Dataset candidate 0.28.0 contains 567 records and 111 routes/variants. Ghosh contributes 21 records: two synthesis routes, three variants, ten procedures and six observations. All supplied 10 main and 9 SI pages, 272 table cells, 36 selected crops, 325 reader items, 33 operation scenes, 25 chemical identities and 45 symbolic product contexts have distinct audits. Integration audit {sha(ia)}; actual-browser receipt {sha(ba)}. All 546 older canonical records and training exports remain unchanged. No atomic product structure or exact structure–recipe pair admitted.

Public science remains 0.27.0 until exact anonymous delivery succeeds. Sommer ZnAl2O4 source extraction and independent reading continue in parallel; its cited SI is unverified locally. Fixed-cutoff evidence priority, separate later arrivals, one heartbeat, no new downloads and deferred paid API decision remain. Original papers/SI/full text/full pages remain local.''')
 print('Prepared release; no live-publication claim made.')
else:
 v=read(M/'research-assets/github-public-delivery-verification.json')
 assert v['status']=='passed' and v['build']['status']=='built' and v['expected_citation_count']==36
 assert len(v['anonymous']['checks'])==77 and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
 proof=O/('science-release-anonymous-verification.json' if args.stage=='verify' else 'progress-release-anonymous-verification.json');assert not proof.exists();save(proof,v)
 if args.stage=='verify':
  monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_ja212032q',status='complete',note='Published after independent source/data/visual/integration audits and browser review; 77 anonymous endpoints and both 36-citation READMEs match.',data={'current_step':'Published and anonymously verified','publication':{'dataset_version':'0.28.0','site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Exact deployed commit and public bytes verified; source PDFs/SI/full pages remain excluded.'}})
  release=read(O/'prior-latest-publication.json')
  release.update(status='published_verified',public_live_version='GitHub Pages / dataset 0.28.0',published_at=v['build']['updated_at'],dataset_version='0.28.0',record_count=567,synthesis_route_count=111,material_hub_count=inv['public_material_hubs'],direct_material_hub_count=inv['direct_synthesis_target_systems'],component_material_hub_count=inv['component_only_hubs'],public_source_group_count=36,formal_source_reader_count=31,exact_structure_recipe_count=0,new_source_ids=['ghosh2012'],scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Ghosh complete supplied main/SI contribution: 5 routes/variants, 10 procedures, 6 observations, 33 operation scenes, 36 selected crops and 45 explicit symbolic product contexts. All 546 previous records and training eligibility unchanged.',progress_only_update=False)
  release.pop('publication_status_delta_audit',None)
  ed=read(MON/'public-progress-editorial.json');ed['current_work']=[x for x in ed['current_work'] if x['short_label']!='Ghosh et al. (2012)']
  ed['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Ghosh CdSe/CdS contribution published and anonymously verified: five synthesis routes/variants, 33 illustrated operations, 36 selected source crops and separately scoped structure/property evidence. Dataset 0.28.0 has 567 records and 111 routes/variants. Sommer ZnAl₂O₄ source extraction and independent review continue.'})
  ed['estimate']['current_batch']='The retained pilot and Evans, Morrison, Lian and Ghosh rolling contributions are published. Sommer ZnAl₂O₄ is in complete source extraction and independent review. Whole-corpus throughput and completion date remain unvalidated.'
  save(MON/'public-progress-editorial.json',ed)
 else:
  release=read(MON/'latest-publication.json');assert release['dataset_version']=='0.28.0'
  release.update(progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Ghosh final publication-status metadata and current Sommer review queue; scientific dataset 0.28.0 unchanged.')
 release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
 release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous']
 release['integration_checks']={p.relative_to(M).as_posix():sha(p) for p in [ia,ba,O/'build-check-output.json']}
 for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
 memory(f'''## 2026-09-20 — Ghosh {'published' if args.stage=='verify' else 'progress release verified'}

Saved {now}. Public site https://cuiyist.github.io/mattersyn-site/ at {v['site_commit']}, built {v['build']['updated_at']}: all 77 anonymous page/data/asset endpoints and both 36-source README citation lists match. Dataset 0.28.0 has 567 structured records, 111 routes/variants, {inv['public_material_hubs']} material/component hubs, 36 source groups and 31 formal source readers. Ghosh reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=ghosh2012 . Exact structure–recipe pairs remain zero; scientific release {release['scientific_dataset_commit']} is tracked separately from progress releases.

Ghosh closed through complete supplied-source reading, extraction, independent audits, website integration and anonymous publication. Unknown precursor preparations, phase/sample joins, atomic coordinates and non-digitized figure values remain explicit. Sommer source extraction and independent audit continue. No downloads or paid processing; later arrivals remain separate from the fixed two-month scope. Original PDFs/SI/raw full text/full-page images stay local. Proof binds project {v['project_commit']}; a subsequent project commit records this proof and latest memory.''')
 print(json.dumps({'stage':args.stage,'dataset':'0.28.0','site_commit':v['site_commit'],'science_commit':release['scientific_dataset_commit'],'status':'published_verified'}))
