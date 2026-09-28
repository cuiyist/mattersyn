# MatterSyn workflow v2: audited and machine-extracted contributions

Adopted September 26, 2026, with the September 28 experimental-display and
reporting instructions below. Calibrated field-precision thresholds remain
98%, 95% and 90% for high-, medium- and low-frequency material families. The
renewed 20-papers/hour target is not an achieved rate; partial experimental
evidence is not a completed paper. Morning and two-hour reports are disabled.

## Two separate lanes

**Gold:** a source-scoped contribution checked by an independent scientific
auditor. Use one paper package and one consolidated audit covering quantities,
units, steps, branches, product/sample links, conflicts and source locators. Main
text may be a minimum publishable unit; report its inspected scope and unreviewed
or unavailable SI explicitly. Later SI is a versioned addition, not a reason to
claim the earlier contribution covered it. Do not omit difficult variants within
the declared scope just to finish a package. No automatic tier promotion.

**Calibrated silver:** local machine extraction, two separate passes that never see one
another's answers, deterministic evidence checks and calibrated field admission.
The public badge is **Machine-extracted, not reviewed**. The 500/day target now
means distinct silver source contributions actually deployed and anonymously
verified. Keep gold/silver counts, record counts and pair counts separate.
Neither model agreement nor a quote match is a scientific audit.

**Experimental silver display:** a separate owner-authorized view of partial
machine-extracted evidence may publish after exact source identity, original
model-output binding, deterministic evidence/schema checks, independent
engineering/privacy review and ordinary release checks. Label it unreviewed,
accuracy unmeasured and training excluded. A single extraction pass is not
two-pass agreement or calibration. Keep withheld claims private; unsupported
notation is not repaired into a supported fact. Count a distinct experimental
display only after deployment and anonymous verification, separately from
completed papers, complete recipes, gold, calibrated silver and verified pairs.

Existing Reader pages retain their scoped review history; do not relabel all of
their fields as complete calibration answers. A method card or optical-only record
does not create a structural training pair.

## Work allocation and packages

The owner's standing instruction authorizes routine implementation, integration
and publication for this existing MatterSyn task without repeated permission
requests. Continue within the established project scope and respect any newer
pause or changed instruction. This authorization does not extend to paid
processing, new downloads or external source transfers. Retain independent
scientific review, exact source and sample attribution, privacy and release
checks; use the existing authenticated local publication workflow.

Rank the existing screened-pass collection by preparation and structural evidence,
then group compatible work by family. Main and SI remain independent intake
documents; link them only when source identity has been checked. Keep unknown
primary-source identities and family classifications unresolved. Do not infer
family-popularity bands from unnormalized screening free text.

Use one issue/PR per paper package when GitHub transport is active. Existing local
packages can continue through the additive importer. Package authors work in
disjoint branches/directories; the tested merger serializes shared integration.
Until repository protection and cross-repository publishing are configured and
tested, the integration owner still applies accepted packages and publishes. A
proposed CI workflow is not evidence that an automatic publisher is operational.

Use `tools/workflow/package_workflow.py` for package validation, scientific diffs,
screened-queue ranking and event-derived metrics. A changed value, uncertainty,
source scope, sample/figure assignment or training eligibility invalidates the
affected scientific audit. Administrative timestamp or revision changes can reuse
an exact accepted audit only under the explicit scientific-digest policy. Derive
aggregate counts and hashes mechanically; do not re-audit unrelated papers.

## Presentation and release

Audited data may publish with **presentation pending** when the scientific record,
source links and required reader qualifications are usable. The pending label is
not an assertion of CdSe-level visual completion. Batch molecular models, unit
cells, morphology and apparatus refinements weekly; preserve the existing high
presentation standard and all exact source/sample bindings for the completed
Reader tier. Figure-derived values and complex panel links remain gold-only.

Use the one-commit source preparer in `tools/publication/prepare_source_release.py`
after reviewing and staging exact changed files. It generates the build blueprint
and content-bound manifest together. It does not make a scientific approval or
publish. Bind that manifest to clean HEAD with `bind_source_allowlist.py` at build
time, then retain the existing exact public-boundary gate. Do not push a payload
with stale release controls. Never remove privacy/provenance checks to reduce
bookkeeping. Full PDFs/SI, raw text, evidence quotes, page renders, private audits,
drafts and model responses stay local.

