"""Yi et al. 2002: complete five-page source, source-scoped private records."""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='yi2002';PRE='yi-2002-';FORMULA='La2(MoO4)3:Yb,Er'
SRC=source(SID,'10.1021/cm0115416','Synthesis and Characterization of High-Efficiency Nanocrystal Up-Conversion Phosphors: Ytterbium and Erbium Codoped Lanthanum Molybdate','Guangshun Yi; Baoquan Sun; Fengzhen Yang; Depu Chen; Yuxiang Zhou; Jing Cheng',2002,si='No matching SI supplied or independently verified. No SI declaration observed in the supplied five-page main article.')
SRC['main_status']='All five main pages read as text and original page images, including ten figures, captions and 27 references. Independent audit pending.'
def E(p,s):return ev(SID,f'Main PDF p. {p}, printed p. {2909+p}, {s}')
SYN=E(2,'Section 2.1, hydrothermal preparation');BULK=E(2,'Section 2.1, solid-state bulk comparison');INST=E(2,'Section 2.2, characterization techniques');XRD=E(2,'Figure 1 and X-ray diffraction discussion');TEM=E(2,'Figure 2 and morphology discussion');SIZE=E(2,'Particle-size discussion')+E(3,'Figure 3');DC=E(3,'Figure 4a and down-conversion discussion');UC=E(3,'Figure 4b and up-conversion discussion');IR=E(3,'Near-IR absorption discussion')+E(4,'Figure 5');TEMP=E(3,'Annealing-temperature comparison')+E(4,'Figure 6');ER=E(3,'Er3+ concentration comparison')+E(4,'Figure 7');POWER=E(3,'Power-law dependence')+E(4,'Figure 8');MECH=E(4,'Figure 9 and two-photon mechanism')+E(5,'Surface-effect interpretation');COMP=E(4,'Nanocrystal/bulk comparison')+E(5,'Figure 10 and comparison');GRIND=E(5,'Bulk-grinding control paragraph')
def Q(v=None,u='',e=SYN,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=SYN,**kw):return fact(v,deepcopy(e),**kw)
CHEM={
 'lanthanum-oxide':('Lanthanum oxide','La2O3',SYN),
 'ytterbium-oxide':('Ytterbium oxide','Yb2O3',SYN),
 'erbium-oxide':('Erbium oxide','Er2O3',SYN),
 'ammonium-molybdate':('Ammonium molybdate; printed identity and conflicting mass/amount preserved','(NH4)2MoO4',SYN),
 'nitric-acid':('Diluted nitric acid; aqueous concentration and volume unspecified','HNO3',SYN),
 'water':('Deionized water','H2O',SYN),
 'molybdenum-trioxide':('Molybdenum trioxide for the bulk solid-state comparator','MoO3',BULK),
 'stock-a':('Solution A: acid-dissolved rare-earth oxides, evaporated and redissolved in water',None,SYN),
 'stock-b':('Solution B: printed ammonium molybdate in water',None,SYN),
 'unannealed-specimen':('Washed and air-dried hydrothermal phosphor before annealing',FORMULA,SYN+TEM),
 'nanocrystal-specimen':('Nominal nanocrystal characterization specimen; physical batch and exact thermal history unresolved',FORMULA,INST+UC+SIZE+IR),
 **{f'anneal-{t}-specimen':(f'Phosphor after {t} °C annealing for 5 h',FORMULA,TEMP if t!=800 else SYN+TEMP)for t in [600,700,800,900,1000]},
 'bulk-specimen':('Solid-state bulk phosphor comparator',FORMULA,BULK),
 'ground-bulk-specimen':('Finely ground bulk phosphor control; final size unspecified',FORMULA,GRIND),
 'erbium-series-specimens':('Separate Er concentration-series specimens; adjusted input quantities unreported',FORMULA,ER)
}
def C(i,role,stage='synthesis',notes=None,e=None,quantities=None):
 n,f,default=CHEM[i];return material(i,n,f,role,stage,deepcopy(e or default),quantities=quantities,notes=notes or [])
def base(k,title,kind='observation',method='Source-scoped characterization and interpretation'):
 r=record(PRE+k,'Yi et al. (2002) · '+title,FORMULA,'Ytterbium- and erbium-codoped lanthanum molybdate phosphors',method,deepcopy(SRC),'Complete supplied main PDF pp. 1–5',kind)
 r['schema_version']='1.3.0';r['collection']='reviewed_literature';r['material'].update(elements=['La','Mo','O','Yb','Er'],architecture='single_material')
 r['lineage'].update(source_group=SID,recipe_family='yi2002-lanthanum-molybdate')
 r['intended_target']['composition']=F(FORMULA,E(1,'Abstract'),note='Source host/dopant notation; not refined atomic occupancies or a measured exact dopant composition.')
 r['quality'].update(review_status='imported_unreviewed',review_scope='Complete five-page main text and images inspected; no SI or cited external papers downloaded. Independent audit and integration pending.',missing_fields=['No verified SI, raw spectral arrays, atomic coordinates, refined dopant occupancies or absolute quantum yield is supplied.','Physical batch identifiers and most characterization specimen preparation/settings are absent; general figure context is not a per-run sample join.'],conflicts=[],requested_tasks=['precursor_selection','partial_protocol']if kind=='literature_protocol'else [],experimental_outcome='reported_product'if kind=='literature_protocol'else'not_established')
 r['context_links']=[{'label':'Complete source review','url':'../paper-review.html?id='+SID,'relation':'Full methods, original figures, source conflicts and interpretation.'}]
 return r
