"""Source-linked Peng 1998 main/SI extraction, staged for independent audit."""
from pathlib import Path
from copy import deepcopy
import json, sys
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='peng1998'; PREFIX='peng-1998-'
SRC=source(SID,'10.1021/ja9805425','Kinetics of II-VI and III-V Colloidal Semiconductor Nanocrystal Growth: “Focusing” of Size Distributions','Xiaogang Peng; J. Wickham; A. P. Alivisatos',1998,si='Matched supplied SI: DOI cover plus three scientific pages; text and visuals reviewed, independent audit pending.')
SRC['main_status']='All two supplied main pages text and visually reviewed; independent audit pending.'
def E(p,loc): return ev(SID,f'Main PDF p. {p}, printed p. {5342+p}, {loc}')
def I(p,loc): return ev(SID,f'SI PDF p. {p+1}, supplemental p. {p}, {loc}')
CD=E(1,'Note 21'); IN=E(1,'Note 22'); DISC=E(2,'Growth-distribution discussion')
def Q(v=None,u='',e=CD,**kw): return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=CD,**kw): return fact(v,deepcopy(e),**kw)
CHEM={'topo':('Trioctylphosphine oxide','C24H51OP'),'tbp':('Tributylphosphine','C12H27P'),'se':('Selenium','Se'),'cdme2':('Dimethylcadmium','C2H6Cd'),'argon':('Argon','Ar'),'methanol':('Methanol','CH4O'),'toluene':('Toluene','C7H8'),'top':('Trioctylphosphine','C24H51P'),'incl3':('Indium(III) chloride','InCl3'),'tms3as':('Tris(trimethylsilyl)arsine','C9H27AsSi3'),'incl3-top':('Concentrated InCl3 in TOP',None),'cdse':('CdSe growth-mixture aliquot','CdSe'),'inas':('InAs growth-mixture aliquot','InAs')}
def C(i,role='solvent',stage='synthesis',e=CD,**kw): return material(i,*CHEM[i],role,stage,deepcopy(e),**kw)
def base(key,title,formula='CdSe',kind='procedure',method='Supporting procedure'):
 r=record(PREFIX+key,'Peng et al. (1998) · '+title,formula,'Colloidal semiconductor nanocrystals',method,deepcopy(SRC),'Main PDF pp. 1–2; matched SI PDF pp. 1–4',kind)
 r['schema_version']='1.3.0'; r['collection']='reviewed_literature';r['lineage']['recipe_family']='peng1998-'+formula.lower()+'-focusing'
 r['intended_target']['composition']=F(formula if kind=='literature_protocol' else None,e=CD if formula=='CdSe' else IN,note='' if kind=='literature_protocol' else 'Supporting procedure or evidence context; not an independently specified synthesis target.')
 r['quality'].update(review_status='imported_unreviewed',requested_tasks=['precursor_selection','partial_protocol'] if kind=='literature_protocol' else [],review_scope='Private full two-page main plus matched four-page SI review. Independent audit and publication pending.',missing_fields=['No author-assigned physical batch IDs or complete cross-technique sample joins.','No measured lattice phase, atomic coordinates or exact experimental CIF supplied.'],conflicts=['CdSe baseline stock gives Se:Cd(CH3)2:tributylphosphine = 2:5:100 by mass; discussion separately describes Cd:Se about 1.4:1 by mole. Preserve both approximate descriptions without replacing either.','Main Figure 3 shows 8.5 nm CdSe by TEM; no demonstrated specimen join to the smaller-particle Figure 1/2 kinetic trajectory.'],experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
 r['context_links']=[{'label':'Complete main and SI review','url':'../paper-review.html?id=peng1998','relation':'Two main pages and matched SI: cover plus three scientific pages.'}]
 return r
def link(r,key,label,relation): r['context_links'].append({'label':label,'url':'../records/'+PREFIX+key+'.html','relation':relation})
def add(r,i,action,label,inputs,out,e=CD,params=None,depends=None,stage='synthesis',description='',environment=None,branch='main',kind='mixture'):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out] if out else [],depends=depends,parameters=params or {},stage=stage,description=description,environment=F(environment,e),branch=branch))
def stock(i,label,parts,e,scope,concs=None):return {'id':i,'name':label,'components':[{'material_id':k,'quantities':{'mass_parts':Q(v,'mass part',e=e)} if v is not None else {}}for k,v in parts],'concentrations':concs or {},'preparation_operation_ids':[],'scope':scope,'evidence':deepcopy(e)}
def P(r,i,label,formula,e,sid=None,explicit=False,notes=None):
 p=product(i,formula,deepcopy(e),link='explicit' if explicit else 'general_context',state=sid,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
def M(r,i,s,prop,v,u,e,tech='Source-reported observation',conditions='',**kw):
 r['measurements'].append(measurement(i,s,prop,Q(v,u,e=e,**kw),tech,deepcopy(e),conditions))
def T(r,i,s,prop,text,e,tech='Source-reported observation',conditions=''):
 r['measurements'].append(measurement(i,s,prop,F(text,e),tech,deepcopy(e),conditions))
records=[]

r=base('cdse-focusing','CdSe growth with precursor reinjection','CdSe','literature_protocol','Hot injection · size-distribution focusing')
r['materials']=[C('topo','coordinating solvent',quantities={'mass':Q(4,'g')}),C('tbp','coordinating solvent'),C('se','chalcogen_precursor'),C('cdme2','metal_precursor'),C('argon','atmosphere'),C('methanol','antisolvent',stage='workup',notes=['For timed aliquots only; not a whole-batch isolation charge.']),C('toluene','optical solvent',stage='characterization',notes=['For purified aliquot redissolution.'])]
r['stocks']=[stock('cdse-feed','Cold CdSe precursor feed',[('se',2),('cdme2',5),('tbp',100)],CD,'Reported Se:Cd(CH3)2:tributylphosphine mass ratio. No total batch mass, molarity, density, selenium dissolution procedure or exact cold temperature supplied. The source labels Se; phosphine-selenium speciation is not established here.')]
add(r,'prepare-stock','precursor_stock','Prepare the cold precursor feed',['se','cdme2','tbp'],'feed-ready',stage='precursor_preparation',description='Composition 2:5:100 by mass. Preparation order, temperature, time and selenium speciation are unreported; this composition does not justify an elemental Se bottle injected alone.')
add(r,'heat','heat','Heat TOPO under flowing argon',['topo','argon'],'hot-topo',params={'temperature':Q(360,'degC'),'topo_mass':Q(4,'g')},environment='Flowing Ar',description='Heating apparatus, pressure, argon flow rate and heating duration unreported. Rapid stirring is specified at injection.')
add(r,'injection','hot_injection','Rapidly inject the cold feed',['hot-topo','feed-ready'],'nucleating',params={'injection_volume':Q(2.4,'mL'),'injection_duration_upper_bound':Q(u='s',maximum=.1,maximum_exclusive=True,raw_text='<0.1 s'),'post_injection_temperature':Q(300,'degC')},depends=['prepare-stock','heat'],description='Inject in less than 0.1 s into rapidly stirred hot TOPO; the injection lowers the temperature from 360 to 300 °C. No separate active cooling action is asserted.')
add(r,'grow','growth','Follow growth and withdraw timed aliquots',['nucleating'],'grown',depends=['injection'],params={'growth_temperature':Q(300,'degC',e=CD+DISC,status='inferred',basis='Nominal growth temperature inferred from the post-injection 300 °C; a maintained hold is not independently reported'),'elapsed_time_before_reinjection':Q(190,'min')},description='Aliquot preparation is a separate branch. Focusing, subsequent defocusing and refocusing describe one monitored growth trajectory; they are not selectable independent batches.')
add(r,'refeed','precursor_reinjection','Slowly reinject the same stock',['grown','feed-ready'],'refocused',depends=['grow'],params={'injection_volume':Q(.8,'mL'),'elapsed_time_from_first_injection':Q(190,'min'),'injection_rate':Q(u='mL/min',qualifier='slowly; numeric rate unreported')},description='This is a second injection into the same reaction. End-of-growth workup and a final stopping time are not supplied. Figure 1 includes observations through 240 min.')
for key,label,params in [
 ('reduced-first-injection','About 15% less initial feed; other conditions unchanged',{'initial_feed_reduction':Q(15,'%',e=DISC,approximate=True)}),
 ('cd-rich','Cd:Se = 1.9:1 comparison',{'cadmium_to_selenium_molar_ratio':Q(1.9,'mol/mol',e=DISC)}),
 ('near-equimolar','Cd:Se = 1.1:1 comparison',{'cadmium_to_selenium_molar_ratio':Q(1.1,'mol/mol',e=DISC)}),
 ('near-equimolar-concentrated','Cd:Se = 1.1:1 with almost doubled Cd and Se concentrations',{'cadmium_to_selenium_molar_ratio':Q(1.1,'mol/mol',e=DISC),'cd_and_se_concentration_multiplier':Q(2,'relative factor',e=DISC,qualifier='almost doubled; not exactly twofold',approximate=True)})]:r['condition_options'].append({'id':key,'label':label,'parameters':params,'evidence':DISC})
r['quality']['missing_fields']+=['Comparison conditions are partial source reports, not complete independent recipes; adjusted absolute charges and general reinjection applicability are unreported.','No final whole-batch purification or isolation protocol; only timed aliquot workup is specified.']
P(r,'cdse-growth-series','Figures 1 and 2 left: monitored CdSe growth','CdSe',E(1,'CdSe kinetics paragraph')+CD,sid='refocused',explicit=True,notes=['Series-level protocol linkage, not a single final size or measured batch ID. No connection to 8.5 nm TEM specimen established.'])
link(r,'cdse-aliquot-analysis','CdSe aliquot preparation and spectroscopy','Separate withdrawals from the monitored reaction; not isolation of the complete batch.')
link(r,'cdse-kinetics','CdSe growth observations and condition comparisons','Time-dependent and condition-specific evidence; not all associated with one endpoint.');records.append(r)

r=base('inas-focusing','InAs growth with sequential precursor injections','InAs','literature_protocol','Hot injection · size-distribution focusing')
r['materials']=[C('top','coordinating solvent',e=IN,quantities={'reactor_charge_mass':Q(2,'g',e=IN)},notes=['Distilled TOP explicitly specified for the upstream InCl3 stock.']),C('incl3','metal_precursor',e=IN,notes=['Prepared as concentrated InCl3 in TOP; see separate upstream record.']),C('tms3as','nonmetal_precursor',e=IN),C('toluene','optical solvent',stage='characterization',e=IN,notes=['For timed aliquot dilution; volume unreported.'])]
r['stocks']=[stock('inas-feed','Cold InAs precursor feed',[('tms3as',1),('incl3',1.1),('top',2.8)],IN,'TMS3As:InCl3:TOP = 1:1.1:2.8 by mass. Total preparation mass, temperature described as cold, mixing order and the exact relation of TOP solvent accounting to the concentrated upstream InCl3 stock are unreported.')]
add(r,'prepare-feed','precursor_stock','Prepare the cold InAs precursor feed',['tms3as','incl3','top'],'feed-ready',IN,stage='precursor_preparation',description='Use the source mass ratio 1:1.1:2.8. The InCl3/TOP preparation is linked separately; do not infer stoichiometric coordination geometry or a complete stock-mixing procedure.')
add(r,'heat','heat','Heat the TOP reactor charge',['top'],'hot-top',IN,params={'temperature':Q(300,'degC',e=IN),'top_mass':Q(2,'g',e=IN)},description='Growth-reactor atmosphere, pressure, stirring rate and heating time are not independently specified; argon is explicitly reported for the upstream InCl3 stock only.')
add(r,'injection','hot_injection','Rapidly inject the cold InAs feed',['hot-top','feed-ready'],'nucleating',IN,params={'injection_volume':Q(1,'mL',e=IN),'injection_duration_upper_bound':Q(u='s',e=IN,maximum=.1,maximum_exclusive=True,raw_text='<0.1 s'),'initial_post_injection_temperature':Q(250,'degC',e=IN)},depends=['prepare-feed','heat'])
add(r,'recover','temperature_adjustment','Continue growth at 260 °C',['nucleating'],'growth-temperature',IN,params={'temperature':Q(260,'degC',e=IN)},depends=['injection'],description='The initial post-injection temperature is 250 °C; growth is reported at 260 °C. Ramp rate and time to recover are unreported.')
add(r,'grow','growth','Grow and sample before the next injection',['growth-temperature'],'grown',IN,params={'elapsed_time_to_next_injection':Q(23,'min',e=IN,basis='Since first injection; not an extra 23-minute hold after temperature recovery')},depends=['recover'],description='Timed aliquots are diluted in toluene; no CdSe methanol workup is inherited.')
add(r,'refeed1','precursor_reinjection','Add the second feed aliquot',['grown','feed-ready'],'refed1',IN,params={'injection_volume':Q(.5,'mL',e=IN),'elapsed_time_from_first_injection':Q(23,'min',e=IN)},depends=['grow'],description='Additional injection at 23 min; speed and temperature of this feed aliquot are not individually reported.')
add(r,'continue','growth','Continue the same InAs growth trajectory',['refed1'],'continued',IN,params={'temperature':Q(260,'degC',e=IN),'next_injection_elapsed_time':Q(158,'min',e=IN,basis='Since first injection; not 158 minutes after the second feed')},depends=['refeed1'])
add(r,'refeed2','precursor_reinjection','Add the third feed aliquot',['continued','feed-ready'],'refed2',IN,params={'injection_volume':Q(.8,'mL',e=IN),'elapsed_time_from_first_injection':Q(158,'min',e=IN)},depends=['continue'],description='This is the third injection in the same run. No final isolation procedure or preparative stopping time is given; SI absorption observations extend to t=245.')
P(r,'inas-growth-series','Figure 2 right and SI InAs spectra','InAs',IN+E(2,'Figure 2')+I(2,'InAs spectra'),sid='refed2',explicit=True,notes=['Series-level protocol linkage; no individual final-size label or absolute yield assigned.'])
link(r,'incl3-top-stock','InCl3/TOP stock preparation','Explicit upstream heating, cooling and drybox storage.');link(r,'inas-aliquot-analysis','InAs aliquot spectroscopy','Source-specific dilution without an asserted precipitation step.');link(r,'inas-kinetics','InAs growth observations','Spectrum times and qualitative focusing remain separate from calibration rows.');records.append(r)

r=base('incl3-top-stock','Concentrated InCl3/TOP stock preparation','InAs')
r['materials']=[C('incl3','metal precursor',stage='precursor_preparation',e=IN),C('top','coordinating solvent',stage='precursor_preparation',e=IN,notes=['Distilled TOP; the source does not describe distillation conditions.']),C('argon','atmosphere',stage='precursor_preparation',e=IN)]
r['stocks']=[stock('incl3-top-stock','InCl3 in distilled TOP',[('incl3',None),('top',None)],IN,'0.33 g InCl3 per mL TOP, a solvent-volume basis, not a demonstrated final-solution molarity. Total prepared volume and ligand coordination structure are unreported.',{'incl3_per_top_volume':Q(.33,'g/mL',e=IN,basis='grams InCl3 per mL TOP')})]
add(r,'heat','heated_stock_preparation','Heat InCl3 in distilled TOP',['incl3','top','argon'],'hot-stock',IN,params={'temperature':Q(260,'degC',e=IN),'incl3_per_top_volume':Q(.33,'g/mL',e=IN,basis='solvent-volume basis')},stage='precursor_preparation',environment='Argon',description='Heating duration and total prepared amount unreported.')
add(r,'cool','cooling','Cool the concentrated solution',['hot-stock'],'cooled-stock',IN,depends=['heat'],stage='precursor_preparation',description='Final temperature, cooling rate and duration unreported.')
add(r,'store','drybox_storage','Transfer the cooled stock to drybox storage',['cooled-stock'],'stored-stock',IN,depends=['cool'],stage='storage',environment='Drybox; internal gas composition unreported',description='Storage temperature and duration unreported. Do not inherit −35 °C from another paper or precursor.')
P(r,'incl3-top-stock','Concentrated InCl3·TOP solution','InCl3 in TOP',IN,sid='stored-stock',explicit=True,notes=['Source notation InCl3·TOP does not establish an isolated crystalline adduct or a unique coordination structure.']);records.append(r)

r=base('cdse-aliquot-analysis','CdSe aliquot purification and optical analysis')
r['materials']=[C('cdse','analytical specimen',stage='characterization'),C('methanol','antisolvent',stage='workup'),C('toluene','optical solvent',stage='characterization')]
add(r,'withdraw','aliquot_sampling','Withdraw a timed reaction aliquot',['cdse'],'aliquot',params={'aliquot_volume':Q(.2,'mL')},stage='characterization',kind='aliquot',description='Repeated at various reaction times; individual time points do not become separate synthesis replicates.')
add(r,'precipitate','precipitation','Precipitate the aliquot in methanol',['aliquot','methanol'],'precipitate',params={'methanol_volume':Q(2,'mL')},depends=['withdraw'],stage='workup')
add(r,'purify','purification','Purify and determine aliquot mass and particle yield',['precipitate'],'purified',depends=['precipitate'],stage='workup',description='Remove excess TOPO, byproducts and solvent before mass/particle-yield determination. Separation technique, washes, drying method, balance and yield calculation are unreported; no centrifugation or numerical yield invented.')
add(r,'redissolve','redissolution','Redissolve the nanocrystals in toluene',['purified','toluene'],'optical-sample',depends=['purify'],stage='characterization',description='Solvent volume and nanocrystal concentration unreported.')
add(r,'adjust-od','optical_density_adjustment','Set optical density for PL',['optical-sample'],'pl-sample',depends=['redissolve'],stage='characterization',params={'optical_density':Q(.09,'dimensionless',qualifier='±0.02'),'optical_density_tolerance':Q(.02,'dimensionless',basis='reported ± tolerance')},description='OD 0.09 ± 0.02 for every PL sample. Wavelength used to set OD, cuvette path length and method of adjustment unreported.')
add(r,'measure','optical_spectroscopy','Measure absorption and photoluminescence',['pl-sample'],'spectra',CD+E(2,'Figure 1 caption'),depends=['adjust-od'],stage='characterization',environment='Room-temperature measurements',description='UV–vis and PL in toluene. Excitation wavelength, instruments and spectral resolution unreported. Figure 1 spectra are normalized/offset as displayed; no raw intensities reconstructed.')
P(r,'cdse-optical-aliquots','Purified CdSe aliquots in toluene','CdSe',CD,sid='pl-sample',notes=['Series-level analytical preparation; physical identity of individual spectra is defined by source time labels only.']);link(r,'cdse-focusing','CdSe synthesis','Parent reaction series.');records.append(r)

r=base('inas-aliquot-analysis','InAs aliquot optical analysis','InAs')
r['materials']=[C('inas','analytical specimen',stage='characterization',e=IN),C('toluene','optical solvent',stage='characterization',e=IN)]
add(r,'withdraw','aliquot_sampling','Withdraw a timed InAs aliquot',['inas'],'aliquot',IN,params={'aliquot_volume':Q(u='mL',e=IN)},stage='characterization',kind='aliquot')
add(r,'dilute','dilution','Dilute the aliquot in toluene',['aliquot','toluene'],'optical-sample',IN,depends=['withdraw'],stage='characterization',description='Dilution volume unreported. No precipitation, purified-particle redissolution or target OD is specified for InAs.')
add(r,'measure','optical_spectroscopy','Record InAs absorption and PL',['optical-sample'],'spectra',IN+I(2,'InAs spectra and note'),depends=['dilute'],stage='characterization',environment='PL at room temperature; absorption temperature not specified',description='Because of reabsorption around 1 eV on the low-energy side, only the higher-energy PL half is used for size distribution and standard deviation. Do not treat that restriction as a symmetric raw spectrum or assign acquisition conditions from CdSe.')
P(r,'inas-optical-aliquots','InAs aliquots diluted in toluene','InAs',IN,sid='optical-sample');link(r,'inas-focusing','InAs synthesis','Parent reaction series.');records.append(r)

r=base('pl-size-analysis','PL-based size-distribution analysis','CdSe/InAs')
analysis=E(1,'Optical sizing assumptions')+I(1,'CdSe calibration table')+I(3,'InAs calibration table')
r['materials']=[material('spectra','CdSe or InAs PL spectra',None,'analytical input','characterization',analysis)]
add(r,'calibrate','optical_calibration','Use the appropriate TEM-calibrated energy–size relation',['spectra'],'calibrated',analysis,stage='characterization',description='CdSe and InAs use separate SI tables; prior calibration sources are main references 5, 7 and 9. These rows are calibration pairs, not documented syntheses in this paper.')
add(r,'convert','spectral_size_conversion','Convert the PL distribution to size space',['calibrated'],'size-distribution',analysis+I(2,'High-energy-half note'),depends=['calibrate'],stage='characterization',description='Assume delta-function emission for each single size and equal emission efficiency across sizes. The authors say both assumptions systematically overestimate distribution widths. InAs uses only the high-energy PL half due reabsorption; interpolation, fitting and normalization implementation unreported.')
add(r,'moments','distribution_moments','Report mean size and variance',['size-distribution'],'moments',analysis,depends=['convert'],stage='characterization',description='First and second moments only; third moment/asymmetry is not determined. Figure 2 displays mean size and standard deviation in percent. These are optical calibration-derived sizes, not new TEM measurements of every aliquot.')
P(r,'analysis-context','Optical size-distribution method',None,analysis,notes=['Mathematical analysis context, not a physical nanocrystal batch.']);link(r,'cdse-calibration','CdSe calibration table','Sixteen reported calibration rows.');link(r,'inas-calibration','InAs calibration table','Twenty reported calibration rows.');records.append(r)

r=base('cdse-kinetics','CdSe growth trajectory and concentration comparisons','CdSe','observation','Growth-kinetics evidence')
e=E(1,'CdSe kinetics paragraph')
P(r,'cdse-trajectory','Figures 1 and 2 left / main-text kinetics','CdSe',e,notes=['Same monitored growth experiment, multiple correlated time points. PL-based sizing; exact sample IDs not supplied.'])
for i,prop,v,u,scope in [('initial-size','optically_estimated_mean_diameter',2.1,'nm','Initial reported size; exact sampling timestamp not given in prose.'),('initial-spread','relative_size_standard_deviation',20,'%','Initial distribution.'),('focused-time','focusing_time',22,'min','First focusing regime.'),('focused-size','optically_estimated_mean_diameter',3.3,'nm','At first focused state, 22 min.'),('focused-spread','relative_size_standard_deviation',7.7,'%','At first focused state, 22 min.'),('defocused-size','optically_estimated_mean_diameter',3.9,'nm','Later defocusing regime before the 190-min reinjection.'),('defocused-spread','relative_size_standard_deviation',10.6,'%','Defocusing regime.'),('refocused-spread','relative_size_standard_deviation',8.7,'%','After second injection; exact endpoint time not stated in prose.')]:M(r,i,'cdse-trajectory',prop,v,u,e,tech='PL distribution with prior TEM calibration',conditions=scope)
T(r,'particle-number','cdse-trajectory','particle_number_trend','Particle count remains constant during focusing/refocusing and decreases during defocusing.',e,'Particle-yield inference')
T(r,'monomer-trend','cdse-trajectory','monomer_concentration_trend','Inferred monomer concentration drops during focusing/refocusing and is approximately constant during defocusing.',e,'Inference from particle yield',conditions='Not a directly measured solution-concentration trace or quantified yield table.')
for t in [.2,1,12,35,55,190,210,240]:M(r,'figure1-time-'+str(t).replace('.','p'),'cdse-trajectory','spectrum_time_label',t,'min',E(2,'Figure 1 labels'),tech='Original source plot',conditions='Displayed time label only; peak position and intensity not digitized.')
for sid,label in [('reduced-feed','About 15% smaller first injection'),('cd-rich','Cd:Se 1.9:1'),('near-equimolar','Cd:Se 1.1:1'),('near-equimolar-concentrated','Cd:Se 1.1:1; nearly doubled Cd and Se concentrations')]:P(r,sid,label,'CdSe',DISC,notes=['Separate condition context; no exact author-assigned batch or complete variant recipe.'])
M(r,'reduced-focusing-time','reduced-feed','focusing_time',11,'min',DISC);M(r,'reduced-focused-size','reduced-feed','optically_estimated_mean_diameter',2.7,'nm',DISC,tech='Source-reported optical sizing');M(r,'baseline-ratio','cdse-trajectory','cadmium_to_selenium_molar_ratio',1.4,'mol/mol',DISC,approximate=True)
M(r,'rich-ratio','cd-rich','cadmium_to_selenium_molar_ratio',1.9,'mol/mol',DISC);T(r,'rich-stability','cd-rich','distribution_stability','Focused nanocrystals can remain at growth temperature for hours before defocusing.',DISC,conditions='No exact duration, final size or temperature-specific stability experiment reconstructed.')
M(r,'lean-ratio','near-equimolar','cadmium_to_selenium_molar_ratio',1.1,'mol/mol',DISC);T(r,'lean-defocusing','near-equimolar','distribution_trend','Defocusing is rapid at the reported 1.1:1 comparison.',DISC)
T(r,'lean-concentrated','near-equimolar-concentrated','concentration_effect','The authors report obtaining a tight distribution by almost doubling both Cd and Se concentrations at 1.1:1.',DISC,conditions='Exact concentrations, width, size and timing unreported.')
link(r,'cdse-focusing','CdSe protocol and condition comparisons','Series/condition links do not turn all observations into one final product.');records.append(r)

r=base('inas-kinetics','InAs growth trajectory and spectra','InAs','observation','Growth-kinetics evidence')
e=IN+E(2,'Figure 2 right')+I(2,'InAs absorption and PL spectra')
P(r,'inas-trajectory','Figure 2 right and SI supplemental p. 2','InAs',e,notes=['Same synthesis time series; only source-stated numbers/labels transcribed, no digitized mean/width curve.'])
T(r,'focusing-trend','inas-trajectory','size_distribution_evolution','InAs shows growth focusing, defocusing and refocusing analogous to CdSe.',E(1,'InAs kinetics statement'),conditions='No transfer of CdSe 7.7%, 8.7% or 22-min values to InAs.')
for tech,times in [('absorption',[18,28,43,158,176,245]),('pl',[23,28,80,158,176])]:
 for t in times:M(r,f'{tech}-time-{t}','inas-trajectory',tech+'_spectrum_time_label',t,'min',I(2,'InAs '+tech+' panel'),tech='Original source plot',conditions='t labels interpreted in minutes from the main kinetic experiment; SI panel itself omits time units. These are distinct displayed sampling sets, not inferred pairwise simultaneous spectra.')
M(r,'reabsorption-energy','inas-trajectory','reabsorption_affected_energy',1,'eV',I(2,'Note below PL panel'),approximate=True)
T(r,'high-half-only','inas-trajectory','analysis_window','Only the higher-energy half of PL was used for size distribution and standard deviation because of low-energy-side reabsorption.',I(2,'Note below PL panel'))
link(r,'inas-focusing','InAs synthesis','Three sequential injections; source labels preserve elapsed times.');link(r,'pl-size-analysis','PL analysis assumptions','Calibration-derived mean and spread, not independent TEM measurements.');records.append(r)

r=base('cdse-tem','TEM of an 8.5 nm CdSe specimen','CdSe','observation','Structural characterization')
e=E(2,'Figure 3 and caption')
p=P(r,'tem-8p5','Figure 3 CdSe TEM specimen','CdSe',e,notes=['Prepared by distribution focusing but no full sample-specific recipe, injection sequence, growth time or join to Figures 1/2 supplied.']);p['morphology']=F('Faceted nanocrystals',E(1,'Faceting statement')+e)
M(r,'tem-diameter','tem-8p5','diameter',8.5,'nm',e,tech='TEM caption');M(r,'tem-scale','tem-8p5','image_scale_bar',25,'nm',e,tech='Original TEM image');records.append(r)

CD_ROWS=[(484,2.47,2.1),(488,2.46,2.1),(516,2.34,2.4),(526,2.30,2.6),(534,2.27,2.7),(542,2.24,2.9),(550,2.21,3.1),(560,2.17,3.3),(566,2.16,3.4),(570,2.14,3.5),(576,2.09,3.6),(596,2.04,4.3),(600,2.03,4.4),(606,2.02,4.6),(608,2.01,4.7),(610,2.00,4.8)]
IN_ROWS=[(838,1.41,2.3),(861,1.38,2.4),(886,1.34,2.6),(905,1.31,2.8),(929,1.28,3.0),(954,1.24,3.2),(976,1.22,3.4),(1004,1.19,3.6),(1029,1.16,3.8),(1051,1.13,4.0),(1078,1.10,4.2),(1107,1.08,4.4),(1132,1.05,4.6),(1159,1.03,4.8),(1187,1.01,5.0),(1216,.98,5.2),(1246,.96,5.4),(1272,.94,5.6),(1305,.92,5.8),(1333,.90,6.0)]
for formula,rows,page in [('CdSe',CD_ROWS,1),('InAs',IN_ROWS,3)]:
 r=base(formula.lower()+'-calibration',formula+' optical/TEM calibration',formula,'observation','Calibration evidence')
 for n,(uv,pl,size) in enumerate(rows,1):
  e=I(page,f'{formula} calibration table, data row {n}')
  sid=f'calibration-row-{n:02}'
  P(r,sid,f'{formula} calibration row {n}',formula,e,notes=['Literature calibration row; no recipe, reaction timestamp or physical sample identity supplied. Not a new synthesis run or an output of the current feed sequence.'])
  M(r,f'uv-{n:02}',sid,'calibration_absorption_exciton_peak',uv,'nm',e,tech='SI calibration table')
  M(r,f'pl-{n:02}',sid,'calibration_pl_peak_energy',pl,'eV',e,tech='SI calibration table')
  M(r,f'size-{n:02}',sid,'calibration_tem_size',size,'nm',e,tech='TEM-calibrated size as table heading',conditions='Source table labels Size (nm); main discussion uses diameter. No independent measured phase or exact coordinates.')
 records.append(r)

r=base('growth-model','Diffusion-limited growth and focusing interpretation','CdSe/InAs','observation','Chemical intuition · author model')
e=E(1,'Gibbs–Thomson equation and definitions')+E(2,'Growth-rate equation, Figure 4 and discussion')
P(r,'model','Diffusion-limited growth interpretation',None,e,notes=['Author theoretical context; not a physical material specimen or fitted numerical kinetic model.'])
for key,prop,value in [
 ('gibbs-thomson','model_equation','Sr = Sb exp(2σVm/(rRT)); Sr and Sb are nanocrystal and bulk solubilities; σ surface energy; Vm molar volume; r radius; R gas constant; T temperature.'),
 ('growth-rate','model_equation','dr/dt = K(1/r + 1/δ)(1/r* − 1/r), under 2σVm/(rRT) ≪ 1. K is proportional to monomer diffusion constant, δ diffusion-layer thickness, r* the equilibrium critical radius at fixed monomer concentration.'),
 ('figure4-limit','model_plot_scope','Figure 4 takes infinite diffusion-layer thickness. Its dimensionless horizontal coordinate is r/r* and its growth rate is in arbitrary units; it is not a measured time series.'),
 ('focusing','author_interpretation','At appropriate high monomer concentration, particles in the distribution are slightly larger than critical radius; smaller particles can grow faster, narrowing the distribution.'),
 ('defocusing','author_interpretation','Monomer depletion increases critical size; smaller particles dissolve while larger ones grow, broadening the distribution through Ostwald ripening.'),
 ('refocusing','author_interpretation','Precursor replenishment at growth temperature lowers the critical size and refocuses the size distribution.'),
 ('automation','author_outlook','Continuous monitoring and adjustment of monomer concentration is proposed as an optimal growth strategy. This paper does not report an implemented closed-loop automated controller.'),
 ('generality','author_scope_statement','Authors state that analogous effects apply to CdS and InP and presume broader II–VI/III–V applicability; no CdS or InP recipe or data is supplied here.'),
 ('nucleation','author_interpretation','Nucleation starts rapidly after injection and continues until temperature and monomer concentration fall below a critical threshold; no threshold value or resolved nucleation kinetic trace supplied.')]:T(r,key,'model',prop,value,e,tech='Author model, interpretation or outlook')
records.append(r)

if __name__=='__main__':
 out=B/'canonical-drafts';out.mkdir(exist_ok=True);errors=[]
 for r in records:
  errors+=validate_record(r)
  (out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report={'status':'failed' if errors else 'passed','records':len(records),'operations':sum(len(r['operations']) for r in records),'measurements':sum(len(r['measurements']) for r in records),'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
 if errors:raise SystemExit(1)
