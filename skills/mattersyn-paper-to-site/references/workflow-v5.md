# MatterSyn workflow v5: simplified paper-to-website pipeline

**Adopted 2026-09-30; quality-hold revision authorized 2026-10-02.** This is the only active workflow. It replaces
`processing-workflow-v4.md`, `throughput-workflow-v3.md`, `throughput-workflow.md` and
`scaling-workflow-v2.md`. Those files are history. **For the exact commands, roles and failure handling, follow
[agent-runbook.md](agent-runbook.md).** Where any other reference disagrees with
this file about scope, pace, staffing, audits or publication cadence, this file wins. Quality
rules are in [standards.md](standards.md) and still apply in full.

## Owner decisions this workflow implements (2026-09-30)

1. **Audit:** quick audit of every paper + full deep audit of a 10% sample.
2. **Counter:** machine-extracted (silver) papers count toward the public paper counter, clearly
   labelled. The silver lane stays **off** until held-out calibration meets the 98% / 95% / 90% field bands.
3. **Figures and visuals ship with the paper.** No "presentation later". Reuse existing molecule
   cards, unit cells and apparatus scenes wherever the chemistry matches.
4. **Scope: quantum-dot / colloidal-nanocrystal papers only.**
5. **Agents run continuously.** No heartbeat bursts and no idle waiting.

**Target:** about 20 newly published papers/hour on the public counter. It is a target, not a
measured result. Report the measured rate from the metrics ledger only.

**Current hold:** no new extraction or source claims. Finish controlled corrections and audits of
already frozen work. The first blind test found 4 of 10 known S1/S2 issues (one further issue was
mentioned only as a scope limit), so it did not meet the 80% threshold. Strengthen and rerun the
blind completeness audit with a different reviewer. The hold ends only after a blind re-audit of
the original nine sampled packages finds at least 80% of their S1/S2 issues **and** the owner
confirms resumption. The owner separately asked to pause after the current papers; a passing test
alone does not override that request.

## The pipeline

```
queue ──► claim ──► extract (one package) ──► checks ──► quick audit ──► [deep audit if sampled] ──► integrate ──► release batch
```

### 1. Queue (once per day, or when it runs low)
```
python -B tools/workflow/package_workflow.py rank <screened_pass.jsonl> --scope quantum-dot \
  --identities <private-identities.json> --live-sources <private-live-sources.json> --output <private-queue.json>
```
- Out-of-scope units are excluded automatically: bulk, thin films, ceramics, CVD, glasses.
- Units with `scope_check_required: true` come last. Take 10 seconds to decide in or out
  from the screen summary before claiming. Never open a paper only to decide its scope.
- Work top-down. The queue already prefers recipe + structure evidence in main text.
- Within the in-scope queue, identified semiconductor quantum-dot papers precede elemental
  Ag/Au/Bi/Pt/Pd/Cu and other metal nanocrystals. Keep the existing evidence order within each
  class; uncertain material labels stay visible and do not get promoted automatically.

### 2. Claim
- Keep every extractor busy: each holds **one active paper plus one claimed next paper**.
- Claim by creating a claim file, then `package_workflow.py log-event <ledger> --stage claimed --package-id <id>`
  (see the runbook). Every stage below is logged the same way.

### 3. Extract: one paper = one package (minimum publishable unit)
- **Scope:** main-text recipes and **all** variants inside that scope, their product samples
  and structure results, page/figure locators, and the source figures and visuals for those
  samples. SI is read for essential recipe values. An explicitly deferred SI remains a later
  follow-up, but source-side audit must still check available related SI preparation and figure
  captions for omitted required inputs, variants and conflicts before a package can claim complete
  coverage of its selected recipe series.
- Package format: `tools/workflow/package.schema.json` (`package_id`, documents, records,
  locators, assets, reagent bindings, scope, audit, presentation).
- **Figures and visuals together:** crop the source figures that support each sample (with
  provenance and rights status as now). Bind molecules and unit cells from the existing
  registries. A **new** chemical or phase not in the registries means: add it in the same package.
- **Time box:** if a paper needs more than ~45 minutes of extraction, or an essential value is
  only in an unavailable document, record `blocked` with the reason and take the next paper.
- **Skip:** no usable preparation, or no recipe-to-structure link → record a source-supported
  skip (counts as processed, never as published).
- Freeze the package, then run:
```
python -B tools/workflow/package_workflow.py validate <pkg>/package.json --checkout <source> --output <private-receipt.json>
python research-assets/incoming-paper-monitor/validate_quote_spans.py ...   # local quote-on-page check (private)
python -B tools/workflow/package_workflow.py audit-sample <pkg>/package.json --output <private-sample.json>
```
Ledger: `extraction_frozen`.

