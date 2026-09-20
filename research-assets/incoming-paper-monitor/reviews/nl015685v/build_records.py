"""Complete private extraction of the supplied six-page Besson et al. main article.
No outside literature, inferred atomic coordinates, or unreported absolute charges.
"""
from pathlib import Path
from copy import deepcopy
import json,sys,hashlib
B=Path(__file__).resolve().parent; S=B.parents[3]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='besson2002'; PRE='besson-2002-'; FORMULA='CdS/SiO2'
SRC=source(SID,'10.1021/nl015685v','3D Quantum Dot Lattice Inside Mesoporous Silica Films','Sophie Besson; Thierry Gacoin; Christian Ricolleau; Catherine Jacquiod; Jean-Pierre Boilot',2002,si='No supporting information supplied or matched; SI existence/availability is not established by the supplied six-page main article.')
SRC['main_status']='All six supplied main pages read and visually inspected, including four figures, captions and references/notes. Independent audit pending.'
def E(p,s): return ev(SID,f'Main PDF p. {p}, printed p. {408+p}, {s}')
HOST=E(2,'Mesoporous matrix preparation, lower left to upper right'); CD=E(2,'Cadmium impregnation solution and impregnation–precipitation protocol'); UV=E(2,'UV–visible results')+E(3,'Figure 1'); X=E(2,'XRD acquisition and initial adsorption')+E(3,'Figure 2 and XRD discussion'); TEM=E(3,'TEM acquisition')+E(4,'Figure 3 and HRTEM discussion'); PL=E(4,'Luminescence acquisition')+E(5,'Figure 4 and luminescence discussion'); VOL=E(3,'CdS and mesopore volume fractions')+E(5,'Reference note 36')+E(6,'Reference note 38')
def Q(v=None,u='',e=CD,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=CD,**kw):return fact(v,deepcopy(e),**kw)
CHEM={
 'teos':('Tetraethyl orthosilicate (TEOS)','Si(OC2H5)4',HOST),
 'water':('Water; deionized for the rinse','H2O',CD+HOST),
 'acidified-water':('Acidified water at pH 1.25; acid identity unspecified',None,HOST),
 'ethanol':('Ethanol; silica-sol and dilution solvent','C2H6O',HOST),
 'ctab':('Cetyltrimethylammonium bromide (CTAB) template','C19H42BrN',HOST),
 'pyrex':('Pyrex glass slide; substrate grade and dimensions unspecified',None,HOST),
 'air':('Air; calcination atmosphere',None,HOST),
 'cadmium-nitrate':('Cadmium nitrate; hydration state not specified','Cd(NO3)2',CD),
 'ammonia':('Ammonia; stock formulation and concentration unspecified','NH3',CD),
 'sodium-citrate':('Sodium citrate; protonation, sodium stoichiometry and hydrate unspecified',None,CD),
 'h2s':('Hydrogen sulfide gas','H2S',CD),
 'ctab-host':('Calcined CTAB-templated mesoporous silica film','SiO2',HOST),
 'cadmium-adsorbed-film':('Cadmium-adsorbed silica film before hydrogen sulfide treatment',None,CD+X),
 'copolymer-host':('Triblock-copolymer-templated mesoporous silica film; polymer identity and preparation missing','SiO2',E(2,'Copolymer-host comparison')+E(5,'Reference 37')),
 'cadmium-stock':('Basic aqueous cadmium–citrate–ammonia impregnation solution',None,CD),
 'silicon':('Silicon wafer; optical specimen substrate','Si',PL),
 'mesoporous-film':('Mesoporous silica film for silicon-wafer luminescence specimen; template not independently specified','SiO2',PL),
 'ctab-loaded':('CdS-loaded CTAB-templated silica film','CdS/SiO2',UV+TEM),
 'copolymer-loaded':('CdS-loaded triblock-copolymer-templated silica film','CdS/SiO2',UV),
 'pl-film':('CdS-loaded mesoporous silica film on silicon for luminescence','CdS/SiO2',PL),
 'cds-colloid':('CdS reference colloid; cited reverse-micelle preparation','CdS',VOL),
}
def C(i,role,stage='synthesis',notes=None,e=None):
 n,f,where=CHEM[i];return material(i,n,f,role,stage,deepcopy(e or where),notes=notes or [])
def base(k,title,kind='observation',method='Source-scoped characterization and interpretation',formula=FORMULA):
 r=record(PRE+k,'Besson et al. (2002) · '+title,formula,'Semiconductor quantum dots in ordered mesoporous silica',method,deepcopy(SRC),'Complete supplied main PDF pp. 1–6',kind)
 r['schema_version']='1.3.0';r['collection']='reviewed_literature'
 r['material'].update(elements=['Si','O'] if formula=='SiO2' else ['Cd','S','Si','O'],components=['SiO2'] if formula=='SiO2' else ['CdS','SiO2'],architecture='single_material' if formula=='SiO2' else 'composite')
 r['lineage'].update(source_group=SID,recipe_family='besson2002-cds-mesoporous-silica')
 r['intended_target']['composition']=F(formula,E(1,'Title and abstract'),note='Material-system descriptor, not a single stoichiometric crystal. Mesoscopic order is distinct from the atomic CdS phase.')
 r['quality'].update(review_status='imported_unreviewed',review_scope='All six main pages read and visually inspected. No external reference or SI was obtained; independent source audit and website integration pending.',missing_fields=['No SI, raw spectra, coordinate file, refined atomic lattice parameters or particle-by-particle size table is supplied.','Absolute synthesis charges, film area, impregnation and H2S exposure times, gas flow, vacuum level, and most acquisition settings are absent.','Mesoscopic 3D hexagonal order and atomic CdS blende fringes must remain separate structure descriptions.'],conflicts=[],requested_tasks=['precursor_selection','partial_protocol'] if kind in ['literature_protocol','protocol_variant'] else [],experimental_outcome='reported_product' if kind in ['literature_protocol','protocol_variant'] else 'not_established')
 r['context_links']=[{'label':'Complete paper review','url':'../paper-review.html?id='+SID,'relation':'Original figures, source facts and unresolved limitations.'}]
 return r
def add(r,i,action,label,inputs,out,e,pars=None,stage='synthesis',desc='',env=None,end=None,kind='reaction_batch',depends=None):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out] if out else [],depends=depends if depends is not None else ([r['operations'][-1]['id']] if r['operations'] else []),parameters=pars or {},stage=stage,description=desc,environment=F(env,e),endpoint=F(end,e)))
def P(r,i,label,e,formula=FORMULA,st=None,explicit=False,notes=None):
 p=product(i,formula,deepcopy(e),link='explicit' if explicit else 'general_context',state=st,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
def M(r,i,s,prop,v,u,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,Q(v,u,e,**kw),tech,deepcopy(e),conditions))
def T(r,i,s,prop,value,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,F(value,e,**kw),tech,deepcopy(e),conditions))
def link(r,k,label,rel):r['context_links'].append({'label':label,'url':'../records/'+PRE+k+'.html','relation':rel})
def stock(r,i,name,parts,concs,e,scope,ops=None):r['stocks'].append({'id':i,'name':name,'components':[{'material_id':m,'quantities':qs} for m,qs in parts],'concentrations':concs,'preparation_operation_ids':ops or [],'scope':scope,'evidence':deepcopy(e)})
records=[]

