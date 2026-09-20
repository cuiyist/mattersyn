"""Private, source-specific extraction; does not mutate source PDFs or queue state."""
import datetime
import hashlib
import json
from pathlib import Path

import pypdfium2 as pdfium

HERE = Path(__file__).resolve().parent
SOURCE_ID = "nagasaki2004"
REVIEWER = "/root/backlog_eta"
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
MANIFEST = json.loads((HERE / "intake-manifest.json").read_text(encoding="utf-8"))
DOCS = {d["role_candidate"]: d for d in MANIFEST["documents"]}
FACTS = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ev(role, page, section, item=None):
    return {"source_id": SOURCE_ID + "-" + role, "source_sha256": DOCS[role]["sha256"],
            "pdf_page": page, "printed_page": str(6395 + page) if role == "main" else None,
            "section": section, "item": item}


def q(identifier, scope, prop, value, unit, raw, evidence, status="reported", qualifier="", approximate=False):
    fact = {"id": SOURCE_ID + "-" + identifier, "source_unit_id": scope, "property": prop,
            "value": value, "unit": unit, "raw_text": raw, "status": status,
            "approximate": approximate, "qualifier": qualifier, "evidence": evidence,
            "eligible_training": False, "independent_audit_status": "pending"}
    FACTS.append(fact)
    return fact["id"]


E1 = [ev("main", 2, "Experimental Section 1: polymer preparation")]
E2 = [ev("main", 2, "Experimental Section 2: aqueous CdS coprecipitation")]
EM = [ev("main", 2, "Experimental Section 3: measurements")]
EFIG1 = [ev("main", 3, "Results and Discussion", "Figure 1")]
EFIG2 = [ev("main", 3, "Results and Discussion", "Figure 2")]
EFIG4 = [ev("main", 4, "Molecular recognition", "Figure 4")]
ESI = [ev("si", 1, "TEM and XRD acquisition")]

Q = {}
for key, scope, prop, value, unit, raw, evidence, qualifier in [
    ("pdp-amount", "pdp-preparation", "PDP initiator amount", 1, "mmol", "PDP, 1 mmol", E1, "PDP amount; individual alcohol/potassium-naphthalene charges are not supplied."),
    ("thf-volume", "pdp-preparation", "THF volume", 45, "mL", "in THF (45 mL)", E1, "Medium for PDP solution before monomer addition."),
    ("eo-amount", "acetal-block-polymer", "ethylene oxide charge", 113.5, "mmol", "113.5 mmol of condensed ethylene oxide", E1, "Added through a cooled syringe; syringe and EO reaction temperatures are unreported."),
    ("eo-time", "acetal-block-polymer", "EO reaction duration", 2, "day", "After a 2-day reaction of EO", E1, "Before AMA addition; not the duration of the later block reaction."),
    ("ama-amount", "acetal-block-polymer", "AMA charge", 60, "mmol", "60 mmol of AMA", E1, "AMA identity follows the PAMA monomer description; no purity is supplied."),
    ("ama-time", "acetal-block-polymer", "additional block-polymerization stirring", 60, "min", "stirred for an additional 60 min at ambient temperature", E1, "Ambient is qualitative; no numerical temperature assigned."),
    ("peg-segment-mw", "purified-acetal-block-polymer", "PEG segment molecular-weight number", 4200, None, "molecular weights ... PEG and PAMA, were 4200 and 15 800", E1, "Units and separate segment molecular-weight averages are not explicitly stated."),
    ("pama-segment-mw", "purified-acetal-block-polymer", "PAMA segment molecular-weight number", 15800, None, "molecular weights ... PEG and PAMA, were 4200 and 15 800", E1, "Do not substitute the 5000-Mn homopolymer control."),
    ("polymer-dispersity", "purified-acetal-block-polymer", "Mw/Mn", 1.35, "dimensionless", "Mw/Mn = 1.35", E1, "For resulting block copolymer; not a particle-size dispersity."),
    ("hydrolysis-media", "aldehyde-polymer", "acetic acid:water volume ratio", [10, 1], "v/v ratio", "acetic acid/water mixture (10:1 v/v)", E1, "Total mixture volume and polymer amount are unreported."),
    ("hydrolysis-time", "aldehyde-polymer", "acetal hydrolysis stirring duration", 5, "h", "stirred for 5 h at 35 °C", E1, "Explicitly this end-group conversion phase."),
    ("hydrolysis-temperature", "aldehyde-polymer", "acetal hydrolysis temperature", 35, "degC", "stirred for 5 h at 35 °C", E1, "Reactor versus bath reading is unspecified."),
    ("biotin-time", "biotin-polymer", "biocytin-hydrazide reaction time before NaBH4", 2, "h", "reacted for 2 h followed by the addition of NaBH4", E1, "NaBH4 reduction time, amount and temperature are unreported."),
    ("aqueous-volume", "cho-cds-representative", "initial aqueous polymer solution volume", 8, "mL", "To an 8 mL aqueous solution of the block copolymer", E2, "Initial polymer solution, not a known final reaction volume."),
    ("amine-mid", "cho-cds-representative", "initial amine-group concentration", 3.08e-4, "mol/L of amine groups", "3.08 × 10^-4 mol/L as amine concentration in the block copolymer", E2 + EFIG1 + EFIG2, "Not whole-polymer-chain molarity; Figure 2 assigns this concentration to b."),
    ("cdcl2-concentration", "cho-cds-representative", "CdCl2 reported concentration", 2.5e-3, "mol/L", "CdCl2 ... 2.5 × 10^-3 mol/L", E2 + EFIG1, "Stock-versus-final basis and addition volume are not explicitly defined; no added moles derived."),
    ("na2s-concentration", "cho-cds-representative", "Na2S reported concentration", 2.5e-3, "mol/L", "Na2S ... 2.5 × 10^-3 mol/L", E2 + EFIG1, "Added after CdCl2; stock-versus-final basis and addition volume unresolved."),
    ("cds-stir-time", "cho-cds-representative", "coprecipitation stirring duration", 1, "h", "stirred for 1 h at ambient temperature", E2, "Ambient qualitative; speed and addition rate unreported."),
    ("peg-control-mn", "peg-control", "PEG-OH control Mn", 5000, None, "PEG-OH (Mn = 5000)", EFIG1, "Molecular-weight units not printed in caption."),
    ("pama-control-mn", "pama-control", "PAMA homopolymer control Mn", 5000, None, "poly(2-(N,N-dimethylamino)ethyl methacrylate (Mn = 5000)", EFIG1, "Distinct from block-PAMA segment molecular weight 15800."),
    ("amine-low", "cho-cds-low-amine", "initial amine-group concentration", 1.16e-4, "mol/L of amine groups", "1.16 (a) ... × 10^-4 mol/L", EFIG2, "Figure 2 curve a; a formulation variant, not a timed aliquot."),
    ("amine-high", "cho-cds-high-amine", "initial amine-group concentration", 4.62e-4, "mol/L of amine groups", "4.62 (c) × 10^-4 mol/L", EFIG2, "Figure 2 curve c; no independent addition volumes supplied."),
    ("fig2-cds-concentration", "figure2-series", "CdS nominal reported concentration", 2.5e-3, "mol/L", "Fluorescent spectra of CdS (2.5 × 10^-3 mol/L)", EFIG2, "Chemical CdS basis is not a measured QD particle-number concentration."),
    ("fig1-ionic-strength-labels", "salt-challenge", "photograph ionic-strength labels", [0, 0.15, 0.3], None, "I=0; 0.15; 0.3", EFIG1, "Figure labels do not print a unit; surrounding text explicitly describes a 0.3 M NaCl challenge. Do not invent separate mixing volumes."),
    ("salt-stability", "cho-cds-salt-challenge", "NaCl stability challenge concentration", 0.3, "mol/L", "no precipitation ... in the 0.3 M NaCl solution for several days", [ev("main", 2, "Results and Discussion: stabilization controls")], "Duration is 'several days', not an exact number; isolated polymer lot and exact aliquot lineage unspecified."),
    ("uv-cell", "uv-vis-measurement", "quartz cell path length", 1, "cm", "a 1 cm quartz cell", EM, "Shimadzu UV-2400PC."),
    ("pl-excitation", "fluorescence-measurement", "excitation wavelength", 400, "nm", "excitation wavelength of 400 nm", EM + EFIG1 + EFIG2 + EFIG4, "Same nominal excitation setting across stated experiments, not proof of same specimen."),
    ("pl-bandwidths", "fluorescence-measurement", "excitation and emission bandwidths", [2.5, 2.5], "nm", "excitation and emission bandwidths were both 2.5 nm", EM, "Hitachi F-2500; no integration-time or slit-shape details."),
    ("zeta-ph-range", "zeta-measurement", "measurement pH range", [2, 11], "pH", "pH range of 2-11", EM, "Series of measurements, not synthesis pH."),
    ("zeta-nacl", "zeta-measurement", "NaCl measurement electrolyte", 7.5, "mmol/L", "in 7.5 mM NaCl solution", EM, "Different from 0.15 M FRET ionic strength and 0.3 M stability challenge."),
    ("zeta-ph-adjusters", "zeta-measurement", "printed pH-adjuster concentration", 7.5, "mmol/L", "pH was adjusted with 7.5 mM HCl or NaOH", EM, "Retains the shared concentration modifier; additions and final solution volume are unreported."),
    ("absorption-edge", "figure2-absorption-sample-unresolved", "reported absorption edge", 467, "nm", "edge ... was 467 nm", [ev("main", 3, "Results: size estimate", "Figure 2d")], "Absorption edge, not a PL peak or precisely assigned member of a/b/c."),
    ("optical-diameter", "figure2-absorption-sample-unresolved", "band-gap-theory-derived CdS size", 4.8, "nm", "size ... estimated to be 4.8 nm", [ev("main", 3, "Results: Henglein band-gap theory", "Figure 2d; reference 19")], "Author-derived estimate; not a separately quantified TEM size distribution. Original Henglein source not inspected."),
    ("cho-pl-peak", "cho-cds-generic", "reported CdS emission wavelength", 540, "nm", "strong emission spectrum ... at 540 nm", [ev("main", 2, "Results: stabilizer comparison")], "CHO-block-stabilized CdS; no absolute quantum yield supplied."),
    ("biotin-pl-peak", "biotin-cds-generic", "reported biotin-CdS emission wavelength", 540, "nm", "strong emission at 540 nm ... excitation at 400 nm", [ev("main", 4, "Biotin functionalization discussion")], "Separate author claim for biotin variant; not proof of same structural specimen as SI."),
    ("zeta-acid", "zeta-measurement", "reported acidic-region zeta potential", 15, "mV", "positive (= +15 mV)", [ev("main", 3, "Zeta-potential discussion", "Figure 3")], "Region-level value; source does not assign one exact pH in prose."),
    ("zeta-alkaline", "zeta-measurement", "reported alkaline-region zeta potential", -3, "mV", "slightly negative (= -3 mV)", [ev("main", 3, "Zeta-potential discussion", "Figure 3")], "Region-level value, not a fitted isoelectric point."),
    ("fret-ionic-strength", "fret-assay", "ionic strength", 0.15, "mol/L", "I = 0.15 M", EFIG4, "Electrolyte identity/composition for this FRET medium is not specified in caption."),
    ("fret-cds-concentration", "fret-assay", "initial nominal CdS concentration", 396, "micromol/L", "[CdS]0 = 396 µmol/L", EFIG4, "Do not equate CdS molarity with QD particle-number molarity or derive an unreported dilution procedure."),
    ("fret-acceptor-peak", "fret-assay", "TexasRed luminescence wavelength", 620, "nm", "peak at 620 nm is TexasRed luminescence", [ev("main", 4, "FRET discussion", "Figure 4")], "Acceptor emission; no measured energy-transfer efficiency is provided."),
    ("fig4-protein-labels", "figure4-fret-series", "printed TexasRed-streptavidin concentration labels", [11400, 9116, 6837, 4558, 2279, 1593, 912, 228, 159, 91.2, 22.8], "nmol/L", "Tex-Avidin Conc. nmol/L: 11,400 ... 22.8", EFIG4, "Transcribed printed legend, not curve digitization. Text/caption identifies streptavidin while graph abbreviates Tex-Avidin."),
    ("tem-voltage", "si-tem", "EF-TEM operating voltage", 200, "kV", "LEO 922 OMEGA operated at 200kV", ESI, "Sample preparation is air-dried dilute dispersion on film-coated Cu grid."),
    ("tem-scale-bars", "si-tem", "upper/lower TEM scale bars", [50, 20], "nm", "50 nm; 20 nm", [ev("si", 2, "TEM figure", "SI Figure 1")], "Scale bars only; no numerical particle histogram or measured mean transcribed."),
    ("xrd-voltage", "si-xrd", "X-ray tube voltage", 40, "kV", "Cu Kα radiation at 40 kV and 30 mA", ESI, "Shimadzu LabX XRD-6100."),
    ("xrd-current", "si-xrd", "X-ray tube current", 30, "mA", "Cu Kα radiation at 40 kV and 30 mA", ESI, "Instrument setting, not synthesis condition."),
    ("xrd-range", "si-xrd", "2theta scan range", [15, 60], "degree", "2θ values in the range 15-60°", ESI, "Samples freeze-dried and supported on glass slides; no acquisition dwell time supplied."),
    ("xrd-step", "si-xrd", "2theta step size", 0.02, "degree", "in steps of 0.02°", ESI, "No scan speed inferred."),
]:
    Q[key] = q(key, scope, prop, value, unit, raw, evidence, qualifier=qualifier,
               status="author_model_derived" if key == "optical-diameter" else "reported")
