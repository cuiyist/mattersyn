# Scientific visuals and interactive stages

## Molecular structures

1. Resolve exact chemical identity and connectivity from an authoritative reference such as PubChem. Similar abbreviations are not interchangeable: TOP and TBP have different alkyl chains.
2. Prefer a valid reference conformer when available. If only 2D connectivity is supplied, either show a clearly labeled 2D depiction or generate a legitimate illustrative conformer with a suitable chemistry toolkit. Do not present coordinates laid on a plane as a measured 3D structure.
3. For computed conformers, record software/version, embedding method and seed, minimization method and convergence, coordinate source, and unsupported parameters. Do not claim an optimized geometry or energy when minimization was not possible. A single conformer is not the unique solution or surface geometry.
4. If a standardized record disconnects an organometallic species into ions, do not invent geometry by connecting those fragments. Use a labeled connectivity schematic unless a valid molecular model is available.
5. Validate element counts/formula, atom indices, bond orders and endpoints, finite coordinates, plausible bond lengths, gross overlaps and highlight indices. Preserve source atom mapping or explicitly remap groups after atom reordering.
6. Highlight actual selected functional-group atoms/bonds. Keep molecular formulas and roles visible. Distinguish a free ligand from a surface-bound ligand, a named stock precursor from unresolved stock speciation, and a solid-element reference from its dissolved form.

Use rotate/zoom/reset controls, clear legends, keyboard support and an informative fallback. A 2D model should pan/zoom, not suggest meaningful out-of-plane geometry. Structure provenance must be available without requiring users to understand the software implementation.

For stock views, let readers inspect both solute and solvent components with their roles and provenance. Independent component conformers are explanatory models, not a measured solution complex or complete speciation analysis. Keep upstream preparation components separate from the eventual injection stock unless the source explicitly connects their compositions.

## Crystal models

- Obtain a verified reference lattice and cite its source. Use the correct phase for the selected method; wurtzite and zinc blende are not interchangeable.
- Crop the lattice to a declared envelope based on reported dimensions where possible. State which dimensions were measured, calculated or chosen just for illustration, and what measurement method supplied them.
- Make one unit conversion consistently; many structures use angstroms while particle dimensions use nanometers.
- Validate finite and unique atom positions, lattice conversion, envelope bounds, bond reciprocity and phase-appropriate coordination. Bulk reference coordinates inside an envelope are not an atom-by-atom experimental reconstruction.
- Disclose relevant omitted ligands, defects, stacking faults, surface reconstruction and faceting. Do not call a perfect bulk crop the actual measured crystal. Do not force a bulk phase label onto ultrasmall clusters when the source says that distinction is not meaningful.
- Keep measured optical properties tied to their source samples rather than the currently displayed geometric model when identity is uncertain.
- Show the bulk unit cell and finite particle as distinct models when both are requested. Give the unit-cell phase, lattice parameters, symmetry and reference provenance; display periodic neighbors separately so boundary coordination is understandable without changing the unit-cell atom count.
- Link verified Materials Project and/or Crystallography Open Database records where relevant and state whether each record is computed or experimentally refined. They are independent references, not measurements of the paper's nanocrystal, and a database name alone does not prove experimental provenance.
- Offer genuine CIF/XYZ downloads for the displayed models when available. Preserve the original reference CIF; label an explicit symmetry-expanded cell separately (for example P1 with all sites listed). A finite cluster in an artificial vacuum cell is not a measured crystal unit cell. Record model parameters, units, atom counts, coordinate transforms and omitted features; a geometric crop's nonstoichiometric atom count does not establish sample composition. Validate symmetry expansion, duplicate sites, periodic neighbors and round-trip coordinates when generating these assets.

## Characterization and properties

### Average crystal models and reflection lists

An average refinement with partial or mixed occupancy is a distinct representation. Preserve site populations and mutually alternative positions without selecting an ordered microstate. Use a source-specific viewer when a generic renderer would show partial sites as fully occupied or introduce unrelated mixed-element labels. State marker size, color and opacity as display conventions. A repeated average cell is not a finite particle, measured ligand shell or DFT-ready ordered input. Keep nominal composition, occupancy-weighted composition, omitted displacement parameters and unresolved coordinate/table discrepancies visible. A qualified curator reconstruction may be downloadable without becoming an exact structure–recipe training label.

For large SI reflection lists, offer a searchable, paginated typed table and raw/numeric downloads. Preserve source row identities, negative observations, zeros and ambiguous signs; retain null numeric values with explicit candidate values when a sign cannot be resolved. Calculated source intensities are not website-recomputed values. Rows are measurement data, not separate synthesis samples. Complete source pages and raw full-text payloads remain local under the publication policy.

Reader contracts must be checked on the built website as well as against evidence: route-evidence context fields contain arrays of real record IDs; narrative scope belongs in separate text fields. Withheld source-page attachments must not leave broken image URLs, and source identities, extracted facts and selected crops must remain intact.

Separate structural evidence (for example TEM, diffraction, phase and morphology) from material properties (for example absorption, emission and Raman). Associate each figure or result with its own reported sample or series, measurement conditions, and main/SI locator. Similar nominal sizes do not prove cross-figure identity.

For selected original figures, render or crop faithfully from the verified PDF and retain axes, legends, panel labels and scale bars. Inspect source pages and extracted panels, provide attribution and source links, and record crop/page provenance. Never generate, cosmetically redraw or enhance a micrograph or spectrum as if it were measured evidence. Enlarging an original figure is preferable to an invented interactive curve; digitization, if requested, needs a separate derived-data label and uncertainty.

