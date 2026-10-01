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
The metrics ledger is the single file `<P>/ledger.jsonl`.

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
- Read [workflow-v5.md](workflow-v5.md) once per session. Do not read the historical workflow files.

## 2. Roles and how to run them continuously

| Role | Instances | Loop |
|---|---|---|
| Extractor | start with 3 (more if available) | §4, forever: one active paper plus one claimed next paper |
| Auditor | 1 per ~4 extractors | §5 and §6, forever: the oldest package in `ready-for-audit` first |
| Integrator / releaser | 1 | §7 and §8, forever: whenever `ready-for-integration` is non-empty and no release is running; when idle, extracts |

Run each role as its own continuous agent session. The **auditor must be a different agent instance**
from the paper's extractor, with a different ID in the package `audit` block. Never pause between
loops waiting for a timer. If a queue is empty, do the next role's work.

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
python -B <SRC>/tools/workflow/package_workflow.py audit-sample <P>/packages/<id>/package.json \
  --output <P>/receipts/<id>-sample.json
python -B <SRC>/tools/workflow/package_workflow.py log-event <P>/ledger.jsonl --stage extraction_frozen --package-id <id>
```
- Fix every validation error. A quote that does not match its page is either corrected, or listed in the
  package for the auditor to check visually.
- Receipts are create-only: use `-2`, `-3`, … for reruns.
- Move the package folder to `<P>/ready-for-audit/` and claim the next paper (4.1).

## 5. Quick audit (auditor; every paper)

Open the package, its validation receipt, its quote receipt and its sample receipt. Log `--stage audit_started`.
Check, in this order, looking at the cited pages and figures only where needed:

| Checklist key (package `audit.checklist`) | What to check |
|---|---|
| `document_scope` | Scope and exclusions are stated honestly (e.g. "SI not reviewed") |
| `recipe_and_variants` | Every recipe and variant inside the stated scope is present; none merged |
| `quantities_units_conditions` | Every value the quote check did not confirm; every reaction step's temperature, time and atmosphere; units |
| `chemical_identities` | Each reagent's identity and stock composition matches the source |
| `sample_structure_links` | Every recipe→sample, sample→structure and figure→sample assignment has evidence |
| `conflicts_missingness` | Conflicts shown side by side; missing values marked missing, not guessed |
| `evidence_locators` | Locators resolve to the evidence actually checked |
| `asset_provenance` | Figure crops, provenance, hashes and rights status are exact |

- Each item is `passed`, or `not_applicable: <reason of at least 10 words>`.
- **Accept:** set `audit.status: accepted`, `reviewer_id` (your ID, different from `author_id`),
  `receipt_id`, and `scientific_sha256` from the validation receipt. Rerun `validate` (new receipt number).
  Log `--stage audit_accepted`.
- **Changes needed:** write the list into `<P>/ready-for-audit/<id>/changes-requested.md`, move the package
  back to `<P>/packages/`, and log `--stage changes_requested`. The original extractor fixes it and refreezes (4.4).
- If `deep_audit_required` is true in the sample receipt, do §6 **before** accepting.
- Then move the accepted package to `<P>/ready-for-integration/`.

## 6. Deep audit (auditor; about 10% of papers, as selected by `audit-sample`)

Read every scoped page, table and figure independently, and compare all values and assignments with the
package. Record the result in `<P>/receipts/deep-audit-log.jsonl` as one line:
`{"package_id": ..., "at": ..., "errors_found": <n>, "summary": "..."}`.
- Errors found: fix them through `changes_requested` as in §5.
- **Stop rule:** if more than 5 of the last 50 deep-audited papers had any error, stop all extraction
  and tell the owner. The quick audit is missing too much.

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

## 8. Release (integrator; right after each push)

```
python <SRC>/tools/publication/release_batch.py --source <SRC> --site <SITE> --work <P>/stages/<batch>/release \
  --release-id <batch> --reviewer "<auditor IDs for this batch>" --wait-ci 20 --push --verify --ledger <P>/ledger.jsonl
```
- It waits for source CI, builds twice (the final build must equal the candidate), stages the site, runs
  the site gate, pushes, waits for the live site, checks 40 files anonymously and logs one `live_verified`
  event per new paper. About 5 minutes plus CI and Pages time.
- On success, move the batch's packages to `<P>/published/` and delete their claim files.
- Use the dry run (drop `--push --verify`) first if the batch touched shared code, policies or many files.

## 9. When something fails

| Symptom | Do this |
|---|---|
| `release_batch` says source CI has not passed | Open the CI run for that commit on GitHub. Fix the cause in a **new** single commit (§7), push, rerun §8. Never push intermediate states |
| Final build differs from the candidate | Stop. Builds must be deterministic; report to the owner with both manifests |
| A site gate or allowlist failure | Never edit policies or allowlists to make it pass. Find the file the guard rejected and fix the package (path, provenance or rights row) |
| Live check timed out (Pages slow) | Rerun the **same** §8 command without `--push` but with `--verify`. It re-checks the already-pushed release and logs events at most once |
| Live check mismatched files | Wait 10 minutes (CDN), then re-verify as above. If it still mismatches, report to the owner |
| `<SRC>` or `<SITE>` not clean, or not fast-forward | Stop and report; do not reset or force-push |
| The owner says pause | Finish the current step, log it, and stop |

## 10. Measuring and reporting (only when the owner asks)

```
python -B <SRC>/tools/workflow/package_workflow.py metrics <P>/ledger.jsonl --start <UTC start> --end <UTC end> \
  --output <P>/receipts/metrics-<start>-<end>.json
```
Report: distinct papers published (live-verified) per elapsed hour; papers skipped and held; median time
claim → frozen → audit accepted → live; deep-audit error count over the last 50. No progress pages, no
interval reports and no progress-only releases.

## 11. Never

- Publish or count a paper before `release_batch.py` reports `live_verification.passed: true`.
- Put papers, SI, extracted text, renders, private quotes or audit notes in either repository.
- Edit policies, allowlists or the rights registry to get past a gate; hand-edit generated files
  (`publication/build-inputs.json`, `publication/project-allowlist.json`, hub counts, Reader metadata).
- Let an extractor audit its own paper, or skip the quick audit.
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
| Deep-audit draw | `package_workflow.py audit-sample <pkg>/package.json --output <receipt>` |
| Merge | `merger.py`, then `preflight.py` |
| Commit | `make_review_receipt.py`, `prepare_source_release.py --apply`, `git commit`, `check_project_manifest.py --pre-push` |
| Release | `release_batch.py ... --wait-ci 20 --push --verify --ledger <ledger>` |
| Metrics | `package_workflow.py metrics <ledger> --start ... --end ...` |
