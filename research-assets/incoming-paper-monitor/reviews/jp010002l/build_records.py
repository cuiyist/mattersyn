"""Braun, Burda and El-Sayed 2001: complete supplied four-page main-source extraction.
Private drafts only. No missing salt, stabilizer formulation, workup or structure is inferred.
"""
from pathlib import Path
from copy import deepcopy
import json,sys,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='braun2001';GROUP='braun2001';PRE='braun-2001-';FORMULA='CdS/HgS/CdS'
SRC=source(SID,'10.1021/jp010002l','Variation of the Thickness and Number of Wells in the CdS/HgS/CdS Quantum Dot Quantum Well System','Markus Braun; Clemens Burda; Mostafa A. El-Sayed',2001,si='No SI supplied or independently matched. SI existence/availability is not established from this supplied four-page main article; no SI was inspected.')
SRC['main_status']='Complete supplied four-page main article read as extracted text and original page images; independent audit pending.'
def E(p,s):return ev(SID,f'Main PDF p. {p}, printed p. {5547+p}, {s}')
A=E(1,'Sample Preparation, step A')+E(2,'Sample Preparation, continuation of step A')
BE=E(2,'Sample Preparation, step B');CE=E(2,'Sample Preparation, step C');EXP=E(1,'Experimental Section, optical methods')
F1=E(2,'Figure 1 and system dimensions');F2=E(2,'Absorption Spectra')+E(3,'Figure 2');F3=E(3,'Figure 3 and Emission Spectra');F4=E(3,'Energy Dependence of the Relaxation Dynamics')+E(4,'Figure 4 and continued discussion')
def Q(v=None,u='',e=A,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=A,**kw):return fact(v,deepcopy(e),**kw)
CHEM={
 'cd2':('Aqueous cadmium(II) ions; precursor salt and counterion unspecified','Cd2+'),
 'hg2':('Aqueous mercury(II) ions; precursor salt and counterion unspecified','Hg2+'),
 'hexametaphosphate':('Hexametaphosphate stabilizer; counterion, exact supplied form and amount unspecified',None),
 'h2s':('Hydrogen sulfide; gas in step A and dissolved solute in step C','H2S'),
 'h2s-aqueous':('Hydrogen sulfide in water; concentration and injection volume unspecified',None),
 'water':('Water; aqueous synthesis medium and optical reference','H2O'),
 'argon':('Argon; step-A atmosphere and excess-H2S removal gas','Ar'),
 'specimen':('Selected source-scoped CdS/HgS quantum-dot quantum-well dispersion',None),
 'system-i-specimen':('System I: single HgS monolayer well in CdS',FORMULA),
 'system-ii-specimen':('System II: double-layer HgS well in CdS',FORMULA),
 'system-iii-specimen':('System III: two separated HgS monolayer wells in CdS',FORMULA),
}
def C(i,role,stage='synthesis',e=A,notes=None):return material(i,*CHEM[i],role,stage,deepcopy(e),notes=notes or [])
def base(k,title,kind='observation',method='Source-scoped characterization and interpretation'):
 r=record(PRE+k,'Braun et al. (2001) · '+title,FORMULA,'Semiconductor quantum-dot quantum-well heterostructures',method,deepcopy(SRC),'Complete supplied main PDF pp. 1–4',kind)
 r['schema_version']='1.3.0';r['collection']='reviewed_literature';r['material'].update(elements=['Cd','Hg','S'],components=['CdS','HgS'],architecture='heterostructure')
 r['lineage'].update(source_group=GROUP,recipe_family='braun2001-cds-hgs-qdqw')
 r['intended_target']['composition']=F(FORMULA if kind=='literature_protocol' else None,e=F1,note='Material descriptor denotes a layered heterostructure, not an overall stoichiometric formula or a measured atomic model.')
 r['quality'].update(review_status='imported_unreviewed',review_scope='All four main pages read and visually inspected. Independent audit and website integration pending. No SI supplied or independently matched.',missing_fields=['Cd and Hg precursor salts/counterions, hexametaphosphate counterion and dose, preparation of H2S/water stock, and pH-adjustment reagents are not reported.','No current-paper TEM micrograph, XRD/SAED pattern, refined phase, unit cell or atomic-coordinate file. Figure 1 is a schematic and cites earlier theory/morphology.','Synthesis temperature, detailed growth timing, final workup/isolation, yield and physical-batch identifiers are not supplied. Room temperature is stated for optical experiments, not assigned numerically or silently transferred to synthesis.'],conflicts=[],requested_tasks=['precursor_selection','partial_protocol'] if kind=='literature_protocol' else [],experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
 r['context_links']=[{'label':'Complete main-paper review','url':'../paper-review.html?id='+GROUP,'relation':'Source figures, complete reported method principles, optical properties, interpretations and unresolved details.'}]
 return r
def add(r,i,action,label,inputs,out,e,pars=None,stage='synthesis',desc='',env=None,end=None,depends=None,kind='reaction_batch'):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out] if out else [],depends=depends if depends is not None else ([r['operations'][-1]['id']] if r['operations'] else []),parameters=pars or {},stage=stage,description=desc,environment=F(env,e),endpoint=F(end,e)))
def P(r,i,label,formula,e,st=None,explicit=False,notes=None):
 p=product(i,formula,deepcopy(e),link='explicit' if explicit else 'general_context',state=st,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
def M(r,i,s,prop,v,u,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,Q(v,u,e,**kw),tech,deepcopy(e),conditions))
def T(r,i,s,prop,value,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,F(value,e,**kw),tech,deepcopy(e),conditions))
def link(r,k,label,rel):r['context_links'].append({'label':label,'url':'../records/'+PRE+k+'.html','relation':rel})
def stock(r,i,name,components,concentrations,e,scope):r['stocks'].append({'id':i,'name':name,'components':[{'material_id':m,'quantities':{}} for m in components],'concentrations':concentrations,'preparation_operation_ids':[],'scope':scope,'evidence':deepcopy(e)})
records=[]
SYSTEMS={
 'i':{'roman':'I','title':'Single-layer HgS well','sequence':'A–B–C','cs':['after-b'],'formula':'CdS/(HgS)1/(CdS)1','well_count':1,'well_layers':1,'well_thickness':.4,'absorption':625,'pl':820,'crossover':600,'inset_short':500,'inset_long':650},
 'ii':{'roman':'II','title':'Double-layer HgS well','sequence':'A–B–C–B–C','cs':['after-b','after-b'],'formula':'CdS/(HgS)2/(CdS)1','well_count':1,'well_layers':2,'well_thickness':.8,'absorption':700,'pl':950,'crossover':700,'inset_short':500,'inset_long':900},
 'iii':{'roman':'III','title':'Two HgS monolayer wells separated by CdS','sequence':'A–B–C–C–C–B–C','cs':['after-b','consecutive','consecutive','after-b'],'formula':'CdS/(HgS)1/(CdS)2/(HgS)1/(CdS)1','well_count':2,'well_layers':1,'well_thickness':.4,'absorption':670,'pl':820,'crossover':650,'inset_short':600,'inset_long':750},
}
for key,d in SYSTEMS.items():
 roman=d['roman'];route_e=E(2,'Sample Preparation, System '+roman)
 r=base('system-'+key,'System '+roman+' — '+d['title'],'literature_protocol','Aqueous cation exchange and sequential CdS shell growth')
 r['intended_target']['composition']=F(d['formula'],route_e,note='Subscripts denote reported layer counts, not bulk stoichiometry. Structure is supported by synthesis sequence and optical evidence, not atom-resolved characterization in this article.')
 r['materials']=[C('cd2','core precursor; released Cd2+ retained after exchange and additional shell precursor only for consecutive step C'),C('hg2','cation-exchange reagent',e=BE),C('hexametaphosphate','colloidal stabilizer'),C('h2s','gas-phase sulfur reagent in A and dissolved reagent in C'),C('h2s-aqueous','dropwise sulfur stock for C',e=CE),C('water','aqueous reaction and stock solvent'),C('argon','core-stage atmosphere and excess-sulfide stripping gas')]
 # Normalize identity roles for the existing precursor-selection export. Preserve
 # every source-specific role description without guessing an unreported salt.
 for m in r['materials']:
  normalized={'cd2':'metal_precursor','hg2':'metal_precursor','h2s':'chalcogen_precursor','h2s-aqueous':'precursor_stock'}.get(m['id'])
  if normalized:
   m['notes'].append('Source-specific role: '+m['role'])
   m['role']=normalized
 stock(r,'cd-stock','Initial aqueous Cd2+ solution',['cd2','water'],{'cd2_concentration':Q(2e-4,'M',A)},A,'Initial 100 mL Cd2+ solution. Salt/counterion and stock-making procedure unspecified. Do not assign this concentration to later extra Cd2+ additions.')
 stock(r,'hg-stock','Aqueous Hg2+ exchange stock',['hg2','water'],{'hg2_concentration':Q(1e-3,'M',BE)},BE,'12 mL stock for each named step B; pH 7.0 attaches to the aqueous exchange solution wording. Per-system repeats follow the common B definition, not separate independently quantified runs.')
 stock(r,'h2s-water-stock','Hydrogen sulfide in water',['h2s','water'],{'h2s_concentration':Q(u='M',e=CE)},CE,'No stock concentration or delivered volume. Do not derive a sulfur dose from the gas volume used in step A.')
 add(r,'a-prepare','aqueous_core_mixture_preparation','A · Prepare and stir the stabilized aqueous Cd2+ solution',['cd2','water','hexametaphosphate','argon'],'a-mixture',A,pars={'solution_volume':Q(100,'mL',A),'cd2_concentration':Q(2e-4,'M',A),'flask_capacity':Q(250,'mL',A),'initial_pH':Q(7.9,'pH',A)},env='Argon',desc='Hexametaphosphate stabilizer is present but its amount and counterion are unknown. Stirring speed and pH-adjustment reagent are unreported. Flask capacity is not reaction volume.')
 add(r,'a-inject','gas_injection','A · Inject hydrogen sulfide gas while stirring',['a-mixture','h2s'],'a-nucleating',A,pars={'h2s_gas_volume':Q(.6,'mL',A,basis='Gas volume at unreported temperature and pressure; no mole conversion.')},env='Argon',desc='The high starting pH promotes rapid sulfur-species generation and nucleation. Injection rate and duration are not specified.')
 add(r,'a-grow','acidification_and_growth','A · Allow acidification and slower CdS growth',['a-nucleating'],'a-core',A,pars={'acidic_onset_time':Q(30,'s',A,approximate=True,basis='Time until the pH enters the acidic range; not full growth duration or exact time to pH 4.6.'),'final_pH':Q(4.6,'pH',A)},env='Argon',end='Reported CdS size reaches 3.5 nm; final pH 4.6',desc='Total growth duration is not supplied. This 3.5 nm preparation statement conflicts with the later 3.2 nm core description shared by all systems.')
 add(r,'a-purge','argon_stripping','A · Remove excess hydrogen sulfide with argon',['a-core','argon'],'a-purged',A,pars={'duration':Q(20,'min',A)},env='Argon',desc='Gas purge, not centrifugation or isolation; dissolved ions and stabilized particles remain in the colloidal solution.')
 P(r,'a-cds-core','System '+roman+', Figure 2 trace a: CdS core','CdS',A+F2,st='a-purged',explicit=True,notes=['Initial spectral stages are described as identical across systems, but separate physical-batch identity is not supplied.'])
 M(r,'a-core-preparation-size','a-cds-core','reported_cds_core_size',3.5,'nm',A,conditions='Step-A preparation text; conflicts with the final system descriptions of 3.2 nm. No current TEM method or raw size distribution.')
 M(r,'a-core-absorption','a-cds-core','reported_core_absorption_feature_wavelength',470,'nm',E(3,'Figure 2 caption'),tech='Absorption spectroscopy',conditions='Caption identifies the starting CdS core spectrum; no raw data or uncertainty supplied.')
 prev='a-purged';bcount=0
 for cidx,mode in enumerate(d['cs'],1):
  if mode=='after-b':
   bcount+=1;bid=f'b{bcount}-exchange';out=f'b{bcount}-exchanged'
   add(r,bid,'cation_exchange',f'B{bcount} · Exchange the outer CdS monolayer for HgS',[prev,'hg2','water'],out,BE+route_e,pars={'hg_stock_volume':Q(12,'mL',BE),'hg2_stock_concentration':Q(1e-3,'M',BE),'hg_solution_pH':Q(7,'pH',BE,basis='pH accompanies the added aqueous Hg2+ solution in the source wording; no separate pH-adjustment operation supplied.')},desc='One outer CdS monolayer is replaced. Displaced Cd2+ remains dissolved and supplies the immediately following C step; no washing, precipitation collection or new Cd charge is inserted. Quantity repeats apply the paper’s common B definition. Exchange duration is unreported.')
   prev=out
   if bcount==1:P(r,'b-hgs','System '+roman+', Figure 2 trace b: first HgS layer','CdS/(HgS)1',BE+F2,st=prev,explicit=True)
   else:P(r,'second-hgs','System '+roman+', Figure 2 trace '+('d' if key=='ii' else 'e')+': second HgS incorporation','CdS/(HgS)2' if key=='ii' else 'CdS/(HgS)1/(CdS)2/(HgS)1',route_e+F2,st=prev,explicit=True)
  else:
   out=f'c{cidx}-cd-ready'
   add(r,f'c{cidx}-add-cd','cadmium_precursor_addition',f'C{cidx} · Add the Cd2+ needed for the next CdS monolayer',[prev,'cd2'],out,CE+route_e,pars={'additional_cd2_amount':Q(u='mol',e=CE),'additional_cd2_stock_volume':Q(u='mL',e=CE),'additional_cd2_stock_concentration':Q(u='M',e=CE)},desc='Required because this C step does not immediately follow B. Inject the correct amount through a septum; salt identity, concentration, volume and dose are not quantified. Do not reuse the initial core-stock concentration or invent a shell molar amount.')
   prev=out
  out=f'c{cidx}-grown'
  add(r,f'c{cidx}-grow','dropwise_cds_overgrowth',f'C{cidx} · Grow one CdS monolayer with aqueous H2S',[prev,'h2s-aqueous'],out,CE+route_e,pars={'dropwise_addition_duration':Q(25,'min',CE),'pH':Q(7,'pH',CE),'h2s_stock_volume':Q(u='mL',e=CE),'h2s_stock_concentration':Q(u='M',e=CE)},desc=('The dissolved Cd2+ released by immediately preceding B is sufficient; no extra Cd2+ addition is reported. ' if mode=='after-b' else 'Use the separately added, unquantified Cd2+ inventory. ')+'Add H2S/water slowly and dropwise through the growth period. Concentration, dose and pH-maintenance reagent are unknown; no temperature is supplied.')
  add(r,f'c{cidx}-purge','argon_stripping',f'C{cidx} · Purge excess hydrogen sulfide with argon',[out,'argon'],f'c{cidx}-purged',CE+route_e,pars={'duration_lower_bound':Q(u='min',e=CE,minimum=20)},env='Argon',desc='At least 20 min, not exactly 20 min. Keep the colloidal dispersion; no unreported isolation or drying follows.')
  prev=f'c{cidx}-purged'
  if cidx==1 and key!='i':P(r,'c-single-well','System '+roman+', Figure 2 trace c: System-I architecture','CdS/(HgS)1/(CdS)1',route_e+F2,st=prev,explicit=True)
  if key=='iii' and cidx==3:P(r,'d-thick-cds','System III, Figure 2 trace d: three CdS overlayer monolayers','CdS/(HgS)1/(CdS)3',route_e+F2,st=prev,explicit=True,notes=['Figure 2 does not separately show the intervening two-CdS-layer state; no seventh spectrum is invented.'])
 p=P(r,'final','System '+roman+', Figure 2 trace '+{'i':'c','ii':'e','iii':'f'}[key]+': final QDQW',d['formula'],route_e+F1+F2,st=prev,explicit=True,notes=['Architecture is reported from synthesis order and optical interpretation. No measured lattice model or current-paper micrograph supplied.'])
 p['surface']=F('CdS outer capping monolayer; hexametaphosphate-stabilized colloidal preparation',route_e+A,note='Stabilizer binding geometry and final surface coverage were not measured.')
 T(r,'step-sequence','final','reported_synthesis_sequence',d['sequence'],route_e)
 M(r,'system-core-size','final','reported_cds_core_size',3.2,'nm',F1,conditions='Shared final-system description; conflicts with step A’s 3.5 nm statement. Do not silently select one for an exact-structure training target.')
 M(r,'well-count','final','reported_hgs_well_count',d['well_count'],'count',F1)
 M(r,'well-layer-count','final','reported_hgs_monolayers_per_well',d['well_layers'],'monolayer',F1)
 M(r,'well-thickness','final','reported_hgs_thickness_per_well',d['well_thickness'],'nm',F1,conditions='Source-reported nominal layer dimensions, not a measured size distribution.')
 M(r,'cap-layer-count','final','reported_cds_capping_layer_count',1,'monolayer',F1)
 M(r,'cap-thickness','final','reported_cds_capping_thickness',.4,'nm',F1)
 if key=='iii':
  M(r,'barrier-layer-count','final','reported_cds_interwell_barrier_layer_count',2,'monolayer',F1)
  M(r,'barrier-thickness','final','reported_cds_interwell_barrier_thickness',.8,'nm',F1)
 M(r,'absorption-transition','final','lowest_optically_allowed_transition_wavelength',d['absorption'],'nm',F2,tech='Absorption second-derivative minimum',conditions='Room temperature; source derives the minimum from absorption. Not a photoluminescence maximum or a digitized raw curve.',status='author_derived')
 M(r,'pl-maximum','final','photoluminescence_maximum_wavelength',d['pl'],'nm',F3,tech='Photoluminescence',conditions='Source system label; acquisition uses 440 nm excitation. No independent physical-batch ID is supplied.')
 M(r,'estimated-qy-bound','final','estimated_photoluminescence_quantum_yield',None,'%',F3,maximum=1,maximum_exclusive=True,approximate=True,qualifier='Authors estimate below 1% for all three systems; no calibrated per-system value.',tech='Author estimate from weak emission')
 M(r,'relaxation-crossover','final','short_to_long_lived_signal_crossover_wavelength',d['crossover'],'nm',F4,tech='Transient absorption and visual-aid line intersections',conditions='Excitation 400 nm. Least-squares lines are expressly intended mainly as a visual aid; uncertainty and fitted functional coefficients are not supplied.',status='author_derived')
 M(r,'short-lived-component','final','short_lived_high_energy_component_decay_time',5,'ps',F4,approximate=True,conditions='Study-wide approximate high-energy component applies to all systems; not a full wavelength-dependent kinetic dataset.')
 M(r,'inset-short-probe','final','figure4_inset_short_lived_probe_wavelength',d['inset_short'],'nm',E(4,'Figure 4 inset, System '+roman),conditions='Printed inset label only; decay curve points and lifetime are not independently digitized.')
 M(r,'inset-long-probe','final','figure4_inset_long_lived_probe_wavelength',d['inset_long'],'nm',E(4,'Figure 4 inset, System '+roman),conditions='Inset calls traces bleach, while the text assigns long-lived low-energy response to stimulated emission; preserve both labels.')
 r['quality']['conflicts']=['Step A says CdS grows to 3.5 nm; the later system descriptions and Figure 1 say 3.2 nm for all three cores.','Figure 4 inset uses bleach labels for representative traces; discussion assigns the low-energy long-lived component to stimulated emission.']
 if key=='iii':r['quality']['missing_fields'].append('No separate Figure 2 spectrum for the intermediate two-CdS-layer overcoat; the shown sequence proceeds from one to three layers.')
 for k,label in [('absorption-acquisition','Absorption acquisition'),('photoluminescence-acquisition','Photoluminescence acquisition'),('transient-absorption-acquisition','Transient-absorption acquisition'),('optical-comparison','Cross-system optical comparison'),('chemical-interpretation','Chemical interpretation and source limitations')]:link(r,k,label,'Shared source method or comparison; retain system labels and unknown physical-batch identities.')
 records.append(r)