### 4. Quick audit (every paper; reviewer ≠ author)
Before seeing the package, the auditor reads the available main and SI preparation, linked Results,
and relevant figure/table captions, then seals an independent inventory of setup, inputs, steps,
variants, purification, samples and panels. Inspect related branches even if the package proposes
to exclude them, and distinguish a partial contribution from a complete recipe series. Compare
this source-first inventory with the frozen package and private validation receipts in both
directions, including exact sample lineage and rendered molecular-card identity. Run the advisory
`tools/workflow/check_records.py --package <frozen-package.json> --out <private-flags.json>`;
resolve every non-style flag against the source in private audit notes. A flag is a question,
never an automatic verdict. Check:
- every value the quote check could not confirm
- every recipe→sample and sample→structure assignment, and every figure→sample assignment
- units, temperatures, times and atmosphere on reaction steps
- conflicts shown side by side; missing values marked as missing, not guessed

Fill the eight-item checklist in the package `audit` block. Ledger: `audit_accepted` or `changes_requested`.

### 5. Deep audit (when `deep_audit_required: true`)
A full independent read of the scoped pages and figures, as in the old gold audit. Record any
finding with severity: S1 is a wrong or missing recipe-changing value, essential input/variant,
sample/structure link or measured claim; S2 is a set-point/event, chemical identity/role,
source-figure illustration or silently resolved conflict; S3 is wording, locator precision,
unit spelling or styling. **Stop new extraction when more than five of the last 50 distinct
sampled papers have any S1/S2 finding.** Preserve all S3 findings for correction; they do not
trigger the stop rule. After an owner-confirmed resume, deep-audit 25% of the next 40 papers.
Return to 10% only if at most one of approximately ten sampled papers has an S1/S2 finding;
otherwise stop again. Do not reset or reclassify the current hold away.

### 6. Integrate (one integrator; batches as papers arrive)
- Merge accepted packages with `tools/package-importer/merger.py`, then `preflight.py`.
- After adding records, let `prepare_source_release.py` derive the baseline and
  blueprint `record_count` from the staged canonical records in the same
  source-preparation step. It rejects a hand-edited baseline and changes to
  prior record digests or task eligibility without exact review. The independent
  build and pre-push manifest check verify the generated count and membership.
- One source commit per batch with generated controls (`tools/publication/SINGLE_COMMIT_RELEASE.md`):
  `make_review_receipt.py`, `prepare_source_release.py --apply`, `git commit`, `check_project_manifest.py --pre-push`, push to `main`.
- Never commit derived aggregates by hand. Never make a separate manifest-closure commit.
- Never wait for a blocked paper. Publish what is ready.

### 7. Release (prepared candidate, browser review, publish)
```
python tools/publication/release_batch.py --source <clean source checkout at pushed main> \
  --site <clean mattersyn-site checkout> --work <new folder outside both> \
  --release-id <batch id> --reviewer "<quick-audit reviewer(s)>" --wait-ci 20
```
It checks source CI, builds the candidate, generates the site allowlist, runs the final gated
build (which must equal the candidate), and stages a separate site worktree through the site's
boundary gate. The live site checkout stays clean. Review that exact preview in a browser and
complete its `browser-review.template.json` as described in the [agent runbook](agent-runbook.md).
Only then rerun the helper with the **same** `--work`, adding `--review-receipt <completed review>
--push --verify --ledger <private ledger.jsonl>`. It checks the reviewed bytes again before
pushing. Finally it verifies every new paper route and backing review data, and every affected
material page and material shard anonymously, alongside sampled files. It appends at most one
`live_verified` event per new paper. A timed-out live check
reuses the same work path with `--verify` alone. **Run this sequence when at least six accepted
papers are ready or three hours have passed, whichever comes first, and the previous release has
finished.** A blocked paper never delays an accepted batch. About 5 minutes plus Pages deployment.

### 8. Measure
```
python -B tools/workflow/package_workflow.py metrics <private ledger.jsonl> --start <UTC> --end <UTC> --output <new receipt>
```
Report the measured published papers/hour and stage times only when the owner asks.

## Staffing (continuous)

| Role | Count | Notes |
|---|---|---|
| Extractor | as many as available (start with 3) | One active paper + one claimed next |
| Quick auditor | 1 per 2 extractors during 25% deep audits; 1 per 3 after 10% resumes | Blind completeness pass; deep auditor differs from quick auditor |
| Integrator / releaser | 1 | Integrates, runs `release_batch.py`; extracts when idle |

After the hold lifts, ramp 4 → 8 → 12 → 16 extractors only when the last step has at most one
S1/S2 paper per ten deep audits, no claim collisions, at most two integration batches waiting,
and spare machine capacity. Report remaining semiconductor-QD and metal queue sizes at each step.
Never exceed available agent slots.

## Retired (do not follow, even if an older file says so)

- The public preliminary lane and any experimental-silver display before calibration.
- Two-hour, morning or interval progress reports; progress-only site releases.
- Heartbeat or 20-minute continuation runs; pauses between batches.
- Per-paper releases; separate manifest-closure, "approve baseline" or "bind digest" commits.
- The 400-papers-by-September-29 deadline and the "500 papers/day" quota language.
- "Careful complete main/SI reading over speed" as a default. The minimum publishable unit replaces it.
- The limits of four agents / five claims.