def add(r,i,action,label,inputs,out,e,pars=None,stage='synthesis',desc='',env=None,end=None,kind='reaction_batch',depends=None,retain=False):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out]if out else [],depends=depends if depends is not None else([r['operations'][-1]['id']]if r['operations']else []),parameters=pars or {},stage=stage,description=desc,environment=F(env,e),endpoint=F(end,e),retained_fraction=out if retain else None))
def P(r,i,label,e,formula=FORMULA,st=None,explicit=False,notes=None):
 p=product(i,formula,deepcopy(e),link='explicit'if explicit else'general_context',state=st,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
def M(r,i,s,prop,v,u,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,Q(v,u,e,**kw),tech,deepcopy(e),conditions))
def T(r,i,s,prop,v,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,F(v,e,**kw),tech,deepcopy(e),conditions))
def link(r,k,title,rel):r['context_links'].append({'label':title,'url':'../records/'+PRE+k+'.html','relation':rel})
records=[]
OXIDES={'lanthanum-oxide':(1.1760,3.607),'ytterbium-oxide':(.3692,.937),'erbium-oxide':(.05370,.140)}
def stock_a(r,charges=True):
 for i,(mass,amount)in OXIDES.items():
  r['materials'].append(C(i,'metal_precursor','precursor_preparation',notes=['Aldrich; oxide purity 99.99% reported for the stated stock preparation.'],quantities={'mass':Q(mass if charges else None,'g'),'amount':Q(amount if charges else None,'mmol'),'purity':Q(99.99,'%')}))
 r['materials'] += [C('nitric-acid','dissolution_reagent','precursor_preparation',quantities={'volume':Q(u='mL'),'concentration':Q(u='mol/L',qualifier='Only diluted nitric acid is specified.')}),C('water','solvent','precursor_preparation')]
 add(r,'dissolve-a','acid_dissolution','Dissolve the rare-earth oxides in diluted nitric acid',list(OXIDES)+['nitric-acid'],'acid-solution-a',SYN,stage='precursor_preparation',desc='La2O3, Yb2O3 and Er2O3 dissolve in diluted nitric acid. Acid concentration, volume, dissolution temperature, addition order and duration are not stated. Nitrate-containing solution is expected chemically, but exact dissolved species are not directly identified.')
 add(r,'dry-a','warm_evaporation','Warm solution A to dryness',['acid-solution-a'],'dry-residue-a',SYN,{'temperature':Q(u='°C'),'duration':Q(u='min')},stage='precursor_preparation',end='Dry residue; unreacted nitric acid driven away',desc='The paper says warmed to dry to remove unreacted nitric acid; no numeric temperature, atmosphere, residue hydrate or exact nitrate composition is supplied.')
 add(r,'redissolve-a','aqueous_redissolution','Redissolve the residue in deionized water',['dry-residue-a','water'],'redissolved-a',SYN,{'water_volume':Q(30,'mL')},stage='precursor_preparation',desc='30 mL is water added, not an independently measured final stock volume. No automatic molarity or pH is inferred.')
 add(r,'stir-a','room_temperature_stirring','Stir solution A at room temperature',['redissolved-a'],'solution-a',SYN,{'duration':Q(1,'h')},stage='precursor_preparation',env='Room temperature; numerical value unspecified')
 r['stocks'].append({'id':'solution-a-stock','name':'Solution A','components':[{'material_id':i,'quantities':{}}for i in list(OXIDES)+['nitric-acid','water']],'concentrations':{'rare_earth_concentration':Q(u='mol/L',qualifier='Final solution volume and measured speciation are not supplied. Acid is removed before redissolution.')},'preparation_operation_ids':['dissolve-a','dry-a','redissolve-a','stir-a'],'scope':'Input-source inventory, not a claim that all original oxide/acid species remain in the final stock.','evidence':deepcopy(SYN)})
def stock_b(r,charges=True):
 r['materials'].append(C('ammonium-molybdate','metal_precursor','precursor_preparation',notes=['Beijing Chemical Corp.; no purity or hydrate stated. Printed mass and mmol are internally inconsistent with the stated formula; both are retained.'],quantities={'mass':Q(1.961 if charges else None,'g'),'amount':Q(9.37 if charges else None,'mmol')}))
 if not any(m['id']=='water'for m in r['materials']):r['materials'].append(C('water','solvent','precursor_preparation'))
 add(r,'dissolve-b','aqueous_dissolution','Dissolve ammonium molybdate in deionized water',['ammonium-molybdate','water'],'dissolved-b',SYN,{'water_volume':Q(30,'mL')},stage='precursor_preparation',depends=[],desc='Printed (NH4)2MoO4: 1.961 g and 9.37 mmol. Formula/mass/amount inconsistency is not repaired by inventing another molybdate or hydrate. The final solution volume is not measured.')
 add(r,'stir-b','room_temperature_stirring','Stir solution B at room temperature',['dissolved-b'],'solution-b',SYN,{'duration':Q(1,'h')},stage='precursor_preparation',env='Room temperature; numerical value unspecified')
 r['stocks'].append({'id':'solution-b-stock','name':'Solution B','components':[{'material_id':'ammonium-molybdate','quantities':{}},{'material_id':'water','quantities':{}}],'concentrations':{'molybdate_concentration':Q(u='mol/L',qualifier='Printed mass and mmol conflict; final solution volume not supplied.')},'preparation_operation_ids':['dissolve-b','stir-b'],'scope':'30 mL is added water; no corrected molarity or hydrate is inferred.','evidence':deepcopy(SYN)})
for k,fn,label in [('stock-a',stock_a,'Rare-earth solution A'),('stock-b',stock_b,'Ammonium molybdate solution B')]:
 r=base(k,label,'procedure','Aqueous precursor-stock preparation');fn(r);P(r,k,label,SYN,formula=None,st='solution-'+k[-1],explicit=True)
 if k=='stock-a':T(r,'supplier','stock-a','oxide_supplier_and_grade','La2O3, Yb2O3 and Er2O3: Aldrich, 99.99% each.',SYN)
 else:r['quality']['conflicts'].append('Printed (NH4)2MoO4, 1.961 g and 9.37 mmol do not form a consistent formula/mass/amount pair; no alternative identity is selected.');T(r,'supplier','stock-b','molybdate_supplier','Beijing Chemical Corp.; purity and hydration state are not stated.',SYN)
 records.append(r)