Q["abstract-size"] = q("abstract-size", "abstract-biotin-cds", "abstract CdS size", 5, "nm", "ca. 5 nm", [ev("main", 1, "Abstract")], approximate=True, qualifier="Abstract-level biotin-CdS summary; do not create a second measured size label or transfer SI specimen identity.")
Q["acetal-functionality"] = q("acetal-functionality", "purified-acetal-block-polymer", "end-acetal functionality", None, "qualitative", "almost quantitative", E1, status="reported_qualitative", qualifier="Authors state1H NMR analysis; no numerical percentage, spectrum or integrations supplied. Not the functionality of the later biotin end group.")

MATERIALS = []
def material(identifier, name, role, scopes, evidence, formula=None, notes="", supplier=None):
    MATERIALS.append({"id": identifier, "name": name, "formula_as_printed": formula,
                      "role": role, "scope_ids": scopes, "supplier_as_reported": supplier,
                      "purity": None, "pretreatment_storage": "unreported unless explicitly in linked operations",
                      "notes": notes, "evidence": evidence})

for args in [
    ("pdp-alcohol", "corresponding alcohol for potassium 3,3-diethoxypropanolate", "initiator precursor", ["pdp-preparation"], E1, None, "Source says corresponding alcohol; no separate charge/purity and no independently verified upstream preparation."),
    ("potassium-naphthalene", "potassium naphthalene", "initiator-forming reagent", ["pdp-preparation"], E1, None, "Name retained as printed; its own preparation and amount unreported."),
    ("pdp", "potassium 3,3-diethoxypropanolate (PDP)", "polymerization initiator", ["pdp-preparation", "acetal-block-polymer"], E1),
    ("thf", "tetrahydrofuran (THF)", "reaction and Soxhlet extraction medium", ["pdp-preparation", "acetal-block-polymer"], E1),
    ("eo", "condensed ethylene oxide (EO)", "PEG block monomer", ["acetal-block-polymer"], E1, None, "Condensed monomer delivered through cooled syringe.", "Sumitomo Seika, Japan"),
    ("ama", "AMA: 2-(N,N-dimethylamino)ethyl methacrylate monomer", "PAMA block monomer", ["acetal-block-polymer"], E1, None, "AMA abbreviation interpreted from the named polymer; source does not supply a structure drawing.", "Wako Pure Chemical Industries, Osaka, Japan"),
    ("2-propanol", "2-propanol", "polymer precipitation medium", ["acetal-block-polymer"], E1),
    ("protonating-agent-unspecified", "unreported reagent used to protonate the PAMA segment", "polymer cleanup reagent", ["acetal-block-polymer"], E1, None, "Protonation is explicit; reagent identity, amount and conditions are absent. Do not borrow HCl from zeta measurements."),
    ("acetal-peg-pama", "acetal-ended PEG/PAMA block copolymer", "intermediate polymer", ["acetal-block-polymer", "aldehyde-polymer"], E1),
    ("peg-prepolymer", "remaining PEG prepolymer", "removed impurity fraction", ["acetal-block-polymer"], E1, None, "Removed by THF Soxhlet extraction after PAMA protonation; small amount not quantified."),
    ("acetic-acid", "acetic acid", "end-acetal hydrolysis medium", ["aldehyde-polymer", "biotin-polymer"], E1),
    ("water", "water", "hydrolysis, aqueous reaction and dialysis medium", ["aldehyde-polymer", "biotin-polymer", "cho-cds-representative", "biotin-cds"], E1 + E2),
    ("naoh", "sodium hydroxide", "neutralization and measurement pH adjustment", ["aldehyde-polymer", "biotin-polymer", "zeta-assay"], E1 + EM, "NaOH", "The polymer-neutralization charge is absent; the zeta measurement solution is a separate scope."),
    ("cho-peg-pama", "CHO-PEG/PAMA block copolymer", "CdS stabilizer; aldehyde-functional polymer", ["aldehyde-polymer", "cho-cds-representative", "cho-cds-low-amine", "cho-cds-high-amine"], E1 + E2),
    ("biocytin-hydrazide", "biocytin hydrazide", "biotin-installing reagent", ["biotin-polymer"], E1, None, "Source describes biotin with hydrazyl group; amount absent.", "Pierce, U.S.A."),
    ("nabh4", "sodium borohydride", "Schiff-base reduction reagent", ["biotin-polymer"], E1, "NaBH4", "Amount, reduction time, workup and temperature absent."),
    ("biotin-peg-pama", "biotin-PEG/PAMA block copolymer", "biotin-functional CdS stabilizer", ["biotin-polymer", "biotin-cds"], E1 + E2),
    ("cdcl2", "cadmium chloride", "Cd precursor", ["cho-cds-representative", "biotin-cds", "no-polymer-control", "peg-control", "pama-control"], E2 + EFIG1, "CdCl2", "Hydration state not specified; do not insert hydrate water.", "Wako, Japan"),
    ("na2s", "sodium sulfide", "S precursor", ["cho-cds-representative", "biotin-cds", "no-polymer-control", "peg-control", "pama-control"], E2 + EFIG1, "Na2S", "Hydration state not specified.", "Wako, Japan"),
    ("peg-oh", "PEG-OH", "homopolymer stabilizer control", ["peg-control"], EFIG1, None, "Commercially available; Mn=5000, no concentration or exact supplier provided."),
    ("pama-homopolymer", "poly(2-(N,N-dimethylamino)ethyl methacrylate) homopolymer", "polyamine stabilizer control", ["pama-control"], EFIG1, None, "Mn=5000; preparation not supplied."),
    ("nacl", "sodium chloride", "stability challenge; zeta electrolyte", ["salt-challenge", "zeta-assay"], EM + [ev("main", 2, "Results: salt stability")], "NaCl"),
    ("hcl", "hydrochloric acid", "zeta measurement pH adjuster", ["zeta-assay"], EM, "HCl"),
    ("texasred-streptavidin", "TexasRed-labeled streptavidin", "FRET acceptor protein conjugate", ["fret-assay", "streptavidin-competition", "bsa-control"], EFIG4, None, "Conjugation preparation, dye loading per protein and supplier are not given; graph abbreviates Tex-Avidin."),
    ("streptavidin", "streptavidin without TexasRed probe", "specific competitive-binding control", ["streptavidin-competition"], [ev("main", 4, "Inhibition discussion", "Figure 5")]),
    ("bsa", "bovine serum albumin without TexasRed probe", "nonspecific protein control", ["bsa-control"], [ev("main", 4, "Inhibition discussion", "Figure 5")]),
    ("cds", "cadmium sulfide", "intended and reported inorganic product", ["cho-cds-representative", "biotin-cds"], E2, "CdS", "Formula molarity is not QD particle-number molarity."),
    ("tem-grid", "formval film-coated Cu grid", "TEM support", ["tem-preparation"], ESI, None, "Source spelling 'formval' retained; not silently corrected to a named film formulation."),
    ("glass-slide", "glass slides", "XRD support", ["xrd-preparation"], ESI),
    ("polymer-only-xrd", "PEG/PAMA without CdS", "XRD sample-preparation comparator", ["xrd-preparation"], ESI, None, "Methods name this sample as freeze-dried, but supplied SI Figure 2 has no separately identified polymer-only trace."),
]:
    material(*args)

