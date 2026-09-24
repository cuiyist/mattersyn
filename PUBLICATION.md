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

Each recipe retains its source, sample assignment, measured conditions, reported
outcomes and review status. Contradictory observations remain separately attributed.
Publication does not imply eligibility for every model-training task. In particular,
a named material or a reference unit cell is not a verified sample-coordinate pair.

An image needs an exact path, content hash, origin classification and a recorded
redistribution basis before it can be delivered. Authored molecular structures and
apparatus illustrations remain distinct from measured images. Where source-image
clearance is pending, the public page retains its factual explanation, sample and
figure locators, and a link to the cited publication. An authored source-link card
is explicitly labeled as such; it is not presented as TEM, SAED, XRD or a spectrum.
Original crops and their source hashes remain available in the private evidence
archive. Display hashes identify the separately generated public cards.

The public asset register contains factual identifiers and license-evidence links.
It is a publication control, not a blanket legal determination about third-party
papers. Future clearance is recorded for the exact asset before restoring delivery.

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
machine paths, unmatched image hashes and unresolved image rights stop delivery.
Source-coordinate formats retain their original bytes. Narrow hash-bound exceptions
identify upstream COD exporter comments, not local research-workspace paths.

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
