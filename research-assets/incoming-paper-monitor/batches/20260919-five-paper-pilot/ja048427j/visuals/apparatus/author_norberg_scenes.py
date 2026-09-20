from pathlib import Path
import json, hashlib
N=Path(__file__).resolve().parents[2]
V=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prose=read(N/'public-review-proposal/operation-reader-prose.json')
# Source-specific choices. Geometry is explanatory; no instrument shape is a source claim.
# id | title | art | illustration inputs | visible specimen | extra source rows
rows='''hydrolysis-op-1|Metal acetate solution|charge|Zn(OAc)₂·2H₂O;Mn(OAc)₂·4H₂O|DMSO solution|Temperature=Room temperature
hydrolysis-op-2|Dropwise base addition|drop|TMAH in ethanol|Metal acetate solution|Temperature=Room temperature;Addition=Dropwise, constant stirring
hydrolysis-op-3|Nanocrystal growth and ripening|ripen||Growing colloids|Initial growth=Minutes;Later alternatives=Several days at room temperature OR near 60 °C
hydrolysis-op-4|Ethyl acetate precipitation|precipitate|Ethyl acetate|Grown nanocrystals|Retain=Nanocrystal fraction;Separation equipment=Not reported
hydrolysis-op-5|Ethanol resuspension|redisperse|Ethanol|Recovered nanocrystals|Solvent amount=Not reported
hydrolysis-op-6|Repeated precipitation and washing|wash|Heptane;Ethanol|Nanocrystal fraction|Sequence=Heptane precipitation / ethanol resuspension;Cycle count=Not reported
hydrolysis-op-7|Initial dodecylamine capping|cap|Dodecylamine;Toluene|Washed nanocrystals|Treatment=Initial capping, distinct from later cleaning
amine-cleaning-op-1|Thermal surface cleaning|heat|Dodecylamine|Capped colloids|Heating ramp=Not reported
amine-cleaning-op-2|Cooling before precipitation|cool||Treated colloids|Cooling rate=Not reported
amine-cleaning-op-3|Ethanol precipitation and washing|wash|Ethanol|Treated nanocrystals|Retain=Nanocrystal fraction;Volumes / cycles=Not reported
amine-cleaning-op-4|Nonpolar redispersion|redisperse|Toluene / nonpolar solvent|Cleaned nanocrystals|Storage=Several months reported; quantitative conditions absent
surface-control-op-1|Prepare pure-ZnO reference|control-particles|Ethanol|Pure ZnO control|Upstream=Common route without manganese feed
surface-control-op-2|Add surface-reference manganese|particle-add|Mn(OAc)₂·4H₂O|Pure ZnO dispersion|Charge meaning=Added Mn relative to Zn, not measured internal doping
surface-control-op-3|Add ethanolic LiOH dropwise|particle-drop|LiOH in ethanol|Surface-control mixture|Addition=Dropwise;Concentration / volume=Not reported
surface-control-op-4|Surface-reference washing and capping|cap|Dodecylamine;Toluene|Surface-Mn reference|Subsequent analysis=EPR;Thermal stripping=180 °C treatment is not applied
topo-op-1|TOPO surface treatment|heat|Technical TOPO|Nanocrystals|Method=Heating, referred to reference 32;Specimen=1.1% Mn optical / MCD context
topo-op-2|Frozen solution on quartz|dropcoat|TOPO-capped colloids|Quartz disk|Specimen=1.1% Mn;MCD temperature=5 K;Solvent / deposited amount=Not reported
films-op-1|Spin coating: films A–C|spin|Cleaned colloids|Fused silica|Mn content=0.20 ± 0.01%;Scope=Films A–C only
films-op-2|Per-layer annealing: films A–C|anneal||Freshly coated substrate|Scope=Each deposited layer, A–C
films-op-3|Repeat film deposition cycles|cycles||Films A, B and C|Film A=40 coats;Films B and C=20 coats each;Films D–F=Preparation details incomplete; do not assign these cycles
oxidation-controls-op-1|Manganese precursor stability stock|solution|Mn(OAc)₂·4H₂O;DMSO|Precursor solution|Context=Separate from nanocrystal synthesis
oxidation-controls-op-2|Separate precursor control variants|alternatives||Independent control solutions|Baseline=Mn acetate in DMSO, air;Alternatives=Zn acetate addition OR anaerobic handling;Acetate control=0.010 M NaOAc, 5:1 to Mn;Nitrate control=0.002 M Mn nitrate replaces Mn acetate;Gas / full Zn series=Not reported
oxidation-controls-op-3|Store and compare control solutions|stability||Separate control solutions|Temperature=Room temperature;Atmosphere=Air-exposed variants open to air;Spectra=Actual source data, no generated curve
titration-op-1|Titration starting mixture|solution|Mn / Zn acetates;DMSO|One titration progression|Zn feed fraction=98%;Absolute volumes=Not reported
titration-op-2|Incremental base titration|titrate|TMAH in ethanol|Titration solution|Solid source trace=1.65 equivalents;Clouding=Beyond approximately 1.65 equivalents;Time between additions=Not reported
titration-op-3|Aliquot dilution and remeasurement|dilute||Spectral aliquot|Temperature=300 K;Optical path=1 cm;Sequence=Measure aliquot, dilute, remeasure
early-aliquot|Early growth aliquot|aliquot||Early reaction bulk|Temperature=Room temperature;Analysis specimen=Washed and capped, in toluene;Lineage=Remaining bulk continues separately
continue-ripening|Continue growth of remaining bulk|heat||Remaining reaction bulk|Lineage=Early analyzed aliquot is not returned
later-aliquot|Later growth aliquot|aliquot||Later reaction bulk|Preparation=Washed and capped for EPR;Lineage=Separate aliquot; no reuse is asserted
clean-growth-product|Clean later-growth product|heat|Dodecylamine|Later-growth product|Handling=Common N₂ cleaning, cooling and workup;Time qualifier=Specimen-d passage states 30 min exactly
prepare-powder|Prepare analytical powder|precipitate||Toluene colloid|Method=Rapid precipitation;Antisolvent / settings=Not restated for this preparation;Aliquots=XRD and magnetic powders not equated
characterize-structure|Structural characterization contexts|structure||Separate source specimens|Methods=TEM / HRTEM; powder and film XRD;Assignments=Figure 3 panel-specific specimens;Atomic coordinates=No refined sample coordinates or CIF supplied
acquire-optics|Compare optical specimens|optical-compare||Separate capped colloids|Specimens=Undoped; 0.13% Mn estimated; 1.3% Mn reported;Normalization=Absorption at excitation; emission scaled proportionally
acquire-magnetism|SQUID specimen comparison|magnetic-compare||Powder and films A–C|Contexts=Separate source specimens;Scope=Keep temperatures, fields and model comparisons attached
zfc-series|Zero-field-cooled magnetometry|magnetic||Films A and B|Temperature interval=5–350 K;Observed result=No transition over measured interval
film-epr|Film and precursor EPR comparison|epr-compare||Film A / precursor colloid|Additional signal=g = 2.00;Interpretation=Tentative radical / redox assignment;Unmeasured=N content and carrier polarity
acquire-epr-x|X-band EPR acquisition|epr||Colloid or film specimen|Instrument=Bruker EMX;Temperature=Room temperature; figure-specific 300 K;Film mounting=Nonmagnetic tape; film perpendicular to field
acquire-epr-q|Q-band EPR acquisition|epr||Toluene colloid|Instrument=Bruker ESP300E;Temperature=Room temperature
acquire-epr-sim|EPR model calculation|model||Model parameters|Software=Høgni Weihe SIM, version 2002;Method=Full-matrix diagonalization;Hamiltonian=Equation 1;Status=Calculated traces, not measured atomic coordinates
acquire-abs|Electronic absorption acquisition|optical||Colloid or film A context|Instrument=Cary 500E Varian;Temperature=Room temperature;Aliquot dilution=70-fold only in the separate titration procedure
acquire-mcd|Magnetic circular dichroism|mcd||Frozen TOPO-capped colloids|Specimen=1.1% Mn on quartz;Apparatus=Referred to prior work; not restated
acquire-lum|Luminescence acquisition|lum||Source-defined optical specimen|Instrument=Jobin Yvon FluoroMax-2
acquire-xrd-powder|Powder diffraction acquisition|xrd-powder||Powder specimen|Instrument=Philips PW1830;Radiation=Cu Kα
acquire-xrd-film|Thin-film diffraction acquisition|xrd-film||Thin-film specimen|Instrument=Rigaku Rotaflex RTP300;Radiation=Cu Kα
acquire-tem|High-resolution electron microscopy|tem||Microscopy specimen|Instrument=JEOL 2010;Electron source=High-brightness LaB₆
acquire-icp|Elemental analysis by ICP-AES|icp||Analytical aliquot|Instrument=Jarrel Ash 955;Reported purpose=Dopant concentration
acquire-mag|SQUID magnetometry acquisition|magnetic||Powder or thin film|Instrument=Quantum Design MPMS-5S;Correction=Subtract substrate and holder diamagnetism;Ceiling meaning=Limits the reported Curie-temperature bound'''
configs={}
for row in rows.splitlines():
    key,title,art,inputs,specimen,extras=row.split('|')
    configs['norberg-2004-'+key]={'title':title,'art':art,'names':inputs.split(';') if inputs else [],'specimen':specimen,'extra_rows':[dict(zip(('label','value'),v.split('=',1))) for v in extras.split(';') if '=' in v], 'note':prose[key]}
