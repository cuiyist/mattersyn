"""Private Yao 1998 extraction; no import or scientific-review promotion."""
from pathlib import Path
from copy import deepcopy
import sys,json
B=Path(__file__).resolve().parent
S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='yao1998'; PREFIX='yao-1998-'
SRC=source(SID,'10.1021/la970480g','Electrolyte Effects on CdS Nanocrystal Formation in Chelate Polymer Particles: Optical and Distribution Properties','Hiroshi Yao; Yukako Takada; Noboru Kitamura',1998)
SRC['main_status']='All seven supplied main pages read and visually inspected; independent audit pending'
def E(p,loc):return ev(SID,f'Main PDF p. {p}, printed p. {594+p}, {loc}')
MAT=E(2,'Experimental Section: Materials'); PREP=E(2,'Preparation of CdS Nanocrystals/Polymer Hybrids'); MEAS=E(2,'Measurements')
def Q(v=None,u='',e=PREP,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=PREP,**kw):return fact(v,deepcopy(e),**kw)
CHEM={'resin':('Chelex 100 chelate polymer microparticles',None),'cd-loaded-resin':('Cadmium-loaded Chelex 100 microparticles',None),'cd-acetate':('Cadmium acetate dihydrate','Cd(C2H3O2)2·2H2O'),'na2s':('Sodium sulfide nonahydrate','Na2S·9H2O'),'nacl':('Sodium chloride','NaCl'),'water':('Distilled water','H2O'),'methanol':('Methanol','CH4O'),'ethanol':('Ethanol','C2H6O'),'hcl':('Hydrochloric acid','HCl'),'naoh':('Sodium hydroxide','NaOH'),'hybrid':('CdS nanocrystal / Chelex 100 hybrid specimen',None),'licl':('Lithium chloride','LiCl'),'kcl':('Potassium chloride','KCl'),'tmacl':('Tetramethylammonium chloride','C4H12NCl')}
CHEM['diagnostic-hs']=('Hydrosulfide test solution','HS−')
def C(i,role='solvent',stage='synthesis',e=MAT,**kw):return material(i,*CHEM[i],role,stage,deepcopy(e),**kw)
def base(key,title,kind='procedure',method='Supporting procedure'):
 r=record(PREFIX+key,'Yao et al. (1998) · '+title,'CdS/polymer','II–VI nanocrystals in chelate polymer microparticles',method,deepcopy(SRC),'Main PDF pp. 1–7, printed pp. 595–601',kind)
 r['schema_version']='1.2.0';r['collection']='reviewed_literature';r['material'].update(components=['CdS'],elements=['Cd','S','C','H','N','O'],architecture='composite');r['lineage']['recipe_family']='yao1998-cds-chelex'
 r['intended_target']['composition']=F('CdS nanocrystals embedded in Chelex 100 polymer',PREP)
 r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],review_scope='Private full supplied-main extraction. Independent audit and publication pending; SI not located or verified.',missing_fields=['Matching supporting information not located or verified.','No atomic coordinates, exact physical batch IDs or complete specimen-to-batch joins supplied.'],conflicts=[],experimental_outcome='not_established')
 r['context_links']=[{'label':'Full paper review','url':'../paper-review.html?id=yao1998','relation':'Seven supplied main pages; SI not located or verified.'}]
 return r
def link(r,key,label,relation):r['context_links'].append({'label':label,'url':'../records/'+PREFIX+key+'.html','relation':relation})
def add(r,i,action,label,inputs,out,e=PREP,parameters=None,stage='synthesis',description='',depends=None,branch='main',kind='mixture',retained=False,environment=None):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out] if out else [],depends=depends,parameters=parameters or {},stage=stage,description=description,branch=branch,environment=F(environment,e),retained_fraction=out if retained else None))
def stock(i,label,ids,e=PREP,amounts=None,concs=None,ops=None,scope=''):
 return {'id':i,'name':label,'components':[{'material_id':x,'quantities':(amounts or {}).get(x,{})}for x in ids],'concentrations':concs or {},'preparation_operation_ids':ops or [],'scope':scope,'evidence':deepcopy(e)}
