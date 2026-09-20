"""Human-readable final prose for the complete paper-coverage record."""
import json,re
from pathlib import Path
OUT=Path(__file__).parent
p=OUT/'coverage.json';c=json.loads(p.read_text(encoding='utf-8'))
c['journal']='ACS Nano 2019, 13, 152–162'
c['table_inventory_status']='No numbered or formal tables occur in either document. Figure S14 is a condition matrix and Figure S17 a ratio/size scheme; both are fully inventoried as figures.'
c['remaining_gaps']=[
 'Every supplied main and SI page was read and visually reviewed. The remaining gaps are absent or ambiguous source information, rather than unreviewed pages.',
 'No acquired SAED image is present. Figure 6b and S12c/d are FFTs.',
 'No exact nanocrystal reactor charge, specimen-specific precursor branch, comprehensive workup, quench, isolated yield or storage history is supplied.',
 'No exact geometrical definition of the size labels or spread statistic is supplied; raw particle measurements, histograms and counts are absent.',
 'No measured CIF or atomic coordinates, quantified phase fractions, or universal final Fe3O4/γ-Fe2O3 assignment is supplied.',
 'No machine-readable spectra, diffraction or magnetic curves, or tilt-series files are supplied in these PDFs. Original figures are retained; curves have not been digitized.',
 'External referenced reconstruction algorithms and prior background recipes were not reviewed as full separate papers. They are listed explicitly under unresolved_referenced_methods.',
 'Original figure rights remain with the source rights holders; this review does not establish a public-republication license.'
]
c['saed_status']['basis']='All figures, captions and text in the 30 pages were reviewed. The relevant patterns are explicitly identified as FFTs. Generic discussion of electron diffraction on SI p.9 does not constitute a SAED dataset.'
c['conditioning']={'source_locator':'Main p.159','conditions':['All reactions use Schlenk nitrogen; apparatus is evacuated/refilled four times.','Water is nitrogen-saturated for 24 h.','OA and ODE are degassed at 25 °C for 1 h at 0.5 mbar, then nitrogen-saturated for an unspecified duration.','Reagents marked as nitrogen-conditioned in the Materials list retain that qualification; no gas flow is invented.']}
chartext={
 'maldi':[
 'Analytical oleate reactions use pure OA (>99%, GC,T); a separate technical-grade OA control is also examined. Samples are collected under nitrogen during heating at approximately 60 °C intervals, with exact dwell times unreported. Sample is diluted 1:25 in dry toluene (ratio basis unspecified). The matrix is 9-nitroanthracene at 12 mg/mL in dry chloroform. Matrix, sample and dry chloroform are combined on a ground steel target in a glovebox, then transferred in a Schlenk bag. Up to 1 s of air contact cannot be excluded.',
 'Bruker ultrafleXtreme with Smartbeam-II laser, positive reflector mode; m/z 350–4500 and 2000–20000. FlexControl 3.3 and flexAnalysis 3.3. External calibration uses peptide II standard in 2,5-dihydroxybenzoic acid; spectra also internally calibrated. Iron-isotope-pattern peaks selected for LIFT MS/MS.',
 'Eight major complex-ion assignments; no detectable complex above 3195 Da within the searched 2–20 kDa range. Multinuclear mixed-valence iron–oleate complexes describe precursor species, not a single stock identity.',
 ['Laser energy, spot/shot count, calibration residuals, replicate counts and raw spectra.']],
 'gc':[
 'Fe(III)-source oleate headspace at 60 °C; separate air-atmosphere iron-oleate and pure-OA closed-flask controls.',
 'PerkinElmer Clarus 500 TCD; He 5.0 (99.999%), 85 mL/min; Supelco 5A 45/60 molecular-sieve packing; oven 230 °C and detector 200 °C.',
 'S10 gives O2 integrated area 4.85% and N2 95.1%. OA-only oxygen consumption increases above 140 °C, whereas iron-oleate consumes oxygen below 100 °C. CO/CO2 production begins around 150 °C. Gas analysis supports redox, without uniquely establishing an elementary mechanism.',
 ['Headspace volume/pressure, loop or injection volume, calibration to absolute concentration, and analytical-control batch amounts.']],
 'co2-source-assay':[
 'Sulfuric acid is added to the prepared carbonate source and the released gas collected in a measuring cylinder. FeCO3: 1.70 g (14.6 mmol). Nominal Fe(III) carbonate source: 1.90 g (6.51 mmol).',
 'Volumetric gas measurement; acid amount and gas temperature/pressure are unreported.',
 'Fe(II) source gives approximately 300 mL gas versus a theoretical 320 mL, described as a 6% difference. Fe(III) source gives approximately 70 mL; authors estimate 16% Fe2(CO3)3, with the remainder probably Fe(OH)3/FeO(OH). Percentage basis is unspecified.',
 ['Acid volume and assay-specific concentration, gas temperature/pressure, water-vapor correction, percentage basis and replicates.']],
 'tem':[
 'A drop of diluted colloidal dispersion is placed on a carbon-coated 400-mesh grid; excess solvent is removed with filter paper and the grid air-dried.',
 'JEOL JEM 1011 at 100 kV and JEM 2200 FS at 200 kV; two CEOS Cs correctors (CETCOR/CESCOR) and Gatan 4K UltraScan 1000 camera.',
 'Morphology galleries and growth series; source condition-map sizes are retained as characteristic sizes, without conversion to diameter.',
 ['Per-figure instrument assignment; size statistic, particle count and geometric definition; aliquot volume and quench.']],
 'haadf-fft':[
 'Particles stored under ambient conditions and partly oxidized.',
 'Aberration-corrected cubed FEI-Titan at 300 kV; camera length 115 mm.',
 'Growth along [111] and side facets {113} from a [110] projection. S12 core FFT supports wustite; edge FFT is compatible with Fe3O4 and/or γ-Fe2O3. No separately acquired SAED panel occurs in the main article or SI.',
 ['Specimen storage duration and oxidation fraction; no measured atomic coordinate file.']],
 'electron-tomography':[
 'An octapod specimen with no exact synthesis-run assignment.',
 'FEI Tecnai G2 at 200 kV, Fischione 2020 single-tilt holder. Methods: −74° to +74° in 2° increments; body: ±76°. Inspect3D cross-correlation and manual tilt-axis adjustment; total-variation minimization reconstruction per reference 51.',
 'Reconstruction supports eight triangular pods. This is morphology tomography, not crystallographic coordinates.',
 ['Actual tilt sequence, raw projections, reconstruction parameters or code; external reference 50/51 implementation details.']],
 'eels-tomography':[
 'An oxidized octapod; degree of oxidation may differ from the Figure 6 specimen.',
 'Cubed FEI-Titan at 120 kV; Fischione 2020 holder; −65° to +65° with 10° increments. Holder allowed to relax several minutes after each tilt. Direct spectroscopic tomography follows Goris et al., reference 32. Body reports 15 data cubes.',
 'Fe2+-rich core and Fe3+-rich exterior with a gradual interface. Authors interpret wustite-to-maghemite oxidation through magnetite or mixed intermediates. FeTiO3 and hematite reference EELS spectra are prior reference standards, not synthesis products.',
 ['Actual 15-view angle list versus 14 nominal positions; energy resolution/dispersion, dwell/dose, raw cubes and quantitative phase fractions.']],
 'sem':[
 'Nanocrystal dispersion in toluene is dropped on a silicon wafer and air-dried.',
 'LEO 1550 at 20 kV. Main Figure 5b has a 70° tilt.',
 'Octapod three-dimensional morphology, without sample-size-derived recipe assignment.',
 ['Recipe and batch identifiers, panel-specific tilt angles, and coating details.']],
 'xrd':[
 'Purified dispersion is filled and sealed in a capillary inside an inert glovebox to prevent subsequent oxidation.',
 'Philips X’Pert PRO, Cu Kα 0.15418 nm, 40 kV and 110 mA, 2θ 30–110°. Capillary wall 0.1 mm, diameter 0.7 mm and length 80 mm.',
 'Both initial iron-source branches give pristine wustite diffraction, compared with reference 00-006-0615. No refined lattice parameters, measured sample CIF or phase fractions are reported.',
 ['Purification procedure, step/dwell time and branch-specific run conditions.']],
 'vsm':[
 'Samples dried under inert conditions in Quantum Design P125E holders.',
 'Quantum Design Dynacool. Methods state 5–350 K and fields up to 30 kOe; figure-specific sequences are retained separately.',
 'Exchange bias below approximately 200 K. Larger stars/cubes retain hysteresis at 300 K. Smaller stars have blocking temperature below 300 K and smaller cubes around 400 K as reported. Warm-up thermal lag causes a transition-temperature offset. Sample mass is absent, so plotted magnetic moments are not mass-normalized.',
 ['Exact nanocrystal size/dilution/phase, batch linkage, sweep rate, sample mass and the 350-versus-400 K scope conflict.']]
}
for row in c['characterization_inventory']:
    for k,v in zip(['preparation','acquisition','results','missing'],chartext[row['id']]):row[k]=v