PROTOCOLS = []
def op(identifier, action, inputs, output, facts=None, conditions=None, retained=None, discarded=None, unknowns=None):
    return {"id": identifier, "action": action, "input_material_ids": inputs, "output_state_id": output,
            "quantity_fact_ids": facts or [], "conditions": conditions or {},
            "retained_fraction": retained, "discarded_fraction": discarded,
            "unreported_fields": unknowns or []}


def protocol(identifier, title, category, evidence, operations, inherited=None, notes=""):
    PROTOCOLS.append({"id": identifier, "title": title, "category": category,
                      "record_granularity": "source-described preparation/measurement scope, not a verified independent batch",
                      "evidence": evidence, "operations": operations,
                      "inherited_framework": inherited, "notes": notes,
                      "independent_audit_status": "pending", "training_admission": "not_assessed"})

protocol("pdp-preparation", "PDP initiator preparation", "upstream_preparation", E1, [
    op("pdp-form", "React the corresponding alcohol with potassium naphthalene in THF to prepare PDP solution.", ["pdp-alcohol", "potassium-naphthalene", "thf"], "pdp-solution", [Q["pdp-amount"], Q["thf-volume"]], unknowns=["separate reagent charges", "duration", "temperature", "atmosphere", "potassium-naphthalene preparation"])
], notes="Present-paper summary of cited polymer methods14a/14b; neither external reference's full procedure was inspected.")
protocol("acetal-block-polymer", "Sequential EO/AMA block-polymer preparation and cleanup", "polymer_preparation", E1, [
    op("eo-add", "Add condensed EO to the PDP solution via a cooled syringe.", ["pdp", "thf", "eo"], "eo-reaction-mixture", [Q["eo-amount"]], {"delivery": "cooled syringe"}, unknowns=["syringe temperature", "addition rate", "reaction temperature", "atmosphere"]),
    op("eo-react", "Allow EO reaction for two days before adding AMA.", ["eo"], "peg-prepolymer-reaction-mixture", [Q["eo-time"]], unknowns=["reaction temperature", "stirring speed"]),
    op("ama-block", "Add AMA to that reaction mixture and stir for an additional60min at ambient temperature.", ["ama"], "acetal-block-reaction-mixture", [Q["ama-amount"], Q["ama-time"]], {"temperature": {"value": None, "raw_text": "ambient temperature", "status": "reported_qualitative"}}, unknowns=["addition rate", "numerical temperature", "stirring speed"]),
    op("polymer-precipitate", "Recover block copolymer by precipitation into a large excess of2-propanol.", ["2-propanol", "acetal-peg-pama"], "precipitated-acetal-block-polymer", conditions={"precipitant_quantity": "large excess"}, retained="precipitated-acetal-block-polymer", discarded="mother-liquor-uncharacterized", unknowns=["2-propanol volume", "collection method", "drying", "yield"]),
    op("pama-protonate", "Protonate the PAMA segment before THF Soxhlet extraction.", ["acetal-peg-pama", "protonating-agent-unspecified"], "protonated-acetal-block-polymer", unknowns=["protonating reagent", "amount", "temperature", "duration"]),
    op("soxhlet-clean", "Remove the small remaining PEG-prepolymer amount by Soxhlet extraction with THF.", ["thf", "peg-prepolymer", "acetal-peg-pama"], "purified-acetal-block-polymer", retained="purified-acetal-block-polymer", discarded="thf-extract-containing-peg-prepolymer", unknowns=["extraction duration", "THF volume", "drying", "isolated yield"]),
], notes="Recovered material has segment molecular-weight numbers4200/15800 and Mw/Mn1.35. End-acetal functionality reported almost quantitative by1H NMR, without a spectrum, integration values or numerical percentage.")
protocol("aldehyde-polymer", "Acetal-to-aldehyde conversion of PEG/PAMA", "polymer_functionalization", E1, [
    op("hydrolyze-acetal", "Dissolve block polymer in acetic acid/water10:1v/v and stir5h at35°C.", ["acetal-peg-pama", "acetic-acid", "water"], "aldehyde-polymer-acid-mixture", [Q["hydrolysis-media"], Q["hydrolysis-time"], Q["hydrolysis-temperature"]], unknowns=["polymer amount", "total solvent volume"]),
    op("neutralize", "Neutralize with NaOH after reaction.", ["naoh"], "neutralized-cho-peg-pama-mixture", unknowns=["NaOH concentration/charge", "endpoint pH"]),
    op("dialyze-polymer", "Dialyze against water.", ["water", "cho-peg-pama"], "cho-peg-pama-in-water", retained="cho-peg-pama-in-water", discarded="diffusible-solutes-not-identified", unknowns=["membrane/MWCO", "duration", "exchange volumes/frequency", "temperature", "final concentration", "yield", "storage"]),
])
protocol("biotin-polymer", "Biotin installation before polymer dialysis", "polymer_functionalization", E1, [
    op("biotin-condense", "Before the dialysis stage, add biocytin hydrazide and react for2h.", ["biocytin-hydrazide", "cho-peg-pama"], "biotin-schiff-base-polymer-mixture", [Q["biotin-time"]], unknowns=["hydrazide/polymer amounts", "pH", "temperature", "site conversion"]),
    op("biotin-reduce", "Add NaBH4 to reduce the formed Schiff base.", ["nabh4"], "biotin-peg-pama-mixture", unknowns=["NaBH4 charge", "reduction duration/temperature", "quench"]),
    op("biotin-dialysis-context", "The biotin branch is inserted before the stated water-dialysis step; the paper gives no separately detailed biotin-polymer purification.", ["water", "biotin-peg-pama"], "biotin-peg-pama-preparation", retained="biotin-peg-pama-preparation", unknowns=["independently specified dialysis conditions", "final concentration", "biotin functionality", "storage"]),
], inherited={"from": "aldehyde-polymer", "scope": "aldehyde precursor and before-dialysis insertion point", "status": "source-described branch; no quantitative charges inherited"}, notes="Ligand installation precedes CdS formation in this study. Post-CdS conjugation is discussed as an alternative, not performed here.")
protocol("cho-cds-representative", "CHO-PEG/PAMA-stabilized aqueous CdS coprecipitation", "cds_synthesis", E2, [
    op("polymer-medium", "Place8mL aqueous block-copolymer solution in a glass vial.", ["water", "cho-peg-pama"], "aqueous-cho-polymer-medium", [Q["aqueous-volume"], Q["amine-mid"]], {"vessel": "glass vial"}, unknowns=["polymer mass/chain concentration", "pH", "vial capacity"]),
    op("cd-add", "Add CdCl2 first.", ["cdcl2"], "cadmium-polymer-mixture", [Q["cdcl2-concentration"]], unknowns=["addition volume", "stock/final concentration basis", "rate", "mixing"]),
    op("s-add", "Add Na2S after CdCl2.", ["na2s"], "cds-coprecipitation-mixture", [Q["na2s-concentration"]], unknowns=["addition volume", "stock/final concentration basis", "rate"]),
    op("cds-stir", "Stir for1h at ambient temperature.", ["cds", "cho-peg-pama"], "cho-polymer-cds-dispersion", [Q["cds-stir-time"]], {"temperature": {"value": None, "raw_text": "ambient temperature", "status": "reported_qualitative"}}, unknowns=["temperature number", "atmosphere", "stirring speed"]),
    op("cds-dialyze", "Purify by dialysis against water.", ["water", "cds", "cho-peg-pama"], "dialyzed-cho-cds-dispersion", retained="dialyzed-cho-cds-dispersion", discarded="diffusible-solutes-not-identified", unknowns=["membrane/MWCO", "duration", "water exchanges", "temperature", "yield", "final volume/concentration", "storage"]),
])
protocol("biotin-cds", "Biotin-PEG/PAMA-stabilized CdS", "cds_synthesis", E2 + [ev("main", 4, "Biotin route selection")], [
    op("biotin-cds-coprecipitate", "Prepare in a similar manner using biotin-PEG/PAMA instead of CHO-PEG/PAMA.", ["biotin-peg-pama", "cdcl2", "na2s", "water"], "biotin-cds-dispersion", unknowns=["independently stated biotin-polymer concentration/charges", "exact batch linkage", "biotin surface density"])
], inherited={"from": "cho-cds-representative", "scope": "qualitative coprecipitation/dialysis framework", "status": "reported similar manner, not independently quantified run"})
for identifier, polymer, outcome in [
    ("no-polymer-control", None, "CdS precipitates; authors attribute this to crystal growth."),
    ("peg-control", "peg-oh", "Commercial PEG-OH does not prevent precipitation under the tested conditions."),
    ("pama-control", "pama-homopolymer", "Transparent pale-yellow low-salt dispersion; increased salt causes immediate precipitation; almost no emission at400nm excitation."),
]:
    protocol(identifier, identifier.replace("-", " "), "stabilizer_control", EFIG1 + [ev("main", 2, "Results: stabilizer controls")], [
        op(identifier + "-prepare", "Coprecipitate CdCl2 with Na2S using the indicated stabilizer condition.", ["cdcl2", "na2s", "water"] + ([polymer] if polymer else []), identifier + "-sample", [Q["cdcl2-concentration"], Q["na2s-concentration"]] + ([Q["amine-mid"], Q["pama-control-mn"]] if polymer == "pama-homopolymer" else [Q["peg-control-mn"]] if polymer == "peg-oh" else []), unknowns=["independent reaction volumes", "exact workup", "number of repeats"])
    ], inherited={"from": "cho-cds-representative", "scope": "coprecipitation comparison; no automatic transfer of all procedure details"}, notes=outcome)
