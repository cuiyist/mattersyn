# MatterSyn publication workflow

MatterSyn has two public repositories. `cuiyist/mattersyn` contains application
source, reviewed structured data, project memory, skills, citations and public
audit summaries. `cuiyist/mattersyn-site` contains the reviewed website release
and the controls used to validate it before GitHub Pages deployment.

Original papers and supporting information, full text and OCR, page renders,
unreviewed candidates, private audit evidence and repository-preservation bundles
remain in the private research workspace. The public audit inventory identifies
preserved audit artifacts by hash; its entries are not a count of completed papers.

## Evidence and image provenance

Current project preference: at the user's explicit direction, keep the original
source figures selected for the MatterSyn reader available on the public site,
including the preserved source-derived figure assets. This supersedes the earlier
blanket exclusion of source figures from public pages. Pair each displayed figure
with its paper citation, page/figure locator, and the supported record/sample
assignment; preserve the exact source and display asset hashes and any crop or
transformation details. The user's display instruction is a project publication
choice, not a claim that publisher permission or a reuse license was verified.
Keep complete papers and SI, extracted/OCR text, full-page renders, private working
crops, and unrelated source assets in the private research workspace. Keep the
asset register's rights status factual; do not mark an asset cleared solely because
it was selected for display.

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

The public asset register records factual identifiers, provenance and permission
status, with license-evidence links where available. It is a release-control record,
not a blanket legal determination about third-party papers. User selection for
display does not relabel an asset as licensed or permission-cleared; preserve the
recorded status while retaining the selected figures under the current project
preference.

## Build and release

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
source/sample provenance stop delivery. The user's explicit display preference
allows the selected original source figures to remain available while their rights
status is unresolved; the release must preserve that status without describing it
as cleared. Source-coordinate formats retain their original bytes. Narrow hash-bound
exceptions identify upstream COD exporter comments, not local research-workspace
paths.

Both README bibliographies come from the same approved source records. The homepage
fallback and dynamic progress display use the same dated release snapshot. Several
completed contributions may be published together; screening, extraction, audit and
building can proceed on different papers in parallel. Each contribution still needs
its own review history. Throughput is reported from completed work, not inferred from
the number of workers or model calls.

GitHub Pages deploys only the artifact validated by the site workflow. The old
same-directory synchronization command is retired. A failed validation must not be
bypassed by uploading the repository root or switching back to branch publication.

## Historical preservation

Before the publication-history repair, all reachable original commits were preserved
in verified private Git bundles, together with working files, diffs, index state and
hash manifests. The public projection retains the reviewed chronology and commit
graph while excluding private source payloads and uncleared image bytes. Original
to public commit mappings and detailed exclusion reports remain private.

Old working checkouts retain their original evidence and have public pushes disabled.
Do not push their old history back into either public repository. Continue releases
from the cleaned public source and reviewed candidates in the private workspace.
Rewriting the repositories does not erase copies already held by other people or
guarantee removal of externally cached objects.
