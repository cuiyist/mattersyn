# Reader and Data views

Apply the September 22, 2026 design to every material hub and its synthesis routes. The same reviewed canonical records supply both views. Reader prioritizes molecular structures, operation illustrations, specimen-scoped final structures, original figures and short referenced interpretation. Data and evidence retains all quantities, branches, unknown values, qualifications, source locators and training decisions. Link both views, the source review and JSON downloads. Preserve earlier evidence editions when replacing bespoke routes.

## Reader components

- Keep equal method cards and academic headings: Precursors, Synthesis protocol, Final structures, Properties, Chemical intuition, Sources.
- Group each stock's composition and component illustrations under its own collapsed heading. Use explicit stock/context bindings where the stable IDs differ; do not join different formulations by similar names.
- Exclude apparatus from chemical inventory cards. Link equipment names to labeled schematics within their protocol step.
- Link protocol chemicals to source-bound molecular models. Match short element symbols case-sensitively (English “in” is not In). Input chips come from explicit inputs/stock components, never from a prose match.
- Label heteroatoms by default in 3D molecules, offer all-atom labels, and keep the element legend consistent with colors. Functional-group halos must not hide element identity. Compact SVG derivatives may remove surrounding prose only when all chemical paths, charges, counterions, isotope/hydrate labels and multiplicities are preserved. Retain uncertain originals.
- Offer unit-cell, morphology, and qualified finite-particle views. Model selection is by source phase/component/context; matching formulas alone do not establish sample coordinates. Distinguish experimental bulk references, computed cells, constructed lattices, source averages and finite illustrations. Provide CIF/provenance/licensing links. Do not invent missing dopant occupancies, coherent interfaces or amorphous periodic cells.
- Seed specimen selectors from every source context, including contexts with unknown composition. Shape, labels and displayed measurements must follow the selected specimen, not the parent recipe's nominal material. Core, shell, washings, controls, and comparisons remain distinct.
- Keep original figures in all applicable structural/property galleries. Mixed XRD/PL figures may appear in both; this is navigation, not a new sample association. Retain complete captions and qualifications behind a disclosure. Unavailable images remain text evidence. Do not split prose at abbreviations or discard qualification.
- Use progressive disclosure, narrow-screen checks, and keyboard/zoom/enlarge controls. A reference cell does not need a detailed finite-particle reconstruction to be useful.

## Structure–recipe metrics

Report coordinate-asset availability, explicit source-verified recipe links, and task-ready exact-structure records separately. Molecular species are not nanocrystal pairs. Bulk references and illustrative coordinates remain excluded from measured labels.

Exact-task admission requires a trusted independent, digest-bound task profile identifying the sample, coordinate bytes and representation, selected recipe graph, required fields, and disposition of existing gaps/conflicts. Optional or characterization missingness is not automatically a synthesis blocker; required unresolved fields still block admission. The default fails closed. A schema validation or matching composition cannot independently approve the scientific audit. Never create an audited profile merely to increase a displayed count.

## Existing implementation and checks

The shared Reader lives in `recipe-atlas/dist/reader-*.mjs` and `reader.css`. `scripts/build_reader_metadata.py` regenerates additive presentation metadata from reviewed source records. `scripts/build_dataset.py` generates the Data pages, manifest, six exports and per-record structure coverage using `data/structure-task-policy.json`. Source-sensitive stock mappings and chemical thumbnail manifests are explicit separate files. Run the dataset build before the reader metadata build.

For broad presentation changes, hash canonical records and training exports before work and verify they remain unchanged unless a separately audited scientific correction is intended. Check all material/route targets, figure and model assets, source/SI destinations, source-specific exceptions, and representative interactions at desktop and phone widths. Save both the initial independent findings and the correction recheck. Publish through the user's selected GitHub repositories using the existing public-projection policy; original papers/SI and raw full-text/page equivalents remain local.
