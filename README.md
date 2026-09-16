# MatterSyn — interactive synthesis notebook

A static, source-linked website for exploring colloidal nanocrystal synthesis.

## Current example: Alivisatos group, 2000

Peng, Manna, Yang, Wickham, Scher, Kadavanich & Alivisatos, *Shape control of CdSe nanocrystals*, Nature 404, 59–61 (2000). DOI: https://doi.org/10.1038/35003535

The supplied three-page article supports two distinct condition sets: a typical synthesis family and a separate high-aspect-ratio variant. The page preserves their separate stock ratios, temperature statements and missing details. Discrete HPA comparisons show only reported qualitative outcomes. Figure-specific particle dimensions are selectable independently; the article does not map them to complete recipes.

- `dist/index.html`, `shape.css`, `shape-app.js`, `shape-data.mjs`: current page and interactions, with shared `styles.css`. No build step.
- `dist/assets/peng2000-recipe.json`: structured extraction with source locators, variants, reported results and missing information.
- `dist/assets/peng2000-molecular-structures.json`: PubChem 3D conformers for HPA and TBP, a PubChem 2D TOPO depiction, and formula-only dimethylcadmium. The disconnected standardized dimethylcadmium record is not presented as molecular geometry.
- `dist/assets/peng2000-crystal-reference.json`: independent bulk wurtzite CdSe reference (COD 9016056). Models crop it to envelopes based on dimensions from Figures 2 and 4. They do not reconstruct experimental surfaces, ligands, defects or exact atom counts.
- `dist/assets/selenium-reference.json`: independent trigonal reference, not a claim about the powder allotrope or dissolved selenium species.
- `dist/assets/flask.png`, `dist/og.png`: generated illustrative apparatus and social preview artwork.
- `dist/vendor/3Dmol-min.js`: official 3Dmol viewer, distributed with its license notice.

The historical article does not supply a complete executable SOP. Missing growth duration, stock preparation, atmosphere, ramp, full injection schedule and purification remain explicit. No conditions are borrowed from later publications.

## Preserved earlier example

`dist/nakonechnyi-2017.html` retains the previous page and loads `nakonechnyi-2017.js`. It covers only the **Zinc Blende CdSe Core QDs** paragraph on printed page 4720 of Nakonechnyi et al., *Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots*, Chemistry of Materials 29 (2017), 4719–4727. DOI: https://doi.org/10.1021/acs.chemmater.7b00354

Its data remains in `dist/assets/recipe.json` and the original structure assets. Main article and supporting information were reviewed. The approximately 3 nm diameter is absorption-derived from the 537 nm first-exciton peak; no PL peak, quantum yield or unreported experimental condition is assigned.

## Local use and validation

Serve `dist` over HTTP, for example with Python's `http.server`, then open the local address in a browser with WebGL. Opening HTML as a local file may prevent coordinate loading.

Drag 3D models to rotate; scroll to zoom. TOPO is a pannable and zoomable 2D diagram. Select recipes, stages, reported particle dimensions, head-group highlighting and crystal display styles. Source facts and missingness remain available without WebGL.

Validation includes JavaScript syntax, local references and IDs, JSON integrity, molecular bond indices, and all four lattice crops. Crystal checks cover unique positions, envelope bounds, reciprocal Cd–Se bonds and maximum tetrahedral coordination. Browser interaction testing was not performed for this update.

Sites hosting is configured in `.openai/hosting.json`; the publication retains owner-only access.
