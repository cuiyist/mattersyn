from pathlib import Path
import json, hashlib, shutil

A=Path(__file__).resolve().parent
N=A.parent.parent
C=N/'canonical-proposal/v2'
S=Path(r'[local path redacted]')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
records=[read(p) for p in sorted(C.glob('morrison-*.json'))]
assert len(records)==18 and sum(len(r['operations']) for r in records)==24
assert sha(C/'package-manifest.json')=='433555d5ccaaa0a3d98c01f3f9657921872611fee766557e9c4756f49e806508'
cfg={}
def scene(op,kind,title,prose,notes,extra=()):
 cfg[op]={'art':kind,'title':title,'prose':prose,'notes':[{'label':a,'value':b} for a,b in notes],'measurement_rows':[{'label':a,'measurement_id':b} for a,b in extra]}

scene('precursor-add','dropwise','Aqueous precursor precipitation',
 'Add the aqueous CdCl₂ solution dropwise to the continuously stirred ammonium phenyldithiocarbamate solution. A white precipitate appears immediately.',
 [('Solvent identity','Both aqueous solutions use deionized water.'),('Addition order','CdCl₂ solution → ammonium phenyldithiocarbamate solution.'),('Missing conditions','Addition rate, vessel geometry, stirring speed and numerical temperature are not reported.')])
scene('precursor-stir-filter','stir-filter','Stirring and vacuum filtration',
 'Continue stirring the precipitation mixture, then collect the solid by vacuum filtration. The wet Cd(PTC)₂ solid proceeds to washing.',
 [('Retained fraction','Precipitated solid on the filter; filtrate is not the product.'),('Missing conditions','Vacuum pressure, filter specification and stirring speed are not reported.')])
scene('precursor-wash-dry','cold-wash-dry','Cold washing and vacuum drying',
 'Wash the collected precursor with ice-chilled deionized water, then ice-chilled ethanol. Dry under vacuum to obtain the pale-yellow precursor powder.',
 [('Wash sequence','Water first; three ethanol portions afterward.'),('Source discrepancy C1','The printed 0.149 g / 33 mmol / 60% isolated-yield statement is inconsistent. The printed amount is preserved, not silently corrected.'),('Missing conditions','Ice-chilled is qualitative. Drying temperature and vacuum pressure are not reported.')])
scene('crystal-solution','crystal-feed','THF solution for precursor crystallization',
 'Place the Cd(PTC)₂ solution in THF in a small vial. This prepares a precursor crystal-growth experiment, separate from nanocrystal shell growth.',
 [('Source discrepancy C3','The paper prints “20 mmol solution”; the THF volume and concentration denominator are absent. This is not a reported 20 mM stock.'),('Species scope','Cd(PTC)₂·THF precursor coordination-polymer crystals, not CdSe/CdS nanocrystals.')])
scene('crystal-vapor','vapor-jar','Hexane vapor diffusion',
 'Place the small THF-solution vial inside a larger jar containing hexane. Seal the jar and leave it undisturbed overnight; pale-yellow spindling crystals form.',
 [('Duration','Overnight; no numerical number of hours is supplied.'),('Apparatus scope','The nested vial and sealed jar are reported. Their geometry and scale are explanatory.'),('Missing conditions','Temperature, hexane amount and vessel dimensions are not reported.')])
scene('crystal-mount-measure','single-crystal','Single-crystal diffraction acquisition',
 'Mount a precursor crystal on a MiTeGen cryoloop for the Bruker X8 Kappa ApexII CCD diffractometer with Oxford Cryostream cooling. Use graphite-monochromated Mo Kα radiation from a fine-focus sealed tube.',
 [('Acquisition scope','The displayed approximate mounting dimensions are separate from the more precise crystal dimensions in Table 1.'),('Structure scope','This is the THF-solvated precursor crystal, not an atomic model of CdSe/CdS belts. No measured diffraction pattern is drawn.'),('Temperature exception','The reported cryogenic acquisition temperature overrides the general ambient-procedure statement.')],
 [('Table 1 acquisition temperature','table-1-r003-c01')])
scene('nmr-heat','nmr-series','NMR decomposition time course',
 'Heat Cd(PTC)₂ in DMSO-d₆ and acquire spectra at the stated intervals over the monitoring period. This decomposition experiment contains no CdSe belts.',
 [('Source discrepancy C2','The printed charge is 12 mg / 0.003 mmol; these values are inconsistent and both are preserved.'),('Source discrepancy C6','Main text reports thiourea after 2 h; SI Figures S2/S3 state 1 h. “After 2 h” is an observation time, not a lower bound on onset.'),('Missing apparatus','NMR-tube closure and heating hardware are not specified. The tube and heating symbols are explanatory.')],
 [('Main-text thiourea observation','morrison2017-nmr-evolution-q3'),('SI thiourea observation','morrison2017-si-hnmr-q8')])