No status-only website releases. Batch accepted calibrated silver contributions after
calibration, and release ready gold or separately labelled experimental display
payloads after their applicable checks without waiting for blocked papers. Do not silently introduce a cross-repository token or broaden permissions;
use the established authenticated local release bridge until a CI transport is
explicitly configured and tested. A merge alone is not publication credit.

## Local extraction and calibration

`tools/silver/local_runner.py` permits only a loopback Ollama endpoint and installed
models with pinned digests. It rejects redirects, disables proxy use, performs no
model download and sends no source text to external services. Two model passes
remain machine drafts. Keep the page map and every quoted span in the private
validation store. Preserve source units; never repair K into degrees Celsius.

`tools/silver/silver.py` reconciles drafts, checks exact source-page/value/unit
anchors and explicit sample context, scores held-out references and produces a
whitelisted public candidate. The first pilot supports scalar text facts only;
ranges, approximate values, figures and unsupported structures must be withheld,
not collapsed into a scalar. Resolve chemical identities from the local registry;
do not infer an unreported salt, isomer or coordination geometry.

Freeze model, prompt, validator and field policy identities before calibration.
Exclude development sources, related document duplicates and prompt-tuning cases
from the held-out set. Ground-truth fields need independent review and explicit
coverage; website omissions are not negative ground truth. Score precision and
recall separately by field and family band, with source-cluster counts and
confidence limits. Insufficient evidence means **STOP**, not 100% accuracy.
Admission uses the plan's field-instance binomial lower confidence bound, with
source-cluster sensitivity reported separately. At zero errors, the high band
needs about 149 audited field instances, not 149 papers. These nominal bounds
assume independent instances; within-paper dependence must be acknowledged by
the independent calibration reviewer. Do not present 60 source groups or model
agreement alone as proof of 98% precision.

High-band disagreements are withheld. Medium/low disagreements retain alternatives
privately and can be labelled uncertain publicly only after field calibration;
uncertain values are masked from training. Accepted silver training data keeps its
tier, locators, calibration version and explicit weighting. Silver never enters
gold evaluation. Prevent primary-source, SI and related-sample leakage across
training/evaluation partitions.

Before production, independently review the calibration result. Then pilot at
50 silver papers/day with a random 5% audit, concentrated enough to detect errors
in the admitted fields. Stop affected field/band publication when the audited
error rate exceeds its threshold. Publish an accuracy summary only from actual
audit results; never fill an accuracy page with forecasts. Scale toward 500/day
only after the pilot demonstrates acceptable errors and complete delivery rate.

## Metrics and memory

Generate durations and counts from idempotent package/PR/deployment events. Credit
a primary source once after anonymous verification; a promotion, additional
variant, SI addition, correction or presentation pass is not another new paper.
Report gold and silver separately. Do not infer active work from commit gaps or
claim continuous unattended processing between runs.

The owner subsequently disabled morning reports; two-hour reports also remain
disabled. Report progress on request, separating actual verified gold,
calibrated silver and partial experimental display, with truthful scope and
publication intervals. Quiet continuation remains active. Save concise memory
and reusable changes with substantive milestones, not a deployment for every
checkpoint. Preserve historical
trial receipts unchanged. New incoming papers remain outside the active screened
snapshot until the owner resumes intake. No paid APIs, source-file transfers,
model downloads or GPU purchases are authorized by this workflow.

## Build-derived inventory and silver monitoring

`recipe-atlas/data/inventory-evidence.json` retains authored source scopes, DOI
bindings, notes and the fixed corpus snapshot. The build derives the inventory
counts, record memberships and material relationships from current canonical
records and generated source/atlas indexes. Never edit generated inventory totals
or refresh an unrelated scientific audit merely because those totals changed.
New source scope metadata still requires review. This migration covers inventory;
other scientific presentation sidecars retain their existing audit boundaries.

The separate calibrated silver Reader is disabled until a real calibrated public manifest
passes release review. It does not fetch drafts or change gold counts/exports.
See [Reader integration](../../../recipe-atlas/scripts/SILVER_READER.md).
`tools/silver/monitor.py` selects a deterministic 5% daily sample of first verified
silver source releases, retains every sampled claim, and proposes field/band
suspensions from actual independent judgments. See
[monitoring](../../../tools/silver/MONITORING.md). Preserve its private input
chain; do not manufacture deployment or accuracy receipts from candidate counts.

