"""Readable source records and explicit discrepancies; run after base builder."""
from pathlib import Path
import json,re,hashlib
B=Path(__file__).resolve().parent
def load(n):return json.loads((B/n).read_text(encoding='utf-8'))
def save(n,d):(B/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
I=load('source-inventory.json');F=load('source-facts.json');C=load('page-coverage.json')
mapping={
 'metalacetate':'metal acetate','fixedhold':'fixed hold','below80°C':'below 80°C','equivalentreference':'equivalent reference',
 'beyondca.1.65eq; not identical tocommonrecipe1.7eq':'Beyond ca. 1.65 equiv; the common preparation separately uses 1.7 equiv.',
 'Reported compositionZn0.998Mn0.002O; feed is0.50%, not0.20%':'Reported composition Zn0.998Mn0.002O; the feed is 0.50%, whereas measured product is 0.20%.',
 'Figure5nominal0.02% label doesnotestablishICPmeasuredproductconcentration':'Figure 5 labels this nominally 0.02%; the initial feed is explicit, but a measured final concentration is not.',
 'Here30min; common method saysca.30min':'This passage says 30 min; the common method says ca. 30 min.',
 'body saysca.100; caption100':'Body text says ca. 100; the caption says 100.',
 'All observedpeaks matchreference; noatomisticrefinement/CIFsupplied':'All observed peaks match the wurtzite reference. No atomic refinement or CIF is supplied.',
 'authors describeincreasefrom6to20nm; notdirectTEMfilmmeasurement':'Authors describe an increase from 6 to 20 nm by Scherrer analysis; this is not a direct film TEM measurement.',
 'authors explicitly saybandgap sizesunreliableinthisrange':'Authors explicitly say band-gap size estimates are not particularly reliable in this range.',
 'absorbance increase relative to air Mnacetate baseline':'Absorbance increase relative to the manganese acetate air control',
 'absorbance/discoloration after5days':'Absorbance/discoloration after 5 days',
 'Zn:Mn ratio asdiscussed':'Zn:Mn ratio stated in discussion',
 'authors say>49:1, whileFigure1a2% feedisexactly49:1; preservewordingratherthanstrictglobalconstraint':'Authors say >49:1, while the 2% feed in Figure 1a is exactly 49:1. Preserve both scopes rather than imposing a strict global constraint.',
 'thinfilm absorbance reachesstraylightlimitca.27000cm−1; bandedgesimilartobulkZnO':'Film absorbance reaches the stray-light limit near 27000 cm−1; the authors describe its band edge as similar to bulk ZnO.',
 'bandgap comparedwithfilm':'Band gap relative to the film',
 'initialfeedandseparatemeasurementuncertaintynotgiven':'Initial feed and sample-specific measurement uncertainty are not supplied.',
 'negative high-energyMCDonset':'Negative high-energy MCD onset','plotted lowerenergy limit':'Plotted lower energy limit',
 'field abovewhichMCDapproachessaturation':'Field above which MCD approaches saturation','MCDmagnetizationprobe':'MCD magnetization probe wavenumber',
 'per-Mn molarextinctioncoefficient':'Molar extinction coefficient per Mn2+',
 '24000cm−1,300K; Figure6scale1000isnotanother measuredvalue':'Measured at 24000 cm−1 and 300 K. The scale bar of 1000 in Figure 6 is not an additional extinction-coefficient result.',
 'no sample-specificICPuncertaintystated':'No sample-specific ICP uncertainty is stated.',
 'absorbanceat excitation':'Absorbance at excitation',
 'normalized tosameabsorbance;emissionscaledproportionally':'Absorption was normalized at the excitation energy, and emission was scaled proportionally.',
 'visibleemissionpeak':'Visible emission peak','UVemissionpeak':'UV emission peak','visiblequenchingvsundoped':'Visible emission quenching relative to undoped ZnO','UVquenchingvsundoped':'UV emission quenching relative to undoped ZnO',
 'Mn ligand-fieldemission':'Mn ligand-field emission','negativeobservation, notamissingmeasurement':'A negative observation, not an unperformed measurement.',
 'UVemission':'UV emission','fitted hyperfineA':'Fitted hyperfine A','fitted axialD':'Fitted axial D','D-strain sigma relative toD':'D-strain sigma relative to D',
 'literatureg parallel/perpendicular':'Literature g, parallel/perpendicular','literatureAparallel/perpendicular':'Literature A, parallel/perpendicular','literatureD':'Literature D',
 'meanrelative remanenceMR/MS at300K':'Mean relative remanence MR/MS at 300 K','meancoercivity300K':'Mean coercivity at 300 K','Curie temperature lowerbound':'Curie temperature lower bound',
 'Tc>350K; instrumentceiling350K; noexactTcmeasured':'Tc >350 K; the instrument ceiling was 350 K, so no exact transition temperature was measured.',
 'residualparamagneticMn fraction':'Residual paramagnetic Mn fraction','non-paramagneticMn fraction':'Non-paramagnetic Mn fraction',
 'ferromagneticallyalignedMn lowerbound':'Lower bound on the ferromagnetically aligned Mn fraction',
 'assumesmaximum5μB/Mn; notexactferromagneticfraction':'Assumes a maximum of 5 μB per Mn; this is a lower bound rather than an exact ferromagnetic fraction.',
 'effectiveferromagneticdomainspinlowerbound':'Lower bound on effective ferromagnetic domain spin',
 'averageSexceeds800,from300Ksaturationcurvature; notatomicspin':'The average effective domain spin exceeds 800, estimated from the 300 K saturation curvature; this is not an individual atomic spin.',
 'newsharpEPRfield':'Field of the new sharp EPR resonance','newsharpEPRg':'g of the new sharp EPR resonance','ZFCmeasurementfield':'ZFC measurement field',
 'temperature-seriesresidualmagnetizationfield':'Applied field for residual-magnetization temperature series','ZFC magneticphase transitions':'ZFC magnetic phase transitions',
 'sourcearguesagainstMnO/Mn3O4, whose citedNCmaxima<ca.45K; no universalimpuritydetectionlimit':'Authors argue against MnO/Mn3O4 impurities, whose cited nanocrystals show transition maxima below ca. 45 K; no universal impurity detection limit is established.',
 'estimatedDq':'Estimated Dq','estimatedRacahB':'Estimated Racah B','estimatedC/B':'Estimated C/B',
 'opticalelectronegativityMn':'Optical electronegativity of Mn','opticalelectronegativityZnOCB':'Optical electronegativity of the ZnO conduction band',
 'opticalelectronegativityZnOVB':'Optical electronegativity of the ZnO valence band','alternativeopticalelectronegativityVB':'Alternative optical electronegativity of the valence band',
 'predictedLMCTenergywithVB2.0':'Predicted LMCT energy with valence-band electronegativity 2.0','predictedMLCTenergy':'Predicted MLCT energy',
 'predictedLMCTenergywithVB2.4':'Predicted LMCT energy with valence-band electronegativity 2.4','subgapassignment':'Sub-bandgap assignment',
 'predictedrequiredp-typecarrierconcentration':'Theoretically predicted required p-type carrier concentration',
 'notmeasuredcarrierconcentrationinthesefilms':'This is cited theory, not a measured carrier concentration in these films.',
 'MnZnOsolidsolubility':'Solid solubility of Mn in ZnO',
 'exceeds10%at525°Cand1kbar; notactualfilmprocessingpressure':'Exceeds 10% at 525°C and 1 kbar in the cited study; 1 kbar is not the film processing pressure.',
 'O2pressureupperboundmaintainingMnOat900°C':'O2 pressure upper bound for maintaining MnO at 900°C',
 'below; NOTthisroomtemperaturesynthesispressure':'The cited value is a strict upper bound for a different high-temperature system, not this room-temperature synthesis.',
 '300K saturation moment forMs; reportedmassforsample':'Ms values are reported at 300 K; mass is the reported film mass.',
 'maintext mass':'Main-text film mass','spincoated layercount':'Spin-coated layer count','size assumedfordopingstatistics':'Size assumed for dopant statistics','meanMnionspernanocrystal':'Mean Mn ions per nanocrystal',
 'Assumeduniformsize,notdirectlycounteddopants. Printedλdefinitionisambiguous; retainedsourcefigureauthoritative.':'Assumes uniform particle size; dopants were not directly counted. The printed λ definition is ambiguous, so the original equation/figure and author-reported means are retained separately.',
 'mass-si':'SI film mass','Ms-emu':'Saturation moment per gram','Ms-per-Mn':'Saturation moment per Mn2+',
 'approximately spherical, highlycrystalline':'Approximately spherical and highly crystalline','wurtziteZnO':'wurtzite ZnO',
 'colorless to brown, broad tail withshoulder20000cm−1':'Colorless to brown, with a broad absorption tail and a shoulder near 20000 cm−1',
 'slightly larger, attributed to weakquantumconfinement':'Slightly larger; attributed by the authors to weak quantum confinement',
 'no corresponding excitonicfeature; weakintensitymaybescattering':'No corresponding excitonic feature; the weak remaining intensity may be scattering.',
 'not observed in5–350Kwindow':'No transition observed in the 5–350 K window',
 'tentative Mn2+→conductionband charge transfer':'Tentative Mn2+ → conduction-band charge transfer',
 'roomtemperature':'room temperature','Figure1b/Figure3/filmA':'Figure 1b / Figure 3 / film A','high-brightnessLaB6filament':'high-brightness LaB6 filament',
 'CuKα':'Cu Kα','S5/2':'S = 5/2','full-matrix diagonalization':'full-matrix diagonalization',
 'measuredpH':'measured pH','nitrogenincorporation':'nitrogen incorporation','carrierdensity/polarity':'carrier density/polarity',
}
# Exact phrase substitutions are deterministic; IDs and keys are kept unchanged.
skipkeys={'id','source_unit_id','sample_scope','source_id','parent_protocol','parent_sample','upstream_protocol','post_treatment','asset_id','linked_items','sample_ids','inputs','output','components','solvent','variant','text_cache','source_sha256','sha256','bundle_sha256','retained_fraction'}
def clean(v,k=None):
 if k in skipkeys:return v
 if isinstance(v,dict):return {k:clean(x,k) for k,x in v.items()}
 if isinstance(v,list):return [clean(x,k) for x in v]
 if isinstance(v,str):
  for a,b in sorted(mapping.items(),key=lambda z:len(z[0]),reverse=True):v=v.replace(a,b)
 return v
I=clean(I);F=clean(F);C=clean(C)
I['scope']='All 12 main-article pages and 4 matched SI pages were read and visually inspected by the extraction author. Complete source extraction remains pending independent scientific audit. Preserving plotted data is not equivalent to numerical trace digitization.'
I['training_status']['reason']='No experimentally refined atomic coordinates are supplied for these specimens, and absolute recipe quantities are incomplete.'
I['training_status']['note']='Task-specific inclusion requires canonicalization and independent audit. Phase, precursor, and relative-condition knowledge remains useful without a CIF.'
I['chemical_intuition']=[
 {'id':'homogeneous-feed','classification':'author_rationale','claim':'Direct solution chemistry aims to control composition and avoid segregated oxide impurities or dopant segregation under high temperatures and reducing conditions. The colloids also provide precursors for solution processing.','evidence':[{'source_role':'main','pdf_page':2,'locator':'Introduction'},{'source_role':'main','pdf_page':12,'locator':'Conclusion'}]},
 {'id':'induction','classification':'author_interpretation_with_cited_model','claim':'The 0.45-equivalent induction period is interpreted as buildup toward supersaturation before ZnO nucleation, following the LaMer model (reference 39). Basic zinc acetate clusters are proposed as the precursors (references 35 and 40).','evidence':[{'source_role':'main','pdf_page':6,'locator':'IV.A'}]},
 {'id':'amine-clean','classification':'author_interpretation_supported_by_EPR','claim':'Dodecylamine is proposed to ligate and solvate surface-exposed dopants. Sharper EPR supports a more homogeneous internal Mn environment. Heating also causes further Ostwald ripening, so cleaning and size evolution are coupled.','evidence':[{'source_role':'main','pdf_page':7,'locator':'IV.B–D'},{'source_role':'main','pdf_page':8,'locator':'IV.D'}]},
 {'id':'air-protection','classification':'author_proposed_mechanism','claim':'Zn2+-bound water acidification, opposed by acetate basicity, is proposed to inhibit Mn oxidation. No pH was measured. Incorporation into basic zinc acetate clusters is proposed to prevent coalescence into Mn-rich phases.','evidence':[{'source_role':'main','pdf_page':8,'locator':'IV.E / Scheme 1'}]},
 {'id':'dstrain','classification':'author_interpretation','claim':'Small D-strain is attributed to structural relaxation and a broader range of trigonal distortions near nanocrystal surfaces. It is not an atomic-coordinate refinement.','evidence':[{'source_role':'main','pdf_page':7,'locator':'IV.C'}]},
 {'id':'ct','classification':'author_tentative_assignment','claim':'The sub-bandgap intensity and MCD shape disfavor a weak ligand-field transition. An optical electronegativity model tentatively favors Mn2+ → conduction-band charge transfer. The strong absorption intensity initially suggests a valence-band → Mn2+ alternative, and that uncertainty is retained.','evidence':[{'source_role':'main','pdf_page':8,'locator':'IV.F'},{'source_role':'main','pdf_page':9,'locator':'IV.F'}]},
 {'id':'luminescence','classification':'author_proposed_photophysics','claim':'Dodecylamine surface passivation is associated with a larger UV-to-green emission ratio. Low-lying MLCT is proposed as a nonradiative Mn decay pathway. Mn is proposed to compete with surface traps for excitonic energy rather than strongly quench them through direct Förster transfer.','evidence':[{'source_role':'main','pdf_page':10,'locator':'IV.G'}]},
 {'id':'ferromagnetism','classification':'author_magnetic_interpretation','claim':'Film FMR and hysteresis indicate cooperative magnetism with residual paramagnetism. Missing impurity peaks in XRD alone are inconclusive at 0.2% Mn; the ZFC behavior and homogeneous precursors provide additional evidence for the authors’ assignment.','evidence':[{'source_role':'main','pdf_page':11,'locator':'IV.H'}]},
 {'id':'carrier-hypothesis','classification':'author_outlook_hypothesis_unverified','claim':'A radical-like g = 2.00 resonance could indicate redox during film formation. Nitrogen remaining from dodecylamine is suggested as one possible source of p-type defects. Carrier polarity, density, nitrogen incorporation, and the magnetic mechanism are not demonstrated; the authors acknowledge n-type compensation as a difficulty.','evidence':[{'source_role':'main','pdf_page':11,'locator':'IV.H'},{'source_role':'main','pdf_page':12,'locator':'IV.H continuation'}]}]
for row in I['chemical_intuition']:
 for e in row['evidence']:
  e.update(source_id='norberg2004-main',source_sha256=F['source_sha256'],printed_page=str(9386+e['pdf_page']))

gaptext=[
 ('Absolute recipe scale','No absolute reagent masses, stock/reaction volumes, yield, addition rate, wash volumes/cycle counts, separation force/time, or quantified initial capping stage are supplied.','Retain partial protocols; do not call these fully quantified recipes or complete laboratory SOPs.'),
 ('TMAH formula discrepancy','Materials prints N(CH4)4OH·5H2O, whereas sample preparation prints N(Me)4OH·5H2O.','Normalize the named tetramethylammonium identity while retaining the printed discrepancy.'),
 ('Base amount and clouding','The titration begins to cloud beyond ca. 1.65 equivalents, while the common preparation uses 1.7 equivalents.','Preserve the separate experimental scopes.'),
 ('TOPO route','The alternative procedure cites reference 32 without restating its full conditions. That referenced full paper was not inspected for this extraction.','Keep the alternative partial; do not inherit the dodecylamine treatment conditions.'),
 ('Feed and measured dopant content','Only the 0.20±0.01% product is explicitly linked to a 0.50% feed. The EPR series uses a 0.02% feed/nominal label; optical and MCD samples do not supply their initial feed.','Retain separate sample identities and mask unavailable feed/outcome fields.'),
 ('SI table count','The main article announces three SI tables; the matched supplied SI contains four.','Inventory all four, including the six-film Table S4.'),
 ('SI statistical notation','The printed variables and λ definition mix concentration with mean dopants per particle. The reported means are 7.9 and 79, not fractions 0.0013 and 0.013.','Preserve the equations, original figure and author-reported means as a model with a notation gap; do not silently repair it.'),
 ('Atomic structure and SAED','Wurtzite is supported by XRD and HRTEM. No experimental CIF, atomic coordinates, refined site occupancies, numerical lattice constants, or SAED pattern appear in the inspected main/SI.','Allow phase/morphology evidence; exclude an exact experimental atomic-structure/recipe label.'),
 ('Films D–F preparation','The SI gives film masses and magnetization, but omits coat counts, individual parent batches, and independently stated annealing conditions.','Retain partial outcomes; do not assign 20 or 40 coats by proximity.'),
 ('Film masses','Main-text A–C masses are 0.59/0.24/0.28 mg; SI values are 593/236/279 μg.','Both are retained as source reporting, consistent with rounding rather than separate replicates.'),
 ('Figure S3 / Table S4 conflict','Figure S3b visually orders mass-normalized high-field curves D > E > F, whereas Table S4 lists D = 0.038, E = 0.059, F = 0.076 emu/g. D/F identities or values are inconsistent between representations.','Preserve the figure and table separately. Do not swap labels or assign resolved D/F outcome training targets. Independent audit must assess this conflict.'),
 ('Raw plot data','Numerical curves and histogram counts were not supplied as raw arrays and have not been digitized.','Readable original plots plus explicit scalar results are retained; do not claim raw-data recovery.'),
 ('Mechanistic evidence','Measured pH, carrier polarity/density, nitrogen content, and a quantitative impurity-detection limit are absent.','Keep mechanistic hypotheses separate from measurements. Tc >350 K remains a lower bound.'),
 ('Other characterization','No Raman, SAED, sample-specific DFT calculation, refined atomic structure, or electrical carrier-transport measurement is reported in these 16 pages.','The actual additional property techniques are MCD, EPR and magnetometry; do not invent missing techniques.')]
for g,t in zip(I['gaps'],gaptext):g.update(scope=t[0],issue=t[1],resolution=t[2]);g.pop('effect',None)

# Bibliography boundaries: remove following figure captions/footer from the last
# numbered entry on each page. Retain the complete cited entry itself.
ends={15:'2, 673-677.',34:'108, 6303-6310.',38:'188, 167-187.',40:'107, 568-574.',44:'58, 13585-13589.',46:'Interscience: New York, 1967.',53:'1475-1478.',58:'1996.',61:'1115-1117.',63:'223, 135-139.'}
for r in I['references']:
 if r['source_role']=='main':
  n=r['reference_number'];t=r['bibliography_extracted_text']
  if n in ends:
   at=t.find(ends[n]);assert at>=0,(n,ends[n]);r['bibliography_extracted_text']=t[:at+len(ends[n])]
  r['inspection_status']='The citation and its discussion in this article were read; the cited full work was not inspected in this task.'
  r['role']='Cited upstream TOPO treatment and MCD procedure' if n==32 else 'Context, model or comparison; not an experiment from this source.'

# Protocol narrative cleaned explicitly; IDs and scientific numeric values persist.
P={p['id']:p for p in I['protocols']}
P['protocol-hydrolysis']['operations'][1]['conditions']='1.7 equivalents of 0.55 M ethanolic N(Me)4OH·5H2O, added dropwise under constant stirring at room temperature; exact addition time not reported.'
P['protocol-hydrolysis']['operations'][2]['conditions']='Initial growth occurs on a minutes timescale. Later ripening can proceed over several days at room temperature OR be accelerated near 60°C; these are alternatives.'
P['protocol-hydrolysis']['operations'][6]['conditions']='Dodecylamine capping and transfer into toluene. Initial capping amounts/conditions are unreported and distinct from subsequent 180°C surface cleaning.'
P['protocol-amine-cleaning']['operations'][0]['conditions']='180°C for ca. 30 min under nitrogen. Dodecylamine melting point is ca. 30°C.'
P['protocol-amine-cleaning']['operations'][1]['conditions']='Cool to below 80°C before precipitation.'
P['protocol-surface-control']['operations'][3]['conditions']='Wash, cap with dodecylamine, and resuspend in toluene for EPR. The surface-bound reference must not automatically receive the later 180°C surface-stripping treatment.'
P['protocol-titration']['operations'][0]['conditions']='0.10 M total metal acetate in DMSO, 2% Mn and 98% Zn.'
P['protocol-titration']['operations'][1]['conditions']='Successive additions of 0.15 equivalent of 0.55 M base in ethanol. The solid Figure 1a trace is 1.65 equivalents; further addition beyond ca. 1.65 equivalents causes clouding.'
P['protocol-titration']['operations'][2]['conditions']='Withdraw an aliquot, measure absorption, dilute it 70-fold, and remeasure to capture weak and intense bands. Spectra at 300 K, 1 cm path length.'
P['protocol-topo']['operations'][0]['conditions']='Heat in technical-grade TOPO following cited reference 32. Temperature, time and amounts are not restated in this paper.'
P['protocol-topo']['operations'][1]['conditions']='Drop-coat the TOPO-capped 1.1% Mn colloids onto quartz disks to form frozen solutions; variable-field MCD at 5 K.'
P['protocol-films']['scope']='Films A–F have nominal 0.20±0.01% Mn. Film-specific reported preparation and outcome details are retained separately.'
P['protocol-films']['operations'][0]['conditions']='Spin-coat dodecylamine-treated colloids onto 1 cm × 0.5 cm fused-silica substrates (the preparation section specifies films A–C).'
P['protocol-films']['operations'][1]['conditions']='Anneal at 525°C for 2 min in air after each spin-coated layer (A–C preparation section). The cited 1 kbar solubility experiment is unrelated to this annealing pressure.'
P['protocol-films']['operations'][2]['conditions']='Film A: 40 coats; films B and C: 20 coats each. SI films D–F are spin-coated but individual coat counts and annealing details are not explicitly restated.'
P['protocol-oxidation-controls']['operations'][0]['conditions']='Prepare 0.002 M Mn(OAc)2·4H2O in DMSO.'
P['protocol-oxidation-controls']['operations'][1]['conditions']='Compare air baseline, varying added Zn(OAc)2, anaerobic baseline, 0.010 M NaOAc (5:1 relative to Mn), and 0.002 M Mn(NO3)2 instead of Mn acetate.'
P['protocol-oxidation-controls']['operations'][2]['conditions']='Store for 5 days; air variants remain open to the atmosphere. Probe absorption at 20000 cm−1. Room-temperature oxidation is described in IV.E.'

for r in F['facts']:
 if r['id']=='norberg2004-domain-spin-bound':
  r['source_unit_id']='figure-8'
  r['sample_scope']='Films A–C collectively / individual film not specified'
  r['sample_ids']=['film-a','film-b','film-c']
  r['qualifier']='The average effective domain spin exceeds 800, estimated from the 300 K saturation curvature in Figure 8. The source discusses the thin-film domains collectively and does not assign a separate film-A value. This is not an individual atomic spin or a film-specific outcome.'
 if r['source_unit_id'] in ['film-d','film-f'] or (r['source_unit_id']=='table-s4' and isinstance(r['value'],dict) and r['value'].get('film') in ['D','F']):
  r['source_conflict']='Figure S3b curve ordering is inconsistent with Table S4 for D/F; values are transcribed, not resolved.'
  r['source_conflict_ids']=['g-si-curve-table']
  r['qualifier']=(r.get('qualifier','')+' The D/F magnetic outcome labels are unresolved between Figure S3b and Table S4; this value is preserved as tabulated, not corrected or relabeled.').strip()
  r['eligible_training']=False

# Supplement quantitative reference/model context omitted from specimen facts.
extra=[
 ('prior-Tc','Prior Mn:ZnO literature Curie-temperature range',[37,250],'K',2,'Introduction','cited_reference'),
 ('prior-surface','Surface-segregated Mn reported in reference 34',45,'%',2,'Introduction','cited_reference_lower_bound_approximate'),
 ('prior-Ms','Previously reported 300 K Mn:ZnO saturation moment',0.16,'µB/Mn2+',10,'IV.H, reference15','cited_reference'),
 ('ligand-epsilon','Typical tetrahedral Mn ligand-field extinction coefficient',[1,10],'M−1 cm−1',9,'IV.F, references47–48','cited_reference'),
 ('Ni-epsilon','Ni:ZnO acceptor-transition extinction coefficient',700,'M−1 cm−1',9,'IV.F, references32/50, 23100 cm−1','cited_reference_approximate'),
 ('Ni-binding','Typical Ni-doped II–VI acceptor CT binding energy',250,'cm−1',9,'IV.F, reference49','cited_reference_approximate'),
 ('halide-CT','No MnX4 LMCT below cited energy',38000,'cm−1',9,'IV.F, reference47','cited_reference_bound'),
 ('photocurrent','Cited Mn:ZnO photocurrent photon-energy lower reach',14500,'cm−1',9,'IV.F continuation p10, reference38','cited_reference'),
 ('Mn-emission-context','Mn ligand-field emission in other doped II–VI QDs',17200,'cm−1',10,'IV.G, references25–27; also580nm','cited_reference_approximate'),
 ('maximum-Mn','Assumed maximum ferromagnetic moment per Mn',5,'µB/Mn2+',11,'IV.H','author_model_assumption'),
 ('MnCl-CB','MnCl4 C/B used in ligand-field estimation',6.32,None,2,'Table S3 footnote','cited_model_input_si'),
 ('MnBr-CB','MnBr4 C/B used in ligand-field estimation',6.59,None,2,'Table S3 footnote','cited_model_input_si')]
for key,prop,value,unit,p,loc,status in extra:
 role='si' if status.endswith('_si') else 'main'
 F['facts'].append({'id':'norberg2004-context-'+key,'source_unit_id':'context-'+key,'sample_scope':'Literature or model context, not a measured outcome of this paper','property':prop,'value':value,'unit':unit,'status':status,'approximate':'approximate' in status,'uncertainty':None,'raw_text':None,'qualifier':'Cited/model system boundaries must be retained.','evidence':[{'source_id':'norberg2004-'+role,'source_role':role,'source_sha256':F['si_sha256'] if role=='si' else F['source_sha256'],'pdf_page':p,'printed_page':'S-'+str(p) if role=='si' else str(9386+p),'locator':loc}],'eligible_training':False,'review_state':'extracted_pending_independent_audit'})

# Replace compressed presentational labels with ordinary scientific phrases.
titles=['Absorption during titration and in the colloid/film pair','EPR during growth and surface cleaning','XRD, TEM, size distribution and HRTEM','Oxidation of manganese precursor solutions','Experimental and simulated X- and Q-band EPR','Absorption and magnetic circular dichroism','Absorption and photoluminescence','Magnetization of colloids and films','ZFC magnetization and paramagnetic residuals','EPR of the colloid and ferromagnetic film','Calculated dopant-number distributions','Temperature dependence of hysteresis parameters','Magnetization of six spin-coated films']
for v,title in zip(I['figures_tables_schemes'],titles):v['title']=title
I['figures_tables_schemes'][-1]['title']='Proposed inhibition of manganese oxidation by zinc acetate'
for q in I['equations']:
 q['meaning']={
 'equation-1':'Zeeman, hyperfine and axial zero-field splitting terms. The g and A tensors were approximated as isotropic for the powder-averaged spectra.',
 'equation-2':'Schematic oxidation expression, not a balanced preparative reaction. Product stoichiometry and hydration are unspecified.',
 'equation-3':'Jørgensen optical electronegativity model. For Mn donor/acceptor transitions, ΔSPE = +(28/9)[(5/2)B+C].',
 'equation-4':'Brillouin magnetization. Nanocrystal data use S=5/2, g=1.999 and N from ICP with no fit; film A residual fits N only.',
 'equation-s1':'Printed binomial expression and surrounding notation are retained without executing them as verified statistical code. The definitions of n, N and x are not consistently assigned to ensemble and particle counts.',
 'equation-s2':'The source defines λ as a concentration fraction while reporting mean counts of 7.9/79 per particle. Preserve the printed equation and flag this mismatch rather than silently repairing it.',
 'mcd-definition':'The normalization includes the printed denominator A; it is not silently replaced by a generic ellipticity convention.'}[q['id']]
for p in C['pages']:
 if p['source_role']=='si':
  p['scope']={1:'Title, full author list and SI identity.',2:'Tables S1–S3: all rows and footnotes, with model and literature roles.',3:'Figure S1, equations S1/S2 and the reported means; notation ambiguity identified.',4:'All panels of Figures S2/S3, all six film rows of Table S4, and five references.'}[p['pdf_page']]
 else:p['scope']=re.sub(r'(?<=\d)(?=[A-Za-z])|(?<=[a-z])(?=[A-Z])',' ',p['scope'])

save('source-inventory.json',I);save('source-facts.json',F);save('page-coverage.json',C)
summary=load('extraction-summary.json');summary.update(facts=len(F['facts']),source_conflicts=['TMAH printed formula','Base titration/common procedure scope difference','SI equation notation','Figure S3/Table S4 D/F ordering'],figures_tables_readable_asset_check='in progress');save('extraction-summary.json',summary)
print(json.dumps({'facts':len(F['facts']),'film_D_F_conflict':'explicit','main_references':63,'si_references':5}))
