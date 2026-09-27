# Silver monitoring workflow

`monitor.py` adds deterministic daily source sampling and cumulative, field-specific
monitoring to the local silver workflow. It uses the Python standard library. It
does not read source papers, run models, call a network, alter scientific records,
deploy, grant calibration approval, or populate an accuracy page with forecasts.
Tests use synthetic fixtures and are not scientific accuracy results.

## What the sampling population means

This first version monitors the **first anonymously verified silver release of
each canonical primary source**, using its immutable published claim manifest.
It does not audit a draft/candidate population. Main text, SI, repeated versions,
corrections and promotions do not create more source contributions. Sources with
a verified silver release before this window are excluded from its new-source
cohort. Gold events and claims never enter silver metrics or gold evaluation.

Each closed UTC day forms a cohort. The sample contains `ceil(source_count / 20)`
sources, ranked by HMAC-SHA256 of the frozen seed, window ID, cohort date and source
ID. At 50 sources/day that means 3 audited sources, so the actual fraction is 6%.
At 500/day it is exactly 25 sources. An empty cohort has no sample. Every published
claim in each selected source manifest remains in the audit inventory, including
claims for which the reviewer returns unknown or supplies no judgment.

This is source sampling, not instance sampling. Every eligible source has the same
selection rule; within-source field instances need not be independent. Subsequent
SI additions or corrections to that source are **outside this first-release audit
scope** and need separately identified version audits. This tool must not be used
to claim that the entire deployed site's latest revisions have been audited.

## Freeze and preserve the window

Before the first monitored day, save a window declaration with:

```json
{
  "schema": "mattersyn-silver-monitor/1/window",
  "window_id": "pilot-window-01",
  "pipeline_id": "local-pipeline-1",
  "pipeline_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "baseline_calibration_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "seed": "1111111111111111111111111111111111111111111111111111111111111111",
  "registered_at": "2026-09-26T12:00:00Z",
  "start": "2026-09-27T00:00:00Z",
  "end_exclusive": "2026-10-04T00:00:00Z",
  "sampling_fraction": 0.05,
  "thresholds": {"high": 0.98, "medium": 0.95, "low": 0.90},
  "scope": "first_verified_silver_release_per_primary_source",
  "cells": [
    {"band": "high", "field": "reaction_temperature"},
    {"band": "high", "field": "duration"}
  ]
}
```

The example fingerprints and seed are synthetic. Use a fresh 256-bit random seed
and bind the declaration's digest to an independently preserved, timestamped
receipt before the population or errors are visible. Declare every admitted
field/band cell. Changing the seed, window duration, pipeline, thresholds or cells
is a new window requiring explicit review; it is not a retry of a failed window.
The referenced baseline must already have passed the independent calibration
approval process. Merely writing its digest does not establish approval.

The CLI writes with exclusive creation and refuses to overwrite receipts. Save
every plan/report. Every subsequent `plan` and `evaluate` call in the same window
must pass its immediate predecessor via `--previous`; the CLI has no hidden
mutable state. Past cohorts, selected sources, ledger events and prior audit
events cannot be dropped, altered, backfilled or rolled back. A late deployment
event for a closed cohort requires the release owner to reconcile the history;
the tool stops instead of silently resampling.

Software cannot prove that a self-reported registration timestamp, complete
history flag, source identity, deployment receipt or reviewer identity is true.
The integration owner must verify and preserve those external receipts. Determinism
prevents casual rerolling within the preserved chain; it does not cryptographically
prove a dishonest operator did not create another chain.

The private sample plan retains the complete supplied ledger and each eligible
source's exact deployed/verified events. Evaluation deterministically reconstructs
the entire population, selection and claim inventory, then rechecks the full
published manifest digest and claim projection before counting any audit. Removing
a difficult claim or an entire source cannot change the denominator while the
frozen input ledger is retained.

## Deployment ledger contract

Use an object with `schema: "mattersyn-silver-monitor/1/deployment-ledger"`,
`complete_lifetime_history: true`, `complete_through` and an `events` list. The
history must extend back before the window so earlier sources are not recounted.
Events use the workflow's `deployed` and `live_verified` stages, with:

- `event_id`, timezone-qualified `at`, `package_id`, `primary_source_id` and
  `source_identity_verified: true`.
- `tier: "silver"`, the exact `pipeline_id` and `pipeline_sha256`, a 40/64-character
  commit hash, and `manifest_sha256`.
- A `deployed` event followed by a `live_verified` event with the same package,
  primary source, commit, manifest and pipeline. Verification must contain
  `anonymous: true`, `passed: true` and a 64-character `receipt_sha256`.
- The `live_verified` event must carry `published_claims`. Its exact JSON digest
  must equal `manifest_sha256` using this module's canonical `digest` function.

Each manifest entry contains `claim_id`, `claim_sha256`, `band`, `field`,
`tier: "silver"` and `state: "accepted_auto_checked"`. `claim_sha256` identifies
the scientific value, units, context and source locators actually deployed; claim
IDs must be stable opaque public IDs, not quotes or paths. IDs here are deliberately
restricted to ASCII letters/numbers plus `_.:-`. Use canonical source IDs from
the verified identity registry, not invented aliases for the same paper.

Existing event metrics do not yet produce the claim manifest fields themselves.
The publication bridge must record them from the exact release payload and retain
the genuine anonymous verification receipt before production use. No sample or
throughput is claimed from the current candidate inventory. Other silver pipeline
versions establish historical source identity but do not enter this pipeline's
monitoring metrics. Gold and noneligible stage events are excluded.