r=base('ctab-silica-host','CTAB-templated mesoporous silica host','literature_protocol','Acid-catalyzed sol–gel preparation, spin coating and template calcination','SiO2')
r['materials']=[C('teos','metalloid_precursor'),C('acidified-water','reagent_stock'),C('water','solvent'),C('ethanol','solvent'),C('ctab','structure_directing_agent'),C('pyrex','substrate'),C('air','process_gas')]
stock(r,'silica-sol','Acidic polymeric silica sol',[('teos',{'molar_ratio':Q(1,'relative mol',HOST)}),('water',{'molar_ratio':Q(5,'relative mol',HOST)}),('ethanol',{'molar_ratio':Q(3.8,'relative mol',HOST)})],{},HOST,'TEOS:water:ethanol = 1:5:3.8 molar. The water has pH 1.25; mixed-sol pH and acid identity/dose are not reported.',['mix','age'])
add(r,'mix','sol_mixing','Mix TEOS, acidified water and ethanol',['teos','acidified-water','ethanol'],'initial-sol',HOST,{'teos_ratio':Q(1,'relative mol',HOST),'water_ratio':Q(5,'relative mol',HOST),'ethanol_ratio':Q(3.8,'relative mol',HOST),'water_pH':Q(1.25,'pH',HOST,basis='pH of starting water, not a measured mixed-sol pH.')},desc='Acid identity and absolute charges are unspecified. The source cites an earlier preparation (reference 29) but reports this molar recipe explicitly.')
add(r,'age','thermal_aging','Age the silica sol',['initial-sol'],'aged-sol',HOST,{'temperature':Q(60,'°C',HOST),'duration':Q(1,'h',HOST)},desc='No stirring speed, atmosphere or heating apparatus is reported.')
add(r,'template','template_dissolution','Dissolve CTAB in the aged sol',['aged-sol','ctab'],'templated-sol',HOST,{'ctab_teos_molar_ratio':Q(.1,'mol/mol',HOST,basis='CTAB/TEOS')})
add(r,'dilute','ethanol_dilution','Dilute the templated sol with ethanol',['templated-sol','ethanol'],'coating-sol',HOST,{'dilution_ratio':Q(1,'ratio',HOST,basis='Source states ethanol (1:1); mass, volume or mole basis is not specified.',raw_text='diluted with ethanol (1:1)')},desc='Do not convert the reported 1:1 dilution into volumes or concentrations without a stated basis.')
add(r,'spin-coat','spin_coating','Spin coat the sol on Pyrex slides',['coating-sol','pyrex'],'coated-slide',HOST,{'rotation_speed':Q(3000,'rpm',HOST),'duration':Q(u='s',e=HOST)},desc='Slide dimensions, dispense volume and spin duration are not reported.')
add(r,'calcine','template_calcination','Calcine in air to remove the template',['coated-slide','air'],'calcined-host',HOST,{'temperature':Q(450,'°C',HOST),'duration':Q(u='h',e=HOST),'heating_rate':Q(u='°C/min',e=HOST)},env='Air',end='Surfactant removed; ordered open mesoporous silica film',desc='No calcination duration, ramp or cooling procedure is provided.')
p=P(r,'host','Calcined CTAB-templated silica film',HOST,'SiO2',st='calcined-host',explicit=True);p['morphology']=F('Ordered mesoporous thin film on Pyrex',HOST)
M(r,'film-thickness','host','film_thickness',300,'nm',HOST,approximate=True)
T(r,'host-meso-order','host','mesoscopic_structure','3D hexagonal order throughout the film thickness; c-axis perpendicular to the substrate',HOST)
T(r,'open-porosity','host','pore_accessibility','Open porosity permits impregnation through the film thickness; interconnected pores are inferred from successful filling.',HOST+E(5,'Conclusion'),status='author_derived')
M(r,'pore-diameter','host','model_derived_average_pore_diameter',3.5,'nm',E(5,'Reference note 36'),tech='Porosity and XRD-based spherical-pore model',status='author_derived',conditions='Assumes spherical pores and hexagonal unit-cell volume determined by XRD. Not a direct TEM pore-size histogram.')
M(r,'initial-c','host','xrd_mesoscopic_c_parameter',6.9,'nm',X,tech='X-ray diffraction',conditions='Initial calcined host before Cd adsorption; not atomic CdS lattice spacing.')
link(r,'ctab-cds-loading','CdS pore filling','Downstream loading route; source-reported film and loading stages are separate records.')
records.append(r)

r=base('cadmium-stock','Cadmium–citrate–ammonia impregnation solution','procedure','Aqueous coordination and pH adjustment')
r['materials']=[C('cadmium-nitrate','metal_precursor','precursor_preparation'),C('water','solvent','precursor_preparation'),C('ammonia','complexing_agent','precursor_preparation'),C('sodium-citrate','complexing_agent','precursor_preparation')]
stock(r,'nitrate-water','Starting cadmium nitrate solution',[('cadmium-nitrate',{}),('water',{})],{'cadmium_nitrate_concentration':Q(.1,'M',CD)},CD,'Starting stock, not the final concentration after ligand additions.')
stock(r,'citrate-water','Sodium citrate stock',[('sodium-citrate',{}),('water',{})],{'sodium_citrate_concentration':Q(1,'M',CD)},CD,'Source associates 1 M in water with sodium citrate. Do not assign 1 M to ammonia.')
stock(r,'final-stock','Basic cadmium impregnation solution',[('cadmium-nitrate',{}),('water',{}),('ammonia',{}),('sodium-citrate',{})],{'final_cadmium_concentration':Q(u='M',e=CD),'final_pH':Q(9.5,'pH',CD)},CD,'Final volume and concentrations are unknown; two ammonia additions are distinct.',['prepare','complex','adjust-ph'])
add(r,'prepare','aqueous_stock_preparation','Prepare the starting aqueous cadmium nitrate stock',['cadmium-nitrate','water'],'nitrate-solution',CD,{'cadmium_nitrate_concentration':Q(.1,'M',CD),'solution_volume':Q(u='mL',e=CD)},stage='precursor_preparation',desc='The paper starts from this solution; salt hydration and absolute charge are unreported.')
add(r,'complex','ligand_addition','Add ammonia and aqueous sodium citrate',['nitrate-solution','ammonia','sodium-citrate','water'],'complexed-cd',CD,{'ammonia_equivalents':Q(1,'equiv',CD,basis='Source says one equivalent added to the cadmium solution; reference amount is not explicitly defined.'),'sodium_citrate_equivalents':Q(1,'equiv',CD,basis='Source says one equivalent; reference amount is not explicitly defined.'),'citrate_stock_concentration':Q(1,'M',CD),'ammonia_stock_concentration':Q(u='M',e=CD)},stage='precursor_preparation',desc='Order between the two ligand additions is not specified. No nitrate/citrate complex stoichiometry is assigned.')
add(r,'adjust-ph','ammonia_ph_adjustment','Add further ammonia to pH 9.5',['complexed-cd','ammonia'],'impregnation-solution',CD,{'target_pH':Q(9.5,'pH',CD),'additional_ammonia_volume':Q(u='mL',e=CD)},stage='precursor_preparation',end='pH 9.5',desc='Further ammonia supplements the initial one-equivalent charge; total ammonia and final Cd concentration cannot be reconstructed.')
P(r,'stock','Cadmium impregnation solution',CD,formula=None,st='impregnation-solution',explicit=True)
T(r,'solution-purpose','stock','complexant_function','Citrate and ammonia retain soluble cadmium species in the alkaline adsorption window and prevent hydroxide precipitation.',E(2,'Chemical strategy and pH window'))
records.append(r)

