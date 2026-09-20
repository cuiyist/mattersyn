"""Lian 2021 source-specific author transcription; supplied PDF scope only.
All 8 main and 26 SI pages were read and viewed. No independent approval is asserted.
"""
TITLE='Realizing Near-Unity Quantum Efficiency of Zero-Dimensional Antimony Halides through Metal Halide Structural Modulation'
AUTHORS=['Linyuan Lian','Peng Zhang','Xiuwen Zhang','Qi Ye','Wei Qi','Long Zhao','Jianbo Gao','Daoli Zhang','Jianbing Zhang']
A='(C12H28N)2SbCl5'; B='(C12H28N)SbCl4'
PAGE_NOTES={'main':[
'Title, nine-author byline, DOI/journal identity, abstract, graphical abstract and introduction. Background compounds are cited comparators, not present-study syntheses.',
'Complete structural/photophysical results through start of decay discussion; Scheme 1. Bulk synthesis ratios, coordination, distortion values, non-emission, PLQE, spectra and stability are composition-scoped.',
'Figure 1 a–d structure views and Figure 2 a–f photographs, spectra, two lifetime fits, temperature map, coupling fit and proposed excited-state scheme; decay prose continues.',
'Complete equations 1–2, temperature behavior and proposed electronic levels; DFT methods interpretation and Figure 3 bands/TDME/DOS. Calculated electronic gaps are not measured optical gaps.',
'DFT parity/TDME continuation, HSE06 gaps; Figure 4 a–f PXRD, TEM/HRTEM, optical spectra and two decay fits; nanocrystal size and dried-powder PLQE.',
'Colloidal settling, film results and Figure 5 a–d; conclusions; all chemicals and five distinct synthesis/film procedures, including controls and workup.',
'All characterization and DFT parameters; associated PDF/ZIP/MP4 declaration, authors/affiliations/ORCIDs, competing-interest statement, acknowledgments and reference 1.',
'References 2–27, full bibliographic text; these cited works were not independently read.'
], 'si':[
'Exact matching title and nine-author byline; affiliations 1–4.',
'Affiliations 5–7 and correspondence; complete four- and five-coordinate bond-angle-variance definitions, including the different sums/denominators.',
'Four- and five-coordinate bond-length-distortion definitions. Figure S1 PXRD artwork; caption continues on S4.',
'Figure S1 caption; full Figure S2 Sb 3d/Cl 2p XPS; Figure S3 TGA artwork with caption on S5.',
'Figure S3 caption; Figure S4 absolute PLQE artwork/caption with 96.8%; Figure S5 CIE artwork with caption on S6.',
'Figure S5 caption; Figure S6 excitation-dependent spectra and 280–400 nm legend.',
'Figure S7 PLQE stability over three months; Figure S8 temperature-series artwork with caption on S8.',
'Figure S8 caption; Figure S9 two-Gaussian fits at 197, 237 and 277 K.',
'Figure S10 ES1 activation plot and 205.26 meV/R=0.99 annotation; Figure S11 size histogram artwork with caption on S10.',
'Figure S11 caption and 6.43±0.17 nm annotation (uncertainty type unspecified); Figure S12 PLQE=89.3%; Figure S13 photographs with caption on S11.',
'Figure S13 caption; Figure S14 spin-coated-film ambient/365 nm photographs and emission spectrum.',
'Figure S15 bulk-crystal beta-irradiation photographs and radioluminescence spectrum.',
'Table S1 crystal data: both compositions, formula/mass/temperature/cell/space group/Z/density/absorption and two-theta bounds.',
'Table S1 indices/reflection counts/refinement metrics/difference peaks; Table S2 first ten bond entries in left/right blocks.',
'Table S2 continuation and Table S3 beginning: both side-by-side bond columns read, with literal atom labels and uncertainties.',
'Table S3 continuation and Table S4 first sixteen bond angles; two independent Sb sites in the B composition remain distinct.',
'Table S4 continuation and Table S5 first twelve angles; all organic and inorganic angles retained.',
'Table S5 continuation and Table S6 coordinate/Ueq heading and scale definition.',
'Table S6 first 23 heavy-atom rows with x/y/z/Ueq and uncertainties; negative/unwrapped coordinates retained.',
'Table S6 final nine rows; Table S7 heading and first nine heavy-atom rows.',
'Table S7 next 24 heavy-atom rows, literal atom IDs, all four numeric columns and uncertainties.',
'Table S7 final three rows. No additional hidden table or figure on remaining page area.',
'Table S8 anisotropic-displacement definition, U11/U22/U33/U23/U13/U12 order and first 18 rows.',
'Table S8 final 14 rows; Table S9 heading/exponent and first four rows.',
'Table S9 next 24 rows with six components each; all negative off-diagonal terms retained.',
'Table S9 final eight rows; all three SI references. No hydrogen-coordinate or occupancy table is supplied.'
]}

