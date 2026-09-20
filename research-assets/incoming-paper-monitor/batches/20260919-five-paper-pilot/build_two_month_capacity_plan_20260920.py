"""Private capacity arithmetic; assumptions remain distinct from observations."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from math import ceil
import json, hashlib

B=Path(__file__).resolve().parent
P=B/'eta-evidence-20260920.json'
raw=P.read_bytes(); eta=json.loads(raw)
assert hashlib.sha256(raw).hexdigest()=='a8bb5070ff9ed03bd1ceca3a093b4d2818e0625a7e1b4f9759edb16bcedc02ea'
N=eta['backlog']['pending_groups'];days=50
anchor=datetime.fromisoformat(eta['evidence_snapshot_at'])
rows=[];sensitivity=[]
# Durations below are deliberately assumptions, NOT a claim about agent speed.
screen_minutes=5; negative_check_minutes=5; utilization=0.8
for f in (.1,.25,.5,1):
 retained=ceil(N*f);negative=N-retained
 screening_hours=N*screen_minutes/60+negative*negative_check_minutes/60
 rows.append({'assumed_retained_fraction':f,'retained_papers_or_scopes_ceiling':retained,'excluded_after_checked_screening':negative,
  'all_scope_screening_per_processing_day':N/days,'retained_complete_and_published_per_processing_day':retained/days,
  'negative_dispositions_per_processing_day':negative/days,'independent_detailed_paper_audits_required':retained,
  'independent_negative_disposition_checks_required':negative,
  'retained_rate_multiple_of_short_observed_20_243_per_day':(retained/days)/eta['observed_calendar_output_windows'][0]['equivalent_per_24h'],
  'single_worker_per_stage_minutes_per_retained_at_24h_ignoring_screening_and_overhead':24*60/(retained/days),
  'maximum_combined_retained_worker_hours_if_3workers_24h_80percent_and_5min_screen_plus_5min_negative_check':
    (days*3*24*utilization-screening_hours)/retained})
 for combined_hours in (2,4,8):
  total=screening_hours+retained*combined_hours
  sensitivity.append({'assumed_retained_fraction':f,'combined_author_auditor_visual_worker_hours_per_retained_paper':combined_hours,
    'combined_worker_hours_required':round(total,2),
    'worker_slots_at_16h_available_per_day_80percent_utilization':ceil(total/(days*16*utilization)),
    'worker_slots_at_24h_available_per_day_80percent_utilization':ceil(total/(days*24*utilization)),
    'additional_coordinator_publication_slot_required':True})

out={
 'schema':'mattersyn-fixed-cutoff-two-month-capacity-plan/1','created_at':datetime.now(timezone.utc).isoformat(),
 'author':'/root/norberg2004_extract','status':'conditional_capacity_plan_not_a_delivery_commitment',
 'scope_authorization':'User accepted fixed existing collection. New arrivals are queued separately; no scope question remains pending.',
 'input':{'path':str(P),'sha256':hashlib.sha256(raw).hexdigest(),'folder_scan_at':eta['folder_scan_at'],
   'provisional_pending_scopes':N,'distinct_papers':None,'verified_recipe_retention_fraction':None,
   'caveat':'9470 is the last dated provisional worklist count. Freeze and deduplicate the exact newly accepted cutoff before setting a final denominator; do not equate copies, DOI groups, recipes or records with unique papers.'},
 'schedule':{'planning_anchor_UTC':anchor.isoformat(),'target_days':60,'calibration_days':3,'processing_days':50,'final_QA_days':7,
   'calibration_end_UTC':(anchor+timedelta(days=3)).isoformat(),'processing_end_UTC':(anchor+timedelta(days=53)).isoformat(),
   'target_finish_UTC':(anchor+timedelta(days=60)).isoformat(),
   'boundary_note':'Illustrative 60-day plan anchored to the frozen evidence timestamp, not a guaranteed deadline. A new exact cutoff can move these boundaries. Calendar dates: Sep23 calibration close, Nov12 processing close, Nov19 target in UTC. Progress completed in calibration is not credited in these conservative 9470/50 calculations.'},
 'required_rates':{'closed_scopes_per_day_over_60days':N/60,'closed_scopes_per_processing_day':N/50,'closed_scopes_per_7_processing_days':N/50*7,'daily_integer_planning_target':ceil(N/50)},
 'retention_scenarios':rows,
 'screening_not_retention':'Text-signal tiers are not true retention fractions: the prior 56.25% A/B/C candidate share is not evidence that 56.25% contain usable recipes, and low signal is not permission to discard a source.',
 'audit_contract':{'every_scope':'Main/SI pairing, stable identity/hash, source-based relevance decision; verified aliases close by documented duplicate mapping.',
   'retained_paper':'Complete required supplied-source extraction with field/page/sample provenance, original figures, independent scientific and canonical review, reader/visual checks and verified publication. Every retained paper receives its own independent audit.',
   'negative_scope':'A bounded independent source-based no-recipe disposition check before skipping; keyword absence alone cannot close the scope.',
   'source_missingness':'Missing/unreadable/local-SI-absent evidence remains explicit. Do not invent values or download without renewed authority. New evidence after cutoff is a separately tracked re-open decision.'},
 'runtime_capacity':{'current_concurrent_agents_including_root':4,'worker_agents_excluding_root':3,
   'typical_roles':['extraction/author','independent audit','reader/visual implementation','root coordination/integration/publication'],
   'batch_size_warning':'Increasing queued batch size does not increase this four-slot concurrency limit; author and auditor are separate work, not two independent paper streams.',
   'measured_active_hours_per_day':None,'guaranteed_24h_runtime':False,
   'condition':'The stage with the smallest validated daily capacity limits the whole pipeline. External worker capacity is useful only with isolated outputs, distinct audit identity, stable contracts and one integration queue.'},
 'capacity_equations':{
   'combined_worker_hours':'H = N*s/60 + (N-R)*q/60 + R*(e+a+v), where R is retained scopes, s is first-screen minutes/scope, q is independent negative-check minutes/scope, and e+a+v is total extraction, independent audit and reader/visual worker-hours per retained paper.',
   'worker_slots':'W >= ceil(H/(50*d*u)), d = actually available hours/day per worker; u = productive fraction after interrupts/rework. Root publication/integration capacity must also be checked independently.',
   'stage_bottleneck':'Daily pipeline output <= min(author capacity, independent audit capacity, visual/reader capacity, root integration/deployment capacity), with rework returning to its owning stage.',
   'elapsed_vs_effort':'Combined worker-hours add author/auditor/visual effort and can run in parallel; they are not a claimed calendar latency per paper.'},
 'illustrative_staffing_sensitivity':{'assumed_first_screen_minutes_per_scope':screen_minutes,
   'assumed_independent_negative_check_minutes_per_negative_scope':negative_check_minutes,
   'assumed_productive_fraction':utilization,'measured':False,
   'caveat':'These 5-minute/2–8-hour/16–24-hour assumptions are arithmetic examples only. They cannot replace the three-day measured benchmark; no promise that a paper can be reviewed in five minutes or that 24-hour availability exists. Counts exclude a coordinator/publication slot.',
   'rows':sensitivity},
 'calibration_and_go_no_go':[
   'Freeze a manifest of the accepted existing scope with per-source hashes and main/SI pairing candidates. Route later arrivals to a separate queue immediately.',
   'During three days, finish a stratified sample of roughly 30–50 source dispositions where feasible, including low-signal, recipe-rich, SI-heavy and scanned-table cases. Retained samples must actually reach their independent audits and publication before counting throughput; preserve incomplete samples as censored.',
   'Estimate retention using the sampling weights rather than an unweighted mix of convenient rich papers; report its uncertainty. Measure stage worker-hours and calendar throughput, rework rate, missing-source share and deployment capacity.',
   'Use conservative measured stage capacities and upper-range effort, not the fastest papers. A two-month commitment is justified only if every pipeline stage can meet its required rate with rework headroom.',
   'If the measured requirement exceeds four available slots, obtain separately provisioned API/cloud/human review workers or revise the completion scope/deadline explicitly. No amount of increasing a batch list alone bypasses the runtime limit.'
 ],
 'acceleration_without_lowering_quality':[
   {'change':'Cache deterministic preprocessing once per source hash','purpose':'Native text extraction, OCR, page renders, tables and main/SI candidate matching become reusable inputs; source changes trigger bounded rechecks rather than replaying the entire pipeline.'},
   {'change':'Generate all reader views from approved canonical data','purpose':'Use the academic CdSe-standard template and stage-specific diagram engine across materials. Reuse qualified chemical/host-reference assets with separate sample bindings; audit the scientific association for every paper.'},
   {'change':'Separate extraction, independent audit and visual work into balanced queues','purpose':'Keep available workers busy on different papers without allowing an author to self-approve. Record pass/fix/recheck states and exact file hashes.'},
   {'change':'Automate lossless validation and uncertainty routing','purpose':'Check units, arithmetic, required fields, source pointers, duplicate specimens, table joins and rendering completeness mechanically; send scan ambiguities and scientific conflicts to manual source inspection. Automated validators do not replace independent reading.'},
   {'change':'Batch reviewed releases','purpose':'Publish several approved papers together with incremental site checks and anonymous delivery verification, reducing repeated deployment overhead. Keep every paper separately auditable.'},
   {'change':'Provision measured additional workers when needed','purpose':'User can provide funded API/cloud compute or trained curators and a single controlled work queue. Benchmark throughput and review quality before increasing concurrency. This session remains limited to four agent slots; no prices assumed.'}
 ],
 'new_arrivals_separate':{'user_reported_documents_per_day':1000,'illustrative_documents_over_60days':60000,
   'unique_papers_over_60days':None,'recipe_papers_over_60days':None,'included_in_fixed_deadline':False,
   'policy':'Monitor and index arrivals into a separate queue without allowing them to consume the accepted fixed-backlog review budget. New SI for an existing cutoff paper is tracked as a source revision requiring an explicit cutoff policy.'},
 'assessment':'Two months is a capacity target, not yet demonstrated by current evidence. Low recipe retention plus strong reuse may fit with less expansion; 25–100% retention demands substantially higher validated throughput and likely separately provisioned workers. Do not promise completion before calibration.',
 'no_mutations':'Private plan JSON/Markdown/helper only; no queue, memory, website, repository, source or automation changes.'
}
J=B/'two-month-capacity-plan-20260920.json';J.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
table='\n'.join(f"| {int(x['assumed_retained_fraction']*100)}% | {x['retained_papers_or_scopes_ceiling']:,} | {x['retained_complete_and_published_per_processing_day']:.2f} | {x['negative_dispositions_per_processing_day']:.2f} |" for x in rows)
st='\n'.join(f"| {int(x['assumed_retained_fraction']*100)}% | {x['combined_author_auditor_visual_worker_hours_per_retained_paper']} h | {x['worker_slots_at_16h_available_per_day_80percent_utilization']} | {x['worker_slots_at_24h_available_per_day_80percent_utilization']} |" for x in sensitivity if x['combined_author_auditor_visual_worker_hours_per_retained_paper']in(2,4))
md=f'''Two-month capacity plan — 20 September 2026 UTC

The user accepted **the fixed existing collection**; new arrivals go into a separate queue. The last dated denominator is **9,470 provisional review scopes**, subject to the exact cutoff inventory and confirmed duplicate/main–SI reconciliation. This is not a verified unique-paper or recipe total.

Allocate **3 days for calibration, 50 days for processing, 7 days for final QA**. From the frozen September 20 UTC planning anchor, the 60-day target is **November 19 UTC**, with processing ending November 12. This is a planning target, not a promise.

All 9,470 scopes need screening and a documented disposition: **189.4 scopes/day**, about **190/day**, or **1,326/week** during processing. The retained-paper workload depends on the true recipe fraction:

| Hypothetical recipe retention | Retained papers/scopes | Fully audited and published/day | Checked no-recipe dispositions/day |
|---:|---:|---:|---:|
{table}

Every retained paper still gets an independent scientific audit, complete source-linked extraction, reader/visual checks and publication. Negative decisions also require a bounded independent source check; a low text score is not an exclusion. Prior text-signal shares do not establish the retention fraction.

**Four agent slots currently means root plus three workers**, roughly author, auditor and visual/reader work with root integrating releases. More papers in a batch do not create more workers. At 25% retention, a dedicated stage working 24 hours/day would have only about 30 minutes per paper before screening, interruptions and rework; at 100%, about 7.6 minutes. These are required rates, not demonstrated capacities.

For a transparent staffing sensitivity only, suppose first screening takes 5 worker-minutes/scope, a negative audit another 5 minutes, productive utilization is 80%, and the retained paper takes the combined author + independent audit + reader/visual worker-hours below. Required workers exclude one coordinator/publication slot:

| Assumed retention | Combined hours/retained paper | Workers at 16 available h/day | Workers at 24 available h/day |
|---:|---:|---:|---:|
{st}

**None of those durations or availability assumptions is measured.** They show why a benchmark is needed and why money/tokens alone do not guarantee a deadline. Combined worker-hours are parallel effort, not elapsed time for one paper. The current three workers cannot be treated as multiple complete independently audited pipelines.

The first three days should close a stratified calibration sample, including weak-signal, rich, scanned and SI-heavy sources; measure retention with sampling weights, stage effort, rework and actual end-to-end publications. Keep unfinished examples visible. Commit to the two-month target only when the slowest stage meets its required rate with headroom.

Acceleration that preserves the standard:

1. Cache source-hash-based text/OCR, tables, page images and main/SI pairing once; reuse unchanged evidence.
2. Generate the CdSe-standard academic reader, molecules and stage-specific diagrams from canonical records and qualified shared assets; independently check each sample/chemical binding.
3. Balance separate author, independent audit and reader/visual queues. Automate mechanical checks; manually resolve uncertain source glyphs and scientific conflicts.
4. Publish several completed papers per release, with per-paper audits and incremental validation.
5. If the calibration exceeds four-slot capacity, provision separate API/cloud workers or trained curators under the same evidence/audit contracts. Benchmark those workers before scaling; no pricing assumptions are made here.

The reported inflow would add roughly **60,000 documents over 60 days**, not necessarily 60,000 papers. It is excluded from this accepted deadline and queued separately. Late SI for a cutoff paper is a versioned source change, not a silently changed completion claim.

Conclusion for planning: **two months is not yet supported by measured capacity**. A low retained fraction could make it much easier; 25–100% retention requires sharply higher verified output. Retention cannot be chosen to make the schedule fit.

Frozen ETA source SHA256: `{hashlib.sha256(raw).hexdigest()}`. Only private planning artifacts were written.
'''
MD=B/'two-month-capacity-plan-20260920.md';MD.write_text(md,encoding='utf-8')
print(json.dumps({'status':'saved','json':str(J),'json_sha256':hashlib.sha256(J.read_bytes()).hexdigest(),'markdown_sha256':hashlib.sha256(MD.read_bytes()).hexdigest(),'target_UTC':out['schedule']['target_finish_UTC'],'required_all_scope_daily_rate':N/days,'retained_rates':[x['retained_complete_and_published_per_processing_day']for x in rows]},indent=2))