r=base('absorption-acquisition','Stage-resolved steady-state absorption','procedure','Absorption spectroscopy')
r['materials']=[C('specimen','Separate aliquot at a named synthesis stage','characterization',F2)]
add(r,'select-stage','stage_sample_selection','Select the named intermediate or final dispersion',['specimen'],'selected-stage',F2,stage='characterization',desc='Use each source-labelled synthesis stage separately. I has 3 spectra, II has 5, and III has 6; shared initial spectra do not establish a common physical batch.',kind='aliquot')
add(r,'record','absorption_spectroscopy','Record the room-temperature absorption spectrum',['selected-stage'],'absorption-data',F2,stage='characterization',pars={'temperature':Q(u='degC',e=F2,qualifier='Room temperature; no numerical value.')},desc='Steady-state instrument, path length, concentration, acquisition resolution and averaging are not specified. Do not import the transient-absorption cell path length.',kind='analysis_data')
add(r,'second-derivative','spectral_derivative_analysis','Locate minima of the absorption second derivative',['absorption-data'],'transition-data',F2,stage='characterization',desc='Authors use minima to identify the lowest optically allowed transition; derivative/smoothing algorithm, sampling and uncertainty are unreported.',kind='analysis_data')
P(r,'acquisition-context','Separate stage spectra across Systems I–III',FORMULA,F2)
T(r,'stage-series','acquisition-context','spectral_stage_assignment','I: a CdS, b CdS/HgS, c final. II: a–c same architectural stages, d CdS/(HgS)2, e final. III: a–c same architectural stages, d CdS/(HgS)1/(CdS)3, e CdS/(HgS)1/(CdS)2/HgS, f final. These are staged spectra, not 14 independent fully specified syntheses.',F2)
T(r,'red-shift','acquisition-context','absorption_trend','Absorption edge red-shifts through each displayed growth/exchange stage; authors attribute shifts to greater well thickness and/or nanoparticle size.',F2)
records.append(r)

