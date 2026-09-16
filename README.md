# MatterSyn — interactive synthesis notebook

A static, source-linked prototype for a single colloidal quantum-dot recipe.

## Selected experiment

Nakonechnyi et al., *Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots*, Chemistry of Materials 29 (2017), 4719–4727. DOI: https://doi.org/10.1021/acs.chemmater.7b00354

Only the **Zinc Blende CdSe Core QDs** paragraph, PDF page 2 / printed page 4720, is represented. The main article and supporting information were reviewed. Wurtzite cores and shell-growth recipes are separate experiments.

## Structure and data

- `dist/index.html`, `styles.css`, and `app.js`: static page, no build step.
- `dist/assets/recipe.json`: structured operations, amounts, material lineage, source evidence, missing fields, and product observations.
- `dist/assets/molecular-structures.json`: PubChem computed 3D conformers, with atom indices for functional-group highlighting. Only the six molecular reagents used by this recipe appear in the UI.
- `dist/assets/*reference.json`: independently sourced reference lattices. The CdSe sphere is a geometric crop, not a measured nanocrystal. Selenium powder allotrope is unspecified in the recipe; the selenium model is a trigonal reference only.
- `dist/assets/flask.png`: generated apparatus illustration. Its exact apparatus configuration and liquid color are not experimental observations.
- `dist/vendor/3Dmol-min.js`: official 3Dmol viewer, distributed with its license notice.

The reported approximately 3 nm diameter is absorption-derived from the 537 nm first-exciton absorption peak. Exact purification state at that measurement is unspecified. No PL peak, PLQY, particle shape, or unreported experimental condition is invented.

## Local use

Serve `dist` over HTTP, for example with Python's `http.server`, then open the local address in a browser with WebGL. Opening the HTML directly as a file can prevent coordinate loading.

Rotate models by dragging and zoom with the mouse wheel. Select reagents, toggle group highlighting, switch crystal representations, and follow the seven stages. The selected paper remains the authority for experimental interpretation.
