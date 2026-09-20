"""Dantas et al. 2002: complete supplied five-page source, privately curated.
Reported sizes remain ambiguous where the source changes between size, radius and height.
"""
from pathlib import Path
from copy import deepcopy
import sys,json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,ev,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record
SID='dantas2002';PRE='dantas-2002-';FORMULA='PbS/glass'
SRC=source(SID,'10.1021/jp0208743','Anti-Stokes Photoluminescence in Nanocrystal Quantum Dots','Noelio Oliveira Dantas; Fanyao Qu; R. S. Silva; Paulo César Morais',2002,si='No matching SI supplied or independently verified. No SI declaration observed in the supplied five-page main article.')
SRC['main_status']='All five main pages read as text and original page images, including all seven figures, captions and 21 references. Independent audit pending.'
def E(p,s):return ev(SID,f'Main PDF p. {p}, printed p. {7452+p}, {s}')
HOST=E(1,'Section 2, powder mixture and fusion')+E(2,'Section 2, cooling and stress relief');AN=E(2,'Section 2, six sample labels and annealing durations');OA=E(2,'Figures 1–2 and optical absorption discussion');MODEL=E(2,'Numerical energy-level calculations and optical sizes')+E(3,'Figure 3 and comparison');AFM=E(3,'AFM analysis')+E(4,'Figure 4');PL=E(2,'Optical setup')+E(3,'ASPL observations')+E(5,'Figures 5–7');POWER=E(3,'Excitation-power dependence')+E(4,'Two-step model discussion')+E(5,'Figure 6');MECH=E(3,'Microscopic mechanism discussion')+E(4,'Model continuation')+E(5,'Raman interpretation and conclusion')
def Q(v=None,u='',e=AN,**kw):return qty(v,u,deepcopy(e),**kw)
def F(v=None,e=AN,**kw):return fact(v,deepcopy(e),**kw)
CHEM={
 'silica':('Silicon dioxide; source glass former','SiO2',HOST),
 'sodium-carbonate':('Sodium carbonate; source melting-point modifier','Na2CO3',HOST),
 'zinc-oxide':('Zinc oxide; source intermediate oxide','ZnO',HOST),
 'alumina':('Aluminum oxide; listed glass-mixture component','Al2O3',HOST),
 'lead-dioxide':('Lead dioxide; literal PbO2 printed in the source','PbO2',HOST),
 'boron-oxide':('Boron oxide; listed glass-mixture component','B2O3',HOST),
 'sulfur-source':('Sulfur dopant source; chemical form, amount and introduction stage unspecified',None,HOST),
 'aluminum-crucible':('Aluminum crucible, literal source wording; vessel identity unresolved','Al',HOST),
 'glass-host':('Sulfur-doped multicomponent glass precursor containing lead; composition ratios unknown',None,HOST+AN),
 **{k+'-specimen':('Sample '+k.upper().replace('SG','SG').replace('AFM','AFM')+': PbS quantum dots embedded in multicomponent glass',FORMULA,AN) for k in ['sg1','sg2','sg3','sg4','afm1','afm2']}
}
def C(i,role,stage='synthesis',notes=None):
 n,f,e=CHEM[i];return material(i,n,f,role,stage,deepcopy(e),notes=notes or [])
def base(k,title,kind='observation',method='Source-scoped characterization and interpretation'):
 r=record(PRE+k,'Dantas et al. (2002) · '+title,FORMULA,'Lead-sulfide quantum dots embedded in a multicomponent glass',method,deepcopy(SRC),'Complete supplied main PDF pp. 1–5',kind)
 r['schema_version']='1.3.0';r['collection']='reviewed_literature';r['material'].update(elements=['Pb','S','Si','O','Na','Zn','Al','B'],components=['PbS'],architecture='composite')
 r['lineage'].update(source_group=SID,recipe_family='dantas2002-pbs-glass')
 r['intended_target']['composition']=F(FORMULA,E(1,'Abstract'),note='Composite-system descriptor, not a stoichiometric single crystal or pure silica host.')
 r['intended_target']['host']=F('Sulfur-doped glass prepared from SiO2–Na2CO3–ZnO–Al2O3–PbO2–B2O3; proportions unreported',HOST,note='Input mixture identifies source precursors, not measured final glass speciation. PbO2 is retained literally.')
 r['quality'].update(review_status='imported_unreviewed',review_scope='Complete five-page main read and visually inspected. No outside papers or SI downloaded. Independent audits and website integration pending.',missing_fields=['Mixture proportions, absolute charges, sulfur chemical source/loading and addition timing, quantitative purity grades, annealing atmosphere and temperature ramps are not reported.','No current TEM, XRD, SAED, refined atomic lattice, crystal coordinate file, yield, error bars or raw numerical spectra are supplied.','The source alternates between generic QD size, calculated radius and AFM grain height. No universal diameter conversion is justified.'],conflicts=[],requested_tasks=['precursor_selection','partial_protocol'] if kind=='literature_protocol' else [],experimental_outcome='reported_product' if kind=='literature_protocol' else 'not_established')
 r['context_links']=[{'label':'Complete source review','url':'../paper-review.html?id='+SID,'relation':'Original figures, all methods, theory and source limitations.'}]
 return r
def add(r,i,action,label,inputs,out,e,pars=None,stage='synthesis',desc='',env=None,end=None,kind='reaction_batch',depends=None):
 if out:r['material_states'].append(state(out,label+' output',inputs,kind))
 r['operations'].append(operation(i,action,label,deepcopy(e),inputs,[out]if out else [],depends=depends if depends is not None else ([r['operations'][-1]['id']]if r['operations']else []),parameters=pars or {},stage=stage,description=desc,environment=F(env,e),endpoint=F(end,e)))
