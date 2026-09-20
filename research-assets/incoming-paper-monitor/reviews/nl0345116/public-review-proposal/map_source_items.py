from pathlib import Path
import json
B=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
pairs='''identity-title|identity
identity-authors|identity acknowledgments
identity-journal|identity
identity-dates|identity administrative
identity-administrative|administrative
overview-chemistry|lead-source selenium tbp injection heated-growth
overview-spheres|sphere-series sphere-morphology
overview-wires|wire-overview wire-intermediate wire-high
overview-properties|conductivity interaction-energy
context-nanocrystals|prior-nanocrystals
context-devices|prior-nanocrystals motivation
context-assemblies|assembly-literature
context-bulk|bulk-context
context-prior-optics|literature-optical
context-prior-intraband|literature-optical
context-prior-murray|prior-synthesis
context-prior-coreshell|prior-synthesis
context-prior-template|prior-synthesis
context-current-techniques|microscopy-method absorption-method electrical-method structure-boundary
context-intro-dimensions|intro-dimensions
precursor-lead|lead-source
precursor-selenium|selenium
precursor-tbp|tbp
precursor-topo|topo
precursor-argon|argon
precursor-workup|quench-solvents
precursor-supports|grid-materials device-materials
stock-prepare|stock-preparation
stock-low|low-stock
stock-medium|intermediate-stock
stock-high|high-stock
stock-scale-missing|tbp missing-fields
protocol-mother|mother-solution
protocol-inject|injection
protocol-low-hold|individual-growth
protocol-heated|heated-growth
protocol-sample|aliquot-quench
protocol-separate|purification
protocol-purify|purification
protocol-sampling-boundary|aliquot-quench individual-growth
method-hrsem|microscopy-method device-sem
method-tem|microscopy-method
method-hrtem|microscopy-method
method-grid|microscopy-preparation
method-absorption|absorption-method
method-electrical|electrical-method
device-substrate|device-surface device-materials
device-markers|device-surface
device-deposit|device-positioning
device-select|device-positioning
device-resist|device-positioning
device-contacts|device-contacts
device-inspect|device-contacts
device-contact-caution|contact-optimization
individual-size|individual-morphology
individual-shape|individual-morphology
individual-structure|individual-hrtem
sphere-series|sphere-series
sphere-diameter|sphere-morphology
sphere-diffraction|sphere-saed
sphere-kinetics|sphere-growth
wire-medium|wire-intermediate wire-image
wire-high|wire-high
wire-caption-conflict|wire-intermediate ratio-conflicts
wire-diffraction|wire-saed
wire-helix|wire-orientation
wire-orientation|wire-orientation
wire-intermediate|wire-overview wire-orientation
wire-bent|bent-wire
optical-cohorts|absorption-cohorts
optical-bands|absorption-spectrum absorption-shift
optical-interpretation|absorption-shift
electric-cohorts|electrical-specimens
electric-field|iv-curves conductivity
electric-conductivity|conductivity
electric-scope|high-stock wire-high
mechanism-assembly-control|assembly-controls motivation
mechanism-spacing|spacing
mechanism-coupling|coupling-boundary
mechanism-redshift|absorption-shift ligand-heating
mechanism-quantum|absorption-shift permanent-dipoles
mechanism-dipole-origin|permanent-dipoles
mechanism-thermodynamics|entropy
mechanism-time|heated-growth kinetic-ordering
mechanism-impurities|topo-impurities
mechanism-transport|transport-options
equation-dipole|dipole-equation
equation-interaction|interaction-energy
equation-free-energy|entropy
equation-field|internal-field
equation-dielectric|internal-field model-limits
equation-capacitance|capacitance
equation-lifetime|transfer-energy
equation-transfer|transfer-energy
equation-drop|barrier
model-field|internal-field
model-capacitance|capacitance
model-transfer|transfer-energy
model-barrier|barrier
model-comparisons|conductivity-comparators
model-outlook|outlook electrical-scope terminology-conflicts
summary-ratio-conflict|ratio-conflicts low-stock
summary-assembly|sphere-series wire-intermediate wire-high
summary-support|acknowledgments
figure-1a|individual-hrtem
figure-1bcd|sphere-morphology sphere-series
figure-1e|sphere-saed
figure-1f|sphere-growth
figure-2a|wire-image wire-orientation
figure-2b|wire-image wire-intermediate
figure-2c|wire-saed
figure-3|bent-wire
figure-4|absorption-cohorts absorption-spectrum
figure-5a|device-materials device-surface
figure-5b|device-sem
figure-5c|electrical-method device-contacts
figure-5d|iv-curves electrical-specimens'''
mapping={'sashchiuk2004-'+k:v.split() for k,v in (row.split('|') for row in pairs.splitlines())}
mapping.update({f'sashchiuk2004-reference-{n:02}':[f'reference-{n:02}'] for n in range(1,68)})
audit=json.loads((B/'source-audit.json').read_text(encoding='utf8'));expected={u['id'] for u in audit['units']}
assert set(mapping)==expected,{'missing':sorted(expected-set(mapping)),'extra':sorted(set(mapping)-expected)}
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Mapped',len(mapping),'units')
