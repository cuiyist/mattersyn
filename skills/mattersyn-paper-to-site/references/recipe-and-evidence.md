# Structured recipes and scientific evidence

Use this reference for extraction or changes to scientific content. Adapt existing project records without breaking working consumers; this is a field contract, not a requirement to migrate older records.

## Recommended record structure

| Record | Information to preserve |
|---|---|
| `sources` | Source ID; main/SI/reference type; title/DOI; verified identity; file or URL; availability and inspection status. Keep local paths out of public exports. |
| `protocols` | Stable ID; selected method; material; scope; explicitly separate alternative routes and optional branches. |
| `materials` | Complete inventory within the selected scope: identity, formula, abbreviation, role, purity, pretreatment/storage as reported, database IDs and connectivity/structure provenance. Distinguish synthesis inputs, upstream precursor inputs, process media, workup reagents, optional branches and characterization/calibration materials. |
| `stocks` | Solute and solvent identities, concentration and basis, preparation operations and source, final amount if reported, storage and later use. Do not substitute elemental starting material for the dissolved precursor or imply that separate component models establish solution speciation. |
| `operations` | Stable ID; branch; operation type; input/output material IDs; additions; condition phases; timing/endpoint; equipment; retained/discarded fraction; source locators. |
| `samples` | Stable sample ID; lineage and workup state; recipe mapping status; composition, phase, morphology and dimensions; measurement method; uncertain identity links. |
| `observations` | Sample-specific results or clearly labeled study-wide findings; measured/calculated/qualitative status; units, uncertainty and source. |
| `visualizations` | Structure references, computed-model methods, geometric envelope, omitted features and illustrative status. |
| `gaps` | Unreported quantities, ambiguous statements, inaccessible SI and unresolved conflicts; why they matter. |

For a scientific quantity, retain:

```json
{
  "raw_text": "approximately 200 degrees C",
  "value": 200,
  "unit": "degC",
  "approximate": true,
  "status": "reported",
  "meaning": "reaction temperature during degassing",
  "evidence": [{"source_id": "main", "pdf_page": 2, "printed_page": "8707", "section": "Method 1"}]
}
```

This is a notation example from the original project, not a default for future papers. Missing quantities use `value: null`, an explicit missing status, and a description. Calculated values identify inputs and derivation; inferred values identify the assumption. A null time is not zero time.

## Extraction decisions that matter

- Capture both amounts and their basis: total reaction, stock, a withdrawn aliquot, a washing cycle, or a selected fraction. Keep ligand-containing isolated mass distinct from inorganic material yield.
- Separate time concepts: degassing duration, injection duration, elapsed growth, sampling interval, stage endpoint and total preparation time. "Rapid", "a few hours", and "until clear" are not precise numerical durations.
- Preserve symbol differences such as `much less than 1 s` vs `less than 1 s`. Do not turn a temperature pair into an invented ramp or infer a cooling bath from a target temperature.
- Pressure belongs to a phase. Do not show vacuum and argon stabilization as simultaneous conditions. State whether temperature is the sample, reactor, bath or device setpoint when the source resolves that.
- For each separation, track which fraction contains the desired product. A later centrifugation can require keeping supernatant even when the earlier one required keeping the pellet.
- Optional reinjection, size selection, ligand exchange, shell growth and alternate chalcogen routes remain separate branches unless explicitly part of the selected recipe. Independent preparation branches do not establish that operations occurred simultaneously; preserve material dependencies without inventing a timing schedule.
- A concentration percentage needs a denominator before converting to a mass. A spectral feature is not necessarily a PL peak. A first-exciton absorption-derived size is not a direct TEM size.
- Distinguish exact recipe-to-figure links from qualitative compatibility. Equal nominal sizes do not establish specimen identity. If only long-axis size is reported, do not invent a measured short axis; a chosen model aspect ratio must be labeled illustrative.
- A study-wide maximum aspect ratio, quantum yield or size range is not automatically the outcome of the default recipe. Do not fill a missing run record from a nearby paragraph or a later paper.
- Preserve discrepancies with source evidence. For example, if listed component volumes exceed the stated syringe capacity, show the original quantities and flag the arithmetic discrepancy instead of changing a value.

## Evidence review

Check visually any source detail prone to OCR error: Greek letters, superscripts, inequality signs, exponent signs, decimal points, units, table footnotes and figure-axis labels. Main text and SI can legitimately describe different variants; record conflicts rather than choosing silently.

A compact review should trace representative facts from source to record to visible page, especially temperatures, quantities, durations, pressures, product fractions and sample-property assignments. Follow a clearly chosen sample through preparation and characterization; leave the link unknown when the paper does.

## Cited preparations and chemical interpretation

- Follow explicitly cited precursor preparations when they affect the requested explanation. Keep a source-specific upstream record and its materials separate from the target synthesis; a downstream reaction on the same page must not supply missing precursor-preparation conditions.
- Distinguish original source inspected, abstract or excerpt inspected, bibliographic identity verified, and full procedure inaccessible. Preserve a citation-year discrepancy rather than silently copying it. Do not infer a one-reference-per-compound assignment when a paper cites several references together.
- A variant described as a substitution can inherit a stated framework, but inherited context is not an independently quantified run. Mark inherited fields explicitly; do not invent a replacement precursor charge, solvent, concentration, duration or yield.
- Storage needs a material, source, temperature, environment and missing duration where appropriate. Reagent storage is distinct from reaction conditions and final-product storage. Differing temperatures in different papers are not interchangeable.
- Derived stock concentrations identify the volume-additivity assumption and input quantities. Do not promote nominal arithmetic into a measured concentration or silently resolve a volume discrepancy.
- Chemical-intuition claims carry a primary source and locator, source access level, and original experimental-system boundary. Label the original authors' explanation, later research, our interpretation and proposed outlook separately. A later mechanism can refine a historical picture without establishing the mechanism, impurity inventory, surface coverage or kinetics of that historical sample. Proposed questions are not novelty claims.
