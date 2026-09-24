# MatterSyn publication workflow

MatterSyn uses a private project repository and a public website repository.
`cuiyist/mattersyn` is private and holds project tooling, reviewed records, memory,
skills, audit summaries and the cleaned project Git history. Complete sources,
raw extraction caches, unreviewed candidates, detailed private audits and original
history bundles remain in the local research workspace, outside both repositories.
`cuiyist/mattersyn-site` remains public and contains only the deployable website,
the reviewed data and citations needed by readers, selected source figures, and
site-specific deployment controls. Keep full papers and SI, raw text/OCR, source
page renders, private working crops, unredacted audit evidence, machine paths and
private project history out of the public site repository. The site may expose only
concise reader-facing provenance and progress needed to use it.

## Evidence and image provenance

At the user's explicit direction, selected original source figures remain available
on the public reader. The 2026-09-24 restoration checkpoint covers 743 figures; see
`research-assets/public-audits/source-figure-restoration-20260924.json` in the
private project repository. This display instruction is not a claim that publisher
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
current collection contains 37 formal paper-review files; their structured text
retains claim types, sample scope and source locators. Assess wording against the
source before shortening a passage; do not truncate scientific content by length.

The user's display preference permits the selected source figures to remain on
the public site while their rights status is unresolved. Preserve that status; do
not describe the figures as cleared.

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

Verified private Git bundles and working-file manifests preserve the original
project history and evidence. The MatterSyn source repository is private; the public
site repository receives only the approved deployable site and its required reader
data. The site's commit history is not a substitute for the private project history
or detailed audit trail.

A follow-up review confirmed that removed content had remained retrievable through
old public GitHub commit IDs. The user has directed the project repository to be
private, and the reviewed old source URL returned 404 anonymously afterward. This
limits anonymous access but does not prove old objects, caches or copies have been
erased. GitHub Support may or may not remove retained objects; no purge is
guaranteed. No further history rewrite is planned, and no support request is to be
submitted without separate explicit user authorization. The public website remains
public.