r=base('photoluminescence-acquisition','Photoluminescence and water-background correction','procedure','Photoluminescence spectroscopy')
r['materials']=[C('specimen','System-labelled colloidal specimen','characterization',EXP),C('water','Separate reference for background and Raman correction','characterization',EXP)]
add(r,'excite','pulsed_optical_excitation','Excite the specimen with the OPO',['specimen'],'pl-excited',EXP,stage='characterization',pars={'excitation_wavelength':Q(440,'nm',EXP),'pump_pulse_duration':Q(5,'ns',EXP,basis='Q-switched Nd:YAG laser pumping the OPO; no separate measured OPO pulse width.'),'laser_repetition_rate':Q(10,'Hz',EXP),'detection_angle':Q(90,'degree',EXP),'temperature':Q(u='degC',e=EXP,qualifier='Room temperature; numerical value unspecified.')},desc='OPO pumped by the third harmonic of a Q-switched Nd:YAG laser. Pulse energy, fluence, spot size and specimen concentration are not reported for PL.',kind='aliquot')
add(r,'record','emission_spectroscopy','Collect emission through the cutoff filter and monochromator',['pl-excited'],'pl-raw',EXP,stage='characterization',desc='90° setup; cutoff filter, monochromator and CCD camera. No instrument models or quantitative spectral-response calibration supplied.',kind='analysis_data')
add(r,'water-reference','reference_spectrum_acquisition','Record a separate water reference spectrum',['water'],'water-reference-data',EXP,stage='characterization',depends=[],desc='Water reference is separate from the nanocrystal specimen; this is not a mixed material or a new synthesis input.',kind='analysis_data')
add(r,'subtract','background_subtraction','Subtract the water-reference spectrum',['pl-raw','water-reference-data'],'pl-corrected',EXP,stage='characterization',depends=['record','water-reference'],desc='Corrects Raman bands and background. This does not provide a nanocrystal Raman spectrum or a measured Raman property.',kind='analysis_data')
P(r,'pl-context','PL acquisition shared by the three separate systems',FORMULA,EXP)
T(r,'pl-scope','pl-context','acquisition_scope','All spectra acquired at room temperature, with source system labels retained. No numerical room temperature, calibrated per-system quantum yield, absolute emission intensity or raw spectral table.',EXP+F3)
records.append(r)

