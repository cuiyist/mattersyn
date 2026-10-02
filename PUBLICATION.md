# MatterSyn publication workflow

## Current verified site — Henkel and Xu, 2026-10-02

Henkel et al. (2009) and Xu et al. (2008) are live on ordinary material pages. Source commit `ca84c096789204b04f9edb1d4bfb080236402b9b` and site commit `6c62e25fe766906bb1a42255152a3764efba723d` passed source CI, exact-preview browser review, Pages deployment, and anonymous verification at 2026-10-02T15:10:47Z. The release checked 40 public files, both new paper routes, and all 17 affected paper/material route combinations without mismatches. This adds **2 distinct literature papers and 33 canonical records**. The verified inventory has **173 contributing source groups in total (172 literature and 1 benchmark source group), 1,703 records, 178 directly synthesized material systems, and 699 broad recipe–structure rows**. Multiple records from Xu count as one source paper. Source figures have exact provenance and unverified publisher display permission. The Xu morphology illustrations were corrected against the displayed source figures before release.

The workflow-v5 deep-audit stop rule is active: 7 of 9 distinct logged sampled papers had at least one error. New extraction is paused; unpublished packages with open findings remain local. The quick-audit checklist is strengthened and requires independent calibration before renewed intake. This is a quality-control hold, not a claim that 7/9 is the corpus-wide error rate. The requested 20-paper/hour publication rate has not been demonstrated.

## Earlier verified site — Naiki, Liu and Jung, 2026-10-02

Naiki et al. (2013), Liu et al. (2008) and Jung et al. (2024) are anonymously verified on their ordinary material pages. Source `76138c61f8bee7fa83f9de45a078ca7652bf3326` and site `5388d79248a03c09708246a837410e144296d9b5` passed source CI, exact-preview browser review, Pages deployment and anonymous checks at 2026-10-02T07:55:03Z. The verified homepage counts **167 distinct contributing papers and 1,666 canonical records**. The private workflow-v5 ledger has three new `live_verified` events and the exact release receipt is `_tmp/v5-naiki-liu-jung-final/live-verification.json`. Source figures retain factual unverified publisher-permission status. Yao, Routzahn, Ko and Chan remain private candidates with no publication credit. The 20-paper/hour target is still not demonstrated.

## Prior verified site and now-completed candidate — 2026-10-02

Saikia et al. (2022), DOI 10.1039/d1nj04039a, is live at source `31084e3f6ba7d55fe1c4ee97405247a503b89bc1`, site `9944edaaee1f1c2dec2d749b0ff06547e79d825d`. Anonymous verification at 2026-10-02T05:07:48Z brings the site to **164 contributing papers and 1,663 records**. Naiki et al. (2013), Liu et al. (2008) and Jung et al. (2024) are a separate three-paper source candidate with independently accepted scoped science, figure/sample bindings and source/site asset-delivery metadata. They are not counted as published until the exact source, build, browser, Pages and anonymous live gates pass. Original papers and SI remain local; selected source figures retain exact provenance and unverified publisher display permission.

## Current verified site — 2026-10-02

Munechika et al. (2011), DOI 10.1021/nl2010127, is anonymously verified on the ordinary CdSe/CdS/ZnS–Ag material page. Source `75926b047e1960b94a7850c6e05ab237792afb6b` and site `d7aaa24ccdb381908c349ec2441ae5116b2dd3ed` passed CI, exact browser review, Pages deployment and anonymous route/file checks. The verified homepage counts **163 distinct source papers, 1,662 records and 628 broad pairs**. The private workflow-v5 ledger and `_tmp/mr1/release-summary.json` pin the live proof. Scope is preformed QD/Ag-nanoprism assembly with named observations; upstream QD syntheses remain unclaimed. Selected source figures retain unverified publisher-permission status. Saikia et al. (2022) is an independently accepted private candidate, with no publication credit until its own site deployment and anonymous verification pass. The 20-paper/hour target is not demonstrated.

## Most recent verified site and current v5 queue