for t in [600,700,800,900,1000]:
 r=base('anneal-'+str(t),f'Hydrothermal preparation and {t} °C annealing','literature_protocol','Hydrothermal precipitation followed by annealing')
 stock_a(r,charges=t==800);stock_b(r,charges=t==800)
 for m in r['materials']:
  if m['role']=='metal_precursor':
   m['stage']='synthesis';m['notes'].append('Synthesis-input inventory: introduced through the explicitly retained precursor-stock preparation operations, not added again after the stock is made.')
 add(r,'combine','controlled_dropwise_addition','Add solution B dropwise into solution A',['solution-a','solution-b'],'mixed-suspension',SYN,{'addition_rate':Q(None,'drops/min',minimum=20,maximum=30)},depends=['stir-a','stir-b'],desc='Vigorous stirring accompanies B-to-A addition. Drop volume, total addition duration, quantitative stirring speed and mixed-suspension pH are not specified. Both full prepared solutions are described, but their combined volume is not measured.')
 add(r,'stir-suspension','suspension_stirring','Continue stirring the formed suspension',['mixed-suspension'],'stirred-suspension',SYN,{'duration':Q(20,'min')},desc='Continuous stirring for 20 min; no specified temperature or speed.')
 add(r,'transfer','autoclave_loading','Transfer into the Teflon vessel and cap the autoclave',['stirred-suspension'],'loaded-autoclave',SYN,{'vessel_capacity':Q(100,'mL')},desc='100 mL Teflon vessel is capped and placed closely in an RD-100 autoclave (Institute of Beijing Petrochemical Industry). Vessel capacity is not a stated reaction volume or fill fraction; no purge or pressurization gas is reported.')
 add(r,'hydrothermal','hydrothermal_reaction','Heat the sealed suspension to 180 °C',['loaded-autoclave'],'hydrothermal-suspension',SYN,{'temperature':Q(180,'°C'),'duration':Q(1,'h'),'pressure':Q(u='bar')},env='Capped Teflon vessel in an RD-100 autoclave; pressure not reported',desc='The suspension is subsequently heated to 180 °C for 1 h. Ramp, measured internal pressure and cooling/opening sequence are not supplied; no guessed autogenous pressure is assigned.')
 add(r,'centrifuge','centrifugal_separation','Centrifuge and retain the precipitate',['hydrothermal-suspension'],'precipitate',SYN,{'rotation_rate':Q(6000,'rpm'),'duration':Q(10,'min')},stage='workup',retain=True,desc='The precipitate proceeds to washing. Rotor radius is unknown, so rpm is not converted to relative centrifugal force. No cooling protocol before separation is supplied.')
 add(r,'wash','water_washing','Wash the precipitate twice with deionized water',['precipitate','water'],'washed-precipitate',SYN,{'wash_count':Q(2,'cycles'),'wash_volume':Q(u='mL')},stage='workup',retain=True,desc='Two water washes are explicit; per-wash volume, redispersion method and any repeated centrifugation conditions are unspecified.')
 add(r,'dry','air_drying','Dry the washed precipitate in air',['washed-precipitate'],'unannealed-powder',SYN,{'temperature':Q(u='°C'),'duration':Q(u='h')},stage='workup',env='Air',end='White powder',desc='Drying temperature and duration are absent. Room temperature must not be copied from stock stirring.')
 add(r,'ramp','annealing_temperature_ramp',f'Heat the powder to {t} °C',['unannealed-powder'],'hot-powder',SYN if t==800 else TEMP,{'target_temperature':Q(t,'°C',SYN if t==800 else TEMP),'heating_rate':Q(20 if t==800 else None,'°C/min',SYN if t==800 else TEMP,qualifier=''if t==800 else'20 °C/min is explicit for the 800 °C recipe; applicability to this comparison is not stated.')},desc='The 800 °C preparation explicitly uses a 20 °C/min ramp. The temperature-series text gives endpoints and 5 h holds, not independently documented ramps. Annealing atmosphere is unreported; air drying and bulk firing in air do not establish it.')
 add(r,'anneal','thermal_annealing',f'Anneal at {t} °C for 5 h',['hot-powder'],'annealed-powder',SYN if t==800 else TEMP,{'temperature':Q(t,'°C',SYN if t==800 else TEMP),'duration':Q(5,'h',SYN if t==800 else TEMP)},desc='Separate reported temperature-series condition. Physical batch identities, charge scaling and independent repetitions are not given.')
 add(r,'cool','natural_cooling','Cool the annealed powder naturally',['annealed-powder'],'final-powder',SYN,{'cooling_rate':Q(u='°C/min')},end='Room temperature; numerical value unspecified',desc='Natural cooling is stated in the 800 °C preparation. It is shown as inherited common workflow for other annealing comparisons, not independently reported cooling histories.')
 pre=P(r,'unannealed','Hydrothermal powder before annealing',SYN+TEM,st='unannealed-powder',explicit=True,notes=['A precursor state in this workflow, not a separate fully identified experimental batch.'])
 p=P(r,'final',f'{t} °C / 5 h phosphor',SYN if t==800 else TEMP,st='final-powder',explicit=True)
 if t==800:
  p['phase']=F('Tetragonal La2(MoO4)3 with a small unidentified second phase',XRD)
  p['morphology']=F('Nearly spherical nanocrystals; no observable size change upon 800 °C annealing reported',TEM+TEMP)
  T(r,'color','final','reported_product_color','White powder',SYN)
  M(r,'crystallite-size','final','scherrer_crystallite_size',52.5,'nm',XRD,tech='XRD / Scherrer calculation',status='author_derived',conditions='Coherent crystallite size, not a universal particle-diameter label; shape factor, X-ray wavelength and exact correction equation are not printed.')
  T(r,'phase-reference','final','diffraction_reference','ICDD 45-0407; literature agreement is reported, but a minor second phase remains and no atomic structure file is supplied.',XRD)
 else:
  r['lineage']['parent_record_id']=PRE+'anneal-800'
  for o in r['operations']:
   if o['id']not in ['ramp','anneal']:
    o['description']='Inherited common hydrothermal/workup framework for the temperature comparison; not an independently quantified batch. '+o['description']
    for q in o['parameters'].values():
     if q['status']=='reported':q['status']='inherited';q['basis']='Shared preparation framework; individual comparison batch not independently quantified.'
    for f in [o['environment'],o['endpoint']]:
     if f['status']=='reported':f['status']='inherited'
  for m in r['materials']:
   if m['id']in OXIDES or m['id']=='ammonium-molybdate':m['notes'].append('Individual temperature-series charges are not restated. The explicitly weighed 800 °C recipe is linked; its masses are not promoted to independent per-run measurements.')
   for q in m['quantities'].values():
    if q['status']=='reported':q['status']='inherited';q['basis']='Shared reagent framework; not independently measured for this comparison batch.'
  if t==900:T(r,'growth','final','annealing_morphology_observation','Particle growth and aggregation are reported at 900 °C; no quantitative final size is supplied.',TEMP)
  if t==1000:
   T(r,'bulk-like','final','annealing_morphology_observation','After 1000 °C for 5 h the authors describe bulk material; no numerical size threshold or phase analysis is supplied.',TEMP)
   T(r,'emission-order','final','annealing_emission_order','541 nm emission becomes stronger than 519 nm, consistent with the bulk-like comparison.',TEMP)
 T(r,'preanneal-emission','unannealed','preannealing_emission_observation','Very low fluorescence before annealing; the authors attribute this to extremely poor crystallinity. No absolute yield or measured crystallinity index is supplied.',E(3,'Preannealing discussion'))
 r['quality']['missing_fields']+=['Diluted nitric acid concentration/volume, stock pH, hydrothermal pressure/ramp/cooling, wash volume, air-drying duration/temperature, annealing atmosphere, isolated yield and sample mass are unreported.']
 r['quality']['conflicts']+=['Printed ammonium molybdate identity (NH4)2MoO4, 1.961 g and 9.37 mmol are inconsistent. The reported Mo and rare-earth amounts also do not directly match nominal La2(MoO4)3 stoichiometry; no correction or actual product occupancy is inferred.']
 link(r,'stock-a','Solution A preparation','Source precursor quantities, acid evaporation and redissolution.');link(r,'stock-b','Solution B preparation','Printed molybdate identity and conflicting mass/amount.');link(r,'tem','TEM evidence','Before/after-800 °C images and scoped morphology.');link(r,'upconversion','Up-conversion and annealing comparison','Original Figure 6 and explicit spectral/size tradeoff.')
 records.append(r)