r=base('transient-absorption-acquisition','Femtosecond transient-absorption procedure','procedure','Pump–probe transient absorption')
r['materials']=[C('specimen','System-labelled colloidal dispersion','characterization',EXP)]
add(r,'load','sample_cell_preparation','Load and rotate the colloidal-sample glass cell',['specimen'],'ta-cell',EXP,stage='characterization',pars={'cell_thickness':Q(2,'mm',EXP),'temperature':Q(u='degC',e=EXP,qualifier='Room temperature, numerical value unspecified.')},desc='Rotate to prevent photodegeneration. Rotation rate and actual degraded fraction are not reported; this is handling, not measured long-term stability.',kind='aliquot')
add(r,'probe','white_light_generation','Generate the white-light probe in sapphire',[], None,EXP,stage='characterization',depends=[],pars={'fundamental_wavelength':Q(800,'nm',EXP),'probe_spectral_range':Q(u='nm',minimum=450,maximum=1050,e=EXP)},desc='Focus a small portion of the fundamental laser output into a sapphire plate. Sapphire is optical hardware, not a synthesis reagent.',kind='analysis_data')
add(r,'pump','pump_probe_excitation','Overlap the excitation and probe in the sample',['ta-cell'],'ta-excited',EXP,stage='characterization',depends=['load','probe'],pars={'excitation_wavelength':Q(400,'nm',EXP),'pulse_duration_fwhm':Q(100,'fs',EXP),'pulse_energy':Q(100,'uJ',EXP)},desc='Source gives pulse energy, not energy density or fluence. Focal spot size is not reported. Quantities belong to transient absorption, not the separate 440 nm PL method.',kind='aliquot')
add(r,'delay-scan','time_resolved_absorption','Vary pump–probe delay and record absorption changes',['ta-excited'],'ta-data',EXP,stage='characterization',pars={'optical_delay_line_spatial_resolution':Q(3,'um',EXP),'reported_delay_time_resolution':Q(21,'fs',EXP)},desc='Source states 3 µm (21 fs) resolution. Preserve both reported quantities without silently recomputing or equating stage resolution with instrument-response width. No raw full delay/wavelength matrix supplied.',kind='analysis_data')
add(r,'analyze','kinetic_comparison','Compare decay times across observation wavelengths',['ta-data'],'ta-comparison',F4,stage='characterization',desc='Figure 4 presents decay times and representative traces; exact kinetic fitting model, point uncertainties and raw data are not supplied. Least-squares lines around the crossover are visual aids, not a validated mechanistic law.',kind='analysis_data')
P(r,'ta-context','Shared pump–probe method for separate Systems I–III',FORMULA,EXP+F4)
T(r,'negative-signal','ta-context','negative_transient_signal_interpretation','Negative transient absorption can be bleaching or stimulated emission. Authors assign high-energy short-lived response to bleach recovery of an optically allowed low-energy excitonic state; long-lived low-energy response is assigned to stimulated emission in the PL range.',F4)
T(r,'wavelength-dependence','ta-context','decay_time_trend','Low-energy decay times form a distribution and increase with increasing observation wavelength; the interpretation invokes recombination through an inhomogeneous distribution of trapping states.',F4)
records.append(r)

