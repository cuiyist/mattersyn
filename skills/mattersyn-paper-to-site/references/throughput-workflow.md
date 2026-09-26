# Reusable paper-to-website workflow

Use this workflow for the existing screened-pass MatterSyn collection. The user requires 20 published papers/hour while retaining the scientific and Reader standard and forbids paid processing. This is a target, not demonstrated capacity. New arrivals remain outside the active screened set.

## Work allocation

Keep at most four workers including the integration owner and five claimed papers. Normally use two paper authors, one independent auditor, and the integration owner. Reassign completed authors to audit another author's paper when that prevents an idle slot. Only the integration owner edits shared repositories and publishes. Use the existing local text/render caches; do not repeat unchanged complete reading or passed source checks.

Each author produces the canonical records and the Reader additions together, using current schema and shared components. A paper package contains all scoped variants and sample contexts, document coverage, evidence locators, figure assignments/crops, reagent and stock bindings, and unresolved information. Do not create a separate demo website or a new apparatus module when existing components express the operation. Reuse molecular identities; process states are not extra reagents. Keep sample context and source-specific conditions outside reusable molecular geometry.

Match the current Reader consumer contract before freezing a package. Reuse actual molecular or ionic structure assets for identifiable precursors; formula-only text cards do not satisfy the complete Reader standard for known molecules. Keep stereochemistry or mixture composition unspecified when the source does, without discarding known connectivity. Unknown solids, resins and sample contexts require clearly labeled appropriate depictions. Figure cards read `title`, `summary`, `scope_label`, `source_locator` and `source_id`; preserve richer source fields and derive compatible aliases from the same audited figure. For an operation that needs an authored apparatus illustration, `protocol_art` binds an exact record and operation to a registered asset path/hash, caption and source locator. This binding changes only the illustration: conditions still come from the canonical operation. Never copy one operation's temperature, pressure or duration into another stage to reuse its picture.

Put new public figure and coordinate assets under `recipe-atlas/static/assets/` in the source checkout; their website paths begin with `assets/`. The release builder does not copy `recipe-atlas/assets/`. Check both paths before freezing a package. A delivery-path correction should preserve the accepted scientific bytes and use a bounded compatibility audit rather than repeat source extraction.

## One accepted record version

1. Author prepares one complete package in the current shared format. Review metadata remains provisional until the independent source audit accepts it.
2. The independent auditor checks the source, numbers, omissions, variants, sample/figure links and illustrations. Return one consolidated correction list, preserving the original audit and bounded amendments.
3. Set accepted review metadata once, then generate all dependent hashes from those final record bytes. Freeze the package with its separate source-audit receipt. Never relabel a schema pass as a scientific audit.
   Bind scientific audits to the paper's immutable records, assets and presentation additions. The final release binds complete aggregate files. A change to another paper's hub counts or a generated hub digest must not trigger a new scientific review of unchanged paper content; verify the scoped postimage and deterministic merge instead.
4. Merge additive deltas into an isolated candidate. Run `tools/package-importer/preflight.py` before a full build. It checks required collection/status, record schema, old-record preservation, Reader source hashes, actual route membership, separate reagent/state namespaces, review scope/page coverage, and both list- and object-shaped characterization links. A passing check is not publication approval.
5. The integration owner runs the existing full build, eligibility comparison, asset/boundary checks and browser QA once per ready batch. Reuse unchanged passed evidence; independently recheck changed scientific claims or sample/figure assignments only. Deterministic metadata/hash corrections need compatibility verification rather than another full-paper read.
6. Publish ready contributions together without waiting for a blocked paper or a new feature. Preserve its unresolved work in the exception queue. Credit each source only after deployment and anonymous verification; variants are records, not extra papers.

Do not make a paper appear complete by omitting difficult information. An exception queue preserves work and prevents it from blocking other ready papers; it does not waive completeness or presentation requirements. Original figures retain exact attribution/provenance and the existing rights status. PDFs/SI, raw extraction, renders and detailed audits stay local.

## Measure the bottleneck

Record source drafting, independent audit, integration, rework, validation, deployment and waiting separately. Report end-to-end distinct published sources per elapsed hour, with inherited work and interruptions identified. Do not claim continuous operation between task runs. Build seconds, records/hour and a successful preflight are not papers/hour.

At four workers, 20 papers/hour allows 12 combined worker-minutes per paper. An illustrative balanced allocation is two authors averaging 6 minutes/paper each, one auditor averaging 3 minutes/paper, and an integration lane averaging 3 minutes/paper. These are capacity thresholds, not instructions to stop reading at a time limit. If any required stage exceeds its budget, the target is unproven; record the gap and improve the limiting stage. Do not lower quality or start paid processing to make the arithmetic fit.

The initial reusable preflight was tested on the 13-record Ghezelbash candidate and all 865 prior canonical records in 5.326 seconds. Ten regression tests cover observed handoff failures. These measurements establish compatibility-check performance only; the 20-paper/hour publication rate remains unachieved.

Use `tools/package-importer/merger.py` for compatible additive packages instead of a new merge implementation per paper. Supply immutable create-only files and a manifest of additions to pinned JSON bases. Existing keys and conflicting list identities must never be overwritten. Let the merger produce a private overlay; root applies it with exact base checks and then runs preflight. Do not auto-merge conflicting rights/provenance claims. A real four-record package produced 16 unchanged overlay outputs in 0.607 seconds, and the combined 17-record candidate preflight passed in 1.952 seconds. These are mechanical checks, not completed-paper throughput.


The September26 reporting instruction requests a progress and publication-rate check every two hours. Preserve the fixed twelve-hour experiment separately and use actual report timestamps for each shorter interval. Count only anonymous-verified deployment events; record zero changes honestly. User-reported model selection is not evidence of a measured speedup.