r=base('bulk','Bulk phosphor prepared by solid-state reaction','literature_protocol','Solid-state oxide mixing, pellet pressing and air firing')
r['materials']=[C(i,'metal_precursor',e=BULK,notes=['Bulk-route amount and purity are not stated. Hydrothermal stock charges and suppliers are not copied here.'],quantities={'mass':Q(u='g',e=BULK)})for i in ['lanthanum-oxide','molybdenum-trioxide','ytterbium-oxide','erbium-oxide']]
add(r,'mix','solid_state_powder_mixing','Mix the four oxide powders',[m['id']for m in r['materials']],'bulk-mixture',BULK,{'la_ratio':Q(77,'molar parts',BULK,basis='La:Yb:Er = 77:20:3; cation ratio.'),'yb_ratio':Q(20,'molar parts',BULK,basis='La:Yb:Er cation ratio.'),'er_ratio':Q(3,'molar parts',BULK,basis='La:Yb:Er cation ratio.')},desc='La2O3, MoO3, Yb2O3 and Er2O3 powders. Absolute charges, Mo-to-rare-earth ratio and mixing method/time are absent; reference 15 is cited without its full external procedure being inspected.')
add(r,'press','pellet_pressing','Press the mixture into a pellet',['bulk-mixture'],'bulk-pellet',BULK,{'pressure':Q(u='bar',e=BULK)},desc='Press load, dimensions, binder, dwell time and equipment are not supplied.')
add(r,'fire','solid_state_firing','Fire the pellet in air',['bulk-pellet'],'bulk-product',BULK,{'temperature':Q(1200,'°C',BULK),'duration':Q(5,'h',BULK)},env='Air',desc='Furnace, ramp, cooling, post-firing workup and final particle size are not supplied.')
P(r,'bulk','Solid-state bulk comparator',BULK,st='bulk-product',explicit=True,notes=['Authors state the same nominal composition and crystal structure as nanocrystals; no separate bulk XRD pattern or refined structure is displayed.'])
T(r,'spectral-order','bulk','bulk_upconversion_emission_order','653 nm > 541 nm > 519 nm, opposite the nanocrystal ordering under 980 nm excitation.',COMP)
T(r,'structural-comparison','bulk','author_bulk_nano_structure_comparison','The authors state that bulk and nanocrystal compositions and crystal structures are the same; exact dopant occupancies and independent bulk refinement are not supplied.',COMP,status='author_derived')
link(r,'upconversion','Nanocrystal/bulk spectra','Original Figure 10 and limits of uncalibrated intensity comparison.');records.append(r)

r=base('bulk-grinding','Grinding control on the solid-state bulk material','procedure','Mechanical grinding control')
r['materials']=[C('bulk-specimen','specimen','characterization')]
add(r,'grind','bulk_grinding','Grind the bulk material into fine powder',['bulk-specimen'],'ground-bulk',GRIND,stage='characterization',desc='The paper reports an experimental grinding control but no mill, medium, duration, energy, final size, aliquot mass or surface characterization.')
add(r,'compare','optical_control_comparison','Compare the optical properties after grinding',['ground-bulk','bulk-specimen'],'grinding-comparison',GRIND,stage='characterization',kind='analysis_data',desc='Separate original and ground specimens are compared, not mixed. No control spectrum, numerical intensity ratio or independent defect measurement is supplied.')
P(r,'ground','Finely ground bulk phosphor',GRIND,st='ground-bulk',explicit=True)
T(r,'result','ground','grinding_control_result','Grinding bulk material into fine powder did not improve its optical properties; the authors say this was experimentally confirmed.',GRIND)
T(r,'interpretation','ground','author_grinding_defect_explanation','The authors attribute the result to altered intrinsic point-defect concentration and decreased emission, citing analogous materials. Defect concentrations and emission-loss magnitude were not measured here.',GRIND,status='author_derived')
link(r,'bulk','Bulk precursor preparation','Described current-paper solid-state comparator; grinding is a support control, not another nanocrystal synthesis.');records.append(r)

