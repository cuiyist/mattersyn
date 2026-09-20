"""Source-bound prepublication checkpoint and verified science-release closure."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,json,sys
N=Path(__file__).resolve().parent;O=N/'site-integration-proposal';MON=N.parents[2];M=N.parents[4];S=M/'recipe-atlas';L=N.parent/'acsami.1c18038'
sys.path.insert(0,str(MON));import monitor
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def memory(text):
 p=M/'MEMORY.md';p.write_text(text+'\n\n'+p.read_text(encoding='utf8'),encoding='utf8')
ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['prepare','verify']);args=ap.parse_args();now=datetime.now(timezone.utc).isoformat()
ia=N/'site-integration-independent-audit/integration-code-audit.json';ba=O/'browser-validation.json'
assert read(ia)['status']=='passed' and read(ba)['status']=='passed'
assert read(S/'dist/data/dataset-manifest.json')['dataset_version']=='0.26.0'
if args.stage=='prepare':
 for p in [MON/'latest-publication.json',M/'research-assets/github-public-delivery-verification.json']:
  dest=O/('prior-'+p.name)
  if not dest.exists():save(dest,read(p))
 milestones={key:{'status':'complete','evidence':[str(p) for p in paths],'note':note} for key,paths,note in [
 ('read',[N/'source-independent-audit/independent-audit-v2.json',N/'page-coverage.json'],'Complete supplied 10 main and 17 SI pages independently reviewed.'),
 ('extract',[N/'canonical-proposal/v2/package-manifest.json',N/'canonical-reader-independent-audit/independent-audit-v2.json'],'18 source-reviewed records and full reader; printed conflicts retained.'),
 ('audit',[ia,N/'site-integration-independent-audit/promotion-delta-audit.json',N/'site-integration-independent-audit/product-context-audit.json'],'Separate scientific, molecular, apparatus, promotion and integration audits passed.'),
 ('integrate',[ia,ba,O/'final-check-output.json',O/'reader-label-rebuild-check.json'],'All24integrated stage controls,155conditionrows, molecular rotation/zoom, product contexts, source figures and mobile layout checked. All512previous records and training eligibility unchanged.') ]}
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',note='All scientific, integration and actual browser checks passed. Public deployment remains pending exact anonymous verification.',data={'current_step':'Publishing audited Morrison contribution; anonymous verification pending','integration_audit':{'path':str(ia),'sha256':sha(ia)},'browser_validation':{'path':str(ba),'sha256':sha(ba)}},milestones=milestones)
 la=L/'source-independent-audit/independent-audit-v2.json';assert read(la)['status']=='passed'
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='legacy::10.1021_acsami.1c18038',note='Complete34-page supplied main/SI source audit passed revision2. Canonical/reader proposal and its distinct independent review proceed in parallel outside Site.',data={'current_step':'Source audit passed; canonical records and reader in independent preparation/review','source_scientific_audit':{'path':str(la),'sha256':sha(la)},'effective_source_freeze':{'path':str(L/'package-freeze.json'),'sha256':sha(L/'package-freeze.json')}},milestones={'read':{'status':'complete','evidence':[str(la),str(L/'page-coverage.json')],'note':'All8main+26SIpages read and visually inspected by author and independent reviewer.'},'extract':{'status':'partial','evidence':[str(la)],'note':'Source extraction passed57facts134quantities9tables891cells; canonical/reader gate pending.'}})
 memory(f'''## 2026-09-20 — Morrison integrated; public verification pending

Saved {now}. Local candidate dataset 0.26.0 has 530 structured records, 103 synthesis routes/variants, 44 material/component hubs, 34 source groups and 29 formal readers. Live verified science is still 0.25.0 until deployment verification passes. Morrison adds 2 routes, 8 supporting procedures and 8 observations; these 18 records are not 18 independent experiments. All 512 older canonical files and all training eligibility remain unchanged; exact structure–recipe pairs remain zero.

Source/canonical/molecular/apparatus audits and root promotion/product-context audits passed. Independent integration audit {sha(ia)} covers the actual imported site. Actual browser receipt {sha(ba)} covers all 24 stage controls, 155 adjacent condition rows, THF rotation/zoom/highlighting, product specimen selection, 15/26 versus 26/26 figure filtering, HRTEM enlargement, both CdSe method cards and 390px responsive layout. Empty mappings for seven zero-material observations, wrapped provenance hashes and a source-specific stale reader-link label were corrected with explicit deltas. Thirty selected crops and 29 chemical identities are retained; no new product coordinates or training approval.

Lian source revision2 independently passed ({sha(la)}); all34pages/53crops/891tablecells checked. Backlog authors unapproved canonical/reader proposals; Peng independently reviews. Missing local ZIP/video remain explicit. Continue existing frozen work, keep later arrivals separate, and use the single existing heartbeat. No source downloads or paid API runs. Public project/site synchronization excludes papers, SI, raw text and full-page scans. Reusable lessons saved to project and installed skills.''')
 save(O/'prepublication-checkpoint.json',{'at':now,'integration_audit_sha256':sha(ia),'browser_validation_sha256':sha(ba),'candidate_dataset':'0.26.0','public_verification_pending':True})
 print('Prepared Morrison publication; no public claim before anonymous verification.')
else:
 v=read(M/'research-assets/github-public-delivery-verification.json')
 assert v['status']=='passed' and v['build']['status']=='built' and v['expected_citation_count']==34
 assert len(v['anonymous']['checks'])==47 and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
 proof=O/'science-release-anonymous-verification.json';save(proof,v)
 monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acs.inorgchem.7b01711',status='complete',note='Complete supplied main/SI review, separate audits, actual integrated browser checks and public publication passed. Exact bytes verified across47anonymous pages/data/assets and both34-source READMEs.',data={'current_step':'Published and anonymously verified','publication':{'dataset_version':'0.26.0','site_commit':v['site_commit'],'verification_path':str(proof),'verification_sha256':sha(proof)}},milestones={'publish':{'status':'complete','evidence':[str(proof)],'note':'Public GitHub Pages exact-byte verification passed; papers/SI/fulltext/fullpages excluded.'}})
 release=read(O/'prior-latest-publication.json')
 release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.26.0',published_at=v['build']['updated_at'],recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],dataset_version='0.26.0',record_count=530,synthesis_route_count=103,material_hub_count=44,direct_material_hub_count=33,component_material_hub_count=11,public_source_group_count=34,formal_source_reader_count=29,exact_structure_recipe_count=0,new_source_ids=['morrison2017'],current_active_paper_claims=len(monitor.active_claims(monitor.read_ledger(MON/'ledger.json'))),scientific_dataset_published_at=v['build']['updated_at'],scientific_dataset_commit=v['site_commit'],publication_scope='Morrison complete supplied main/SI:2shell-growth routes,8supportingprocedures,8observations;24operation scenes,29chemicalreferences,30selectedcrops. All512priorrecords and taskeligibility unchanged.',progress_only_update=False,raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
 release.pop('publication_status_delta_audit',None)
 release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']};release['anonymous_verification']=v['anonymous'];release['integration_checks']={p.relative_to(M).as_posix():sha(p) for p in [ia,ba,O/'final-check-output.json',O/'reader-label-rebuild-check.json']}
 for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
 ed=read(MON/'public-progress-editorial.json');ed['current_work']=[x for x in ed['current_work'] if x['short_label']!='Morrison et al. (2017)']
 for x in ed['current_work']:
  if x['short_label']=='Lian et al. (2021)':
   x.update(stage='Complete source audit passed; structured records and reader in parallel review',summary='All34 supplied main/SI pages,57facts,134quantities,9tables with891cells and53selectedcrops passed independent source review. Structured records and the reader are being checked separately. Bulk crystals, nanocrystals, films and calculated results retain distinct sample scopes.')
 ed['recent_milestones'].insert(0,{'at':v['build']['updated_at'],'text':'Morrison CdSe/CdS contribution published and anonymously verified: 2 synthesis routes, 8 supporting procedures and 8 observation records. Dataset0.26.0 now has530records,103routes/variants and44material/component hubs. Lian source review passed; structured-data review continues.'})
 ed['estimate']['current_batch']='The retained five-paper pilot and Evans/Morrison rolling contributions are published. Lian has passed complete source review and is in structured-record/reader review. The throughput required for the two-month goal remains unvalidated.'
 save(MON/'public-progress-editorial.json',ed)
 memory(f'''## 2026-09-20 — Morrison published and verified

Saved {now}. Dataset 0.26.0 is LIVE at https://cuiyist.github.io/mattersyn-site/ . Source reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=morrison2017 . Science commit {v['site_commit']} built {v['build']['updated_at']}; all47anonymous page/data/asset checks and both34-citation READMEs passed. Current totals:530structuredrecords,103synthesisroutes/variants,44material/componenthubs,34sourcegroups,29formalreaders. All512previous scientific records and task eligibility unchanged; exact structure–recipe pairs0. Morrison is closed through read/extract/audit/integrate/publish. Separate progress/status release follows; its commit must not overwrite this science release's date/identity.

Morrison's 18records separate2routes,8supportingprocedures and8observations;24illustratedoperations,29chemicalreferences,30selectedcrops and17explicit symbolic product contexts are included. No CdSe/CdS atomic model is inferred from precursor crystal tables. Lian source audit passed; its canonical/reader extraction and independent audit continue outsideSite. Original source binaries, complete text and full-page images remainlocal. Public project verified at {v['project_commit']}; subsequent commits store this proof and memory.''')
 print(json.dumps({'status':'published_verified','dataset':'0.26.0','science_commit':v['site_commit'],'morrison_closed':True,'progress_release_pending':True}))