def P(r,i,label,e,formula=FORMULA,st=None,explicit=False,notes=None):
 p=product(i,formula,deepcopy(e),link='explicit'if explicit else 'general_context',state=st,notes=notes or []);p['source_sample_label']=label;r['products'].append(p);return p
def M(r,i,s,prop,v,u,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,Q(v,u,e,**kw),tech,deepcopy(e),conditions))
def T(r,i,s,prop,v,e,tech='Source-reported observation',conditions='',**kw):r['measurements'].append(measurement(i,s,prop,F(v,e,**kw),tech,deepcopy(e),conditions))
def link(r,k,title,rel):r['context_links'].append({'label':title,'url':'../records/'+PRE+k+'.html','relation':rel})
records=[]
powders=['silica','sodium-carbonate','zinc-oxide','alumina','lead-dioxide','boron-oxide']
r=base('glass-host','Shared sulfur-doped glass precursor preparation','procedure','Powder fusion, rapid cooling and stress-relief annealing')
r['materials']=[C(i,'metal_precursor'if i=='lead-dioxide'else 'host_component','precursor_preparation',notes=['High-purity powder is stated without a supplier or numerical grade; individual charge and mixture ratio are absent.'])for i in powders]+[C('sulfur-source','chalcogen_precursor','precursor_preparation'),C('aluminum-crucible','vessel','precursor_preparation',notes=['Printed as aluminum, not alumina. Do not use vessel Al as an added reagent or silently correct the source.'])]
r['stocks']=[{'id':'precursor-matrix','name':'Shared precursor glass for the six growth anneals','components':[{'material_id':i,'quantities':{}}for i in powders+['sulfur-source']],'concentrations':{'sulfur_loading':Q(u='',e=HOST,qualifier='Dopant form and composition basis are not reported.')},'preparation_operation_ids':['mix','melt','quench','stress-relief'],'scope':'This is a multicomponent solid matrix, not a solution concentration. The sulfur introduction stage is absent; component identities do not establish final oxide speciation.','evidence':deepcopy(HOST)}]
add(r,'mix','powder_mixture_preparation','Prepare the reported high-purity precursor-powder mixture',powders,'powder-mixture',HOST,{'batch_mass':Q(u='g',e=HOST)},stage='precursor_preparation',desc='SiO2, Na2CO3, ZnO, Al2O3, PbO2 and B2O3 are listed. Sulfur doping is reported, but its source and addition timing are unknown; no discrete elemental-sulfur addition is invented.')
add(r,'melt','glass_fusion','Melt the mixture in the source-described crucible',['powder-mixture','aluminum-crucible'],'fused-matrix',HOST,{'temperature':Q(1400,'°C',HOST),'duration':Q(2,'h',HOST)},stage='precursor_preparation',desc='The paper literally says aluminum crucible at 1400 °C. Vessel identity is unresolved; do not silently replace it with alumina. Furnace design and atmosphere are unspecified.')
r['material_states'][-1]['parent_ids']=['powder-mixture'] # Equipment is used, not incorporated as a material ancestor.
add(r,'quench','rapid_cooling','Cool the melt rapidly to room temperature',['fused-matrix'],'cooled-glass',HOST,{'cooling_rate':Q(u='°C/min',e=HOST)},stage='precursor_preparation',end='Room temperature; numeric value not supplied',desc='Cooling is described as fast; the cooling medium, mold, rate, duration and numerical terminal temperature are not reported.')
add(r,'stress-relief','stress_relief_annealing','Anneal the glass to relieve thermal stresses',['cooled-glass'],'stress-relieved-glass',HOST,{'temperature':Q(350,'°C',HOST),'duration':Q(3,'h',HOST)},stage='precursor_preparation',desc='Common preparation before the separate 600 °C growth anneals. No intermediate cooling sequence, ramp or atmosphere is specified.')
P(r,'precursor-glass','Shared sulfur-doped multicomponent glass before growth annealing',HOST,formula=None,st='stress-relieved-glass',explicit=True,notes=['Lead and sulfur precursors are present, but this intermediate is not assigned measured PbS dots, crystalline phase or a molecular formula.'])
T(r,'component-functions','precursor-glass','source_assigned_glass_component_functions','SiO2 acts as glass former, ZnO as intermediate oxide, and Na2CO3 reduces the melting point. Functions of Al2O3 and B2O3 are not explicitly assigned in the paper.',HOST)
T(r,'purity','precursor-glass','precursor_purity','High-purity powders; suppliers, numerical purity and source sulfur formulation are unspecified.',HOST)
r['quality']['conflicts']=['The literal aluminum-crucible wording is retained alongside 1400 °C. The source gives no clarification of whether a different refractory vessel was intended.']
records.append(r)