r=base('xrd','Diffraction phase assignment and Scherrer crystallite estimate','procedure','Powder X-ray diffraction')
r['materials']=[C('anneal-800-specimen','specimen','characterization')]
add(r,'acquire','powder_xrd_acquisition','Acquire the annealed powder diffraction pattern',['anneal-800-specimen'],'xrd-data',XRD+INST,stage='characterization',kind='analysis_data',desc='Bruker D8 advance. Radiation wavelength, voltage/current, scan step/rate, sample holder, refinement and phase fractions are not given.')
add(r,'scherrer','scherrer_analysis','Estimate coherent crystallite size from line broadening',['xrd-data'],'scherrer-data',XRD,{'peak_two_theta':Q(28.053,'°',XRD),'measured_fwhm_b1':Q(.186,'°',XRD),'instrument_broadening_b0':Q(.104,'°',XRD)},stage='characterization',kind='analysis_data',desc='Source invokes Scherrer’s equation and reports B1/B0. No explicit equation, shape factor, wavelength or correction convention is printed; no new calculation replaces its 52.5 nm result.')
p=P(r,'annealed-800','800 °C / 5 h XRD specimen',XRD,explicit=True);p['phase']=F('Tetragonal La2(MoO4)3 with a little unidentified second phase',XRD)
M(r,'scherrer-size','annealed-800','scherrer_crystallite_size',52.5,'nm',XRD,status='author_derived',tech='XRD / Scherrer equation')
T(r,'reference','annealed-800','diffraction_reference','ICDD No. 45-0407; peak positions agree with literature tetragonal La2(MoO4)3 and compare well with bulk phosphors.',XRD)
T(r,'minor-phase','annealed-800','phase_purity_limit','A little second phase is explicitly reported; its identity, concentration and indexed peaks are not supplied. Do not label this sample phase-pure.',XRD)
T(r,'figure-scope','annealed-800','figure1_display_scope','Figure 1 plots linear counts versus 2-theta, with ticks from 10° through 70° and a displayed count scale up to 500. No tabulated peak list, Rietveld refinement, unit-cell constants or atom coordinates are supplied.',E(2,'Figure 1 axes'))
T(r,'single-crystal-inference','annealed-800','author_particle_crystallinity_inference','Agreement of Scherrer size with particle-size measurements is used to infer individual single crystals rather than aggregates of much smaller crystallites. This is an author inference, not lattice-resolved TEM or SAED evidence.',XRD+SIZE,status='author_derived')
records.append(r)

r=base('tem','Before/after annealing electron microscopy','procedure','Transmission electron microscopy')
r['materials']=[C('unannealed-specimen','specimen','characterization'),C('anneal-800-specimen','specimen','characterization')]
add(r,'acquire','tem_acquisition','Image the unannealed and 800 °C specimens separately',['unannealed-specimen','anneal-800-specimen'],'tem-images',TEM+INST,stage='characterization',kind='analysis_data',desc='Hitachi TEM (Tokyo, Japan); instrument model, accelerating voltage, grid, dispersion medium and deposition method are not reported.')
add(r,'compare','tem_morphology_comparison','Compare particle morphology before and after annealing',['tem-images'],'tem-comparison',TEM+TEMP,stage='characterization',kind='analysis_data',desc='Figure 2a is before annealing; Figure 2b is after 800 °C for 5 h. Different scale bars prevent interpreting raw apparent image size as a change in diameter.')
P(r,'before','Figure 2a: before annealing',TEM,explicit=True);P(r,'after','Figure 2b: 800 °C for 5 h',TEM,explicit=True);P(r,'comparison','Study TEM morphology comparison',TEM)
M(r,'scale-before','before','tem_scale_bar',300,'nm',E(2,'Figure 2a scale bar'),tech='Printed TEM scale')
M(r,'scale-after','after','tem_scale_bar',100,'nm',E(2,'Figure 2b scale bar'),tech='Printed TEM scale')
M(r,'diameter-range','comparison','tem_majority_particle_diameter_range',None,'nm',TEM,minimum=40,maximum=60,tech='TEM',conditions='Prose describes most particles across the paired microscopy discussion; no per-panel histogram, count or uncertainty is supplied.')
T(r,'shape','comparison','tem_morphology','Nearly spherical, well-separated particles are described; the figure is not an atomic-resolution lattice image or selected-area diffraction pattern.',TEM)
T(r,'unchanged','after','annealing_size_comparison','Particle size reportedly remains unchanged at 800 °C; numerical before/after paired distributions are absent.',TEMP)
records.append(r)

r=base('particle-size','Instrumental particle-size distribution','procedure','Particle-size analysis')
r['materials']=[C('nanocrystal-specimen','specimen','characterization',notes=['Named nominal nanocrystal context; exact annealing/physical batch linkage of Figure 3 is not explicitly specified.'])]
add(r,'acquire','particle_size_distribution_acquisition','Acquire the source particle-size distribution',['nanocrystal-specimen'],'size-distribution',SIZE+INST,stage='characterization',kind='analysis_data',desc='BI-90Plus Particle Size Analyzer (Brookhaven). The paper does not specify dispersant, concentration, temperature, scattering angle, viscosity correction or whether the displayed values are hydrodynamic diameters. Figure 3 has an intensity axis; do not relabel it as a counted-particle frequency distribution.')
P(r,'distribution','Figure 3 particle-size-analysis specimen; annealing/batch not independently resolved',SIZE,notes=['General nanocrystal context only. No exact sample match to TEM or XRD is established by a similar nominal size.'])
M(r,'majority-range','distribution','instrumental_majority_particle_diameter_range',None,'nm',SIZE,minimum=45,maximum=65,tech='BI-90Plus particle-size analysis')
M(r,'average','distribution','instrumental_average_particle_diameter',53,'nm',SIZE,approximate=True,tech='BI-90Plus particle-size analysis',conditions='Source prose says average diameter; exact weighting convention, uncertainty and number of particles are unknown.')
M(r,'rounded-summary','distribution','abstract_summary_particle_diameter',50,'nm',E(1,'Abstract')+E(5,'Conclusion'),approximate=True,conditions='Rounded study summary, not a second independent measured population.')
T(r,'histogram','distribution','figure3_distribution_scope','Histogram vertical axis is Intensity, reaching 100; most signal lies near 50–55 nm, with small bars outside the prose majority interval. No full raw histogram or normalized probability distribution is inferred.',E(3,'Figure 3'))
T(r,'comparison','distribution','author_size_method_agreement','Authors report agreement with TEM and the Scherrer result; these are distinct particle/distribution and coherent-crystallite metrics.',SIZE+XRD,status='author_derived')
records.append(r)

r=base('downconversion','Down-conversion emission and excitation spectra','procedure','Conventional fluorescence spectroscopy')
r['materials']=[C('nanocrystal-specimen','specimen','characterization',notes=['Nominal optimized nanocrystal context; no unique physical batch is stated for Figure 4a.'])]
add(r,'excite','ultraviolet_excitation','Excite the nanocrystals at 374 nm',['nanocrystal-specimen'],'uv-excited-specimen',DC,{'excitation_wavelength':Q(374,'nm',DC)},stage='characterization',desc='LS-50B fluorescence spectrophotometer with front-surface accessory. Source describes its xenon source as the standard source later replaced for up-conversion; lamp power, slit widths and sample preparation are absent.')
add(r,'acquire','downconversion_spectroscopy','Record emission and the displayed excitation spectrum',['uv-excited-specimen'],'downconversion-data',DC+INST,stage='characterization',kind='analysis_data',desc='Figure 4a solid line is emission and dotted line is excitation. Excitation-spectrum monitored emission wavelength, scan settings, correction and absolute yield are not reported.')
P(r,'nano','Figure 4a nominal nanocrystal specimen',DC)
for i,w,tr in [('h',525,'2H11/2 → 4I15/2'),('s',549,'4S3/2 → 4I15/2')]:
 M(r,'emission-'+i,'nano','downconversion_emission_peak',w,'nm',DC,tech='Fluorescence spectroscopy',conditions='374 nm excitation; transition '+tr+'.')
 T(r,'transition-'+i,'nano','author_downconversion_transition_assignment',tr,DC,status='author_derived')