for identifier, fact, label in [("cho-cds-low-amine", Q["amine-low"], "a"), ("cho-cds-high-amine", Q["amine-high"], "c")]:
    protocol(identifier, "CHO-PEG/PAMA concentration variant " + label, "concentration_variant", EFIG2, [
        op(identifier + "-prepare", "Prepare CdS using the Figure2 initial amine-group concentration; preserve this as a formulation variant.", ["cho-peg-pama", "cdcl2", "na2s", "water"], identifier + "-sample", [fact, Q["fig2-cds-concentration"]], unknowns=["independent addition volumes", "exact batch-to-curve mapping beyond label", "yield"])
    ], inherited={"from": "cho-cds-representative", "scope": "reported common aqueous preparation; concentration explicitly replaced", "status": "framework_inherited"})

protocol("salt-challenge", "Salt-dependent dispersion controls", "measurement_preparation", EFIG1 + [ev("main", 2, "Results: stability")], [
    op("salt-expose", "Compare prepared dispersions under the three Figure1 ionic-strength labels; text explicitly reports0.3M NaCl stability for several days for the block-copolymer CdS.", ["nacl", "cds", "cho-peg-pama", "pama-homopolymer", "peg-oh"], "salt-challenged-comparison-samples", [Q["fig1-ionic-strength-labels"], Q["salt-stability"]], unknowns=["salt addition volumes", "time of each photo/spectrum", "separate exposure duration for each control", "precise sample lineage"])
], notes="Controls remain separate material conditions. The photographs are not independent synthesis replicates; NaCl challenge is not a reagent input for the base synthesis.")
protocol("zeta-assay", "pH-dependent zeta-potential measurement", "measurement_preparation", EM + [ev("main", 3, "Figure3 and discussion")], [
    op("zeta-medium", "Measure CdS zeta potential in7.5mM NaCl across pH2-11, adjusting with7.5mM HCl or NaOH.", ["cds", "nacl", "hcl", "naoh"], "ph-series-measurement-samples", [Q["zeta-ph-range"], Q["zeta-nacl"], Q["zeta-ph-adjusters"]], {"instrument": "LEZA-600, Otsuka Electric Co., Japan"}, unknowns=["exact Figure2 member", "sample concentration", "titration order", "temperature", "equilibration time"])
])
protocol("fret-assay", "Biotin-CdS/TexasRed-streptavidin recognition assay", "recognition_assay", EFIG4 + [ev("main", 4, "FRET discussion", "Figure6")], [
    op("fret-mix", "Mix biotinylated CdS QD with TexasRed-streptavidin and acquire fluorescence at400nm excitation.", ["cds", "biotin-peg-pama", "texasred-streptavidin"], "biotin-cds-texasred-streptavidin-mixtures", [Q["fret-ionic-strength"], Q["fret-cds-concentration"], Q["fig4-protein-labels"], Q["pl-excitation"]], unknowns=["mixture volumes", "buffer/electrolyte identity", "incubation time", "temperature", "protein dye labeling ratio", "exact dialysis/dilution lineage"])
], notes="Figure4 contains spectra; Figure6 contains concentration-response plots, including an inset with different axes/scales. Exact point-to-spectrum joins are not supplied.")
for identifier, protein, finding in [
    ("streptavidin-competition", "streptavidin", "Unlabeled streptavidin reduces FRET; interpreted as specific competition."),
    ("bsa-control", "bsa", "Small BSA addition slightly increases FRET; further BSA has little effect, according to prose. Excluded-volume explanation is the authors' interpretation, not a measured mechanism."),
]:
    protocol(identifier, identifier.replace("-", " "), "recognition_control", [ev("main", 4, "Inhibition discussion", "Figure5")], [
        op(identifier + "-premix", "Premix biotinylated CdS with the indicated nonlabeled protein, then add TexasRed-streptavidin and monitor FRET.", ["cds", "biotin-peg-pama", protein, "texasred-streptavidin"], identifier + "-mixtures", unknowns=["protein addition volumes", "mixing/incubation times", "unambiguous varied concentration identity", "fixed TexasRed-streptavidin concentration"])
    ], inherited={"from": "fret-assay", "scope": "Figure5 caption says conditions same as Figure4", "status": "caption-inherited common settings only"}, notes=finding + " Figure5 caption/text/axis concentration identity is unresolved and retained as contradiction C2.")
protocol("tem-preparation", "Air-dried TEM grid preparation", "measurement_preparation", ESI, [
    op("tem-grid-dry", "Place a drop of dilute sample solution on a formval-film-coated Cu grid and allow it to dry in air.", ["cds", "tem-grid"], "air-dried-tem-grid", conditions={"instrument": "energy-filtered TEM LEO922 OMEGA"}, facts=[Q["tem-voltage"]], retained="air-dried-tem-grid", unknowns=["dilution factor", "drop volume", "drying duration", "source dispersion batch"])
])
protocol("xrd-preparation", "Freeze-dried PEG/PAMA and PEG/PAMA-CdS powder specimens", "measurement_preparation", ESI, [
    op("xrd-freeze-dry", "Freeze-dry samples of PEG/PAMA and PEG/PAMA-CdS, then support them on glass slides.", ["polymer-only-xrd", "cds", "glass-slide"], "freeze-dried-xrd-specimens", retained="freeze-dried-xrd-specimens", unknowns=["freeze-drying duration/temperature", "loading mass", "dispersion batch", "separate polymer-only diffraction trace"]),
    op("xrd-scan", "Measure with a vertical goniometer using CuKα radiation.", ["glass-slide", "cds"], "xrd-pattern", [Q["xrd-voltage"], Q["xrd-current"], Q["xrd-range"], Q["xrd-step"]], {"instrument": "Shimadzu LabX XRD-6100 automated powder diffractometer"}, unknowns=["dwell time", "scan rate", "reference-stick provenance"])
])

SAMPLES = [
    {"id": "cho-cds-representative", "protocol_id": "cho-cds-representative", "state": "water-dialyzed dispersion", "link_status": "explicit preparation description", "measurement_scope": "Representative conditions are compatible with Figure1d and Figure2b; identity of an actual common batch is unreported."},
    {"id": "no-polymer-control", "protocol_id": "no-polymer-control", "state": "precipitated CdS comparison", "link_status": "explicit Figure1a control", "measurement_scope": "Three ionic-strength photographs; failure retained."},
    {"id": "peg-control", "protocol_id": "peg-control", "state": "PEG-OH/CdS precipitating comparison", "link_status": "explicit Figure1b control", "measurement_scope": "Three ionic-strength photographs; failed stabilization retained."},
    {"id": "pama-control", "protocol_id": "pama-control", "state": "low-salt dispersion; high-salt precipitate", "link_status": "explicit Figure1c/e control", "measurement_scope": "Figure1e PL scale differs substantially from Figure1f; no quantum yield inferred."},
    {"id": "cho-cds-salt-challenge", "protocol_id": "salt-challenge", "state": "salt-challenged CHO-PEG/PAMA-CdS dispersions", "link_status": "explicit Figure1d/f material/control relation; batches unreported", "measurement_scope": "I=0,0.15,0.3 photographs and PL spectra; no time trace or independent replicate claim."},
    {"id": "cho-cds-low-amine", "protocol_id": "cho-cds-low-amine", "state": "aqueous CHO-PEG/PAMA-CdS", "link_status": "explicit Figure2a concentration label", "measurement_scope": "1.16e-4mol/L amine groups."},
    {"id": "cho-cds-mid-amine", "protocol_id": "cho-cds-representative", "state": "aqueous CHO-PEG/PAMA-CdS", "link_status": "explicit Figure2b concentration; same-batch relation to representative preparation unknown", "measurement_scope": "3.08e-4mol/L amine groups."},
    {"id": "cho-cds-high-amine", "protocol_id": "cho-cds-high-amine", "state": "aqueous CHO-PEG/PAMA-CdS", "link_status": "explicit Figure2c concentration label", "measurement_scope": "4.62e-4mol/L amine groups."},
    {"id": "figure2-absorption-sample-unresolved", "protocol_id": None, "state": "optical solution specimen", "link_status": "unresolved exact a/b/c member", "measurement_scope": "Figure2d absorption edge467nm and author-model size4.8nm; not a measured size for all variants."},
    {"id": "zeta-series", "protocol_id": "zeta-assay", "state": "pH-adjusted dispersion", "link_status": "Figure3 says same sample as Figure2 without identifying a/b/c/d", "measurement_scope": "No coagulation reported across pH range; point-level pH values not digitized."},
    {"id": "biotin-cds-generic", "protocol_id": "biotin-cds", "state": "biotin-PEG/PAMA-CdS dispersion", "link_status": "explicit biotin route and qualitative540nm PL claim", "measurement_scope": "No batch-specific TEM/XRD or biotin-loading number supplied."},
    {"id": "figure4-fret-series", "protocol_id": "fret-assay", "state": "biotin-CdS/protein assay mixtures", "link_status": "explicit formula-CdS concentration and printed protein concentration series", "measurement_scope": "Spectral series; unreported replicate count and exact aliquot lineage."},
    {"id": "figure5-competition-series", "protocol_id": "streptavidin-competition", "state": "competition mixtures", "link_status": "protein identity by filled-symbol legend; concentration variable ambiguous", "measurement_scope": "No exact individual concentrations/intensities transcribed from curves."},
    {"id": "figure5-bsa-series", "protocol_id": "bsa-control", "state": "BSA control mixtures", "link_status": "protein identity by open-symbol legend; concentration variable ambiguous", "measurement_scope": "Separate biological control, not failed CdS synthesis."},
    {"id": "figure6-response-series", "protocol_id": "fret-assay", "state": "concentration-response assay series", "link_status": "same assay family; exact Figure4 point joins unverified", "measurement_scope": "Main plot μmol/L, inset nmol/L; no regression coefficients or detection limit supplied."},
    {"id": "si-tem-grid", "protocol_id": "tem-preparation", "state": "air-dried dilute-dispersion deposit on Cu grid", "link_status": "caption identifies PEG/PAMA-CdS; functional end-group and batch unspecified", "measurement_scope": "Two images with50/20nm bars; no particle histogram or exact lattice-spacing measurement."},
    {"id": "si-xrd-cds", "protocol_id": "xrd-preparation", "state": "freeze-dried PEG/PAMA-CdS on glass slide", "link_status": "caption identifies PEG/PAMA-CdS; no exact biotin/CHO concentration-series join", "measurement_scope": "Author assigns hexagonal wurtzite using SI trace. No CIF, refined atomic coordinates or measured lattice parameters."},
    {"id": "si-xrd-polymer", "protocol_id": "xrd-preparation", "state": "freeze-dried PEG/PAMA on glass slide", "link_status": "sample named in SI methods; no separately identified supplied trace", "measurement_scope": "Do not invent polymer-background subtraction or label sharp peaks without evidence."},
]
for sample in SAMPLES:
    sample.update(independent_audit_status="pending", unique_experiment_verified=False, training_eligible=False)

