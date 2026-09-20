# Original MatterSyn reference project

This is a contextual map for continuing the user's MatterSyn work. Do not redirect unrelated projects here or assume these paths exist on another machine. Read the local project memory for changes after this skill was written.

- Workspace: `[local path redacted]
- Memory: `MEMORY.md`
- User's paper collection: `downloaded_papers/`
- Extractions, inspected source pages and model provenance: `research-assets/`
- Working static website: `recipe-atlas/`
- Published reference: https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/
- Access was changed to public and independently checked without login on September 16, 2026. The material-centered redesign below was successfully published as version 6 on the same date; current audience was confirmed public before publication. Read current access before future mutations. No project ID or credential is embedded in this skill; resolve identity from the working checkout.

The September 17 atlas adds periodic-table discovery and a full-folder bibliographic index. See `corpus-atlas.md` for indexed-versus-reviewed scope and material-family review rules; consult MEMORY.md for actual publication status.

## Existing examples and reusable components

| Item | Current location relative to `recipe-atlas` |
|---|---|
| Periodic-table parent and material collections | `dist/index.html`, `dist/material.html` |
| Material-centered CdSe hub and paper contributions | `dist/cdse.html` |
| Whole-folder source library and paper coverage | `dist/library.html`, `dist/paper.html` |
| Full original Murray figure archive and Nakonechnyi SAED | `dist/murray-1993-characterization.html`, `dist/nakonechnyi-2017-saed.html` |
| Murray, Norris & Bawendi, JACS 1993, separate Methods 1 and 2 | `dist/murray-1993-method-1.html`, `dist/murray-1993-method-2.html` |
| Shared material/method content and views | `dist/material-data.mjs`, `dist/material-app.mjs`, `dist/academic.css`; original `dist/murray-data.mjs` remains a source module |
| Stage-specific scenes and condition cards | `dist/apparatus-scenes.mjs`, `apparatus.css` |
| Preserved Alivisatos/Peng2000 example | `dist/alivisatos-2000.html`, `shape-data.mjs`, `shape-app.js`, `shape.css` |
| Preserved Nakonechnyi2017 CdSe core example | `dist/nakonechnyi-2017.html`, `nakonechnyi-2017.js` |
| Shared visual styles | `dist/styles.css` |
| Recipe, molecular and lattice records | `dist/assets/` |
| Original characterization galleries | `dist/characterization.mjs`, `dist/characterization.css`, `dist/assets/murray1993-characterization.json` |
| Unit cell and finite-particle downloads | `dist/assets/cdse-structures/`, including `download-manifest.json` |
| Cited chemical intuition | `research-assets/cdse-chemical-intuition.json` in the workspace; sanitized copy under `dist/assets/` |
| Molecular viewer and license | `dist/vendor/3Dmol-min.js`, companion license |
| Source and deployment identity | `.openai/hosting.json` |

The component patterns are reusable; their chemical contents are paper-specific. Do not copy CdSe amounts, compounds, phase choices, figure dimensions, missing-SI status or access authorization into an unrelated recipe. Do not duplicate the entire research archive or dependency runtime to create another page.

The Murray 1993 supplement was not located or verified. The method pages therefore use the full main article and explicitly mark the SI gap. TOP/TOPO use locally computed illustrative conformers; TOPSe's embedding is unminimized. These are paper-specific provenance facts, not defaults for later papers.

### Current scientific boundaries

- Method 1 uses TOPSe; Method 2 substitutes bis(trimethylsilyl)selenium, `(TMS)2Se`, within the Method 1 framework. Method 2 is not an independently quantified complete CdSe procedure. Its missing charge, stock composition and general thermal history remain missing; the approximately 100 °C/1.2 nm smallest-species example is separate, and 290–320 °C in that paragraph is CdS only.
- Murray's General section reports prepared `(TMS)2Se` and `(BDMS)2Te` stored at −35 °C in a drybox; gas composition and storage duration are not specified. This is precursor storage, not CdSe growth or product storage.
- Verified upstream source: Steigerwald et al., *Surface Derivatization and Isolation of Semiconductor Cluster Molecules*, JACS 1988, DOI `10.1021/ja00218a008`, p. 3047. It provides a limited `(TMS)2Se` solution-preparation example from Se, lithium triethylborohydride and chlorotrimethylsilane in THF, approximately 0.3 M. Do not transplant its THF stock or its 0 °C storage into Murray. Murray's reference prints 1987; the original is 1988. Detty and Seidler 1982, DOI `10.1021/jo00346a041`, has verified bibliographic identity but its full procedure was not accessed. Detailed review: `research-assets/murray1993-precursor-method2-review.json`.
- The experimental bulk reference is COD 9016056; Materials Project mp-1070 is a separate computed reference. The unit cell and finite 3.5 × 3.0 nm wurtzite crop are separate views/downloads. The 582-atom crop (Cd288Se294) is an illustrative envelope, not measured stoichiometry or a reconstruction including stacking faults. Its CIF uses an artificial 80 Å vacuum box.
- Seven chemical-intuition cards separate the 1993 evidence, later primary research, our interpretation and proposed outlook. Later studies do not fill missing recipe fields or establish the mechanism of the original specimens. Source-access limitations remain in `research-assets/cdse-chemical-intuition.json`.

## User preferences established in this project

- Colloidal materials and quantum dots are the current research focus, with a collaborating lab for eventual validation.
- Use a material-centered hub with paper contributions and distinct method detail routes. Each recipe should be understandable to non-experts while retaining scientific traceability and academic primary labels.
- Method pages have five sections: Precursors, Synthesis protocol, Final structures, Properties, and Chemical intuition; Sources is an appendix. Maintain complete scoped inventories, inspectable solute/solvent components, cited upstream preparations, explicit storage and missingness.
- Show chemical formulas, structure and highlighted functional groups; allow rotation and zoom where valid coordinates exist.
- Make apparatus/action illustrations change by stage. Put reported temperature, duration and pressure beside the scene. Split condition phases instead of displaying incompatible conditions together.
- Include morphology, size, a bulk unit cell and clearly labeled finite crystal model when supported; offer CIF/XYZ downloads and verified MP/COD links. Preserve uncertain sample-to-property links and evidence/interpretation/outlook distinctions.
- Keep useful earlier examples accessible and save durable progress in MatterSyn memory.

The skill's editable project copy is under `mattersyn/skills/mattersyn-paper-to-site`; the discoverable installed copy is under the personal Codex skills directory. Keep these copies aligned for user-requested workflow updates after validation, without touching unrelated personal skills. Consult project memory for the most recent synchronization status.


## Training-data pilot (September 16, 2026)

The user approved several colloidal nanocrystal families. `recipe-atlas/data/README.md` is the maintained implementation guide. Canonical records live in `data/records/`; generated pages in `dist/records/`; catalog `dist/dataset.html`. Build with `scripts/build_dataset.py`, validate behavior with unittest in `tests`, and check local delivery using `scripts/check_site.py`. Use `benchmarks/` for reproducible published-PbS baseline calculations.

Current pilot: nine literature protocol/variant records and three shared procedures across CdSe, InP, CsPbBr3 and ZnO, plus100 separately attributed PbS numeric experiment rows (95 outcomes, five null-target failures). Seven source groups, no exact experimental-CIF-to-complete-recipe supervision;39 candidate papers remain uncurated. Do not mistake these for112 independent papers or a trained inverse model. The full2552-row local benchmark and source audits are in `research-assets/training-migration`. See MEMORY.md for source distinctions, completed validation and final publication status.