T(r,'signal-roles','nano','figure4a_signal_roles','Solid emission and dotted excitation are different measurements on an arbitrary intensity axis. Do not treat the dotted curve as absorption or infer its detection wavelength.',E(3,'Figure 4a legend'))
records.append(r)

r=base('upconversion','Up-conversion spectra, annealing comparison and bulk control','procedure','980 nm excited fluorescence spectroscopy')
r['materials']=[C('anneal-'+str(t)+'-specimen','specimen','characterization')for t in [600,700,800,900,1000]]+[C('bulk-specimen','specimen','characterization'),C('nanocrystal-specimen','specimen','characterization')]
add(r,'excite','near_ir_laser_excitation','Excite separate phosphor specimens with the 980 nm laser',[m['id']for m in r['materials']],'ir-excited-specimens',INST+UC,{'excitation_wavelength':Q(980,'nm',INST),'laser_power_specification':Q(50,'mW',INST,basis='External laser specification; not a per-sample irradiance or confirmed power at the specimen.')},stage='characterization',kind='sample_set',desc='Beijing Hi-Tech Optoelectronic Co. external laser replaces the LS-50B xenon source; optic-fiber accessory is used. General setup also describes a front-surface accessory. No spot area, optical throughput, exposure, geometry normalization or power density is provided.')
add(r,'acquire','upconversion_emission_acquisition','Record the separate up-conversion emission spectra',['ir-excited-specimens'],'uc-spectra',UC+TEMP+COMP,stage='characterization',kind='analysis_data',desc='LS-50B fluorescence spectrophotometer (Perkin-Elmer). Figures 4b, 6 and 10 have separate arbitrary intensity scales; no absolute photoluminescence quantum yield or calibrated enhancement factor is measured.')
add(r,'compare','spectral_control_comparison','Compare annealing variants and the solid-state bulk control',['uc-spectra'],'uc-comparisons',TEMP+COMP,stage='characterization',kind='analysis_data',desc='Five 5 h annealing temperatures remain discrete reported comparisons. Figure 10 compares nominal optimized nanocrystals and solid-state bulk material, not the ground control. No interpolated temperature-to-intensity model is fitted.')
P(r,'nano','Figures 4b/10 nominal optimized nanocrystals; physical batch unresolved',UC+COMP);P(r,'bulk','Figure 10 bulk comparator',COMP,explicit=True);P(r,'temperature-series','Figure 6 separate annealing conditions',TEMP)
for w,tr in [(519,'2H11/2 → 4I15/2'),(541,'4S3/2 → 4I15/2'),(653,'4F9/2 → 4I15/2')]:
 M(r,'peak-'+str(w),'nano','upconversion_emission_peak',w,'nm',UC,tech='980 nm excited fluorescence',conditions='Source peak positions, not digitized curve maxima.')
 T(r,'assignment-'+str(w),'nano','author_upconversion_transition_assignment',tr,UC,status='author_derived')
T(r,'nano-order','nano','nanocrystal_upconversion_emission_order','519 nm > 541 nm > 653 nm; strong green bands and very weak red emission.',COMP)
T(r,'bulk-order','bulk','bulk_upconversion_emission_order','653 nm > 541 nm > 519 nm; red dominates in bulk phosphors.',COMP)
T(r,'enhancement','nano','author_nano_bulk_luminescence_comparison','Nanocrystals are reported to show much stronger luminescence than the bulk comparator despite lower annealing temperature. Arbitrary spectra do not establish an absolute quantum yield or normalized enhancement factor.',COMP)
T(r,'temperature-response','temperature-series','annealing_intensity_trend','Intensity rises strongly from 600 to 800 °C, rises more slowly from 800 to 900 °C, then decreases sharply at 1000 °C.',TEMP)
T(r,'selected-condition','temperature-series','author_selected_annealing_condition','800 °C was selected for subsequent experiments because it retains nanocrystal size; 900 °C can be brighter but causes growth and aggregation. It is not the claimed maximum raw intensity among all temperatures.',TEMP,status='author_derived')
T(r,'temperature-mechanism','temperature-series','author_annealing_surface_explanation','Authors attribute low initial emission to poor crystallinity and the 1000 °C loss to growth/reduced surface area. These interpretations are not independent quantitative crystallinity or surface-area measurements.',TEMP,status='author_derived')
T(r,'figure6-labels','temperature-series','figure6_curve_assignments','a: 600 °C; b: 700 °C; c: 800 °C; d: 900 °C; e: 1000 °C, all 5 h. Pumping uses a 980 nm laser diode. Curves have arbitrary intensities and no raw numeric peak table.',E(4,'Figure 6 legend'))
T(r,'figure10-style','nano','figure10_signal_roles','Solid line: nanoparticles. Dotted line: bulk. The bulk comparison is separate from the 1000 °C annealed series and from the grinding control.',E(5,'Figure 10 legend'))
records.append(r)

