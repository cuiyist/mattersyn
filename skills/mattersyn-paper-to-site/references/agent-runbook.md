# MatterSyn agent runbook (workflow v5)

Step-by-step operating instructions for the curation agent on the curation machine (the one with the
papers, text caches and local tools). **What** to do and **why** are in [workflow-v5.md](workflow-v5.md);
quality rules are in [standards.md](standards.md). This file says **how**, command by command. If this
file and workflow-v5 ever disagree, follow workflow-v5 and tell the owner.

Commands are written for PowerShell or bash; the Python is the same on Windows, macOS and Linux.

## 0. Placeholders used below

| Placeholder | Meaning |
|---|---|
| `<WS>` | The MatterSyn workspace root on the curation machine |
| `<SRC>` | `<WS>/repos/mattersyn`, the source checkout (clean, on `main`) |
| `<SITE>` | `<WS>/repos/mattersyn-site`, the site checkout (clean, on `main`) |
| `<P>` | `<WS>/research-assets/workflow-v5`, the **private** working area (never committed) |
| `<SCREEN>` | The private screened-pass manifest (`accepted-manifest.jsonl`) |
| `<TODAY>` | Today's date, `YYYYMMDD` |

Create the private folders once: `<P>/queue`, `<P>/claims`, `<P>/packages`, `<P>/ready-for-audit`,
`<P>/ready-for-integration`, `<P>/published`, `<P>/skipped`, `<P>/blocked`, `<P>/receipts`, `<P>/stages`.
The release transport ledger remains `<P>/ledger.jsonl`. The new full-audit cohort uses the separate private `full-audit-20261002/ledger.jsonl`, validated by `full_audit_plan.py`; preserve historical events in their original ledgers.

Everything under `<P>` stays local: papers, SI, extracted text, renders, quotes, drafts, audits and receipts.
Only reviewed data, code and documents go into `<SRC>`/`<SITE>`, through the commands below.

## 1. Start of every session

```
git -C <SRC> pull --ff-only
git -C <SITE> pull --ff-only
python -m pip install -r <SRC>/requirements-build-lock.txt      # once per environment
python -B -m unittest discover -s <SRC>/tools/workflow/tests      # 30-second self-test
```

- If `<SRC>` or `<SITE>` is not clean, stop and tell the owner. Never discard someone else's work.
- If the owner has said "pause", finish the current step, write the ledger event, and stop.
- **2026-10-02 owner restart:** full independent audits replace the retired quick audit. New QD
  claims may proceed under the first-40 sampling plan. Keep the failed blind results unchanged.
- Read [workflow-v5.md](workflow-v5.md) once per session. Do not read the historical workflow files.

## 2. Roles and how to run them continuously

| Role | Instances | Loop |
|---|---|---|
| Extractor | requested four pairs; actual runtime is four agents total | §4: author one frozen contribution at a time |
| Full auditor | one different agent per paper, after extraction | §5: read scoped sources and compare every claim |
| Sampled deep auditor | third distinct identity | §6: 25% of first 40; conditional 10% thereafter |
| Integrator / releaser | one | §7 and §8: merge accepted packages and release six-ready/three-hour batches |

Run root as integrator with three rotating workers under the current four-agent cap. Do not claim
nine simultaneous workers. Keep author, full auditor and sampled deep auditor identities distinct
for each paper. Scale requested pairs 4 → 8 → 12 → 16 only after the quality, collision, backlog,
queue reporting and machine/agent capacity gates in workflow-v5. Reuse frozen unpublished work
but identify it as carried-in extraction; an old quick receipt is not full-audit acceptance.

## 3. Queue (integrator, once a day or when fewer than 20 units remain)

```
python -B <SRC>/tools/workflow/package_workflow.py live-sources <SITE> --output <P>/queue/live-<TODAY>.json
python -B <SRC>/tools/workflow/package_workflow.py identity-map <SRC>/recipe-atlas/data/paper-reviews \
  --output <P>/queue/identities-<TODAY>.json --report <P>/queue/identity-report-<TODAY>.json
python -B <SRC>/tools/workflow/package_workflow.py rank <SCREEN> --scope quantum-dot \
  --identities <P>/queue/identities-<TODAY>.json --live-sources <P>/queue/live-<TODAY>.json \
  --output <P>/queue/queue-<TODAY>.json
```

