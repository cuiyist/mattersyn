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