r=base('optical-comparison','Comparison of well thickness, separation and optical response')
P(r,'comparison','Paired comparison of Systems I, II and III',FORMULA,F2+F3+F4)
M(r,'oscillator-ratio','comparison','relative_lowest_exciton_oscillator_strength_system_iii_to_i_or_ii',2,'ratio',F2,conditions='System III relative to each of I and II; no absolute oscillator strengths, uncertainty or normalization protocol. Source says I and II have the same oscillator strength.')
M(r,'atom-count-ratio','comparison','author_approximate_atom_count_system_iii_to_i',2,'ratio',E(2,'Absorption Spectra, final paragraph'),approximate=True,conditions='Author qualitative structural argument, not composition analysis or absolute atom count.',status='author_derived')
T(r,'hg-content','comparison','reported_hgs_amount_comparison','Authors state that System III contains the same amount of HgS as System II; no measured elemental assay or absolute Hg amount for final particles is supplied.',E(2,'Absorption Spectra, final paragraph'))
T(r,'energy-order','comparison','lowest_transition_energy_order','System I has the highest transition energy, System II the lowest, and System III lies between. PL onset and transient crossover follow the same ordering; PL maxima differ, with I and III both 820 nm and II at 950 nm.',F2+F3+F4)
T(r,'trap-interpretation','comparison','trap_state_location_interpretation','Broad weak PL is mainly assigned to trap states. Similar I/III emission maxima but red-shifted II emission suggest a trap governed by well thickness; authors conclude the site is at the CdS/HgS interface rather than the exterior surface. This is an interpretation, not direct trap imaging.',F3)
T(r,'well-interaction','comparison','interwell_coupling_interpretation','System III’s red shift relative to I is smaller than for adjacent double-layer II, but is interpreted as showing that separated well layers are not independent. Authors assume mixing of states from the two wells accounts for newly allowed transitions and enhanced oscillator strength.',E(2,'Absorption Spectra, final paragraph')+E(4,'Conclusion'))
T(r,'structural-evidence-scope','comparison','optical_architecture_evidence','The authors use absorption, emission onset and dynamics to distinguish separated single-layer wells from one adjacent double-layer well. No current-paper TEM, chemical map, XRD, SAED or atomic coordinate measurement independently establishes the layer geometry.',F2+F3+F4)
records.append(r)