c['simulations_and_models']=[
 {'id':'isotope-envelopes','source':'Main Figure 1; SI Figures S8–S9','scope':'Own calculated isotope patterns and a 10% LA mixture comparison; not atomic structure labels.'},
 {'id':'facet-model','source':'Main Figure 6c,d','scope':'Explanatory (100)/(111) terrace/step model of {113} facets; not refined coordinates.'},
 {'id':'shape-schemes','source':'Main Figure 8; SI Figures S14/S17','scope':'Authors schematic growth and condition illustrations; not newly measured particles.'},
 {'id':'tomographic-reconstruction','source':'Main Figures 5d and 7f–k','scope':'Projection-derived shape and valence reconstructions; not CIF crystal coordinates.'},
 {'id':'vortex-model','source':'SI p.19, reference 5','scope':'A prior simulation of spherical magnetite is cited as speculation; not performed or confirmed in this study.'}
]
refs=[
 ('Main reference 32: Goris et al., Ultramicroscopy 2016, 171, 55–62','Direct spectroscopic tomography reconstruction and reference EELS','Acquisition reported here is preserved; detailed algorithm implementation is incomplete.'),
 ('Main reference 50: Schoenmakers et al., Microscopy and Microanalysis 2005, 11, 312–313','Automated tomography acquisition/alignment','Inspect3D cross-correlation/manual axis adjustment is stated; no extra parameters invented.'),
 ('Main reference 51: Goris et al., Ultramicroscopy 2012, 113, 120–130','Total-variation tomography reconstruction','No executable reconstruction parameters claimed.'),
 ('SI reference 5: Betto and Coey, Journal of Applied Physics 2014, 115, 17D138','Prior micromagnetic simulation motivating the vortex-state suggestion','Not a new simulation or confirmed magnetic state in this paper.'),
 ('Main references 13–16: prior FeCl3, Fe(acac)3, FeO(OH) and Fe(CO)5 synthesis examples','Background precursor context','No fully specified additional recipe created from cited prior work.')
]
c['unresolved_referenced_methods']=[{'reference':a,'purpose':b,'status':'Citation read; external full procedure or raw data not retrieved/read as part of this paper review.','effect':d} for a,b,d in refs]
names=['acetone','dry acetone','dry chloroform','helium','hydrochloric acid','iron(II) sulfate heptahydrate','iron(III) sulfate','technical-grade oleic acid','pure oleic acid','1-octadecene','sodium carbonate','sulfuric acid','tetrahydrofuran','dry toluene','toluene','9-nitroanthracene','molecular sieve 5A 45/60 mesh','Milli-Q water','nitrogen','peptide II standard and 2,5-dihydroxybenzoic acid']
roles=['Listed; exact procedural use unspecified.','Listed; not assigned as the nanocrystal antisolvent.','MALDI matrix and target preparation.','GC carrier gas.','Listed; no quantified recipe use.','Fe(II) source; nitrogen-conditioned.','Fe(III) source; hydrate ambiguous; nitrogen-conditioned.','Ligand/medium; nitrogen-conditioned; impurity control.','Analytical MALDI reactions; exact nanocrystal grade unassigned.','Diluent.','Precipitating reagent; nitrogen-conditioned.','CO2 assay.','Listed; exact procedural use unspecified.','MALDI sample dilution.','Microscopy dispersion.','MALDI matrix; nitrogen-conditioned.','GC column packing.','Nitrogen-saturated for 24 h; carbonate preparation and washing.','Protective gas; four evacuation/refill cycles.','MALDI calibration.']
for row,n,role in zip(c['materials_inventory'],names,roles):row['name']=n;row['role']=role
for row in c['materials_inventory']:
    row['grade']=row['grade'].replace('notstated','not stated').replace('drybasis',' dry basis').replace('asprinted','as printed').replace('max0.01%H2O','max 0.01% H2O').replace('98.5%HPLC','98.5% HPLC')
    row['supplier']=row['supplier'].replace('notstated','not stated').replace('Th.Geyer','Th. Geyer').replace('AcrosOrganics','Acros Organics').replace('BrukerDaltonik','Bruker Daltonik')