# id, role, page, locator, title, claim, specimen/model context, typed (meaning, raw, unit), gap/conflict IDs.
FACTS=[]
def F(i,p,l,t,c,s,qs=(),flags=(),role='main'):FACTS.append((i,role,p,l,t,c,s,list(qs),list(flags)))
F('source-identity',1,'Title/byline/DOI/abstract','Article identity','The supplied main identifies this title, nine authors and DOI 10.1021/acsami.1c18038; source date is 2021.','study')
F('background',1,'Introduction; continues p.2','Cited structural comparators','MnBr4 tetrahedra, SnBr4 seesaws, CuI2 dimers, CuBr2 rods and SnBr6 octahedra are cited precedents. No synthesis or measurements from these references are admitted as current data.','cited-background')
F('bulk-a-charge',6,'4.2','Bulk A precursor solution','Dissolve tetrapropylammonium chloride and SbCl3 in DMF and filter to a clear precursor solution.','bulk-a',[('C12H28NCl charge','2','mmol'),('SbCl3 charge','1','mmol'),('DMF solvent charge','800','uL')],['G1'])
F('bulk-a-growth',6,'4.2; Scheme 1 p.2','Bulk A crystallization','Slow solvent evaporation at room temperature for four days produces bulk A single crystals. No absolute room temperature or yield is supplied.','bulk-a',[('evaporation duration','4','day')],['G1'])
F('bulk-b-variant',6,'4.2 final sentence','Bulk B variant','Use 1 mmol C12H28NCl instead in the same stated crystal-growth procedure; the SbCl3 charge, DMF charge and four-day room-temperature evaporation are inherited by this explicit variant.','bulk-b',[('C12H28NCl charge','1','mmol'),('SbCl3 inherited charge','1','mmol'),('DMF inherited solvent charge','800','uL'),('inherited evaporation duration','4','day')],['G1'])
F('nc-stock',6,'4.3','Nanocrystal precursor stock','Dissolve salts in DMF and filter clear. The 2000 uL describes solvent charged, not a separately calibrated final solution volume.','nc-a',[('C12H28NCl charge','1','mmol'),('SbCl3 charge','0.5','mmol'),('DMF solvent charge','2000','uL')],['G2'])
F('nc-injection',6,'4.3','Ligand-assisted reprecipitation','Rapidly inject a precursor-solution aliquot into vigorously stirred toluene/oleic acid. The source does not state a numerical growth temperature, stirring rate or injection duration.','nc-a',[('precursor solution aliquot','500','uL'),('toluene antisolvent','5','mL'),('oleic acid ligand','500','uL')],['G2'])
F('nc-recovery',6,'4.3','Nanocrystal recovery','Centrifuge crude solution and collect nanocrystal powders. No wash, drying, yield or defined redispersion protocol is supplied.','nc-a',[('centrifuge speed','7000','rpm'),('centrifuge duration','3','min')],['G2'])
F('composite-mixing',6,'4.4; Figure 5 a/b','Composite film ratio series','Blend blue BaMgAl10O17:Eu2+ phosphor and yellow A nanocrystals in PS/toluene at the five stated blue/yellow mass ratios, including pure-component controls; stir 20 min. No absolute loading or PS concentration is reported.','film-composite-series',[('blue/yellow ratio film 1','1/0','mass_ratio_parts'),('blue/yellow ratio film 2','1/3','mass_ratio_parts'),('blue/yellow ratio film 3','1/2','mass_ratio_parts'),('blue/yellow ratio film 4','2/3','mass_ratio_parts'),('blue/yellow ratio film 5','0/1','mass_ratio_parts'),('mixing duration','20','min')],['G3'])
F('composite-casting',6,'4.4','Composite film casting and peeling','Drop-cast the homogeneous mixture onto glass, slowly evaporate solvent in a fume hood, and peel the composite film to obtain a flexible film. Drying temperature/time and film dimensions are not reported.','film-composite-series',[],['G3'])
F('spincoat-stock',6,'4.4 final sentences','Separate spin-coating precursor','Dissolve the two salts in DMF and filter clear. This precursor-film route is separate from the nanocrystal/PS drop-cast composite procedure.','film-spincoat',[('C12H28NCl charge','2','mmol'),('SbCl3 charge','1','mmol'),('DMF solvent charge','1000','uL')],['G3'])
F('spincoat-deposit',6,'4.4 final sentences','Spin-coating and annealing','Spin-coat precursor solution on glass, then anneal; no film thickness or atmosphere is stated.','film-spincoat',[('precursor solution aliquot','200','uL'),('spin speed','2000','rpm'),('spin duration','40','s'),('annealing temperature','80','degC'),('annealing duration','30','min')],['G3'])
F('a-structure',2,'2.1; Figure 1 a/b','Bulk A crystallographic identity','SCXRD assigns triclinic P-1, isolated pyramid-shaped [SbCl5]2− units separated by C12H28N+ cations. Zero-dimensional denotes inorganic connectivity, not particle size.','bulk-a-crystal')
F('b-structure',2,'2.1; Figure 1 c/d','Bulk B crystallographic identity','SCXRD assigns monoclinic P21/c and isolated seesaw-shaped [SbCl4]− units; SI includes two independent Sb sites.','bulk-b-crystal')
F('a-distortion',2,'2.1','Reported A distortion metrics','The main article reports the following calculated local distortion measures and mean Sb–Cl length.','bulk-a-crystal',[('bond angle variance sigma squared','5.35','deg^2'),('bond length distortion','17.46','1e-4'),('reported average Sb-Cl distance','2.56','angstrom')])
F('b-distortion',2,'2.1','Reported B distortion metrics','The main article gives one set for B, without identifying which of the two independent Sb centres supplies it. Preserve these main values and the full individual S3/S5 rows.','bulk-b-crystal',[('bond angle variance sigma squared','6.04','deg^2'),('bond length distortion','33.07','1e-4'),('reported average Sb-Cl distance','2.49','angstrom')],['C1'])
F('pxrd-consistency',2,'2.1; Figure S1','Experimental versus simulated PXRD','The author reports agreement of experimental and simulated patterns for both bulk compositions. This is phase-consistency evidence, not a supplied numerical pattern or quantified phase-purity result.','bulk-a-and-b')
F('xps-shift',2,'2.1; Figure S2','XPS shift and interpretation','B Sb 3d and Cl 2p shift to higher binding energy than A; the author attributes this to stronger Sb–Cl interaction and shorter average bonds. No fitted peak-energy table is provided.','author-bonding-interpretation',[],['C1'])
F('thermal-stability',2,'2.1; Figure S3','Thermal decomposition','Both bulk compositions are reported to decompose above 200 °C. TGA is under nitrogen; this does not establish an inert synthesis atmosphere.','bulk-a-and-b',[('reported decomposition temperature lower bound','>200','degC')])
F('b-nonemission',2,'2.2; Figure 2 a','B non-emissive outcome','Both crystals appear colorless under ambient light. B does not emit under 365 nm UV at room temperature, and no B emission spectrum was detected at 77 K. No numerical zero PLQE or instrument detection limit is supplied.','bulk-b',[('photograph UV wavelength','365','nm'),('low-temperature non-detection','77','K')],['G4'])
F('a-yellow-band',2,'2.2; Figure 2 b','Bulk A yellow emission','Under 400 nm excitation A has a broadband yellow emission. The stated Stokes shift is retained without replacing its rounded reported value.','bulk-a',[('excitation','400','nm'),('emission centre','612','nm'),('FWHM','130','nm'),('reported Stokes shift','221','nm')],['C2'])
F('a-plqe',2,'2.2; Figure S4','Bulk A absolute PLQE','Bulk A single crystals have 96.8% PLQE under 365 nm excitation at room temperature.','bulk-a',[('PLQE','96.8','%'),('PLQE excitation','365','nm')])
F('a-blue-band',2,'2.2; Figure 2 b','Bulk A blue emission/PLE','A subsidiary blue band appears under 300 nm excitation; PLE monitored at the yellow and blue bands has distinct maxima.','bulk-a',[('blue excitation','300','nm'),('blue emission','459','nm'),('PLE yellow monitor','612','nm'),('PLE yellow peak','392','nm'),('PLE blue monitor','459','nm'),('PLE blue peak','310','nm')],['C2'])
F('a-cie',2,'2.2; Figure S5','Excitation-dependent CIE','CIE chromaticity changes from (0.54,0.44) at 400 nm excitation to (0.51,0.41) at 300 nm.','bulk-a',[('first excitation','400','nm'),('first CIE x','0.54','dimensionless'),('first CIE y','0.44','dimensionless'),('second excitation','300','nm'),('second CIE x','0.51','dimensionless'),('second CIE y','0.41','dimensionless')])
F('excitation-series',2,'2.2; Figure S6','Excitation scan','Excitation wavelengths span 280–400 nm; blue-band intensity rises then declines. SI legend lists 10 nm steps.','bulk-a',[('excitation range','280–400','nm'),('legend step','10','nm')])
F('bulk-air-stability',2,'2.2; Figure S7','Bulk air stability','PLQE shows almost no change after three months in air. No numerical degradation rate, humidity or continuous irradiation condition is given.','bulk-a',[('air storage duration','3','month')],['G5'])
F('a-yellow-decay',3,'2.2 continuation; Figure 2 c','Bulk yellow decay','Biexponential fit and the source-reported average for 612 nm emission. Amplitudes are not tabulated; do not reconstruct a unique weighting.','bulk-a',[('emission monitor','612','nm'),('tau1','0.60','us'),('tau2','10.04','us'),('average lifetime','9.82','us')])
F('a-blue-decay',3,'2.2 continuation; Figure 2 c inset','Bulk blue decay','Biexponential fit and source-reported average for 459 nm emission; the fast and slow channels remain in nanoseconds.','bulk-a',[('emission monitor','459','nm'),('tau1','0.89','ns'),('tau2','3.99','ns'),('average lifetime','2.29','ns')])
F('temperature-series',4,'2.2; Figure 2 d/S8/S9','Temperature-dependent emission','At 300 nm excitation both bands increase from 77–197 K; from 197–297 K the high-energy band decreases while the low-energy band increases; above 297 K both quench. S8 extends through 337 K in 20 K steps; S9 fits 197,237,277 K spectra.','bulk-a',[('excitation','300','nm'),('measurement range','77–337','K'),('S8 step','20','K'),('crossover1','197','K'),('crossover2','297','K'),('S9 fit1','197','K'),('S9 fit2','237','K'),('S9 fit3','277','K')])
F('activation',4,'Equation 1; Figure S10 S9','Thermal activation fit','An activated intensity model gives Ea=205.26 meV. SI S10 identifies the plotted band as ES1 and labels R=0.99; no independent fit or uncertainty is supplied.','author-activation-model',[('activation energy','205.26','meV'),('S10 reported R','0.99','dimensionless')])
F('phonon-coupling',4,'Equation 2; Figure 2 e','Huang–Rhys fit','The fitted Huang–Rhys factor and phonon energy support the author interpretation of strong electron–phonon coupling and localized excitons.','author-phonon-model',[('Huang-Rhys factor S','28.74','dimensionless'),('phonon energy hbar omega','19.44','meV')])
F('photophysical-model',4,'2.2; Figure 2 f','Proposed singlet/triplet mechanism','The author maps Sb3+ 5s2 ground state 1S0 and 5s1 5p1 excited singlet/triplet levels to ES1 fluorescence and ES2 phosphorescence through structural reorganization/intersystem crossing. At 300 nm both channels emit; at 400 nm only ES2 emits. These are mechanistic assignments, not directly measured electronic coordinates.','author-photophysical-model',[('dual-channel excitation','300','nm'),('ES2-only excitation','400','nm')])
F('dft-orbitals',4,'2.3; Figure 3','Calculated orbital character','VBM states are mainly Sb 5s/Cl 3p; CBM states mainly Sb 5p/Cl 3p. The flat bands and inorganic-localization/organic-separation discussion are DFT interpretations.','author-dft-model')
F('dft-gaps',5,'2.3 continuation; PBE p.4','Calculated electronic band gaps','PBE and HSE06 gaps are calculation outputs for separately relaxed structures, not measured absorption edges or supplied relaxed-coordinate files.','author-dft-model',[('A PBE gap','3.40','eV'),('B PBE gap','3.47','eV'),('A HSE06 gap','4.40','eV'),('B HSE06 gap','4.46','eV')],['G6'])
F('parity-interpretation',5,'2.3; main p.2/p.6 symmetry discussion','Calculated parity/TDME interpretation','The author assigns equal parity at the B band edges at Gamma and much weaker TDME than A, while noting nonzero transitions away from Gamma. Both reported space groups are centrosymmetric; this narrative must not be rewritten as A lacking inversion symmetry.','author-dft-model',[('approximate TDME order difference','about 2','orders_of_magnitude')],['C3'])
F('nc-phase-size',5,'2.4; Figure 4 a/b/c; S11','Nanocrystal phase and size','Nanocrystal PXRD agrees with simulated A; TEM yields average diameter 6.43 nm. SI prints 6.43±0.17 nm but does not define that uncertainty. Broad polydispersity is reported. HRTEM labels 3.4 Å as (224).','nc-a',[('mean diameter','6.43','nm'),('SI diameter with unspecified uncertainty','6.43±0.17','nm'),('HRTEM fringe spacing','3.4','angstrom'),('assigned plane','224','identifier'),('TEM scale bar','20','nm'),('HRTEM scale bar','5','nm')],['C4','G7'])
F('nc-optical-bands',5,'2.4; Figure 4 d','Nanocrystal PL/PLE','Under 400 nm excitation the nanocrystal low-energy band is at 614 nm with 135 nm FWHM and stated 252 nm Stokes shift; a 465 nm subsidiary band appears under 300 nm excitation.','nc-a',[('yellow excitation','400','nm'),('yellow emission','614','nm'),('yellow FWHM','135','nm'),('Stokes shift','252','nm'),('blue excitation','300','nm'),('blue emission','465','nm')])
F('nc-yellow-decay',5,'2.4; Figure 4 e','Nanocrystal yellow decay','Biexponential decay and source-reported average for the 614 nm band.','nc-a',[('emission monitor','614','nm'),('tau1','0.70','us'),('tau2','10.00','us'),('average lifetime','9.72','us')])
F('nc-blue-decay',5,'2.4; Figure 4 f','Nanocrystal blue decay','Biexponential decay and source-reported average for the 465 nm band.','nc-a',[('emission monitor','465','nm'),('tau1','1.18','ns'),('tau2','12.89','ns'),('average lifetime','2.56','ns')])
F('nc-plqe',5,'2.4; S12; acquisition p.7','Dried-nanocrystal PLQE','The 89.3% absolute PLQE belongs to dried nanocrystal powders measured in the integrating sphere at 365 nm, not an explicitly measured colloid.','nc-a-dried-powder',[('PLQE','89.3','%'),('PLQE excitation','365','nm')])
F('nc-surface-interpretation',5,'2.4','Author surface/size interpretation','Similarity of crystal/nanocrystal optical behavior is attributed to electronic isolation of the inorganic units and reduced sensitivity to size/surface defects. This is not a measured universal size–property law.','author-nc-optical-interpretation')
F('nc-settling',6,'2.4 continuation; S13','Colloidal instability and dry-powder stability','As-prepared nanocrystals in toluene deposit in five minutes; dried powders retain relatively stable optical properties in air for several months. The duration of the latter and quantitative decay are not specified.','nc-a-colloid-vs-dry',[('reported deposition time','5','min')],['G5'])
F('film-spectrum-series',6,'2.5; Figure 5 a/b','Composite-film color tuning','Five ratio-series films show tunable emission under 365 nm UV. Figure 5 b spectra are explicitly assigned to the photographed films in 5 a; no numerical film PLQE, thickness, or color-coordinate table is supplied.','film-composite-series',[('excitation','365','nm')],['G3'])
F('spincoat-optics',6,'2.5; S14','Spin-coated-film emission','The separate precursor-spin-coated film emits at 611 nm with 123 nm linewidth under 365 nm excitation.','film-spincoat',[('excitation','365','nm'),('emission centre','611','nm'),('spectrum linewidth','123','nm')])
F('scintillation',6,'2.5; Figure 5 c/d and S15','Beta-excited emission','A flexible A-nanocrystal composite film and A bulk crystals show yellow radioluminescence under beta irradiation. No absolute scintillation yield, sensitivity/detection limit or radiation-aging metric is reported. The beta-film exact blue/yellow ratio is not independently stated as one of the five numbered blends.','bulk-a-and-nc-film',[('UV comparison','365','nm')],['G8'])
F('chemicals',6,'4.1','Chemical grades and suppliers','DMF, SbCl3 and tetrapropylammonium chloride: Aladdin; toluene: Sinopharm; oleic acid technical grade: Alfa Aesar; polystyrene: Sigma-Aldrich. Used as received.','study-materials',[('DMF purity','>=99.8','%'),('SbCl3 purity','99.98','%'),('tetrapropylammonium chloride purity','97','%'),('toluene purity','>=99.5','%'),('oleic acid technical-grade purity','90','%'),('PS average Mw','about 280000',None)])
F('acquisition-xray',7,'4.5','Diffraction acquisition','PXRD: PANalytical B.V. x\u2019pert3. SCXRD: Rigaku XtaLAB PRO MM007HF with Cu Kalpha at room temperature; precise crystal temperatures and refinement values are retained in S1. No numeric wavelength is supplied here.','study-acquisition')
F('acquisition-xps-tga',7,'4.5','XPS and TGA acquisition','XPS: Shimadzu Kratos AXIS SUPRA+. TGA: PerkinElmer Pyris1 under N2. No scan ramp or flow is stated.','study-acquisition')
F('acquisition-pl',7,'4.5','PL, PLE and lifetime acquisition','Edinburgh FLS980 with TCSPC and liquid-nitrogen cooler for spectra/decay/temperature. Film PL uses Zolix OmniFluo.','study-acquisition')
F('acquisition-plqe',7,'4.5','Absolute PLQE acquisition','Zolix OmniFluo with calibrated Labsphere integrating sphere; measure 365 nm baseline, then single crystals or dried nanocrystal powder.','study-acquisition',[('baseline and PLQE excitation','365','nm')])
F('acquisition-tem',7,'4.5','TEM acquisition','FEI Tecnai G2 F30 in EFTEM mode at 300 kV. No TEM grid or deposition protocol is provided.','nc-a',[('accelerating voltage','300','kV')],['G7'])
F('acquisition-beta',7,'4.5','Beta irradiation/acquisition','WASIK (USA) linear electron accelerator; the printed energy is 0.4 MeV, power 16 kW and dose rate 400 Gy/s. Ocean Optics USB2000+ fibre spectrometer collects radioluminescence.','bulk-a-and-nc-film',[('electron energy','0.4','MeV'),('accelerator power','16','kW'),('dose rate','400','Gy/s')],['G8'])
F('dft-method',7,'4.6','DFT settings','VASP PAW with PBE and HSE06; relax both lattice constants and positions until each Hellmann–Feynman force is below 0.01 eV/Å. Different k-meshes are assigned by composition, not swapped.','author-dft-model',[('plane-wave kinetic cutoff','400','eV'),('B k-mesh','2x4x4','mesh'),('A k-mesh','4x4x4','mesh'),('force stopping criterion','<0.01','eV/angstrom')],['G6'])
F('supplement-scope',7,'Associated Content','Supplied versus cited attachments','The main declares a characterization PDF, crystal-structure ZIP and beta-scintillation MP4. Only the paired 26-page PDF is present in the intake and exact-filename local search. The ZIP/video are not claimed read or recovered.','study',[],['G9'])
F('si-distortion-definitions',2,'Distortion definitions, continues S3','Distortion equations','SI defines four-coordinate angle variance with denominator 4 and five 90-degree angles; five-coordinate variance with denominator 7 and eight 90-degree angles. Length distortions use four or five squared relative deviations. Literal formulas are retained, including the selected-angle convention.','author-distortion-model',[],[],role='si')
F('si-coordinates',18,'S6 heading through S22 S7','Printed heavy-atom coordinates','S6 contains 32 heavy-atom sites for A and S7 36 for B. Positions are printed multiplied by 10^4; Ueq by 10^3 Å². No hydrogen-position or occupancy columns are supplied.','bulk-crystal-tables',[('A asymmetric-unit heavy sites','32','count'),('B asymmetric-unit heavy sites','36','count')],['G6'],role='si')
F('si-adps',23,'S8/S9 through S26','Printed anisotropic displacement parameters','All 68 heavy-atom ADP rows are retained with literal column order U11,U22,U33,U23,U13,U12 and scale to Å² of 10^-3. Off-diagonal negatives are data, not missingness. No atomistic model is qualified by extraction.','bulk-crystal-tables',[('A ADP rows','32','count'),('B ADP rows','36','count')],['G6'],role='si')

