# MatterSyn sample structure descriptor v0.2

**Status:** pilot specification. Apply to a small, audited sample before migrating canonical records. It defines separate data views; it does not make every published row training-ready.

## Pair unit

A synthesis–structure pair is a source-supported relation between:

1. one recipe instance or explicitly distinguished recipe variant, including its reported conditions;
2. one identified product sample or fraction produced by that recipe; and
3. at least one source-supported structural outcome for that sample, such as composition plus phase, particle morphology, a size/dimension/distribution, lattice data, or heterostructure architecture.

Atomic coordinates are not required. A TEM size and an XRD phase assigned to the same sample enrich one pair; they do not create two pairs. A changed synthesis condition that produced a separately identified sample with a different measured size or other structure is a distinct pair, even if its morphology is unchanged. A recipe that yields separately isolated and characterized fractions may link to multiple pairs. A trend or figure with no defensible sample-to-recipe assignment remains an unpaired observation until the link is resolved.

Keep the record-row count distinct from a deduplicated physical-sample count. Use explicit batch, parent-sample, aliquot and fraction lineage when reported. If records might refer to the same specimen but the relation is unresolved, retain separate source rows and mark the cross-record identity as unresolved; do not silently merge them. If a later paper contributes evidence about the same physical sample, attach that evidence to the existing sample. A new independent synthesis run is a new observation, grouped with related recipe families for evaluation splits.

## Reuse one schema without reusing the answer

Use the same versioned descriptor schema for a requested target and an observed product, but keep them in separate instances:

```json
{
  "schema_version": "mattersyn.structure/0.2",
  "intended_target": {
    "structure": { "composition": {}, "architecture": {}, "components": [] }
  },
  "products": [{
    "sample_id": "stable-source-scoped-sample-id",
    "structure": { "composition": {}, "architecture": {}, "components": [] },
    "measurement_ids": ["source-linked-measurement-id"]
  }]
}
```

The target describes what a user asks the model to make. The product descriptor contains observations made after synthesis. Do not copy observed measurements, captions, outcomes, or outcome-derived interpretations into the target input. A training view selects fields from these two objects for a named task; the website may show both.

## Descriptor fields

Each value is a typed `fact` or `quantity`, with its raw source wording when normalization changes the form and a source/page/section/table/figure locator. Preserve all method-specific observations. Where practical, the descriptor references canonical measurement IDs rather than copying their values.

| Block | Required contents |
|---|---|
| Sample state | Stable `sample_id`, `parent_sample_id`, `batch_id`, state (as-synthesized, purified, fractionated, shelled, exchanged, annealed, embedded, film, or an extensible `other`), and the operation that produced the state when known. |
| Composition | Formula and elements, with basis kept explicit (`nominal`, measured bulk, surface-sensitive, or unresolved). Dopants, elemental ratios and component-specific composition retain method, uncertainty and evidence. |
| Architecture | Controlled value plus an extensible source label; ordered components from core/domain outward through shell, crown, coating or host. Distinguish alloy, gradient, heterodimer, supported and embedded systems. |
| Crystal structure | Phase/polytype per component, space group, lattice parameters, phase fractions, defects and evidence methods (XRD, SAED, HRTEM/FFT, WAXS, Raman, EXAFS, or other). A phase fact requires its evidence method. |
| Morphology and dimensions | Shape and each relevant dimension (diameter, axes, length, width, thickness, edge, shell, aspect ratio) with measurement or derivation method, sample/statistical basis and distribution when reported. Keep particle size distinct from crystallite size, hydrodynamic size, pore size and a model parameter. |
| Surface and host | Ligand identity/binding group, coverage and method when reported; surface stoichiometry, inorganic passivation, medium, substrate or matrix. Preserve unknown interfaces and partial coverage. |
| Structure assets | IDs for source coordinates, refined experimental structures, external phase references, computations and illustrations, each with an explicit role and provenance. A database CIF, constructed particle or viewer model never becomes a measured sample label merely because it shares the formula. |
| Properties | Optical, electrical, magnetic, catalytic and other outcomes stay in separate property records with sample, measurement method, acquisition conditions and evidence. Absorption may support a stated size derivation, but optical response alone is not silently relabeled as morphology or crystal phase. |

Do not impose one universal `headline_size` across methods. TEM, SAXS, XRD, optical sizing and DLS may refer to different estimands or populations. Preserve each qualified result. A display or task-specific summary can select one with a declared rule and retain its method and source; it is derived metadata, not a replacement for the observations.

## Missingness, disagreements and training tiers

Use statuses that distinguish `reported`, `author_derived`, `calculated`, `inherited`, `inferred`, `not_reported_in_reviewed_scope`, `not_reviewed`, `not_located`, `not_applicable`, `conflicting`, and `sample_link_unresolved`. `not_reported_in_reviewed_scope` is allowed only after the named source scope was checked. Every non-reported status carries a reason; reported or derived claims carry evidence and derivation details. Never turn an unknown into zero or silently average conflicting methods.

Track separate counts for source papers, route records, source-linked recipe/sample structure rows, deduplicated physical sample outcomes, task-eligible examples, and sample-linked measured-coordinate examples. The broad pair count does not require a CIF. Exact-coordinate tasks are a stricter subset and require independently reviewed sample, coordinate asset, representation, recipe graph, task profile and gap/conflict decisions.

Completeness is task-specific. A phase-conditioned route retrieval task may require composition, phase and a linked recipe; a size-conditioned task additionally needs comparable sample-linked dimensions and their methods; exact atomic-structure design needs an appropriately qualified coordinate asset. Do not publish one global completeness score as if it decided every task. Keep uncertain and conflicted cases visible to readers while blocking only the task whose required fields remain unresolved.

## Initial projection pilot

The current dataset export projects each accepted canonical recipe/sample row into `mattersyn.structure/0.2` with `mapping_status: partial_canonical_projection`. This is an additive export; canonical records have not yet been migrated to the new nested schema. Unit checks cover three contrasting source shapes: Dabbousi et al. (1997) CdSe/CdS overgrowth, whose route-level product has qualitative core/shell morphology but no linked final-size measurement; Fu et al. (2007) ZnO sample S1, whose target has no prespecified numerical size while the observed product has source-linked phase, morphology, and HRTEM dimensions; and Saha et al. (2019) CoO/CoFe2O4 growth, with sample-linked microscopy and diffraction measurements. The PbS optical benchmark is a negative control: absorption outcomes stay in the property view and do not create a structure pair without a sample-linked structural result.

These examples test target/outcome separation, measurement references and the rule that several techniques on one sample remain one pair. Before migrating canonical records, review each projected descriptor against the paper/SI and associated figures, including whether any cross-record rows refer to the same specimen. Keep the projection marked partial until that source-level audit is complete. Extend the allowlist only with a reviewed reason and evidence-backed sample mapping; do not replace it with substring matching.
