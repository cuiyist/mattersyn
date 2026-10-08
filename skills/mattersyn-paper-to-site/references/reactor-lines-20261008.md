# Reactor lines for new audited-lane papers, 2026-10-08

Apply this owner instruction to new independently audited papers. Use the current record schema and its evidence fields. Do not backfill already published papers, migrate the schema, or change frozen local-model prompts, schemas, counters, calibration or publication gates. Machine-lane reactor extraction is deferred to its next version after calibration. Missing reactor details do not change five-field eligibility or reject a paper.

Use only source text and its actual locators. A schematic, familiar technique, neighbouring step or related paper supplies no missing value. "Standard air-free technique" does not establish a flask type, Schlenk line, glovebox or inert gas. Preserve the original operation description, environment value, status, evidence and note, including endpoints and conflicting statements.

| Fixed field name | Existing-schema carrier | Unit or value rule |
|---|---|---|
| `vessel_volume` | `operation.parameters` quantity | mL; preserve reported basis |
| `fill_fraction` | `operation.parameters` quantity | Source-stated fraction or percent; retain denominator/basis |
| `reaction_volume` | `operation.parameters` quantity | mL; distinguish charge from vessel capacity |
| `heating_rate` | `operation.parameters` quantity | degC/min; never derive a ramp from two temperatures |
| `stirring_rate` | `operation.parameters` quantity | rpm; missing rate remains not reported |
| `addition_rate` | `operation.parameters` quantity | Source-stated unit and basis |
| `pressure` | `operation.parameters` quantity | Source-stated unit, phase and pressure basis |
| `vessel_type` | `environment.note` reactor mapping | Three-neck flask, round-bottom flask, Schlenk flask, vial, beaker, autoclave, sealed tube, microwave vial, flow reactor, tube furnace, or other verbatim |
| `atmosphere` | `environment.note` reactor mapping | N2, Ar, air, vacuum, or other verbatim; distinguish successive phases |
| `schlenk_line`, `glovebox`, `stirring` | `environment.note` reactor mapping | Yes/no only when source-stated; absence is not "no" |
| `heating_method` | `environment.note` reactor mapping | Mantle, oil bath, metal or sand bath, hot plate, microwave, oven or furnace; retain source wording |
| `addition_method` | `environment.note` reactor mapping | Swift injection, dropwise, syringe pump, or none (heat-up) only when stated |
| `cooling_method` | `environment.note` reactor mapping | Water bath, ice bath, natural cooling, solvent injection, or other verbatim |

Each numeric parameter is an existing quantity with its own `value`/range, `unit`, `status`, `raw_text` and `evidence: [{source_id, locator}]`. Preserve the source basis and qualifiers; do not manufacture precision, convert a category to a numeric enum, calculate an unstated fill fraction, or infer pressure for a sealed vessel. An absent numeric field uses `status: "not_reported"`, null numeric values, and `raw_text: "not reported"`. Leave its evidence empty unless there is an actual source statement of absence; never fabricate a quotation or locator.

Serialize a fixed-name `reactor_line` mapping as JSON text appended to the existing `environment.note`, separated from its unchanged original narrative. Do not add an object-valued environment or new schema property, replace the environment value, or put a reported category into a null-valued quantity. The mapping contains `reactor_line_id` and the eight categorical names above. Each categorical entry contains `value`, `status`, `source_id` and `locator`; each reported value has its own source ID and exact locator. Preserve verbatim wording when no category fits and retain conflicts with their separate locators rather than choosing silently. For a scoped absence, use `value: "not reported"`, `status: "not_reported"`, `source_id: null`, `locator: null`; absence is never a fabricated source statement. The enclosing environment fact keeps its original status and evidence, rather than being promoted because some appended fields are reported.

Assign a stable local `reactor_line_id` only for a source-established vessel line. Share it between steps only where the source establishes that they use the same vessel; a different stated vessel gets a different ID. If continuity is unknown, leave the shared line unknown and do not link the steps through an invented vessel. A schematic never establishes continuity. Preserve separate preparation, reaction, transfer, workup and cooling stages.

For sealed vessels, check vessel volume, fill fraction or reaction volume, and pressure independently; each missing item remains not reported. Stirring does not establish a stirring rate. Injection style does not establish an addition rate. A target temperature does not establish a heating or cooling method.

Step schematics and captions must agree with the reviewed data, phase handling and vessel links. Depict an unstated vessel only as conceptual and say so in the caption; do not show invented flask necks, baths, atmosphere, solvent phases or shared vessels as reported apparatus. Authored schematics remain illustrations. Apply this light current-schema mapping during the normal independent source audit; no schema migration or retrospective release rewrite is required.

