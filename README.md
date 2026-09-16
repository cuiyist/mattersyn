# MatterSyn — interactive synthesis notebook

A static, source-linked website for exploring colloidal nanocrystal synthesis.

## Current example: Murray, Norris & Bawendi, 1993

Murray, Norris & Bawendi, *Synthesis and Characterization of Nearly Monodisperse CdE (E = S, Se, Te) Semiconductor Nanocrystallites*, JACS 115, 8706–8715 (1993). DOI: https://doi.org/10.1021/ja00072a025

The ten-page original was obtained from the MIT-hosted copy and inspected. A matching supplement has not been located or verified; the website and data explicitly record that limit. No method is attributed to unverified SI.

- `dist/index.html`, `murray-app.js`, `murray-data.mjs`, `murray.css`: CdSe Method 1, its 10-mL aliquot purification, and separate size-selective precipitation sequence. Existing shared styles and lattice generation are reused.
- `dist/assets/murray1993-recipe.json`: full structured extraction, source locators, alternate methods kept separate, and missing/ambiguous conditions.
- `dist/assets/murray1993-molecular-structures.json`: source-referenced molecular assets with explicitly labeled representation types. TOP and TOPO use locally computed ETKDGv3/MMFF94s conformers; TOPSe uses unminimized ETKDGv3 geometry, with no energy claim. Methanol and 1-butanol use PubChem conformers. Dimethylcadmium remains a connectivity schematic.
- Spectrum-based growth feedback is qualitative historical logic, not an AI prediction. Thermal landmarks are not a time trace.
- `dist/apparatus-scenes.mjs` and `dist/apparatus.css` provide stage-specific illustrations and adjacent condition cards for all 14 stages. The Hot bath stage has independent degassing and argon-stabilization views; reaction temperatures are not labeled as bath setpoints. Equipment geometry, heating bath and vessel colors are schematic.
- The displayed 3.5 × 3.0 nm ellipsoid uses Figure 6 TEM dimensions. Its wurtzite reference omits stacking faults and surface details. Figure 5 optical properties and Figure 1 fractionation results are displayed separately.
- The approximately 300-mg isolated mass is capped product from a 10-mL reaction aliquot, not a whole-batch yield. The 50-mL syringe description and nominal 51-mL sum are retained without inventing a measured injection volume.

Validation covers source consistency, molecular connectivity, static links and IDs, JavaScript syntax and crystal geometry. The Figure 6 model contains 582 reference atoms and 1,017 Cd–Se bonds, with maximum coordination four and all coordinates within its stated envelope. These atom counts describe only the illustrative model. Browser interaction testing was not performed.

## Structural characterization and properties

The featured page has four main sections: Precursors, Protocols, Final structures and Properties, followed by a Sources appendix. `characterization.mjs` and `characterization.css` provide independent structural and optical figure selectors plus an accessible enlarged-figure dialog with zoom and fit controls. The existing crystal viewer remains a separate illustrative model.

Five faithful, visually inspected 300-dpi figure extracts retain the original labels, axes and TEM scale bar: TEM Figure 6, XRD Figure 11, experiment/model comparison Figure 15, absorption Figure 3 and absorption/PL Figure 5. Public provenance is recorded in `dist/assets/murray1993-figures/figure-manifest.json`; the full article and local machine paths are excluded from deployed assets.

`dist/assets/murray1993-characterization.json` records experimental conditions, figure-specific observations, source discrepancies and missing properties. SAED is text-only; cited EXAFS is prior work; EDX describes discarded byproducts. Raman is not reported in the inspected main article, and SI remains unverified. Figure 15’s one-versus-1.3 fault-count discrepancy is preserved. Equal nominal optical/TEM sizes do not establish specimen identity.

## Preserved example: Alivisatos group, 2000

Peng, Manna, Yang, Wickham, Scher, Kadavanich & Alivisatos, *Shape control of CdSe nanocrystals*, Nature 404, 59–61 (2000). DOI: https://doi.org/10.1038/35003535

The supplied three-page article supports two distinct condition sets: a typical synthesis family and a separate high-aspect-ratio variant. The page preserves their separate stock ratios, temperature statements and missing details. Discrete HPA comparisons show only reported qualitative outcomes. Figure-specific particle dimensions are selectable independently; the article does not map them to complete recipes.

- `dist/alivisatos-2000.html`, `shape.css`, `shape-app.js`, `shape-data.mjs`: current page and interactions, with shared `styles.css`. No build step.
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