Lin et al. (2021), Klecha et al. (2009) and Yuan et al. (2026) are live on ordinary material pages. Source `7ed952e484b6d196436ef3f7a31a42a30cc0ebca` and site `3fc2901baf978eba5714468a754df660f5ab2d78` passed source CI, exact browser review, Pages deployment and anonymous verification at 2026-10-02T01:12:26Z. The verified site contains **159 distinct contributing papers, 1,658 canonical records, 162 material families and 577 broad recipe–structure pairs**. The release helper checked forty public files, all three new paper routes and both affected material hubs without mismatches. Selected source figures retain exact provenance; publisher display permission is unverified.

Klecha et al. (2010), Choi et al. (1999) and Ouhenia-Ouadahi et al. (2016) have accepted scoped science in private preparation. They remain unpublished until the full release gates pass; status-only corrections require exact independent delta receipts. Munechika et al. (2011) is still under scientific correction. The 20-papers/hour target is not demonstrated.

## Latest verified site and current source candidate — 2026-10-01

The most recent anonymously verified site release is source commit `645d5158900153165d330eaf55ab7ec4fffb47a7` and site commit `bcf9b029`. It integrated Bhattacharya et al. (2023) and Fafarman et al. (2014) into ordinary material pages. The live counter is **153 distinct contributing papers**, **1,640 canonical records** and **555 broad recipe–structure pairs** at this checkpoint. The private v5 ledger records anonymous live verification by 2026-10-01T19:27:21Z. Selected source figures retain exact provenance and unverified publisher-permission status.

The next candidate is the scoped Fanfair and Korgel (2005) Bi nanocrystal seed route. Its main pages 1–3 and Figure 1 are independently accepted; pages 4–6 concern downstream nanowires and are excluded. The candidate remains unpublished until its source/build, exact browser, Pages and anonymous live gates pass. A source paper can contribute several variants, but it counts once on the homepage.

For a selected-page v5 contribution, the release gate verifies the exact source-linked record page, record data and public scoped inventory entry instead of inventing a complete-paper Reader. The material-page route and shard remain separately checked. A full-paper Reader, when present, remains the primary paper route. The scoped fallback requires a published source DOI, exact record membership, explicitly incomplete main-page coverage and the accepted independent-audit status.

## Current instruction: workflow v5, regular material pages only

Follow [workflow v5](skills/mattersyn-paper-to-site/references/workflow-v5.md) and its [agent runbook](skills/mattersyn-paper-to-site/references/agent-runbook.md). The owner retired the public preliminary collection and set a target of about twenty newly published contributing papers per hour. This is a target, not demonstrated capacity. Skips and private drafts never increase the website counter. Every paper receives an independent quick audit, and the selected 10% receives a deep audit. Existing scientific, sample/figure, privacy, browser and release checks remain in force. Historical v4 directions do not govern new work.

## Retired preliminary display

The experimental preliminary-synthesis display was retired by the owner. Do not
publish its page, raw JSON or homepage link. Keep historical extraction and review
receipts private to the research workspace; they are not reviewed website
contributions and add no paper or pair credit. The former v3 publication allowance
is superseded. Only sufficiently supported, reviewed contributions belong in the
regular material pages.

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

## Earlier verified deployment — Zhang et al. (2011)

The Zhang et al. (2011) Cu–Zn–In–S release was anonymously verified at
2026-09-30T22:48:38Z (site commit `258896d5b7103712aa859f23dc9d363ca2a67590`).
The public site reports 137 primary source groups, 1,564 records, 132 material
families and 488 broad recipe–structure rows. This includes one published
benchmark source group; the reviewed-literature inventory has 136 groups.
Its local proof is `research-assets/workflow-v4-20260930/zhang-publication-proof.private.json`.
This historical checkpoint predates the verified v5 releases described above.

## Earlier verified deployment