for key,host,first,last,cycles in [('ctab','ctab-host',2.2,3.6,9),('copolymer','copolymer-host',3.3,5.8,6)]:
 iscop=key=='copolymer';scope=E(2,'Copolymer-host comparison')+E(3,'Figure 1c–d') if iscop else UV
 r=base(key+'-cds-loading',('Triblock-copolymer' if iscop else 'CTAB')+'-templated CdS/silica film','protocol_variant' if iscop else 'literature_protocol','Repeated cadmium adsorption and gaseous hydrogen-sulfide precipitation')
 r['intended_target']['host']=F(CHEM[host][0],scope,note='Porous host identity distinguishes synthesis conditions for equal CdS/SiO2 material-system descriptors; not an atomic target structure.')
 r['materials']=[C(host,'host_matrix',notes=['Source-specific role: porous host confining CdS growth.']),C('cadmium-nitrate','metal_precursor',notes=['Identity within the cadmium impregnation solution; no separately added solid nitrate is implied.']),C('h2s','chalcogen_precursor'),C('cadmium-stock','precursor_stock'),C('water','solvent'),C('ammonia','complexing_agent'),C('sodium-citrate','complexing_agent')]
 stock(r,'impregnation-stock','Cadmium–citrate–ammonia solution',[('cadmium-nitrate',{}),('ammonia',{}),('sodium-citrate',{}),('water',{})],{'starting_cadmium_nitrate_concentration':Q(.1,'M',CD,status='inherited' if iscop else 'reported',basis='Starting nitrate stock before ligand additions, not final impregnation concentration.'),'sodium_citrate_stock_concentration':Q(1,'M',CD,status='inherited' if iscop else 'reported'),'pH':Q(9.5,'pH',CD,status='inherited' if iscop else 'reported'),'final_cadmium_concentration':Q(u='M',e=CD)},CD+scope,'Common loading solution. '+('Applied to the copolymer comparison by contextual inheritance; no separate copolymer-specific preparation quantities are given.' if iscop else 'See the dedicated stock-preparation record.'))
 prefix='Common loading conditions inherited from the paper’s general protocol; no independently quantified copolymer batch. ' if iscop else ''
 add(r,'impregnate','cadmium_adsorption','Impregnate the mesoporous film with cadmium solution',[host,'cadmium-stock'],'cd-adsorbed',CD+scope,{'solution_pH':Q(9.5,'pH',CD,status='inherited' if iscop else 'reported'),'immersion_duration':Q(u='min',e=CD),'solution_volume':Q(u='mL',e=CD)},desc=prefix+'Cadmium species adsorb on pore-wall sites; soak time and volume are missing.')
 add(r,'rinse','water_rinse','Rinse with deionized water',['cd-adsorbed','water'],'rinsed-film',CD+scope,{'rinse_volume':Q(u='mL',e=CD)},stage='workup',desc=prefix+'Retain the film; remove excess cations and avoid accumulation at the film–air interface. No precipitation collection, centrifugation or drying is specified.')
 add(r,'evacuate','film_evacuation','Place the rinsed film under vacuum',['rinsed-film'],'evacuated-film',CD+scope,{'vacuum_pressure':Q(u='Pa',e=CD),'duration':Q(u='min',e=CD)},desc=prefix+'Chamber geometry, vacuum level and dwell time are not reported; evacuation is not a quantified drying step.',env='Vacuum; pressure unspecified')
 add(r,'sulfide','hydrogen_sulfide_admission','Admit hydrogen sulfide gas slowly',['evacuated-film','h2s'],'first-cds-film',CD+scope,{'h2s_pressure_endpoint':Q(u='Pa',e=CD,qualifier='P(H2S) = atmospheric pressure; no numerical pressure or reference atmospheric conditions reported.'),'gas_flow':Q(u='mL/min',e=CD),'exposure_duration':Q(u='min',e=CD)},env='Hydrogen sulfide gas',end='P(H2S) equals atmospheric pressure',desc=prefix+'Slow gas admission precipitates CdS inside the pores. The symbolic pressure endpoint is preserved without assigning 1 atm numerically.')
 add(r,'repeat','impregnation_precipitation_cycles','Repeat impregnation and precipitation to saturation',['first-cds-film','cadmium-stock','water','h2s'],'saturated-film',CD+scope,{'total_cycles':Q(cycles,'cycles',scope,status='inferred' if iscop else 'reported',basis='Six-cycle endpoint read from Figure 1c–d; identification with the textual saturation state is contextual. The body does not state its cycle count.' if iscop else 'Nine total impregnation–precipitation cycles, including the first cycle.')},desc='Each cycle repeats impregnation, water rinsing, evacuation and H2S admission; it is not nine or six additional cycles. '+('The sixth-cycle plot endpoint is contextually associated with saturation; no numerical cycle count is stated in the body or a separate kinetic table.' if iscop else 'Saturation is reported after nine cycles. No final anneal, drying or isolation is supplied.'),end='Film saturation')
 P(r,'first-cycle',('Copolymer' if iscop else 'CTAB')+' host after one impregnation–precipitation cycle',scope,st='first-cds-film',explicit=True)
 p=P(r,'saturated',('Copolymer' if iscop else 'CTAB')+' host at saturation',scope,st='saturated-film',explicit=True);p['morphology']=F('CdS nanoparticles confined within an ordered mesoporous silica thin film',scope)
 for sid,size in [('first-cycle',first),('saturated',last)]:M(r,sid+'-diameter',sid,'gap_size_derived_average_cds_diameter',size,'nm',scope,tech='UV–visible absorption and cited gap–size correlation',status='author_derived',conditions='Source endpoint values derived using reference 35; no digitization, particle histogram, uncertainty or physical-batch identifier.')
 M(r,'saturation-cycles','saturated','figure_endpoint_impregnation_count' if iscop else 'impregnation_precipitation_cycles_to_saturation',cycles,'cycles',scope,status='inferred' if iscop else 'reported',conditions='Six is read from the terminal Figure 1c–d position. Association with the textual 5.8 nm saturation state is contextual; the body does not provide a numeric cycle count.' if iscop else 'Explicit text and Figure 1')
 T(r,'template-scope','saturated','host_template_scope','Unknown triblock copolymer; highly ordered 3D structure with larger spherical pores. Preparation is reference 37, listed only as to be published.' if iscop else 'CTAB-templated silica prepared by the separately reported sol–gel and calcination route.',scope)
 if iscop:
  T(r,'exciton-loss','saturated','absorption_exciton_feature_evolution','Excitonic transitions are no longer present after the second impregnation; absorption is red-shifted relative to the CTAB-host series.',scope)
  M(r,'weak-confinement-size','saturated','author_weak_confinement_size_threshold',None,'nm',E(2,'Copolymer absorption interpretation'),minimum=5,minimum_exclusive=True,conditions='Author general interpretation citing reference 35; not a measured size for each intermediate cycle.')
  r['quality']['missing_fields']+=['Triblock copolymer identity, concentration, host preparation and separately specified copolymer loading conditions are absent; reference 37 is unpublished in this article.']
 else:
  T(r,'color-sequence','first-cycle','reported_visual_color_sequence','Cd2+-impregnated film is colorless; first H2S exposure gives light yellow, with progressively stronger yellow in subsequent cycles.',E(2,'Visual and SIMS observations'))
  T(r,'narrow-size-inference','saturated','author_size_distribution_inference','Excitonic absorption features suggest a narrow size distribution; no numerical width or direct histogram is supplied.',UV,status='author_derived')
  p['phase']=F('Some saturated-film CdS clusters exhibit 111 fringes assigned to a blende-type structure',TEM,note='Qualitative local HRTEM assignment. No refined unit cell, atomic coordinates or whole-film phase fraction; the mesoscopic hexagonal lattice is a separate object.')
 link(r,'cadmium-stock','Impregnation solution','Upstream stock recipe; missing final concentration retained.')
 link(r,'uv-visible','Size and absorption evidence','Stage-specific optical observations and figure scopes.')
 link(r,'ctab-silica-host' if not iscop else 'literature-context','Host preparation or cited-method limit','CTAB preparation is explicit; copolymer preparation remains unavailable.')
 records.append(r)