The code and synthetic tests establish software behavior, not scientific precision.
Complete source-separated labels, measured calibration, independent approval,
version-audit handling and a release-admitted silver pilot remain required.

## Current continuation and administrative batching

Continue until the owner explicitly pauses. Morning and two-hour reporting are
off; provide progress on request and keep quiet continuation separate from
reporting. A scheduled heartbeat is not evidence of continuous execution.

After actual publication and anonymous verification, retain exact successful
CI, public-byte proofs, source/site commits and idempotent event IDs privately
immediately. Batch the sanitized public memory/control/receipt updates into the
next ready substantive source transaction. Rebase exact before-images and run
all fresh source, policy, rights, privacy, build, output and CI checks for that
combined payload. Do not mark a private overlay public, reuse changed-input
approvals or add publication credit before verification. Use the normal full
standalone transaction when an urgent public update is needed or no suitable
batch is ready. This operator sequencing change does not cache decisions or
weaken any calibrated, gold or training gate.

## Exact excerpt experiments

For damaged PDF text, try bounded method-specific source excerpts with field-specific unit choices and an explicit omission option. Keep original page offsets and hashes, literal source labels, raw model responses and rejected attempts. Do not repair model values, join damaged source symbols or reassign units to satisfy a schema. If humans select spans or reagent slots, state that assistance; scalar extraction is not autonomous recipe discovery. Measure preparation, failed attempts, review and publication as well as model-call time. Unmeasured partial experimental fields retain zero complete-paper/pair/training credit.

## Strict numeric bounds

For source inequalities, set `minimum_exclusive` or `maximum_exclusive` on the existing quantity object; a prose qualifier alone does not preserve the boundary in machine exports or displayed conditions. Keep the bound value and source locator, and verify the displayed relation after building. For a bounded correction, reuse unchanged source audits, independently check the corrected relation, and refresh the dependent record, molecule, apparatus and figure provenance hashes without changing asset content.

## September 28: remove duplicate release work

Use two source-scoped extractors, one independent auditor and one integration owner within the four-worker limit. Author canonical records and Reader bindings together with the generic importer; keep five or fewer claimed papers. The accepted queue feeds ready batches without waiting for blocked papers. Run one clean full batch build through `tools/publication/one_build.py`, then reuse its sealed output via a fresh boundary gate rather than repeat the entire build. Follow `tools/publication/ONE_BUILD_RELEASE.md`; never invent science or browser receipts. Reuse unchanged independent audits and exact artifact checks. The 20 distinct verified papers/hour objective requires two extractors averaging six active minutes per paper each and one auditor averaging three minutes per paper, before integration constraints. Those are capacity targets, not timeouts or demonstrated performance. Measure each stage and rework; count only distinct deployed and anonymously verified source contributions.


### Ready-batch overlap and unchanged-review reuse

After an exact artifact is copied into the site checkout, committed and pushed, the next source batch may be prepared while Pages deploys. Keep the earlier artifact, source commit, CI, boundary and anonymous checks separately bound; a changing later checkout is not a reason to rebuild the earlier release. Do not count either batch before its own deployment verification.

Reuse prior exact file-review objects during allowlist preparation when bytes, size and current path/content-class approval still match. Check current allowed classes and any required exact-blob approval. Run the final full boundary under current rights/policy for all files; the prior guard verdict is not cached. This avoids repeating sanitation during approval preparation. Independent science and changed figure/sample bindings remain required.

Use fixed start/end times and a verified live baseline when the owner requests a throughput trial. Record carried-over work separately and never silently extend the denominator, count record variants as papers, or call an unachieved throughput target demonstrated.


### Early delivered-asset completeness

Before the first full batch build, validate every declared public_asset and its exact public_asset_sha256 across figure, table, scheme, equation and Reader original_assets entries. A duplicate table descriptor still requires its own hash even when the same image is correctly listed under figures. Check all occurrences against delivered bytes during package preflight; reuse that acceptance if those bytes and assignments stay unchanged. A missing metadata checksum may be corrected against the already accepted identical asset without restarting scientific reading.
