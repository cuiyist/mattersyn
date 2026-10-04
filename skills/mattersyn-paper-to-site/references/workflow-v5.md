# MatterSyn workflow v5: full independent audit plan

The owner's 2026-10-02 full-audit restart supersedes the earlier quick-audit workflow and quality hold. The quick audit is retired. Its failed blind-test results and original checklist remain historical evidence; do not revise them or treat them as acceptance under this plan.

## Evidence for the restart

The original-version retrospective found S1/S2 errors in 6/8 v5 papers, 1/5 flagged older papers and 1/5 random older papers: 8/18 papers, with 10 S1 and 2 S2 findings. The second blind quick test detected 2/12 findings (16.7%), below 80%. These selected cohorts are not a corpus-wide error-rate estimate. Only 1/5 random older papers was positive, so the owner's conditional background re-audit trigger (at least 3/5) was not met; do not start a corpus re-audit without approval.

## Paper lifecycle

1. Prioritize existing screened-pass QD papers, then metal papers. Reconcile primary-source identity and existing live coverage before reserving one exclusive claim. Preserve existing extractions and receipts; do not call reassessment new extraction.
2. One extractor authors and freezes the contribution. Declare the scoped source pages and exclusions, retain all in-scope variants and sample assignments, and keep unavailable values explicitly missing. Related available SI preparation sections and captions must be checked where needed to assess essential details or omissions. An optional missing morphology or reference unit cell alone is not a skip.
3. Run `tools/workflow/check_records.py` on the exact frozen package **before every full or sampled deep audit starts**. Record command result, timestamp, package/record hashes and flag receipt. Flags are questions for the auditor, not automatic scientific verdicts. They may remain open at audit start; acceptance requires a source-backed disposition for each flag (style-only flags may be explicitly retained with a reason).
4. A different agent conducts a **full independent audit of every paper**, reading the scoped source pages and inspecting relevant figures and tables. Write a source-first inventory before comparing the package, then check both source-to-record completeness and record-to-source accuracy. Verify every quantity and condition, including quote-validated values; variants, workup, input identities and stock compositions, lineage, sample/figure assignments, missingness, conflicts and asset interpretation. Record the actual pages inspected and exact accepted scientific hashes. A checker, quote matcher, model agreement or old quick receipt cannot replace this audit.
5. The preregistered sample gets a **third distinct agent's deep audit**, after full-audit acceptance. Run the checker again first. Preserve original findings and first-pass outcomes through all corrections. Changed science is rechecked by a distinct auditor; untouched accepted claims can reuse exact receipts.
6. Root alone integrates accepted packages into ordinary material pages and publishes ready batches. Keep source figures with their exact provenance and factual permission status, reusable chemical/phase viewers and stage-specific apparatus. Do not publish drafts, preliminary lanes or misleading reviewed/training-ready labels.
7. Count a paper once only after its contribution is deployed and anonymously verified. Multiple records or correction releases add no extra source-paper credit.

## Sampling and stop rule

Use the append-only `full_audit_plan.py` cohort ledger. Freeze the cohort seed and baseline before assigning sample ordinals. The first 40 auditable new contributions receive exactly ten preselected slots, one per block of four; corrections do not redraw a slot. Skips, technical holds and previously published sources are separate outcomes and cannot pad this denominator. Reused unpublished extraction is identified as carried-in work.

The third-agent sampling rate is 25% for these first 40. Reduce to 10% only after all 40 and all ten required deep audits are complete, with at most one distinct S1/S2-positive sampled paper. Otherwise retain 25% and report the result; do not silently relax sampling.

Stop extraction and report if **more than five of the last 50 distinct sampled papers have an S1/S2 finding**. Multiple findings or corrective re-audits of one paper count once, and a subsequent fix never erases the positive result. The owner's explicit restart begins the full-independent-audit regime; retain prior quick-regime logs separately and never reset this new regime to evade a stop. Corrections already in progress may finish during a stop.

## Staffing and scaling

The owner approved two additional extraction/audit tasks on October 3 Chicago time. Follow [the multi-session arrangement](multi-session-full-audit.md): each worker task may run two extractor-auditor pairs within its actual four-agent session allowance; the existing task alone integrates and publishes. Its remaining workers handle existing corrections, sampled deep audits and the separately authorized retrospective queue. Each paper has distinct extractor and full-auditor identities; a sampled deep auditor differs from both. A created task or prepared role is not proof of an active worker. Measure actual agent and command availability; never bypass a runtime cap.

Requested pair steps are 4, 8, 12 and 16. Advance only when the previous step has at least ten deep audits, no more than one S1/S2-positive paper per ten deep audits, no claim collisions, at most two batches in the integrator backlog, and measured spare machine AND agent capacity. Report remaining QD and metal queue sizes at every step, distinguishing provisional filename groups from verified eligible primary papers. Missing capacity or evidence blocks a ramp; it does not waive a scientific requirement.

## Release and records

Release when at least six papers are ready or three hours have elapsed since the first ready paper, whichever happens first. Do not wait for blocked papers. Use one source preparation commit per ready batch, shared components and the existing exact-source CI, build, browser, privacy and anonymous release gates. Reuse unchanged passing checks; repeat only for changed inputs, failures or unresolved concerns. Do not make separate binding commits, per-release prose notes or status-only site releases. The private ledger is release history; at most one short daily workflow memory line is needed.

Never edit policies or allowlists to pass a gate. Generated control files must be produced through the normal preparation tools; scientific assets still require their actual provenance and review. Original PDFs/SI, extracted text, page renders, raw quotes, drafts and detailed audits stay local. Only release-cleared data, assets, code, skills, concise memory and references go to the public repositories. Existing local sources only; no paid APIs, cloud document processing, source transfer or new paper/model downloads.

After the first 40, report actual distinct live-verified papers per elapsed hour, carried-in work separately, all ten deep-audit outcomes, distinct S1/S2-positive papers and finding types, stage counts, skips/holds, rework, queue sizes and any backlog/capacity limit. Twenty papers per hour remains a target until measured. Scheduled morning, two-hour and twenty-minute reports remain disabled; report when asked, at the requested first-40 checkpoint, or for a stop/material failure.

Operational commands and receipt requirements are in [agent-runbook.md](agent-runbook.md).