r=base('uv-visible','Absorption evolution and optical size inference','procedure','UV–visible spectroscopy and published gap–size correlation')
r['materials']=[C('ctab-loaded','specimen','characterization'),C('copolymer-loaded','specimen','characterization')]
add(r,'acquire','uv_visible_acquisition','Acquire the film absorption series after each cycle',['ctab-loaded','copolymer-loaded'],'absorption-series',UV,stage='characterization',kind='analysis_data',desc='Two separate host series, not mixed specimens. Spectrometer model, optical path, acquisition temperature, baseline procedure and uncertainties are not specified. Original Figure 1 preserves the curves; no tabulated raw spectrum is fabricated.')
add(r,'convert','optical_size_conversion','Infer average CdS size using the cited gap–size curves',['absorption-series'],'optical-size-series',UV,stage='characterization',kind='analysis_data',desc='Reference 35: Wang and Herron, Physical Review B 1990, 42, 7253. The paper supplies endpoint sizes and plotted intermediate values, but no numerical conversion equation or calibrated coefficient set.')
P(r,'ctab-series','Figure 1a–b: CTAB-host absorption and size series',UV)
P(r,'copolymer-series','Figure 1c–d: copolymer-host absorption and size series',UV)
for s in ['ctab-series','copolymer-series']:
 M(r,s+'-spectral-range',s,'figure1_displayed_wavelength_range',None,'nm',E(3,'Figure 1a and c axes'),minimum=300,maximum=600,conditions='Displayed plot extent, not an asserted instrument scan range.')
 M(r,s+'-absorbance-range',s,'figure1_displayed_absorbance_range',None,'dimensionless',E(3,'Figure 1a and c axes'),minimum=0,maximum=.5,conditions='Displayed plot extent; some curves extend above the plotting window.')
T(r,'ctab-traces','ctab-series','figure1_absorption_trace_labels','Calcined film and cycles 1, 2, 3, 4, 5, 7 and 9 are labeled. No cycle-6 or cycle-8 spectrum is separately labeled.',E(3,'Figure 1a'))
T(r,'ctab-size-points','ctab-series','figure1_size_plot_scope','Size markers appear at cycles 0, 1, 2, 3, 4 and 9. The zero-cycle point is a plotting origin; it does not establish a measured 0 nm CdS particle. Intermediate marker coordinates are not digitized as exact values.',E(3,'Figure 1b'))
T(r,'copolymer-traces','copolymer-series','figure1_absorption_trace_labels','Calcined film and cycles 1, 2, 3, 4 and 6 are labeled; no separately labeled cycle-5 spectrum.',E(3,'Figure 1c'))
T(r,'copolymer-size-points','copolymer-series','figure1_size_plot_scope','Size markers appear at cycles 0, 1, 2, 3 and 6. Only first-cycle 3.3 nm and saturation 5.8 nm are stated in the prose; no exact intermediate data are invented.',E(3,'Figure 1d'))
T(r,'host-comparison','copolymer-series','host_dependent_absorption_comparison','Larger-pore copolymer films give larger CdS sizes and absorption edges shifted to longer wavelengths than CTAB films; the authors attribute this to pore-constrained growth.',UV,status='author_derived')
link(r,'ctab-cds-loading','CTAB loading route','2.2 to 3.6 nm endpoint outcomes.')
link(r,'copolymer-cds-loading','Copolymer loading route','3.3 to 5.8 nm endpoint outcomes; host preparation not reproduced.')
records.append(r)