r=base('chemical-interpretation','Source chemical rationale and architectural limits')
P(r,'source-model','Source growth/exchange and structural interpretation',FORMULA,A+BE+CE+F1)
T(r,'nucleation-ph','source-model','ph_control_rationale','At initial pH 7.9, rapid ionization of injected H2S produces sulfur species and promotes many small CdS crystallites. Consumption of sulfur shifts dissociation and releases protons, giving an acidic range after about 30 s and slower subsequent growth. Source prints S−; this is retained as source notation rather than an experimentally established speciation model.',A)
M(r,'solubility-contrast','source-model','reported_orders_of_magnitude_hgs_vs_cds_solubility_product_difference',26,'orders_of_magnitude',BE,conditions='Author statement that the HgS solubility product is smaller. Absolute constants, phase, temperature, activity model and reference data are not given.')
T(r,'exchange-mass-balance','source-model','cation_exchange_inventory','B exchanges the outermost CdS layer for HgS; displaced Cd2+ stays dissolved. The authors state this inventory is enough for one CdS monolayer when sulfur is supplied. No purification is inserted between B and C.',BE)
T(r,'conditional-cd','source-model','conditional_precursor_replenishment','C immediately after B uses released Cd2+. C after another C requires new Cd2+ through a septum, with dose and formulation unknown. This distinction is needed in System III’s repeated shell-growth sequence.',CE+E(2,'System III'))
T(r,'two-well-construction','source-model','reported_two_well_growth_logic','After A–B–C, two further C steps create three CdS overlayer monolayers. The next B replaces the outermost of those layers with HgS, leaving a two-monolayer CdS barrier. Final C caps the outer HgS layer.',E(2,'System III')+F1)
T(r,'morphology-context','source-model','cited_core_morphology','The introduction and Figure 1 caption identify small CdS crystallites as tetrahedral with {111} facets, citing earlier QDQW work. Figure 1 uses circular layer schematics; neither is a new measured morphology dataset in this paper.',E(1,'Introduction, Mews et al. context')+E(2,'Figure 1 caption'),conditions='Cited historical morphology, not a measured label for each new System I–III batch.')
T(r,'wavefunction-scope','source-model','wavefunction_schematic_scope','Figure 1 sketches carrier wavefunctions and refers to Figure 4 of reference 18. The discussion says prior theoretical predictions describe I and II, while calculations for the lowest excitonic states of the separated-two-well System III were unavailable. Do not promote the System III sketch to a newly computed or validated atomic model.',E(2,'Figure 1 caption')+E(4,'Theory comparison before Conclusion'))
T(r,'future-barriers','source-model','author_future_outlook','Investigate how carrier interactions between two wells depend on CdS barrier thickness and the thickness of the HgS wells. This is a proposed study, not additional completed synthesis variants.',E(4,'Conclusion'))
r['quality']['conflicts']=['The description calls System III’s two wells independent in the geometric sense, whereas the conclusion infers electronic interaction. Preserve geometric separation without claiming electronic independence.']
records.append(r)

