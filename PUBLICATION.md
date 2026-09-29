# MatterSyn publication workflow

## Current instruction: regular material pages only

The owner retired the public preliminary collection and changed the throughput target to papers processed, including source-supported skips and successfully published regular contributions. Follow [processing workflow v4](skills/mattersyn-paper-to-site/references/processing-workflow-v4.md). Preserve private drafts, but do not display them or count them as website contributions. Historical preliminary publication permissions below are superseded. Existing reviewed records, scientific review requirements, exact release checks and historical receipts remain intact.

## Current preliminary-first instruction

The owner requested a temporary pause on September 28 to revise workflow and
first-publication quality, then resume toward 20 published primary papers/hour.
The [v3 workflow](skills/mattersyn-paper-to-site/references/throughput-workflow-v3.md)
allows a separate preliminary synthesis contribution with a source-checked
protocol and explicitly linked structural outcome before independent scientific
review or custom illustrations. It must disclose its limited scope, pending
independent audit, unmeasured accuracy and training exclusion. Old scalar-only
experimental notes do not meet this contribution definition. Gold and
calibrated-silver admission remain unchanged. Count preliminary publications
separately from reviewed papers and verified pairs; upgrades and extra variants
do not create new primary-paper credit. All lanes retain exact source evidence,
public schema/privacy checks, batch release validation and anonymous verification.

Publication order: pass the local build, source CI, browser review and fresh
public-file boundary, then push the approved site commit to trigger site CI.
The Pages deploy job depends on `build-and-validate`; a push is not proof of a
successful deployment. After site CI and deployment succeed, verify the live
files anonymously and only then record publication credit. These post-push
checks cannot precede the push that starts them, and none may be bypassed.

Both `cuiyist/mattersyn` and `cuiyist/mattersyn-site` are public at the owner's
request. The project repository contains code, reviewed records, project memory,
reusable skills, safe audit summaries and cleaned history. The site repository
contains the deployable website, reviewed data and citations, selected source
figures and site-specific deployment controls. Complete source PDFs/SI, raw
text/OCR, full-page renders, private working crops, detailed private audit
evidence, unreviewed candidates, credentials and original history bundles remain
local. Public status does not mean every old GitHub object or cache is gone: the
review-cited old raw-source URL returned HTTP 200 anonymously after the repository
became public on 2026-09-24. Do not claim server-side deletion or cache purging.

## Evidence and image provenance

At the user's explicit direction, selected original source figures remain available
on the public reader. The 2026-09-24 restoration checkpoint covers 743 figures; see
`research-assets/public-audits/source-figure-restoration-20260924.json` in the
project repository. This display instruction is not a claim that publisher
permission or a reuse license was verified: the audit records permission as
unverified, and the registry must retain that status. Pair each public figure with
its citation, page/figure locator, supported record/sample assignment, exact asset
hashes and any crop or transformation details. Keep complete papers and SI,
extracted/OCR text, full-page renders, private working crops, unselected source
assets and detailed audit materials out of the public site repository.

Each recipe retains its source, sample assignment, measured conditions, reported
outcomes and review status. Contradictory observations remain separately attributed.
Publication does not imply eligibility for every model-training task. In particular,
a named material or a reference unit cell is not a verified sample-coordinate pair.

Every displayed image needs an exact path, content hash, origin classification,
citation and source/sample provenance. Preserve original figure content and label
any crop or transformation. Selected source figures remain distinct from authored
molecular structures, apparatus illustrations and source-link cards; never present
an authored card as TEM, SAED, XRD or a spectrum. The project display choice does not
change the recorded rights status or imply permission was independently verified.
Full source documents, full-page renders and private working crops remain in the
private evidence archive; display hashes identify the public figure assets.

The asset register, also copied into the site's release controls, records factual identifiers, provenance and permission
status, with evidence links where available. It is a release-control record, not a
blanket legal determination about third-party papers. User selection for display
does not relabel an asset as licensed or permission-cleared; preserve the recorded
status while retaining the selected figures under the current project preference.

## Build and release

The September 26 scaling workflow uses a single source commit with generated,
content-bound controls. Follow [the single-commit guide](tools/publication/SINGLE_COMMIT_RELEASE.md): stage reviewed payloads, prepare the blueprint and manifest together, then bind the committed manifest to clean HEAD outside the repository before export. CI uses that runtime allowlist. This removes the follow-up closure commit without removing exact public-file review or scientific evidence checks.

Calibrated silver contributions require frozen-pipeline calibration and independent
calibration approval. The owner's September 28 authorization also permits a separate
experimental display of partial machine-extracted evidence before calibration.
That display must say machine-extracted, not reviewed and accuracy unmeasured;
retain explicit input-page and incomplete-recipe scope; pass deterministic evidence
checks, privacy review and the ordinary release/anonymous-verification gates; and
withhold rejected claims. It adds no gold, calibrated-silver, completed-paper,
usable-complete-recipe, verified structure-pair or training-ready credit. Quotes,
source text and model responses remain private. Experimental display is not
calibration approval. A scoped
gold contribution may be presentation-pending; its declared scientific scope
still needs the consolidated independent audit. Automatic cross-repository
publishing is not installed by this increment; the existing local handoff remains.