r=base('xrd','Mesostructural diffraction during CdS filling','procedure','Low-angle X-ray diffraction in Bragg–Brentano geometry')
r['materials']=[C('ctab-host','specimen','characterization'),C('cadmium-adsorbed-film','specimen','characterization'),C('ctab-loaded','specimen','characterization')]
add(r,'align','textured_film_geometry','Place the textured film in Bragg–Brentano geometry',['ctab-host','cadmium-adsorbed-film','ctab-loaded'],'xrd-specimens',X,stage='characterization',kind='sample_set',desc='Separate initial, Cd-adsorbed and cycle-treated films or states; not a mixture. The c-axis is normal to the film. No sample area or mounting details are reported.')
add(r,'acquire','low_angle_xrd','Acquire low-angle diffraction patterns',['xrd-specimens'],'xrd-data',X,stage='characterization',kind='analysis_data',desc='X’Pert Philips diffractometer, Cu Kα radiation. The mesostructural 0002 reflection and its harmonic dominate due to texture; no CdS atomic diffraction pattern is reported.')
for i,label in [('calcined','Initial calcined CTAB host'),('cadmium-adsorbed','Before the first H2S treatment'),('first-h2s','After the first H2S treatment'),('saturated','Saturated CdS/CTAB silica film')]:P(r,i,label,X,formula='SiO2' if i=='calcined' else None if i=='cadmium-adsorbed' else FORMULA,notes=['No physical-batch identifiers; source treatment-state scope only. Before H2S, cadmium is adsorbed and CdS is not yet present.'])
for i,val in [('calcined',6.9),('cadmium-adsorbed',6.8),('saturated',7.2)]:M(r,i+'-meso-c',i,'xrd_mesoscopic_c_parameter',val,'nm',X,tech='X-ray diffraction',conditions='Mesoscopic silica/CdS array parameter, not an atomic CdS unit-cell parameter.')
M(r,'adsorbed-relative-intensity','cadmium-adsorbed','0002_intensity_relative_to_calcined_host',.5,'ratio',X,conditions='Prose says twice less intense after first Cd adsorption; approximate qualitative comparison, not a fitted peak integral.',approximate=True)
T(r,'initial-shift','cadmium-adsorbed','0002_peak_shift','Shifts toward larger 2θ after Cd adsorption, with c decreasing 6.9 to 6.8 nm; possible high-pH silica-wall condensation.',X,status='author_derived')
T(r,'contrast-inversion','first-h2s','0002_intensity_evolution','Intensity decreases dramatically after first H2S, then rises progressively with further CdS filling. Authors assign this to inversion from silica–air to silica–CdS scattering contrast, not loss and recovery of order.',X,status='author_derived')
T(r,'peak-width','saturated','0002_peak_width_evolution','No significant peak-width change is reported; no numerical FWHM, domain-size fit or uncertainty is supplied. Constant ordered-domain size and homogeneous growth are author inferences.',X,status='author_derived')
T(r,'growth-shift','saturated','0002_peak_shift','Progressive shift toward lower 2θ during filling, with c reaching 7.2 nm; attributed to slight pore deformation upon filling.',X,status='author_derived')
M(r,'figure-range','saturated','figure2_displayed_two_theta_range',None,'degree',E(3,'Figure 2 axis'),minimum=2.2,maximum=2.9,conditions='Plot range, not a separately stated scan acquisition range.')
M(r,'calcined-scale','calcined','figure2_intensity_display_multiplier',.5,'ratio',E(3,'Figure 2 label'))
M(r,'first-cycle-scale','first-h2s','figure2_intensity_display_multiplier',5,'ratio',E(3,'Figure 2 label'))
T(r,'trace-labels','saturated','figure2_trace_labels','Calcined film, Cd2+-impregnated film, and cycles 1, 2, 3, 4, 5, 7 and 9 are labeled. Intensity axis is arbitrary units; no raw numerical intensities supplied.',E(3,'Figure 2'))
r['quality']['conflicts']=['Saturated-film XRD discussion gives mesoscopic c = 7.2 nm, while saturated-film HRTEM/power-spectrum discussion gives approximately c = 6.8 nm. The paper does not resolve the discrepancy; do not collapse them into a single fitted parameter.']
records.append(r)

r=base('hrtem','HRTEM and Fourier power of the CdS mesoscopic lattice','procedure','Cross-sectional high-resolution TEM and image Fourier power')
r['materials']=[C('ctab-loaded','specimen','characterization'),C('ctab-host','comparison_specimen','characterization')]
add(r,'section','cross_section_specimen','Prepare or select cross sections of filled and empty films',['ctab-loaded','ctab-host'],'cross-sections',TEM,stage='characterization',kind='sample_set',desc='Cross sections are reported, but cutting, thinning, grid, embedding and thickness details are not provided. Empty and filled films remain separate comparators.')
add(r,'image','high_resolution_tem','Image the cross sections under slight underfocus',['cross-sections'],'hrtem-data',TEM,{'acceleration_voltage':Q(200,'kV',TEM),'point_resolution':Q(.18,'nm',TEM)},stage='characterization',kind='analysis_data',desc='Topcon 002B microscope. Slight underfocus enhances particle/matrix contrast; numerical defocus is absent. Comparison assumes equal specimen thickness and experimental conditions and states identical objective-lens underfocus.')
add(r,'fourier','image_fourier_power','Calculate the image power spectrum',['hrtem-data'],'power-spectrum',TEM,stage='characterization',kind='analysis_data',desc='Figure 3d is the squared modulus of the Fourier transform of Figure 3a, not selected-area electron diffraction and not a separately acquired atomic diffraction pattern.')
for i,label,f in [('filled','Figure 3a and enlarged 3c: saturated CTAB-host film',FORMULA),('empty','Figure 3b: calcined film before impregnation','SiO2'),('power','Figure 3d: Fourier power of Figure 3a',FORMULA)]:P(r,i,label,TEM,f)
M(r,'filled-scale-bar','filled','figure3a_scale_bar_length',30,'nm',E(4,'Figure 3a'))
M(r,'empty-scale-bar','empty','figure3b_scale_bar_length',30,'nm',E(4,'Figure 3b'))
M(r,'enlargement-scale-bar','filled','figure3c_scale_bar_length',20,'nm',E(4,'Figure 3c'))
T(r,'contrast','filled','filled_empty_image_contrast','Filled CdS particles appear as dark dots on lighter background; empty pores appear light on darker silica. Authors compare this inversion with XRD contrast inversion.',TEM)
T(r,'contrast-assumptions','filled','contrast_interpretation_assumptions','HRTEM contrast also depends on zone-axis orientation, specimen thickness, focus and accelerating voltage. Filled/empty contrast interpretation assumes the same thickness and experimental conditions, including identical underfocus.',TEM)
T(r,'filling','filled','pore_occupancy_observation','Homogeneous particle filling and preserved periodic order are observed; a few white points near the film/substrate interface are interpreted as remaining empty pores. The prose also uses totally filled, which must not override these exceptions or the independent approximately 85% volume-filling estimate.',TEM,status='author_derived')
T(r,'atomic-fringes','filled','local_atomic_structure_assignment','Some clusters show 111 fringes of blende-type CdS; cited reference 39 supports this size-regime assignment. No atomic lattice constant, fringe distance, phase fraction or refined coordinates are reported.',TEM)
T(r,'orientation-contrast','filled','particle_orientation_contrast','Darkest particles are attributed to zone-axis, strong-Bragg orientations; differing particle orientations affect contrast.',TEM,status='author_derived')
T(r,'projection','filled','mesoscopic_projection','Projected 3D particle array with slight misorientation of the mesostructural [11−20] direction relative to the electron beam; superposition accounts for continuous gray contrast between some particles.',TEM,status='author_derived')
T(r,'power-definition','power','image_power_definition','Power spectrum = |Fourier transform|² of the cross-sectional image; Figure 3d is not SAED.',TEM)
T(r,'meso-space-group','power','mesoscopic_space_group','P6₃/mmc',TEM,conditions='Mesoscopic pore/particle array, not atomic CdS space group.')
M(r,'meso-a','power','image_derived_mesoscopic_a_parameter',6,'nm',TEM,approximate=True,status='author_derived')
M(r,'meso-c','power','image_derived_mesoscopic_c_parameter',6.8,'nm',TEM,approximate=True,status='author_derived')
M(r,'meso-c-a','power','image_derived_mesoscopic_c_over_a',1.13,'ratio',TEM,status='author_derived')
T(r,'power-labels','power','figure3d_index_labels','0002, 01−11 and 01−10 are indexed in the image power spectrum.',E(4,'Figure 3d'),conditions='Four-index mesoscopic hexagonal labels. Overbars are retained in plain-text minus notation.')
r['quality']['conflicts']=['HRTEM discussion gives mesoscopic c approximately 6.8 nm for the filled-film image, versus XRD saturated-film c = 7.2 nm. No resolution is supplied.','The prose says totally filled but explicitly notes a few empty pores; the separate volume model yields about 85% pore filling. These are distinct observation/model scopes, not a 100% occupancy measurement.']
records.append(r)