- `ranked_units` are in work order. Units with `scope_check_required: true` come last.
- For a flagged unit, read only the screen summary and decide in 10 seconds whether it is a quantum-dot or
  colloidal-nanocrystal paper. If not, write a one-line reason to `<P>/skipped/<unit>.txt` and move on.
- The queue only says where evidence probably is. It never says a recipe is complete.

## 4. Extractor loop (one paper)

**4.1 Claim.** Take the next unit in today's queue that has no file in `<P>/claims`. Claim it by
*exclusively creating* `<P>/claims/<package_id>.json`. If the file already exists, another agent has it,
so take the next unit.
```
python -c "import sys,json;open(sys.argv[1],'x').write(json.dumps({'by':sys.argv[2]}))" <P>/claims/<package_id>.json <agent-id>
python -B <SRC>/tools/workflow/package_workflow.py log-event <P>/ledger.jsonl --stage claimed --package-id <package_id>
```
`package_id` = the primary source ID used on the site (first author + year + DOI slug, for example
`zhang2011-cm201400w-cu-zn-in-s`). Reuse the queue's `primary_source_id` when it has one.

**4.2 Decide (≤ 10 minutes).** Read the experimental section and the results that identify the products.
Choose one:
- **Eligible:** an operational preparation with meaningful quantities and conditions, and an explicit link
  to a reported structure (phase, size, morphology or structural measurement). Continue to 4.3.
- **Skip:** no usable preparation, or no recipe-to-structure link. Write the reason and page locators to
  `<P>/skipped/<package_id>.json`, log `--stage blocked --note "skip: <reason>"`, and delete your claim.
- **Hold:** unreadable file, missing document, identity unclear, or an unresolvable conflict. Write
  `<P>/blocked/<package_id>.json` and log `--stage blocked --note "hold: <reason>"`.

**4.3 Extract** into `<P>/packages/<package_id>/` (log `--stage extraction_started`):
- **Scope = minimum publishable unit:** every recipe and variant in the main text, their product samples,
  and the structure results. Read SI only where the main text sends you there for an essential recipe
  value. Record the SI as not reviewed otherwise.
- **Records:** canonical records exactly as in `<SRC>/recipe-atlas/data/record.schema.json`. Use the most
  recently published similar paper in `<SRC>/recipe-atlas/data/records/` as the template. Follow
  [recipe-and-evidence.md](recipe-and-evidence.md) and [standards.md](standards.md): every value has a
  locator; unreported stays unreported; conflicts are kept side by side; reported vs calculated vs
  inferred are separated; recipe → sample → structure links only with evidence.
- **Figures (ship with the paper):** crop the source figures that support each sample, as in the latest
  published paper. Keep the citation, page and figure locator, sample assignment, hashes, crop details and
  the factual (unverified) rights status. Never label an authored image as measured data.
- **Visuals (ship with the paper):** bind each chemical to the existing chemical registry and each phase to
  the existing crystal-reference registry. If a chemical or phase is new, add its registry entry in this
  package (see [visuals-and-models.md](visuals-and-models.md)). Reuse apparatus scenes; add one only when
  no existing scene fits the step.
- **Package manifest:** `package.json` per `<SRC>/tools/workflow/package.schema.json` (documents with
  reviewed pages and exclusions, records, locators, assets, reagent bindings, scope, `audit` with status
  `pending`, `presentation` state `complete`, `derived_files: []`). Add `merge-contract.json` per
  `<SRC>/tools/package-importer/MERGER.md` (create-only files plus additive keys and lists pinned to
  current base hashes).
- **Time box:** if extraction passes ~45 minutes, or an essential value is only in an unavailable
  document, stop. Move to `<P>/blocked/` with a reason and log `blocked`.

