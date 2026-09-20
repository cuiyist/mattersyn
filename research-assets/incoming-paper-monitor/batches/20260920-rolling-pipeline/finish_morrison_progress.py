"""Record a verified progress-only release and its bounded project snapshot."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys

R=Path(__file__).resolve().parent; MON=R.parents[1]; M=MON.parents[1]
sys.path.insert(0,str(M/'research-assets'))
import public_projection_policy as policy
from sync_github_public import io_path
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
now=datetime.now(timezone.utc).isoformat()
v=read(M/'research-assets/github-public-delivery-verification.json')
assert v['status']=='passed' and v['site_commit']=='cb90e336367e1d527ef0fdfe045e51686ae2be7b'
assert v['build']['status']=='built' and len(v['anonymous']['checks'])==47
assert all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
N=R/'acs.inorgchem.7b01711'; L=R/'acsami.1c18038'
proof=N/'site-integration-proposal/progress-release-anonymous-verification.json'
assert not proof.exists();save(proof,v)
release=read(MON/'latest-publication.json')
assert release['scientific_dataset_commit']=='22e894390eae26cfcf4eb84c4c69157f49cf617b'
release.update(recorded_at=now,commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Verified Morrison publication-status metadata and parallel Lian/Ghosh queue; scientific dataset 0.26.0 unchanged.',publication_status_delta_audit={'path':str(N/'site-integration-independent-audit/publication-label-audit.json'),'sha256':sha(N/'site-integration-independent-audit/publication-label-audit.json')})
release['deployment']['commit']=v['site_commit'];release['anonymous_verification']=v['anonymous']
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,release)
apparatus=L/'visuals/apparatus/package-freeze.json'
assert sha(apparatus)=='fe99285425cfe7de6526f75f47808f0b5d980739d41dfce85f20c0facdcc3957'
note=f'''## 2026-09-20 — Progress deployment verified; current review handoffs

Saved {now}. Public progress https://cuiyist.github.io/mattersyn-site/progress.html is verified at website commit {v['site_commit']}, built {v['build']['updated_at']}. All 47 anonymous page/data/asset checks and both 34-citation READMEs passed. Root also inspected the actual public dashboard. Dataset 0.26.0 remains 530 structured records, 103 routes/variants, 44 material/component hubs and 29 formal source readers. This progress-only release preserves the Morrison scientific publication timestamp and commit 22e894390eae26cfcf4eb84c4c69157f49cf617b. Full corpus review is not complete; the fixed-cutoff screen includes 238 manual format/text cases and three held nested identity cases.

Active work: Lian source and canonical/reader audits passed. Both molecular and apparatus proposals are now frozen and assigned to Peng for independent review. Molecular freeze 4630547b7d44afd66a2c9ca46db39c9e90c566fbe63f6cf149c81a9ce1652321; apparatus freeze {sha(apparatus)}, module 08b09f1cf06a68950014ee8684321bb4cfb81d92e127a0982801ada7d8a2a928. Apparatus author checked all 21 operations across nine records, 122 rows and 594 function/quantity checks; this is not the independent approval. No Lian Site integration yet. Ghosh complete 19-page local main/SI reading/extraction is with Backlog; Norberg independently reads its sources alongside the author, binding an audit only after freeze. Keep separate paper histories; no self-audits.

Project memory and installed delivery skill match at SHA acd2d310dd6061e0aae2aef20b005e220dbf5901a9613930d2fc3de509d93b5a for the delivery reference. Source binaries, raw text and complete-page renders remain excluded. The current anonymous proof binds project commit {v['project_commit']}; a subsequent project commit stores this proof and the final handoffs. Use the existing single heartbeat and latest memory rather than restarting completed work. No paid API pipeline or source download was initiated.
'''
p=M/'MEMORY.md';p.write_text(note+'\n'+p.read_text(encoding='utf8'),encoding='utf8')
# Only the already-audited projection is applied. No deletions or source edits.
dest=M.parent/'mattersyn-github-project'
files=[p,Path(__file__),proof,MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json',M/'research-assets/github-public-delivery-verification.json',M/'research-assets/github-public-project-sync.json',M/'research-assets/github-public-site-sync.json']
for folder in [L/'visuals/apparatus']:
 for directory,dirs,names in os.walk(io_path(folder)):
  dirs[:]=[d for d in dirs if d!='__pycache__']
  files += [folder/(Path(directory)/n).relative_to(io_path(folder)) for n in names]
kept=0;omitted=0
for source in files:
 rel=source.relative_to(M).as_posix()
 if io_path(source).is_symlink() or policy.exclude_path(rel):omitted+=1;continue
 raw,_=policy.project_bytes(rel,io_path(source).read_bytes())
 target=io_path(dest/rel);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);kept+=1
print(json.dumps({'verified_site_commit':v['site_commit'],'science_commit_preserved':release['scientific_dataset_commit'],'project_files_projected':kept,'excluded':omitted,'source_files_modified':False}))