r=base('sims','Cadmium depth-distribution evidence','procedure','Secondary ion mass spectrometry')
r['materials']=[C('ctab-loaded','specimen','characterization'),C('cadmium-adsorbed-film','specimen','characterization')]
se=E(2,'SIMS results')+E(5,'Acknowledgment of SIMS analyses')
add(r,'profile','sims_depth_profile','Measure cadmium distribution versus film depth',['ctab-loaded','cadmium-adsorbed-film'],'sims-data',se,stage='characterization',kind='analysis_data',desc='Two treatment states: Cd2+-impregnated before sulfiding and saturated CdS film. Instrument, primary ions, sputter conditions, depth calibration and raw profiles are not given. This is not an EDS dataset.')
for i,label in [('cadmium-adsorbed','Cadmium-impregnated film before H2S'),('saturated','CdS-saturated film')]:
 P(r,i,label,se,formula=None if i=='cadmium-adsorbed' else FORMULA)
 T(r,i+'-depth',i,'cadmium_depth_distribution','Homogeneous cadmium distribution as a function of depth is reported; no numerical concentration profile or uncertainty is supplied.',se,tech='SIMS')
records.append(r)

r=base('pl-silicon','Silicon-supported film preparation and photoluminescence','procedure','Stage-resolved photoluminescence and excitation spectroscopy')
r['materials']=[C('silicon','substrate','characterization'),C('mesoporous-film','porous_host','characterization'),C('cadmium-stock','precursor_stock','characterization'),C('water','solvent','characterization'),C('h2s','chalcogen_precursor','characterization')]
add(r,'deposit','silicon_supported_film','Deposit a mesoporous film on a silicon wafer',['mesoporous-film','silicon'],'silicon-film',PL,stage='characterization',desc='Silicon replaces luminescent Pyrex to avoid substrate interference. This paragraph does not separately specify the template, spin speed, thickness or host processing; do not silently copy all Pyrex-film parameters.')
add(r,'first-cycle','initial_loading_cycle','Obtain the first H2S-treated film',['silicon-film','cadmium-stock','water','h2s'],'first-h2s-film',PL+CD,stage='characterization',desc='The common adsorption/rinse/evacuation/H2S sequence supplies context, but no separate silicon-specimen charges or exposure times are reported.')
add(r,'measure-first','photoluminescence_acquisition','Record emission and excitation after the first H2S treatment',['first-h2s-film'],'first-pl-data',PL,stage='characterization',kind='analysis_data',env='Room temperature; numerical temperature unspecified',desc='Hitachi F-4500 fluorescence spectrophotometer. Exact excitation wavelength, monitored emission wavelength, slits, corrections and absolute quantum yield are not supplied.')
add(r,'reimpregnate','cadmium_readorption','Perform the following cadmium impregnation',['first-h2s-film','cadmium-stock'],'next-cd-film',PL,stage='characterization',desc='This state follows first H2S and precedes second H2S. It is not a completed second CdS-growth cycle; no added CdS size is assigned.',depends=['first-cycle'])
add(r,'measure-cd','photoluminescence_acquisition','Record emission and excitation after the cadmium impregnation',['next-cd-film'],'cadmium-pl-data',PL,stage='characterization',kind='analysis_data',env='Room temperature; numerical temperature unspecified',desc='Body text and Figure 4 caption disagree on upper/lower curve assignments; retain both source statements.')
add(r,'later-cycle','further_loading_cycles','Continue to second H2S treatment and subsequent impregnation stages',['next-cd-film','h2s','cadmium-stock','water'],'later-film',PL,stage='characterization',desc='Later stage count and individual spectra are not supplied. Do not impose the CTAB nine-cycle saturation endpoint on this optical specimen.',depends=['reimpregnate'])
add(r,'measure-later','photoluminescence_observation','Assess later-stage luminescence',['later-film'],'later-pl-data',PL,stage='characterization',kind='analysis_data',desc='Later emission decrease and bound-exciton disappearance are described in prose; no separate later-stage graph or numerical intensity is reproduced.')
for i,label in [('first-h2s','Silicon film after first H2S treatment'),('next-cd','Same process sequence after the next Cd impregnation'),('later-cycles','Second H2S treatment and later impregnations'),('figure4','Original Figure 4 display, stage-to-curve conflict unresolved')]:P(r,i,label,PL,notes=['The paper does not give physical-batch identifiers or a verified join to the Pyrex absorption/TEM specimens.'])
M(r,'first-surface-emission','first-h2s','surface_defect_emission_band_center',640,'nm',PL,approximate=True,tech='Photoluminescence',conditions='Body text reports a weak broad band around 640 nm after first H2S. Caption instead assigns the upper curves to this stage.')
M(r,'next-surface-emission','next-cd','surface_defect_emission_band_center',640,'nm',PL,tech='Photoluminescence',conditions='Body text reports enhancement after the following Cd impregnation; exact peak or calibrated intensity not tabulated.')
M(r,'bound-exciton','next-cd','bound_exciton_emission_band_wavelength',450,'nm',PL,tech='Photoluminescence',conditions='Sharp band assigned in body text to direct bound-exciton recombination after the next Cd impregnation. Curve positioning in Figure 4 caption conflicts with this sequence.')
T(r,'surface-band-mechanism','next-cd','author_surface_emission_interpretation','Enhancement is attributed to sulfur vacancies at the nanoparticle surface, citing reference 40.',PL,status='author_derived')
T(r,'passivation-mechanism','next-cd','author_bound_exciton_interpretation','Ammonia or hydroxyl complexation may passivate the surface, allowing bound-exciton emission; this is a proposed explanation, not a measured ligand structure.',PL,status='author_derived')
T(r,'later-emission','later-cycles','reported_luminescence_evolution','After second H2S and further impregnations, emission decreases and the bound-exciton signal disappears.',PL)
T(r,'later-mechanism','later-cycles','author_quenching_interpretation','Growth may reduce surface accessibility and increase particle/silica-wall interactions unfavorable to direct exciton recombination; the discussion cites reference 42.',PL,status='author_derived')
T(r,'figure-curve-style','figure4','figure4_curve_styles','Dashed lines are excitation spectra and solid lines are luminescence spectra; arbitrary intensity units, no raw numerical data.',E(5,'Figure 4 caption'))
T(r,'figure-stage-label','figure4','figure4_caption_stage_assignment','Caption: upper curves after first H2S; lower curves after the following Cd impregnation. This conflicts with the body’s described enhancement and appearance of the 450 nm peak after the Cd treatment.',E(5,'Figure 4 caption and body'))
M(r,'figure-wavelength-range','figure4','figure4_displayed_wavelength_range',None,'nm',E(5,'Figure 4 axis'),minimum=300,maximum=700,conditions='Displayed plot extent, not an instrument scan limit.')
T(r,'measurement-temperature','figure4','acquisition_temperature','Room temperature; no numerical value supplied.',E(5,'Figure 4 caption'))
r['quality']['conflicts']=['Figure 4 caption assigns upper curves to first H2S and lower curves to next Cd impregnation, while body text describes weak first emission and stronger 640 nm plus new 450 nm emission after Cd. Preserve both; no silent curve relabeling.']
r['quality']['missing_fields']+=['The silicon optical specimen’s host template, numerical measurement temperature, excitation wavelength, emission monitoring wavelength, exact intensities, quantum yield and batch link to the Pyrex specimens are unreported.']
records.append(r)