## Audit event contract

An independent scientific reviewer supplies an immutable event per sampled claim:

```json
{
  "schema": "mattersyn-silver-monitor/1/audit-event",
  "event_id": "audit-source-claim-001",
  "at": "2026-09-28T12:00:00Z",
  "window_sha256": "exact digest of the frozen window",
  "tier": "silver",
  "source_id": "canonical-source-id",
  "manifest_sha256": "exact deployed manifest digest",
  "claim_id": "stable-claim-id",
  "claim_sha256": "exact published scientific claim digest",
  "judgment": "correct",
  "independent_scientific_audit": true,
  "auditor_id": "reviewer-id",
  "extractor_ids": ["extractor-id"],
  "truth_receipt_sha256": "digest of the independently reviewed private truth"
}
```

Judgments are `correct`, `incorrect` or `unknown`. Reviewers must assess source
support, units, context and source/sample linkage, not just model agreement. A
missing event remains missing truth. Neither missing nor unknown truth becomes a
success or dilutes the error denominator. Unknown is an immutable unresolved
judgment; resolving or correcting an existing judgment needs a separate reviewed
correction process outside this tool. Conflicting labels stop instead of choosing
the more favorable one. Repeated identical events are idempotent; extra receipt
IDs for the same claim do not increase the audited instance or source counts.

Audits bind the exact sampled manifest, claim and window. Nonselected sources,
gold claims, changed versions, nonindependent reviewers and audits dated before
verified deployment fail closed. Extra private evidence text may be present in a
local audit event, but the report retains only its hash and numeric judgments.
Keep source quotes and full truth artifacts outside Git.

## Stop rules and uncertainty

The monitoring error threshold is 2%, 5% or 10% for the high, medium or low band,
respectively. The rule is predeclared: evaluate each immutable reviewed event in
timestamp/ID order, cumulatively within its field/band. The first observed error
rate **above** the threshold latches suspension for that cell for this window.
Equality is not exceedance. Later correct cases cannot erase a stop; previous
reports also carry suspensions forward. This conservative operational rule is
not a sequential statistical confidence claim.

During the window, a small clean sample has `MONITORING_ONLY` status. Missing or
unknown truth has `MONITORING_INCOMPLETE` status. Neither status authorizes new
field admission or proves the initial calibration precision. At the predeclared
window end, any missing/unknown truth, no reviewed instances, or a nominal
one-sided 95% exact binomial lower precision bound below the band's threshold
suspends the affected cell. A numerical pass still requires independent review.
An interim sample is not required to re-prove 98% precision every day.

Reports disclose sampled/reviewed/error/unknown/missing counts and distinct source
counts per cell. They also show an all-correct source-cluster sensitivity bound.
The field-instance bound assumes IID instances and can overstate certainty for
correlated paper variants. The source-cluster bound is a sensitivity summary;
neither is a simultaneous guarantee across fields, repeated-look confidence
sequence, per-value probability or blanket claim of site accuracy. The tool does
not estimate recall from a published-claim-only inventory.

`through` closes the **deployment population** cohort, not the audit clock; final
source audits can finish after that cohort cutoff. Their immutable timestamps
are preserved in hashed input receipts. A final report with incomplete truth
stops the field instead of treating overdue review as a success.

## Commands and candidate controls

```powershell
python -B -m unittest -v test_monitor.py
python -B monitor.py plan --window window.json --ledger deployment-ledger.json --through 2026-09-28T00:00:00Z --out plan-day-1.json
python -B monitor.py evaluate --plan plan-day-1.json --audits audit-events.json --out report-day-1.json
python -B monitor.py plan --window window.json --ledger deployment-ledger.json --through 2026-09-29T00:00:00Z --previous plan-day-1.json --out plan-day-2.json
python -B monitor.py evaluate --plan plan-day-2.json --audits audit-events.json --previous report-day-1.json --out report-day-2.json
python -B monitor.py project --report report-day-2.json --plan plan-day-2.json --audits audit-events.json --previous report-day-1.json --out control-candidate.json
```

All paths are local private artifacts. Evaluation returns exit code 2 on field
suspension; invalid inputs/output conflicts also return 2. Error receipts avoid
echoing source text or local paths. `project` uses a strict public allowlist and
produces only a **candidate** control document. It requires the same plan, audit
events and prior report used for evaluation; it recomputes all report metrics and
decisions and rejects altered counts, bounds, masks or suspension flags. It contains numeric metrics,
pipeline/calibration bindings and field/band decisions; no scientific values,
source quotes, local paths, auditor IDs or source-level truth details.

For a suspended field/band it proposes `suspend_field_band`,
`propose_versioned_revocation`, `training_masked: true` and `training_weight: 0.0`.
Apply those controls to every applicable silver contribution in the bound
pipeline/field/band, not only sampled sources. Published values are never silently
edited. The release owner must review, version and publish an explicit change
through existing science/privacy/release gates. Unsuspended controls say to retain
existing admission gates; `null` weights/masks do not authorize unmasking.
Every candidate has `publication_enabled: false`, `scientific_values_modified:
false`, `new_admissions_authorized: false` and `gold_evaluation_eligible: false`.

No real production window, audit result, public accuracy metric or publication
was created by this implementation.