scene('nmr-isolate','centrifuge-xrd','Isolation of the NMR decomposition solid',
 'Collect the resulting solid using a benchtop centrifuge, wash with toluene, and deposit the solid onto a substrate for powder X-ray diffraction.',
 [('Retained fraction','The precipitated solid proceeds to XRD.'),('Missing conditions','Centrifuge speed and duration, substrate identity and drying conditions are not reported.')])
scene('thf-heat','septum-heat','THF decomposition control',
 'Heat Cd(PTC)₂ in THF in a septum-capped vial. This precursor-only control is separate from the shell-growth and DMSO experiments.',
 [('Source discrepancy C2','The printed charge is 12 mg / 0.003 mmol; both conflicting values are retained.'),('Missing conditions','Heating duration, heating hardware, vial dimensions and pressure are not reported.'),('Apparatus scope','A septum-capped vial is reported for this control only; no reflux condenser is inferred.')])
scene('thf-wash','wash-xrd','THF-control powder preparation for XRD',
 'Wash the THF-control solid with toluene and deposit it on a substrate for powder X-ray diffraction.',
 [('Retained fraction','Washed solid, with no claimed shared specimen identity with the DMSO product.'),('Recovery method','The initial solid-separation method is not stated. Centrifugation is not imported from the NMR control.'),('Missing conditions','Substrate identity and drying conditions are not reported.')])
scene('dmso-hot','powder-heat','DMSO decomposition without nanobelts',
 'Heat Cd(PTC)₂ in DMSO without CdSe belts. A powdery yellow precipitate appears within the reported window; the reaction appears complete later.',
 [('Observation scope','Precipitate appearance and apparent completion are reported observations, not independently established stop criteria.'),('Source discrepancy C7','The main-text DMSO EDS assignment and SI THF label are not merged into one physical powder specimen.'),('Missing conditions','Precursor charge, solvent volume, vessel, heating hardware and isolation details are not reported.')],
 [('Yellow precipitate observed by','morrison2017-dmso-powder-q2'),('Apparent completion','morrison2017-dmso-powder-q3')])
scene('base-nmr','base-compare','Added-base comparison by NMR',
 'Compare precursor decomposition in DMSO with aniline and without added base. The plotted time window is an acquisition context, not a prescribed reaction duration.',
 [('Independent comparisons','The two panels are alternative experiments, not sequential additions.'),('Source discrepancy C5','Main p. 5 names n-octylamine as catalyst, whereas main p. 6 and Figure S8 name aniline. This scene represents the explicit aniline/no-base comparison.'),('Missing conditions','Base dose, solution amounts and detailed NMR vessel/heater are not reported.')])
scene('rt-combine','rt-combine','Room-temperature excess-precursor treatment',
 'Combine amine-ligated CdSe quantum belts with excess saturated Cd(PTC)₂ in DMSO at room temperature. Exact reagent charges and solvent volumes are not supplied.',
 [('Temperature','Room temperature; numerical temperature is not specified.'),('Material identity','Starting objects are CdSe quantum belts. Their schematic rectangles do not encode measured dimensions or surface structure.'),('Variant scope','This room-temperature experiment is separate from the 70 °C excess-precursor treatment.')])
scene('rt-backexchange','rt-amine','Removal of excess precursor and amine redispersion',
 'After the reported room-temperature exposure, remove the excess precursor and redisperse the belts in neat n-octylamine.',
 [('Material flow','Remove excess precursor; retain the belts for neat-amine redispersion.'),('Missing conditions','Removal method, n-octylamine amount and redispersion duration are not reported. No centrifuge or wash cycle is inferred.')],
 [('Reported exposure before back-exchange','morrison2017-rt-shift-q4')])
scene('hot-growth','hot-colors','Heated excess-precursor treatment',
 'Heat the CdSe-belt / Cd(PTC)₂ / DMSO mixture. The paper reports a pale-yellow to tangerine-orange change within 15 minutes and a deep-red mixture after 4 hours.',
 [('Time interpretation','Orange color is observed within an upper-bound window. Deep red is a later observation; neither is converted into an exact onset or a required stop condition.'),('Missing conditions','Exact charges, vessel geometry, pressure and heating hardware are not reported. No bath or reflux apparatus is assigned.')],
 [('Orange observed by','morrison2017-hot-excess-q2'),('Deep-red observation time','morrison2017-hot-excess-q3')])