**4.4 Check and freeze.**
```
python -B <SRC>/tools/workflow/package_workflow.py validate <P>/packages/<id>/package.json --checkout <SRC> \
  --output <P>/receipts/<id>-validate-1.json
python <SRC>/research-assets/incoming-paper-monitor/validate_quote_spans.py \
  --source-text <private page-marked text of the document> --draft-json <private quote draft for this package> \
  > <P>/receipts/<id>-quotes-1.json
python -B <SRC>/tools/workflow/package_workflow.py log-event <P>/ledger.jsonl --stage extraction_frozen --package-id <id>
```
- Fix every validation error. A quote that does not match its page is either corrected, or listed in the
  package for the auditor to check visually.
- Receipts are create-only: use `-2`, `-3`, … for reruns.
- Freeze the scientific package, author identity and source scope in the new cohort ledger. The
  preregistered ordinal draw selects exactly ten of the first forty, without redrawing for revisions.
  Do not use the retired content-hash `audit-sample` command for this cohort. Run `check_records.py`
  and record its exact-package result before dispatching the auditor. Move only the frozen package
  to `<P>/ready-for-audit/`; unresolved checker flags are resolved during the full audit.

## 5. Full independent source audit (different auditor; every paper)

**Before the auditor begins**, the integrator or extractor runs the source-free checker and
records the package hash, command exit status, timestamp and exact flag receipt:
```
python -B <SRC>/tools/workflow/check_records.py --package <P>/ready-for-audit/<id>/package.json \
  --out <P>/receipts/<id>-consistency-flags.json
```
**Before opening the package claims or earlier scientific findings**, the different auditor reads
all scoped source pages, relevant available SI preparation sections, linked Results, figure/table
captions and visual panels. Write a timestamped source-first inventory of vessel preparation,
atmosphere, inputs (including unquantified ones), stock composition, steps, purification, deposition,
post-treatment, variants, product samples and cited panels. Log the exact pages actually read and
any unavailable pages. Inspect related branches before accepting an exclusion. Then open the frozen
package and receipts and verify all claims against the source. A quote match does not waive checking.

Record a source-backed disposition for every flag (style-only flags may be explicitly retained with a reason) in the private audit notes before
acceptance. A checker flag is a question, not an error verdict. Check, in this order:

| Checklist key (package `audit.checklist`) | What to check |
|---|---|
| `document_scope` | Scope and exclusions are stated honestly (e.g. "SI not reviewed"). Compare the source-first inventory with all available Methods, Results, figure and SI pages. If a related branch is deliberately deferred, keep the contribution explicitly partial and do not claim complete recipe-series coverage. |
| `recipe_and_variants` | Every recipe and variant inside the stated scope is present; none merged. Keep a typical or study-wide preparation separate from individually measured samples unless the source links them. Check deposition, purification and assembly branches and omitted, even unquantified, inputs. |
| `quantities_units_conditions` | Every value, including quote-confirmed values; every reaction step's temperature, time and atmosphere; units. Separate observed events (for example, solution clearing) from heater targets, and check all in-scope SI conditions and apparatus. |
| `chemical_identities` | Each reagent's identity and stock composition matches the source. Inspect rendered molecule-card role, caption and cited provenance when a shared registry entry is reused. |
| `sample_structure_links` | Every recipe→sample, sample→structure and figure→sample assignment has evidence. Explicitly mark a general-context or unknown edge rather than making it an exact experimental pair. |
| `conflicts_missingness` | Conflicts shown side by side; missing values marked missing, not guessed. Compare visible figure labels, body text and captions as separate source statements. |
| `evidence_locators` | Locators resolve to the exact pages and panels actually checked; note which pages and panels support each disputed edge. |
| `asset_provenance` | Figure crops, provenance, hashes and rights status are exact. Compare rendered particle and apparatus illustrations, captions and legends with the cited specimen; an asset key or hash alone is insufficient. |

- Each item is `passed`, or `not_applicable: <reason of at least 10 words>`.
- Before acceptance, compare a one-page claim/edge map covering route or variant → input
  batch → deposition/purification/assembly branch → product sample → structure or property →
  figure panel. Record the supporting locator for every edge and mark unresolved or
  study-wide relationships explicitly. This is a private
  audit aid, not an additional public scientific claim.