def P(r,i,label,composition='CdS nanocrystals in Chelex 100 polymer',e=PREP,sid=None,explicit=False,notes=None):
 p=product(i,composition,deepcopy(e),link='explicit' if explicit else 'general_context',state=sid,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
records=[]
r=base('resin-conditioning','Chelex 100 purification and storage')
r['material'].update(formula='Chelex 100',components=[],elements=['C','H','N','O'],architecture='single_material')
r['intended_target']['composition']=F('Washed and dried Chelex 100 resin',MAT)
r['materials']=[C('resin','host matrix','precursor_preparation',quantities={'mesh':Q(u='mesh',e=MAT,minimum=200,maximum=400),'dry_fixed_charge_capacity':Q(2,'mequiv/g',e=MAT),'wet_fixed_charge_capacity':Q(0.4,'mequiv/mL',e=MAT)},notes=['Analytical Grade, Bio-Rad Laboratories. Styrene–divinylbenzene copolymer bearing iminodiacetate groups -CH2N(CH2COO-)2. Polymer formula and crosslink ratio unreported. Fixed charges from cited manufacturer manual, not a new measurement.']),*[C(i,stage='precursor_preparation')for i in ['water','methanol','hcl','naoh','ethanol']]]
r['stocks']=[stock('hcl-wash','Aqueous HCl wash',['hcl','water'],MAT,concs={'hcl_molarity':Q(2,'mol/L',e=MAT)},scope='Wash volume unreported.'),stock('naoh-wash','Aqueous NaOH wash',['naoh','water'],MAT,concs={'naoh_molarity':Q(2,'mol/L',e=MAT)},scope='Wash volume unreported.')]
add(r,'soak','polymer_swelling','Soak the resin in distilled water',['resin','water'],'soaked',MAT,stage='precursor_preparation',description='Duration and water volume not supplied.')
last='soaked';dep='soak'
for key,inp,label in [('methanol','methanol','Wash with methanol'),('hcl','hcl-wash','Wash with 2 M hydrochloric acid'),('naoh','naoh-wash','Wash with 2 M sodium hydroxide'),('water','water','Wash thoroughly with distilled water')]:
 add(r,'wash-'+key,'resin_washing',label,[last,inp],'washed-'+key,MAT,depends=[dep],stage='precursor_preparation',description='Successive source order; wash volume, cycles and separation method unreported.',retained=True,kind='fraction',parameters={'eluent_ph':Q(10,'pH',e=MAT,approximate=True)}if key=='water'else{});last='washed-'+key;dep='wash-'+key
add(r,'ethanol','solvent_treatment','Treat the washed resin with ethanol',[last,'ethanol'],'ethanol-treated',MAT,depends=[dep],stage='precursor_preparation',description='Treatment amount, duration and recovery method unreported.')
add(r,'dry','vacuum_drying','Dry the resin under vacuum',['ethanol-treated'],'dry-resin',MAT,depends=['ethanol'],stage='precursor_preparation',environment='Vacuum; numerical pressure unreported',kind='product')
add(r,'store','storage','Store the dried resin',['dry-resin'],'stored-resin',MAT,depends=['dry'],stage='storage',description='Storage temperature, atmosphere, container and duration unreported.',kind='product')
P(r,'conditioned-resin','Conditioned Chelex 100','Chelex 100 polymer',MAT,'stored-resin',True)
link(r,'cadmium-loading','Cadmium loading','Upstream host preparation.');records.append(r)

r=base('cadmium-loading','Load cadmium ions into the chelate resin')
r['material'].update(formula='Cd/Chelex 100',components=[],elements=['Cd','C','H','N','O'],architecture='composite')
r['intended_target']['composition']=F('Cadmium-loaded Chelex 100 resin',PREP)
r['materials']=[C('resin','host matrix','precursor_preparation',PREP,quantities={'dry_mass':Q(0.107,'g')}),C('cd-acetate','metal_precursor','precursor_preparation',MAT,notes=['GR grade, Kanto Chemical, used as received.']),C('water',stage='precursor_preparation',e=PREP),C('diagnostic-hs','diagnostic reagent','characterization',PREP,notes=['Source names HS− as the diagnostic species. Counterion, stock source, diagnostic concentration and quantity are unreported. Formula describes the ion, not an isolated neat reagent.'])]
r['stocks']=[stock('cadmium-stock','Aqueous cadmium acetate',['cd-acetate','water'],concs={'molarity':Q(8.4e-3,'mol/L'),'solution_volume':Q(5,'mL')},scope='0.107 g dry resin in 5.0 mL of 8.4×10−3 M aqueous cadmium acetate. Concentration is reported; no reagent mass inferred.'),stock('diagnostic-sulfide','Diagnostic hydrosulfide test solution',['diagnostic-hs','water'],scope='Qualitative supernatant check; diagnostic concentration and aliquot volume unreported.')]
add(r,'load','ion_exchange_sonication','Soak and sonicate the resin in cadmium solution',['resin','cadmium-stock'],'loading',stage='precursor_preparation',parameters={'duration':Q(10,'min')},description='Sonication frequency and power unreported; initial temperature unreported.')
add(r,'equilibrate','standing','Store the loading suspension at room temperature',['loading'],'loaded-suspension',depends=['load'],stage='precursor_preparation',parameters={'duration':Q(2,'day'),'temperature':Q(u='degC',qualifier='room temperature')})
add(r,'take-supernatant','supernatant_sampling','Separate a supernatant test aliquot',['loaded-suspension'],'supernatant-aliquot',depends=['equilibrate'],stage='characterization',branch='diagnostic aliquot',kind='aliquot',description='Supernatant fraction only; aliquot volume and separation technique unreported. This diagnostic branch does not consume the retained cadmium-loaded beads.')
add(r,'supernatant-test','qualitative_precipitation_test','Test the supernatant for unbound cadmium',['supernatant-aliquot','diagnostic-sulfide'],'test-result',depends=['take-supernatant'],stage='characterization',branch='diagnostic aliquot',description='Supernatant did not react with HS− to produce CdS. The authors interpret this as all Cd2+ incorporated; no analytical detection limit or independent concentration assay supplied.')
add(r,'wash','resin_washing','Wash cadmium-loaded resin several times',['loaded-suspension','water'],'cd-loaded',depends=['equilibrate'],stage='precursor_preparation',kind='product',retained=True,description='Distilled water; wash volume and recovery method unreported. Diagnostic aliquot is separate from the retained resin.')
p=P(r,'loaded-resin','Cd2+-polymer','Cadmium-loaded Chelex 100',PREP,'cd-loaded',True)
r['measurements']=[measurement('loading-fraction','loaded-resin','adsorbed_cadmium_fraction_of_capacity',Q(0.4,'fraction',approximate=True,status='author_derived'),'Source adsorption-capacity comparison',PREP,'Approximate uptake relative to total resin adsorption capacity; not a CdS synthesis yield.'),measurement('supernatant-outcome','loaded-resin','supernatant_cadmium_test',F('No CdS precipitation observed upon HS− addition'),'Qualitative supernatant test',PREP,'No detection limit; author inference of complete uptake is not an independently measured zero concentration.')]
link(r,'resin-conditioning','Resin conditioning','Common upstream purification.');records.append(r)

saltconflict='Sample b is pretreated in 10 mL of 0.5 M NaCl before adding 100 mL aqueous Na2S, but figures and discussion retain a 0.5 M sample-b label. No adjustment or post-mixing salt concentration is stated; preserve stock concentration and nominal sample label separately.'
clockconflict='The method gives 2 h stirring followed by 2 days standing, whereas Figure 1b labels reaction time 48 h. The relation of the 48 h characterization clock to the sequential method duration is not resolved.'
for x in ['a','b']:
 r=base('sample-'+x,'CdS in chelate polymer, '+('without added NaCl (sample a)'if x=='a'else'with NaCl pretreatment (sample b)'),'literature_protocol','Aqueous reaction within a chelate polymer')
 r['intended_target']['host']=F('Chelex 100 styrene–divinylbenzene copolymer with iminodiacetate groups',MAT)
 r['materials']=[C('cd-loaded-resin','metal_precursor',e=PREP,notes=['Common upstream loading uses 0.107 g dry resin, 5.0 mL 8.4×10−3 M cadmium acetate. No separate physical batch or recovered loaded-resin mass supplied.']),C('na2s','chalcogen_precursor',e=MAT,notes=['Na2S·9H2O, GR grade, Wako Pure Chemicals, as received. Fresh aqueous feed; Note 15 describes Na+, HS− and OH− under source conditions.']),C('water',e=PREP),C('ethanol',stage='workup',e=PREP)]
 if x=='b':r['materials'].append(C('nacl','electrolyte',e=MAT,notes=['GR grade, Kanto Chemical, as received. 0.5 M is the pretreatment-stock concentration and later nominal source condition, not a verified final-mixture concentration.']))
 r['materials'][1]['evidence']+=E(1,'Note 15: source aqueous sulfide species')
 r['stocks']=[stock('sulfide-stock','Fresh dilute aqueous sodium sulfide',['na2s','water'],concs={'molarity':Q(3.8e-4,'mol/L',status='reported'if x=='a'else'inherited',basis=''if x=='a'else'Procedure analogous to sample a'),'solution_volume':Q(100,'mL',status='reported'if x=='a'else'inherited',basis=''if x=='a'else'Procedure analogous to sample a')},ops=['prepare-sulfide'],scope='Freshly prepared; final reaction concentration not stated. Sample b inherits this feed from the expressly analogous sample-a procedure.')]
 if x=='b':r['stocks'].append(stock('nacl-stock','Aqueous sodium chloride pretreatment',['nacl','water'],concs={'molarity':Q(0.5,'mol/L'),'solution_volume':Q(10,'mL')},scope='Pretreatment stock. Post-mixing concentration unresolved.'))
 add(r,'precondition','electrolyte_preconditioning'if x=='b'else'polymer_dispersion','Pretreat cadmium-loaded beads with NaCl'if x=='b'else'Disperse cadmium-loaded beads in water',['cd-loaded-resin','nacl-stock'if x=='b'else'water'],'preconditioned',parameters={'duration':Q(10,'min'),**({'water_volume':Q(10,'mL')}if x=='a'else{})},description='Cd2+ did not elute during the source NaCl treatment. Pretreatment temperature not supplied.'if x=='b'else'No added NaCl; solution is not asserted to have zero total ionic strength.')
 add(r,'prepare-sulfide','stock_preparation','Prepare the fresh dilute sulfide solution',['na2s','water'],'fresh-sulfide',stage='precursor_preparation',description='100 mL, 3.8×10−4 M Na2S solution. No stock storage period or preparation mass supplied.')
 add(r,'add-sulfide','solution_addition','Add sulfide solution under vigorous stirring',['preconditioned','sulfide-stock'],'reaction-mixture',depends=['precondition','prepare-sulfide'],description='Addition rate, vessel geometry, temperature, atmosphere and pressure unreported. Beads slowly become pale yellow; the source describes faster coloration with NaCl.')
 add(r,'stir','stirring','Stir the reaction mixture',['reaction-mixture'],'stirred',depends=['add-sulfide'],parameters={'duration':Q(2,'h')},description='Stirring speed and temperature not supplied. Analytical time-point sampling is a separate branch, not an extra chronological step after standing.')
 add(r,'stand','standing','Allow the reaction suspension to stand',['stirred'],'aged',depends=['stir'],parameters={'duration':Q(2,'day'),'temperature':Q(u='degC',qualifier='room temperature')},description=clockconflict)
 add(r,'remove-supernatant','supernatant_removal','Remove the supernatant and retain the beads',['aged'],'recovered',depends=['stand'],stage='workup',kind='fraction',retained=True,description='Recovery technique unreported; no centrifuge, filtration or decantation technique inferred.')
 last='recovered';dep='remove-supernatant'
 for solv in ['water','ethanol']:
  add(r,'wash-'+solv,'resin_washing','Wash thoroughly with '+solv,[last,solv],'washed-'+solv,depends=[dep],stage='workup',kind='fraction',retained=True,description='Source order water then ethanol. Volumes and cycle counts unreported.');last='washed-'+solv;dep='wash-'+solv
 add(r,'dry','vacuum_drying','Dry the CdS/polymer hybrid',['washed-ethanol'],'hybrid-product',depends=[dep],stage='workup',kind='product',environment='Vacuum; numerical pressure unreported',description='Drying temperature and duration unreported; product remains embedded in the host polymer.')
 p=P(r,'sample-'+x,'sample '+x,sid='hybrid-product',explicit=True,notes=['Nominal formulation; exact physical batch and analytical aliquot identifiers unreported. XRD/TEM/optical data have separately scoped specimen records.']);p['morphology']=F('Pale-yellow CdS-containing polymer microparticles')
 r['quality']['experimental_outcome']='reported_product';r['quality']['conflicts']=[clockconflict]+([saltconflict]if x=='b'else[])
 r['quality']['missing_fields']+=['No isolated yield, actual free CdS mass, numerical temperature during stirring, gas environment, mixing rate, drying duration, or recovery settings.']
 link(r,'cadmium-loading','Cadmium-loaded host preparation','Common upstream procedure; no recovered mass or unique batch split asserted.');link(r,'timepoint-workup','Time-resolved sampling and workup','Analytical branch sampled at times after mixing.');link(r,'characterization','Structure, distribution and optical data','Source formulation and depth contexts; no unsupported same-aliquot joins.');records.append(r)

r=base('timepoint-workup','Time-resolved aliquot sampling and specimen workup')
r['materials']=[C('hybrid','reaction suspension','characterization',PREP),C('water',stage='workup',e=PREP),C('ethanol',stage='workup',e=PREP)]
add(r,'sample','aliquot_sampling','Withdraw a time-point aliquot',['hybrid'],'aliquot',stage='characterization',kind='aliquot',parameters={'aliquot_volume':Q(u='mL',qualifier='several milliliters')},description='Sample at various times after Na2S mixing. Full list of withdrawal times and total aliquot count not supplied; do not fabricate an experiment per plotted point.')
add(r,'recover','supernatant_removal','Remove the aliquot supernatant',['aliquot'],'beads',depends=['sample'],stage='workup',kind='fraction',retained=True,description='Recovery method and quench chemistry unreported. Washing is not evidence of an instantaneous reaction quench.')
for solv,last,dep in [('water','beads','recover'),('ethanol','washed-water','wash-water')]:add(r,'wash-'+solv,'resin_washing','Wash aliquot beads with '+solv,[last,solv],'washed-'+solv,depends=[dep],stage='workup',kind='fraction',retained=True)
add(r,'dry','vacuum_drying','Dry the sampled hybrid',['washed-ethanol'],'dry-aliquot',depends=['wash-ethanol'],stage='workup',environment='Vacuum; pressure unreported',kind='product')
P(r,'timepoint-specimen','Time-point hybrid specimen',sid='dry-aliquot',explicit=True,notes=['Known timing anchor: after mixing. No unique aliquot labels, quench kinetics or exact full sampling schedule.'])
link(r,'absorption','Absorption specimen preparation','Dry particles redispersed in water for microspectroscopy.');records.append(r)

r=base('absorption','Single-particle absorption microspectroscopy')
r['materials']=[C('hybrid','analytical specimen','characterization',MEAS),C('water',stage='characterization',e=MEAS)]
add(r,'redisperse','polymer_swelling','Disperse hybrid particles in water',['hybrid','water'],'wet-hybrid',MEAS,stage='characterization',description='Reduces scattering from dry beads. Polymer swells in water; 100–110 µm is wet host diameter, not nanocrystal diameter.')
add(r,'acquire','absorption_microspectroscopy','Measure absorption of a single hybrid particle',['wet-hybrid'],'absorption-results',MEAS,depends=['redisperse'],stage='characterization',parameters={'lamp_power_rating':Q(150,'W',e=MEAS,basis='Source lamp specification; not sample irradiance or delivered optical power'),'wet_host_diameter':Q(u='um',e=MEAS,minimum=100,maximum=110)},description='Nikon Optiphoto 2, Oriel Multispec 257 polychromator, Princeton Instruments ICCD-576E/G multichannel detector; Hamamatsu L2273 Xe lamp. Beam diameter, path length, spectral resolution and measurement temperature unreported.')
add(r,'time-readout','absorbance_readout','Evaluate absorbance at 450 nm',['absorption-results'],'kinetic-readout',E(3,'Figure 2 and formation kinetics')+E(5,'Figure 8 discussion'),depends=['acquire'],stage='characterization',parameters={'monitor_wavelength':Q(450,'nm',e=E(3,'Figure 2'))},description='450 nm is a monitoring wavelength near an excitonic shoulder, not a new peak or bandgap label. Note 27 limits its early-time interpretation. Different formulation/time specimens remain distinct.')
r['operations'][-1]['evidence']+=E(6,'Note 27: early-time optical interpretation limit')
P(r,'absorption-specimens','Wet single-particle optical specimens',e=MEAS,sid='wet-hybrid',notes=['No independent synthesis; spectra at nominal 30 min and 48 h and kinetic series do not by themselves identify physical batch/aliquot joins.']);records.append(r)

r=base('optical-microscopy','Optical imaging of the CdS dispersion layer')
r['materials']=[C('hybrid','analytical specimen','characterization',MEAS)]
add(r,'image','optical_microscopy','Image individual hybrid particles',['hybrid'],'optical-images',MEAS,stage='characterization',description='Sony DXC-930 CCD camera attached to the microscope; Mitsubishi CP-11 video printer. Figure 6 optical image contains a 25 µm scale bar. Do not equate the bright ring with an atomically thin shell.')
add(r,'measure-layer','radial_layer_measurement','Measure the width from bead surface to the ring boundary',['optical-images'],'layer-results',E(3,'Figure 6 and definition of L')+E(5,'Figure 9 discussion'),depends=['image'],stage='characterization',parameters={'precision_limit':Q(4,'um',e=E(5,'Layer width limitation'),qualifier='L below this value was not measured precisely; not an instrumental resolution specification')},description='L is CdS dispersion-layer width within the host; small L ring boundary is hard to establish. Absorbance-derived early L is an author-model estimate, not a direct image measurement.')
P(r,'optical-image-specimens','Single-particle layer-imaging specimens',e=MEAS,notes=['Figure 6 identifies sample a. General time-dependent layer measurements discuss both formulations.']);records.append(r)

r=base('xrd','X-ray diffraction acquisition')
r['materials']=[C('hybrid','analytical specimen','characterization',MEAS)]
add(r,'acquire','xrd','Acquire the diffraction pattern',['hybrid'],'diffraction',MEAS,stage='characterization',parameters={'two_theta_range':Q(u='degree',e=MEAS,minimum=20,maximum=60),'xray_wavelength':Q(0.154,'nm',e=MEAS)},description='Rigaku RINT 2000, Cu Kα. Specimen mount, scan speed, step size and instrumental-broadening correction are not supplied. No original XRD pattern is printed in these seven pages.')
add(r,'fit','xrd_peak_fit','Fit the broad reflection and estimate crystallite size',['diffraction'],'size-estimates',E(3,'XRD discussion'),depends=['acquire'],stage='characterization',parameters={'fitted_two_theta':Q(26.5,'degree',e=E(3,'XRD discussion'))},description='Gaussian fit to 26.5° reflection and Debye–Scherrer formula (source spelling Debye–Scheller), references 22–23. Derived mean sizes 3.8 nm (a) and 3.1 nm (b), not raw TEM diameters.')
for x in ['a','b']:P(r,'xrd-'+x,'sample '+x+' XRD',e=E(3,'XRD discussion'),notes=['Source formulation identity explicit; exact reaction age and specimen-to-TEM or optical linkage unreported.'])
records.append(r)

r=base('tem','TEM cross-section preparation and imaging')
r['materials']=[C('hybrid','analytical specimen','characterization',MEAS)]
add(r,'section','polymer_sectioning','Prepare a thin hybrid-particle cross section',['hybrid'],'sections',E(3,'Dispersion textures: TEM preparation'),stage='characterization',kind='fraction',description='Source notes elaborate effort due to swelling in water. Embedding resin, sectioning instrument, section thickness, dehydration and staining are not reported.')
add(r,'low','tem','Acquire low-magnification TEM',['sections'],'low-mag',MEAS+E(4,'Figure 3')+E(6,'Figure 7'),depends=['section'],stage='characterization',description='Hitachi H-300; source Figure 3 sample a and Figure 7 sample b. Each panel has 250 nm bar. Voltage, dose, grid and section orientation calibration unreported.')
add(r,'high','tem','Acquire high-magnification TEM',['sections'],'high-mag',MEAS+E(4,'Figure 4'),depends=['section'],stage='characterization',description='JEOL JEM 2010; Figure 4 sample a surface and 4–5 µm interior, 50 nm scale bars. Separate fields of view; no exact atomistic coordinates or SAED image supplied.')
add(r,'distribution','tem_size_distribution','Measure and fit regional size distributions',['high-mag'],'size-distributions',E(5,'Figure 5'),depends=['high'],stage='characterization',description='Sample a: surface log-normal fit mean 2.7 nm, SD 0.4 with unit unspecified; interior normal fit mean 4.6 nm, SD 1.8 nm. Raw particle lists, counts and fit uncertainty not tabulated. Do not substitute flocculate size for constituent nanocrystal size.')
P(r,'tem-specimens','Cross-sectional TEM fields',e=MEAS,notes=['Formulation, radial depth and magnification constrain sample scope; raw identifiers or whole-batch representation are unreported.']);records.append(r)

# Qualitative electrolyte substitutions are documented comparisons, not complete recipes.
r=base('other-electrolytes','Comparative monovalent-electrolyte observations','observation','Qualitative electrolyte comparison')
e=E(4,'Note 25: LiCl, KCl and tetramethylammonium chloride')
r['materials']=[C('hybrid','contextual analytical specimen','characterization',e),*[C(i,'electrolyte','characterization',e,quantities={'nominal_source_concentration':Q(0.5,'mol/L',e=e,basis='Reported electrolyte condition; stock versus final mixture is not stated for these comparisons')})for i in ['licl','kcl','tmacl']]]
for i in ['licl','kcl','tmacl']:
 p=P(r,'electrolyte-'+i,CHEM[i][0]+' comparison',e=e,notes=['Qualitative comparison in Note 25 only. Individual preparation amounts, duration, specimen history, exact spectra and layer widths are not supplied. Other electrolyte materials in this record are separate comparisons, not one combined mixture.'])
 for prop,label in [('visible_absorption_comparison','Visible absorption quite similar to the nominal 0.5 M NaCl sample'),('cds_layer_width_comparison','CdS layer width L quite similar to the nominal 0.5 M NaCl sample')]:
  r['measurements'].append(measurement(i+'-'+prop,p['sample_id'],prop,F(label,e),'Qualitative source comparison',e,'Note 25; no numeric difference, uncertainty, equivalence criterion or independent batch count.'))
r['quality']['missing_fields']+=['Comparative electrolyte routes are not independently specified; no full synthesis protocol is inferred from a qualitative note.']
link(r,'sample-b','NaCl-treated route','Reference formulation for the qualitative comparisons.');records.append(r)

if __name__=='__main__':
 from characterization_rows import build_characterization
 records.append(build_characterization(base,P,Q,F,E,measurement))
 out=B/'canonical-drafts';out.mkdir(exist_ok=True)
 errors=[]
 for r in records:
  errors+=validate_record(r)
  (out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 report={'status':'failed'if errors else'passed','scope':'All 11 source-scoped drafts; schema validation only. Independent scientific, reader and publication gates are tracked separately.','records':len(records),'operations':sum(len(r['operations'])for r in records),'measurements':sum(len(r['measurements'])for r in records),'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(report))
 if errors:raise SystemExit(1)