MEASUREMENTS = [
    {"id": "uv-vis-measurement", "technique": "UV-vis absorption", "instrument": "Shimadzu UV-2400PC", "sample_ids": ["figure2-absorption-sample-unresolved"], "quantity_fact_ids": [Q["uv-cell"], Q["absorption-edge"]], "evidence": EM + EFIG2, "data_status": "original plot and reported edge retained; curve not digitized"},
    {"id": "fluorescence-measurement", "technique": "steady-state fluorescence", "instrument": "Hitachi F-2500", "sample_ids": ["pama-control", "cho-cds-salt-challenge", "cho-cds-low-amine", "cho-cds-mid-amine", "cho-cds-high-amine", "figure4-fret-series"], "quantity_fact_ids": [Q["pl-excitation"], Q["pl-bandwidths"]], "evidence": EM + EFIG1 + EFIG2 + EFIG4, "data_status": "reported peaks and printed concentration labels only; no raw spectra, QY or transfer efficiency"},
    {"id": "zeta-measurement", "technique": "zeta potential", "instrument": "LEZA-600 (Otsuka Electric Co.)", "sample_ids": ["zeta-series"], "quantity_fact_ids": [Q["zeta-ph-range"], Q["zeta-nacl"], Q["zeta-ph-adjusters"], Q["zeta-acid"], Q["zeta-alkaline"]], "evidence": EM + [ev("main", 3, "Zeta potential", "Figure3")], "data_status": "region-level author values and original plot; no fitted pKa or isoelectric point"},
    {"id": "si-tem", "technique": "energy-filtered TEM", "instrument": "LEO922 OMEGA", "sample_ids": ["si-tem-grid"], "quantity_fact_ids": [Q["tem-voltage"], Q["tem-scale-bars"]], "evidence": ESI + [ev("si", 2, "TEM", "Figure1")], "data_status": "original two-view image; no particle sizing/digitization, diffraction pattern or atom coordinates"},
    {"id": "si-xrd", "technique": "powder X-ray diffraction", "instrument": "Shimadzu LabX XRD-6100", "sample_ids": ["si-xrd-cds", "si-xrd-polymer"], "quantity_fact_ids": [Q["xrd-voltage"], Q["xrd-current"], Q["xrd-range"], Q["xrd-step"]], "evidence": ESI + [ev("si", 3, "XRD", "Figure2")], "data_status": "one plotted PEG/PAMA-CdS trace and unlabeled reference sticks; no indexed peak table or refinement"},
    {"id": "polymer-nmr", "technique": "1H NMR end-acetal functionality assessment", "instrument": None, "sample_ids": [], "quantity_fact_ids": [], "evidence": E1, "data_status": "authors report almost quantitative end-acetal functionality; no spectrum, field strength, solvent, integrations or percentage supplied"},
]

CONTRADICTIONS = [
    {"id": "C1", "topic": "Figure2 polymer-concentration/PL trend", "evidence": EFIG2, "source_claim": "Prose states that increasing block-copolymer concentration increased emission intensity along with a hypochromic shift.", "visual_observation": "Caption assigns a=1.16,b=3.08,c=4.62×10^-4mol/L; printed a/b/c arrow orders the spectra from larger to smaller plotted amplitudes. The highest amplitude is labeled a and lowest c.", "resolution": "Unresolved source discrepancy. Preserve caption values, curve labels, image and prose separately; do not reverse concentrations, correct the word hypochromic, or create a monotonic concentration-to-size rule."},
    {"id": "C2", "topic": "Figure5 varied protein concentration", "evidence": [ev("main", 4, "Inhibition prose and plot", "Figure5")], "source_claim": "Caption calls the abscissa TexasRed-streptavidin concentration, while prose describes changing nonlabeled streptavidin/BSA in inhibition experiments.", "visual_observation": "Abscissa reads10^-5 Protein Conc.(mol/L), with filled/nonfilled symbols assigned to nonlabeled streptavidin/BSA in the caption.", "resolution": "Do not decide which protein concentration varies or populate quantitative competitive-binding rows until separately resolved."},
    {"id": "C3", "topic": "Figure6 proportionality and intensity scales", "evidence": [ev("main", 4, "Concentration response", "Figure6")], "source_claim": "Authors describe FRET peak as increasing proportionally with TexasRed-streptavidin concentration.", "visual_observation": "Main plotted response is curved over its displayed micromolar range. Inset is approximately linear over a lower nanomolar range, and its arbitrary intensity scale differs from the main plot.", "resolution": "Retain as qualitative author conclusion plus original plots. No global linear model, calibration slope, exact limit of detection or cross-panel intensity normalization is extracted."},
    {"id": "C4", "topic": "Protein name in figure axes", "evidence": EFIG4 + [ev("main", 4, "Concentration response", "Figure6")], "source_claim": "Text and captions identify TexasRed-streptavidin.", "visual_observation": "Graph labels abbreviate Tex-Avidin/Tex-Av Conc.", "resolution": "Use streptavidin according to explicit text/caption; retain the original graph labels and do not create an additional avidin reagent or claim equivalence of the proteins."},
]

GAPS = [
    {"id": "G1", "scope": "pdp-preparation/acetal-block-polymer", "missing": "Separate initiator reagent charges, EO-stage temperature, atmosphere, addition rates, PAMA protonating reagent, precipitation/extraction volumes and durations, yields/drying/storage.", "impact": "Present paper has an operational summary, not a fully reproducible upstream polymer SOP. References14a/14b are cited but their full texts were not inspected."},
    {"id": "G2", "scope": "aldehyde-polymer/biotin-polymer", "missing": "Polymer/solvent charges, neutralization endpoint, biocytin-hydrazide and NaBH4 amounts, reduction duration/temperature, exact purified biotin-polymer concentration and biotin functionality.", "impact": "Do not infer stoichiometry, quantitative biotin coverage, reduction conditions or yield."},
    {"id": "G3", "scope": "all dialysis operations", "missing": "Membrane/MWCO, time, water-exchange schedule, temperature, final volume/concentration, recovered yield and storage.", "impact": "Final material is an incompletely specified dialyzed dispersion; no invented isolated powder preparation."},
    {"id": "G4", "scope": "CdS coprecipitation", "missing": "CdCl2/Na2S solution-addition volumes and unequivocal stock-versus-final concentration basis, hydration state, pH, numerical ambient temperature, atmosphere, speed and addition rates.", "impact": "Do not multiply2.5mM by8mL to assert an added reagent charge or total yield;8mL is the initial polymer-solution volume."},
    {"id": "G5", "scope": "comparison and concentration variants", "missing": "Independent whole-batch records, exact workup and specimen links, replicate counts and outcomes per salt/concentration combination.", "impact": "Variants/photographs are not verified independent experiments or a timing sequence."},
    {"id": "G6", "scope": "optical/structural sample links", "missing": "Which Figure2 concentration supplies absorption trace d, Figure3 specimen, SI TEM or SI XRD; whether SI samples are biotin-ended.", "impact": "No exact recipe-to-structure, biotin-to-TEM, or structure-to-FRET join. Nominal same material is insufficient."},
    {"id": "G7", "scope": "size and atomistic structure", "missing": "TEM particle counts/histogram, measured mean and distribution, indexed XRD peak table, lattice parameters, refinements, atom coordinates/CIF, defect or facet determination.", "impact": "4.8nm remains an author band-gap-derived estimate; hexagonal wurtzite is an author powder-diffraction assignment, not a refined atomistic model."},
    {"id": "G8", "scope": "recognition assays", "missing": "Buffer/electrolyte composition, volumes, incubation times, temperature, dye labeling ratio, exact sample dilution lineage, background corrections, repeats/errors, QY/FRET efficiency and detection limit.", "impact": "Preserve original arbitrary intensity plots and printed concentration labels without inventing calibration or protein-count-per-QD values."},
    {"id": "G9", "scope": "SI acquisition", "missing": "TEM drop/dilution/drying numbers, XRD freeze-drying/loading details, dwell/scan rate, provenance and indexing of reference sticks, separately labeled polymer-only XRD trace.", "impact": "No assignment of sharp XRD features to polymer/impurity and no background subtraction inferred."},
    {"id": "G10", "scope": "external cited sources", "missing": "Full primary procedures/data from references cited in this paper.", "impact": "Bibliography is inventoried as cited context only; full8-page coverage applies only to the supplied main and matched SI. No extra papers downloaded or opened."},
]

INTERPRETATIONS = [
    {"id": "author-coordination", "claim": "PAMA multivalent surface coordination and PEG steric stabilization explain dispersion stability.", "status": "original_authors_interpretation", "evidence": [ev("main", 2, "Results: polymer stabilization"), ev("main", 3, "Results continuation and zeta discussion")], "limits": "No measured grafting density, surface-site stoichiometry or quantitative binding constants supplied."},
    {"id": "author-segregation", "claim": "PAMA/PEG segregation is proposed to strengthen PAMA attachment by minimizing interfacial free energy.", "status": "original_authors_proposal", "evidence": [ev("main", 2, "Results ending"), ev("main", 3, "Opening continuation")], "limits": "Retain source's 'probably' character; no free-energy calculation supplied."},
    {"id": "author-size-control", "claim": "Polymer coordination controls CdS crystallization growth; authors link concentration-dependent spectral changes to size.", "status": "original_authors_interpretation_with_source_conflict", "evidence": EFIG2, "limits": "C1 prevents turning this into a validated monotonic quantitative relationship."},
    {"id": "author-phase", "claim": "Obtained PEG/PAMA-CdS shows characteristic hexagonal wurtzite powder-XRD peaks.", "status": "source_reported_phase_assignment", "evidence": [ev("main", 3, "XRD discussion"), ev("si", 3, "XRD", "Figure2")], "limits": "No unit-cell/atom refinement or independently resolved exact-sample association."},
    {"id": "author-fret", "claim": "620nm emission arises through CdS-to-TexasRed FRET enabled by biotin-streptavidin recognition.", "status": "original_authors_interpretation_supported_by_reported_controls", "evidence": [ev("main", 4, "Recognition discussion", "Figures4-6")], "limits": "No transfer efficiency, distance, lifetime or donor/acceptor stoichiometry supplied."},
    {"id": "author-bsa", "claim": "BSA slightly enhances approach through an excluded-volume effect.", "status": "original_authors_interpretation", "evidence": [ev("main", 4, "BSA discussion", "Figure5; reference22")], "limits": "No measured excluded-volume parameter; external reference22 not inspected."},
    {"id": "outlook", "claim": "Authors propose sensitive bioanalysis, simultaneous dyes/wide excitation and potentially high-throughput specific-protein detection.", "status": "original_authors_proposed_application", "evidence": [ev("main", 1, "Abstract"), ev("main", 2, "Introduction ending"), ev("main", 5, "Conclusion")], "limits": "No demonstrated multiplexing, clinical detection validation or numerical sensitivity limit in supplied sources."},
]

