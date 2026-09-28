# MatterSyn workflow v2: audited and machine-extracted contributions

Adopted September 26, 2026 from the owner's scaling plan. This supersedes the
earlier 20 audited papers/hour target, two-hour reporting cadence and mandatory
per-paper presentation hold. The owner confirmed field-precision thresholds of
98%, 95% and 90% for high-, medium- and low-frequency material families.

## Two separate lanes

**Gold:** a source-scoped contribution checked by an independent scientific
auditor. Use one paper package and one consolidated audit covering quantities,
units, steps, branches, product/sample links, conflicts and source locators. Main
text may be a minimum publishable unit; report its inspected scope and unreviewed
or unavailable SI explicitly. Later SI is a versioned addition, not a reason to
claim the earlier contribution covered it. Do not omit difficult variants within
the declared scope just to finish a package. No automatic tier promotion.

**Silver:** local machine extraction, two separate passes that never see one
another's answers, deterministic evidence checks and calibrated field admission.
The public badge is **Machine-extracted, not reviewed**. The 500/day target now
means distinct silver source contributions actually deployed and anonymously
verified. Keep gold/silver counts, record counts and pair counts separate.
Neither model agreement nor a quote match is a scientific audit.

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

No status-only website releases. Batch accepted silver contributions daily after
calibration, and release ready gold contributions without waiting for blocked
papers. Do not silently introduce a cross-repository token or broaden permissions;
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

The owner subsequently restored a daily progress report at 08:00 America/Chicago
and resumed remaining workflow revisions followed by website building. Report the
actual interval, completed and pending revisions, newly verified gold and silver
papers, cumulative coverage, pairs, audit/calibration state, blockers and next work.
Keep two-hour checks retired; report material failures when they occur. Save concise memory and reusable changes with substantive
milestones, not a new commit/deployment for every checkpoint. Preserve historical
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

The separate silver Reader is disabled until a real calibrated public manifest
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

## September28 continuation and experimental silver display

The owner now requests continued work until explicitly paused and reasserts the20 papers/hour target. Use the active20-minute continuation heartbeat separately from the daily08:00 report; do not restore the retired two-hour reports or reopen historical trial windows. Count only actually deployed and anonymously verified distinct source contributions.

The latest instruction explicitly requests silver publication. A separate experimental display may expose evidence-validated machine-extracted records labelled not independently reviewed, with accuracy unmeasured until calibration. Exclude these records from training-ready exports and gold counts; do not claim the earlier calibration thresholds passed. The98%/95%/90% thresholds and independent calibration approval remain required for calibrated silver admission. Preserve privacy, source identity, exact evidence, schema and public-release checks. Routine decisions within this scope need no repeated permission.

The owner subsequently disabled the morning check. Both morning and two-hour reporting are off; provide progress on request. Quiet continuation remains active and this reporting change does not pause curation.