# Clear condition-specific prose, retaining all source values and IDs.
recipe_fixes={
 'feii-carbonate':('Fe(II) carbonate precipitation',['Slow-addition rate, recovered mass/yield and salt-conditioning time are absent; sodium-carbonate mass/mmol conflict retained.']),
 'feiii-source':('Nominal Fe(III) carbonate/hydroxide/oxyhydroxide source',['Sulfate hydration and nominal molar loading unresolved; phase proportions beyond the authors 16% nominal-carbonate estimate are absent.']),
 'feii-oleate':('Fe(II)-source oleate preparation',['FeCO3 mass/mmol conflict; vacuum pressure and stock concentration/yield absent. Sevenfold scale-up is a claim, not another batch.']),
 'feiii-oleate':('Fe(III)-source oleate preparation',['Mixed precursor with nominal molar loading; vacuum pressure and concentration absent. Fourfold scale-up is a claim, not another batch.']),
 'generic-thermolysis':('General Fe(II)- or Fe(III)-source oleate thermolysis',['Charge amount, source choice, dilution-specific setpoint within 330–350 °C, exact hold within 3–5 h, and workup are unresolved.']),
 'ode0':('No ODE, Fe:OA 1:7 growth family including the late cubic condition',['Individual run/iron-source linkage, exact temperatures and size definition are unresolved.']),
 'ode8':('8 vol% ODE growth family and four-point temperature trajectory',['Physical identity linking trajectory to grid, additional S18 temperatures, and reactor quantities are absent.']),
 'ode30':('30 vol% ODE growth family',['Exact per-run temperature, branch and amount absent; do not substitute 34 vol%.']),
 'ode56':('56 vol% ODE growth family',['Exact per-run temperature, branch and amount absent.']),
 'high-ode-ratio':('Greater-than-66-vol% ODE cubic family at Fe:OA 1:2.5, 1:4, 1:5 or 1:7',['Exact ODE fraction, temperature, time, amount, iron-source branch and spread definition are absent.']),
 'ode34':('34 vol% ODE star example',['Size, temperature, time, amount and branch absent; magnetic S19 is similar, not the same identified batch.']),
 'oxide-oxidation':('Post-synthetic ambient oxidation of microscopy specimens',['Exposure time/humidity, oxygen concentration, workup and conversion fractions absent.']),
 'other-iron-sources':('Qualitative FeO(OH)/Fe(acac)3 comparison and background FeCl3/Fe(CO)5 routes',['Authors mention hydroxide/acetylacetonate experiments without run quantities or protocols; chloride/carbonyl examples cite prior studies.']),
 'analytical-controls':('CO2 assays, iron-oleate/air and OA-only/air GC, and OA-purity MALDI controls',['Acid amount, assay gas temperature/pressure, air headspace volume and individual control charges absent.'])
}
for row in c['recipe_inventory']:row['label'],row['gaps']=recipe_fixes[row['id']]