GitHub Pages run #73 (`26df1afe5f16124de95cadfc0d362480d606647d`) was anonymously verified on 2026-09-30. It adds two distinct papers (Kudryavtseva 1997 SnO2 and Venkatesan 2003 Fe3O4), 10 records and 5 broad recipe–structure rows. The live totals are 136 papers, 1,564 records, 132 material families and 480 broad rows. Site CI build-and-validate and deploy both succeeded; each new material route resolved publicly. The preliminary collection is absent from the homepage navigation. The measured interval since run #72 was about 7h08m for two papers (0.28/hour), so the 20-paper/hour target remains unmet. Run #73 took 5m34s for CI and deployment, excluding curation and waiting time.

## Historical verified deployment — batch24

Batch24 (`2200f0269ab98cf743e677bd4b1c7df1e2f23df3`) was anonymously verified at 2026-09-29 23:08:15 UTC: six new papers, 58 records and 21 broad pairs; cumulative site totals are 131 papers, 1,530 records, 128 material families and 464 broad pairs. The measured 6h15m26s release interval equals 0.96 distinct papers/hour including idle time. The 20-paper/hour target remains unmet. The 400-decision cutoff was missed: the private 18:00 Chicago checkpoint was 45/400, and deployment followed at 18:08:15. See `research-assets/workflow-v4-20260929/batch24-release/public-verification.private.json` for the local proof; source PDFs, private receipts and audit evidence remain local.

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

**Workflow-v5 release sequence:** `tools/publication/release_batch.py` prepares an
isolated, gated site preview from a pushed, CI-passed source commit. It builds a
candidate, derives the site allowlist, and requires the final gated build to
match the candidate byte for byte. Review the exact preview in a browser and
record the pinned review receipt before rerunning the helper with the same work
path, `--review-receipt`, `--push`, `--verify` and a private ledger. It rechecks
the reviewed bytes, waits for the Pages deployment and verifies new paper routes
and backing data anonymously. A later `--verify` run with the same work path
rechecks an already pushed release without adding duplicate ledger credit. This
sequence has been exercised in the verified v5 releases above. The [agent runbook](skills/mattersyn-paper-to-site/references/agent-runbook.md)
contains the exact commands. `tools/publication/make_review_receipt.py` records
the staged source changes for `prepare_source_release.py`.

Workflow v5 also permits a **truthfully scoped main-text contribution** when its
accepted package, exact quotes, source-linked samples and figures, independent
quick audit and sampled deep audit cover the stated method. The public inventory
must identify the pages reviewed and excluded. A partial six-page read cannot
be represented as a complete six-page paper review, and no formal full-paper
Reader is generated from that claim. The private scoped-acceptance receipt binds
the accepted package, audit and any later status-only promotion to the exact
canonical bytes before additive preflight. This changes the publication unit,
not the sample-linkage, rights, browser or live-verification gates.

Source and site pushes are separate steps. After the reviewed source commit
passes the existing local source-boundary and complete-build checks, push that
exact clean commit to `cuiyist/mattersyn`. This starts validation-only source CI;
it does not deploy the website. The exact source-head CI result necessarily
follows that source push and must pass before site promotion. Keep the candidate
unapproved until the existing science, browser, source-export and exact-head CI
requirements are satisfied; then promote the identical artifact through the
fresh public boundary and push the approved site commit. Site CI and anonymous
verification still precede publication credit. This clarifies the existing
sequence without adding a gate or approval.

The September 26 scaling workflow uses a single source commit with generated,
content-bound controls. Follow [the single-commit guide](tools/publication/SINGLE_COMMIT_RELEASE.md): stage reviewed payloads, prepare the blueprint and manifest together, then bind the committed manifest to clean HEAD outside the repository before export. CI uses that runtime allowlist. This removes the follow-up closure commit without removing exact public-file review or scientific evidence checks.

Calibrated silver contributions require frozen-pipeline calibration and independent
calibration approval. Experimental preliminary display is not authorized. Each gold
paper needs an independent v5 quick audit, and a deep audit when selected by the
frozen scientific hash. Figures and authored visuals travel with the paper package;
any unavailable or uncertain visual evidence must be labelled honestly. The source
and site releases remain separate, with the exact review and live-verification gates
described above.