r=base('near-ir','Near-infrared absorption and estimated excitation window','procedure','FTIR near-infrared absorption')
r['materials']=[C('nanocrystal-specimen','specimen','characterization',notes=['Nominal nanocrystal context; exact Figure 5 batch and thermal history not independently supplied.'])]
add(r,'acquire','near_ir_absorption_acquisition','Measure near-infrared absorption',['nanocrystal-specimen'],'near-ir-data',INST+IR,{'wavenumber_range':Q(None,'cm^-1',IR,minimum=9000,maximum=11000)},stage='characterization',kind='analysis_data',desc='PE SYSTEM 2000 FTIR spectrophotometer with a quartz beam splitter. Pellet/dispersion preparation, reference, path length, resolution, scan count and temperature are not stated. Source calls the horizontal quantity frequency; its unit is wavenumber.')
P(r,'nano','Figure 5 near-IR nanocrystal specimen',IR)
M(r,'center-wavenumber','nano','near_ir_absorption_center',10238,'cm^-1',IR,approximate=True,tech='Near-IR FTIR')
M(r,'center-wavelength','nano','source_corresponding_absorption_wavelength',976,'nm',IR,conditions='Companion source-reported wavelength, not a newly calculated conversion.')
M(r,'band-wavenumber','nano','reported_absorption_band_range',None,'cm^-1',IR,minimum=9875,maximum=10625,conditions='Source writes 10625–9875 cm^-1; ordering normalized without changing bounds.')
M(r,'band-wavelength','nano','source_estimated_excitation_wavelength_range',None,'nm',IR,minimum=941,maximum=1013,conditions='Source companion range; absorption suggests an excitation window but is not a measured wavelength-dependent up-conversion efficiency map.')
T(r,'transitions','nano','author_near_ir_transition_assignment','Er3+: 4I15/2 → 4I11/2; Yb3+: 2F7/2 → 2F5/2.',IR,status='author_derived')
T(r,'plot-axis','nano','figure5_axis_convention','The original absorbance axis is displayed with 0 at the top and 1 at the bottom; wavenumber decreases from 11000 to 9000 cm^-1 from left to right. Preserve the original figure rather than inventing a corrected trace.',E(4,'Figure 5 axes'))
records.append(r)

r=base('erbium-series','Erbium concentration dependence and quenching interpretation','procedure','Dopant-composition comparison')
r['materials']=[C('erbium-series-specimens','specimen','characterization')]
add(r,'compare','dopant_series_comparison','Compare the six displayed Er3+ concentration conditions',['erbium-series-specimens'],'er-comparison',ER,{'stated_er_range':Q(None,'mol%',ER,minimum=1,maximum=7),'selected_er_fraction':Q(3,'mol%',ER)},stage='characterization',kind='analysis_data',desc='Figure 7 markers occur at 1, 2, 3, 4, 5 and 7%; there is no 6% marker. Adjusted La/Yb fractions, oxide charges, fixed-total convention and batch identities are unreported. The stated optimum 800 °C precedes subsequent experiments, but individual thermal histories and the exact plotted emission channel are not independently specified.')
for er in [1,2,3,4,5,7]:
 P(r,'er-'+str(er),f'Figure 7 nominal {er}% Er3+ condition',ER)
 M(r,'fraction-'+str(er),'er-'+str(er),'reported_er_mole_fraction',er,'mol%',ER,conditions='Figure marker composition label; concentration denominator/compensation are not explicitly defined for the series.')
P(r,'series','Er3+ concentration comparison',ER)
T(r,'text-trend','series','source_prose_dopant_intensity_trend','Prose says all three transition peaks increase from 1% to 3%, then decrease sharply with further Er3+ from 4% to 7%, attributed to concentration quenching.',ER)
T(r,'figure-trend','series','figure7_dopant_display_limit','The single unassigned intensity curve has its highest displayed point at 3%; 4% remains close to 3%, while 5% and 7% are much lower. No numerical intensity values are digitized and the curve cannot be assigned to each of three channels.',E(4,'Figure 7'))
T(r,'optimum','series','author_selected_er_fraction','3 mol% Er3+ was selected as the optimum within the studied comparison.',ER,status='author_derived')
T(r,'recipe-limit','series','dopant_series_recipe_missingness','This series is not six fully weighed synthesis recipes. No guessed oxide substitutions, 6% experiment, constant Yb fraction, renormalized La fraction or chemical-dose interpolation is added.',ER)
r['quality']['conflicts']=['Body describes a sharp intensity decline over 4–7%, but the plotted 4% point remains near the 3% maximum.','Body discusses three transition peaks, whereas Figure 7 supplies one intensity curve without an emission-channel label.'];records.append(r)

r=base('power-response','Excitation-power scaling and two-photon interpretation','procedure','Log–log up-conversion power dependence')
r['materials']=[C('nanocrystal-specimen','specimen','characterization',notes=['Nominal optimized nanocrystal context; no unique Figure 8 batch or excitation spot area.'])]
add(r,'sweep','excitation_power_sweep','Vary the 980 nm excitation intensity',['nanocrystal-specimen'],'power-series',POWER,{'excitation_wavelength':Q(980,'nm',POWER),'irradiance':Q(u='W/cm^2',e=POWER)},stage='characterization',kind='analysis_data',desc='Three emission channels are followed. The log-axis has no explicit physical intensity unit or calibration; the 50 mW laser specification does not define every sweep point or sample irradiance.')
add(r,'fit','log_log_regression','Fit emission versus excitation on logarithmic axes',['power-series'],'power-fits',POWER,stage='characterization',kind='analysis_data',desc='Source relation I_up ∝ (I_exc)^n. Figure 8 uses natural-log axes and reports slopes; fitted intercepts, errors, raw points, power units and fitting weights are absent.')
P(r,'nano','Figure 8 power-dependence specimen',POWER)
for w,rounded,precise in [(519,2.20,2.2024),(541,1.89,1.8853),(653,2.09,2.0907)]:
 M(r,'slope-prose-'+str(w),'nano','prose_power_law_exponent',rounded,'dimensionless',E(3,'Power-law slopes'),status='author_derived',tech='Log–log regression',conditions=f'{w} nm channel; source rounded prose value.')
 M(r,'slope-figure-'+str(w),'nano','figure_power_law_exponent',precise,'dimensionless',E(4,'Figure 8 legend'),status='author_derived',tech='Log–log regression',conditions=f'{w} nm channel in legend; additional displayed precision is not a stated fit uncertainty.')
T(r,'relation','nano','source_power_law_relation','I_up ∝ (I_exc)^n; I_up is up-conversion emission intensity, I_exc is near-IR excitation intensity, and n is interpreted as excitation photon number.',POWER)
M(r,'photon-count','nano','author_inferred_excitation_photon_count',2,'photons',POWER,status='author_derived',conditions='Approximate slopes near two support the authors’ two-photon interpretation; no uniquely resolved microscopic pathway or absolute efficiency follows from this fit alone.')
M(r,'caption-wavelength','nano','figure8_caption_short_wavelength_channel',520,'nm',E(4,'Figure 8 caption'),conditions='Caption conflicts with 519 nm in the body, diagram and plotted legend.')
T(r,'figure-axes','nano','figure8_display_axes','ln(I_exc) horizontal ticks run approximately 2.0–4.0; ln(I_up) vertical ticks approximately 2–8. No physical reference intensity or dimensional logarithm normalization is supplied.',E(4,'Figure 8 axes'))
r['quality']['conflicts']=['Figure 8 caption says 520 nm; body and legend say 519 nm. Both are retained without relabeling the original image.'];records.append(r)