replacements={
 'IronII':'Iron(II)','IronIII':'Iron(III)','FeIIgas':'Fe(II) gas','FeIIIgas':'Fe(III) gas',
 'Initial complex formation60 C':'Initial complex formation at 60 °C','S/N>5':'S/N > 5',
 'Panelc':'Panel c','N2,O2,CO,CO2':'N2, O2, CO, CO2','3a34':'3a: 34','3b8':'3b: 8','3c separate':'3c: separate',
 'Fe:OA1:7':'Fe:OA 1:7','Fe:OA1:2.5':'Fe:OA 1:2.5','Fe:OA1:2.5/4/5/7':'Fe:OA 1:2.5/4/5/7',
 '3a66':'3a: 66','3b92':'3b: 92','reference00':'reference 00',
 'TEM scale':' TEM scale','SEM tilt70':'SEM tilt 70','pods;3D':'pods; 3D','[110]projection':'[110] projection','growth[111]':'growth [111]',
 'facets{113}':'facets {113}','modeled(100)/(111)terraces':'modeled (100)/(111) terraces',
 'Figure6and7':'Figures 6 and 7','Fe3+ from hematite, citedref32':'Fe3+ from hematite, cited reference 32',
 'Fe2+-rich interior/Fe3+-rich exterior;':'Fe2+-rich interior / Fe3+-rich exterior; ',
 'phase1':'phase 1','phase2':'phase 2','phase3':'phase 3','phase4':'phase 4',
 'Fe(II)carbonate':'Fe(II) carbonate','Fe(III)carbonate':'Fe(III) carbonate','four washes':'four washes',
 'displayed peak955':'displayed peak 955','peak955':'peak 955','peaks1027':'peaks 1027','the955':'the 955',
 'FeII2(oleate)3+':'[Fe(II)2(oleate)3]+','Caption:oleate':'Caption: oleate ',
 'spacingannotated':'spacing annotated','10%linoleic-acid':'10% linoleic-acid','10%LA':'10% LA',
 'not an independently':'not an independently','O2RT0.76,area4.85%':'O2 RT 0.76, area 4.85%',
 'N2RT0.92,area95.1%':'N2 RT 0.92, area 95.1%','min:sek':'min:sek',
 '[100]wustite':'[100] wustite','edge[100]magnetite':'edge [100] magnetite','no ODE':'no ODE',
 'MainFig':'Main Fig','mainFigure':'main Figure ','Figure5':'Figure 5','FigureS14':'Figure S14','FigureS15':'Figure S15','FigureS16':'Figure S16','FigureS17':'Figure S17','FigureS18':'Figure S18',
 '2–6min':'2–6 min','40–60min':'40–60 min','stated;50':'stated; 50','only four temperatures directly available in mainFigure8':'only four temperatures directly available in main Figure 8',
 'after4':'after 4','after5':'after 5','ZFCfield':'ZFC field','20kOefield-cooled':'20 kOe field-cooled',
 '20 kOefield-cooled':'20 kOe field-cooled','350K plotted':'350 K plotted','above200':'above 200','at300':'at 300',
 '50OeZFC':'50 Oe ZFC','Stars5K/300K':'Stars: 5 K/300 K','cubes10K':'cubes: 10 K',
 '10K-exchange':'10 K exchange','300K.':'300 K.','blocking<300':'blocking <300','cubes around400':'cubes around 400',
 'mainmethod350':'main method 350','sayskOe':'says kOe','Bodyreports':'Body reports',
 'Sourcecalls':'Source calls','FigS':'Fig. S','Mainp.':'Main p.','SIp.':'SI p.','pp.11–15':'pp.11–15',
 'vol%ODE':'vol% ODE','vol%OA':'vol% OA','and3D':'and 3D','Assigned m/z:':'Assigned m/z: ',
 '0.5min331 C':'0.5 min at 331 °C','2min331 C':'2 min at 331 °C','8min339 C':'8 min at 339 °C','56min341 C':'56 min at 341 °C',
 'body tilt±76 vs Methods±74degrees':'body tilt ±76° versus Methods ±74°',
 'washes.1L':'washes. A 1 L','955.6ion':'955.6 ion','FeOA337':'FeOA 337','annotation281':'annotation 281',
 'A10%':'A 10%','at60':'at 60','O2release':'O2 release','labelmin':'label min','above140':'above 140',
 'bars20':'bars 20','angle70degrees':'angle 70 degrees','ODE0':'ODE 0','windows2':'windows 2',
 'row:0%82':'row: 0%: 82','8%45':'8%: 45','30%37':'30%: 37','56%21':'56%: 21',
 'the2–6':'the 2–6','the40–60':'the 40–60','Upper-left21':'Upper-left 21','upper-right37':'upper-right 37','lower-left45':'lower-left 45','lower-right82':'lower-right 82',
 'Upper-left23':'Upper-left 23','upper-right28':'upper-right 28','lower-left40':'lower-left 40','lower-right60':'lower-right 60',
 'nm=56%ODE':'nm = 56% ODE','nm=30%':'nm = 30%','nm=8%':'nm = 8%','nm=noODE':'nm = no ODE',
 'than66':'than 66','at8':'at 8','Times0.5':'Times 0.5','Figure3a':'Figure 3a','Figure3b':'Figure 3b',
 'including50':'including 50','and300':'and 300','stars(top)and cubes(bottom)under':'stars (top) and cubes (bottom) under',
 'labels10':'labels 10','reach400':'reach 400','0615.100':'0615. 100',
 'S14is':'S14 is','S17is':'S17 is','sourcebranch':'source branch','priorstudies':'prior studies'
}
skip={'id','record_id','record_ids','record_type','source_id','source_group','recipe_family','source_path','text_path','image_path','sha256','original_crop_asset','coverage_status','status','link_status','source_sample_label','reviewed','eligible_training','physical_batch_id','document_role','crop_box_fraction','page_size_points','counts','validation'}
def clean(v,key=''):
    if isinstance(v,dict):return {k:clean(x,k) for k,x in v.items()}
    if isinstance(v,list):return [clean(x,key) for x in v]
    if not isinstance(v,str) or key in skip or ':/' in v or ':\\' in v or v.startswith('https://'):return v
    for a,b in replacements.items():v=v.replace(a,b)
    v=re.sub(r'(?<=\d)(vol%|nm|Da|kOe|Oe|mmol|mL|mg|kV|mbar|rpm|mm)(?=\W|$)',r' \1',v)
    v=re.sub(r'(?<=\d)vol%',r' vol%',v)
    v=re.sub(r'(?<=\d)(min|C|K)(?=\W|$)',r' \1',v)
    v=re.sub(r'([,;])(?=[A-Za-z0-9])',r'\1 ',v)
    return v