- Perform the comparison in both directions: every source-side item must be mapped to a record or
  a justified, visible coverage limit, and every package claim must map back to a specific source
  statement. Treat a typical preparation, study-wide ratio, group average and individually
  measured specimen as four different kinds of evidence; do not silently turn one into another.
- Inspect the rendered chemical cards and source figures as well as JSON. Verify the named
  reagent and role on each reused card, and compare figure-panel labels, body text and captions
  as separate statements. A byte-valid asset is not proof that its scientific identity is right.
- **Accept:** set `audit.status: accepted`, `reviewer_id` (your ID, different from `author_id`),
  `receipt_id`, and `scientific_sha256` from the validation receipt. Rerun `validate` (new receipt number).
  Log `--stage audit_accepted`.
- **Changes needed:** write the list into `<P>/ready-for-audit/<id>/changes-requested.md`, move the package
  back to `<P>/packages/`, and log `--stage changes_requested`. The original extractor fixes it and refreezes (4.4).
- Record full-audit acceptance first. If the fixed cohort ordinal requires a deep audit, a third agent does §6 before integration; do not self-award sampled acceptance.
- Then move the accepted package to `<P>/ready-for-integration/`.

## 6. Sampled deep audit (third agent; ten of first forty)

After full acceptance, rerun `check_records.py` on the exact package before dispatch. A third agent,
different from all scientific authors and the full auditor, independently reads every scoped page,
table and figure and checks the entire package. Use the preregistered ledger ordinals; no redrawing
for revisions, skips or holds. This is a check of the accepted full-audit output, not a second extractor.

Classify findings S1 (recipe-changing value, essential input/variant, false sample link or measured
claim), S2 (set-point/event, reagent role, contradictory illustration or silently resolved conflict),
or S3 (caption/locator precision, unit spelling or styling). Preserve every original finding and
first-pass positive outcome after correction. Full-audit findings caught before acceptance and
third-agent findings that escaped full acceptance have separate stage counts.

The first forty contributions require exactly ten third-agent samples. Reduce 25% to 10% only
when all ten are completed and at most one distinct sampled paper has S1/S2 findings. At first forty,
report the measured rate and ledger results. Stop extraction and report if more than five of the last
fifty distinct sampled papers in this full-audit regime are S1/S2-positive. Corrections may finish;
no reset or severity reclassification to evade a stop. Preserve historical quick-regime logs and
failed blind tests separately. The owner has explicitly authorized this stronger regime's restart.

## 7. Integrate a batch (integrator)

Take **all** packages in `<P>/ready-for-integration/`; never wait for blocked ones.
```
git -C <SRC> pull --ff-only
git -C <SRC> worktree add <P>/stages/<batch>/candidate origin/main        # isolated candidate
python -B -X utf8 <SRC>/tools/package-importer/merger.py --checkout <P>/stages/<batch>/candidate \
  --payload <P>/ready-for-integration/<id> --contract <P>/ready-for-integration/<id>/merge-contract.json \
  --importer <SRC>/tools/package-importer/importer.py --output <P>/stages/<batch>/<id>-overlay
#   copy each <id>-overlay/overlay/ tree into the candidate worktree (merger already pinned the base hashes)
python -B <SRC>/tools/package-importer/preflight.py --candidate <P>/stages/<batch>/candidate --base <SRC> \
  --new-records <P>/stages/<batch>/new-record-ids.json --report <P>/receipts/<batch>-preflight.json
```
- `new-record-ids.json` is a JSON array of every record ID in this batch's `package.json` `records` lists.
- A v5 contribution may review only the relevant main-text pages and figures. Do not
  turn those pages into a fictitious complete-paper Reader. For such a package,
  keep an `inventory-evidence.json` row with the exact reviewed page numbers,
  explicit exclusions and `selected_recipe_and_figure_review` status. Create a
  **private** scoped-acceptance manifest pinning the frozen accepted package,
  validation receipt and distinct independent-audit receipt by path and SHA-256;
  pass it to preflight with `--scoped-acceptance <private manifest>`. Verify the
  screened-pass source receipt and local document SHA separately. If the accepted
  package already contains the final `source_reviewed` canonical record, its
  bytes must match the candidate exactly. If a draft record is promoted after
  acceptance, add a pinned `status_delta_receipts` array containing an independent
  status-only audit of the exact old and new record hashes and changed fields.
  A previously `source_reviewed` record may correct stale audit-status prose only
  with a revision increment and an independent exact-hash status-delta receipt;
  never use that path to change a chemical, sample, figure or quantity claim.
  Legacy quick-only packages require a new full independent source audit under §5. Keep old
  receipts as historical evidence; do not normalize them into full-audit acceptance.
  Preflight rejects an unreviewed promotion, false full-page coverage, stale
  receipts or a source-title mismatch. Neither path waives figure, rights, full
  build, browser or live-verification checks.