r=base('literature-context','Cited methods, prior structural evidence and missing information')
P(r,'references','Scope of cited literature and current evidence',FORMULA,E(4,'References and Notes'))
T(r,'cited-preparation','references','cited_method_scope','The main article summarizes A/B/C principles and order; preparation details are attributed to reference 2 (Mews et al., J. Phys. Chem. 1994, 98, 934) and reference 13 (Braun, Burda and El-Sayed, submitted). Neither cited work is automatically a matched supplement or a fully inspected upstream recipe.',E(1,'Sample Preparation')+E(4,'References 2 and 13'))
T(r,'cited-structure','references','cited_structural_evidence','Interface lattice imperfections are discussed using TEM work in reference 3 (Mews, Kadavanich, Banin and Alivisatos, Phys. Rev. B 1996, 53, R13242) and ODMR/ESR work in reference 15 (Lifshitz et al., J. Phys. Chem. B 1999, 103, 6870). These are references, not reproduced measurements for the present samples.',E(3,'Emission Spectra, interface discussion')+E(4,'References 3 and 15'))
T(r,'cited-theory','references','theory_comparison_scope','Prior predictions by Jaskólski and Bryant, reference 18 (Phys. Rev. B 1998, 57, R4237), are said to agree with I/II hole-burning, line-narrowing and transient-absorption observations. Reference 19 (Chang and Xia, Phys. Rev. B 1998, 57, 9780) is introduced as prior two-layer theory; neither fills missing System III experimental or atomic data.',E(1,'Introduction')+E(4,'Theory comparison and References 18–19'))
T(r,'source-completeness','references','inspected_source_scope','All four main pages, all four original figures, captions, methods, results, conclusion and references were inspected. No source table, raw spectral matrix, matched SI, current micrograph or lattice-coordinate file was supplied. No outside papers were downloaded for this record.',E(1,'Complete article opening')+E(4,'Complete article ending'))
T(r,'historical-motivation','references','author_motivation','The paper contrasts wet-chemical multilayer QDQW preparation with expensive physical multilayer methods requiring clean-room/UHV facilities, and proposes easier ambient solution handling and deposition. These are motivation/outlook statements, not measured economic or manufacturing performance.',E(1,'Introduction'))
records.append(r)

