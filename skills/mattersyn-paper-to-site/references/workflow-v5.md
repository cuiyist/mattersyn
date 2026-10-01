# MatterSyn workflow v5: simplified paper-to-website pipeline

**Adopted 2026-09-30 at the owner's request.** This is the only active workflow. It replaces
`processing-workflow-v4.md`, `throughput-workflow-v3.md`, `throughput-workflow.md` and
`scaling-workflow-v2.md`. Those files are history. Where any other reference disagrees with
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

### 2. Claim
- Keep every extractor busy: each holds **one active paper plus one claimed next paper**.
- Claim = one line in the private event ledger (`stage: claimed`, `package_id`, UTC `at`).

### 3. Extract: one paper = one package (minimum publishable unit)
- **Scope:** main-text recipes and **all** variants inside that scope, their product samples
  and structure results, page/figure locators, and the source figures and visuals for those
  samples. SI is read only when the main text points to it for an essential recipe value.
  Otherwise SI is a later follow-up.
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
The auditor works from the package and the private validation receipts, not by rereading the
whole paper. Check:
- every value the quote check could not confirm
- every recipe→sample and sample→structure assignment, and every figure→sample assignment
- units, temperatures, times and atmosphere on reaction steps
- conflicts shown side by side; missing values marked as missing, not guessed

Fill the eight-item checklist in the package `audit` block. Ledger: `audit_accepted` or `changes_requested`.

### 5. Deep audit (when `deep_audit_required: true`, about 10%)
A full independent read of the scoped pages and figures, as in the old gold audit. Record any
error found in the deep-audit log. **If deep audits find errors in more than 1 in 10 sampled
papers over a rolling 50, stop and tell the owner.** The quick audit is then missing too much.

### 6. Integrate (one integrator; batches as papers arrive)
- Merge accepted packages with `tools/package-importer/merger.py`, then `preflight.py`.
- One source commit per batch with generated controls (`tools/publication/SINGLE_COMMIT_RELEASE.md`):
  `prepare_source_release.py --apply`, `git commit`, `check_project_manifest.py --pre-push`, push to `main`.
- Never commit derived aggregates by hand. Never make a separate manifest-closure commit.
- Never wait for a blocked paper. Publish what is ready.

### 7. Release (one command)
```
python tools/publication/release_batch.py --source <clean source checkout at pushed main> \
  --site <clean mattersyn-site checkout> --work <new folder outside both> \
  --release-id <batch id> --reviewer "<quick-audit reviewer(s)>" --push --verify --ledger <private ledger.jsonl>
```
It checks that source CI passed for that commit. It then builds the candidate, generates the
site allowlist, runs the final gated build (which must equal the candidate), stages the site,
runs the site's own gate, commits and pushes. Finally it waits for the live site, checks it
anonymously, and appends one `live_verified` event per new paper. **Run it whenever papers are
waiting and the previous release has finished.** About 5 minutes plus Pages deployment. Run it
without `--push` first if anything about the batch is unusual. It never publishes on a dry run.

### 8. Measure
```
python -B tools/workflow/package_workflow.py metrics <private ledger.jsonl> --start <UTC> --end <UTC> --output <new receipt>
```
Report the measured published papers/hour and stage times only when the owner asks.

## Staffing (continuous)

| Role | Count | Notes |
|---|---|---|
| Extractor | as many as available (start with 3) | One active paper + one claimed next |
| Quick auditor | 1 per ~4 extractors | Also performs the sampled deep audits |
| Integrator / releaser | 1 | Integrates, runs `release_batch.py`; extracts when idle |

Throughput scales with extractors. Add extractors before changing any quality rule.

## Retired (do not follow, even if an older file says so)

- The public preliminary lane and any experimental-silver display before calibration.
- Two-hour, morning or interval progress reports; progress-only site releases.
- Heartbeat or 20-minute continuation runs; pauses between batches.
- Per-paper releases; separate manifest-closure, "approve baseline" or "bind digest" commits.
- The 400-papers-by-September-29 deadline and the "500 papers/day" quota language.
- "Careful complete main/SI reading over speed" as a default. The minimum publishable unit replaces it.
- The limits of four agents / five claims.
