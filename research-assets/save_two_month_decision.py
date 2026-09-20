"""Save the user's deadline and latest delivery state without changing scientific approval."""
from pathlib import Path
from datetime import datetime, timezone
import json

ROOT=Path(__file__).resolve().parent.parent
now=datetime.now(timezone.utc).isoformat()
decision={
 'saved_at':now,
 'user_target':'Complete the existing collection in two months; queue later arrivals separately.',
 'scope':'Both existing local paper collections. Immutable cutoff inventory is being prepared; a missing/late SI linked to an included paper must reopen that paper rather than silently disappear from the quality gate.',
 'deadline_status':'user_requested_target_not_yet_validated_capacity',
 'planning_days':60,
 'last_measured_pending_provisional_scopes':9470,
 'required_average_closures_per_day_60_days':9470/60,
 'required_average_closures_per_day_50_production_days':9470/50,
 'not_unique_papers':True,
 'new_arrivals_queue':'separate_from_deadline_collection',
 'quality':'Full available main/SI reading, extraction, source-linked figures/sample verification, independent per-paper audit and CdSe-standard reader for retained recipe papers. An independently evidenced no-recipe exclusion closes a scope without a website.',
 'capacity_plan_status':'benchmark_and_scaling_proposal_in_preparation; no paid API jobs, cloud services or purchased capacity started',
 'public_delivery':'Both cuiyist/mattersyn and cuiyist/mattersyn-site are now authorized public. Original paper/SI binaries and full-document text/page equivalents remain local. Project repository is still private until sanitized history is prepared and verified.',
 'actual_live_dataset':'0.23.0',
 'actual_live_records':470,
 'actual_live_material_hubs':42,
 'actual_live_sources':31,
 'batch_published':4,
 'batch_total':5,
 'heo':'All 14 SI pages have independently audited numeric transcription; 1209 rows, 7252 resolved numeric positions and 2 unresolved signs. Average-position/occupancy CIF candidate independently audited with explicit source conflicts and geometry caveats. Canonical and molecular proposals are frozen but their final audits/integration remain pending. Not published; no exact structure-recipe pair approved.'
}
out=ROOT/'research-assets/incoming-paper-monitor/two-month-decision.json'
out.write_text(json.dumps(decision,indent=2)+'\n',encoding='utf8')
entry=f'''## 2026-09-20 — Two-month target for a fixed collection; public project authorized

Saved {now}. The latest user instruction is to finish the EXISTING collection in two months and queue later arrivals separately. Prepare an immutable cutoff inventory of BOTH original source folders and retain the included scope IDs/file fingerprints; late or changed SI of an included paper reopens its evidence review. The last measured backlog is 9,470 provisional pending scopes (not verified unique papers). A 60-day target requires about158 scope closures/day, or190/day across50 production days with10 days reserved for calibration/final QA. These are required capacity, not achieved performance. The previous15–20/day scenario implies16–21months; it is not a validated delivery schedule. Expanded API processing, staffing and budget are proposals only; no paid service or API workload has been started. See research-assets/incoming-paper-monitor/two-month-decision.json and the dated capacity/cutoff artifacts when complete. Preserve independent audits and CdSe standards; no-recipe exclusion requires evidence, and automated title/text screening alone cannot close it.

The latest visibility choice supersedes ALL earlier private-project instructions: both cuiyist/mattersyn (code, data, memory, skills, development/audit history) and cuiyist/mattersyn-site (website) should be PUBLIC, with citations in both GitHub READMEs and maintained REFERENCES.md. Original papers and SI remain local. Publication preparation discovered full-text caches, embedded raw first-page text and full-page renders in the private backup; these are also excluded from public history. The current remote project remains PRIVATE while a fresh sanitized history is prepared; do not claim the visibility change is complete. Preserve the unfiltered local checkout. Current live dataset remains0.23.0 /470records /42hubs /31primarysources. Progress dashboard and31-source README citations are locally prepared and independently checked, but not yet deployed. Meaningful milestone snapshots, not unverified intermediate source data, will be synchronized.

Current scientific batch is4/5published. Heo main/SI source review now includes all14SIpages,1209reflectionrows,7252resolved numeric positions and2explicit unresolved signs. Complete-SI transport audit passed, as did the bounded average-position/occupancy CIF audit and correction addendum. This is not an exact structure–recipe or ordered DFT model approval. Frozen canonical proposal v1 and molecular assets still need their independent final binding audits; apparatus/reader integration, browser verification and publication remain pending. Earlier memory claiming SI13–14unread is superseded. Heo remains active; no new paper has been claimed or published in this update. All original evidence and historical audit freezes remain unchanged.

'''
p=ROOT/'MEMORY.md'
p.write_text(entry+p.read_text(encoding='utf-8-sig'),encoding='utf8')
print(json.dumps({'saved_at':now,'decision':str(out),'memory_updated':True,'paid_work_started':False}))