REFERENCES_RAW = [
    ("1", "Bruchez, M., Jr.; Moronne, M.; Gin, P.; Weiss, S.; Alivisatos, A.P. Science1998,281,2013.", 1, "biolabeling precedent"),
    ("2", "Chan, W.C.; Nie, S. Science1998,281,2016.", 1, "biolabeling precedent"),
    ("3", "Sondi, I.; Siiman, O.; Koester, S.; Matijevic, E. Langmuir2000,16,3107.", 1, "bioanalytical context"),
    ("4", "Wu, X.; Liu, H.; Liu, J.; Haley, K.N.; Treadway, J.A.; Larson, J.P.; Ge, N.; Peale, F.; Bruchez, M.P. Nat.Biotechnol.2003,21(4),452.", 1, "bioanalytical context"),
    ("5", "Jaiswal, J.K.; Mattoussi, H.; Mauro, J.M.; Simon, S.M. Nat.Biotechnol.2003,21(1),47.", 1, "bioanalytical context"),
    ("6", "Taylor, J.R.; Fang, M.M.; Nie, S. Anal.Chem.2000,72,1979.", 1, "bioanalytical context"),
    ("7", "Huang, J.; Sooklal, K.; Murphy, C.J.; Ploehn, H.J. Chem.Mater.1999,11,3595.", 1, "polymer/polyamine stabilization context"),
    ("8", "Sooklal, K.; Hanus, L.H.; Ploehn, H.J.; Murphy, C.J. Adv.Mater.1998,10(14),1083-1087.", 1, "polymer-supported QD context"),
    ("9", "Kumbhojkar, N.; Mahamuni, S.; Leppert, V.; Risbud, S.H. Nanostruct.Mater.1998,10(2),117-129.", 1, "polymer-supported QD context"),
    ("10", "Qi, L.; Colfen, H.; Antonietti, M. NanoLett.2001,1,61.", 1, "PEI/PEG-stabilized CdS coprecipitation precedent; not this paper's block-polymer recipe"),
    ("12", "Otsuka, H.; Akiyama, Y.; Nagasaki, Y.; Kataoka, K. J.Am.Chem.Soc.2001,123,8226.", 1, "CHO-PEG-SH/gold precedent; gold route not performed here"),
    ("13", "Ishii, T.; Nagasaki, Y.; Otsuka, O.; Kataoka, K. Langmuir2004,20(3),561.", 2, "CHO-PEG/PAMA-gold precedent; author initial O retained as printed"),
    ("14a", "Nagasaki, Y.; Sato, Y.; Kato, M. Macromol.RapidCommun.1997,18(9),827.", 2, "cited upstream polymer method"),
    ("14b", "Kataoka, K.; Harada, A.; Wakebayashi, D.; Nagasaki, Y. Macromolecules1999,32(20),6892.", 2, "cited upstream polymer method; name retained as printed"),
    ("15", "Kuno, M.; Lee, J.K.; Dabbousi, B.O.; Mikulec, F.V.; Bawendi, M.G. J.Chem.Phys.1997,106,9869.", 2, "surface-charge/photoluminescence context"),
    ("16a", "Moore, D.E.; Patel, K. Langmuir2001,17,2541.", 2, "PL activation context"),
    ("16b", "Zhang, Z.; Dai, S.; Fan, X.; Blom, D.A.; Pennycook, S.J.; Wei, Y. J.Phys.Chem.B2001,105(29),6755-6758.", 2, "PL activation context"),
    ("16c", "Elbaum, R.; Vega, S.; Hodes, G. Chem.Mater.2001,13(7),2272.", 2, "PL activation context"),
    ("16d", "Farmer, S.C.; Patten, T.E. Chem.Mater.2001,13(11),3920.", 2, "PL activation context"),
    ("17", "Fogg, D.E.; Radzilowski, L.H.; Blanski, R.; Schrock, R.R.; Thomas, E.L. Macromolecules1997,30(3),417.", 2, "electron-donor coordination/PL precedent"),
    ("18", "Veinot, J.G.C.; Galloro, J.; Pugliese, L.; Bell, V.; Pestrin, R.; Pietro, W.J. Can.J.Chem.1998,76(11),1530.", 2, "electron-donor coordination/PL precedent"),
    ("19", "Henglein, A. Chem.Rev.1989,89,1961.", 3, "band-gap theory cited for4.8nm size; equation not reproduced"),
    ("20", "Mamedova, N.N.; Kotov, N.A.; Rogach, A.L.; Studer, J. NanoLett.2001,1,281-286.", 4, "albumin/CdTe energy-transfer precedent; distinct experimental system"),
    ("21", "Willard, D.M.; Carillo, L.L.; Jung, J.; Orden, A.V. NanoLett.2001,1(9),469.", 4, "biotinylated albumin/CdSe-ZnS and tetramethylrhodamine-streptavidin precedent; distinct from current CdS route"),
    ("22", "Ortega-Vinuesa, J.L.; Molina-Bolivar, J.A.; Hidalgo-Alvarez, R. J.Immunol.Methods1996,190,29.", 4, "excluded-volume interpretation context"),
]
REFERENCES = [{"id": "reference-" + label, "printed_label": label, "bibliography_as_printed_normalized_spacing": citation,
               "use_in_current_paper": scope, "evidence": [ev("main", page, "References", label)],
               "access_level": "bibliographic citation and current authors' summary only; external full text not inspected",
               "supplies_current_recipe_missing_fields": False} for label, citation, page, scope in REFERENCES_RAW]

FIGURES = [
    {"id": "main-figure1", "role": "main", "page": 3, "label": "Figure1a-f", "rect": [.08, .052, .925, .384], "sample_ids": ["no-polymer-control", "peg-control", "pama-control", "cho-cds-salt-challenge"], "content": "a: no polymer; b:PEG-OH Mn5000; c:PAMA Mn5000; d:CHO-PEG/PAMA; e:PL of c; f:PL of d. Three salt conditions pictured, with e/f emission axes separately scaled.", "axes_and_labels": {"photo_I": [0, .15, .3], "PL_wavelength_nm_ticks": [400,450,500,550,600,650,700], "e_intensity_ticks_au": [0,1,2,3,4,5], "f_intensity_ticks_au": [0,200,400,600,800,1000]}, "disposition": "full original figure/caption retained; qualitative controls and reported settings extracted; no spectra digitized"},
    {"id": "main-figure2", "role": "main", "page": 3, "label": "Figure2a-d", "rect": [.08, .386, .493, .674], "sample_ids": ["cho-cds-low-amine", "cho-cds-mid-amine", "cho-cds-high-amine", "figure2-absorption-sample-unresolved"], "content": "Three PL concentration variants with right intensity axis; absorption trace d with left absorbance axis. Caption concentration mapping retained despite C1.", "axes_and_labels": {"wavelength_nm_ticks": [300,400,500,600,700], "absorbance_ticks": [0,.4,.8,1.2], "PL_intensity_ticks_au": [0,100,200,300,400], "curves": {"a": "1.16e-4mol/L amine", "b": "3.08e-4mol/L amine", "c": "4.62e-4mol/L amine", "d": "UV-vis absorption; exact concentration member unresolved"}}, "disposition": "full original figure/caption, edge/size author facts, C1 retained; no curve-derived sizes"},
    {"id": "main-figure3", "role": "main", "page": 3, "label": "Figure3", "rect": [.51, .386, .917, .606], "sample_ids": ["zeta-series"], "content": "Zeta potential versus pH, with a dashed zero line. Caption's same-sample link to Figure2 is not member-specific.", "axes_and_labels": {"pH_ticks": [1,2,3,4,5,6,7,8,9,10,11], "zeta_mV_ticks": [-10,-5,0,5,10,15]}, "disposition": "original plot/caption and region-level +15/-3mV prose retained; individual points not digitized"},
    {"id": "main-figure4", "role": "main", "page": 4, "label": "Figure4", "rect": [.08, .05, .494, .362], "sample_ids": ["figure4-fret-series"], "content": "CdS donor and TexasRed acceptor spectra at the printed protein concentrations; CdS396µmol/L,I0.15M,excitation400nm.", "axes_and_labels": {"wavelength_nm_ticks": [400,500,600,700], "intensity_au_ticks": [0,40,80,120,160], "protein_legend_fact": Q["fig4-protein-labels"]}, "disposition": "full original figure/caption and all11 printed concentration labels retained; no raw curve digitization"},
    {"id": "main-figure5", "role": "main", "page": 4, "label": "Figure5", "rect": [.51, .051, .917, .286], "sample_ids": ["figure5-competition-series", "figure5-bsa-series"], "content": "Filled circles nonlabeled streptavidin, open circles nonlabeled BSA. Varied-concentration identity unresolved between axis, caption and prose.", "axes_and_labels": {"x_as_printed": "10^-5 Protein Conc.(mol/L)", "x_tick_numbers": [0,1,2,3,4,5], "y_as_printed": "FRET intensity(a.u.)", "y_ticks": [0,100,200,300,400,500,600,700,800,900]}, "disposition": "full original plot/caption and C2 retained; no numeric competition curve exported"},
    {"id": "main-figure6", "role": "main", "page": 4, "label": "Figure6 and inset", "rect": [.51, .294, .917, .506], "sample_ids": ["figure6-response-series"], "content": "Concentration-response plot and low-concentration inset; preserve differing main/inset intensity scales and source proportionality claim.", "axes_and_labels": {"main_x": "Tex-Avidin Conc.(µmol/L)", "main_x_ticks": [0,2,4,6,8,10,12], "main_y_ticks_au": [0,.5,1,1.5,2,2.5,3,3.5], "inset_x": "Tex-Av Conc.(nmol/L)", "inset_x_ticks": [0,50,100,150,200,250], "inset_y_ticks_au": [0,20,40,60,80,100,120]}, "disposition": "full original plot/inset/caption retained; no fit/slope/LOD or exact Figure4 point joins"},
    {"id": "si-figure1", "role": "si", "page": 2, "label": "SI Figure1 (two views)", "rect": [.29, .12, .72, .763], "sample_ids": ["si-tem-grid"], "content": "Two original PEG/PAMA-CdS TEM views with50nm upper and20nm lower scale bars.", "axes_and_labels": {"scale_bar_nm": [50,20]}, "disposition": "both images and caption retained; no measured particle population statistics or exact biotin linkage"},
    {"id": "si-figure2", "role": "si", "page": 3, "label": "SI Figure2", "rect": [.28, .145, .73, .44], "sample_ids": ["si-xrd-cds"], "content": "PEG/PAMA-CdS powder diffractogram with reference sticks; no labeled hkl/phase card or separate polymer-only trace.", "axes_and_labels": {"x": "2θ(degree)", "x_ticks": [20,30,40,50,60], "y": "intensity(a.u.)", "indexed_peak_table": None}, "disposition": "original trace, sticks, axes and caption retained; author wurtzite assignment separately sourced to mainp3"},
]

