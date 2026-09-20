"""Root release checkpoint: no live claim before exact anonymous verification."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys
A=Path(__file__).resolve().parent;O=A/'site-integration-proposal';MON=A.parents[2];M=A.parents[4];S=M/'recipe-atlas'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def memory(t):
 p=M/'MEMORY.md';p.write_text(t+'\n\n'+p.read_text('utf8'),'utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify','finish']);stage=ap.parse_args().stage;now=datetime.now(timezone.utc).isoformat()
ia=A/'site-integration-independent-audit/integration-transport-audit.json';ba=O/'browser-validation.json'
assert all(read(p)['status']=='passed' for p in [ia,ba])
assert read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.30.0'
ss=read(S/'data/inventory-summary.json')['summary'];assert ss['canonical_records']==607 and ss['synthesis_route_variant_records']==115 and ss['verified_exact_structure_recipe_pairs']==0
gid='10.1021_acsanm.2c04342'
if stage=='prepare':
 assert read(A/'site-integration-independent-audit/browser-gate-delta-audit.json')['status']=='passed'
 assert read(A/'site-integration-independent-audit/conditional-publication-rule-audit.json')['status']=='passed_conditionally'
 prior=O/'prior-latest-publication.json';assert not prior.exists();save(prior,read(MON/'latest-publication.json'))
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=gid,note='Complete supplied main/SI contribution integrated after separate source/data/visual audits and actual browser checks; anonymous release remains pending.',data={'current_step':'Publishing independently passed Matuhina contribution','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones={'audit':{'status':'complete','evidence':[str(ia),str(A/'source-independent-audit/independent-audit-v2.json')],'note':'Independent source, canonical, molecular, apparatus, product-context and transport audits passed.'},'integrate':{'status':'complete','evidence':[str(ia),str(ba),str(O/'build-check-output.json')],'note':'All39 stage controls and source-specific figure/sample views checked. Existing586records and training exports preserved.'}})
 memory(f'''## 2026-09-20 — Matuhina integrated; anonymous publication pending

Saved {now}. Candidate dataset0.30.0 contains607records115routes/variants. Matuhina2023 adds21records(one hot-injection route with five paired conditions,13procedures,seven observation records),39illustrated stages,30original selected crops,28chemical references/fivestocks and47symbolic product contexts. Complete13main+13matchedSI review and distinct source/data/visual/transport/browser audits passed. No exact atomic pair or training promotion. Existing586records unchanged. Scientific public release remains0.29.0 until exact anonymous delivery verification. Pati2009 source audit passed; canonical/reader preparation continues. Original PDFs/SI/full text/full pages stay local; no downloads or paid API run.''')
 print('Release prepared; no live-publication claim.');raise SystemExit
v=read(M/'research-assets/github-public-delivery-verification.json');plan=read(O/'release-endpoints.json')
assert v['status']=='passed' and v['build']['status']=='built' and v['site_commit']==v['build']['commit'] and v['expected_citation_count']==38
assert len(v['anonymous']['checks'])==plan['count'] and {x['path'] for x in v['anonymous']['checks']}==set(plan['paths']) and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
proof=O/('science-release-anonymous-verification.json' if stage=='verify' else 'progress-release-anonymous-verification.json')
if proof.exists():assert read(proof)==v
else:save(proof,v)
if stage=='verify':
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id=gid,status='complete',note='Complete supplied main/SI contribution independently reviewed and published; exact public bytes and both38-citation READMEs verified.',data={'current_step':'Published and anonymously verified within supplied main/SI scope','publication':{'dataset_version':'0.30.0','site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Exact deployed commit/public bytes verified; changed main/SI reopens scope.'}})
 release=read(O/'prior-latest-publication.json');reviews=read(S/'dist/data/paper-review-index.json')['papers']
 release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.30.0',published_at=v['build']['updated_at'],dataset_version='0.30.0',record_count=ss['canonical_records'],synthesis_route_count=ss['synthesis_route_variant_records'],material_hub_count=ss['public_material_hubs'],direct_material_hub_count=ss['direct_synthesis_target_systems'],component_material_hub_count=ss['component_only_hubs'],public_source_group_count=ss['total_canonical_source_groups'],formal_source_reader_count=len(reviews),exact_structure_recipe_count=0,new_source_ids=['matuhina2023'],scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Matuhina complete supplied main/SI contribution:21records,39stage illustrations,30selected original crops and47source-scoped symbolic product contexts. Prior586records and training exports unchanged.',progress_only_update=False)
 release.pop('publication_status_delta_audit',None)
 ed=read(MON/'public-progress-editorial.json');ed['current_work']=[x for x in ed['current_work'] if x['short_label']!='Matuhina et al. (2023)']
 ed['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Matuhina CsMnCl₃ contribution published and anonymously verified: five paired hot-injection conditions, 39 illustrated stages, 30 original source crops and separately assigned structure, optical, aging and device specimens. Dataset0.30.0 contains607records and115routes/variants. Complete supplied main and matched SI reviewed; source contradictions remain explicit.'})
 ed['estimate']['current_batch']='Matuhina CsMnCl₃ complete main/SI contribution is published. Pati CeO₂ source audit passed and its canonical records/reader are in preparation. Whole-corpus throughput and finish date remain unvalidated.'
 save(MON/'public-progress-editorial.json',ed)
else:
 release=read(MON/'latest-publication.json');assert release['dataset_version']=='0.30.0'
 release.update(progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Matuhina verified-publication labels and current review progress; scientific dataset0.30.0 unchanged.')
release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous'];release['integration_checks']={p.relative_to(M).as_posix():sha(p) for p in [ia,ba,O/'build-check-output.json']}
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
memory(f'''## 2026-09-20 — Matuhina {'science' if stage=='verify' else 'progress'} release verified

Saved {now}. Public website commit {v['site_commit']}, built {v['build']['updated_at']}; all{plan['count']}anonymous endpoints and both38-source README citation lists verified. Dataset0.30.0 has607records115routes/variants,{ss['public_material_hubs']}material/component hubs38sourcegroups. Scientific dataset commit {release['scientific_dataset_commit']} is separate from progress-only delivery. Reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=matuhina2023 . All prior586records/training exports unchanged; exact atomic structure-recipe pairs0.

Matuhina closed within complete supplied main13+SI13 scope after source,canonical,visual,transport and browser audits and verified publication. Source ambiguities and unknown specimen joins remain explicit. Pati2009 CeO2 main/SI source audit passed; canonical/reader preparation continues. Resume immutable packages at rolling-pipeline/la8031286. Existing cutoff evidence priority, separate later arrivals, one heartbeat, public filtered project/site, no downloads and deferred API pilot persist. A subsequent project commit records this proof without changing the scientific website.''')
print(json.dumps({'stage':stage,'status':'published_verified','dataset':'0.30.0','site_commit':v['site_commit'],'science_commit':release['scientific_dataset_commit']}))
