"""Record only independently checked and remotely verified publication state."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
R=Path(__file__).resolve().parent.parent;M=R/'research-assets/incoming-paper-monitor'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
V=read(R/'research-assets/github-public-delivery-verification.json')
assert V['status']=='passed' and V['build']['commit']==V['site_commit']
now=datetime.now(timezone.utc).isoformat()
for p in [R/'research-assets/github-publication-checkpoint.json',M/'latest-publication.json']:
 old=read(p);backup=p.with_name(p.stem+'-before-public-project-20260920.json')
 if not backup.exists():shutil.copyfile(p,backup)
release=read(M/'latest-publication.json')
release.pop('private_repository',None)
release.update(schema='mattersyn.publication-checkpoint.github.v2',recorded_at=now,
 project_repository='https://github.com/cuiyist/mattersyn',project_repository_visibility='public',
 scientific_dataset_published_at=release.get('scientific_dataset_published_at',release['published_at']),
 published_at=V['build']['updated_at'],commit_sha=V['site_commit'],project_commit_sha=V['project_commit'],
 publication_scope='Public project visibility, filtered history, citations and progress dashboard. Dataset0.23.0 scientific records unchanged.',
 new_source_ids=[],deployment={'provider':'github_pages','status':'built','source_branch':'main','source_path':'/','commit':V['site_commit']},
 anonymous_verification=V['anonymous'],
 current_worktrees={'authoring':str(R),'project_projection':str(R.parent/'mattersyn-github-project'),'website_projection':str(R.parent/'mattersyn-github-public-clean/mattersyn-site')},
 preserved_private_original_repositories=['https://github.com/cuiyist/mattersyn-source-archive-20260920','https://github.com/cuiyist/mattersyn-site-source-archive-20260920'],
 full_document_equivalents_excluded_from_public_history=True,
 history_projection_report='research-assets/public-history-projection-20260920/sanitized-history-report.json',
 filtered_initial_history_head='d5b2ede7f6ec02e8a12e66f5dc07163ad1693434',
 cutoff_manifest_sha256='8822a771eef5b01d52748a0c6882256de4a0a9a9e92675f3608b2e76fb15a519')
for p in [R/'research-assets/github-publication-checkpoint.json',M/'latest-publication.json']:
 p.write_text(json.dumps(release,indent=2)+'\n',encoding='utf8')
entry=f'''## 2026-09-20 — Public GitHub delivery verified; fixed-scope pilot proposal prepared

Saved {now}. BOTH repositories are now PUBLIC: https://github.com/cuiyist/mattersyn (project, code, memory, skills, structured work and filtered history) and https://github.com/cuiyist/mattersyn-site (website). Live website https://cuiyist.github.io/mattersyn-site/ ; saved progress https://cuiyist.github.io/mattersyn-site/progress.html . Both READMEs and REFERENCES.md contain31primarysourcecitations from the published dataset. Anonymous verification passed13website/data/figure requests, both repository endpoints and both citation READMEs. Pages built commit{V['site_commit']} at{V['build']['updated_at']}. Project uploaded commit{V['project_commit']}; later commits save this verification and the final proposal. Public-project visibility is complete; earlier pending/private policy entries are superseded.

The32development commits were preserved with message, author, dates and ancestry; first30commitIDs are unchanged and final2were mapped into a clean Git object store. Public filtering removed12556historical full-document-equivalent paths and embedded private first-page text, preserving structured facts, selected figures, memory, skills and audits. Historical source hashes continue to refer to local originals; filtered copies are not silently recertified scientific audits. The original repositories were preserved PRIVATELY as mattersyn-source-archive-20260920 and mattersyn-site-source-archive-20260920; local originals and their checkouts remain. No raw paper/SI binaries were added. Norberg's16completepageimages were removed from the public website;34public-image attachment fields were removed from its reader while its facts, source locators and24selectedscientificcrops remain. Independent projection audit passed19761checks and8offline delivery-guard tests. Root opened the Norberg TEM/XRD figure and checked the progress page in the browser. All470canonicalrecords remain byte-identical; no Heo publication or new exact structure–recipe pair is claimed.

CURRENT WORKING COPIES: authoring [local path redacted] ; public project projection [local path redacted] ; public website projection [local path redacted] . Use research-assets/sync_github_public.py with project/site, public_projection_policy.py, github_public_delivery.py and verify_public_delivery.py. The old private synchronizer is explicitly disabled and old-checkout remotes now point to their private preservation names. Never upload the unfiltered original source directory directly. Refresh build_public_progress.py and build_reference_readmes.py at meaningful milestones, independently check changed scientific content, coalesce publication as necessary, verify anonymous deployment, save memory and synchronize the public project. Existing5minuteheartbeat remains single; browser checks for published snapshots everyminute, not liveworkertelemetry.

The two-month deadline covers the fixed existing collection, with later new papers separate. Immutable cutoff at2026-09-20T03:34:39.542641Z:13831eligible documentcopies,9470knownpendingprovisionalscopes plus45unmappedfiles and3nestedheldcandidates. The target is2026-11-20UTC (November19local evening), not a validated completion forecast. active-cutoff.json and deadline-scope-partition.json preserve membership; use partition_deadline_scope.py against future ledgers and included_pending_group_ids as a mandatory selection filter after normal grouping. Late/changed SI for included papers reopens review. Current Heo work remains active. The generator does not itself mutate the monitor; the automation/work-owner must apply the filter before claiming additional work.

User authorized PREPARING an API pilot budget/capacity proposal, not paid execution. The proposal is research-assets/incoming-paper-monitor/deadline-20260920/PILOT_PROPOSAL.md with pilot-budget-model.json:50source-based screening decisions independently checked; up to20retainedpapers through full audit and publication; assumed API subtotal$57.80–$145.80, proposed$200cap. This is a model-token budget, not an all-in compute/expert price or a guaranteed quantity. No API key accessed or paid job started. Candidate samplev2 contains50nonrepeating DOI/main-hash samplingkeys; v1's duplicate candidate was preserved and replaced in the same stratum. This deliberately diverse QA sample is NOT a probability survey and cannot estimate corpus prevalence. A separate representative prevalence assessment and separately budgeted72hour throughput test are required before supporting the approximately190closedscopes/productionday target. Additional processing capacity remains unproven. Pilot pricing/sampling revision history is preserved. See the final proposal audit when saved.

'''
p=R/'MEMORY.md';p.write_text(entry+p.read_text(encoding='utf-8-sig'),encoding='utf8')
print(json.dumps({'public_delivery':'verified','site_commit':V['site_commit'],'project_commit_verified':V['project_commit'],'science_changed':False,'memory_saved':True}))