r=base('mechanisms','Energy transfer, surface interpretation and source limitations')
P(r,'study','Author mechanism and literature context',MECH+E(1,'Introduction'))
T(r,'sensitizer','study','author_sensitizer_emitter_roles','Yb acts as absorber/sensitizer and Er as emitter in the host lattice. Yb excitation near 980 nm transfers energy to Er; rates and site occupancies are not measured.',E(2,'Introduction')+MECH,status='author_derived')
T(r,'two-steps','study','author_two_photon_excitation_path','Under 980 nm excitation Er electrons are excited 4I15/2 → 4I11/2 → 4F7/2, followed mainly by nonradiative relaxation to 2H11/2, 4S3/2 and 4F9/2 before emission.',MECH,status='author_derived')
T(r,'energy-diagram','study','figure9_energy_level_scope','Yb 2F7/2 and 2F5/2 levels; Er 4I15/2, 4I13/2, 4I11/2, 4I9/2, 4F9/2, 4S3/2, 2H11/2 and 4F7/2 levels. Diagram is schematic with no numerical level energies, measured lifetimes or transfer rates.',E(4,'Figure 9'))
T(r,'bulk-decay','study','author_bulk_nano_relaxation_interpretation','Stronger bulk red emission is interpreted as a larger population of Er 4F9/2 and a higher probability of relaxation to this lower emitting state compared with nanocrystals.',COMP,status='author_derived')
T(r,'surface-sites','study','author_surface_luminescence_hypothesis','Smaller particles expose more luminescent ions; surface ions remain part of the lattice but interact more weakly with surrounding ions because of pendent bonds. This is a proposed explanation, not a measured surface-site census.',MECH,status='author_derived')
T(r,'lifetime','study','author_surface_lifetime_hypothesis','Weaker local interaction is proposed to prolong Er 4I11/2 lifetime and improve up-conversion efficiency, citing Blasse (reference 25). No lifetime trace or absolute efficiency measurement is reported.',MECH,status='author_derived')
T(r,'emission-location','study','author_emission_surface_interior_assignment','519 nm emission is mainly attributed to surface luminescent ions and 653 nm to interior ions. No spatially resolved emission, surface-selective control or separate rate measurement directly verifies this assignment.',MECH,status='author_derived')
T(r,'size-explanation','study','author_size_effect_scope','Authors assume matched nominal composition/structure when attributing nano/bulk spectral differences to size and surface effects. Source gives no measured dopant distribution, exact phase fraction, normalization or isolated size-controlled series.',COMP+MECH,status='author_derived')
T(r,'background','study','literature_materials_scope','Introduction cites down-conversion ZnS:Mn and Y2O3:Eu, and discussion cites Y2O3:Tb, Eu-doped CaS and rare-earth oxysulfides. These are background comparisons, not new syntheses in this paper.',E(1,'Introduction')+E(5,'Discussion'))
T(r,'applications','study','prospective_application_scope','Bioassay/biochip labels for DNA, RNA and proteins motivate narrow nanoscale distributions, low background, resistance to photobleaching and multiplexing. Solid-state lasers and GaAs LED conversion are prior application context; no current bioconjugation, assay, photobleaching trial, device or laser performance is demonstrated.',E(1,'Introduction')+E(5,'Conclusion'))
T(r,'excitation-definition','study','upconversion_definition','At least two low-energy photons are required in the introductory description to produce one higher-energy photon; down-conversion gives lower-energy output after higher-energy excitation.',E(1,'Introduction'))
T(r,'reference-scope','study','cited_method_access','Reference 15: X. Yu, Practical luminescent materials and mechanism of photoluminescence (Chinese), 1997, is cited for bulk preparation. Reference 16 supports phase data; 17–24 support assignments and up-conversion, 25 lifetime arguments, 26–27 grinding/defect analogies. Their bibliographic entries were inspected, not their external full texts.',E(2,'References 15–16')+E(5,'References 17–27'))
T(r,'source-completeness','study','inspected_source_scope','All five supplied main pages, ten figures, captions and 27 bibliography entries were read and visually inspected. No SI declaration, matched SI, tables, numbered equation, source atomic coordinate file, SAED or raw measurement arrays were supplied.',E(1,'Article opening')+E(5,'Article ending'))
T(r,'intensity-efficiency','study','intensity_efficiency_distinction','The article uses high efficiency and stronger fluorescent intensity qualitatively. Its arbitrary intensity plots do not provide a measured absolute up-conversion quantum yield, calibrated absorbed-photon efficiency or universal nano/bulk enhancement ratio.',UC+COMP)
records.append(r)

if __name__=='__main__':
 out=B/'canonical-drafts';out.mkdir(exist_ok=True);errors=[]
 for r in records:
  errors+=validate_record(r);(out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report={'status':'failed'if errors else'passed','record_count':len(records),'operation_count':sum(len(r['operations'])for r in records),'measurement_count':sum(len(r['measurements'])for r in records),'material_slots':sum(len(r['materials'])for r in records),'source_read_pages':5,'source_visual_pages':5,'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (B/'canonical-material-identities.json').write_text(json.dumps({'source_id':SID,'source_group':SID,'materials':[{'id':i,'name':n,'formula':f}for i,(n,f,e)in CHEM.items()],'record_material_ids':{r['record_id']:[m['id']for m in r['materials']]for r in records}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 raw=json.loads((B/'source-manifest.json').read_text(encoding='utf-8-sig'))
 (B/'canonical-record-manifest.json').write_text(json.dumps({'source_id':SID,'source_group':SID,'source_sha256':raw.get('sha256'),'main_pages_read_and_visually_inspected':5,'supporting_information':'No SI supplied or independently matched.','records':[{'id':r['record_id'],'record_type':r['record_type'],'sha256':hashlib.sha256((out/(r['record_id']+'.json')).read_bytes()).hexdigest(),'operation_ids':[o['id']for o in r['operations']],'sample_ids':[p['sample_id']for p in r['products']],'measurements':len(r['measurements'])}for r in records]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report))
 if errors:raise SystemExit(1)