SAMPLES={'sg1':(1,'SG1'), 'sg2':(3,'SG2'),'sg3':(6,'SG3'),'sg4':(12,'SG4'),'afm1':(5,'AFM1'),'afm2':(30,'AFM2')}
peaks={'sg1':[1.391,2.486,2.691,2.894],'sg2':[1.420,2.200,2.490,2.863]}
optical_sizes={'sg1':24,'sg2':27,'sg3':40}
for key,(hours,label)in SAMPLES.items():
 r=base(key,label+' growth anneal at 600 °C for '+str(hours)+' h','literature_protocol','Thermally induced PbS precipitation and growth in precursor glass')
 r['lineage']['parent_record_id']=PRE+'glass-host'
 r['materials']=[C('glass-host','host_matrix',notes=['Requires the linked shared 1400 °C fusion / fast cooling / 350 °C stress-relief preparation; not a generic off-the-shelf glass.']),C('lead-dioxide','metal_precursor',notes=['Lead precursor in the upstream glass formulation. No fresh PbO2 addition during this anneal is specified; oxidation/reduction pathway is not resolved.']),C('sulfur-source','chalcogen_precursor',notes=['Source is chemically unidentified. This entry records missing sulfur input identity, not elemental S or sulfide salt.'])]
 r['materials'] += [C(i,'host_component','precursor_preparation')for i in powders if i!='lead-dioxide']+[C('aluminum-crucible','vessel','precursor_preparation')]
 r['stocks']=deepcopy(records[0]['stocks']);r['material_states']=deepcopy(records[0]['material_states']);r['operations']=deepcopy(records[0]['operations'])
 for shared_op in r['operations']:
  shared_op['description']='Shared upstream preparation applied to this annealing variant; not evidence of six independently counted fusion batches. '+shared_op['description']
  for parameter in shared_op['parameters'].values():
   if parameter['status']=='reported':parameter['status']='inherited';parameter['basis']=(parameter['basis']+'; 'if parameter['basis']else'')+'Shared glass preparation, inherited by this annealing variant.'
 add(r,'anneal','diffusion_induced_nanocrystal_growth','Anneal '+label+' at 600 °C',['stress-relieved-glass'],'annealed-'+key,AN,{'temperature':Q(600,'°C',AN),'duration':Q(hours,'h',AN),'heating_rate':Q(u='°C/min',e=AN)},desc='The second thermal treatment enhances diffusion of Pb2+ and S2− and forms PbS dots in the glass. The named ions describe the authors’ growth mechanism, not newly identified starting salts. Atmosphere, cooling after annealing and absolute batch charge are unreported.')
 p=P(r,'final',label+' annealed glass containing PbS quantum dots',AN,st='annealed-'+key,explicit=True);p['morphology']=F('Quantum dots embedded in multicomponent glass',AN,note='No atomic-coordinate model or current diffraction phase identification is supplied.')
 M(r,'growth-duration','final','growth_annealing_duration',hours,'h',AN)
 T(r,'sample-cohort','final','source_sample_cohort','Optical cohort SG1–SG4, cut and polished for measurements.'if key.startswith('sg')else 'Separate AFM cohort AFM1–AFM2; not interchangeable with an SG sample of a similar size.',AN)
 if key in peaks:
  for sym,val in zip(['s','1','2','3'],peaks[key]):M(r,'absorption-'+sym,'final','surface_associated_absorption_feature_energy'if sym=='s'else 'intrinsic_absorption_feature_'+sym+'_energy',val,'eV',OA,tech='Optical absorption',conditions='Feature '+sym.upper()+' assigned to '+label+' in the paired SG1(SG2) body-text list. Room-temperature measurement; no uncertainty or raw spectrum.')
 if key in optical_sizes:M(r,'optical-size','final','source_reported_optically_inferred_qd_size',optical_sizes[key],'Å',MODEL,tech='Comparison of numerical levels with absorption',status='author_derived',approximate=key=='sg1',conditions='Prose calls this size, whereas Figure 3 horizontal axes specify dot radius. Metric ambiguity retained; neither diameter nor radius is imposed and no factor-of-two conversion is made.')
 if key=='sg1':
  M(r,'main-aspl','final','reported_aspl_feature_energy',2.978,'eV',E(5,'ASPL and narrow-line discussion'),approximate=True,tech='Photoluminescence',conditions='High-energy ASPL feature, distinct from the narrow 2.476 eV line.')
  M(r,'near-excitation-line','final','near_excitation_upconverted_line_energy',2.476,'eV',E(5,'Figure 7 and text'),approximate=True,tech='Photoluminescence',conditions='Proposed resonant-Raman origin; not a confirmed second band-gap PL assignment.')
  M(r,'power-exponent','final','integrated_aspl_excitation_power_exponent',.86,'dimensionless',POWER,approximate=True,status='author_derived',tech='Log–log regression',conditions='Figure 6 SG1 only; no uncertainty, fitted coefficient or per-sample exponent for SG2–SG4.')
 if key.startswith('afm'):
  rounded=40 if key=='afm1' else 291;exact=40.19 if key=='afm1' else 291.24;depth=1.57 if key=='afm1' else 0
  M(r,'afm-size','final','source_reported_afm_qd_size',rounded,'Å',AFM,approximate=True,tech='AFM',conditions='Rounded prose average QD-size statement; Figure 4 labels a grain height, not a measured particle diameter.')
  M(r,'afm-grain-height','final','figure_reported_afm_grain_height',exact,'Å',E(4,'Figure 4'+('a'if key=='afm1'else'b')+' histogram label'),tech='AFM height distribution',conditions='Printed image-analysis label, distinct from rounded prose size; no uncertainty or count supplied.')
  M(r,'afm-substrate-depth','final','figure_reported_afm_substrate_depth',depth,'Å',E(4,'Figure 4'+('a'if key=='afm1'else'b')+' histogram label'),tech='AFM image-analysis label',conditions='Reference depth printed in the figure; do not interpret as substrate thickness or particle radius.')
  T(r,'distribution','final','reported_afm_size_distribution','Relatively narrow distribution.'if key=='afm1'else 'Wider distribution than AFM1.',AFM,conditions='Qualitative comparison, no FWHM or standard deviation supplied.')
 if key.startswith('sg'):T(r,'series-color','final','source_optical_cohort_color_scope','The SG-series color varies from brown to black with annealing time; exact per-sample colors are not tabulated.',AN)
 link(r,'glass-host','Required shared precursor preparation','Full upstream fusion, cooling and stress relief; unknown source identities and quantities remain explicit.')
 link(r,'optical-preparation'if key.startswith('sg')else'afm-analysis','Sample-specific characterization context','SG optical and AFM cohorts remain distinct.')
 r['quality']['missing_fields']+=['Precursor-selection supervision is partial: printed PbO2 is known but the sulfur precursor identity is absent. No complete precursor set or executable weighed recipe is claimed.']
 if key in optical_sizes:r['quality']['conflicts']+=['Prose calls the optical estimate QD size, while the theoretical axis is radius; a diameter interpretation is not established.']
 records.append(r)

