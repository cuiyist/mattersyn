## Current material atlas — 2026-09-17

`dist/index.html` is the periodic-table parent. `cdse.html` preserves the detailed CdSe hub; `material.html?id=…` aggregates other material collections. `library.html` searches local paper groups and `paper.html?id=…` records source coverage. `dataset.html?material=…` filters canonical protocols by material or component system.

The source library contains 4,176 local paper groups linked to 479 candidate/reviewed material collections. The 7,373-document indexing pass is complete: 7,171 text extractions, 154 legacy DOCs, 44 mismatched XLSX/ZIP payloads, and 4 PDFs without extractable text. Full text and candidate windows remain private outside this Site. Indexing is not full-paper scientific curation. Title-level formula associations are candidates and cannot create training labels.

Dataset 0.3.0 contains 151 canonical records: 39 reviewed protocols, variants and controls, 12 supporting procedures, and 100 published PbS benchmark rows, across 9 source groups. Protocol variants, controls and procedures are not counts of independent physical experiments. No exact measured structure-to-complete-recipe pairs are verified.

Four main–SI sets have complete page inventories covering 64 pages: Fu (ZnO), Nakonechnyi (CdSe/core–shell), Stowell (Ir), and Feld (Fe–O). `paper-review.html?id=…` exposes their source coverage, recipes, characterization, original graphics, tables, equations, models, conflicts and unresolved sample links. The library's **Full main + SI** filter distinguishes these four groups from the rest of the corpus. Each review records the actual scope of its independent audit; full reading does not imply resolved source errors, raw-curve digitization, a complete laboratory SOP, or training eligibility. Most local paper groups still require this review.

The CdSe hub gives four historical methods equal cards and adds a separate seeded core/shell route. `murray-1993-characterization.html` exposes all 15 original main-article figures. `nakonechnyi-2017-saed.html` exposes SI Figure S2, whose four panels are core/shell products. Murray's SAED remains text-only. Figure JSON and crop hashes are separate paper-level evidence, not experimentally linked recipe targets.

After changing canonical sources, run `scripts/build_dataset.py`, then `build_reader_views.py`, `build_evidence_views.py`, `build_paper_reviews.py`, and `build_atlas.py`. Validate with the dataset unit tests, `check_site.py` and `check_atlas.py`; the paper-review builder additionally checks page completeness and source/asset hashes. The public corpus snapshot is `data/corpus/library-source.json`; the resumable extraction and review implementations remain in the parent project's research-assets directory. Earlier sections below describe historical versions.

# Training-oriented pilot · September 2026

`dist/dataset.html` provides 112 canonical record pages: nine curated recipe variants, three shared procedures and 100 separately attributed published PbS experiment rows. Five material families are represented. The schema, records, exports, source grouping and full PbS regression comparison are documented in [data/README.md](data/README.md).

The existing illustrated paper guides are retained and linked to their canonical records. These guides provide contextual figures and models; they are not separate labeled experiments. New record pages and training exports are generated from the same validated JSON. Browser checks cover the new catalog and molecular viewer; scientific regression tests and static integrity checks cover data and exports. The earlier implementation notes below describe historical stages.

# MatterSyn — interactive synthesis notebook

A static, source-linked website for exploring colloidal nanocrystal synthesis.

## Material-centered CdSe atlas

The entry page is a CdSe material overview that accommodates contributions from multiple papers. Hot injection is the first method category. Murray et al. (1993) Methods 1 and 2 have separate detail routes; the earlier Alivisatos-group (2000) and Nakonechnyi et al. (2017) pages remain linked.

- `dist/index.html`: material overview, method selection, shared structural and optical evidence, chemical intuition and literature.
- `dist/murray-1993-method-1.html`: TOPSe route, complete reported CdSe inventory, stock solutions, synthesis, isolation, size selection and optional pyridine exchange.
- `dist/murray-1993-method-2.html`: bis(trimethylsilyl)selenium route; explicit boundaries around the incompletely specified formulation and the approximately 100 °C small-species variant.
- `dist/material-data.mjs`, `material-app.mjs`, `academic.css`: shared source-linked records, molecule/stock interactions, stage illustrations and unit-cell/nanocrystal viewers. `dist` is the authored static source; there is no build step.

Method pages use five academic sections: **Precursors**, **Synthesis protocol**, **Final structures**, **Properties** and **Chemical intuition**. Stock panels display both precursor and solvent structures. Approximate concentrations calculated from additive volumes are labeled as calculations, not measured concentrations.

Method 1 dissolves selenium shot in TOP to prepare TOPSe; it does not inject elemental selenium alone. Method 2 instead uses (TMS)2Se, stored at −35 °C in a drybox. The precursor section follows reference 3a to Steigerwald et al. (1988), DOI 10.1021/ja00218a008, and reports its Se / lithium triethylborohydride / trimethylsilyl chloride / THF preparation without importing that approximately 0.3 M THF formulation into the unspecified Murray injection stock. Murray's reference list prints 1987 for this 1988 article. Reference 4, Detty and Seidler (1982), is identified but its full experimental text was not accessed. The Murray SI remains unlocated/unverified.

`dist/assets/cdse-structures/` contains the original COD 9016056 CIF, a four-site expanded P1 CIF, and the displayed illustrative 582-atom nanocrystal as XYZ and CIF in an artificial 80 Å vacuum box. CIF files are compatible with VESTA. The independent Materials Project mp-1070 link is not presented as the source of these experimental bulk coordinates. Ligand positions, faults and relaxed surface structure are not reconstructed.

`cdse-chemical-intuition.json` separates original explanations, later evidence, interpretations, limitations and research outlooks, with claim-level references. Measurements retain figure-specific sample identities and are not automatically assigned to Method 2. Original TEM, XRD, absorption and photoluminescence figures remain accessible.

Validation for this revision includes source review, molecular identity/connectivity and coordinate checks, structure-file hashes and CIF round trips, JavaScript syntax, and static link/ID consistency. Local browser checks exercised both method routes, stock components, the ionic precursor diagram, thermal subphases, optional exchange, unit-cell periodic context and nanocrystal representation controls. No console errors or warnings were observed in these checks. This does not establish chemical reproducibility or complete an unreported SOP.

## Original single-paper implementation: Murray, Norris & Bawendi, 1993

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

Sites hosting is configured in `.openai/hosting.json`; publication retains the existing public audience. Historical validation descriptions above refer to the original implementations; the current revision includes the browser checks described at the top.
