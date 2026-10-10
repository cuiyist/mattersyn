# Site patches

Changes to the MatterSyn site code, prepared and tested on a local copy. Nothing here has been pushed to GitHub.

## unit-cell-default.patch (2026-10-10)

**Problem.** Only 279 of the site's 1,156 synthesis routes (24%) and 96 of its 283 materials show a unit cell. A cell appears only when a library entry lists that exact record, and the library has been extended one paper at a time.

**Change.** A route with no hand-bound reference now shows the library's bulk cell for the same composition, or one cell per component for a composite such as CdSe/CdS. If the record reports a phase, only matching cells are shown; otherwise all bulk forms in the library are shown. The card says "Reference by composition" and states that it is not a structure of the synthesized sample. Hand-bound references and the custom viewers are unchanged.

**Result.** 900 of 1,156 routes (78%) and 168 of 283 materials show a cell.

**Files.** New `recipe-atlas/static/crystal-defaults.mjs`; small edits to `reader-structures.mjs` and `crystal-viewer.mjs`.

**Tested.** Full site build on a local copy of main at `dd11573`: all 13 stages passed and 206 Python tests passed. Checked in the browser on a CdS route, a CdSe/CdS composite and a hand-bound CdSe route, with no console errors. **Not run:** the JavaScript tests, because Node is not installed on the test machine.

**To apply.** `git apply site-patches/unit-cell-default.patch`, then regenerate `publication/build-inputs.json` and the allowlist with the project's own tools, since both list every file by checksum.

**Still without a cell (256 routes).** These need new crystal files in the library: ZrO2, AlN, CoPt3, CuInS2, Ag2Se, Ag2Te, LiMn2O4, CaCO3, AgInTe2, FeIn2S4, GdFeO3, SnSe, Bi2Te3, AgBiS2, PbTe, Sn, BaTiO3, Al, AgInS2, In2O3, MoS2, CuFeS2, Cd3P2, Zn3P2 and others. Some entries have no single crystal structure to show: amorphous silica, organic molecules, phase mixtures and alloys of unstated structure.