STOCKS = [
    {"id": "pdp-thf-solution", "solute": "pdp", "solvent": "thf", "preparation_protocol": "pdp-preparation", "reported_fact_ids": [Q["pdp-amount"], Q["thf-volume"]], "concentration": None, "concentration_status": "not explicitly stated; no volume-additivity derivation performed", "storage": "unreported"},
    {"id": "aqueous-polymer-medium", "solute": "cho-peg-pama", "solvent": "water", "preparation_protocol": "cho-cds-representative", "reported_fact_ids": [Q["aqueous-volume"], Q["amine-mid"]], "concentration_basis": "amine groups; not whole chains", "stock_preparation_details": "unreported", "storage": "unreported"},
    {"id": "cdcl2-na2s-concentration-statements", "components": ["cdcl2", "na2s"], "reported_fact_ids": [Q["cdcl2-concentration"], Q["na2s-concentration"]], "stock_status": "source concentration statements; not verified stock formulations", "solvent_and_final_volume": "aqueous overall method; separate stock composition/volumes unresolved"},
]

OBSERVATIONS = [
    {"sample_ids": ["no-polymer-control", "peg-control"], "outcome": "precipitation in the tested control conditions", "status": "reported_unsuccessful_stabilization", "evidence": [ev("main", 2, "Results: controls")] + EFIG1},
    {"sample_ids": ["pama-control"], "outcome": "transparent pale-yellow low-salt solution; immediately precipitates at increased salt; almost no PL at400nm excitation", "status": "reported_partial_success_with_failure_condition", "evidence": [ev("main", 2, "Results: controls")] + EFIG1},
    {"sample_ids": ["cho-cds-salt-challenge"], "outcome": "strong PL and no precipitation in0.3M NaCl for several days", "status": "reported_qualitative_success", "evidence": [ev("main", 2, "Results: controls")] + EFIG1},
    {"sample_ids": ["cho-cds-low-amine", "cho-cds-mid-amine", "cho-cds-high-amine"], "outcome": "solutions transparent throughout the tested concentration region; PL trend contains C1", "status": "reported_qualitative_observation_with_conflict", "evidence": EFIG2},
    {"sample_ids": ["zeta-series"], "outcome": "no coagulation over the measured pH region despite changing zeta potential", "status": "reported_qualitative_observation", "evidence": [ev("main", 3, "Zeta discussion", "Figure3")]},
    {"sample_ids": ["figure4-fret-series", "figure6-response-series"], "outcome": "TexasRed620nm emission grows with labeled-protein concentration under400nm excitation", "status": "reported_qualitative_response", "evidence": [ev("main", 4, "FRET discussion", "Figures4,6")]},
    {"sample_ids": ["figure5-competition-series", "figure5-bsa-series"], "outcome": "streptavidin inhibits FRET; BSA does not inhibit and initially gives a slight enhancement", "status": "reported_control_result_with_concentration_ambiguity", "evidence": [ev("main", 4, "Inhibition discussion", "Figure5")]},
]

PAGE_CONTENT = {
    "main": {
        1: ["title, six authors, affiliations/correspondence footnotes, received/revised/publication dates and DOI", "abstract includingca.5nm and0.15M assay summary", "introduction and distinct cited gold/CdS/polymer precedents", "references1-10,12 and substantive reference-note11"],
        2: ["introduction continuation", "Experimental1: initiator/block-polymer preparation, workup, molecular-weight numbers, aldehyde and biotin modifications", "Experimental2: representative CdS and similar-manner biotin variant across columns", "Experimental3: UV-vis/fluorescence/zeta acquisition", "Results: no-polymer,PEG,PAMA and block-polymer controls, salt stability and coordination interpretation", "references13,14a-b,15,16a-d,17,18"],
        3: ["Figures1a-f,2a-d,3 and all captions/axes/labels", "PL concentration conflictC1 and original hypochromic wording", "467nm edge, Henglein-derived4.8nm, qualitative TEM agreement and author wurtzite assignment", "zeta interpretation and uncertain Figure2 linkage", "ligand-installation alternatives begin", "reference19"],
        4: ["ligand alternatives continue; pre-CdS biotin installation selected", "biotin540nm PL", "FRET, inhibition and concentration-response assays", "Figures4,5,6 with legends,inset,captions and conflictsC2-C4", "distinct cited CdTe/CdSe-ZnS precedents", "conclusion begins", "references20-22"],
        5: ["conclusion continuation", "acknowledgment/funder", "supporting-information declaration naming PEG/PAMA-CdS TEM and XRD", "manuscript IDLA036034C and printed page6400"],
    },
    "si": {
        1: ["Supporting information heading", "complete EF-TEM instrument/settings and air-dried grid preparation", "complete XRD instrument/settings and freeze-dried specimen preparation"],
        2: ["SI Figure1 upper/lower TEM images", "50nm/20nm bars", "full PEG/PAMA-CdS caption"],
        3: ["SI Figure2 trace, reference sticks and all visible axes", "full PEG/PAMA-CdS caption", "absence of indexed peak numbers, reference-card identity and separately labeled polymer-only trace"],
    },
}


def render_assets():
    out = HERE / "reader-assets"
    out.mkdir(exist_ok=True)
    assets = []
    qa_path = out / "visual-qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.exists() else {"assets": []}
    inspected = {item["id"]: item for item in qa["assets"]}
    for figure in FIGURES:
        role = figure["role"]
        document = pdfium.PdfDocument(DOCS[role]["path"])
        page = document[figure["page"] - 1]
        try:
            w, h = page.get_size()
            left, top, right, bottom = figure["rect"]
            crop = (left * w, (1 - bottom) * h, (1 - right) * w, top * h)
            bitmap = page.render(scale=3.0, crop=crop)
            image = bitmap.to_pil()
            target = out / (figure["id"] + ".png")
            image.save(target)
            record = {"id": figure["id"], "path": str(target), "sha256": sha(target),
                      "source_role": role, "source_sha256": DOCS[role]["sha256"], "pdf_page": figure["page"],
                      "label": figure["label"], "crop_rectangle_fraction_top_origin": figure["rect"],
                      "crop_rectangle_pdf_points_top_origin": [left*w,top*h,right*w,bottom*h],
                      "pdf_canvas_size": [w,h], "render_scale": 3.0, "pixel_size": list(image.size),
                      "creation": "PDFium clipped rendering from unchanged original PDF; no retouching/redrawing",
                      "visual_verification": "pending", "data_status": "source image, not raw curve digitization"}
            if record["id"] in inspected and inspected[record["id"]]["sha256"] == record["sha256"]:
                record["visual_verification"] = "passed_by_extracting_reader"
                record["visual_verification_evidence"] = str(qa_path)
            assets.append(record)
            image.close()
            bitmap.close()
        finally:
            page.close()
            document.close()
    return assets