scene('hot-backexchange','hot-amine','Amine redispersion after heated treatment',
 'Redisperse the product of the heated excess-precursor experiment in n-octylamine. Keep this product context separate from the room-temperature back-exchange.',
 [('Missing conditions','Recovery method, amine quantity, treatment duration and final concentration are not reported.'),('Specimen scope','No exact physical-sample identity with the separate optical or TEM monolayer series is implied.')])
scene('qb-wash','belt-wash','Removal of excess amine from starting belts',
 'Add toluene to the starting CdSe quantum-belt dispersion and centrifuge. Discard the supernatant and retain the precipitated belts. Repeat twice for three total washes.',
 [('Charge basis','The 0.512 g is the mass of dispersion, not dry CdSe. CdSe concentration is not given.'),('Retained fraction','Belt precipitate; discard the supernatant after each cycle.'),('Apparatus scope','Centrifuge and tube geometry are explanatory; the reported rotation rate is not converted to relative centrifugal force.')])
scene('qb-shell','shell-heat','Controlled CdS shell growth',
 'Redisperse the washed belts in the Cd(PTC)₂ / THF solution and heat. The source identifies three hours as ideal and describes the charge as 1.0–1.5 times its estimated monolayer requirement.',
 [('Charge basis','The monolayer estimate cannot be reconstructed from the reported dispersion mass because core concentration and surface-area basis are missing.'),('Missing apparatus','Reaction vessel, heating hardware, pressure and gas atmosphere are not specified. The septum vial used for a separate control is not inherited.'),('Geometry','The belt and shell symbols are explanatory, with no atomic lattice, ligand coordinates or quantitative shell dimensions.')])
scene('qb-sample','time-aliquots','Time-resolved aliquot sampling',
 'Remove small aliquots at the reported times from the monolayer shell-growth family for optical workup. These are sampling points, not five independent synthesis recipes.',
 [('Aliquot unit','Drops; no unsupported conversion to volume is made.'),('Sample lineage','Each aliquot feeds its own optical workup. No one-to-one association with a TEM image is inferred.')])
scene('aliquot-thf','thf-spin','THF dilution and aliquot isolation',
 'Dilute a shell-growth aliquot with THF and centrifuge. Discard the supernatant and retain the precipitate for amine repassivation.',
 [('Retained fraction','Aliquot precipitate; discard supernatant.'),('Sample lineage','An optical time-course aliquot, not the independently described TEM preparation.')])
scene('aliquot-repassivate','amine-passivate','Repassivation with n-octylamine',
 'Resuspend the washed aliquot precipitate in n-octylamine before removing excess amine.',
 [('Missing conditions','Amine amount, mixing method, temperature and repassivation duration are not reported.'),('Geometry','No exact bound-ligand coverage or binding geometry is inferred.')])
scene('aliquot-toluene-wash','toluene-spin','Removal of excess repassivating amine',
 'Add toluene, centrifuge, and retain the precipitate while discarding the supernatant. Repeat to remove excess amine.',
 [('Repeat count','Not reported for this stage. The three initial belt washes are not inherited here.'),('Retained fraction','Optical-workup precipitate; supernatant discarded.')])
scene('aliquot-optics','optical','Optical dispersion and spectroscopy',
 'Disperse the washed, amine-passivated product in toluene for UV–visible absorption and photoluminescence measurements.',
 [('Missing conditions','Final toluene volume, dispersion concentration and cell path length are not reported for this preparation.'),('Acquisition scope','Light-source, sample-cell and detector symbols are explanatory. No synthetic spectrum is drawn.')])
scene('qb-tem','tem-grid','Separate preparation for electron microscopy',
 'For TEM, redisperse material from the shell-growth family in n-octylamine and deposit it on a copper grid carrying a carbon film.',
 [('Sample lineage','This microscopy branch begins from the shell-growth family, not from a named optical aliquot or its final dispersion.'),('Missing conditions','Amine amount, deposition volume, grid mesh, drying conditions and exact optical–TEM specimen join are not reported.'),('Image scope','The grid is an apparatus symbol, not a fabricated TEM image.')])

