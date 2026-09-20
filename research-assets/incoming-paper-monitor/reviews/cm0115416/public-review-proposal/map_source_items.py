from pathlib import Path
import json
O=Path(__file__).resolve().parent;B=O.parent
data='''
identity-title|identity
identity-authors|identity source-context
identity-journal|identity
identity-dates|identity
identity-administrative|source-context
abstract-material|size-distribution bioassay-context
abstract-anneal|anneal-800 bulk-spectrum
abstract-scope|anneal-emission erbium-trend two-photon-model surface-rationale
abstract-priority|historical-claims
context-nanocrystals|size-context
context-downconversion|phosphor-context
context-upconversion|phosphor-context
context-lasers|application-context
context-led|application-context
context-bio-labels|bioassay-context
context-bio-size|bioassay-context
context-sensitizer|sensitizer-emitter
context-bulk-history|bulk-fire reference-15
context-study|size-distribution bulk-spectrum
precursor-la-oxide|lanthanum-oxide
precursor-yb-oxide|ytterbium-oxide
precursor-er-oxide|erbium-oxide
precursor-nitric-acid|nitric-acid acid-dissolution
precursor-residue|acid-removal
precursor-water-a|water stock-a-composition
precursor-ammonium-molybdate|ammonium-molybdate
precursor-water-b|water stock-b-composition
precursor-mass-amount-conflict|mass-amount-check
precursor-feed-stoichiometry|feed-ratio-check
precursor-dopant-composition|dopant-basis
precursor-bulk-moo3|molybdenum-trioxide
protocol-stock-a-stir|a-redissolution
protocol-stock-b-stir|b-dissolution
protocol-addition|dropwise-addition
protocol-suspension|post-addition
protocol-transfer|autoclave-charge
protocol-hydrothermal|hydrothermal-treatment
protocol-centrifuge|centrifugation
protocol-wash|washing
protocol-dry|drying
protocol-anneal-ramp|anneal-800
protocol-anneal-hold|anneal-800 drying
protocol-anneal-cool|anneal-800 white-powder
protocol-route-limits|missing-fields sample-boundaries structure-limit bioassay-context
bulk-mix|bulk-mix
bulk-composition|dopant-basis bulk-mix
bulk-pellet|bulk-press
bulk-fire|bulk-fire
bulk-identity|bulk-spectrum figure10 sample-boundaries
method-tem|tem-method
method-fluorescence|fluorescence-method
method-nir|near-ir-method
method-xrd|xrd-method
method-particle-size|sizing-method
method-upconversion|upconversion-method
method-missing|fluorescence-method upconversion-method power-method bulk-spectrum
xrd-sample|phase
xrd-phase|phase
xrd-reference|phase reference-scope
xrd-peak|xrd-widths
xrd-fwhm|xrd-widths
xrd-size|scherrer-size
xrd-single-crystal|single-crystal-inference
size-tem-panels|tem-morphology tem-scales
size-tem-range|tem-morphology
size-distribution|size-distribution
size-rounding|size-distribution
size-narrow|size-distribution
optical-down-excitation|downconversion-peaks figure4
optical-down-peaks|downconversion-peaks
optical-up-peaks|upconversion-peaks
optical-abs-range|near-ir-method
optical-abs-center|nir-band
optical-abs-transitions|nir-assignment
optical-abs-window|nir-band
optical-preanneal|before-anneal
anneal-series|annealing-series figure6
anneal-trend|anneal-emission
anneal-800-size|anneal-size
anneal-900-growth|anneal-size
anneal-1000-bulk|anneal-size anneal-emission figure10
anneal-selection|annealing-series anneal-emission
anneal-mechanism|anneal-rationale
doping-scope|erbium-method
doping-trend|erbium-trend erbium-conflict
doping-optimum|erbium-trend
doping-quenching|quenching
doping-figure-conflict|erbium-conflict erbium-method
power-law|power-law
power-measurement|power-method figure8
power-rounded-slopes|power-slopes
power-two-photon|power-law two-photon-model
mechanism-levels|figure9-model
mechanism-excitation|two-photon-model figure9-model
mechanism-relaxation|two-photon-model
mechanism-comparison|bulk-spectrum
mechanism-population|bulk-population
comparison-ranking|bulk-spectrum
comparison-efficiency|bulk-spectrum
comparison-same-structure|bulk-structure-claim
comparison-prior-materials|size-context
comparison-surface-centers|surface-rationale
comparison-lifetime|surface-rationale
comparison-surface-emission|surface-bands
comparison-grinding|bulk-grinding grinding-result
comparison-grinding-model|grinding-intuition grinding-result
figure-1|phase xrd-widths
figure-2|tem-scales tem-morphology
figure-3|size-distribution sizing-method
figure-4a|figure4 downconversion-peaks
figure-4b|figure4 upconversion-peaks
figure-5|figure5-axis nir-band
figure-6|figure6 anneal-emission
figure-7|erbium-conflict
figure-8|figure8 power-slopes power-label-conflict
figure-9|figure9-model two-photon-model
figure-10|figure10 bulk-spectrum
conclusion-synthesis|size-distribution
conclusion-optics|anneal-emission erbium-trend bulk-spectrum two-photon-model surface-rationale
conclusion-funding|funding
source-missing|coverage missing-fields structure-limit data-precision
'''
mapping={'yi2002-'+line.split('|')[0]:line.split('|')[1].split() for line in data.strip().splitlines()}
for n in range(1,28):mapping[f'yi2002-reference-{n:02}']=[f'reference-{n:02}']
audit=json.loads((B/'source-audit.json').read_text(encoding='utf8'));assert set(mapping)=={u['id'] for u in audit['units']},set(mapping)^{u['id'] for u in audit['units']}
(O/'source-item-mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('Mapped',len(mapping),'source units')