MATERIALS=[
('tpa-cl','Tetrapropylammonium chloride','C12H28NCl','organic-cation reagent','97%, Aladdin; do not substitute tetrabutylammonium.'),
('sbcl3','Antimony trichloride','SbCl3','metal halide precursor','99.98%, Aladdin; no hydrate or dissolved complex is specified.'),
('dmf','N,N-Dimethylformamide','C3H7NO','polar solvent','>=99.8%, Aladdin; quantities are solvent charges, not verified final stock volumes.'),
('toluene','Toluene','C7H8','nanocrystal antisolvent, colloid and PS solvent','>=99.5%, Sinopharm; separate physical roles and unreported amounts remain distinct.'),
('oleic-acid','Oleic acid','C18H34O2','LARP ligand additive','Technical grade,90%, Alfa Aesar; actual bound surface stoichiometry unknown.'),
('ps','Polystyrene',None,'film matrix','Average Mw approximately280000, Sigma-Aldrich; tacticity/dispersity/end groups and solution concentration not specified.'),
('blue-phosphor','Eu2+-doped barium magnesium aluminate','BaMgAl10O17:Eu2+','blue phosphor','Eu fraction, supplier, particle size and preparation not reported; a preformed input, not a new synthesis.'),
('glass','Glass substrate',None,'film support','Glass composition, cleaning, dimensions and roughness not reported.'),
('nitrogen','Nitrogen','N2','TGA atmosphere','No synthesis atmosphere implication; no gas flow or purity specified.'),
('liquid-nitrogen','Liquid nitrogen','N2','instrument cooling','PL temperature-control utility, not sample input.'),
('bulk-a',A,'C24H56Cl5N2Sb','bulk single-crystal product','P-1, isolated [SbCl5]2−; not a source-provided atomic model file.'),
('bulk-b',B,'C12H28Cl4NSb','bulk single-crystal product','P21/c, isolated [SbCl4]−; retain non-emissive result and two independent Sb sites.'),
('nc-a',A+' nanocrystals','C24H56Cl5N2Sb','nanocrystal product/film input','Composition/phase reference; ligand coverage and actual particle coordinates unknown.'),
('composite-film','Nanocrystal/phosphor/PS composite',None,'film product','Five blue/yellow mass-part compositions; no molecular formula or ordered structure assigned.'),
('spincoat-film',A+' spin-coated film','C24H56Cl5N2Sb','film product','Precursor-derived film separate from NC/PS composite.'),
]