r=base('optical-preparation','Cutting and polishing the SG optical specimens','procedure','Optical sample preparation')
r['materials']=[C(k+'-specimen','specimen','characterization')for k in ['sg1','sg2','sg3','sg4']]
add(r,'cut','glass_sectioning','Cut the SG1–SG4 glass samples',[k+'-specimen'for k in ['sg1','sg2','sg3','sg4']],'cut-specimens',AN,stage='characterization',kind='sample_set',desc='Each SG sample remains separate. Cutting tool, orientation, sample thickness and dimensions are not reported; AFM samples are not assigned this preparation by inference.')
add(r,'polish','optical_surface_polishing','Polish the cut SG specimens',['cut-specimens'],'polished-specimens',AN,stage='characterization',kind='sample_set',desc='Polishing is explicitly reported, but abrasives, grit, slurry, pressure, final roughness and cleaning procedure are absent.')
P(r,'sg-cohort','Separate polished SG1–SG4 optical specimens',AN)
T(r,'preparation-scope','sg-cohort','optical_preparation_scope','Only SG1–SG4 are explicitly said to be cut and polished. No matching AFM preparation, material removal or cross-section dimensions are provided.',AN)
records.append(r)

r=base('optical-absorption','Absorption spectra and annealing-dependent features','procedure','Room-temperature optical absorption')
r['materials']=[C(k+'-specimen','specimen','characterization')for k in ['sg1','sg2','sg3','sg4']]
add(r,'acquire','optical_absorption_acquisition','Acquire the separate SG-series absorption spectra',[k+'-specimen'for k in ['sg1','sg2','sg3','sg4']],'absorption-data',OA+E(2,'Optical setup'),stage='characterization',kind='analysis_data',env='Room temperature; numerical value unspecified',desc='The shared optical setup is a SPEX-750M monochromator with Joban-Yvon CCD 2000 × 800-3. The paper gives no absorption illumination spectrum, reference substrate, path thickness, slit widths or baseline procedure. The 514.5 nm Ar-ion excitation belongs to the excited optical measurements, not an invented monochromatic absorption scan.')
for key in ['sg1','sg2','sg3','sg4']:P(r,key,key.upper()+' optical absorption',OA)
P(r,'series','Separate SG-series absorption comparison',OA)
M(r,'prose-spectral-range','series','prose_absorption_spectral_range',None,'eV',E(2,'Figure 1 discussion'),minimum=.5,maximum=3,conditions='Body describes SG2 and SG1 inset in the same 0.5–3.0 eV range; inset axis visibly includes a 3.5 eV tick.')
T(r,'figure1-scope','series','figure1_sample_assignment','Main panel SG2 (3 h); inset SG1 (1 h). Both label S and intrinsic features 1, 2 and 3. Paired energies in prose are listed SG1(SG2), despite main/inset order.',E(2,'Figure 1 and paired energy list'))
T(r,'feature-s','series','author_surface_feature_assignment','Feature S is broader than 1–3 and is attributed to surface states, with localized phonon scattering at surface defects proposed to broaden it.',OA,status='author_derived')
T(r,'anneal-redshift','series','intrinsic_absorption_annealing_trend','Increasing annealing time shifts intrinsic features 1–3 to lower energy, suggesting QD growth. Exact SG3/SG4 feature energies are not tabulated.',OA,status='author_derived')
T(r,'surface-trend','series','surface_absorption_annealing_trend','Feature S has no significant energy shift but grows in intensity and broadens with annealing. Exact widths, amplitudes and fitting criteria are absent.',OA)
T(r,'state-merging','series','author_state_merging_explanation','As size increases, QD levels move closer together and toward surface-state energy; surface and intrinsic features become harder to resolve. This is interpretation, not a directly measured electronic density of states.',OA,status='author_derived')
T(r,'absorption-controls','series','absorption_dependence_scope','Spectra depend on QD concentration, host-glass properties and annealing details; these factors are not independently quantified or separated experimentally.',OA)
T(r,'bulk-comparator','series','figure2_bulk_absorption_reference','The dash-dotted E^(1/2) line represents bulk PbS in Figure 2. It is not a separately synthesized current-paper bulk sample and no normalization coefficient is provided.',E(2,'Figure 2 caption and label'))
T(r,'figure1-ticks','sg1','figure1_inset_axis_scope','Inset energy ticks extend to 3.5 eV, whereas the body describes the same 0.5–3.0 eV range as SG2. Original plot retained; no interpolation or resampling.',E(2,'Figure 1 inset'))
T(r,'figure2-offsets','series','figure2_display_scope','Curves labeled 1, 3, 6 and 12 hours with arbitrary absorption units. The paper does not provide absolute absorption coefficients or state a numerical correction for visual offsets.',E(2,'Figure 2'))
r['quality']['conflicts']=['Prose describes both Figure 1 spectra as 0.5–3.0 eV, while the SG1 inset axis includes a 3.5 eV tick. This display difference is preserved rather than forcing identical ranges.']
records.append(r)