r=base('loading-fraction','CdS volume fraction and pore-filling estimate','procedure','Absorbance calibration and mesopore-volume comparison')
r['materials']=[C('ctab-loaded','specimen','characterization'),C('cds-colloid','calibration_reference','characterization')]
add(r,'compare','absorbance_reference_comparison','Compare saturated-film absorbance with a CdS colloid reference',['ctab-loaded','cds-colloid'],'volume-calibration',VOL,{'reference_mean_diameter':Q(3.5,'nm',VOL)},stage='characterization',kind='analysis_data',desc='Reference maximum absorbance comes from a same-average-size CdS colloid. Reverse-micelle preparation is cited in note 38 to reference 42, without reagents or a complete recipe here. Concentration, path-length normalization and full conversion equation are absent.')
add(r,'estimate','volume_fraction_ratio','Estimate CdS loading and mesopore filling',['volume-calibration'],'filling-estimate',VOL,stage='characterization',kind='analysis_data',desc='Authors compare inferred CdS volume fraction with mesopore volume fraction calculated from crystallographic data. Preserve the reported approximate 85% value; no new exact 13/15 calculation replaces it.')
P(r,'saturated','Saturated CTAB-host film, optical filling model',VOL)
P(r,'reference','CdS colloid used only for optical calibration',VOL,formula='CdS')
M(r,'reference-size','reference','reference_colloid_average_diameter',3.5,'nm',VOL,conditions='Source calls this the same average size as the saturated-film particles, whereas the UV–visible growth section gives 3.6 nm for saturation. Distinct reported contexts retained.')
M(r,'cds-volume','saturated','cds_volume_fraction',13,'%',VOL,status='author_derived',tech='Absorbance-reference comparison')
M(r,'pore-volume','saturated','mesopore_volume_fraction',15,'%',VOL,status='author_derived',tech='Crystallographic mesopore model')
M(r,'pores-per-cell','saturated','mesopores_per_mesoscopic_hexagonal_unit_cell',2,'count',VOL,conditions='Model input; not two atoms or CdS formula units per atomic cell.')
M(r,'pore-filling','saturated','mesopore_volume_filling_fraction',85,'%',VOL,approximate=True,status='author_derived',tech='Comparison of CdS and mesopore volume fractions',conditions='Author-rounded estimate; no uncertainty or full calibration data supplied.')
T(r,'reference-method','reference','reference_colloid_preparation_scope','Reverse-micelle technique is named in reference note 38, citing reference 42; chemicals, concentrations and operations are not reproduced. This is a calibration comparator, not a newly complete synthesis route.',VOL)
r['quality']['conflicts']=['Optical growth endpoints report 3.6 nm at CTAB saturation, while the volume-calibration paragraph uses a 3.5 nm same-average-size colloid comparison. These rounded/contextual values are retained separately.','About 85% pore filling is a volume model, not proof that every pore is full; HRTEM notes a few empty pores despite also using totally filled wording.']
records.append(r)

r=base('chemical-intuition','Chemical intuition and evidence-limited mechanism')
e=E(2,'General chemical strategy and pH window')
P(r,'strategy','Author mechanism for pore filling',e)
M(r,'ph-window','strategy','proposed_adsorption_solution_pH_window',None,'pH',e,minimum=9,maximum=10,conditions='General design window; actual stock target is pH 9.5.')
M(r,'adsorption-threshold','strategy','cadmium_adsorption_optimal_pH_threshold',None,'pH',e,minimum=9,minimum_exclusive=True,conditions='Author strategy statement, citing silica surface chemistry; no adsorption-isotherm dataset reproduced.')
M(r,'silica-solubility','strategy','silica_partial_solubility_pH_threshold',None,'pH',e,minimum=10,minimum_exclusive=True,conditions='Author warning for the chemical design window; no measured dissolution-rate curve.')
T(r,'uniform-adsorption','strategy','cation_adsorption_rationale','Well-controlled aqueous pH and soluble cationic species promote homogeneous adsorption on the silica pore walls; complexants avoid hydroxide precipitation.',e,status='author_derived')
T(r,'cadmium-binding','strategy','surface_binding_rationale','Strong Cd interactions with Si–O− groups retain adsorbed ions during water rinsing; no significant leaching is reported qualitatively, without a numerical limit.',e)
T(r,'rinse-rationale','strategy','water_rinse_rationale','Rinsing removes excess reagents and cations at the film–air interface, reducing unwanted surface deposition.',e)
T(r,'gas-rationale','strategy','gaseous_precipitation_rationale','H2S gas rapidly diffuses into the porous film and precipitates particles throughout; authors propose this avoids isolated domains blocked by nanoparticles and heterogeneous filling.',e,status='author_derived')
T(r,'site-regeneration','strategy','repeated_cycle_rationale','CdS precipitation regenerates pore-wall silanol sites for another cadmium adsorption step; several cycles are needed for saturation.',e,status='author_derived')
T(r,'order-rationale','strategy','host_order_rationale','Highly ordered, textured and accessible mesoporous films constrain particle size and spatial organization through their thickness. Surviving repeated cycles is essential to reach saturation.',E(2,'Host strategy')+E(5,'Conclusion'),status='author_derived')
T(r,'contrast-model','strategy','xrd_contrast_rationale','Cadmium adsorption raises pore electron density and reduces silica/air contrast; CdS formation eventually makes pore scattering stronger than silica because Cd and S scatter more strongly than Si and O. Intensity inversion does not imply structural collapse.',X,status='author_derived')
T(r,'template-tuning','strategy','particle_size_tuning_rationale','The larger-pore copolymer comparison supports tuning CdS size by host selection; host-specific absolute preparation parameters are not disclosed.',UV,status='author_derived')
T(r,'mesoscopic-v-atomic','strategy','structure_scale_distinction','The 3D hexagonal P6₃/mmc assignment describes the pore/particle array at nanometer periodicities. Blende-type 111 fringes describe atomic CdS inside individual pores. No periodic atomic model spanning the film follows from these claims.',TEM)
T(r,'outlook','strategy','author_future_outlook','The approach could extend to other sulfides or selenides if their cations can be anchored to silica. This is prospective, not evidence of additional synthesized materials.',E(5,'Conclusion'))
records.append(r)

