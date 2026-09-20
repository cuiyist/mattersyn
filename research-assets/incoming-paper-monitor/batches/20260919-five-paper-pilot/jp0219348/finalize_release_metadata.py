"""Save verified release metadata and project only its bounded final checkpoints."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
H=Path(__file__).resolve().parent;MON=H.parents[2];M=H.parents[4];O=H/'site-integration-proposal';D=M.parent/'mattersyn-github-project'
sys.path.insert(0,str(M/'research-assets'));import public_projection_policy as policy
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(b):return hashlib.sha256(b).hexdigest()
v=read(M/'research-assets/github-public-delivery-verification.json');assert v['status']=='passed'
assert v['site_commit']=='809162289b2ad1d99858a58a19771cafccb704e5'
now=datetime.now(timezone.utc).isoformat()
for p in [M/'research-assets/github-publication-checkpoint.json',MON/'latest-publication.json']:
 d=read(p);d.update(commit_sha=v['site_commit'],published_at=v['build']['updated_at'],recorded_at=now,project_commit_sha=v['project_commit'],anonymous_verification=v['anonymous']);d['deployment']['commit']=v['site_commit']
 d['release_consistency_audit']={'path':str(H/'release-consistency-audit/release-consistency-audit.json'),'sha256':'eff1bdbff85e74020936c0d9c55a069562af9491a8441d9a8a349fc200b961a2'};save(p,d)
save(O/'public-browser-validation.json',{'at':now,'status':'passed','reviewer':'root','mechanism':'Actual Codex in-app browser via cua_repl','origin':'https://cuiyist.github.io/mattersyn-site/',
 'checks':['Heo material hub loaded its reviewed method, precursors, stage diagrams and qualified average model without browser errors.','Public repeated-cell control produced5,440visible position markers.','Public progress dashboard displayed5/5pilot papers published, dataset0.24.0 and Evans independent source audit complete with reader audit ongoing.','Temporary viewport reset; public progress tab retained for the user.'],
 'network_verification':{'path':'research-assets/github-public-delivery-verification.json','site_commit':v['site_commit'],'anonymous_exact_byte_checks':24},
 'local_preview_cleanup':'Root-owned5191and5192servers stopped;5196confirmed absent.'})
p=M/'MEMORY.md'
entry=f'''## 2026-09-20 — Final verified release and continuation checkpoint

Saved {now}. Current public site commit {v['site_commit']} built {v['build']['updated_at']}; all 24 anonymous page/data/model requests and both 32-source citation READMEs matched the checked files. The progress page shows 5/5 retained pilot papers published and Evans in independent structured-record/reader review. Root opened the live Heo material page and exercised its repeated-cell viewer (5,440 markers); no browser errors. The final independent release consistency audit passed 121 checks, including source exclusions, retained SI/crops, reader-route classification and all 470 old record hashes. Exact source uncertainties remain explicit. Temporary root preview servers are stopped; the public progress tab is retained.

Memory, project/installed skills and the existing single five-minute heartbeat were updated to resume current artifacts, with Heo closed and Evans active. Evans source audit revision2 passed, but canonical audit has identified a bounded distinction between distillation residue C and collected distillates; the author is preparing a preserved correction. Molecular assets proceed alongside that audit. Do not publish Evans or call its structured records fully audited until that gate passes. No paid API run, new infrastructure or source-paper download was started. Both public repositories remain the delivery targets; original papers/SI/raw full text/full-page scans remain local. This checkpoint is included in a subsequent public project commit; avoid an impossible self-referential commit hash in the same file.

'''
p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
# A full safe projection already completed. These explicit final checkpoints
# were written afterward; reuse the same audited projection function.
paths=[M/'MEMORY.md',M/'research-assets/github-publication-checkpoint.json',MON/'latest-publication.json',M/'research-assets/github-public-delivery-verification.json',MON/'public-progress-editorial.json',MON/'build_public_progress.py',M/'recipe-atlas/dist/data/review-progress.json',M/'recipe-atlas/dist/index.html',M/'recipe-atlas/dist/progress.mjs',O/'public-browser-validation.json',H/'finalize_release_metadata.py']
rows=[]
for src in paths:
 rel=src.relative_to(M).as_posix();assert not policy.exclude_path(rel)
 raw,stats=policy.project_bytes(rel,src.read_bytes());dst=D/rel;assert dst.resolve().is_relative_to(D.resolve());dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
 rows.append({'path':rel,'projected_sha256':sha(raw),'transformed':stats['changed']})
save(O/'final-checkpoint-projection.json',{'at':now,'scope':'Bounded metadata files written after full project sync; same source exclusion/transform policy.','files':rows,'source_files_deleted':False})
rel=(O/'final-checkpoint-projection.json').relative_to(M);raw,_=policy.project_bytes(rel.as_posix(),(M/rel).read_bytes());(D/rel).write_bytes(raw)
print(json.dumps({'projected_final_checkpoints':len(rows)+1,'website_commit':v['site_commit'],'memory_saved':True},indent=2))