if __name__=='__main__':
 out=B/'canonical-drafts';out.mkdir(exist_ok=True);errors=[]
 for r in records:
  errors+=validate_record(r)
  (out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report={'status':'failed' if errors else 'passed','record_count':len(records),'operation_count':sum(len(r['operations']) for r in records),'measurement_count':sum(len(r['measurements']) for r in records),'material_slots':sum(len(r['materials']) for r in records),'source_read_pages':4,'source_visual_pages':4,'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (B/'canonical-material-identities.json').write_text(json.dumps({'source_id':SID,'source_group':GROUP,'materials':[{'id':i,'name':n,'formula':f} for i,(n,f) in CHEM.items()],'record_material_ids':{r['record_id']:[m['id'] for m in r['materials']] for r in records}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 raw=json.loads((B/'source-manifest.json').read_text(encoding='utf-8-sig'))
 (B/'canonical-record-manifest.json').write_text(json.dumps({'source_id':SID,'source_group':GROUP,'source_sha256':raw['sha256'],'main_pages_read_and_visually_inspected':4,'supporting_information':'No SI supplied or independently matched; existence/availability unresolved.','records':[{'id':r['record_id'],'record_type':r['record_type'],'sha256':hashlib.sha256((out/(r['record_id']+'.json')).read_bytes()).hexdigest(),'operation_ids':[o['id'] for o in r['operations']],'sample_ids':[p['sample_id'] for p in r['products']],'measurements':len(r['measurements'])} for r in records]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report))
 if errors:raise SystemExit(1)
