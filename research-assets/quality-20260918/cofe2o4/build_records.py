"""Factual extraction from Saha 2019 main and matched SI. Writes only this research folder."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parents[2]/'recipe-atlas/scripts'))
from record_helpers import *
SID='saha2019'; DOI='10.1021/acs.jpcc.8b11124'
SRC=source(SID,DOI,'Interface Modeling Leading to Giant Exchange Bias from the CoO/CoFe2O4 Quantum Dot Heterostructure','Avijit Saha; Siddhartha Sohoni; Ranjani Viswanatha',2019,'Matched title, authors and content; all 3 SI pages read and visually reviewed together with all 7 main pages.')
E=lambda loc:ev(SID,loc)
Q=lambda v,u,loc,**kw:qty(v,u,E(loc),**kw)
F=lambda v,loc,**kw:fact(v,E(loc),**kw)
MLOC='main p.2422, Experimental Methods / Materials'
CLOC='main p.2422, Synthesis'
SLOC='main pp.2422–2423, CoO/CoFe2O4 Core Shell Heterostructure'
LINK='main p.2424, Results paragraph explicitly selecting the 30 min sample for the remaining measurements'
CHEM={
 'cobalt-acetate':('Cobalt(II) acetate','C4H6CoO4',99.9,'Nominal acetate formula only; hydration/solvation is not specified. Source Co(ac)2 means acetate, not acetylacetonate.'),
 'iron-acetate':('Iron(II) acetate','C4H6FeO4',95,'Nominal acetate formula only; hydration/solvation is not specified. Source is iron(II), not iron(III), and acetate, not acetylacetonate.'),
 'oleic-acid':('Oleic acid','C18H34O2',90,'Commercial reagent as used; purified molecular speciation and surface binding are not measured.'),
 'oleylamine':('Oleylamine','C18H37N',70,'Commercial reagent as used; purified molecular speciation and surface binding are not measured.'),
 'hexane':('Hexane','C6H14',None,'Purity, supplier and isomeric composition not reported.'),
 'ethanol':('Ethanol','C2H6O',None,'Purity and supplier not reported.'),
 'argon':('Argon','Ar',None,'Flow rate and purity not reported.'),
 'water':('Water','H2O',None,'Grade not reported.'),
}
def mat(id,role,stage,loc,qs=None):
 n,f,p,note=CHEM[id];qs=qs or {}
 if p is not None:qs['purity']=Q(p,'%',MLOC,qualifier='supplier label; purity basis not specified')
 return material(id,n,f,role,stage,E(loc),qs,[note]+(['Sigma-Aldrich; used without further purification.'] if p is not None else []))
def base(id,title,formula,method,kind='literature_protocol'):
 r=record(id,title,formula,'magnetic oxide nanocrystals',method,SRC,CLOC if formula=='CoO' else SLOC,kind)
 r['collection']='reviewed_literature';r['lineage']['recipe_family']='saha2019-coo-cofe2o4'
 r['material'].update(elements=['Co','O'] if formula=='CoO' else ['Co','Fe','O'],components=['CoO'] if formula=='CoO' else ['CoO','CoFe2O4'],architecture='single_material' if formula=='CoO' else 'core_shell')
 r['quality']['review_scope']='All 7 main and 3 matched SI pages text-read and visually reviewed; synthesis, characterization, original figures, table, equations and source conflicts inventoried. Literature extraction, not independent reproduction. IDs identify method/timepoint cohorts, not author-assigned physical batches.'
 r['context_links']=[{'label':'Primary paper and supporting information','url':'https://doi.org/'+DOI,'relation':'primary_source'}]
 return r
def op(id,action,label,loc,inputs,outputs,depends=None,qs=None,**kw):
 return operation(id,action,label,E(loc),inputs,outputs,depends,qs,**kw)
def meas(id,s,prop,v,u,tech,loc,conditions='',**kw):
 return measurement(id,s,prop,Q(v,u,loc,**kw),tech,E(loc),conditions)

core=base('saha-2019-coo-core','CoO seed nanocrystals by thermal decomposition of cobalt(II) acetate','CoO','thermal decomposition')
core['materials']=[mat('cobalt-acetate','metal_precursor','synthesis',CLOC,{'amount':Q(.4,'mmol',CLOC)}),mat('oleic-acid','ligand','synthesis',CLOC,{'volume':Q(2,'mL',CLOC)}),mat('oleylamine','ligand_solvent','synthesis',CLOC,{'volume':Q(5,'mL',CLOC)}),mat('argon','process_gas','synthesis',CLOC),mat('hexane','workup_solvent','workup',CLOC,{'volume':Q(None,'mL',CLOC)}),mat('ethanol','antisolvent','workup',CLOC,{'volume':Q(None,'mL',CLOC)})]
core['material_states']=[state('core-charge','Cobalt acetate in OA/OlAm',['cobalt-acetate','oleic-acid','oleylamine']),state('core-degassed','Degassed core charge',['core-charge']),state('core-220','Charge after 220 °C hold',['core-degassed'],'reaction_batch'),state('core-300','Black CoO reaction solution',['core-220'],'reaction_batch'),state('core-cooled','Room-temperature CoO solution',['core-300']),state('core-powder','Washed CoO powder precipitate',['core-cooled'],'product')]
core['operations']=[
 op('core-mix','mix','Charge a three-neck round-bottom flask',CLOC,['cobalt-acetate','oleic-acid','oleylamine'],['core-charge'],description='Flask connected to a Schlenk line. Vessel volume not reported.'),
 op('core-degas','degas','Degas under evacuation with vigorous stirring',CLOC,['core-charge'],['core-degassed'],['core-mix'],{'temperature':Q(80,'degC',CLOC),'duration':Q(1,'h',CLOC),'pressure':Q(None,'Torr',CLOC),'stirring_rate':Q(None,'rpm',CLOC)},environment=F('Evacuation',CLOC)),
 op('core-heat220','heat_hold','Heat and hold under argon',CLOC,['core-degassed','argon'],['core-220'],['core-degas'],{'temperature':Q(220,'degC',CLOC),'hold_duration':Q(20,'min',CLOC),'ramp_rate':Q(None,'K/min',CLOC)},environment=F('Argon flow',CLOC)),
 op('core-heat300','ramp_hold','Raise to 300 °C and hold',CLOC,['core-220'],['core-300'],['core-heat220'],{'temperature':Q(300,'degC',CLOC),'ramp_rate':Q(5,'K/min',CLOC),'hold_duration':Q(10,'min',CLOC)},environment=F('Argon flow continued from preceding stage',CLOC,status='inherited',note='Continuation of the explicitly stated argon heating sequence; a second atmosphere instruction is not given.')),
 op('core-cool','cool','Cool the black solution to room temperature',CLOC,['core-300'],['core-cooled'],['core-heat300'],{'temperature':Q(None,'degC',CLOC,qualifier='room temperature; numerical value not given')},endpoint=F('Room temperature',CLOC)),
 op('core-wash','centrifuge_wash','Wash with hexane–ethanol and retain powder precipitate',CLOC,['core-cooled','hexane','ethanol'],['core-powder'],['core-cool'],{'centrifugation_speed':Q(None,'g_relative',CLOC),'centrifugation_duration':Q(None,'min',CLOC),'wash_count':Q(None,'count',CLOC)},stage='workup',retained_fraction='core-powder',description='Source calls the retained material powder precipitate. No separate drying operation or solvent ratio is reported.'),
 op('core-store','store','Store the powder in a vial for further use',CLOC,['core-powder'],[],['core-wash'],{'storage_temperature':Q(None,'degC',CLOC),'storage_duration':Q(None,'h',CLOC)},stage='storage')]
p=product('saha2019-coo-core','CoO',E('main pp.2422–2424; Figure 1; Figure 2a,c; Table 1; SI Figure S1'),'explicit','core-powder','Cubic CoO',notes=['The named CoO cohort is linked to the core method; no physical batch identifier or yield is given.','No measured atomic coordinates or surface ligand coverage.'])
p['source_sample_label']='CoO core QDs';p['morphology']=F('Almost spherical','main p.2424, Figure 2a,c');core['products']=[p]
core['measurements']=[
 meas('core-diameter',p['sample_id'],'diameter',12,'nm','TEM size distribution','main p.2424 and SI p.S2 Figure S1','Average diameter, not a requested target.'),
 meas('core-spread',p['sample_id'],'diameter_spread',3.2,'nm','TEM size distribution','main p.2424 and SI p.S2 Figure S1',qualifier='reported ±; spread statistic not defined'),
 meas('core-xrd-size',p['sample_id'],'crystallite_size',14.7,'nm','XRD / Scherrer analysis','main p.2423 Table 1 and adjacent discussion',status='author_derived',approximate=True,qualifier='instrumental broadening not corrected'),
 meas('core-lattice-a',p['sample_id'],'lattice_parameter_a',4.258,'angstrom','XRD','main p.2423 Table 1',status='author_derived'),
 meas('core-d111',p['sample_id'],'interplanar_spacing_111',2.43,'angstrom','HRTEM','main p.2424 Figure 2c,d and text')]
core['quality']['missing_fields']=['Acetate hydration/solvation, vessel capacity and exact pressure/argon flow are unspecified.','Heating rate to 220 °C and numerical room-temperature endpoint are not given.','Workup solvent volumes/ratio, centrifugation speed/time and wash count are not reported.','Drying, storage temperature/atmosphere/duration and isolated yield are not reported.','Physical batch ID, ± statistic, per-cohort particle count and measured atomic coordinates are unavailable.']
core['quality']['experimental_outcome']='reported_product'

shell=base('saha-2019-coo-cofe2o4-seeded-growth','CoFe2O4 shell growth on CoO seeds: 15 and 30 min aliquots','CoO/CoFe2O4','seeded thermal decomposition')
shell['lineage']['parent_record_id']=core['record_id']
shell['materials']=[material('coo-seeds','Presynthesized CoO powder','CoO','seed','synthesis',E(SLOC),{'mass':Q(30,'mg',SLOC,basis='powder mass; inorganic/ligand fraction not measured')},['Prepared by the same paper core method; not a reported core synthesis yield.']),mat('cobalt-acetate','metal_precursor','synthesis',SLOC,{'feed_amount':Q(.05,'mmol',SLOC)}),mat('iron-acetate','metal_precursor','synthesis',SLOC,{'feed_amount':Q(.1,'mmol',SLOC)}),mat('oleic-acid','ligand','synthesis',SLOC,{'feed_volume':Q(1,'mL',SLOC)}),mat('oleylamine','ligand_solvent','synthesis',SLOC,{'reactor_volume':Q(2,'mL',SLOC),'feed_volume':Q(2,'mL',SLOC)}),mat('argon','process_gas','synthesis',SLOC),mat('hexane','workup_dispersion_solvent','workup',SLOC,{'volume':Q(None,'mL',SLOC)}),mat('ethanol','antisolvent','workup',SLOC,{'volume':Q(None,'mL',SLOC)})]
shell['stocks']=[{'id':'co-fe-feed','name':'Separately degassed Co(II)/Fe(II) acetate feed in OA/OlAm','components':[{'material_id':i,'quantities':{k:Q(v,u,SLOC)}} for i,k,v,u in [('cobalt-acetate','amount',.05,'mmol'),('iron-acetate','amount',.1,'mmol'),('oleic-acid','volume',1,'mL'),('oleylamine','volume',2,'mL')]],'concentrations':{},'preparation_operation_ids':['feed-mix','feed-degas'],'scope':'One shell-growth charge; component quantities repeat the feed-scoped material inventory, not extra additions. No additive-volume concentration assumed.','evidence':E(SLOC)}]
shell['material_states']=[state('seed-charge','CoO seeds in reactor oleylamine',['coo-seeds','oleylamine']),state('seed-degassed','Degassed seed mixture',['seed-charge']),state('feed-mixed','Co/Fe feed before degassing',['cobalt-acetate','iron-acetate','oleic-acid','oleylamine']),state('seeds-200','Seed dispersion at 200 °C',['seed-degassed'],'reaction_batch'),state('shell-injected','Seeds after slow feed injection',['seeds-200','co-fe-feed'],'reaction_batch'),state('shell-280','Shell-growth mixture at 280 °C',['shell-injected'],'reaction_batch')]
shell['operations']=[
 op('seed-mix','mix','Disperse CoO powder in reactor oleylamine',SLOC,['coo-seeds','oleylamine'],['seed-charge'],description='Three-neck round-bottom flask; reactor OlAm charge is 2 mL, separate from 2 mL in the feed.'),
 op('seed-degas','degas','Evacuate the seed mixture',SLOC,['seed-charge'],['seed-degassed'],['seed-mix'],{'temperature':Q(80,'degC',SLOC),'duration':Q(1,'h',SLOC),'pressure':Q(None,'Torr',SLOC)},environment=F('Evacuation',SLOC)),
 op('feed-mix','mix','Prepare a separate Co/Fe feed vial',SLOC,['cobalt-acetate','iron-acetate','oleic-acid','oleylamine'],['feed-mixed'],stage='precursor_preparation',description='0.05 mmol Co acetate, 0.1 mmol Fe acetate, 1 mL OA and 2 mL OlAm. This preparation can occur in parallel with seed degassing.'),
 op('feed-degas','degas','Degas the separate precursor feed',SLOC,['feed-mixed'],['co-fe-feed'],['feed-mix'],{'temperature':Q(80,'degC',SLOC),'duration':Q(30,'min',SLOC),'pressure':Q(None,'Torr',SLOC)},stage='precursor_preparation',description='Degassing specified; feed-vial pressure and atmosphere are not explicitly stated. Do not silently inherit reactor evacuation.'),
 op('seed-heat','heat','Heat the seed reactor under argon',SLOC,['seed-degassed','argon'],['seeds-200'],['seed-degas'],{'temperature':Q(200,'degC',SLOC),'ramp_rate':Q(None,'K/min',SLOC)},environment=F('Constant argon flow',SLOC)),
 op('feed-inject','inject','Slowly inject the prepared Co/Fe feed',SLOC,['seeds-200','co-fe-feed'],['shell-injected'],['seed-heat','feed-degas'],{'temperature':Q(200,'degC',SLOC),'injection_rate':Q(None,'mL/min',SLOC,qualifier='slowly; numerical rate and duration absent')},environment=F('Constant argon flow',SLOC)),
 op('shell-ramp','ramp','Raise the temperature to 280 °C',SLOC,['shell-injected'],['shell-280'],['feed-inject'],{'temperature':Q(280,'degC',SLOC),'ramp_rate':Q(5,'K/min',SLOC)},environment=F('Argon heating sequence',SLOC,status='inherited',note='Continuation of the stated reactor argon sequence.'))]
for t in [15,30]:
 a=f'aliquot-{t}min';pel=f'pellet-{t}min';dis=f'hexane-{t}min';s=f'saha2019-core-shell-{t}min';b=f'timepoint-{t}min'
 shell['material_states'] += [state(a,f'{t} min shell-growth aliquot',['shell-280'],'aliquot'),state(pel,f'Washed {t} min precipitate',[a],'fraction'),state(dis,f'{t} min sample in hexane',[pel,'hexane'],'product')]
 shell['operations'] += [op('collect-'+a,'anneal_sample',f'Collect an aliquot after {t} min annealing',SLOC,['shell-280'],[a],['shell-ramp'],{'annealing_temperature':Q(280,'degC',SLOC),'elapsed_annealing_time':Q(t,'min',SLOC),'aliquot_volume':Q(None,'mL',SLOC)},branch=b,description='Related aliquots of the stated growth sequence, not independent batches. Time is reported as annealing time, not total time after injection. Aliquot quench/cooling procedure absent.'),op('wash-'+a,'centrifuge_wash','Wash the aliquot once using hexane–ethanol',SLOC,[a,'hexane','ethanol'],[pel],['collect-'+a],{'wash_count':Q(1,'count',SLOC),'centrifugation_speed':Q(None,'g_relative',SLOC),'centrifugation_duration':Q(None,'min',SLOC)},stage='workup',branch=b,retained_fraction=pel,description='Precipitate retention follows the stated wash and redissolution; numerical fraction recovery is absent.'),op('redisperse-'+a,'redisperse','Redisperse the washed sample in hexane',SLOC,[pel,'hexane'],[dis],['wash-'+a],stage='workup',branch=b,description='Source says dissolved in hexane; solvent volume and final particle concentration absent.')]
 p=product(s,'CoO/CoFe2O4',E(SLOC+'; main p.2423 Figure 1'),'explicit',dis,'Cubic CoO and cubic inverse-spinel CoFe2O4',notes=['Core–shell architecture assigned by the authors; XRD alone identifies phases, not geometry.','Timepoint cohort label, not an independently replicated physical batch.'])
 p['source_sample_label']=f'CoO/CoFe2O4-{t} min'
 if t==30:
  p['link_evidence']+=E(LINK);p['morphology']=F('Almost spherical',LINK+'; Figure 2b,d');p['notes']+=['The authors select the 30 min sample for the remaining TEM and magnetic/heating measurements. Physical specimen identity across instruments is not supplied.']
 else:p['notes']+=['No distinct TEM diameter, shell thickness or magnetic value is assigned to the 15 min aliquot.']
 shell['products'].append(p)
s='saha2019-core-shell-30min'
shell['measurements']=[
 meas('shell-diameter',s,'diameter',14.9,'nm','TEM size distribution','main p.2424 and SI p.S2 Figure S1; '+LINK,'Whole core–shell particle, not the internal CoO domain diameter.'),
 meas('shell-spread',s,'diameter_spread',3.6,'nm','TEM size distribution','main p.2424 and SI p.S2 Figure S1',qualifier='reported ±; spread statistic not defined'),
 meas('shell-thickness',s,'shell_thickness',1.5,'nm','Authors estimate in magnetic discussion','main p.2424, magnetic-properties paragraph',approximate=True,qualifier='thin CoFe2O4 layer; extraction method and uncertainty not separately stated'),
 meas('shell-coo-xrd-size',s,'CoO_domain_crystallite_size',16.4,'nm','XRD / Scherrer analysis','main p.2423 Table 1',status='author_derived',qualifier='table value retained; adjacent text says overlapping phases permit approximate size only for core-only sample'),
 meas('shell-coo-a',s,'CoO_lattice_parameter_a',4.246,'angstrom','XRD','main p.2423 Table 1; p.2424 text',status='author_derived'),
 meas('shell-ferrite-a',s,'CoFe2O4_lattice_parameter_a',8.373,'angstrom','XRD','main p.2423 Table 1; p.2424 text',status='author_derived'),
 meas('shell-coo-d111',s,'CoO_interplanar_spacing_111',2.43,'angstrom','HRTEM','main Figure 2d, p.2424; SI Figure S2, p.S2'),
 meas('shell-ferrite-d311',s,'CoFe2O4_interplanar_spacing_311',2.58,'angstrom','HRTEM','main Figure 2d, p.2424; SI Figure S2, p.S2'),
 meas('shell-rt-coercivity',s,'coercivity',95,'Oe','SQUID VSM','main p.2424 and SI Figure S3a','Room temperature, 300 K; low-field inset. SI caption/legend colors conflict.',approximate=True),
 meas('shell-blocking-temperature',s,'blocking_temperature',292,'K','DC magnetization / ZFC maximum','main p.2424; SI Figure S3b','Applied field 200 Oe.',status='author_derived'),
 meas('shell-exchange-bias',s,'exchange_bias',5.6,'kOe','FC hysteresis / SQUID VSM','main pp.2422,2425; Figures 3c,4','2 K; cooling field 70 kOe. Initial cooling temperature conflicts: methods RT/300 K vs results 400 K.',status='author_derived'),
 meas('shell-lowt-coercivity',s,'coercivity',10.5,'kOe','Hysteresis / SQUID VSM','main p.2425; Figure 4b','2 K; temperature-series discussion uses 70 kOe field cooling.',status='author_derived')]
shell['quality']['missing_fields']=['No pure CoFe2O4 synthesis is reported; this is CoO/CoFe2O4 seeded core–shell growth.','Acetate hydration/solvation, seed inorganic mass fraction, vessel capacities, pressure and gas flow rates absent.','Precursor-feed degassing atmosphere, injection rate/duration and ramp rate to 200 °C absent.','Aliquot volumes, cooling/quench, solvent ratio/volumes, centrifugation speed/time and final dispersion concentrations absent.','15 min particle size, shell thickness and magnetic properties are not separately measured/reported.','No author physical batch IDs, replication count, definitive ± statistic, atomic coordinates or measured ligand coverage.']
shell['quality']['conflicts']=['Main methods p.2423 say cooling from RT (300 K); results pp.2424–2425 say 400 K.','SI Figure S3a legend: black 300 K, olive 2 K; caption reverses the color assignment.','Table 1 reports 16.4 nm for CoO in the heterostructure despite nearby text limiting reliable approximate crystallite size to core-only due to overlap.','Table 1 places TEM 14.9 nm in the CoO-from-core-shell row; Figure 2/S1 and text identify 14.9 nm as whole core–shell particle size.']
shell['quality']['experimental_outcome']='reported_product'

chars=base('saha-2019-structural-magnetic-characterization','Shared XRD, TEM and magnetic characterization of CoO/CoFe2O4','CoO/CoFe2O4','characterization procedures','procedure')
chars['lineage']['parent_record_id']=shell['record_id'];chars['quality']['requested_tasks']=[]
cloc='main p.2423, Characterization; pp.2424–2425 magnetic discussion; Figures 1–4 and SI Figures S1–S3'
chars['materials']=[material('characterization-specimen','CoO and/or CoO/CoFe2O4 specimens',None,'sample','characterization',E(cloc),notes=['Technique-specific cohorts and numerical observations are linked in the core/growth records; no separate synthetic batch inferred.']),material('tem-grid','Cu-coated holey carbon TEM grids',None,'support','characterization',E(cloc),notes=['Wording follows the source; grid loading procedure is not supplied.'])]
chars['material_states']=[state('specimen','Technique-specific specimens',['characterization-specimen'],'aliquot')]
chars['operations']=[op('xrd','xrd','Powder X-ray diffraction',cloc,['specimen'],[],qs={'wavelength':Q(1.5406,'angstrom',cloc)},stage='characterization',description='Bruker D8 Advance; Cu Kα. CoO core and 15/30 min heterostructures. Scan step/rate and specimen preparation absent.'),op('tem','tem','Bright-field TEM and HRTEM',cloc,['specimen','tem-grid'],[],qs={'accelerating_voltage':Q(200,'kV',cloc),'particles_analyzed':qty(unit='count',minimum=300,maximum=350,approximate=True,evidence=E('main p.2424'),qualifier='about 300–350 particles for size analysis; exact per-cohort count unspecified')},stage='characterization',description='Technai F30 UHR, field emission gun. CoO core and selected 30 min core–shell cohort; grid deposition/drying not specified.'),op('squid','magnetic_hysteresis','SQUID VSM hysteresis under ZFC/FC conditions',cloc,['specimen'],[],qs={'cooling_start_methods':Q(300,'K','main p.2423 Characterization',qualifier='RT in methods; conflicts with results'),'cooling_start_results':Q(400,'K','main pp.2424–2425',qualifier='results value retained; not averaged with methods'),'measurement_temperature_low':Q(2,'K',cloc),'measurement_temperature_room':Q(300,'K',cloc)},stage='characterization',description='Quantum Design SQUID VSM. 30 min cohort. Figure 3a–c: 2 K at 10/30/70 kOe cooling; d–f: 10/100/200 K at 70 kOe. Each compared to ZFC; ramp/sweep rates and sample mounting absent.'),op('dc-susceptibility','dc_magnetization','Measure FC/ZFC magnetization versus temperature',cloc,['specimen'],[],qs={'applied_field':Q(200,'Oe','main p.2424 DC susceptibility paragraph')},stage='characterization',description='SI Figure S3b. Initial cooling-field protocol and rate are not completely specified; do not transfer all hysteresis cooling conditions to this scan.')]
chars['condition_options']=[{'id':f'fig3-{panel}','label':f'Figure 3{panel}: {temp} K, {field} kOe field cooling, with ZFC comparison','parameters':{'measurement_temperature':Q(temp,'K','main p.2425 Figure 3 caption'),'cooling_field':Q(field,'kOe','main p.2425 Figure 3 caption')},'evidence':E('main p.2425 Figure 3 caption')} for panel,temp,field in [('a',2,10),('b',2,30),('c',2,70),('d',10,70),('e',100,70),('f',200,70)]]
chars['quality']['missing_fields']=['Procedure record only; no independent synthesis or new product.','XRD scan settings, specimen mounting, TEM grid loading, scan/temperature sweep rates and repeated measurements absent.','Raw diffraction/magnetization arrays and individual TEM particle measurements are not supplied.']
chars['quality']['conflicts']=shell['quality']['conflicts'][:2]

heat=base('saha-2019-magnetic-heating-assay','Alternating-field heating assay of the high-exchange-bias core–shell sample','CoO/CoFe2O4','magnetic heating assay','procedure')
heat['lineage']['parent_record_id']=shell['record_id'];heat['quality']['requested_tasks']=[]
hloc='main p.2423 Characterization and Equation 1; p.2425 heating discussion; SI p.S3 Figure S4'
heat['materials']=[material('core-shell-powder','Core–shell nanoparticles having maximum exchange bias','CoO/CoFe2O4','assay_sample','characterization',E(hloc),{'mass':Q(.8,'mg',hloc,basis='total powder, not measured suspended active fraction')},['30 min cohort selected for the remaining measurements on p.2424; actual physical vial identity not supplied.']),mat('water','assay_medium','characterization',hloc,{'volume':Q(2,'mL',hloc)})]
heat['material_states']=[state('heating-suspension','Particle suspension in water',['core-shell-powder','water'],'mixture')]
heat['operations']=[op('assay-disperse','disperse','Form the particle suspension in water',hloc,['core-shell-powder','water'],['heating-suspension'],stage='characterization',description='Dispersion method, ligand exchange, sonication, drying history and stabilization chemistry not given; authors report subsequent settling.'),op('ac-heating','magnetic_heating','Expose the suspension to alternating magnetic field',hloc,['heating-suspension'],[],['assay-disperse'],{'field_frequency':Q(500,'kHz',hloc),'field_amplitude':Q(37.4,'kA/m',hloc),'water_volumetric_heat_capacity':Q(4185,'J/L/K',hloc),'exposure_duration':Q(None,'s',hloc)},stage='characterization',description='EASYHEAT induction heating system, Ameritherm Inc.; sample in induction coil with immersed thermometer. Record temperature versus time and fit initial slope. Heat loss correction not reported.')]
p=product('saha2019-heating-suspension','CoO/CoFe2O4',E(hloc),'general_context','heating-suspension',notes=['Assay specimen, not newly synthesized product. Linked to the selected 30 min/high-EB cohort by paper context; physical specimen not identifiable.','Authors state particles are insoluble in water and settle during measurement. No active-mass correction is applied.'])
p['source_sample_label']='core–shell nanoparticles having maximum EB';heat['products']=[p]
heat['measurements']=[meas('heating-slope',p['sample_id'],'initial_heating_rate',.034,'degC/s','Linear fit to initial temperature rise','SI p.S3 Figure S4',status='author_derived',qualifier='annotation gives 0.034; unit follows temperature (°C) / time (sec) axes'),meas('heating-slp',p['sample_id'],'specific_loss_power',355,'W/g','Equation 1 and fitted initial temperature rise',hloc,status='author_derived',approximate=True,basis='normalization by all 0.8 mg powder; settling makes active suspended mass uncertain')]
heat['quality']['missing_fields']=['Procedure only, not a synthetic recipe.','Actual water dispersion method, ligand transfer, suspended fraction, thermal losses, powder inorganic fraction and run replication absent.','Raw temperature-time array and exact fit window absent; original plot retained.','Not a validated biomedical treatment; reported heating assay only.']
heat['quality']['conflicts']=['Authors describe insoluble particles settling during the assay while the SLP denominator uses the total powder mass. Both facts retained; no guessed active-mass normalization.']

records=[core,shell,chars,heat]
for r in records:
 (R/'canonical').mkdir(exist_ok=True)
 (R/'canonical'/f"{r['record_id']}.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
contributions=[{'material_system':r['material']['formula'],'elements':r['material']['elements'],'contains_materials':r['material']['components'],'architecture':r['material']['architecture'],'primary_record_id':r['record_id'],'source':{'doi':DOI,'url':'https://doi.org/'+DOI},'contribution_type':'synthesis_protocol' if r['record_type']!='procedure' else 'shared_procedure','component_hub_note':'CoFe2O4 occurs as a shell; this paper does not provide a pure CoFe2O4 product recipe.'} for r in records]
(R/'material-contributions.json').write_text(json.dumps(contributions,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
 from dataset_lib import validate_record,eligibility
 validation={'schema_version':'1.0.0','records':[{'record_id':r['record_id'],'errors':validate_record(r),'eligibility':eligibility(r)} for r in records]}
 validation['passed']=all(not x['errors'] for x in validation['records'])
 (R/'record-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(validation,ensure_ascii=False))