labels={'graph_duration':'Plotted NMR time window','precursor_mass':'Printed Cd(PTC)₂ mass','printed_precursor_amount':'Printed Cd(PTC)₂ amount (conflicted)','dmso_d6_mass':'DMSO-d₆ mass','temperature':'Temperature','spectrum_interval':'NMR acquisition interval','monitoring_period':'NMR monitoring period','wash_count':'Toluene wash count','toluene_each_wash':'Toluene per wash','thf_volume':'THF volume','saturated_concentration':'Saturated Cd(PTC)₂ concentration','dispersion_aliquot_mass':'Starting dispersion mass','toluene_per_cycle':'Toluene per cycle','centrifuge_speed':'Centrifuge rotation rate','centrifuge_duration':'Centrifugation time','total_cycles':'Total initial wash cycles','thf_solution_volume':'Cd(PTC)₂ / THF solution volume','precursor_concentration':'Cd(PTC)₂ stock concentration','ideal_time':'Source-reported ideal growth time','relative_estimated_monolayer_precursor':'Estimated monolayer requirement multiplier','time1':'Aliquot sampling time 1','time2':'Aliquot sampling time 2','time3':'Aliquot sampling time 3','time4':'Aliquot sampling time 4','time5':'Aliquot sampling time 5','aliquot':'Aliquot amount','thf_dilution':'THF dilution volume','toluene_wash':'Toluene per repeated wash','printed_solution_amount':'Ambiguous printed solution amount','cdcl2_mass':'CdCl₂ mass','cdcl2_amount':'CdCl₂ amount','cdcl2_water':'Deionized water for CdCl₂','nh4ptc_mass':'NH₄PTC mass','nh4ptc_amount':'NH₄PTC amount','nh4ptc_water':'Deionized water for NH₄PTC','stirring_duration':'Stirring before filtration','water_wash':'Ice-chilled deionized-water wash','ethanol_wash_cycles':'Ice-chilled ethanol portions','ethanol_each_wash':'Ethanol per portion','vacuum_drying':'Vacuum-drying time','approx_length':'Approximate mounting-crystal length','approx_width':'Approximate mounting-crystal width','approx_depth':'Approximate mounting-crystal thickness','mo_kalpha_wavelength':'Mo Kα wavelength','preliminary_frame_scans':'Preliminary frames','typical_scan_width':'Typical scan width','counting_time':'Counting time per frame','crystal_detector_distance':'Crystal-to-detector distance','cell_refinement_reflections':'Cell-refinement reflections'}

bindings=[]; compact=[]; counts=0
for r in records:
 if not r['operations']: continue
 selected=[]
 for i,o in enumerate(r['operations']):
  c=cfg[o['id']]; c['record_id']=r['record_id']; c['operation_pointer']=f'/operations/{i}'
  for k in o['parameters']: assert k in labels
  extras=[]
  for e in c['measurement_rows']:
   hits=[(j,m) for j,m in enumerate(r['measurements']) if m['id']==e['measurement_id']]; assert len(hits)==1
   j,m=hits[0]; e.update(pointer=f'/measurements/{j}/value',quantity=m['value']); extras.append(m['id'])
  bindings.append({'record_id':r['record_id'],'record_path':str(C/(r['record_id']+'.json')),'record_sha256':sha(C/(r['record_id']+'.json')),'operation_id':o['id'],'operation_pointer':f'/operations/{i}','art':c['art'],'inputs':o['inputs'],'outputs':o['outputs'],'retained_fraction':o.get('retained_fraction'),'parameter_bindings':[{'label':labels[k],'pointer':f'/operations/{i}/parameters/{k}','quantity':v} for k,v in o['parameters'].items()],'extra_measurement_bindings':c['measurement_rows'],'source_evidence':o['evidence'],'canonical_description':o['description'],'human_prose':c['prose'],'source_specific_notes':c['notes']})
  selected+=extras; counts+=len(o['parameters'])
 compact.append({k:r[k] for k in ['record_id','lineage','materials','material_states','operations']}|{'measurements':[m for m in r['measurements'] if m['id'] in selected]})
assert len(cfg)==24==len(bindings)
write(A/'scene-config.json',{'source_group':'morrison2017','configs':cfg,'parameter_labels':labels})
write(A/'records.json',compact)
write(A/'canonical-bindings.json',{'source_group':'morrison2017','canonical_manifest_sha256':sha(C/'package-manifest.json'),'operation_count':24,'canonical_parameter_count':counts,'bindings':bindings})
shutil.copyfile(S/'dist/quantity-value.mjs',A/'quantity-value.mjs')
module=(A/'protocol-template.mjs').read_text(encoding='utf-8').replace('__CONFIG__',json.dumps({'source_group':'morrison2017','configs':cfg,'parameter_labels':labels},ensure_ascii=False))
(A/'morrison2017-protocol.mjs').write_text(module,encoding='utf-8')
print(json.dumps({'operations':len(bindings),'parameter_count':counts,'extra_measurement_rows':sum(len(b['extra_measurement_bindings']) for b in bindings),'operation_records':len(compact)}))
