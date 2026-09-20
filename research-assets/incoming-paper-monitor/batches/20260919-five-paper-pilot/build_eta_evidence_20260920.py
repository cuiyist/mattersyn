"""Read-only checkpoint synthesis; writes only private dated ETA artifacts."""
import json, hashlib, math
from pathlib import Path
from datetime import datetime, timedelta, timezone

B = Path(__file__).resolve().parent
M = B.parent.parent
bound = {}

def read(p):
    p = Path(p)
    raw = p.read_bytes()
    bound[str(p)] = {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return json.loads(raw.decode("utf-8-sig"))

def bind(p):
    p = Path(p)
    raw = p.read_bytes()
    bound[str(p)] = {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    return bound[str(p)]

def dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

ledger = read(M / "ledger.json")
queue = read(M / "queue-status.json")
scan = read(B / "scan-20260920T0238.json")
publication = read(M / "latest-publication.json")
workflow = read(B / "workflow-state.json")
screen = read(M / "corpus-screening/20260919/reports/d5d9e7efb9dabecd2f46e6d6bfde6be650f0b58de30864c2d44485b16e819d0f.json")
backfill = read(M / "published-source-backfill-audit.json")
heo = read(B / "jp0219348/comprehensive-source-checkpoint.json")
mapping = read(B / "jp0219348/canonical-mapping-plan.json")
earlier_scan = read(B / "resume-scan.json")
index = read(B / "source-review-index.json")

matched = {"10.1021_ja9805425", "10.1021_ja035980c", "10.1021_ja036811v", "10.1021_ja0496423", "10.1021_la036034c", "10.1021_ja048427j"}
completed = []
excluded = []
for gid, group in ledger["groups"].items():
    review = group["review"]
    if review["status"] not in ("complete", "no_useful_information"):
        continue
    milestones = review["milestones"]
    audit_evidence = [bind(p) for p in milestones["audit"]["evidence"]]
    pubs = []
    for p in milestones["publish"]["evidence"]:
        if Path(p).name == "publication-checkpoint.json":
            checkpoint = read(p)
            pubs.append({"path": p, "status": checkpoint.get("status"), "published_at": checkpoint.get("published_at"), "sha256": bound[str(Path(p))]["sha256"]})
    entry = {
        "group_id": gid, "title": review["checkpoint"].get("title"),
        "status": review["status"], "review_updated_at": review.get("updated_at"),
        "first_recorded_status_at": review.get("history", [{}])[0].get("at"),
        "milestones": {k: v.get("status") for k, v in milestones.items()},
        "recorded_read_scope": milestones["read"].get("note"),
        "source_scope_class": "supplied_main_and_matched_SI" if gid in matched else "supplied_main_only_SI_unverified",
        "publication_checkpoints": pubs, "audit_evidence": audit_evidence,
        "interpretation": "Evidence-file bookkeeping only; the ETA author did not freshly scientifically re-audit these papers. First history entry is not a reliable work-start timestamp."
    }
    if review["status"] == "complete":
        assert all(milestones[x]["status"] == "complete" for x in ("read", "extract", "audit", "integrate", "publish"))
        assert len(pubs) == 1 and pubs[0]["status"].startswith("published")
        completed.append(entry)
    else:
        entry["source_scope_class"] = "one_page_secondary_news_audited_no_recipe_disposition"
        excluded.append(entry)

assert len(completed) == 21 and len(excluded) == 1
assert sum(x["source_scope_class"] == "supplied_main_and_matched_SI" for x in completed) == 6
assert scan["pending_groups"] == 9470 and scan["canonical_review_units"] == 9492
snapshot = dt(queue["generated_at"])
claim = dt(queue["batch"]["claimed_at"])
pub = dt(publication["published_at"])
window_hours = (snapshot - dt(ledger["created_at"])).total_seconds()/3600
batch_hours_to_pub = (pub - claim).total_seconds()/3600
batch_hours_to_snapshot = (snapshot - claim).total_seconds()/3600
scenarios = []
for rate in (10, 13, 15, 20, 30):
    days = 9470/rate
    scenarios.append({"closed_provisional_scopes_per_calendar_day": rate,
        "days": round(days, 1), "months_at_30_4375_days": round(days/30.4375, 1),
        "illustrative_finish_date_UTC": (snapshot+timedelta(days=math.ceil(days))).date().isoformat()})
tiers = screen["counts"]["priority_tiers"]
tier_rows = [{"tier": k, "candidate_scopes": v, "percent_of_9187": round(v/9187*100, 3)} for k, v in tiers.items()]
duration_downstream = (pub-dt("2026-09-19T23:12:18.474217+00:00")).total_seconds()/3600
arrival_hours = (dt(scan["last_scan_at"])-dt(earlier_scan["last_scan_at"])).total_seconds()/3600
arrival_copies = scan["present_files"]-earlier_scan["present_files"]
result = {
    "schema": "mattersyn-private-eta-evidence/1",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "author": "/root/norberg2004_extract",
    "evidence_snapshot_at": queue["generated_at"], "folder_scan_at": scan["last_scan_at"],
    "scope": "Existing two-folder provisional worklist only; later arrivals separate. This is checkpoint/throughput analysis, not a fresh paper audit, source scan, publication, or task scheduling action.",
    "backlog": {k: scan[k] for k in ["source_document_copies", "present_files", "groups", "canonical_review_units", "confirmed_duplicate_main_aliases", "pending_groups", "active_review_claims", "waiting_review_scopes", "distinct_paper_total", "normalized_doi_candidates", "groups_without_main_candidate", "count_note"]},
    "count_reconciliation": "9515 group labels - 23 confirmed main aliases = 9492 provisional scopes; 9492 - 21 published-scope completions - 1 audited exclusion = 9470 pending (9469 waiting + 1 active). Copies, scopes, DOI candidates, records, recipes and independent experiments are different units.",
    "publication_snapshot": {k: publication[k] for k in ["public_url", "dataset_version", "published_at", "commit_sha", "record_count", "synthesis_route_count", "material_hub_count", "public_source_group_count", "remaining_batch_papers"]},
    "formal_review_count_caveat": "The queue inventory reports 11 formal main/SI first-pass sources; this is not the number of newly completed independent paper audits. Earlier baseline had 10 published source groups with heterogeneous coverage; those are not added to the throughput numerator.",
    "completed_scope_counts": {"recorded_audited_and_published": 21, "supplied_main_plus_matched_SI": 6, "supplied_main_only_SI_unverified": 15, "audited_no_recipe_exclusions": 1, "active": 1},
    "completed_papers": completed, "excluded_papers": excluded,
    "selection_disposition_limits": {"closed_selected_scopes": 22, "published_contribution_fraction": 21/22, "audited_exclusion_fraction": 1/22, "population_recipe_retention_fraction": None, "note": "Selected tiny, biased sample; published contribution is not a verified independently executable recipe. Do not use 21/22 as a corpus retention estimate."},
    "screening": {"screened_at": screen["screened_at"], "source_snapshot_at": screen["source_ledger_last_scan_at"], "screened_provisional_scopes": 9187,
        "screened_document_copies": 13474, "scientific_review_performed": False, "candidate_tiers": tier_rows,
        "A_B_C_candidate_total": 5168, "A_B_C_candidate_percent": round(5168/9187*100, 3),
        "current_pending_unranked_scopes": 305,
        "caveat": "Text/metadata ranking only. The 3971 low-signal candidates are not audited no-recipe exclusions. None of these tier shares establishes recipe retention, unique materials, verified CIF pairs or full reading."},
    "observed_calendar_output_windows": [
        {"name": "all_monitor_completions", "start": ledger["created_at"], "end": queue["generated_at"], "calendar_hours": window_hours, "published_scope_completions": 21, "equivalent_per_24h": 21/window_hours*24},
        {"name": "current_batch_claim_to_fourth_publication", "start": queue["batch"]["claimed_at"], "end": publication["published_at"], "calendar_hours": batch_hours_to_pub, "published_papers": 4, "fifth_unfinished": True, "equivalent_per_24h": 4/batch_hours_to_pub*24},
        {"name": "current_batch_claim_to_status_snapshot", "start": queue["batch"]["claimed_at"], "end": queue["generated_at"], "calendar_hours": batch_hours_to_snapshot, "published_papers": 4, "fifth_unfinished": True, "equivalent_per_24h": 4/batch_hours_to_snapshot*24}
    ],
    "throughput_limits": [
        "Calendar throughput, not measured active hours, person-hours or per-paper latency. Activity, idle time, parallel work, setup and interruptions are not separately logged.",
        "Less than 25 hours, only 21 completed scopes, non-random older/selected sources; scope/complexity differs substantially and SI may be missing.",
        "The current batch is right-censored: four finished while the most demanding scanned-SI paper remains in progress. Dividing elapsed time by four cannot forecast the fifth or establish steady-state speedup.",
        "Published means completed to the explicitly supplied-source scope and preserved gaps, not every possible structure/property task; new or changed SI reopens work."
    ],
    "fixed_batch": {
        "published": 4, "remaining_paper": "Heo 2003, DOI 10.1021/jp0219348", "remaining": 1,
        "current_checkpoint_at": heo["at"], "current_status": heo["status"],
        "source_progress": "9 main pages and all 14 scanned SI pages reviewed; combined 1209-row SI independently reconciled; two signs explicitly unresolved. Source/average-model audits do not close canonical or publication gates.",
        "next_steps": heo["next_steps"],
        "canonical_status": mapping["status"],
        "firm_estimated_finish_at": None,
        "root_planning_estimate": {"additional_active_work_hours": [3, 6], "confidence": "low", "source": "Root work-owner message on 2026-09-20 after inspecting remaining canonical, molecule/apparatus/reader and independent QA work.", "measured_duration": False, "calendar_deadline": None, "caveat": "Planning judgement, not inferred from the historical output windows; interruptions or audit findings can extend it."},
        "rough_remaining_time_basis": "No comparable measured Heo downstream rate or reliable active-hour forecast is available. It is the next paper to finish, but claiming a definite finish time would invent precision.",
        "comparison_only": {"other_three_papers_canonical_checkpoint_at": "2026-09-19T23:12:18.474217+00:00", "publication_at": publication["published_at"], "calendar_hours": duration_downstream,
            "caveat": "About 3.19 elapsed hours for three other papers after their canonical checkpoint, processed in parallel. Heo has no completed canonical package and substantially different crystallographic work; this is not its ETA."}
    },
    "frozen_backlog_estimate": {
        "credible_point_estimate": None, "confidence_interval": None,
        "preferred_wording": "No dependable completion date yet. For scale only, sustaining 15–20 completed review scopes per calendar day would put the frozen 9470-scope worklist at roughly 16–21 months; 13/day is roughly 24 months.",
        "conditional_scenarios": scenarios,
        "assumptions": ["All 9470 provisional scopes require a completed disposition to the authorized quality standard.", "Average scope-completion rate includes audited skips and full retained-paper review/publication.", "Average calendar-day rate persists through weekends, interruptions and runtime limits; no additional downtime adjustment.", "No later arrivals, new source revisions or reopened missing-SI work in this frozen-snapshot duration.", "These are arithmetic sensitivity scenarios, not guaranteed speed, statistical confidence intervals or a promised completion date."],
        "old_eta": workflow["eta"],
        "old_eta_interpretation": "The prior 4–7-month range was explicitly an assumed twofold speedup, not measured. At the current frozen scope count it requires about 44–78 scope completions/calendar day; this has not been demonstrated.",
        "required_daily_for_old_4_to_7_months": [9470/(7*30.4375), 9470/(4*30.4375)]
    },
    "incoming_work": {
        "user_reported_document_copies_per_day": 1000, "verified_new_unique_papers_per_day": None, "verified_new_recipe_papers_per_day": None,
        "observed_short_scan_interval": {"start": earlier_scan["last_scan_at"], "end": scan["last_scan_at"], "hours": arrival_hours, "added_document_copies": arrival_copies, "added_provisional_group_labels": scan["groups"]-earlier_scan["groups"], "note": "Observed queue growth between stored scans; not a steady daily estimate or verified unique-paper count."},
        "catch_up_date": None, "balance_condition": "A growing queue can shrink only when sustained completed-scope output exceeds independently established new canonical review-scope inflow, accounting for aliases, paired SI and audited exclusions.",
        "interpretation": "1000 new documents/day cannot be equated with 1000 papers/day. At that copy volume, current demonstrated output provides no evidence that the growing collection can be caught up with."
    },
    "checkpoint_inconsistencies_not_mutated": [
        "workflow-state retains older nested source_review_summary and next_action text despite newer top-level Heo checkpoint; latest dated paper/milestone checkpoints take precedence.",
        "The dedicated corpus screen computed hashes in a separate immutable snapshot/cache; monitor ledger hash-cache counts are incomplete and have a different basis. Do not use their apparent difference as new/duplicate paper counts."
    ],
    "recommended_recalibration": "Measure the next 20–30 fully closed, evidence-prioritized scopes across several batches, recording reading/canonical/visual/audit/deployment timestamps, available-source scope, page/table complexity and actual skips. Report a rolling median and range with active-vs-calendar time; keep no-recipe screening separate from publication throughput.",
    "mutations": "Only this private script and eta-evidence-20260920.json/.md; no ledger, queue, memory, source, Site, publication or scheduling changes.",
    "bound_files": list(bound.values())
}
out = B / "eta-evidence-20260920.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
rows = "\n".join(f"| {x['closed_provisional_scopes_per_calendar_day']} | {x['days']} | {x['months_at_30_4375_days']} | {x['illustrative_finish_date_UTC']} |" for x in scenarios)
md = f"""Dated ETA evidence — 20 September 2026 UTC

The 02:40 UTC folder scan contains **13,786 document copies**, **9,492 provisional review scopes**, and **9,470 pending scopes** (9,469 waiting; Heo active). The unique-paper total and total recipe count are **unverified**. Counts cover both incoming and legacy folders; files, papers and recipe records are different units.

The 03:08 UTC checkpoints record **21 audited and published available-source contributions** plus **one audited no-recipe exclusion**. Fifteen of the 21 have supplied-main-only scope with SI unverified; six include matched SI. This ETA check verified milestone/publication records and bound their audit files; it did not freshly re-audit the science. The older 10-source website baseline has heterogeneous coverage and is excluded from the throughput numerator.

**Current batch: four of five published.** Gu, Nagasaki, Ribeiro and Norberg are live; Heo's 9 main pages and 14-page scanned SI are reviewed, including independently reconciled 1,209 reflection rows with two explicit unresolved signs. Heo's canonical records, reader, visuals, integration and final publication remain. The root work-owner's provisional plan is **3–6 additional active-work hours, low confidence**; this is a planning judgement, not a measured throughput estimate or calendar deadline. Interruptions or audit findings can extend it. For context only, the other three papers took {duration_downstream:.2f} calendar hours from their shared canonical checkpoint to publication, in parallel; that is not a Heo estimate.

Observed output is **21 completed source scopes in {window_hours:.2f} calendar hours** ({21/window_hours*24:.2f}/24 h). The current batch produced **four publications in {batch_hours_to_pub:.2f} hours** ({4/batch_hours_to_pub*24:.2f}/24 h), with the fifth still unfinished; by the later status snapshot its rate is {4/batch_hours_to_snapshot*24:.2f}/24 h. These short, biased, partly unfinished windows do not measure active hours or steady-state capacity.

For scale only, the following arithmetic assumes a sustained average rate of fully closed review scopes, including audited skips, for the frozen 9,470-scope backlog:

| Closed scopes/calendar day | Days | Approx. months | Illustrative date (UTC) |
|---:|---:|---:|---|
{rows}

**15–20/day implies roughly 16–21 months**, rather than a firm finish date. The previous 4–7-month planning range assumed a speedup that was not measured; it would now require about 44–78 closed scopes/day. Audited exclusions and simpler papers could shorten the backlog; complex tables, missing SI, corrections, runtime limits and downtime could lengthen it. Dates above exclude future arrivals and reopened scopes and assume sustained calendar-day output; they are not confidence intervals or promises.

The corpus screen ranked **9,187 scopes**, of which 5,168 (56.25%) have recipe/structure text signals, 3,971 (43.22%) are low-signal candidates, and 48 (0.52%) need manual format/text work. **Low signal does not mean no recipe.** There are 305 newer unranked scopes. The selected 22 closed dispositions (21 publications/one skip) cannot estimate corpus retention. There is currently no verified retained/excluded proportion for the whole corpus.

The user's **~1,000 documents/day** inflow is separate from this frozen backlog; unique-paper/recipe inflow is unknown. Stored scans show {arrival_copies} additional copies over {arrival_hours:.2f} hours, which also does not establish unique-paper/day throughput. No catch-up date for the growing collection is supported.

Recalibrate after another 20–30 fully closed, evidence-prioritized scopes, keeping screening, matched-source scope, audit, reader/visual work and deployment timestamps separate. Existing publication checkpoint: {publication['public_url']} (dataset {publication['dataset_version']}, {publication['published_at']}); no publication was performed by this ETA task.

Exact evidence snapshots and {len(bound)} bound input hashes are in the companion JSON. Only private ETA artifacts were written.
"""
(B / "eta-evidence-20260920.md").write_text(md, encoding="utf-8")
print(json.dumps({"status": "saved", "json": str(out), "json_sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "markdown_sha256": hashlib.sha256((B/'eta-evidence-20260920.md').read_bytes()).hexdigest(), "bound_inputs": len(bound)}, indent=2))
