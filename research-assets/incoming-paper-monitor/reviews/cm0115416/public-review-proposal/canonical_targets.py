operation_targets={
 'stock-a':{'dissolve-a':'acid-dissolution','dry-a':'acid-removal','redissolve-a':'a-redissolution','stir-a':'a-redissolution'},
 'stock-b':{'dissolve-b':'b-dissolution','stir-b':'b-dissolution'},
 'bulk':{'mix':'bulk-mix','press':'bulk-press','fire':'bulk-fire'},
 'bulk-grinding':{'grind':'bulk-grinding','compare':'grinding-result'},
 'xrd':{'acquire':'xrd-method','scherrer':'xrd-widths'},
 'tem':{'acquire':'tem-method','compare':'tem-scales'},
 'particle-size':{'acquire':'sizing-method'},
 'downconversion':{'excite':'fluorescence-method','acquire':'fluorescence-method'},
 'upconversion':{'excite':'upconversion-method','acquire':'fluorescence-method','compare':'bulk-spectrum'},
 'near-ir':{'acquire':'near-ir-method'},
 'erbium-series':{'compare':'erbium-method'},
 'power-response':{'sweep':'power-method','fit':'power-law'},
}
for r in R:operation_targets[r]={**operation_targets['stock-a'],**operation_targets['stock-b'],'combine':'dropwise-addition','stir-suspension':'post-addition','transfer':'autoclave-charge','hydrothermal':'hydrothermal-treatment','centrifuge':'centrifugation','wash':'washing','dry':'drying','ramp':'anneal-800' if r=='anneal-800' else 'annealing-series','anneal':'anneal-800' if r=='anneal-800' else 'annealing-series','cool':'anneal-800' if r=='anneal-800' else 'annealing-series'}
measurement_targets={
 'stock-a':{'supplier':'lanthanum-oxide'},'stock-b':{'supplier':'ammonium-molybdate'},
 'bulk':{'spectral-order':'bulk-spectrum','structural-comparison':'bulk-structure-claim'},
 'bulk-grinding':{'result':'grinding-result','interpretation':'grinding-intuition'},
 'xrd':{'scherrer-size':'scherrer-size','reference':'phase','minor-phase':'phase','figure-scope':'phase','single-crystal-inference':'single-crystal-inference'},
 'tem':{'scale-before':'tem-scales','scale-after':'tem-scales','diameter-range':'tem-morphology','shape':'tem-morphology','unchanged':'anneal-size'},
 'particle-size':{'majority-range':'size-distribution','average':'size-distribution','rounded-summary':'size-distribution','histogram':'size-distribution','comparison':'single-crystal-inference'},
 'downconversion':{'emission-h':'downconversion-peaks','transition-h':'downconversion-peaks','emission-s':'downconversion-peaks','transition-s':'downconversion-peaks','signal-roles':'figure4'},
 'upconversion':{'peak-519':'upconversion-peaks','assignment-519':'upconversion-peaks','peak-541':'upconversion-peaks','assignment-541':'upconversion-peaks','peak-653':'upconversion-peaks','assignment-653':'upconversion-peaks','nano-order':'bulk-spectrum','bulk-order':'bulk-spectrum','enhancement':'bulk-spectrum','temperature-response':'anneal-emission','selected-condition':'annealing-series','temperature-mechanism':'anneal-rationale','figure6-labels':'figure6','figure10-style':'figure10'},
 'near-ir':{'center-wavenumber':'nir-band','center-wavelength':'nir-band','band-wavenumber':'nir-band','band-wavelength':'nir-band','transitions':'nir-assignment','plot-axis':'figure5-axis'},
 'erbium-series':{**{f'fraction-{v}':'erbium-method' for v in [1,2,3,4,5,7]},'text-trend':'erbium-trend','figure-trend':'erbium-conflict','optimum':'erbium-trend','recipe-limit':'erbium-method'},
 'power-response':{**{f'slope-{p}-{w}':'power-slopes' for p in ['prose','figure'] for w in [519,541,653]},'relation':'power-law','photon-count':'power-law','caption-wavelength':'power-label-conflict','figure-axes':'figure8'},
 'mechanisms':{'sensitizer':'sensitizer-emitter','two-steps':'two-photon-model','energy-diagram':'figure9-model','bulk-decay':'bulk-population','surface-sites':'surface-rationale','lifetime':'surface-rationale','emission-location':'surface-bands','size-explanation':'size-context','background':'phosphor-context','applications':'bioassay-context','excitation-definition':'phosphor-context','reference-scope':'reference-scope','source-completeness':'coverage','intensity-efficiency':'bulk-spectrum'},
}
for r in R:measurement_targets[r]={'preanneal-emission':'before-anneal','bulk-like':'anneal-size','emission-order':'anneal-emission','color':'white-powder','crystallite-size':'scherrer-size','phase-reference':'phase','growth':'anneal-size'}
material_targets={'lanthanum-oxide':'lanthanum-oxide','ytterbium-oxide':'ytterbium-oxide','erbium-oxide':'erbium-oxide','nitric-acid':'nitric-acid','water':'water','ammonium-molybdate':'ammonium-molybdate','molybdenum-trioxide':'molybdenum-trioxide'}