r=base('photoluminescence','SG-series anti-Stokes emission and narrow-line comparison','procedure','Ar-ion-excited room-temperature photoluminescence')
r['materials']=[C(k+'-specimen','specimen','characterization')for k in ['sg1','sg2','sg3','sg4']]
add(r,'excite','argon_ion_laser_excitation','Excite the SG specimens with the Ar-ion laser',[k+'-specimen'for k in ['sg1','sg2','sg3','sg4']],'excited-specimens',E(2,'Optical setup'),{'excitation_wavelength':Q(514.5,'nm',E(2,'Optical setup'))},stage='characterization',kind='sample_set',desc='Argon-ion names the laser, not the synthesis atmosphere. Power density is described as low without a single per-spectrum value; polarization, spot size and exposure duration are absent.')
add(r,'acquire','photoluminescence_acquisition','Record the separate emission spectra',['excited-specimens'],'pl-data',PL,stage='characterization',kind='analysis_data',env='Room temperature; numerical value unspecified',desc='SPEX-750M monochromator and Joban-Yvon CCD 2000 × 800-3. Spectral correction, quantum yield, gain, slit widths, integration time and per-sample excitation intensity are not supplied.')
for key in ['sg1','sg2','sg3','sg4']:P(r,key,key.upper()+' optical emission',PL)
P(r,'series','Separate SG-series ASPL comparison',PL)
M(r,'source-aspl-range','series','source_described_aspl_energy_range',None,'eV',E(1,'Abstract')+E(3,'ASPL observations')+E(5,'Conclusion'),minimum=2.409,maximum=2.978,conditions='Authors describe green-to-violet ASPL using these energies. The lower value also corresponds to the 514.5 nm excitation context; this is not a tabulated continuous emission bandwidth or per-sample peak range.')
T(r,'aspl-presence','series','reported_aspl_presence','ASPL is reported for all SG optical samples at room temperature. The abstract/conclusion say all samples, but plotted optical spectra identify SG1–SG4, not AFM1/AFM2.',PL+E(1,'Abstract'))
T(r,'aspl-evolution','series','aspl_annealing_trend','Longer annealing broadens and red-shifts the ASPL line and enhances its lower-energy tail; exact SG2–SG4 peak energies and widths are not tabulated.',E(3,'Figure 5 discussion')+E(5,'Figure 5'))
T(r,'figure5-scope','series','figure5_display_scope','Spectra are labeled 1, 3, 6 and 12 hours; visible energy ticks include 2.90, 2.95 and 3.00 eV. Intensity is arbitrary and curves are vertically separated; no raw matrix or offset values are supplied.',E(5,'Figure 5'))
T(r,'figure7-dual-axis','sg1','figure7_signal_assignment','Absorption symbols use the left vertical axis; PL solid line uses the right. The narrow PL line is compared with the first intrinsic absorption feature. Arbitrary axes cannot be interpreted as equal absolute intensities.',E(5,'Figure 7 caption'))
M(r,'figure7-axis','sg1','figure7_displayed_energy_range',None,'eV',E(5,'Figure 7 axis'),minimum=2.3,maximum=2.9,conditions='Displayed axis limits, not a separately stated acquisition scan range.')
T(r,'near-line-mechanism','sg1','author_near_excitation_line_interpretation','The narrow approximately 2.476 eV line aligns approximately with the first intrinsic absorption feature and is more likely assigned to resonant Raman scattering. No Raman mode, shift, selection rule or independent Raman measurement is provided.',E(5,'Figure 7 discussion'),status='author_derived')
T(r,'emission-scope','series','stimulated_emission_claim_limit','The discussion motivates growth control through prior stimulated-emission work, but this article does not supply a lasing threshold, gain measurement, coherence measurement or quantitative proof that these ASPL curves are stimulated emission.',E(3,'Discussion preceding Figure 5'))
r['quality']['conflicts']=['Abstract/conclusion use all samples for ASPL, whereas the optical plots and methods assign the SG1–SG4 cohort; AFM-only specimens do not receive invented PL measurements.','The stated green-to-violet ASPL range includes an energy associated with the excitation source. Preserve the wording without promoting it to a raw spectral bandwidth.']
records.append(r)

r=base('afm-analysis','AFM topography, correlation and height distributions','procedure','Atomic force microscopy')
r['materials']=[C(k+'-specimen','specimen','characterization')for k in ['afm1','afm2']]
add(r,'scan','afm_topography','Image AFM1 and AFM2 as separate specimens',['afm1-specimen','afm2-specimen'],'topography-data',AFM,{'afm1_scan_width':Q(5,'µm',AFM),'afm1_scan_height':Q(5,'µm',AFM)},stage='characterization',kind='analysis_data',desc='The 5 × 5 µm² field applies to the upper AFM1 image. AFM instrument, mode, tip, resolution, environment and AFM2 full-field dimensions are unreported; optical cutting/polishing is not silently transferred.')
add(r,'analyze','afm_image_distribution_analysis','Inspect selected areas, correlation curves and height distributions',['topography-data'],'afm-analysis-data',AFM,stage='characterization',kind='analysis_data',desc='Figure 4a includes a magnified selected square, a correlation panel and a depth/height histogram; Figure 4b shows AFM2 detail and matching analysis panels. No particle counts, uncertainty, tip correction, correlation algorithm or exact size-distribution function is supplied.')
for key in ['afm1','afm2']:P(r,key,key.upper()+' source AFM specimen',AFM)
T(r,'afm1-scope','afm1','figure4a_panel_scope','Upper AFM1 overview is a 5 × 5 µm² scan with a selected rectangular region; lower image magnifies that selection. Histograms and correlation plot belong to this region, not the entire annealing series.',E(4,'Figure 4a caption and panels'))
T(r,'afm2-scope','afm2','figure4b_panel_scope','AFM2 shows a magnified image and its own correlation and histogram panels. No identical magnification, absolute lateral size or particle count is established relative to AFM1.',E(4,'Figure 4b caption and panels'))
M(r,'afm1-hist-range','afm1','figure4_histogram_displayed_depth_range',None,'Å',E(4,'Figure 4a histogram axis'),minimum=0,maximum=90,conditions='Figure axis, not min/max particle size.')
M(r,'afm2-hist-range','afm2','figure4_histogram_displayed_depth_range',None,'Å',E(4,'Figure 4b histogram axis'),minimum=0,maximum=670,conditions='Figure axis, not min/max particle size.')
T(r,'histogram-axis','afm1','figure4_histogram_axis_labels','Horizontal axis Depth (Å), vertical axis Hist. %. Separate upper panels are labeled Correlation. Grain-height values are not a diameter histogram merely because prose says QD-size.',E(4,'Figure 4 analysis panels'))
T(r,'afm-observation','afm2','author_afm_growth_observation','Authors state direct observation of QDs in both AFM specimens and larger mean apparent size with wider distribution after 30 h than after 5 h. No chemical map or atomic-resolution phase verification accompanies AFM.',AFM)
T(r,'cross-cohort-comparison','afm1','author_optical_afm_comparison','AFM1 (5 h) approximately 40 Å is compared with theory/absorption size for SG3 (6 h), also 40 Å. This is a comparison between distinct samples and size metrics, not a shared physical batch.',AFM+MODEL)
r['quality']['conflicts']=['Rounded AFM prose sizes about 40 Å and 291 Å are compared with optical estimates, but Figure 4 specifies grain heights 40.19 Å and 291.24 Å. No diameter/radius conversion or identical metric is established.']
records.append(r)