def build():
    for d in DOCS.values():
        assert sha(d["path"]) == d["sha256"], "Source changed; refuse extraction release"
    batch_manifest = json.loads((HERE.parent / "intake-manifest.json").read_text(encoding="utf-8"))
    batch_paper = next(item for item in batch_manifest["papers"] if item["paper_id"] == "10.1021_la036034c")
    original_copies = []
    for item in batch_paper["file_copies"]:
        actual = sha(item["source_path"])
        assert actual == item["sha256"], "An original duplicate copy changed"
        original_copies.append({**item, "actual_sha256_reverified": actual, "reverified_at": NOW,
                                "same_contents_not_extra_pages_or_experiments": True})
    assets = render_assets()
    for figure in FIGURES:
        figure["evidence"] = [ev(figure["role"], figure["page"], "Original figure and caption", figure["label"])]
        figure["asset_id"] = figure["id"]
        figure.pop("rect", None)
    coverage = {"schema": "mattersyn-page-coverage/1", "source_id": SOURCE_ID, "doi": "10.1021/la036034c", "reviewer": REVIEWER,
                "reviewed_at": NOW, "scope": "All5 main and3 matched SI pages text-read and visually inspected for source extraction; independent scientific audit pending.",
                "documents": [], "totals": {"main_pages": 5, "si_pages": 3, "text_read_pages": 8, "visually_inspected_pages": 8, "source_pages_uninspected": 0},
                "figure_inventory_complete": True, "scientific_audit_complete": False,
                "raw_plot_digitization_performed": False, "external_reference_full_texts_reviewed": 0}
    for role, doc in DOCS.items():
        pages=[]
        for number, topics in PAGE_CONTENT[role].items():
            text_path = HERE/f"{role}-{number:02d}.txt"
            render_path = HERE/f"{role}-{number:02d}.png"
            pages.append({"pdf_page": number, "printed_page": str(6395+number) if role=="main" else None,
                          "text_read": True, "visual_inspection": True, "reviewer": REVIEWER,
                          "text_cache": str(text_path), "text_sha256": sha(text_path),
                          "render_cache": str(render_path), "render_sha256": sha(render_path),
                          "covered_content": topics, "remaining_page_coverage_gap": None})
        coverage["documents"].append({"role":role,"original_path":doc["path"],"original_filename":doc["filename"],"source_sha256":doc["sha256"],"hash_reverified_at":NOW,"page_count":doc["page_count"],"pages":pages})
    sourcefacts = {"schema": "mattersyn-full-source-extraction/1", "revision": 1, "source_id": SOURCE_ID,
                  "group_id": "10.1021_la036034c", "source_generation": 2, "doi": "10.1021/la036034c",
                  "title": "Novel Molecular Recognition via Fluorescent Resonance Energy Transfer Using a Biotin-PEG/Polyamine Stabilized CdS Quantum Dot",
                  "authors": ["Yukio Nagasaki","Takehiko Ishii","Yuka Sunaga","Yousuke Watanabe","Hidenori Otsuka","Kazunori Kataoka"],
                  "bibliography": {"journal":"Langmuir","year":2004,"volume":20,"issue":15,"pages":"6396-6400","received":"2003-10-29","final_form":"2004-03-23","published_web":"2004-06-18"},
                  "extracted_by": REVIEWER, "extracted_at":NOW, "source_sha256":DOCS["main"]["sha256"], "si_sha256":DOCS["si"]["sha256"],
                  "scope":"Complete supplied main+matched SI source extraction, with original plots retained and all uncertain joins/quantities explicit. No independent scientific audit or canonical/training admission claimed.",
                  "original_file_copies": original_copies,
                  "facts": FACTS,"materials":MATERIALS,"stocks":STOCKS,"protocols":PROTOCOLS,"samples":SAMPLES,"measurements":MEASUREMENTS,
                  "observations":OBSERVATIONS,"author_interpretations_and_outlook":INTERPRETATIONS,
                  "figures":FIGURES,"references":REFERENCES,"contradictions":CONTRADICTIONS,"gaps":GAPS,
                  "unperformed_options":[{"id":"post-cds-ligand-installation","description":"Conjugating ligand to PEG aldehyde ends after CdS formation is discussed as an alternative; authors explicitly select ligand installation before CdS preparation.","evidence":[ev("main",3,"Ligand alternatives"),ev("main",4,"Selected ligand route")],"status":"discussed_not_performed","recipe_conditions":None}],
                  "structure_status":{"reported_phase":"hexagonal wurtzite CdS","basis":"authors' powder-XRD assignment, mainp3/SIp3","exact_measured_atomic_coordinates":False,"CIF_supplied":False,"external_structure_imported":False,"verified_recipe_structure_sample_join":False},
                  "completion":{"full_supplied_source_extraction":True,"independent_full_scientific_audit":False,"original_plot_digitization":False,"canonical_recipe_admission":False,"site_integration":False,"publication":False},
                  "training_status":{"eligible_records":0,"reason":"Independent audit and task-specific canonical eligibility pending; missing charges/sample joins cannot be filled from related records."}}
    source_units = []
    for protocol_item in PROTOCOLS:
        source_units.append({"id":protocol_item["id"],"kind":protocol_item["category"],"title":protocol_item["title"],"disposition":"extracted_with_reported_conditions_and_explicit_missingness","evidence":protocol_item["evidence"]})
    for measurement in MEASUREMENTS:
        source_units.append({"id":measurement["id"],"kind":"measurement","title":measurement["technique"],"disposition":measurement["data_status"],"evidence":measurement["evidence"]})
    for fact in FACTS:
        if fact["source_unit_id"] not in {unit["id"] for unit in source_units}:
            source_units.append({"id": fact["source_unit_id"], "kind": "reported_fact_scope",
                                 "title": fact["source_unit_id"].replace("-", " "),
                                 "disposition": "typed source facts retained with scope, evidence and missingness",
                                 "evidence": fact["evidence"]})
    administrative = [
        {"id":"identity-and-dates","kind":"bibliographic_identity","evidence":[ev("main",1,"Title/authors/header/footer")],"disposition":"extracted title,six authors,journal,dates and DOI"},
        {"id":"author-footnotes","kind":"administrative_footnotes","evidence":[ev("main",1,"Correspondence and affiliation footnotes")],"disposition":"inspected; Tokyo University of Science/University of Tokyo affiliations and Otsuka present-address note retained as source context; contact details are not chemical recipe data"},
        {"id":"reference-note11","kind":"substantive_reference_note","evidence":[ev("main",1,"Reference note11")],"disposition":"authors state the prior PEG/PEI polymer is graft, not block, despite the prior article's wording; retained as author correction, no independent verification of prior paper"},
        {"id":"acknowledgment","kind":"administrative","evidence":[ev("main",5,"Acknowledgment")],"disposition":"Special Coordination Funds, Ministry of Education, Science and Sports, Japan; no recipe condition"},
        {"id":"si-declaration","kind":"source_relationship","evidence":[ev("main",5,"Supporting Information Available")],"disposition":"declared PEG/PAMA-CdS TEM and XRD match supplied SI content and embedded manuscript identifier"},
        {"id":"inline-math","kind":"mathematical_expressions","evidence":[ev("main",2,"Methods"),ev("main",3,"Figures and Results"),ev("main",4,"Assays"),ev("si",1,"XRD")],"disposition":"typed concentrations,exponents,Mw/Mn,zeta signs and2theta settings retained; no numbered/display equations or derivation of band-gap sizing is supplied"},
    ]
    inventory={"schema":"mattersyn-source-inventory/1","source_id":SOURCE_ID,"created_at":NOW,"reviewer":REVIEWER,
               "documents":coverage["documents"],"original_file_copies":original_copies,"pairing":{"status":"matched and previously independently audited for intake","review_file":str(HERE/"pairing-review.json"),"basis":"main explicitly announces PEG/PAMA-CdS TEM/XRD; SI supplies those exact contents and metadata containsla036034csi","caveat":"SI omits article title/authors; it does not establish biotin-specific specimen identity"},
               "source_units":source_units,"figures":FIGURES,"tables":[],"schemes":[],"displayed_or_numbered_equations":[],
               "absence_scope":"All8 supplied pages visually inspected; no tables,schemes or displayed/numbered equations found. Inline expressions and plotted labels are retained in facts/figures.",
               "references":REFERENCES,"administrative_and_footnote_units":administrative,"assets":assets,
               "counts":{"documents":2,"original_file_copies":len(original_copies),"source_pages":8,"materials":len(MATERIALS),"protocol_scopes":len(PROTOCOLS),"source_units":len(source_units),"sample_scopes":len(SAMPLES),"measurement_types":len(MEASUREMENTS),"typed_facts":len(FACTS),"figures":8,"figure_crops":len(assets),"tables":0,"schemes":0,"displayed_numbered_equations":0,"bibliographic_entries":len(REFERENCES),"numbered_reference_groups":21,"substantive_reference_notes":1,"contradiction_or_interpretation_flags":len(CONTRADICTIONS),"explicit_gap_groups":len(GAPS)},
               "independent_scientific_audit_status":"pending","source_originals_modified":False,"live_ledger_modified":False,"site_modified":False}
    for filename, data in [("source-facts.json",sourcefacts),("source-inventory.json",inventory),("page-coverage.json",coverage)]:
        (HERE/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    notes=["# Nagasaki2004 source extraction", "", "DOI10.1021/la036034c; Langmuir20,6396-6400. Private extraction by/root/backlog_eta; independent full scientific audit pending.", "",
           "All five main pages and three matched SI pages were read as text and visually inspected. Source SHA256 values were rechecked against the intake manifest before rendering evidence crops. The separate pairing audit is retained; this extraction does not claim its own independent audit.", "",
           "The inventory preserves initiator/block-polymer preparation, acetal-to-aldehyde and biotin branches, representative aqueous CdS synthesis, stabilizer controls, concentration variants, salt/pH tests, FRET and inhibition assays, and TEM/XRD specimen preparation. Protocol scopes and specimen/measurement series are not counts of independently replicated experiments.", "",
           "## Quantities and specimen boundaries", "",
           "The initial aqueous polymer medium is8mL with3.08e-4mol/L AMINE GROUPS. CdCl2 and Na2S are reported at2.5e-3mol/L and added in that order; their volumes and stock/final basis are unresolved. Do not derive20µmol reagent charges from the8mL polymer volume. Ambient stirring is1h, followed by water dialysis with missing membrane/time/exchange details.", "",
           "Biotin is installed on the polymer before CdS formation in the selected route. The biotin variant is described as prepared similarly; it is not a separately quantified run. The SI captions identify generic PEG/PAMA-CdS, with air-dried TEM and freeze-dried XRD specimens. They do not resolve biotin end-group identity, a Figure2 concentration member, or the exact assay sample. The4.8nm size is author-derived from the467nm absorption edge via cited band-gap theory; no new particle measurement or distribution was generated.", "",
           "## Source discrepancies preserved", ""]
    notes += ["- "+c["id"]+": "+c["topic"]+". "+c["resolution"] for c in CONTRADICTIONS]
    notes += ["", "## Coverage and missingness", "", "All six main figures and two SI figures have clipped original-PDF renders with source hashes and page/crop locators. Legends,scale bars,axes,captions and the Figure6 inset are retained. These are images, not raw curve digitization. No supplied tables,schemes,numbered equations,CIF,refined atomic coordinates,absolute PLQY or measured FRET efficiency were found.", "", "All25 individual bibliographic entries (21 numbered groups) and substantive note11 are inventoried. Cited preparations,theories and other-material examples remain separate context; no external reference full text was opened and no missing field was imported. Ten gap groups detail missing charges,workup/acquisition settings,protein assay composition and unresolved sample links.", "", "Outputs: source-facts.json,source-inventory.json,page-coverage.json,reader-assets/*.png. Scientific admission,integration and publication remain pending.", ""]
    (HERE/"extraction-notes.md").write_text("\n".join(notes),encoding="utf-8")
    print(json.dumps(inventory["counts"]))


if __name__ == "__main__":
    build()