c=clean(c)
# Reviewed, source-local complex assignments; no molecular stock formula is implied.
c['precursor_complex_assignments']=[{'mz':mz,'assignment':assignment,'scope':'Positive ion assignment from Figure 1a; not a neutral stock formula.','source_locator':'Main p.153, Figure 1a','reviewed':True} for mz,assignment in [(955.6,'[Fe(II)2(OA−)3]+'),(1308.7,'[Fe(III)2Fe(II)(O−II)(OA−)4]+'),(1590.0,'[Fe(II)2Fe(III)(O−II)(OA−)5]+'),(1871.2,'[Fe(III)3(O−II)(OA−)6]+'),(1927.2,'[Fe(II)3Fe(III)(O−II)(OA−)6]+'),(2208.4,'[Fe(II)2Fe(III)2(O−II)(OA−)7]+'),(2561.6,'[Fe(III)3Fe(II)2(O−II)2(OA−)8]+'),(2842.9,'[Fe(III)4Fe(II)2(O−II)2(OA−)9]+')]]
c['mechanistic_findings']=[
 {'source':'Main pp.154–155','finding':'Formation of oleates at 60 °C is separated by an approximately 80 K thermal window from later degradation. Little change in assigned complexes is observed over 60–140 °C.','status':'Authors interpretation of analytical series; not an exact run schedule.'},
 {'source':'Main p.155','finding':'At 320–350 °C viscosity and apparent boiling point rise; low-temperature complex signals later disappear near nucleation. The authors propose a cross-linked iron-oleate network that breaks down while releasing FeO monomers.','status':'Mechanistic proposal; no unique direct molecular structure of the network established.'},
 {'source':'Main pp.158–159; Figure 8','finding':'Fast anisotropic star growth is followed by smoothing/truncation, then a slower cubic growth regime attributed to Ostwald ripening.','status':'Morphology-based growth interpretation; no independently measured monomer count or diffusion constant.'},
 {'source':'Main p.156','finding':'Authors report that either starting iron-source oxidation state can yield identical shape, size and crystal structure and that nanocrystal output can reach 20 g per batch.','status':'General capability statements; no individual figure is assigned a 20 g yield or a complete scale-up protocol.'}
]
c['crop_review']={'all_36_original_crops_visually_checked':True,'method':'Every source page reviewed; all resulting crops reviewed in three contact sheets for intact panels, captions, axes, scale bars and equation numbers.','contact_sheets':[str(OUT/f'crop-contact-{i}.png') for i in [1,2,3]],'remaining_crop_issues':[]}
c['validation_summary']=json.loads((OUT/'validation.json').read_text())
p.write_text(json.dumps(c,indent=2,ensure_ascii=False),encoding='utf-8')
print('Readable coverage finalized; IDs and numeric source values preserved.')
