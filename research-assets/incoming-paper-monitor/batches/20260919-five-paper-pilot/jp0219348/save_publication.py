"""Advance publication metadata only from the saved anonymous verification."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
H=Path(__file__).resolve().parent;MON=H.parents[2];M=H.parents[4];O=H/'site-integration-proposal'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(M/'research-assets/github-public-delivery-verification.json');science=read(O/'science-release-anonymous-verification.json')
assert v['status']=='passed' and v['build']['status']=='built'
assert read(M/'recipe-atlas/dist/data/dataset-manifest.json')['dataset_version']=='0.24.0'
assert read(MON/'ledger.json')['groups']['10.1021_jp0219348']['review']['status']=='complete'
now=datetime.now(timezone.utc).isoformat();old=read(MON/'latest-publication.json')
if not (O/'prior-publication-checkpoint.json').exists():save(O/'prior-publication-checkpoint.json',old)
release={k:old[k] for k in ['schema','host','public_url','public_repository','project_repository','project_repository_visibility','current_worktrees','preserved_private_original_repositories','history_projection_report','filtered_initial_history_head','cutoff_manifest_sha256'] if k in old}
release.update(status='published_verified',public_live_version='GitHub Pages / dataset0.24.0',published_at=v['build']['updated_at'],recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],dataset_version='0.24.0',record_count=480,synthesis_route_count=98,material_hub_count=44,direct_material_hub_count=33,component_material_hub_count=11,public_source_group_count=32,formal_source_reader_count=27,exact_structure_recipe_count=0,new_source_ids=['heo2003'],remaining_original_pilot_papers=0,remaining_batch_papers=0,current_active_paper_claims=1,scientific_dataset_published_at=science['build']['updated_at'],scientific_dataset_commit=science['site_commit'],publication_scope='Heo complete main/SI contribution:1route,3acquisition procedures,6contexts;14stage diagrams,average-occupancy model and1209reflection rows. Existing470records and training admission unchanged.',raw_papers_and_si_uploaded=False,full_document_equivalents_excluded_from_public_history=True,subsequent_project_commits_may_record_this_verification=True)
release['deployment']={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':v['site_commit']}
release['anonymous_verification']=v['anonymous']
release['integration_checks']={p.relative_to(M).as_posix():sha(p) for p in [O/'build-check-output.json',O/'browser-validation.json',H/'site-integration-independent-audit/promotion-projection-delta-audit.json',H/'integration-code-independent-audit/delta-audit.json']}
for p in [M/'research-assets/github-publication-checkpoint.json',MON/'latest-publication.json']:save(p,release)
ed=read(MON/'public-progress-editorial.json');ed['batch']['published']=5
for p in ed['batch']['papers']:
 if p['label']=='Heo et al. (2003)':p.update(published=True,href='paper-review.html?id=heo2003',scope='Indium nanoclusters in zeolite X; complete main/SI, qualified average model')
ev=next(w for w in ed['current_work'] if w['short_label']=='Evans et al. (2010)')
ev.update(stage='Source audit passed; canonical records and illustrated reader in preparation',summary='All3main-paper pages and21matched SI pages,25selected crops and the molecular CIF were read and independently checked. The source audit covers198evidence units,457typed facts and2896CIF table cells. One dimensionless CIF completeness value was corrected in a preserved revision. Canonical records and reader now have a separate review gate.')
ev['stages']=[{'label':'Main/SI/CIF pairing and full reading','status':'complete','detail':'24pages,25selected scientific crops; original source hashes retained'}, {'label':'Source extraction and independent audit','status':'complete','detail':'457facts; all CIF cells checked; one unit correction preserved'}, {'label':'Canonical records and reader audit','status':'in_progress','detail':'Routes, controls and analytical contexts retain separate identities; no automatic training promotion'}, {'label':'Illustrations, browser checks and publication','status':'pending','detail':'Release only after the remaining individual gates pass'}]
ev['gaps']=['The supplied CIF describes molecular compound9; it does not supply quantum-dot atomic coordinates.','Source variants, negative controls and sample assignments remain separated; no exact QD structure–recipe pair is established.']
ed['current_work']=[ev]
ed['estimate']['current_batch']='The retained five-paper pilot is now5/5published within each recorded source scope. Evans has passed independent source review and is entering canonical/reader integration. The two-month required pace remains unvalidated.'
milestone={'at':science['build']['updated_at'],'text':'Heo contribution published and anonymously verified: dataset0.24.0,480records,98routes/variants,44material/component collections. Complete1209-row SI reader and qualified average-occupancy CIF included; original five-paper pilot5/5published.'}
if not any(x.get('at')==milestone['at'] for x in ed['recent_milestones']):ed['recent_milestones'].insert(0,milestone)
save(MON/'public-progress-editorial.json',ed)
entry=f'''## 2026-09-20 — Heo published; original five-paper pilot complete

Saved {now}. Dataset0.24.0 is LIVE at https://cuiyist.github.io/mattersyn-site/ . Heo reader: https://cuiyist.github.io/mattersyn-site/paper-review.html?id=heo2003 ; material: https://cuiyist.github.io/mattersyn-site/material.html?id=in66si100al92o384-e3d988 . Pages commit{v['site_commit']} built{v['build']['updated_at']}. Both public repositories,32-source citation READMEs and24anonymous page/data/model/SI paths passed exact-byte verification. Complete-page paths returned404. Public project verified commit{v['project_commit']}; subsequent project commits save this release checkpoint. No original paper/SI binaries or raw full-text payloads were uploaded.

Heo current-generation claim is now closed after read/extract/audit/integrate/publish gates. Original five-paper pilot5/5published. Published totals:480structuredrecords,98synthesis routes/variants,44material/component collections(33direct+11component),32sourcegroups,27formalreaders. These are not independent experiment counts. All470previous records and machine-training eligibility counts remain unchanged; exact structure–recipe pairs0. Heo's average-occupancy CIF is explicitly qualified, including statistical Si/Al composition, alternate partially occupied sites, omitted ADPs and unresolved source discrepancies. Two SI signs remain null, not guessed.

Evans2010 remains active. Independent source audit revision2 PASSED:24pages,25crops,198units,457facts,99CIFscalars and2896loopcells; measured completeness0.98 corrected to dimensionless with v1 preserved. Audit8ed8d242fcf07d44515f4b6711975c9c9c0a9b538d9fab0a06db8ab067097267. Private canonical/reader authoring continues with a separate audit. Continue local screen-first evidence-priority work and refill only through cutoff-eligible queue admission. Paid API decision is deferred. New arrivals remain separate; changing main/SI reopens evidence review. The two-month target is not an achieved throughput forecast.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
print(json.dumps({'publication_saved':v['site_commit'],'dataset':'0.24.0','original_pilot_published':5,'source_readers':27},indent=2))
