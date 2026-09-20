from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
G=Path(__file__).resolve().parent;O=G/'site-integration-proposal';MON=G.parents[2];M=G.parents[4]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
v=read(M/'research-assets/github-public-delivery-verification.json')
assert v['status']=='passed' and v['site_commit']=='d223f71ed65ce56348f4dea7cea3539e8e341475'
assert v['build']['commit']==v['site_commit'] and v['build']['status']=='built'
assert len(v['anonymous']['checks'])==77 and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
proof=O/'progress-readability-anonymous-verification.json';assert not proof.exists();save(proof,v)
r=read(MON/'latest-publication.json');assert r['dataset_version']=='0.28.0' and r['record_count']==567
r.update(recorded_at=datetime.now(timezone.utc).isoformat(),commit_sha=v['site_commit'],project_commit_sha=v['project_commit'],progress_only_update=True,progress_published_at=v['build']['updated_at'],publication_scope='Readability-only wording correction in the Sommer progress card; all scientific data, source review states and training eligibility unchanged.')
r['deployment']['commit']=v['site_commit'];r['anonymous_verification']=v['anonymous']
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:save(p,r)
p=M/'MEMORY.md';note=f'''## 2026-09-20 — Verified public release and continuation

The latest website commit is {v['site_commit']}, built {v['build']['updated_at']}. All 77 anonymous endpoint checks passed, and both GitHub READMEs retain 36 source citations. This final change only improves the readability of the progress card. Scientific dataset 0.28.0 remains at commit 5c138bb63bba8702453d209c5ecf7e48714a4b5c: 567 structured records, 111 synthesis routes or variants, 46 material/component hubs, 36 source groups and 31 formal readers. Ghosh is fully closed through publication. Its exact structure–recipe contribution remains zero.

Sommer (2020), DOI 10.1021/acs.cgd.9b01519, is the active paper. The frozen source package is 18e1e1e2c220c108f74e079043bad72a44551f798be9fb28ded314b49e1622c6 under research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/acs.cgd.9b01519. Norberg independently audits it; Backlog prepares the canonical data and reader; Peng prepares source-qualified chemical references. All work stays outside the Site until the applicable audits pass. The 11-page main article is supplied; cited SI has not been located or verified. Preserve the 13 source conflicts and qualifications.

The fixed collection currently has 9,533 provisional scopes: 9,506 pending and 27 terminal. Three nested identity cases remain held, and 238 files require manual format/text screening. Later arrivals (268 groups, 270 files at the last scan) remain separate. These are worklist counts, not established paper or recipe totals. No paid API work or paper downloads are authorized. The existing single heartbeat resumes this handoff; do not create a duplicate or repeat Ghosh's completed reviews.

The root preview server on port 5193 is stopped. Public Ghosh and progress tabs remain open. The project and installed delivery skill reference match SHA256 92e80ab283a010d6395d09eab0d1a65527bf8c371d552e5b64af8039766e9a28 and passed validation. Both repositories are public; original papers, SI, raw full text, complete-page images and credentials remain excluded. The final project commit stores this receipt; the receipt binds the preceding project commit to avoid a self-reference.

''';p.write_text(note+p.read_text(encoding='utf8'),encoding='utf8')
sys.path.insert(0,str(M/'research-assets'));import public_projection_policy as policy
D=M.parent/'mattersyn-github-project'
files=['MEMORY.md','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/incoming-paper-monitor/latest-publication.json',str(proof.relative_to(M)).replace('\\','/'),str(Path(__file__).relative_to(M)).replace('\\','/')]
for rel in files:
 assert not policy.exclude_path(rel);raw,_=policy.project_bytes(rel,(M/rel).read_bytes());target=D/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
print(json.dumps({'verified_site':v['site_commit'],'science_commit':r['scientific_dataset_commit'],'final_project_proof_ready':True}))