r=base('parabolic-model','Single-particle parabolic-band calculation','procedure','Infinite-well effective-mass model')
add(r,'solve','effective_mass_model','Solve the source-described single-particle model',[],'parabolic-levels',MODEL,{'electron_effective_mass_ratio':Q(.25,'m0',MODEL),'hole_effective_mass_ratio':Q(.25,'m0',MODEL)},stage='characterization',kind='analysis_data',desc='Single-particle Schrödinger equation with infinite potential well and parabolic energy bands. m0 is free-electron mass. No full equation, boundary-condition implementation, numerical solver, convergence grid or executable coefficients are printed; no reconstructed model is asserted as the authors’ calculation.')
add(r,'compare','energy_level_model_comparison','Compare ground and first-excited transitions with the four-band model',['parabolic-levels'],'parabolic-comparison',MODEL,stage='characterization',kind='analysis_data',desc='Authors report close agreement for ground and first-excited transitions. Higher-state curves are retained as original Figure 3a; no numerical curve table is fabricated.')
P(r,'model','Figure 3a theoretical PbS confinement model',MODEL,formula='PbS')
M(r,'radius-axis','model','figure3a_displayed_dot_radius_range',None,'Å',E(3,'Figure 3a axis'),minimum=10,maximum=90,conditions='Explicit theoretical dot-radius axis, not a measured sample diameter.')
T(r,'curve-labels','model','figure3a_model_state_labels','Electron and hole states are labeled 1S, 1P, 2S and 2P; legend shows E_(2,1), E_(2,0), E_(1,1), E_(1,0). l denotes orbital angular momentum.',E(3,'Figure 3a and caption'))
T(r,'method-limits','model','effective_mass_model_scope','Parabolic and infinite-barrier assumptions are model choices. Agreement claimed with four-band low states is not independent experimental phase or atomic-structure validation.',MODEL)
records.append(r)

r=base('four-band-model','Four-band envelope-function calculation and optical-size interpretation','procedure','Bulk (4 × 4) k·p envelope-function formalism')
add(r,'solve','four_band_envelope_calculation','Calculate levels with the four-band k·p formalism',[],'four-band-levels',MODEL,{'hamiltonian_dimension':Q(4,'matrix dimension',MODEL)},stage='characterization',kind='analysis_data',desc='Bulk (4 × 4) k·p Hamiltonian in envelope-function formalism; PbS band parameters treated as nearly isotropic and anisotropy neglected. References 19–20 support the formalism. The paper gives no explicit Hamiltonian elements or complete parameter set; the parabolic model’s 0.25 m0 masses are not silently assigned here.')
add(r,'compare','optical_energy_size_comparison','Compare calculated transitions with experimental absorption',['four-band-levels'],'size-inferences',MODEL,stage='characterization',kind='analysis_data',desc='Source assigns approximate optical sizes by matching transitions. Figure 3 axis is radius, while the prose says size. Preserve the ambiguity; do not calculate universal diameters or an atomic structure from these values.')
P(r,'model','Figure 3b theoretical levels and size interpretation',MODEL,formula='PbS')
M(r,'radius-axis','model','figure3b_displayed_dot_radius_range',None,'Å',E(3,'Figure 3b axis'),minimum=10,maximum=50,conditions='Theoretical radius-axis range, not a measured size distribution.')
T(r,'eigenvalue-labels','model','four_band_quantum_labels','Eigenvalues labeled by angular momentum j and parity π; l is orbital angular momentum.',E(2,'Four-band model')+E(3,'Figure 3 caption'))
T(r,'space-i','model','figure3b_space_i_definition','Space I: j = l + 1/2, π = (−1)^(l+1).',E(3,'Figure 3b legend'),conditions='Literal legend, not a reconstructed derivation.')
T(r,'space-ii','model','figure3b_space_ii_definition','Space II: j = (l + 1) − 1/2, π = (−1)^l.',E(3,'Figure 3b legend'),conditions='Literal legend preserved, including its l convention; no algebraic reinterpretation of the basis.')
T(r,'curve-parities','model','figure3b_labeled_curve_states','Labeled curves include j = 1/2, π = 1; j = 1/2, π = −1; j = 3/2, π = 1; j = 3/2, π = −1; and j = 5/2, π = −1. No exact eigenvalue arrays are supplied.',E(3,'Figure 3b'))
M(r,'strong-regime','model','source_strong_confinement_size_upper_bound',None,'Å',E(2,'Confinement-regime discussion'),maximum=80,conditions='Prose QD size ≤ 80 Å; metric ambiguity with radius axis retained.')
M(r,'weak-size','model','source_weaker_size_dependence_threshold',None,'Å',E(2,'Confinement-regime discussion'),minimum=100,minimum_exclusive=True,conditions='Prose dot size larger than 100 Å; not an experimentally measured threshold for these glass samples.')
T(r,'level-spacing','model','author_large_dot_level_spacing_interpretation','For larger dots, electron/hole subband dependence weakens and spacings become smaller than room-temperature thermal energy; authors infer breakdown of the phonon bottleneck and temperature-dependent lasing characteristics. No temperature series or laser experiment is supplied.',MODEL,status='author_derived')
M(r,'comparison-size','model','source_model_comparison_qd_size',24,'Å',E(2,'SG1 size estimate'),conditions='Source calls it size; Figure 3 radius axis prevents automatic diameter assignment.')
M(r,'comparison-energy','model','calculated_first_transition_energy',2.44,'eV',E(2,'SG1 size estimate'),status='author_derived',conditions='Calculated for source-described 24 Å dot; not a measured absorption energy.')
M(r,'rounded-experimental-energy','model','rounded_sg1_absorption_feature_for_model_comparison',2.48,'eV',E(2,'SG1 size estimate'),conditions='Comparison paragraph rounding; earlier SG1 feature 1 is 2.486 eV. Both retained without silently replacing either.')
T(r,'size-agreement','model','author_size_validation_scope','Authors compare SG1/SG2/SG3 inferred sizes with prior Thielsch et al. results (reference 8) and separate AFM specimens. This is qualitative model agreement, not a coordinate-level validation.',MODEL+AFM)
r['quality']['conflicts']=['Source optical sizes 24, 27 and 40 Å are called QD size, while theoretical axes explicitly say dot radius. AFM labels instead give grain height. These quantities are retained separately without unit-metric conversion.']
records.append(r)

