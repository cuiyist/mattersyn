"""Save final verified metadata and project only these bounded final checkpoints."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,sys
E=Path(__file__).resolve().parent;MON=E.parents[2];M=E.parents[4];O=E/'site-integration-proposal';D=M.parent/'mattersyn-github-project'
sys.path.insert(0,str(M/'research-assets'));import public_projection_policy as policy
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
ap=argparse.ArgumentParser();ap.add_argument('--site-commit',required=True);args=ap.parse_args()
v=read(M/'research-assets/github-public-delivery-verification.json');assert v['status']=='passed' and v['site_commit']==args.site_commit and v['expected_citation_count']==33
assert len(v['anonymous']['checks'])==36 and all(x['matches_checked_local_bytes'] for x in v['anonymous']['checks'])
audit=E/'site-integration-independent-audit/publication-label-audit.json';assert read(audit)['status']=='passed'
now=datetime.now(timezone.utc).isoformat();save(O/'final-publication-anonymous-verification.json',v)
for p in [MON/'latest-publication.json',M/'research-assets/github-publication-checkpoint.json']:
 d=read(p);assert d['dataset_version']=='0.25.0';d.update(commit_sha=v['site_commit'],published_at=v['build']['updated_at'],recorded_at=now,project_commit_sha=v['project_commit'],anonymous_verification=v['anonymous']);d['deployment']['commit']=v['site_commit'];d['publication_status_delta_audit']={'path':str(audit),'sha256':sha(audit)};save(p,d)
save(O/'public-browser-validation.json',{'status':'passed','at':now,'tool':'CUA actual public GitHub Pages browser','origin':'https://cuiyist.github.io/mattersyn-site/','checks':['Public PbSe record loaded source molecules,stocks and reviewed protocol.','Changing the DPPSe-solution component selector to anhydrous toluene displayed the separate correct solvent representation and caption.','Public step3 shows sealed1cm cuvette in80degreeC oil bath with adjacent source conditions.','Public progress snapshot and its512record counts were opened after verification.'],'exact_deployment_commit':v['site_commit'],'anonymous_probe_count':36,'local_preview_cleanup':'Root-owned port5193 server stopped; other agents own their separate previews.'})
entry=f'''## 2026-09-20 — Final verified Evans release and active handoffs

Saved {now}. Public atlas: https://cuiyist.github.io/mattersyn-site/ . Live progress: https://cuiyist.github.io/mattersyn-site/progress.html . Latest website commit {v['site_commit']} built {v['build']['updated_at']}; all 36 anonymous page/data/model checks and both 33-citation READMEs passed. This progress/status release preserves the scientific release commit 1727559a0bc66149a86e33ef26c01599e34feb9e and its publication time. Dataset 0.25.0 remains 512 structured records, 101 synthesis routes/variants, 44 material/component hubs, 33 source groups and 28 formal readers. Exact structure–recipe pairs remain zero. The 480 previous records and training eligibility are unchanged.

Evans is closed after complete supplied main/SI/CIF review, distinct scientific and presentation audits, integrated browser checks and anonymous publication. Its public reader metadata now correctly marks browser/publication gates complete; the separate metadata audit {sha(audit)} verifies scientific deep equality. Root also tested the public solvent-component selector and oil-bath operation. Original papers, SI binaries, raw full text and complete-page images remain local. Memory and project/installed skills include reusable source-scoped display, qualified structure-viewer and persistent navigation lessons.

Active continuation: Morrison DOI 10.1021/acs.inorgchem.7b01711 has passed source revision 2, canonical/reader v2 and the independent molecular audit (ba09f9a79ad75b075bf20ab5b68485c838ffd9a8944278f0ce818bd0a2283f6a). Its molecular freeze is 79747e889a10786599a2ed4638cab8d3ba30f37df7f71f68bed990f42c0db848. Norberg's apparatus package is frozen at 1c7688c5d9c0d073fcb8c1812cb20de6ff16909dfca820a5e1a1324d5dc6d5b5; Peng independently audits its 24 scenes and 70 source parameters/observations. Root Site integration/browser/publication remain pending. Lian DOI 10.1021/acsami.1c18038 has a matching local 8-page main and 26-page SI, bundle a66f9080c2876ab1cf3186edc8821f577dd9a5455a1e91839e0aa7c3711c0fd5. Backlog reports all 34 pages read/viewed and is completing structured extraction; Norberg now independently reads the sources alongside that extraction, binding the final audit only after the source freeze. Mentioned crystal/video attachments are absent from the current intake pair and remain a gap pending local matching. Working directories are under batches/20260920-rolling-pipeline/acs.inorgchem.7b01711 and acsami.1c18038. Use the latest saved handoffs; neither new contribution is published yet.

Latest scan and queue:13,984document copies; two active claims; fixed-cutoff9,511pending provisional scopes plus three held nested identity cases;152later-arrival groups separate. The existing five-minute heartbeat is ACTIVE and its stale Evans-draft narrative was replaced with these continuation pointers. It reads current memory/ledger before acting. Do not duplicate the scheduler or restart completed source extraction. Paid API decision remains deferred; no new downloads or paid infrastructure. Final project commits save this verification and memory; the proof above binds project commit{v['project_commit']} before those self-documenting commits.

'''
p=M/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf8'),encoding='utf8')
paths=[M/'MEMORY.md',M/'research-assets/github-publication-checkpoint.json',M/'research-assets/github-public-delivery-verification.json',MON/'latest-publication.json',MON/'public-progress-editorial.json',MON/'ledger.json',MON/'queue-status.json',MON/'queue-status.md',MON/'queue-status.html',M/'research-assets/github-public-site-sync.json',M/'research-assets/github-public-project-sync.json',audit,audit.with_suffix('.md'),O/'public-browser-validation.json',O/'final-publication-anonymous-verification.json',Path(__file__)]
rows=[]
paths += [E/'polish_public_progress.py',M/'recipe-atlas/dist/data/review-progress.json',M/'recipe-atlas/dist/index.html']
paths += [E/'save_final_handoffs.py',E.parent/'final-handoffs-20260920T0730.json']
# Recently finished audit packages are bounded additions after the full sync.
for folder in [E.parent/'acs.inorgchem.7b01711/visuals/molecules-independent-audit',E.parent/'acs.inorgchem.7b01711/visuals/apparatus']:
 for src in folder.rglob('*'):
  if src.is_file() and not policy.exclude_path(src.relative_to(M).as_posix()):paths.append(src)
for src in paths:
 if not src.exists():continue
 rel=src.relative_to(M).as_posix();assert not policy.exclude_path(rel)
 raw,stats=policy.project_bytes(rel,src.read_bytes());dst=D/rel;assert dst.resolve().is_relative_to(D.resolve());dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw);rows.append({'path':rel,'projected_sha256':hashlib.sha256(raw).hexdigest(),'transformed':stats['changed']})
save(O/'final-checkpoint-projection.json',{'at':now,'scope':'Explicit final metadata only, after full safe project synchronization; same source-exclusion policy.','files':rows,'source_files_deleted':False})
src=O/'final-checkpoint-projection.json';rel=src.relative_to(M).as_posix();raw,_=policy.project_bytes(rel,src.read_bytes());(D/rel).write_bytes(raw)
print(json.dumps({'final_website_commit':v['site_commit'],'metadata_files_projected':len(rows)+1,'memory_saved':True}))
