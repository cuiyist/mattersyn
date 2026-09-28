# One-build batch promotion

This is one reusable batch wrapper, not a per-paper workflow. It invokes the existing full `build_release.py --candidate` **once**, seals that run, and later copies the identical artifact into a new private stage and invokes the current full `gate.py` once. Promotion performs no second build, test run, source write, Git mutation, network operation, deployment or publication credit.

Status: engineering reviewed and independently tested by the integration owner (26 passing tests). Adopted for subsequent clean batch builds; no production speedup is claimed before measurement. Existing candidates cannot be retroactively sealed. Actual promotion remains contingent on the exact evidence described below.

## Invocation

Use the same approved Python environment for both commands. Output parents must exist; output directories must not. All evidence and outputs stay outside the source checkout. The source must remain at the same exact clean commit throughout. Display overrides are deliberately unsupported in this first version; the existing standard source-link transform is required.

```powershell
& $python -B -X utf8 one_build.py build --source $source --snapshot $snapshot --out $candidate --contract $contract --contract-sha $reviewedContractSha
& $python -B -X utf8 one_build.py promote --source $source --candidate $candidate --seal-sha $reviewedSealSha --out $promoted --review $promotionReview --review-sha $reviewedPromotionReviewSha
```

The first command uses the real unchanged builder and writes `build-seal.private.json` only after every required stage passes. Root reviews and pins this seal externally. The second command requires actual source CI results and both independent CI artifact manifests. It produces `dist/`, fresh boundary outputs, and `promotion-receipt.private.json`. **That receipt is intentionally a new private schema, not a forged legacy final-build or deployment receipt.** Downstream transport must explicitly accept this reviewed schema and still bind the exact stage inventory, exact site-commit CI and anonymous bytes before publication credit. Current downstream release helpers have not been changed.

`build-contract.example.json` and `promotion-review.example.json` are deliberately invalid templates with null pins. They are not approval generators. The root reviewer must fill exact existing proofs; no automatic scientific or browser approval is inferred.

## What is preserved

| Gate | Behavior |
|---|---|
| Independent scientific, source and artwork review | Existing accepted receipts are pinned in the externally reviewed promotion descriptor; this module does not conduct or invent those reviews. |
| Clean committed input closure | Every tracked file is read and SHA-256 inventoried, independently matched against its Git blob, before/after the build and promotion. Index/worktree status and exact HEAD are checked. Copied source trees and `tools` reject ignored/untracked files that could enter the build or imports. |
| Snapshot and metadata | Exact committed blueprint projection; snapshot identity and all declared hashes; complete independent source inventory additionally covers blueprint omissions. Metadata-only commits also invalidate reuse. |
| Build, canonical preservation, tests, QA | Unchanged builder executes its seven builders, metadata/canonical checks, transforms, complete unittest discovery, site, atlas and quality checks. Exactly 13 ordered successful log entries, predeclared positive test count, no skipped-summary acceptance, and positive passed QA count are bound to the seal. Full stdout/stderr remains private. |
| Independent reproducibility and exact-head source CI | Both existing required Windows/Linux build jobs and compare job must succeed for the exact commit. The unchanged comparator compares every local candidate binding/file against both actual CI manifests. Nothing is normalized or excluded. Existing CI also retains its additional boundary/importer/publication/workflow/silver/JavaScript/source-export tests. |
| Existing actual browser checks | Pin real browser receipts and exact scoped artifact paths/hashes in the reviewed descriptor. No new browser check is claimed. Changing a bound artifact invalidates reuse. |
| Source export | Exact source boundary manifest/report, current source commit, policy and rights hashes, passed counts; acquisition and authenticity reviewed by root. |
| Site boundary | Current unchanged guard runs fully and freshly against a new exact copy using the reviewed allowlist/current policy/current registry. No final policy/content/rights verdict cache is introduced. All candidate files, copied files, inputs and evidence are rechecked after the gate. |
| Release and credits | Receipt remains unpublished with zero credit. Required site CI, final stage/commit hash verification and anonymous verification remain external, mandatory root gates. |

## Trust and limits that root must accept before adoption

* The operator owns the source, candidate and promotion directories exclusively during transactions. No portable Python hashing routine prevents a malicious concurrent writer from replacing and restoring bytes between observations. Reparse points, symlinks, multiply linked input/artifact files, same-length changes, ordinary read/copy/gate races and path aliases in manifests are rejected. This is **not** a sandbox, signed attestation, cross-process filesystem lock or defense against a malicious operator.
* Reviewed SHA pins are supplied out of band. If an attacker may rewrite both a seal and its trusted expected hash, authenticity is lost. The tool cannot authenticate fabricated offline GitHub/science/browser receipts. Root must verify that CI manifests actually came from the named successful exact-head workflow artifacts before pinning the descriptor.
* The OS and installed runtime remain trusted, operator-managed dependencies. Python executable bytes, package names/versions, version, prefix and the restricted child environment are recorded/rechecked; this is **not a full byte inventory of the Conda/OS installation**. A replaced package with unchanged version is outside this trust model. No guard verdict is reused: the full guard runs under the current runtime. A hermetic-runtime guarantee would require a separately reviewed immutable environment, and is not claimed here.
* Child environment excludes secrets and arbitrary Python/Git overrides. The script and exact expected builder/comparator/guard/transform hashes are bound; all other tracked dependency files are in the source closure. Git symlinks/submodules and non-UTF8 paths are unsupported and fail closed.
* Historical unsealed candidates, alternate transform/override modes, failed/changed builds, unavailable exact CI manifests or an unreviewed promotion descriptor cannot use this path. Use the existing release procedure when necessary; never fabricate a seal to avoid it.
* Root engineering review and release documentation accept this path. Downstream transport must explicitly verify the new receipt and exact artifact inventory; legacy helpers that expect a final-build manifest cannot consume it silently. There is no `--skip-tests`, approval toggle or backward-compatible fake final manifest.

## Verification and timing

Run `python -B -X utf8 -m unittest discover -s . -p test_one_build.py -v`. Tests use a tiny temporary committed fixture, unchanged production builder/comparator/gate/guard, synthetic builders/data and clearly synthetic review receipts. The success path executes the full fixture build once and proves promotion invokes only the fresh gate. This is engineering evidence, not a scientific or production release acceptance.

Twenty-six tests pass. Adversarial coverage includes complete source closure even with Git assume-unchanged, ignored inputs, same-size/mtime-restored artifact edits, simultaneous manifest+artifact rewrite, missing/extra files, log/seal/contract/snapshot drift, failed/incomplete/skipped tests, wrong/missing CI, unequal CI artifacts, changed science/browser proofs, changed browser bytes, stale export, policy/rights/runtime drift, mid-copy/mid-gate changes, path traversal/Windows devices/case collisions/duplicate JSON/hardlinks/reparse flags, failed actual boundary and actual source-text sanitation rejection.

Saved Ge/Du final logs measured about 105.17/105.39 seconds of repeated build/validation stages, with fresh boundary stages about 46.87/43.44 seconds. Those are historical stage timings, **not measured promoter savings**. This prototype has not run on the full current site; no end-to-end speedup or papers/hour claim is justified. The 26-test fixture suite took 9.176 seconds in the final author run, unrelated to production throughput.