r=base('power-response','SG1 excitation-power dependence of integrated ASPL','procedure','Log–log excitation-power series and regression')
r['materials']=[C('sg1-specimen','specimen','characterization')]
add(r,'sweep','excitation_power_series','Vary excitation intensity for SG1',['sg1-specimen'],'power-series',POWER,{'excitation_wavelength':Q(514.5,'nm',E(5,'Figure 6 caption'))},stage='characterization',kind='analysis_data',desc='514.5 nm laser excitation of SG1 (600 °C, 1 h). Excitation axis is kW/cm²; exact sampled powers, spot area, exposure duration and absolute calibration are not tabulated.')
add(r,'integrate','aspl_spectral_integration','Integrate the ASPL line at each excitation intensity',['power-series'],'integrated-aspl',POWER,stage='characterization',kind='analysis_data',desc='Integration limits, baseline subtraction, detector corrections and errors are not given. Integrated intensity uses arbitrary units.')
add(r,'fit','log_log_regression','Fit the excitation-power dependence on logarithmic axes',['integrated-aspl'],'power-fit',POWER,stage='characterization',kind='analysis_data',desc='Figure 6 gives an approximately 0.86 slope. No intercept, regression uncertainty, fitting weights or raw points are reported.')
P(r,'sg1','Figure 6 SG1 excitation-power series',POWER)
M(r,'exponent','sg1','integrated_aspl_excitation_power_exponent',.86,'dimensionless',POWER,approximate=True,status='author_derived',tech='Log–log regression',conditions='SG1 only, not a shared exponent fitted for all six annealed samples.')
T(r,'power-law','sg1','reported_power_law','I ∝ I_exc^0.86',POWER,conditions='I is integrated ASPL intensity; I_exc is excitation intensity. No proportionality constant supplied.')
T(r,'power-axis','sg1','figure6_axis_scope','Horizontal excitation intensity is kW/cm² on a log scale, with labeled 0.1 and 1 ticks; vertical integrated intensity is arbitrary units on a log scale. Tick labels do not establish a full tabulated sweep or exact extrema.',E(5,'Figure 6'))
T(r,'sublinear-inference','sg1','author_power_law_interpretation','Authors use sublinear rather than superlinear response to argue against Auger-driven ASPL under low excitation and in favor of a surface-state-mediated two-step process. The power law is evidence for their interpretation, not unique mechanistic proof.',POWER,status='author_derived')
records.append(r)

