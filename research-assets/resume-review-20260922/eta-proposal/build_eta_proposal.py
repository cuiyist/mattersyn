"""Compose a bounded ETA proposal from saved evidence; no source/monitor writes."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, hashlib, math

P=Path(__file__).resolve().parent
M=P.parents[1]/'incoming-paper-monitor'
bound={}
def read(path):
    path=Path(path); data=path.read_bytes(); bound[str(path)]=hashlib.sha256(data).hexdigest()
    return json.loads(data)
def save(name,obj):
    path=P/name; path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); return path
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

baseline=read(P/'state-inspection.json')
scope=read(P/'scope-evidence-current.json')
through=read(P/'throughput-support/observed-throughput.json')
partition=read(M/'deadline-20260920/resume-20260922/resume-partition.json')
control=read(M/'review-control.json')
decision=read(M/'two-month-decision.json')
publication=read(M/'latest-publication.json')
skip=read(M/'reviews/cen-v076n039-p008/independent-audit.json')
coverage=read(M/'deadline-20260920/workflow-20260920T0412/screen-coverage-check.json')
now=datetime.now(timezone.utc)
n=scope['partition_counts']['included_pending_scopes']
window=through['windows']['new_cohort_claim_to_last_verified_closure']
rate=window['event_count']/window['elapsed_hours']
deadline=datetime.fromisoformat('2026-11-20T03:34:39.542641+00:00')
remaining_days=(deadline-now).total_seconds()/86400
rows=[]
for h in (8,16,24):
    perday=rate*h; days=n/perday
    rows.append({'id':f'observed_cadence_{h}h_day','label':f'Observed selected-cohort cadence sustained for {h} hours/day',
                 'classification':'unvalidated_conditional_extrapolation_not_forecast',
                 'assumed_pipeline_hours_per_day':h,'verified_scope_closures_per_day':perday,
                 'remaining_scope_count':n,'duration_days':days,'duration_years':days/365.25,
                 'duration_label':f'about {round(days):,} days',
                 'conditions':'Every pending scope requires comparable full treatment; same concurrent team cadence; no downtime, new evidence, missing-source delays or extra pipeline restart cost.'})
terminal=scope['terminal_scopes']
assert len(terminal)==32 and all(x['milestones'][k]['status']=='complete' for x in terminal if x['status']=='complete' for k in ['read','extract','audit','integrate','publish'])
assert skip['status']=='passed'
assert partition['counts']==scope['partition_counts']
assert sum(scope['pending_cutoff_tier_counts'].values())==n==9500
assert len(through['rows'])==9
assert abs(rate-0.6993824118980879)<1e-12
assert all(row['public_verification_status']=='passed' for row in through['rows'])

out={
 'schema':'mattersyn.readonly-eta-proposal/1','generated_at':now.isoformat(),'author':'/root/backlog_eta',
 'status':'bounded_readonly_analysis_complete','is_completion_promise':False,
 'scope':'Existing fixed-cutoff collection; later arrivals reported separately. No source scan, claim, review, paid call, ledger/control or Site modification by this task.',
 'as_of':{'source_scan_at':scope['ledger_last_scan_at'],'scope_read_at':scope['read_at'],
          'ledger_sha256_at_scope_read':next(v for k,v in scope['bound_files'].items() if k.endswith('ledger.json')),
          'current_control_status_at_report_read':control.get('status'),
          'earlier_pause_snapshot_at':baseline['at'],
          'note':'The saved Sep20 queue-status and old9470-pending decision are historical. Root separately resumed work after user authorization; this report does not authorize or change automation.'},
 'workload':{
   'cutoff_utc':'2026-09-20T03:34:39.542641+00:00','immutable_top_level_file_copies':13831,
   'known_included_provisional_scopes':9532,'pending_including_active':n,
   'pending_statuses_at_scope_read':dict(Counter(x['review_status'] for x in scope['pending_tier_rows'])),
   'closed_scopes':32,'retained_published_scopes_with_all_five_milestones':31,
   'independently_audited_exclusion_scopes':1,'no_recipe_enum_closures':0,
   'exclusion_detail':{'group_id':'10.1021_cen-v076n039.p008','title':skip['title'],'source_type':'secondary_news',
                      'meaning':'No reproducible primary synthesis/sample dataset; one supplied page independently reviewed. Private contextual information retained; publication not applicable.'},
   'nested_cutoff_candidates_held':3,'unmapped_top_level_cutoff_files':0,
   'pending_cutoff_scopes_without_main_candidate':328,
   'later_arrival_candidate_groups':3136,'later_arrival_document_copies':3777,
   'total_pending_groups_all_arrivals':12636,
   'unique_paper_count':None,'retained_fraction_of_pending':None,
   'denominator_caveat':'Scopes and file copies are not unique papers, recipes or materials. Pending aliases, evidence gaps and retention/exclusion yield are unresolved. Nested candidates are additional held identity work.',
   'cutoff_reconciliation':'Original9470pending+22closed used an incomplete group mapping with45unmapped cutoff files. Current9500pending+32closed reflects40additional mapped scopes and10closures, not a changed file cutoff.',
   'changed_si_policy':'Changed/new SI belonging to an included paper reopens that included scope; it is not excluded as a later new paper.',
   'generation_checks':'Four cutoff-to-current generation consistency checks are present, not four asserted unresolved re-reviews.'},
 'screening':{
   'type':'Automated text-layer evidence ranking; not complete independent scientific reading',
   'cutoff_document_copies_dispositioned':13831,'text_screened_candidates':13593,
   'manual_format_or_text_review_required_copies':238,
   'pending_cutoff_tiers':scope['pending_cutoff_tier_counts'],
   'retained_scientific_papers_inferred_from_tiers':False,
   'note':'A/B/C are evidence candidates, not verified coordinate/recipe pairings; D remains unreviewed rather than excluded; U requires manual reading/format resolution. All9500 pending scopes still need a defensible source disposition. Cached bulk text processing speed is not scientific review throughput.'},
 'published_collection_context':{
   'last_scientific_release_timestamp':'2026-09-20T17:11:29Z','last_scientific_dataset_version_in_receipt':'0.33.0',
   'canonical_records':675,'routes':123,'material_hubs':50,'source_groups':41,'formal_readers':36,
   'note':'Website counts include pre-monitor/historical contributions and use different denominators from31cutoff queue publications. Reader redesign releases do not constitute new paper completions. No new exact training label is inferred.'},
 'observed_throughput':{
   'window':window,'cohort_sources':[x['source_id'] for x in through['rows']],
   'claim_to_closure_minutes':through['claim_to_closure_minutes'],
   'source_only_window':through['windows']['new_cohort_claim_to_last_source_audit'],
   'steady_interclosure_window':through['windows']['new_cohort_between_first_and_last_closure'],
   'scope_notes':['Eight supplied main+SI scopes; Sommer supplied-main scope with SI unlocated/unverified.',
                  'Heo carry-over was claimed the prior day and excluded from the nine-new-scope denominator.',
                  'Elapsed overlapping workflow throughput, not single-agent labor; nine deliberately evidence-rich selections, not a representative sample.',
                  '0.699 and0.803 differ by cohort boundary and are not confidence bounds. Progress-only publication timestamps are not scientific completions.']},
 'public_scenario_rows':rows,
 'two_month_capacity_requirements':{
   'classification':'required_capacity_not_achieved_rate','original_deadline_utc':deadline.isoformat(),
   'days_remaining_from_report_time':remaining_days,'required_scope_closures_per_day_original_deadline':n/remaining_days,
   'required_per_pipeline_hour_if24h_day':n/remaining_days/24,
   'multiple_of_observed_full_pipeline_cadence_if24h_day':n/remaining_days/24/rate,
   'fresh60_production_days_required_per_day':n/60,'fresh50_production_days_required_per_day':n/50,
   'observed_rate60day_capacity_if24h_day':rate*24*60,
   'note':'The original two-calendar-month target remains Nov20; a fresh60day scenario does not reset it. Faster rejection/duplicate closure may reduce effort, but neither its rate nor corpus yield has been measured.'},
 'current_two_scope_planning_allowance':{
   'group_ids':['legacy::10.1021_acsami.3c08812','legacy::10.1021_acsami.8b04556'],
   'classification':'intake_informed_planning_only_no_combined_pair_eta',
   'intake_count_provenance':'Root handoff during this ETA audit; counts were supplied by the source teams, not independently re-read by this ETA task.',
   'papers':[{'source':'Saini2023','main_pages':12,'si_pages':107,
              'scope':'NAT-CQD preparation, multiple nanoaminocatalytic protocols and extensive organic product spectra',
              'planning_window':'Longer, potentially days; no calibrated duration available for this source size and scope.',
              'measured_eta':False},
             {'source':'Chen2018','main_pages':8,'si_pages':10,
              'scope':'Cs4PbBr6 refined tables plus fixed/minority CsPbBr3 coordinates',
              'planning_window':'A few hours is only a provisional small-paper planning allowance; structure validation or corrections may extend it.',
              'measured_eta':False}],
   'conditions':'Do not apply one universal hours-per-paper estimate to both sources. Source teams must revise after detailed inventory and structure/chemistry assessment.'},
 'recommendation':'Resume the fixed-cutoff queue with later arrivals separate; retain all scientific gates. Treat whole-backlog duration as conditional, on the order of18–19months at continuously sustained current depth, longer with limited daily runtime. Re-estimate after20–50 resumed, independently disposed scopes across evidence tiers, recording active elapsed windows and separate retained/excluded/duplicate/missing-source outcomes. No two-month completion commitment is supported by current measurements.',
 'historical_input_hashes_at_read':{'pre_resume':baseline['bound_files'],'post_scan_scope_snapshot':scope['bound_files']},
 'bound_files':bound,
 'qa':{'cutoff_pending_tier_sum':n,'fresh_partition_matches_independent_recomputation':True,
       'all31_retained_scopes_have_read_extract_audit_integrate_publish_complete':True,
       'one_exclusion_independent_audit_passed':True,'nine_new_cohort_release_verifications_passed':True,
       'scientific_full_paper_reaudit_performed':False,'shared_files_written':False}
}
save('eta-proposal.json',out)
md=f'''# Remaining MatterSyn review: bounded ETA proposal

As of the saved source scan at {scope['ledger_last_scan_at']}, **9,500 fixed-cutoff review scopes remain**, including the two resumed claims. These are provisional scopes, not a verified unique-paper total. A further **3,136 later-arrival groups / 3,777 file copies** are separate. The cutoff remains20September2026,03:34:39UTC.

Of9,532 included scopes, **31 have complete reading, extraction, audit, integration and publication milestones**, and **one secondary-news item was independently reviewed and excluded from scientific publication**. Three nested files remain held for identity work;328pending scopes lack a main candidate. Website totals (675records,41sourcegroups,36readers) use different denominators and cannot be counted as675completed papers.

Automated screening dispositioned all13,831cutoff document copies:13,593text candidates and238manual-format/text cases. It did not fully read their figures/SI or independently verify recipes. Remaining evidence tiers are: A coordinate/recipe candidates1; B recipe/crystalline candidates3,920; C recipe candidates1,279; D low signal4,252; U manual48. **No low-signal tier is an exclusion, and the retained fraction is unknown.**

The defensible recent measure is **nine new scopes closed in12.8685elapsed hours:0.6994/hour**. Individual claim-to-closure times were103–174minutes (median140), with overlapping work. Eight had supplied main+SI; Sommer had main only with SI unverified. Heo was carry-over and is excluded. The cohort was selected for strong evidence, so it does not establish a representative corpus rate.

| Conditional same-depth scenario | Closures/day | Duration for9,500scopes |
|---|---:|---:|
'''
for row in rows:
    md+=f"| {row['assumed_pipeline_hours_per_day']}pipeline hours/day | {row['verified_scope_closures_per_day']:.2f} | about{row['duration_days']:,.0f}days ({row['duration_years']:.2f}years) |\n"
md+=f'''
These are **unvalidated linear extrapolations, not forecasts or commitments**. They assume every remaining scope needs comparable treatment and ignore downtime, missing-source delays and rework. Independent exclusions/duplicate reconciliation could reduce effort, but their yield and speed have not been measured. New or changed SI for an included source must reopen its review.

The original20November2026target requires **{n/remaining_days:.1f}verified closures/day** from this report time—about{n/remaining_days/24/rate:.1f}times the measured cadence even with24-hour operation. A fresh60production days would require158.3/day (50days:190/day); at observed cadence24/7,60days yields only about{rate*24*60:,.0f}full-work closures. Two months is not supported by current throughput.

The current intake is unequal: root reports **Saini2023:12main+107SIpages**, including extensive organic spectra and several protocols; **Chen2018:8main+10SIpages**, including refined/fixed structure tables. There is **no calibrated combined-pair ETA**. Chen may fit a provisional few-hour planning window; Saini warrants a longer, potentially days-long allowance pending complete scope assessment. These counts come from the source teams, not a repeated source audit here. Re-estimate the backlog after20–50resumed dispositions across tiers, separately tracking retained contributions, independent exclusions, duplicates and unavailable evidence.

Only private ETA artifacts were written. Root owns resumption, claims and shared-state changes. The stale9470decision and Sep20queue snapshot were preserved as historical evidence; the fresh partition and independently recomputed counts agree. Exact input hashes, cohort endpoints and calculation fields are in`eta-proposal.json`; detailed timing evidence is in`throughput-support/observed-throughput.json`.
'''
# Human-readable spacing in generated prose is deliberate, not a source transformation.
for a,b in [('cutoff remains20','cutoff remains 20'),('20September2026,03:34:39UTC','20 September 2026, 03:34:39 UTC'),('Of9,532','Of 9,532'),('328pending','328 pending'),('675records,41sourcegroups,36readers','675 records, 41 source groups, 36 readers'),('as675completed','as 675 completed'),('all13,831cutoff','all 13,831 cutoff'),('copies:13,593text','copies: 13,593 text'),('and238manual','and 238 manual'),('candidates1;','candidates 1;'),('manual48','manual 48'),('in12.8685elapsed','in 12.8685 elapsed'),('hours:0.6994/hour','hours: 0.6994/hour'),('were103–174minutes','were 103–174 minutes'),('(median140)','(median 140)'),('for9,500scopes','for 9,500 scopes'),('pipeline hours',' pipeline hours'),('about1,','about 1,'),('about849','about 849'),('about566','about 566'),('20November2026target','20 November 2026 target'),('with24-hour','with 24-hour'),('fresh60production','fresh 60 production'),('(50days:190/day)','(50 days: 190/day)'),('cadence24/7,60days','cadence 24/7, 60 days'),('2–4hours','2–4 hours'),('after20–50resumed','after 20–50 resumed'),('stale9470decision','stale 9,470 decision'),('Sep20queue','Sep 20 queue'),('in`eta','in `eta'),('in`throughput','in `throughput')]:
    md=md.replace(a,b)
md=md.replace('Saini2023:12main+107SIpages','Saini 2023: 12 main + 107 SI pages').replace('Chen2018:8main+10SIpages','Chen 2018: 8 main + 10 SI pages')
for a,b in [(';328','; 328'),('candidates3,920','candidates 3,920'),('candidates1,279','candidates 1,279'),('signal4,252','signal 4,252'),('days (',' days ('),('years)',' years)'),('original20','original 20'),('verified closures/day',' verified closures/day'),('—about','—about '),('times the',' times the'),('require158.3','require 158.3'),('full-work closures',' full-work closures')]:
    md=md.replace(a,b)
(P/'eta-proposal.md').write_text(md,encoding='utf-8')
manifest={'schema':'mattersyn.eta-proposal-manifest/1','generated_at':now.isoformat(),'author':'/root/backlog_eta',
          'files':{str(p):sha(p) for p in [P/'eta-proposal.json',P/'eta-proposal.md',P/'state-inspection.json',P/'scope-evidence-current.json',P/'build_eta_proposal.py',P/'derive_scope_snapshot.py',P/'throughput-support/observed-throughput.json',P/'throughput-support/observed-throughput.md']}}
save('package-manifest.json',manifest)
print(json.dumps({'report_sha256':sha(P/'eta-proposal.json'),'manifest_sha256':sha(P/'package-manifest.json'),
                  'required_daily_original_deadline':n/remaining_days,'scenarios':rows},indent=2))
