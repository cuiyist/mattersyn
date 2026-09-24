# Training-oriented record design

Read when a synthesis atlas is intended to supply machine-learning examples. Apply these scientific distinctions to the requested scope; do not infer that every literature method is training-ready. The original MatterSyn project now implements a pilot canonical-record pipeline; see the project reference for its current files and limits.

## Unit of evidence and presentation

Use one immutable, versioned experiment or recipe-variant record with linked product samples as the underlying scientific entity. A record page is a view of that entity; material and method hubs index multiple records and are not independent training examples. One paper may describe many records. One general method or an unassigned figure does not establish a fully quantified experiment.

For the reader-facing broad synthesis–structure count, one pair is a source-supported recipe instance/condition variant linked to an identified product sample and at least one structural outcome such as phase, morphology, dimensions/distribution, lattice data, or heterostructure architecture. Atomic coordinates are optional for this count. Count a newly produced and separately identified sample when a changed condition changes only its size as a separate pair. Several methods measuring the same sample enrich one pair; repeated papers describing the same physical specimen enrich its evidence; independent runs remain separate observations and stay grouped for evaluation. Keep raw record/sample rows, cross-record deduplicated outcomes, task-eligible examples, and measured-coordinate examples as separate counts. An unresolved sample-to-recipe relation is not a verified pair.

Represent a synthesis batch once, with linked aliquots, fractions, time points and measurements. Task-specific exports may make several examples from it, but these share a parent group and remain together in evaluation splits. Repeated papers, copied methods and synthetic augmentations do not create independent experiments.

Generate the human website and training exports from the same validated structured source. Preserve attractive molecular, apparatus and characterization views as review tools. Do not require separate handcrafted applications for thousands of records or train on decorative page markup by default.

## Information needed for model supervision

- Stable record, source, recipe-family, batch, sample and measurement identifiers; schema version, revision and duplicate relationships.
- Separate intended target from observed product: composition, phase, morphology, dimensions/distribution, surface state and measured properties with explicit unknowns.
- Structure assets carry origin and role: experimentally refined sample structure, phase-matched external reference, computed structure or illustrative particle. An external CIF can encode an independently verified phase but cannot establish that phase or exact atomic structure for the sample.
- Chemical identities use stable identifiers and verified formula/connectivity; distinguish hydrate, oxidation state, ligand form, purity/grade and stock composition when reported.
- Quantities are typed values, units, ranges, approximations and missing statuses, with original text retained. Mark reported, derived, inherited, inferred and unreported fields. Derived concentrations retain inputs and volume assumptions. Unknown is not zero.
- Operations have action types, input/output material or stock IDs, ordering/dependencies and stage-specific conditions. Keep preparation, synthesis, workup, fractionation, optional exchange and characterization preparation distinct. Preserve source-prescribed feedback endpoints rather than inventing a fixed time.
- Measurements link to sample IDs and their recipe/fraction lineage. Include technique, acquisition conditions and source locator. Record the status of each recipe-to-product link; shared nominal size is insufficient to establish it.
- Every important claim has source and page/section/figure locators, extraction/review status and missingness. Retain source and asset reuse metadata for dataset management.

## Training views and inclusion

For inverse planning, a useful proposed input is desired composition/phase/structure plus requested size, morphology or surface properties and relevant lab constraints. The output is one or more candidate structured recipes. Crystal structure alone does not specify a unique colloidal synthesis or desired size. The same target may have multiple valid recipes.

Keep task eligibility separate from overall page completeness. A record may support precursor selection while lacking sufficient information for temperature prediction, exact structure-conditioned planning or recipe-outcome evaluation. Mask unavailable targets; do not fill experimental labels with generated guesses. Partial records remain useful evidence.

Keep reader navigation separate from training admission too. An independently reviewed synthesis route can have `reader_role: synthesis_route` and no eligible training tasks. Require reviewed literature, actual synthesis operations and appropriate record type before showing its method card. A supporting acquisition procedure, contextual observation or numeric benchmark cannot become a route through this flag. Preserve legacy classifications when introducing the field; do not add a machine-learning task merely to make a reviewed method visible.

Chemical intuition and literature context belong in separately labeled knowledge records. Generated explanations are not experimental labels or verified author reasoning. Do not feed result-revealing captions, measured outcomes or recipe-revealing explanations into model inputs when those fields are unavailable for the intended prediction task. Exclude decorative molecular coordinates and particle renders from experimental supervision; their underlying verified chemical identities may still be useful descriptors.

Successful literature recipes alone support imitation/recommendation. Reliable estimates of experimental success need outcomes including failures, partial successes and repetition, with consistent definitions. Unreported or untried recipes are not failures. A reported preparation is not independently reproduced in the collaborating lab.

## Scale and evaluation

A 5,000–50,000-record collection is a plausible basis for a specialized model or adaptation of a pretrained model; the count alone cannot establish sufficiency. Track complete linked examples, distinct chemistry, recipe diversity, source dependence and coverage of the intended task. Start with a diverse curated pilot, measure extraction agreement and evaluate learning curves before maximizing page count.

Compare retrieval/expert precedents, a simple forward outcome model where outcomes exist, and constrained recipe generation. Split by source paper and connected duplicate/recipe/batch families before augmentation. Use chronological, unseen-chemistry or laboratory holdouts when they match the claimed generalization. Evaluate chemical validity, ingredient/operation/condition quality and uncertainty, then use prospective collaborating-lab experiments. Exact agreement with one published recipe is not the only valid endpoint.

## Deferred MatterSyn extensions