# source role,image page,caption page,id,title,context,scope note
FIGURES=[
('main',1,1,'graphical-abstract','Metal-halide structural modulation','author-overview','Conceptual/structural summary, not a new measurement or independent sample.'),
('main',3,3,'figure-1','Two crystal structures','bulk-a-and-b','a,b A; c,d B. Crystal structure views do not provide nanocrystal surface geometry.'),
('main',3,3,'figure-2','Bulk photophysics and proposed mechanism','bulk-a-and-b','a comparison A/B; b–f A. a dishes have a 35 mm scale; this is not a crystal or nanocrystal diameter.'),
('main',4,4,'figure-3','Calculated bands, TDME and DOS','author-dft-model','a,c B; b,d A. Calculated results; no measured bandgap substitution.'),
('main',5,5,'figure-4','Nanocrystal diffraction, microscopy and optics','nc-a','a PXRD; b TEM20nm scale; c HRTEM5nm scale/3.4Å(224); d spectra; e614nm decay; f465nm decay. Shared composition, physical cross-technique batch unspecified.'),
('main',6,6,'figure-5','Composite films and radioluminescence','film-composite-series','a,b five blends in stated order, c,d A NC flexible-film beta context; its exact membership in numbered blend series is not stated.'),
('si',3,4,'figure-s1','Bulk experimental and simulated PXRD','bulk-a-and-b','Image on S3, caption on S4; no numeric intensity array supplied.'),
('si',4,4,'figure-s2','Sb 3d and Cl 2p XPS','bulk-a-and-b','Relative shifts shown without tabulated fitted peak energies.'),
('si',4,5,'figure-s3','Bulk thermal gravimetry','bulk-a-and-b','Image on S4; caption on S5; N2 atmosphere from main method.'),
('si',5,5,'figure-s4','Bulk A absolute PLQE','bulk-a','365nm excitation; 96.8% printed. Baseline/sample spectra are not digitized.'),
('si',5,6,'figure-s5','Bulk A CIE coordinates','bulk-a','Image on S5, caption on S6; two excitation conditions remain separate.'),
('si',6,6,'figure-s6','Excitation-dependent bulk PL','bulk-a','280–400nm legend in10nm increments; normalized curves not raw quantum yields.'),
('si',7,7,'figure-s7','Bulk A air-storage PLQE stability','bulk-a','Three months; no numerical humidity or fitted degradation constant.'),
('si',7,8,'figure-s8','Temperature-dependent PL','bulk-a','Image S7, caption S8;77–337K,20K steps; no raw curve arrays.'),
('si',8,8,'figure-s9','Two-Gaussian spectral fits','bulk-a','197,237,277K; fitting component areas/widths are not tabulated.'),
('si',9,9,'figure-s10','ES1 activation fit','author-activation-model','1/I versus1/T, Ea205.26meV, R0.99; fitted parameter not a synthesis condition.'),
('si',9,10,'figure-s11','Nanocrystal diameter histogram','nc-a','6.43±0.17nm; uncertainty definition/sample count not stated. Preserve broad distribution.'),
('si',10,10,'figure-s12','Nanocrystal powder absolute PLQE','nc-a-dried-powder','89.3% at365nm, dried powder per acquisition method.'),
('si',10,11,'figure-s13','Nanocrystal dispersion and powder photographs','nc-a-colloid-vs-dry','Colloidal deposition in5min; dried powder storage qualitative, not a quantified stability series.'),
('si',11,11,'figure-s14','Spin-coated film emission','film-spincoat','Ambient/365nm images and normalized PL; separate precursor route,611nm/123nm main result.'),
('si',12,12,'figure-s15','Bulk A beta radioluminescence','bulk-a','Photographs and RL trace; not composite-film data or an absolute light-yield test.')]