Inventory totals and memberships are generated during the build from canonical
records, source review metadata and atlas indexes. The authored
`recipe-atlas/data/inventory-evidence.json` preserves scientific review scope and
notes; it is not a place to hand-update totals. Source scope, DOI, page counts,
record assignments and component relationships must reconcile before rendering.
No scientific record or training eligibility is changed by this migration.

The calibrated silver Reader remains hidden until its existing admission gates
pass. Experimental evidence uses its own schema, page and counts; it must not be
routed through a fabricated calibration receipt or mixed into reviewed/training
exports. Its measured accuracy remains unknown and all training weights remain
zero. Candidate/monitoring projections keep `publication_enabled:false` and cannot
authorize deployment. Actual source credit requires a successful controlled release
and anonymous verification; partial evidence does not establish a complete paper.
Calibration and independent approval remain necessary for calibrated admission and
measured accuracy claims. Synthetic tests establish software behavior only.

Use the single build entry point documented in the project README. Authored static
inputs live in `recipe-atlas/static`; generated `dist` is a build output. A committed
input blueprint and an externally generated runtime snapshot bind each build to
its source commit and input hashes. Candidate mode produces an explicitly
unapproved artifact, suitable for inspection but not publication.

A final release must pass record/schema checks, record-membership and task-eligibility
comparisons, site/link/asset checks, the per-paper scientific audit requirements,
and the separate public-boundary gate. The gate accepts only the exact reviewed
paths and hashes in its allowlist. Unlisted files, source documents, private caches,
machine paths, unmatched image hashes, or missing figure attribution and
source/sample provenance stop delivery. Release path scanning recognizes local paths
in ordinary prose and source-code literals, including escaped or repeated Windows
separators such as doubled backslashes in JavaScript and Python. Regression tests
cover these forms while retaining ordinary chemistry, citations and URLs. Do not
approve a release if an escaped personal path is missed.

Generated UTF-8 website text uses explicit LF newlines before release hashes are
recorded, for reproducibility across Windows, macOS and Linux. Apply this rule only
to generated text. Preserve approved scientific records, original figure/image
assets and CIF/SDF/XYZ coordinate files byte-for-byte; do not normalize source
values or binary assets to make hashes match. Narrow hash-bound exceptions identify
upstream COD exporter comments, not local research-workspace paths.

Windows and Linux CI build the same committed input snapshot and compare every
artifact path, byte count and SHA-256, together with the source and snapshot
bindings. A configured comparison is not evidence of success; check the completed
run before claiming cross-platform reproducibility.

Long reader explanations are not automatically verbatim paper quotations. The
earlier repository-review checkpoint contained 37 formal paper-review files; their structured text
retains claim types, sample scope and source locators. Assess wording against the
source before shortening a passage; do not truncate scientific content by length.

The user's display preference permits the selected source figures to remain on
the public site while their rights status is unresolved. Preserve that status; do
not describe the figures as cleared.

Both README bibliographies come from the same approved source records. Public collection counts and the homepage fallback use the same dated release snapshot. Owner-only review progress is excluded from the public interface and its progress endpoint redirects to the synthesis catalogue. Several
completed contributions may be published together; screening, extraction, audit and
building can proceed on different papers in parallel. Each contribution still needs
its own review history. Throughput is reported from completed work, not inferred from
the number of workers or model calls.

GitHub Pages deploys only the artifact validated by the site workflow. The old
same-directory synchronization command is retired. A failed validation must not be
bypassed by uploading the repository root or switching back to branch publication.

Before pushing a source update, use the current single-commit preparer described
above. It stages the reviewed payload and generated controls together. Commit
once, check the clean manifest, bind it to final HEAD outside the checkout, and
run the required source boundary and clean build checks. Do not push intermediate
memory, asset or data changes with stale controls. The earlier separate closure
commit procedure is retired for current content-bound manifests.

## Historical preservation

Verified private Git bundles and working-file manifests preserve the original
project history and evidence. Both MatterSyn repositories are public, but the
source and site contain different reviewed deliverables. The source repository
preserves cleaned project history and safe project documentation; the site
repository contains the approved deployable website and its required reader data.
Neither contains the private source archive or detailed private audit evidence.

A follow-up review confirmed that removed content had remained retrievable through
old public GitHub commit IDs. The user later reauthorized the project repository to
be public; the reviewed old source URL then returned HTTP 200 anonymously. This
visibility choice does not prove old objects, caches or copies have been erased.
GitHub Support may or may not remove retained objects; no purge is guaranteed. No
further history rewrite is planned, and no support request is to be submitted
without separate explicit user authorization.

## Reuse one successful batch build

The integration owner has adopted the tested [sealed one-build workflow](tools/publication/ONE_BUILD_RELEASE.md). Build and run the complete checks once on clean committed batch inputs. Promote only those identical files after the required science, browser, source-export and exact-head CI evidence is verified; run the public artifact boundary once. A promoted-artifact receipt is not a publication receipt. Site CI and anonymous verification still precede paper credit. Any changed or failed dependency invalidates reuse. Do not create per-paper publishing scripts or rerun a passing unchanged release merely to produce another status report.