assert len(configs)==47
# Semicolons inside row values are intentionally reconstructed below, rather than lost as delimiters.
configs['norberg-2004-characterize-structure']['extra_rows'][0]['value']='TEM / HRTEM; powder and thin-film XRD'
configs['norberg-2004-acquire-optics']['extra_rows'][0]['value']='Undoped; 0.13% Mn estimated; 1.3% Mn reported'
configs['norberg-2004-acquire-epr-x']['extra_rows'][1]['value']='Room temperature; figure-specific 300 K'
configs['norberg-2004-acquire-epr-x']['extra_rows'][2]['value']='Nonmagnetic tape; film perpendicular to field'
configs['norberg-2004-acquire-optics']['extra_rows'][1]['value']='Absorption at excitation; emission scaled proportionally'
configs['norberg-2004-films-op-3']['extra_rows'][2]['value']='Preparation details incomplete; A–C cycles not assigned'
configs['norberg-2004-amine-cleaning-op-4']['extra_rows'][0]['value']='Several months reported; quantitative conditions absent'
configs['norberg-2004-later-aliquot']['extra_rows'][1]['value']='Separate aliquot; no reuse is asserted'
labels={'frequency_GHz':'Microwave frequency','path_length_cm':'Optical path','temperature_K':'Temperature','field_T_range':'Magnetic field','cuvette_dimension_1':'Cuvette dimension 1','cuvette_dimension_2':'Cuvette dimension 2','excitation_cm-1':'Excitation wavenumber','accelerating_voltage_kV':'Accelerating voltage','instrument_temperature_ceiling_K':'Instrument temperature ceiling','temperature':'Temperature','duration':'Duration','precipitation_temperature_limit':'Temperature before precipitation','substrate_length':'Substrate length','substrate_width':'Substrate width','spin_speed':'Spin speed','spin_duration':'Spin duration','dispensed_volume':'Dispensed volume','per_layer_duration':'Duration per layer','time_after_base_addition':'Time after base addition','combined_metal_concentration':'Total metal concentration','reaction_volume':'Reaction volume','base_equivalents':'Base amount · mixture basis','base_stock_concentration':'Base stock concentration','stirring_speed':'Stirring speed','addition_duration':'Addition duration','initial_capping_temperature':'Initial capping temperature','initial_capping_duration':'Initial capping duration','dodecylamine_charge':'Dodecylamine charge','measurement_field':'Measurement field','excitation_absorbance_range':'Absorbance at excitation','excitation_wavenumber':'Excitation wavenumber','Mn_concentration':'Manganese concentration','absorption_probe':'Absorption probe','storage_duration':'Storage duration','Mn_relative_to_Zn':'Added Mn relative to Zn','LiOH_charge_basis_unspecified':'LiOH amount · equivalent basis unknown','Mn_feed_fraction':'Mn feed fraction','base_increment':'Base increment','remeasurement_dilution':'Remeasurement dilution','TOPO_charge':'TOPO charge'}
records=[read(p) for p in sorted((N/'canonical-drafts').glob('*.json'))]
selection={}
for r in records:
    if r['operations']:selection[r['record_id']]=[o['id'] for o in r['operations']]
    for o in r['operations']:
        assert o['id'] in configs
        for k in o['parameters']: assert k in labels,k
(V/'scene-config.json').write_text(json.dumps({'source_group':'norberg2004','configs':configs,'parameter_labels':labels,'records':selection},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
template=(V/'module-template.mjs').read_text(encoding='utf-8')
(V/'norberg2004-protocol.mjs').write_text('const DATA='+json.dumps({'configs':configs,'parameter_labels':labels,'records':selection},ensure_ascii=False,separators=(',',':'))+';\n'+template,encoding='utf-8')
print(json.dumps({'scenes':len(configs),'records':len(selection),'module_sha256':sha(V/'norberg2004-protocol.mjs')}))