- A **stale base** error means `main` moved since the contract was written. Regenerate that package's
  `merge-contract.json` against the new base. Science is unchanged, so no new audit is needed.
- Any other preflight failure: return that package with `changes_requested`, and continue the batch without it.

Commit once, with generated controls (no separate closure commit):
```
cd <P>/stages/<batch>/candidate
git add -A
python <SRC>/tools/publication/make_review_receipt.py --root . --reviewer "<auditor IDs for this batch>" \
  --out <P>/receipts/<batch>-review.json
python tools/publication/prepare_source_release.py --root . --reviews <P>/receipts/<batch>-review.json \
  --release-id <batch> --report-out <P>/receipts/<batch>-prepare.json --apply
git commit -m "Integrate <n> reviewed papers (<batch>)"
python tools/publication/check_project_manifest.py --pre-push
python recipe-atlas/scripts/make_runtime_snapshot.py --root . --blueprint publication/build-inputs.json --output <P>/stages/<batch>/snap.json
python recipe-atlas/scripts/build_release.py --candidate --output <P>/stages/<batch>/build --snapshot <P>/stages/<batch>/snap.json \
  --registry publication/asset-rights-registry.json --artifact-transform tools/publication/source_link_artifacts.py
git push origin HEAD:main
```
Then `git -C <SRC> pull --ff-only` and remove the worktree. Log `--stage merged` for each package.

## 8. Release (integrator; at least six accepted papers or three hours, whichever comes first)

Prepare the exact candidate first. This leaves `<SITE>` clean and keeps a gated copy at
`<P>/stages/<batch>/release/site-preview`:
```
python <SRC>/tools/publication/release_batch.py --source <SRC> --site <SITE> --work <P>/stages/<batch>/release \
  --release-id <batch> --reviewer "<auditor IDs for this batch>" --wait-ci 20
```
- It waits for source CI, builds twice (the final build must equal the candidate), stages an isolated
  site worktree, and runs the site's boundary gate. Check `release-summary.json` and
  `browser-review.template.json` in the same work directory. No site checkout files are changed.
- Serve `site-preview` locally (`cd <P>/stages/<batch>/release/site-preview` then
  `python -m http.server 8172`) and open it in a browser. Inspect every route in
  `required_browser_routes`. A completed supplied-paper Reader uses its paper-review route; an
  independently audited selected-page contribution without a full Reader uses its exact record
  route and scoped inventory entry. Check every affected ordinary material page, record links,
  source figures and responsive layout. Also inspect
  changed shared pages and controls. Save the actual browser review
  by copying `browser-review.template.json` to `browser-review.json`, setting `passed: true`, filling
  `reviewer`, `reviewed_at`, `checked_routes` and notes. Keep the pinned commit, site base, release ID,
  candidate SHA and preview SHA unchanged. A template or a build result is not a browser review.