CONFLICTS=[
('C1','B local-geometry scope','Main p.2 gives mean Sb–Cl2.49Å, sigma²6.04 and delta d33.07×10^-4 without identifying one of the two SI Sb centres. Individual S3/S5 values remain authoritative per site; do not average all eight bonds and claim that reproduces the main mean.'),
('C2','Rounded bulk Stokes-shift numbers','Main reports221nm while its stated612nm emission and392nm PLE peak differ by220nm. Preserve all three reported numbers and do not replace the source shift with arithmetic.'),
('C3','Space-group/parity interpretation','Both P-1 and P21/c are centrosymmetric. The article emphasizes an inversion centre for B; preserve the calculated band-edge parity/TDME claim without implying A is noncentrosymmetric.'),
('C4','Nanocrystal diameter uncertainty','SI prints6.43±0.17nm without saying whether the error is SD, SEM or fit uncertainty; source also calls the distribution broad. No uncertainty type is inferred.')]
GAPS=[
('G1','Bulk growth missingness','Absolute room temperature, vessel, evaporation conditions, filtration details, isolated yield and batch identifiers are not stated.'),
('G2','Nanocrystal reproducibility limits','Growth temperature, injection rate, stir rate, aging time, filter details, wash/drying/redispersion and yield are not supplied; do not import bulk room temperature.'),
('G3','Film reproducibility limits','Absolute component masses, PS concentration, solvent amount, casting/evaporation duration/temperature, thickness, dimensions and exact beta-film ratio are missing.'),
('G4','Non-emission limit','No B PLQE value or detection limit is given; absence of detected spectrum is not a measured zero.'),
('G5','Stability scope','Bulk three-month air storage, colloidal settling and several-month dry-powder statement differ in sample state and metric; no standardized stability comparison is established.'),
('G6','Structural/calculation files missing','No local cited ZIP, complete hydrogen/occupancy model, raw reflections or relaxed DFT coordinates are available. Printed heavy-atom positions/ADPs are extracted, not qualified as an ordered or training-ready atomic structure.'),
('G7','Microscopy scope','TEM count/uncertainty definition/grid/preparation and physical cross-technique batch joins are unreported; no SAED is supplied.'),
('G8','Scintillator quantitative limits','Exposure duration, absolute light yield, calibrated sensitivity/detection limit and radiation durability not supplied; do not assign all five blend ratios to beta tests.'),
('G9','Attachment completeness','Main cites crystal ZIP and scintillation MP4 absent from paired local files; only the8+26PDF pages were read.'),
('G10','Raw curve data','Spectra, diffractograms, histograms and fitted curves are artwork without raw arrays. No plotted point is silently converted into an exact scalar.')]