Inventory totals and memberships are generated during the build from canonical
records, source review metadata and atlas indexes. The authored
`recipe-atlas/data/inventory-evidence.json` preserves scientific review scope and
notes; it is not a place to hand-update totals. Source scope, DOI, page counts,
record assignments and component relationships must reconcile before rendering.
No scientific record or training eligibility is changed by this migration.

The calibrated silver Reader remains hidden until its existing admission gates
pass. Historical experimental evidence remains private and is not included in site
builds, reviewed counts or training exports. Candidate/monitoring projections keep
`publication_enabled:false` and cannot authorize deployment. Actual source credit
requires a successful controlled release and anonymous verification.
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

## Verified v5 colloidal release — 2026-10-01

The Huang 2015 CdSe/9-ACA, Slejko 2017 CdSe shell-growth and Dierick 2014 CuInS2 batch passed exact source CI and artifact comparison at `58468006403db75580acd35cdff9902241e0920f`. The release helper prepared an isolated site preview, matched candidate and final builds, checked all 14 required routes in a browser, and deployed site commit `aa9a318fedbb7703017b7e6e12ebe943c240a47e`. Anonymous verification passed for 40 sampled files, all three new paper routes and all affected material routes. This credits three distinct papers and 20 canonical records, making 145 live contributing papers and 1,602 records. The private browser receipt, release plan and live ledger remain local; complete source PDFs, text, renders and detailed audit evidence were not deployed. Source-figure publisher permission is still unverified. This is a measured release, not evidence of the 20-papers/hour target.

The current v5 `release_batch.py` deliberately runs both candidate and final full builds and compares their tree hashes. This supersedes the historical one-build intention above for releases using that helper; do not treat an earlier passing build as permission to skip v5's exact-preview gates.

## Verified Urban and Sahoo release — 2026-10-01

Urban et al. (2007, DOI 10.1038/nmat1826) and Sahoo and Arora (2010, DOI 10.1021/jp912103t) were published from source commit `897251a3f677cfec9b0fcfece229b8abf40b86ef` to site commit `65732a1155d10df325ba6da7e524400738816921`. The two independently audited sources add seven canonical records and seven broad recipe–structure pairs. Source CI and cross-platform artifact comparison, the exact staged browser review, the public-boundary check, Pages deployment and anonymous verification of forty files plus every new source and affected material route passed. The live totals at that release are 156 contributing papers, 1,648 records and 563 broad pairs. The official private release plan, browser receipt, summary and deduplicating live ledger are under `research-assets/workflow-v5/stages/urban-20261001/official-release-r2` and `research-assets/workflow-v5/ledger.jsonl`.

The selected source figures are displayed under the owner's earlier direction with exact provenance; publisher permission remains unverified. Urban's binary assembly labels are mesoscale, and Sahoo's 4 nm Scherrer estimate is not a TEM diameter. The active [workflow v5](skills/mattersyn-paper-to-site/references/workflow-v5.md) still governs the next batch. A privately staged package, build or passed preflight does not increase public paper counts until the exact new release is anonymously verified.

## Verified Ag-assembly release — 2026-10-02

Choi (1999), Klecha (2010), and Ouhenia-Ouadahi (2016) were published from source commit `ae1d98ae9e22648422a15c0e14b55300dcfbedf6` to site commit `c0b70cdeff6a7618f6f38dc5d710a886f3c3ac60`. Separate accepted paper packages and independent audits were retained. The source CI jobs, exact staged browser review, full site boundary and Pages deployment passed; anonymous verification passed for 40 sampled files, all three new paper routes and every affected material route. The release helper appended three deduplicated `live_verified` events to the private ledger. This adds three distinct source papers and three canonical records; the current live atlas shows 162 contributing papers, 1,661 records and 622 broad recipe–structure pairs. The selected source figures retain attribution and an explicit unverified publisher-permission status.