- Publish that reviewed candidate using the **same** `--work` path:
```
python <SRC>/tools/publication/release_batch.py --source <SRC> --site <SITE> --work <P>/stages/<batch>/release \
  --release-id <batch> --reviewer "<auditor IDs for this batch>" --review-receipt <P>/stages/<batch>/release/browser-review.json \
  --wait-ci 20 --push --verify --ledger <P>/ledger.jsonl
```
- The helper rechecks the candidate and staged-preview hashes, source/site commits, browser receipt,
  source CI and exact staged site bytes before push. It then waits for Pages, checks 40 sampled files,
  **every new paper's formal Reader or scoped record and inventory, and every affected material route and material shard**
  anonymously, and logs each new
  `live_verified` event at most once. About 5 minutes plus CI and Pages time.
- On success, move the batch's packages to `<P>/published/` and delete their claim files.
- The private ledger is the release history. Do not write per-release prose in MEMORY.md,
  PUBLICATION.md or curation-control.json; use at most one short daily memory line. Do not make
  separate reagent-bind or baseline-closure commits.

## 9. When something fails

| Symptom | Do this |
|---|---|
| `release_batch` says source CI has not passed | Open the CI run for that commit on GitHub. Fix the cause in a **new** single commit (§7), push, rerun §8. Never push intermediate states |
| Final build differs from the candidate | Stop. Builds must be deterministic; report to the owner with both manifests |
| A site gate or allowlist failure | Never edit policies or allowlists to make it pass. Find the file the guard rejected and fix the package (path, provenance or rights row) |
| Live check timed out (Pages slow) | Reuse the **same** `--work` path and arguments, omitting `--push` and `--review-receipt` but keeping `--verify --ledger`. It checks the already-pushed release and logs events at most once |
| Live check mismatched files, paper routes or material routes | Wait 10 minutes (CDN), then re-verify as above. If it still mismatches, report to the owner |
| `<SRC>` or `<SITE>` not clean, or not fast-forward | Stop and report; do not reset or force-push |
| The owner says pause | Finish the current step, log it, and stop |

## 10. Measuring and reporting (on request and after the first forty)

```
python -B <SRC>/tools/workflow/package_workflow.py metrics <P>/ledger.jsonl --start <UTC start> --end <UTC end> \
  --output <P>/receipts/metrics-<start>-<end>.json
```
Use `full_audit_plan.py` for the new cohort and retain the old command for historical release-transport metrics. Report: distinct papers published (live-verified) per actual elapsed hour; papers skipped and held; median time
claim → frozen → audit accepted → live; deep-audit error count over the last 50. No progress pages, no
interval reports and no progress-only releases.

## 11. Never

- Publish or count a paper before `release_batch.py` reports `live_verification.passed: true`.
- Put papers, SI, extracted text, renders, private quotes or audit notes in either repository.
- Edit policies, allowlists or the rights registry to get past a gate; hand-edit generated files
  (`publication/build-inputs.json`, `publication/project-allowlist.json`, hub counts, Reader metadata).
- Let an extractor audit its own paper, or skip the full independent audit or required third-agent sample.
- Turn on the machine-extracted (silver) lane, or any preliminary display, before the owner approves the
  calibration result.
- Use paid or cloud model processing on paper text, or download new papers, without the owner's approval.
- Force-push, rewrite history, or change repository settings.

## 12. One-page cheat sheet

| Step | Command (short form) |
|---|---|
| Queue | `package_workflow.py live-sources`, `identity-map`, `rank --scope quantum-dot` |
| Log a stage | `package_workflow.py log-event <ledger> --stage <stage> --package-id <id>` |
| Validate | `package_workflow.py validate <pkg>/package.json --checkout <SRC> --output <receipt>` |
| Deep-audit draw | Fixed cohort seed/ordinal in `full_audit_plan.py`; never redraw on package revisions |
| Merge | `merger.py`, then `preflight.py` |
| Commit | `make_review_receipt.py`, `prepare_source_release.py --apply`, `git commit`, `check_project_manifest.py --pre-push` |
| Release | `release_batch.py ... --wait-ci 20` → browser review of exact `site-preview` → same `--work ... --review-receipt <review> --push --verify --ledger <ledger>` |
| Metrics | `package_workflow.py metrics <ledger> --start ... --end ...` |
