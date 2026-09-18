# MatterSyn training data pilot

The canonical files in `records/` are the source for generated record pages and task-specific exports. Edit a canonical JSON record, increment its revision when changing published scientific content, then regenerate. Never edit `dist/data/records` or `dist/records` by hand. Dataset version 0.4.0 uses record schema 1.0.0.

## Current collection

- 41 source-reviewed literature protocols, variants and controls, plus 14 separately scoped supporting procedures. These are not 55 independent experiments.
- A separate, attributed 100-row coverage subset of the published Voznyy 2019 PbS dataset: 95 optical-outcome rows and five failure-coded rows. These are experimental rows, not 100 reviewed complete SOPs or 100 independent papers.
- Five fully inventoried main–SI sets cover 74 pages: ZnO, CdSe/core–shell, Ir, Fe–O and CoO/CoFe2O4. Their review ledgers expose original graphics, tables, equations, sample links and unresolved claims. Most of the 4,176 local paper groups still await full curation. Screening alone does not create a training example; source-reviewed recipes do not imply whole-paper review.
- Zero verified sample-resolved exact-CIF-to-complete-recipe pairs. The existing bulk CdSe CIF and finite particle illustration cannot supply those labels.

## Scientific entities and review

One record represents a coherent protocol, variant, procedure, experiment or observation. Paper, recipe-family, parent, batch, sample and measurement identities are separate. A source-row ID is not an author-assigned physical batch ID. Intended targets remain distinct from observed products.

Every reported or derived quantity carries evidence, units, status and basis; missing values are null rather than zero. Retain reported ranges, uncertainties and conflicting source statements. State whether a product is explicitly linked to this recipe, only general context, or unresolved. Author-derived sizes remain labeled. Diameter, particle size, optical wavelength and geometric model size are different fields.

Use the original paper and verified SI. Record page/section/figure locators; do not assign a nearby figure to a protocol without evidence. Inspect extraction and sample links independently before setting `source_reviewed`. The pilot has source audits, not a measured inter-annotator agreement study or laboratory reproduction. Murray 1993 SI remains unlocated/unverified.

`retained_fraction` is a resolvable material/stock/state ID. Optional inputs use `optional_inputs`; alternatives use `condition_options`. Shared workups are standalone procedure records. Do not inherit missing conditions from another method without labeled evidence. References and illustrations have explicit structure roles and never become measured structure labels automatically.

## Rebuild and validation

Use Python 3.12+ with `pip install -r requirements-data.txt` in your own environment, then from the project root:

```text
python scripts/build_dataset.py
python scripts/build_paper_reviews.py
python -m unittest discover -s tests -v
python scripts/check_site.py
```

The current workspace also supports its ignored `.sites-runtime/python-packages` dependency directory. The generator validates schema, source and material references, operation order, material-state/sample/measurement cycles, quantity status and evidence, product links and structure roles. It fails on stale generated pages rather than silently retaining removed records.

Generated outputs include individual HTML and JSON, `records.jsonl`, a schema, manifest, validation report and six gated task exports. Precursor selection, partial protocol and diameter-conditioned supervision are available for subsets of the reviewed literature. Standalone characterization operations are excluded from synthesis output steps. Exact-structure and success-prediction exports are intentionally empty. PbS optical regression has its own nine-feature allowlist; measurement values, failure codes and derived cohort labels are not model inputs.

Source/recipe/parent/batch/duplicate connected components remain together. Exact normalized recipe signatures cover unordered chemical inventories, stocks, alternatives and ordered operations. They are conservative duplicate checks, not a complete chemical-equivalence algorithm: synonymous identities, equivalent unit conversions and near duplicates still need curation. All catalog exports are development-only while there are fewer than ten groups. At ten or more groups a deterministic group hash assigns 80/10/10 bins; review coverage before claiming a usable split. Freeze a versioned manifest before model comparisons because merging new duplicate evidence can change a connected component.

## PbS benchmark and reproducibility

Source: Voznyy et al., *Machine Learning Accelerates Discovery of Optimal Colloidal Quantum Dot Synthesis* (2019), paper DOI 10.1021/acsnano.9b03864, dataset DOI 10.1021/acsnano.9b03864.s002. The adapted data are **CC BY-NC 4.0**; attribution, changes and the noncommercial restriction remain in records/exports. Other article/figure rights remain separate.

The local baseline uses the full 2,552 published rows, not the 100-row coverage subset. Twenty-three failure placeholders have null continuous targets and are excluded, leaving 2,529 regression rows. Mean, ridge and distance-weighted kNN use nine inputs. Eight physical recipe columns define groups, excluding the seasonal outdoor-temperature proxy; repeated physical recipes stay together. Train-only grouped cross-validation chooses hyperparameters and scaling. Author-cohort transfer uses the published lead-stock-volume rule, not assumed chronology.

Absorption-wavelength MAE: held-out physical recipe groups 303.93 / 140.44 / 70.61 nm (mean/ridge/kNN); author-cohort transfer 296.47 / 250.20 / 191.23 nm. These estimates concern one study and chemistry, not particle-size error, success probability, synthesis generation or cross-lab reproducibility. Exact chloride species are pooled/rescaled in the author data; per-run duration, phase, atomic coordinates and direct particle size are unavailable.

See `benchmarks/README.md` for reproducing the saved baseline. Its model artifacts, splits, predictions, source hashes and independent numerical checks remain available locally. Public reports are generated with the dataset, without publishing downloaded paper PDFs or local filesystem paths.

## Expansion to 5,000–50,000 records

Keep this scientific schema and shared renderer; extend it through explicit migrations, controlled action/property/unit vocabularies and verified chemical identifiers. Pilot records are not yet a fully normalized chemical ontology. Measure extraction agreement and curator throughput before scaling. Add a review queue, database indexing and server-side catalog pagination when the collection outgrows the current static manifest. The current implementation has been tested at 151 records, not load-tested at 50,000. Keep rich paper guides as separate context with reciprocal links to canonical records. Prospectively test proposed recipes with the collaborating lab and retain failures and repeats.