Give nonexperts a concise explanation of what the technique probes and how to read the displayed figure. Label experimental traces and author simulations separately, preserve source inconsistencies, and avoid claiming a unique atomic reconstruction from a model fit. Text-only characterization stays text-only; cited prior work and byproduct measurements must not become newly measured product results. An unreported technique is missing only within the inspected source scope, especially while SI is unresolved.

## Apparatus scenes

Make the scene communicate the action, not merely decorate the page. Derive its apparatus, caption, condition cards and material-flow labels from the same selected operation. Use a phase selector when a single stage contains materially different conditions.

| Operation | Useful scene cues |
|---|---|
| Material or stock preparation | Reagent containers; elemental starting material becoming a stock; concentration and handling context. |
| Drying/degassing | Vessel above a schematic heating device; vacuum/argon indication; reaction temperature, pressure and duration for this phase. |
| Stabilization | The heated vessel with the new atmosphere/pressure and temperature; no inherited degassing time. |
| Combining solutions | Separate A/B containers, their contents, and a combined stock; drybox only when supported. |
| Rapid injection | Syringe or other reported addition method entering the vessel; heating removed when stated; before/after reaction temperatures. |
| Growth/monitoring | Heated vessel plus aliquot/cuvette; reported sampling interval and qualitative feedback; no fabricated spectra. |
| Withdrawal | Cannula or reported transfer device leading to a collection vessel. |
| Isolation/purification | Addition and separation; emphasize retained fraction and distinguish unwanted precipitate. |
| Drying | Product solid and declared drying environment; label generic equipment as schematic. |
| Size selection | Dropwise nonsolvent, visual endpoint, enriched fraction and repeat-until condition. |

Place temperature, time, pressure, atmosphere, quantity or endpoint beside the scene as appropriate. Missing values stay explicit. Use "reaction temperature" instead of a heater readout if no heater setting is reported. Do not invent water, oil or ice baths, apparatus dimensions, gas connections, centrifuge speed or sampling frequency.

Reuse suitable existing imagery and code-native components. Follow the current Sites/image-generation rules for new representational apparatus artwork; existing diagrams can be refined without rebuilding them. Chemical connectivity, stock-flow and scientific-data diagrams can remain code-native when that best preserves their meaning. Apparatus geometry and unreported liquid colors remain illustrative. Do not infer motion or chemical kinetics from a decorative animation.

Responsive diagrams must keep controls and condition text readable; ensure scenes remain distinct on mobile. Respect reduced motion. Do not reset unrelated viewers or merge protocol state when changing a stage.

## Source-bound illustrations and quantities

- A distillation pot residue and its collected distillates are separate material states. Give each retained fraction its own identity; an independently prepared comparison stock must not become another distillation cut. Diagram arrows must follow the reviewed state lineage.
- Render quantity bounds and intervals as bounds and intervals in every caption, including purity labels. A lower-bound value such as 99.9+% must not become a missing scalar, an exact percentage or a string such as `None%`.
- Match a structure model to the identified sample or chemical species. A molecular precursor or mechanistic complex CIF does not provide the atomic coordinates of the nanocrystal product, even when both occur in the same synthesis paper.
- Keep a generic heating schematic when the source reports heating without specifying a bath. Do not carry an oil-bath label, vessel closure, sample preparation mode or temperature from another control into the selected operation.
- Check every operation selector and its conditions, inspect all illustrated scenes, and test a narrow viewport. Private component previews, independent scientific audits and integrated website approval are separate checks; record their actual scopes.
- For a source-specific structure viewer, gate on the exact record, sample, composition and audited model identity. Test rejection on unrelated products. Expose whether coordinates are an asymmetric unit, a periodic structure or an illustrative geometry, and retain calculated hydrogen and omitted-contact qualifications.
- Do not show internal JSON strings as stock descriptions. Render their fields as readable quantities and notes without changing values; preserve identifiers in provenance and the machine download. Reusable templates should retain progress navigation across rebuilds.
- Bind symbolic product cards to an explicit product/sample context, not merely the record's overall material formula. A control or optical aliquot can have different or unreported phase information. Keep symbolic identities distinct from qualified coordinate models and retain source-scoped exclusions.
- Narrow-screen checks should include long provenance hashes and identifiers as well as diagrams. Wrap provenance text without truncating it or hiding scientific evidence.
- A supplied coordinate table can support a qualified partial reconstruction even when the original crystal-data archive is absent. Preserve literal coordinates, standard uncertainties, displacement parameters, units and site labels; independently verify scaling, the chosen space-group setting and reported bond geometry. Missing hydrogen positions and occupancies stay missing (`null` or CIF `?`). Label symmetry-generated markers as geometric positions, not an occupancy-weighted atom count. Such a bulk model does not establish nanocrystal, film, DFT or exact structure–recipe eligibility.
- Keep a table reconstruction in a separately audited display binding when it does not establish the identity of a physical synthesis aliquot. Match record, source, product/sample, formula and phase; reject unrelated contexts even when their formula matches. Preserve the frozen proposal and record subsequent presentation-only changes as explicit deltas.
- Check initial camera framing as well as rotation/zoom at narrow widths. A cell outline can extend beyond the atomic bounding box; responsive viewer dimensions and camera scaling should keep the intended geometry visible. Use a versioned module import after a rendering correction so browser QA and publication load the same code.
- Keep the intended synthesis target separate from observed phase components and whole-specimen composition. A failed target, mixed phase, transient phase or below-quantification impurity must not inherit the target formula as a measured pure product. Bind each symbolic phase card to a specific sample and evidence claim; leave unresolved specimen compositions unknown.
- Group alternative schedules by their source sample or profile in condition displays. Preserve every quantity and its exact canonical pointer, including uncertainty, bounds and fractional exponents; never combine alternative conditions into one apparent recipe. Acquisition intervals are not heating dwells or reactor residence times.
