"""Explicit semantic source-unit coverage; never based on substring similarity."""
from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
pairs='''
identity identity-dates | identity
identity-affiliation | identity-affiliation
abstract-01 | ag-diameter-range
abstract-02 | heat
abstract-03 | why-arrested
abstract-04 | dispersibility
abstract-05 | coagulation-condensation
context-01 | background-properties
context-02 | why-arrested why-supercritical
context-03 | why-supercritical
context-04 | environmental-context conflict-temperature
context-05 | why-fluorinated
context-06 | why-arrested why-fluorinated
context-07 | optical-c10 chain-length
context-08 | historical-claim
context-09 | prior-film-deposition
chemical-ag | chemical-ag
chemical-ir | chemical-ir
chemical-pt | chemical-pt
chemical-ligand | chemical-ligand
chemical-co2 | chemical-co2
chemical-h2 | chemical-h2
chemical-acetone | chemical-acetone
chemical-heptane | chemical-heptane
chemical-fluorinert chemical-freon | chemical-other-solvents
chemical-tem-grid | tem-acquisition
synthesis-cell | apparatus
synthesis-load | charge-ag apparatus
synthesis-initial-co2 | fill-co2
synthesis-pressurize | pressurize
synthesis-heat synthesis-temperature-verification | heat
synthesis-simultaneous-dose | simultaneous-injection
synthesis-constant-pressure | pressurize
synthesis-reaction-duration | reaction-dwell
synthesis-cool synthesis-depressurize | cool-vent
synthesis-collect | collect
synthesis-precipitate | precipitate
synthesis-redisperse | redisperse
synthesis-variant-inheritance | sample-boundaries ir-route pt-route
synthesis-missing | unreported-details stocks-unreported
characterization-tem-instrument characterization-tem-deposition | tem-acquisition
characterization-size-analysis | size-analysis
characterization-eds-instrument | eds-acquisition
characterization-size-method | ag-concentration-trend ag-temperature-trend size-analysis
characterization-optical-instrument-gap | optical-measurement-scope
table1 | sample-boundaries
fig1-overview | apparatus
fig1-thiol-loop fig1-hydrogen-loop | simultaneous-injection
result-ag-reduction | why-arrested
result-temperature-comparison result-low-temperature-explanation | why-hydrogen
result-diameter-range | ag-diameter-range conflict-size
result-concentration-effect | ag-concentration-trend
result-polydispersity | ag-diameter-range
result-temperature-effect | ag-temperature-trend
fig2a | ag-tem
fig2b | ag-packing
fig2c | ag-lattice
fig3 fig3-symbols | ag-concentration-trend
fig4 fig4-axes | ag-temperature-trend
result-thiol-ratio result-coverage-rationale | thiol-excess
result-redispersion | dispersibility
result-spacing | ag-tem spacing-comparison
comparison-octanethiol-spacing | spacing-comparison
intuition-ligand-rigidity | ligand-rigidity
fig5-overview | ag-histograms
fig6 fig6-scope | ag-eds
fig7-overview | optical-measurement-scope
fig7-i | optical-current
fig7-ii | optical-c10
fig7-iii | optical-hydrocarbon
optical-comparison-interpretation | optical-width-interpretation
ir-conditions | ir-route
pt-conditions | pt-route
ir-pt-crystallinity | ir-tem pt-tem
eq1 | equation-1
eq2 eq2-uv-frequency eq2-vacuum | equation-2
eq3 | equation-3
model-hamaker-comparison | equation-3 conflict-temperature
intuition-solvation | why-fluorinated chain-length
comparison-c10-ligand | chain-length
result-inreaction-stability result-no-co2-redispersion | dispersibility
intuition-chain-length | chain-length conflict-chain
comparison-hexanethiol | polar-solvation
intuition-polar-solvents | polar-solvation
model-three-stages model-temporal-separation model-growth-paths | nucleation-growth
model-self-preserving model-psi1 model-integrals model-sphere-assumption model-mechanism-independence | scaled-distributions
model-broadening-narrowing model-coagulation-inference | coagulation-condensation
model-radius-means model-monodisperse-limit model-measured-moments model-thresholds | moment-ratios
model-psi2 | cumulative-distribution conflict-integral
model-brownian model-sticking | cumulative-distribution
fig8a fig8a-inset | ir-tem
fig8b | pt-tem
fig9 | scaled-distributions
fig10 | cumulative-distribution
result-polycrystallinity | ag-majority-single ag-polycrystals
intuition-realignment comparison-gold-restructuring | coagulation-structure
fig11a fig11b fig11c fig11d | ag-polycrystals
conclusion-01 | ag-diameter-range dispersibility historical-claim
conclusion-02 conclusion-03 | outlook
conclusion-04 | ag-diameter-range coagulation-condensation scaled-distributions
conclusion-05 | chain-length
acknowledgments | acknowledgments
note22-context | reference-22
note32-context | note32-context reference-32
conflict-pt-identity | chemical-pt
conflict-minimum-diameter | conflict-size
conflict-fig4-point-count | ag-temperature-trend
conflict-hamaker-co2-state | conflict-temperature
conflict-fluorinated-length | conflict-chain
conflict-percent-dispersity | table1-a table1-b table1-c table1-d table1-e table1-f table1-g table1-h table1-i
conflict-population-scope | ag-diameter-range
conflict-cohort-joins | sample-boundaries optical-current
conflict-volume-bases | stocks-unreported apparatus simultaneous-injection
conflict-distribution-integral | conflict-integral
scope-no-precursor-preparation | chemical-ag stocks-unreported
scope-no-diffraction | structural-limitations optical-measurement-scope
scope-no-si | review-coverage
'''
mapping={}
for row in pairs.strip().splitlines():
 left,right=row.split('|')
 for uid in left.split():
  assert uid not in mapping,uid
  mapping[uid]=right.split()
for c in 'abcdefghi':
 mapping['table1-'+c]=['table1-'+c];mapping['fig5'+c]=['table1-'+c,'ag-histograms']
for n in range(1,49):mapping[f'reference-{n:02}']=[f'reference-{n:02}']
audit=json.loads((B/'source-audit.json').read_text(encoding='utf8'))
unitids={u['id'] for u in audit['units']}
assert set(mapping)==unitids,(unitids-set(mapping),set(mapping)-unitids)
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Mapped',len(mapping),'source units')