r=base('mechanisms','Chemical intuition and proposed anti-Stokes mechanisms')
P(r,'study','Source mechanism and growth interpretation',HOST+MECH)
T(r,'growth','study','author_growth_rationale','600 °C thermal treatment enhances Pb2+ and S2− diffusion and produces PbS QDs; increasing annealing time grows the dots and changes optical behavior. Starting PbO2 identity and sulfur form do not specify the full redox pathway.',AN,status='author_derived')
T(r,'three-mechanisms','study','considered_aspl_mechanisms','The article considers two-step two-photon absorption via intermediate states, Auger-like transfer from one recombining pair to another carrier, and phonon-assisted thermal activation.',E(1,'ASPL introduction')+MECH)
T(r,'phonon-model','study','author_phonon_mechanism_argument','Bulk relaxation is described through Fröhlich coupling to LO phonons. Discrete QD levels and energy/momentum restrictions create a phonon bottleneck; strong confinement allows only weak multiphonon processes when level spacings exceed LO-phonon energy. Authors argue phonon absorption is not dominant here.',MECH,status='author_derived')
T(r,'auger-model','study','author_auger_mechanism_argument','Spatial confinement could enhance effective carrier density and relax translational-momentum restrictions, but discrete final states hinder energy-conserving Auger transitions. Low excitation and the SG1 sublinear power law are used to argue for negligible Auger contribution.',MECH,status='author_derived')
T(r,'two-step-first','study','proposed_ts_tpa_first_step','Optical excitation creates an electron–hole pair in a QD; the electron relaxes into a defect-associated surface state near the QD–glass interface, while the hole remains trapped in a valence-band state.',MECH,status='author_derived')
T(r,'two-step-second','study','proposed_ts_tpa_second_step','A second photon excites the trapped surface-state electron to the QD conduction band; radiative electron–hole recombination then spans the effective QD gap.',MECH,status='author_derived')
T(r,'localization','study','proposed_surface_localization_effect','Strong surface localization implies broad momentum uncertainty, which the authors argue relaxes the momentum restriction for the second optical transition. No measured wavefunction or localization length is supplied.',MECH,status='author_derived')
T(r,'photon-source','study','proposed_second_photon_sources','The second photon may arrive directly from the excitation source or through photon recycling, citing reference 21. Neither channel is separately measured.',E(4,'Model continuation'),status='author_derived')
T(r,'saturation','study','proposed_sublinear_response_explanation','A small density of surface-defect states accepts electrons in the first step faster than their second-step photoionization, leading to sublinear power behavior. State density and rates are not quantified.',E(4,'Model continuation'),status='author_derived')
T(r,'model-support','study','author_model_support','The authors cite sublinear power dependence and small sample-to-sample ASPL energy shifts as support for the proposed surface-state pathway; exact surface-defect identity is not established.',E(4,'Model continuation'),status='author_derived')
T(r,'surface-loss','study','surface_trapping_context','Large distributions, low loading and poor surface passivation can cause surface trapping and nonradiative losses in glass-embedded dots, making stimulated emission difficult. These are explanatory context, not measured loading or passivation values for each batch.',E(3,'Discussion before Figure 5'))
T(r,'raman','study','author_narrow_line_hypothesis','The near-excitation 2.476 eV line in SG1 is more likely resonant Raman scattering, based on approximate alignment with intrinsic absorption. Its microscopic vibrational assignment is not supplied.',E(5,'Figure 7 discussion and Conclusion'),status='author_derived')
T(r,'mechanistic-certainty','study','mechanism_evidence_limit','TS-TPA, phonon and Auger arguments are author interpretations of optical data; no independent defect spectroscopy, time-resolved rate extraction, temperature activation experiment or surface reconstruction is shown.',MECH)
records.append(r)

r=base('literature-context','Cited background, theoretical limits and source completeness')
P(r,'context','Study scope and cited literature',E(1,'Introduction')+E(5,'References and Notes'))
T(r,'source-scope','context','inspected_source_scope','All five main pages, seven figures, captions, conclusions and 21 references were read and visually inspected. No table or numbered equation, verified SI, raw spectrum, atomic coordinate file or cited external full text was added.',E(1,'Article opening')+E(5,'Article ending'))
T(r,'six-samples','context','source_sample_inventory','Six named annealing variants: SG1 1 h, SG2 3 h, SG3 6 h, SG4 12 h, AFM1 5 h and AFM2 30 h at 600 °C. Shared upstream preparation is reused, not counted as six independently documented melt batches.',AN)
T(r,'model-references','context','four_band_theory_references','References 19–20: Tudury et al., Physical Review B 2000, 62, 7357; Andreev and Lipovskii, Physical Review B 1999, 59, 15402. Current article cites their formalism but does not reproduce a complete Hamiltonian or parameter set.',MODEL+E(5,'References 19–20'))
T(r,'size-reference','context','prior_size_comparison_reference','Reference 8: Thielsch et al., Nanostructured Materials 1998, 10, 13. Cited agreement does not substitute for reading its recipe, size metric or characterization.',MODEL+E(5,'Reference 8'))
T(r,'prior-aspl','context','prior_aspl_material_scope','Introduction cites bulk semiconductors, one-dimensional heterostructures, quantum wells, InAs/GaAs and InP/GaInP systems, and colloidal InP/CdSe. None is synthesized in this current PbS/glass study.',E(1,'ASPL introduction')+E(5,'References 9–18'))
M(r,'bohr-radius','context','cited_pbs_exciton_bohr_radius',200,'Å',E(1,'PbS introduction'),conditions='Cited material context, not a fitted radius of a current QD.')
M(r,'bulk-gap','context','cited_bulk_pbs_band_gap',.41,'eV',E(1,'PbS introduction'),conditions='Literature background, not a new bulk measurement.')
M(r,'small-dot-gap','context','cited_small_qd_band_gap',5.2,'eV',E(1,'PbS introduction'),approximate=True,conditions='Prior reported tunability, not observed for SG1–SG4 here.')
M(r,'telecom-wavelength','context','cited_pbs_absorption_wavelength_range',None,'µm',E(1,'PbS introduction'),minimum=1,maximum=2,conditions='Telecommunications motivation; not this paper’s SG absorption interval.')
M(r,'telecom-energy','context','cited_pbs_absorption_energy_range',None,'eV',E(1,'PbS introduction'),minimum=.6,maximum=1.3,conditions='Source companion literature range; no fresh wavelength-to-energy conversion applied.')
T(r,'lasers-context','context','laser_motivation_scope','Quantum-well and dot lasers are discussed for density-of-states enhancement, oscillator strength, gain, lower thresholds and reduced temperature sensitivity. These prior results motivate the paper; no laser device performance is demonstrated for its six glass samples.',E(1,'Introduction'))
T(r,'missing-reproduction','context','reproduction_limit','Without oxide proportions, sulfur source/loading, atmospheres and ramps, this source does not establish a complete weighed preparation. Literal aluminum crucible and PbO2 remain unresolved source details, not silently corrected chemical identities.',HOST+AN)
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