The original project's user anticipates an evidence-grounded reader chatbot, crystal-structure tools for DFT workflows, and comparison of experimental papers with theory to inform website revisions. These are deferred directions, not authorization to implement, run calculations, retrieve additional papers or expand recurring curation. Current paper review remains the priority until the user requests an extension.

Maintain stable identifiers, source/sample links, structure provenance and version history during current curation. When later requested, ground chatbot answers in cited curated evidence and preserve gaps; validate any DFT model for its intended calculation rather than treating a viewer asset as simulation-ready; keep theoretical assumptions and comparisons separate from reported experimental evidence. Record evidence-supported interpretation changes transparently without rewriting observations to match theory. Scope the actual feature when requested.

## Original MatterSyn example

The implemented pilot uses `data/records/*.json` as the canonical source. `scripts/build_dataset.py` validates records and generates `dist/records/*.html`, public JSON, a manifest, grouped assignments and task-specific JSONL. Run `python -m unittest discover -s tests -v` and `python scripts/check_site.py` after scientific or schema changes. Edit canonical records and increment their revision for published scientific changes; generated copies are not independent authoring sources. Keep old rich paper guides linked as context rather than treating them as extra training examples.

Use `retained_fraction` as a resolvable material/state ID; distinguish optional inputs and alternative condition sets. Check multi-hop material, measurement and sample cycles, declared stock preparation order and primary source-group references. Matching molecular formulas alone cannot select a conformer because isomers may share a formula; match verified identities or reviewed aliases.

Keep curated literature records and imported published benchmark rows as different collections. A numeric dataset can support an outcome benchmark without supplying complete individual protocols, crystal structures or verified chronology. Preserve its attribution, license, changed fields, row identifiers and source hashes. Failure encodings such as sentinel wavelengths become null continuous targets; keep the original encoding as separately labeled provenance.

Evaluate leakage at the task-view boundary: choose explicitly linked measurements, allowlist input features, exclude standalone final characterization from synthesis output steps, and keep outcome-derived cohort labels out of inputs. An empty manually written missing-fields list must not override typed unknown protocol conditions. Recipe signatures should ignore chemical-inventory order but include stock quantities and condition alternatives. Exact signatures do not replace near-duplicate or chemical-equivalence review.

The current collection is a pilot, not a load-tested 50,000-record service. Freeze source-group manifests for comparisons and add indexed catalog storage/pagination when needed. Report how many records are actually eligible for each task; do not use page count as a claim of independent experiments or model readiness.

In the MatterSyn chemical registry, retain explicit empty bindings for canonical observations that have no material inventory. The binding record-ID set must equal the canonical record-ID set; an empty material list is not a reason to omit its provenance entry. Update stale draft labels through source-specific presentation metadata after audit, preserving the frozen scientific record.

For host-mediated synthesis, carry the intended host explicitly into task inputs when it is source-supported. Schema 1.2.0 provides an optional `intended_target.host`. Precursor-selection exports may carry separately identified host matrices and electrolytes in `process_materials`; do not relabel a salt used for ionic-strength control as an elemental product precursor merely to satisfy an allowlist. Verify the actual exported JSONL after changing roles or schemas. Regional observations, author-model potentials, inferred diffusivities and qualitative electrolyte comparisons remain contextual records unless a specific supervised task has defensible sample linkage and labels.

The Murray 1993 Method 1 page is a useful partial precursor/protocol record. Its study-wide figures are not all mapped to exact recipe instances. Method 2 lacks several independently quantified inputs. The current COD CIF is an external 1977 bulk reference; the 582-atom particle is a geometric illustration. Do not convert either page into a verified exact experimental-CIF-to-complete-recipe pair merely because these assets appear together.

Primary precedents checked September 16, 2026:

- Wang et al., Scientific Data (2022), DOI 10.1038/s41597-022-01317-2: 35,675 structured solution-synthesis procedures. https://www.nature.com/articles/s41597-022-01317-2
- Gu et al., ACS Nano (2025), DOI 10.1021/acsnano.5c09134: 3,508 colloidal recipes covering 348 compositions; recipe-to-size/shape prediction. This is forward prediction, not evidence of general exact-structure-to-complete-recipe planning. https://pubs.acs.org/doi/10.1021/acsnano.5c09134

## Preserve experimental variants and cross-paper evidence

Create a distinct immutable recipe-variant / experiment record for every source-reported change in precursor identity or quantity, stock concentration, sequence, temperature, duration, solvent, atmosphere or other controlled input when it corresponds to a distinct experimental run or reported sample. Link variants to a shared parent recipe family and material hub, but keep each input set, sample, measured product/structure/property outcome and paper locator separate. Never infer a continuous response curve from a sparse condition series or merge distinct measurements because the product formula is the same.

Several papers may contribute to the reader's material or method view. Store each paper as independent source evidence and link it to the specific route, sample or claim it supports. A paper that reports synthesis but no matching atomic model can corroborate the route without supplying coordinates; a structural paper may contribute an external/refined structure only when the sample and phase relationship are supported. Do not fuse complementary details across papers into a synthetic “complete experiment” unless the source chain explicitly establishes that they refer to the same preparation and specimen. Keep source-specific disagreements and missing links visible.

For training exports, one record is one experimentally distinct recipe-to-observation example, not one website or paper. Preserve recipe-family, source-paper, batch, sample and variant group IDs so related variants and cross-paper duplicates stay together in evaluation splits. A pass-screened document is only a candidate, not an audited data point; no record becomes eligible until its preparation, specimen, target structure/property and source linkage pass the required independent review.
