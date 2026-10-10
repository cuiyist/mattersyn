# Site patches

Changes to the MatterSyn site code, prepared and tested on a local copy of `main` at `dd11573`. Nothing here changes `main`.

## Unit cells (2026-10-10)

**Problem.** Only 279 of the site's 1,156 synthesis routes (24%) and 96 of its 283 materials showed a unit cell. A cell appeared only when a library entry listed that exact record, and the library had been extended one paper at a time.

**Change 1: a default by composition** (`unit-cell-default.patch`). A route with no hand-bound reference shows the library's bulk cell for the same composition, or one cell per component for a composite such as CdSe/CdS.

- If the paper states a phase, only cells of that phase are shown.
- If the paper states a phase and the library has no cell of that phase, **nothing is shown**. For example, "chemically disordered fcc CoPt3" stays blank although the library holds the ordered CoPt3 cell.
- If the paper states no phase, every bulk form in the library is shown, with a note saying so.
- The card says "Reference by composition" (or "Component reference") and that it is not a structure of the synthesized sample.
- Hand-bound references and the custom viewers are unchanged.

Files: new `recipe-atlas/static/crystal-defaults.mjs`; small edits to `reader-structures.mjs` and `crystal-viewer.mjs`.

**Change 2: 27 new bulk cells** (`add_crystal_references.py`, `crystal-references/`). Structure files from the Crystallography Open Database for ZrO2 (monoclinic, tetragonal), AlN, CoPt3, CuInS2, Ag2Se, Ag2Te, LiMn2O4, CaCO3 (calcite, aragonite), AgInTe2, FeIn2S4, GdFeO3, SnSe, Bi2Te3, PbTe, Sn, BaTiO3 (tetragonal, cubic), Al, AgInS2 (chalcopyrite, orthorhombic), In2O3, MoS2, CuFeS2, Zn3P2 and Te. Each was chosen as an ambient, stoichiometric entry and its lattice constants were checked against known values (all within 1%). The entries are bound to no record; they appear through the default.

**Result.** 1,008 of 1,156 routes (87%) and 195 of 283 materials show a cell.

**Left blank on purpose.** Amorphous materials (silica), organic molecules, solid solutions and mixtures, hybrid layered perovskites, and phases the library does not hold (cubic ZrO2, cubic AgBiS2, corundum In2O3, cubic CsPbBr3).

**Tested.** Full site build with both changes: all 13 stages passed, including the library checks in `check_quality.py`. The converter reproduced the atom positions of all 102 database-derived cells already in the library. Checked in the browser on CdS, CdSe/CdS, a hand-bound CdSe route, ZrO2, PbTe and CoPt3, with no console errors. **Not run:** the JavaScript tests, because Node is not installed on the test machine.

**To apply.**

```
git apply site-patches/unit-cell-default.patch
python site-patches/add_crystal_references.py --repo . --cif-dir site-patches/crystal-references/cif --list site-patches/crystal-references/chosen.json --retrieved 2026-10-10
```

The second command writes the 27 CIF files and model files, and appends the entries to `registry.json` and `crystal_reference_pins.json`. Then regenerate `publication/build-inputs.json`, the allowlist and the rights register with the project's own tools, since they list every file by checksum.

`python site-patches/add_crystal_references.py --verify .` rebuilds the cells already in the library and compares them with the stored models.

## Extracted records in the Reader (2026-10-10)

**Problem.** The Reader, the material pages and the final quality check accept only records marked `source_reviewed`, so a paper read by the local model could not appear at all.

**Change** (`extracted-records.patch`, 7 lines in 4 files).

- `schema_definition.py`: a new review status, `source_extracted`.
- `build_atlas.py` and `check_quality.py`: records with that status count as synthesis routes.
- `build_atlas.py`: each route on a material page carries its review status.
- `reader-app.mjs`: a page that includes an extracted record is headed "Synthesis and evidence".

Not changed: training eligibility, the audited pair table and the paper counts still require `source_reviewed`.

**Tested.** With the converter in `simple/to_site.py`, a made-up extracted paper passed the complete site build and rendered in the Reader. The JavaScript tests were not run.

**To apply.** `git apply site-patches/extracted-records.patch`. The schema file has mixed line endings; the patch changes one line of it and leaves the rest byte-identical.