r=base('literature-context','Cited methods, study scope and unresolved evidence')
le=E(1,'Introduction')+E(5,'References')+E(6,'References')
P(r,'context','Bibliographic and study-scope context',le)
T(r,'complete-source','context','inspected_source_scope','All six supplied main pages, four figures, captions, result discussions, conclusion and 43 references/notes were inspected. No SI, raw spectra, atom-coordinate files or cited full-text papers were added.',le)
T(r,'prior-host','context','cited_host_preparation','Reference 29: Besson et al., Journal of Materials Chemistry 2000, 10, 1331; reference 30: Besson et al., Journal of Physical Chemistry B 2000, 104(51), 12095. Current paper provides a partial host recipe and compares the mesoscopic image power with the earlier empty film.',HOST+TEM+E(5,'References 29–30'))
T(r,'copolymer-reference','context','copolymer_preparation_availability','Reference 37 is listed as Besson et al., to be published. No polymer identity, composition, host synthesis parameters or full citation is available in the supplied article.',E(2,'Copolymer comparison')+E(5,'Reference 37'))
T(r,'gap-size-reference','context','size_conversion_reference','Reference 35: Wang and Herron, Physical Review B 1990, 42, 7253. Current optical particle sizes are derived using its gap–size correlation; no conversion coefficients or uncertainty propagation are printed here.',UV+E(5,'Reference 35'))
T(r,'prior-single-cycle','context','prior_method_comparison','References 32–34 concern CdS in MCM-41 powders using a single impregnation step. The authors contrast those protocols with repeated filling of accessible ordered films; the cited powder recipes are not reproduced or newly curated.',E(2,'Repeated precipitation strategy')+E(5,'References 32–34 and Conclusion'))
T(r,'reference-colloid','context','cited_calibration_preparation','Note 38 identifies a reverse-micelle CdS colloid and cites reference 42 (Gacoin et al., MRS Proceedings 1996, 435, 643). It supplies neither an independent precursor list nor an executable synthesis.',VOL)
T(r,'blende-reference','context','atomic_assignment_reference','Reference 39: Ricolleau et al., European Physical Journal D 1999, 9, 565, supports the blende-type assignment for this CdS size regime. It is not a coordinate-file source inspected in this review.',TEM+E(6,'Reference 39'))
T(r,'luminescence-references','context','surface_emission_references','Surface vacancies and passivation explanations cite reference 40 (Wang et al., Journal of Chemical Physics 1990, 92(11), 6927), reference 41 (Spahnel et al., JACS 1987, 109(19), 5649), and particle–matrix effects cite reference 42. These are interpretive references, not additional measurements made here.',PL+E(6,'References 40–42'))
T(r,'historical-context','context','historical_material_scope','The introduction discusses prior SiGe, silicon, silver, magnetic particles, carbon/platinum replicas and MCM/SBA host work to motivate ordered coatings. Those cited materials are not synthesized or entered as new routes by this paper.',E(1,'Introduction')+E(2,'Introduction continuation'))
M(r,'historical-nano-scale','context','introductory_nanocrystal_size_scale',None,'nm',E(1,'Introduction'),maximum=10,maximum_exclusive=True,conditions='General introductory scale for size-dependent properties; not the measured diameter of a present sample.')
M(r,'historical-pore-range','context','cited_mesoporous_material_pore_size_range',None,'nm',E(1,'Introduction'),minimum=2,maximum=30,conditions='Historical literature range, not a size distribution of the current CTAB or copolymer host.')
T(r,'applications','context','author_motivation_and_outlook','Ordered nanoparticle films are motivated by optical and electronic applications and studying collective effects. Large-area order is claimed relative to small self-organized colloidal domains, but coated area and ordering correlation length are not quantified.',E(1,'Introduction')+E(5,'Conclusion'))
records.append(r)

if __name__=='__main__':
 out=B/'canonical-drafts';out.mkdir(exist_ok=True);errors=[]
 for r in records:
  errors+=validate_record(r)
  (out/(r['record_id']+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report={'status':'failed' if errors else 'passed','record_count':len(records),'operation_count':sum(len(r['operations']) for r in records),'measurement_count':sum(len(r['measurements']) for r in records),'material_slots':sum(len(r['materials']) for r in records),'source_read_pages':6,'source_visual_pages':6,'errors':errors}
 (B/'records-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (B/'canonical-material-identities.json').write_text(json.dumps({'source_id':SID,'source_group':SID,'materials':[{'id':i,'name':n,'formula':f} for i,(n,f,e) in CHEM.items()],'record_material_ids':{r['record_id']:[m['id'] for m in r['materials']] for r in records}},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 src=json.loads((B/'source-manifest.json').read_text(encoding='utf-8-sig'))
 (B/'canonical-record-manifest.json').write_text(json.dumps({'source_id':SID,'source_group':SID,'source_sha256':src.get('sha256'),'main_pages_read_and_visually_inspected':6,'supporting_information':'No SI supplied or independently matched; existence/availability unresolved.','records':[{'id':r['record_id'],'record_type':r['record_type'],'sha256':hashlib.sha256((out/(r['record_id']+'.json')).read_bytes()).hexdigest(),'operation_ids':[o['id'] for o in r['operations']],'sample_ids':[p['sample_id'] for p in r['products']],'measurements':len(r['measurements'])} for r in records]},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(report))
 if errors:raise SystemExit(1)
