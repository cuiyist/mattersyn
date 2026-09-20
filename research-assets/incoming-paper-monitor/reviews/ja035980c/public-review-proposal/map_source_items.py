from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
TEXT='''
identity-title|identity
identity-authors|identity source-context
identity-journal|identity
identity-dates|identity source-context
identity-administrative|source-context
abstract-product|mwnt crystal-phase
abstract-approach|tdpa-competition figure8-model
abstract-methods|coverage property-limits
context-cnt-properties|assembly-context
context-assembly|assembly-context
context-applications|assembly-context outlook
context-functionalization|chemistry-context
context-heterostructures|chemistry-context
context-previous-cdse-tio2|prior-cdse
context-previous-limitation|prior-cdse
context-coordination|coordination-context
context-ligand-role|mwnt shape-variables figure8-model
context-transport-outlook|outlook
context-generalization|outlook
precursor-mwnt|mwnt
precursor-oxidant|oxidants
precursor-hcl|hcl
precursor-hf|hf
precursor-wash-water|water
precursor-oxidized-mwnt|surface-groups
precursor-cdo|cdo
precursor-tdpa|tdpa tdpa-competition
precursor-topo|topo
precursor-te-top|te-top
precursor-argon|argon
precursor-toluene|toluene
precursor-methanol|methanol
precursor-filter|ptfe
precursor-analysis-media|ethanol dmf uv-preparation
protocol-oxidation|oxidative-treatment hcl-treatment hf-treatment
protocol-wash-dry|water-wash dry-nanotubes
protocol-purification-result|purification-evidence oxidative-treatment
protocol-mix-heat|precursor-mixing precursor-heating
protocol-substoich-rationale|tdpa-competition
protocol-injection|te-injection
protocol-growth|growth
protocol-heat-off|cooling
protocol-dilution|toluene-addition
protocol-precipitate|precipitation
protocol-filter|filtration
protocol-toluene-wash|toluene-washing
protocol-final-dry|product-drying
method-tem-preparation|tem-preparation
method-tem|tem-acquisition
method-hrtem|hrtem-acquisition
method-sem-preparation|sem-preparation
method-sem|sem-acquisition
method-xps-preparation|xps-mounting
method-xps-survey|xps-survey
method-xps-high-resolution|xps-high-resolution
method-xrd|xrd-acquisition
method-uvvis-instrument|uv-acquisition
method-uvvis-preparation|uv-preparation
method-ftir|ir-acquisition
method-raman|raman-acquisition
morphology-oxidation|oxidation-morphology figure1
morphology-sites|surface-groups site-selectivity
morphology-purity|purification-evidence
morphology-tip-density|site-selectivity figure2-sem figure2-tem
morphology-etched-layers|site-selectivity
morphology-sidewall|figure2-tem prior-cdse
morphology-junctions|figure2-sem figure2-tem figure4-junction property-limits
morphology-eds-elements|eds-elements
morphology-lattice|figure3-interface crystal-phase
morphology-elongated-tip|figure3-sites
morphology-defect|figure3-sites
morphology-edge|figure3-sites figure3-interface
growth-diffusion|diffusion-model
growth-steric|diffusion-model
growth-free-size|free-particle-size
growth-bound-size|particle-dimensions
growth-heterogeneity|shape-variables
growth-spacing|shape-variables
growth-controls|control-scope oxidation-coverage
growth-oxygen-high|oxidation-coverage
growth-oxygen-low|oxidation-coverage
growth-coverage-correlation|oxidation-coverage
xrd-phase|crystal-phase
xrd-broadening|xrd-broadening
xrd-indexing|xrd-indexing
xps-carbon|surface-xps
xps-cadmium|surface-xps
xps-tellurium|teo3
xps-passivation|passivation-model
xps-thermal-carboxyl|thermal-context
raman-cdte|raman-cdte
raman-bulk-reference|raman-cdte
raman-g-band|raman-carbon
raman-d-band|raman-carbon
optical-hybrid|uv-heterostructure
optical-background|uv-heterostructure
optical-washings|uv-washings free-particle-size
optical-detachment|uv-washings detachment-model
optical-anisotropy|diffusion-model detachment-model
conclusion-scope|quantum-confinement figure8-model
conclusion-swnt-limit|mwnt-swnt
conclusion-outlook|outlook
conclusion-support|funding
si-declaration|si-identity
figure-1a|figure1
figure-1b|figure1
figure-1c|figure1
figure-1d|figure1
figure-2a|figure2-sem
figure-2b|figure2-sem
figure-2c|figure2-tem
figure-2d|figure2-tem
figure-2e|figure2-tem
figure-3a|figure3-interface
figure-3b|figure3-sites
figure-3c|figure3-sites
figure-3d|figure3-sites
figure-4a|figure4-junction
figure-4b|figure4-junction
figure-4c|figure4-junction
figure-4-eds|eds-elements eds-unit-conflict
figure-5i-carbon|surface-xps figure5-xps
figure-5i-oxygen|figure5-xps
figure-5i-cadmium|surface-xps figure5-xps
figure-5i-tellurium|teo3 figure5-xps
figure-5ii|xrd-indexing crystal-phase
figure-6|figure6
figure-7|figure7
figure-8|figure8-model
si-identity|si-identity
si-infrared|si-ir
si-limits|si-ir coverage
source-completeness|coverage missing-fields structure-limit data-precision
'''
mapping={f'banerjee2003-{u}':t.split() for line in TEXT.splitlines() if line.strip() for u,t in [line.split('|')]}
mapping.update({f'banerjee2003-reference-{n:02}':[f'reference-{n:02}'] for n in range(1,44)})
audit=json.loads((B/'source-audit.json').read_text(encoding='utf8'));expected={u['id'] for u in audit['units']};assert set(mapping)==expected,(set(mapping)-expected,expected-set(mapping))
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Mapped',len(mapping),'source units')
