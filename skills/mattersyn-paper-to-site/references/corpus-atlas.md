# Material atlas and corpus review

For MatterSyn's large local library, organize discovery as **periodic table → material hub → material-filtered synthesis dataset**. Keep a searchable source library as a parallel entrypoint. Give methods from different papers equal card prominence; add CdSe-containing core/shell and hybrid methods with distinct architecture and component labels.

Global navigation is **Periodic table · Source library · Synthesis dataset**. Do not promote CdSe or another individual material into the global navigation. Material names belong in their own page titles, contextual navigation and breadcrumbs.

Current MatterSyn preference (September 19): first screen the local corpus, then prioritize papers rich in synthesis and crystal-structure evidence, retaining batches of up to five independently reviewed papers and separate audits. This supersedes the older one-paper-at-a-time and oldest-arrival selection rules. Preserve the current batch's work and use arrival order to break priority ties. Respect actual worker capacity; five claimed papers does not mean five simultaneous workers. Only the Site owner integrates and publishes; several individually passed papers may share a deployment. Preserve each paper's separate completion evidence. Automated ranking is provisional selection evidence, not a verified recipe, sample join or completed source review.

## Preserve status and identity

- Inventory, text extraction, bibliographic matching, selected-protocol review, full-paper coverage and task eligibility are separate states. A title formula is a discovery candidate, not a verified synthesis contribution.
- One reviewed recipe does not establish that all methods or figures in its paper have been curated. A reviewed contribution for one material does not give every material mentioned by that paper a reviewed label.
- A core/shell recipe can appear on both component hubs but retains one canonical record and experiment identity. Show the actual product composition beside its measurements.
- Hash source documents, retain extraction failures and ambiguous main/SI matches, inspect actual file signatures, and preserve private text/page caches. A DOCX suffix can conceal XLSX or ZIP source-data payloads. Do not execute archive contents. Do not publish private full-text caches.
- Formula candidates need conservative acronym filtering: NCs, NPs and QDs often describe particles, not nitrogen/caesium or other elements. Preserve variable-composition uncertainty and never fabricate a precise formula from truncated notation.
- Keep selected figure images and paper-level evidence separate from supervised recipe labels unless sample-to-recipe linkage has been reviewed.

## Characterization display

Render both product phase/morphology facts and dimensional measurements. Use controlled property categories: optical `wavelength` is not structural `length`. Preserve status, qualifier, basis, sample label, conflicts and source locator in summaries. Show all contributions through pagination or explicit links/counts; avoid silent truncation.

Murray 1993 reports SAED qualitatively but displays no SAED pattern in the inspected main article; matching SI remains unverified. Peng 2000 Figure 2 is powder XRD, not SAED. Nakonechnyi 2017 SI Figure S2 (PDF p.3, printed S3) contains actual patterns: (a) wz-CdSe/CdS, (b) zb-CdSe/CdS, (c) wz-CdSe/ZnSe, (d) zb-CdSe/ZnSe. These are core/shell products, not the selected bare-core sample. Overall phase evidence does not establish measured atomic coordinates or exact batch identity.

## Local implementation

Current MatterSyn pipeline and private caches: `research-assets/corpus-20260917/build_corpus.py`, `README.md`, and `private/` under the project. Use its current manifest for counts, and reuse caches when only metadata heuristics change.

Site builders: `scripts/build_dataset.py`, `build_reader_views.py`, `build_evidence_views.py`, `build_atlas.py`. Authored public source snapshot: `data/corpus/library-source.json`. Only the canonical records feed gated training exports. Validate with existing dataset tests, `check_site.py` and `check_atlas.py`; check changed navigation and figure controls in preview.

## Reviewed-page publication gate and shared quality standard

Leave a material blank if no synthesis recipe has been verified, and review the existing local corpus without downloading new papers. The user now permits skipping no-recipe papers to save time: inspect the relevant supplied main/SI content and independently check the exclusion, record its source hashes, scope, locators and reason, then omit full recipe/website preparation. A partial recipe is not automatically a no-recipe paper. Unavailable or ambiguous SI remains a gap and later evidence reopens the decision. Keep skipped sources in the private disposition index, separate from fully curated sources. Keep the periodic-table element available, but do not populate a synthesis page from title formulas, characterization-only studies, benchmark rows, upstream preparation alone, or irrelevant composites. An empty reviewed set means not yet verified, not proof that no synthesis paper exists.

Every material page requires at least one source-reviewed non-procedure synthesis route with an actual precursor inventory and synthesis operations. Its source list includes only papers supporting those material-specific routes. Component hubs can share a canonical heterostructure route, clearly labeled with its whole product and specimen identities; pure-material claims cannot inherit shell/composite measurements.

Use CdSe as the common reader standard: complete scoped chemical/stock cards, validated chemical depictions, stage-specific illustrated operations with source conditions, measured structural/property evidence, crystal-reference controls/downloads when available, and referenced chemical intuition. Generate all views from canonical data. Ionic salts, hydrates, unresolved mixtures and coordination complexes need honest component/formula views if a valid molecule model is unavailable. Stage drawings must not imply unreported reflux equipment, vessel closure, bath medium, atmosphere or pressure. Original source crops retain readable labels, axes, panels and explicit specimen associations; audit regenerated crop hashes.

Use reference crystals only where a reviewed phase supports the comparison. Keep external lattice parameters and mixed occupancy unchanged and label them independent bulk references; do not refit them into purported experimental particle coordinates. Reference views never create exact-structure training targets.

For this MatterSyn project, search existing local files and metadata only. Missing sources remain explicit gaps; do not search or download outside papers under the current instruction. The following retrieval notes apply only if the user later reauthorizes downloads: Open-Papertrail's generic one-DOI CLI can target a dedicated research output folder. Inspect its current entrypoint before use; its fetch_si --limit 1 does not select a DOI. Avoid broad queue runs for one missing paper. Use ordinary authorized access and retain source hashes/status; if login is needed, use the normal login flow rather than inspecting credential/session contents. Verify every supplement by its content, not download success, and do not equate one acquired SI with all supplements. Record inaccessible sources and continue unrelated review.

## Inventory before page population

The user wants the existing corpus summarized before filling material pages. Maintain per-paper and per-material inventories alongside the websites. Distinguish document files, provisional paper groups, verified direct product systems, component-only hubs, synthesis routes/condition variants, contextual controls, supporting procedures and published benchmark rows. Shared component contributions retain one record identity and cannot inflate recipe counts. Full-corpus material and recipe totals stay unknown until content review establishes them; never estimate them from title tokens or mark an unreviewed paper as containing zero recipes. Show reviewed-subset counts, review scope and remaining unknown totals clearly. Reconcile the inventory ledger with canonical records and page publication gates on every scientific-data release.
