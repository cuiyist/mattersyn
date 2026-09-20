from pathlib import Path
import json, hashlib
from datetime import datetime, timezone

B=Path(__file__).resolve().parent
SOURCE=Path('[local path redacted]')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
units=[]
def add(id,category,page,locator,text,scope,claim='reported',**detail):
    pages=page if isinstance(page,list) else [page]
    u=dict(id=id,category=category,text=text,sample_scope=scope,claim_type=claim,evidence=[dict(source_id='veinot1997',pdf_page=p,printed_page=str(2116+p),locator=locator) for p in pages])
    u.update(detail); units.append(u)

# Chemical inventory includes preparation, assay media, comparative and calibration-only materials.
chemicals=[
('toluene','Reagent-grade toluene; dried over 4 Å molecular sieves and filtered before use. Dry medium for acyl-chloride routes and recrystallization solvent.','organic precursor preparation'),
('dmso','Aldrich ACS spectrophotometric-grade DMSO, used without further purification; QDOH suspension and esterification medium.','QDOH and esterification'),
('water','Water passed through Sybron-Barnstead D8902 mixed-bed ion-exchange column then D8204 activated-charcoal filter; synthesis, quench and washing medium.','general experimental inventory'),
('deuterated-solvents','Cambridge Isotope Laboratories sealed ampules, opened immediately before use; DMSO-d6 and CDCl3 are NMR solvents. D2O is the hydroxyl-exchange probe.','spectroscopy'),
('sodium-sulfide','Sodium sulfide nonahydrate, Aldrich reagent grade, used as supplied; reported 2.53 g, 11 mmol in QDOH synthesis.','QDOH'),
('hydroxythiophenol','4-Hydroxythiophenol, Aldrich reagent grade, distilled under reduced pressure immediately before use; reported 4.93 g, 39 mmol.','QDOH'),
('cadmium-acetate','Cadmium acetate, Aldrich reagent grade, recrystallized from glacial acetic acid and dried at 100 °C in vacuo; synthesis reports 5.05 g, 29 mmol. Hydration state not supplied.','QDOH'),
('imidazole','Imidazole, Aldrich reagent grade, used as supplied; excess for anhydride routes or 2.05 equivalents for acyl-chloride route.','N-acylimidazoles'),
('pyrene-acid','1-Pyrenecarboxylic acid, Aldrich reagent grade, used as supplied; 1.0 g, 4.1 mmol in acid-chloride preparation.','pyrene precursor'),
('butanoyl-chloride','n-Butanoyl chloride, Aldrich reagent grade, used as supplied; listed chemical, but explicit N-butanoylimidazole experimental preparation uses butyric anhydride.','listed inventory; alternative scheme context'),
('decanoyl-chloride','Decanoyl chloride, Aldrich reagent grade, used as supplied; input to N-decanoylimidazole.','3e'),
('thionyl-chloride','Thionyl chloride, Aldrich reagent grade, used as supplied; 20 mL for pyrene acid-chloride preparation, reagent and reaction medium.','pyrene precursor'),
('acetic-anhydride','Acetic anhydride, BDH reagent grade, used without further purification; large excess for N-acetylimidazole preparation.','3a'),
('butyric-anhydride','Butyric anhydride, BDH reagent grade, used without further purification; large excess for N-butanoylimidazole preparation.','3b'),
('benzoyl-chloride','Benzoyl chloride, BDH reagent grade, used without further purification; input to N-benzoylimidazole.','3d'),
('other-solvents','Acetonitrile and methanol form the 1:1:2 v/v acetonitrile/methanol/water trapping medium. Acetone and ether are wash solvents. Purities and suppliers for these additional solvents are not separately supplied.','synthesis and workup'),
('chloroform','CHCl3 is electronic-spectroscopy solvent for esters and TEM suspension medium for the clusters. CDCl3 is separately the 2e NMR solvent.','analytical preparation'),
('kbr','KBr pellet matrix for FTIR; matrix loading and pellet pressure not supplied.','FTIR'),
('calibration-media','TEM uses acetone/CHCl3-cleaned carbon-coated copper grids, filter paper and precision silicon grid at 21,600 lines cm−1. NMR Figure3 labels TMS and residual water; no TMS charge is given.','analytical supplies and reference signals'),
('other-solubility-media','DMF, ethanol and hexane occur in qualitative solubility comparisons; they are not automatically synthesis inputs.','solubility observations')]
for i,(name,text,scope) in enumerate(chemicals,1):
    p={4:[1,2,4],16:[1,2],19:[2,4],20:[3,6]}.get(i,1 if i<=15 else 2)
    add(f'chemical-{i:02d}','chemical_inventory',p,'Experimental Chemicals; related method/solubility sections',text,scope,chemical_key=name)

procedures=[
([1,2],'QDOH formation','Dissolve Na2S·9H2O 2.53 g (11 mmol) and 4-hydroxythiophenol 4.93 g (39 mmol) in 150 mL of 1:1:2 v/v CH3CN/CH3OH/H2O. Add to rapidly stirring cadmium acetate 5.05 g (29 mmol) in the same solvent system under N2. The receiving solution volume and addition duration are unreported.','1 / QDOH'),
([1,2],'QDOH formation','Protect from light and stir under nitrogen for 12 h; bright-yellow precipitate forms. Formation temperature is not numerically stated and must not inherit the later room-temperature drying condition.','1 / QDOH'),
([1,2],'QDOH workup','Use rotary evaporation to about one-third original volume; isolate the solid by centrifugation. Starting total volume remains unknown because the Cd solution volume is absent.','1 / QDOH'),
(2,'QDOH workup','Repeated washing/sonication/centrifugation cycles, sequentially water, acetone, then ether; dry high vacuum overnight at room temperature. Cycle count, volumes, centrifugal force/time, pressure and numeric overnight duration are not reported.','1 / QDOH'),
(2,'QDOH observation preparation','Sonicate yellow powder in DMSO to obtain transparent suspension; ambient nonopalescence contrasts with pronounced Tyndall scattering under a He–Ne laser. Concentration, sonication power/time and laser settings not supplied.','1 / QDOH dispersed in DMSO'),
(2,'1-Pyrenecarboxylic acid chloride','Dissolve 1-pyrenecarboxylic acid 1.0 g (4.1 mmol) in thionyl chloride 20 mL under dry N2; stir at room temperature for several minutes and observe olive-green precipitate. Heat at 80 °C for 3 h; precipitate redissolves.','pyrene acid-chloride intermediate'),
(2,'1-Pyrenecarboxylic acid chloride','Cool and filter; remove excess thionyl chloride completely from the filtrate in vacuo. Highly fluorescent orange-yellow solid is immediately used for 3c. Isolated mass, yield, cooling setpoint and vacuum pressure not given.','pyrene acid-chloride intermediate'),
([2,3],'N-acylimidazoles','3a and 3b: dissolve imidazole in large excess of corresponding acid anhydride; stir under dry N2 at room temperature. Prose says 30 min for both; Table1 3a says30 min and3b15 min. Absolute charges absent.','3a acetyl and3b butanoyl, separate anhydride routes'),
(2,'N-acylimidazoles','For anhydride routes remove liquid acid/excess anhydride under reduced pressure to obtain white crystals; recrystallize from toluene. Do not infer wash count or temperatures.','3a and3b'),
([2,3],'N-acylimidazoles','Other acylimidazoles: add a 50% solution of corresponding acyl chloride in dry toluene dropwise with rapid stirring to a toluene solution containing2.05 equivalents imidazole at room temperature. Percent basis and absolute volumes are unreported.','3c pyrene,3d benzoyl,3e decanoyl'),
([2,3],'N-acylimidazoles','Heat to100 °C; hot-filter the white imidazole hydrochloride precipitate. Cool filtrate in ice bath to crystallize N-acylimidazole; recrystallize once from toluene before use. Table1 total reaction-time labels are30,15,30 min for3c,3d,3e; allocation to addition/heating stages is unstated.','3c,3d,3e'),
(2,'Esterification','Representative2a: sonicated suspension of300 mg QDOH in5 mL DMSO receives5 mL DMSO solution containing170 mg acetylimidazole, dropwise with rapid stirring, in the dark under dry N2. Mixture then stirred30 min at room temperature. These exact charges belong only to2a.','2a acetyl ester'),
(2,'Esterification workup','Cool in ice bath and quench with water; centrifuge precipitate; sonicate repeatedly and consecutively in water, methanol, acetone, ether. Dry high vacuum at room temperature24 h. Water charge, cooling endpoint, centrifuge settings and wash amounts are not supplied.','2a representative ester workup; inherited framework for2b–e'),
([2,3,4],'Esterification variants','2b butanoyl,2c pyrenecarboxoyl,2d benzoyl,2e decanoyl all described under similar esterification conditions, using corresponding3b–e. Table1 gives DMSO30 min for each; their masses/concentrations and individual isolated product masses are absent. General15–30 min completion is a qualitative study-wide range, not a sampled time trajectory.','2b–e'),
(4,'NMR exchange probe','Add one drop of D2O to the QDOH DMSO(-d6 in Figure1) suspension; the8.6–9.1 ppm signal disappears. No synthesis recipe or quantitative hydroxyl-exchange rate is established.','QDOH spectroscopy before/after D2O'),
(5,'Unfunctionalized control','Unfunctionalized thiophenol-capped CdS control shows no reaction with N-acylimidazoles; aqueous workup gives unchanged clusters and organic acid. Individual reagent identity, amounts and complete preparation are not reported.','control; distinct from QDOH'),
(5,'Prolonged esterification exposure','Extending time gives no greater conversion; more than12 h exposure destroys QDOH with bulk-CdS precipitation and crystalline corresponding O,S-diester isolation. Acyl identity, exact duration, quantities and phase confirmation are not given.','failure/decomposition control; not successful ester branch'),
([2,6],'TEM preparation','Prepare fresh sonicated and centrifuged suspension of2.5 mg nanocluster in3 mL CHCl3. Place three drops on JBS-183300-mesh carbon-coated Cu grid precleaned acetone→CHCl3→acetone and air-dried. Filter paper absorbs solvent through grid; air-dry at room temperature. No centrifugation retained fraction, drop volume or sonication settings stated.','TEM1/2a–e; Figure6 specificallyQDOH'),
([2,3],'Direct esterification failure','Initial attempts using acyl chlorides destroyed the cluster. Individual acyl identity, amount, solvent, duration and temperature are not supplied. Separately, Fischer–Speier acid conditions are predicted to destroy the cluster; that prediction is not a fully described experiment.','Direct-acyl-chloride failure; distinguish predicted acidic route')]
for i,(p,loc,text,scope) in enumerate(procedures,1): add(f'procedure-{i:02d}','procedures_and_controls',p,loc,text,scope)

methods=[
(2,'Spectroscopy','IR recorded as KBr pellets using Mattson3000 FTIR; no resolution or scan count.','1 and2a–e'),
([2,3,4],'Spectroscopy; Table1; Figures1–3','400 MHz1H NMR using source-spelled Brucker ARX400 instrument. DMSO-d6 for QDOH and esters except2e inCDCl3. Fig2 explicitly3e inDMSO-d6. Solvents of other3a–d are not individually specified.','1,2a–e,3a–e'),
([2,5],'Electronic spectroscopy; Figure5','HP8452 diode-array UVvis in1 cm quartz cuvettes; esters inCHCl3 andQDOH in methanol. Figure5QDOH concentration10^-4 M; molarity basis for polydisperse cluster not supplied.','UVvis1 and2a–e'),
([2,6],'Electron Microscopy; Figure6','Philips EM-301 TEM, precision silicon-grid calibration21,600 lines cm−1; Figure6 magnification290,000× and scale bar6 nm. Accelerating voltage, particle count and exact image-analysis protocol not given.','TEM1 and2a–e'),
(5,'NMR conversion analysis','Esterification percentages estimated from residualOH/aromatic-proton integration ratio. These are site conversions, not isolated mass yields or inorganic core yields.','2a–e'),
([5,6],'Electronic sizing; Table3','Optical diameter estimates attributed to tight-binding analyses in ref13; paper supplies no explicit usable Eq1 despiteTable3 title.2c is unassignable by this method because pyrene absorbs intensely.','author-calculated sizes1,2a,b,d,e;2c missing')]
for i,(p,loc,text,scope) in enumerate(methods,1): add(f'method-{i:02d}','characterization_methods',p,loc,text,scope)

names={'1':'QDOH phenolic CdS cluster','2a':'acetyl ester of QDOH','2b':'butanoyl ester of QDOH','2c':'pyrene-1-carboxoyl ester of QDOH','2d':'benzoyl ester of QDOH','2e':'decanoyl ester of QDOH','3a':'N-acetylimidazole','3b':'N-butanoylimidazole','3c':'N-pyrene-1-carboxoylimidazole','3d':'N-benzoylimidazole','3e':'N-decanoylimidazole'}
nmr=[
('1','CH3CN/CH3OH/H2O',720,None,'6.0–7.3 (m,4H,arom);8.6–9.1 (m,1H,OH)'),
('2a','DMSO',30,95,'6.0–7.7 (m,4H,arom);2.2 (s,3H,CH3)'),
('2b','DMSO',30,97,'6.0–7.7 (m,4H,arom);2.5 (br,2H,alpha-CH2);1.6 (br,2H,beta-CH2);0.95 (br,3H,CH3)'),
('2c','DMSO',30,95,'6.4–9.5 (m,arom)'),
('2d','DMSO',30,100,'6.4–8.2 (m,arom)'),
('2e','DMSO',30,100,'6.4–7.3 (m,4H,arom);2.5 (br,2H,alpha-CH2);1.7 (br,2H,beta-CH2);1.2–1.5 (br,12H,aliph);0.91 (br,3H,CH3)'),
('3a','acetic anhydride',30,100,'8.4 (s,1H,ImC2);7.7 (s,1H,ImC4);7.1 (s,1H,ImC5);2.2 (s,3H,CH3)'),
('3b','butyric anhydride',15,50,'8.4 (s,1H,ImC2);7.7 (s,1H,ImC4);7.1 (s,1H,ImC5);3.1 (t,2H,alpha-CH2);1.8 (m,2H,beta-CH2);1.0 (t,3H,CH3)'),
('3c','toluene',30,65,'8.2–8.5 (m,10H,ImC2+pyrene);7.8 (s,1H,ImC4);7.2 (s,1H,ImC5)'),
('3d','toluene',15,100,'8.2 (s,1H,ImC2);7.7 (s,1H,ImC4);7.2 (s,1H,ImC5);7.8 (d,2H,phenyl2,6);7.6 (m,2H,phenyl3,5);7.7 (s,1H,phenyl4);2.6 (s,3H,CH3) [source anomaly preserved]'),
('3e','toluene',30,100,'8.4 (s,1H,ImC2);7.7 (s,1H,ImC4);7.0 (s,1H,ImC5);3.0 (t,2H,alpha-CH2);1.7 (m,2H,beta-CH2);1.2–1.4 (br,12H,aliph);0.9 (t,3H,CH3)')]
for c,sol,t,y,peaks in nmr:
    add('table1-'+c,'table_rows',3,'Table1 row'+c,'Reaction solvent/time and400 MHz1H NMR; all printed signals retained.',names[c],reaction_solvent=sol,reaction_time=dict(value=t,unit='min',raw_text='12 h' if c=='1' else str(t)+' min'),yield_or_conversion_percent=y,quantity_kind='phenolic_site_conversion' if c.startswith('2') else 'precursor_yield' if c.startswith('3') else 'not_reported',nmr=dict(unit='ppm',signals=peaks))

ir={
'1':'3301(s,vbr,O–H stretch);1870 and1730(w,1,4-disubstituted-phenyl overtone);1636(m);1598(s);1488(s,ringC=C);1429(s);1359(m);1170(s,br,phenyl–O);1088(m);1009(m,phenyl–S);819(s,phenylC–H out-of-plane);634(m);510(m)',
'2a':'3400(w,vbr,residualOH);3060(w,aromaticC–H);2931(w,aliphaticC–H);1486(s,ringC=C);1758(vs,C=O);1582(w);1427(w);1369(s);1223(s,br,phenyl–O);1085(m);1013(s,phenyl–S);911(w);840(m);820(m,phenylC–H out-of-plane);797(w);510(m)',
'2b':'3375(vw,vbr,residualOH);3090(w,aromaticC–H);2965(m,br,aliphaticC–H);2934(w,shoulder,aliphaticC–H);2875(w,aliphaticC–H);1751(vs,C=O);1580(vw);1539(vw);1485(vs,ringC=C);1245–1203(vs,br,phenyl–O);1167(vs);1080(m);1013(m,phenyl–S);836(w,phenylC–H out-of-plane);749(vw);653(vw);510(w)',
'2c':'3129,3047,2973(w,aromaticC–H);1720(s,C=O);1583(m);1490(vs,ringC=C);1364(m);1234(s,br,phenyl–O);1205(shoulder);1167(shoulder);1066(m);842(s);818(s,phenylC–H out-of-plane);748(w);712(w);645(w);511(w)',
'2d':'3400(vw,vbr,residualOH);3060,3033(w,aromaticC–H);1736(vs,C=O);1673(m);1600(w);1485(s,ringC=C);1451(m);1269(vs,br,phenyl–O);1201(vs);1166(s,shoulder);1061(s);1013(m,phenyl–S);902(w);876(w);822(w,phenylC–H out-of-plane);705,686(vs,sharp,monosubstitutedphenylC–H out-of-plane);634(vw);511(m)',
'2e':'3060(vw,aromaticC–H);2925(s,aliphaticC–H);2852(s,br,aliphaticC–H);1754(s,C=O);1579(w);1537(w);1486(s,ringC=C);1458(m);1377(w);1170–1081(s,br,manybands);1012(m,phenyl–S);915(w);840–802(w,br);736(vw);510(m)'}
for c,peaks in ir.items(): add('table2-'+c,'table_rows',3,'Table2 row'+c,'Complete printed FTIR feature list; author assignments retained.',names[c],unit='cm^-1',signals=peaks,preparation='KBr pellet')
add('table2-legend','table_metadata',3,'Table2 footnote','Intensity:vs very strong,s strong,m medium,w weak,vw very weak. Width:vbr very broad,br broad,shrp sharp,shldr shoulder;arom aromatic,aliph aliphatic.','all Table2 rows')
for c,lam,calc,tem in [('1',390,24,30.4),('2a',400,25,27.3),('2b',420,27,24.7),('2c',[356,420],None,26.3),('2d',350,19,28.2),('2e',420,27,28.2)]:
    add('table3-'+c,'table_rows',3,'Table3 row'+c,'Reported electronic absorption and measured/author-calculated cluster diameters.',names[c],wavelength_nm=lam,wavelength_assignment='pyrene pi–pi* range; CdS masked' if c=='2c' else 'CdS band-to-band absorption',author_calculated_diameter_angstrom=calc,TEM_diameter_angstrom=tem,calculation_basis='tight-binding band theory ref13; Eq1 referenced in heading but absent in supplied main',TEM_uncertainty='not specified per row; QDOH additionally discussed p6')

obs=[
(2,'QDOH characterization','Isolated yellow solid2.23 g. Under assumed quantitative sulfide yield, authors state20 mol% cluster sulfur from thiol. This is an assumption-dependent interpretation, not measured elemental composition.','QDOH','author_calculation'),
(2,'QDOH characterization','Prose1H NMR:6.0–7.3ppm(m,4H),8.6–9.1ppm(m,1H,D2O exchangeable). IR(KBr):3302cm−1(s,broadOH),1870/1734(w,ring overtone),819(s,ringCH). UVvis295nm(edge),305nm(shoulder).','QDOH','reported'),
([3,4],'QDOH mass accounting','A separate author calculation assumes quantitative limiting-sulfide yield and assigns excess mass to thiophenolate cap;34mol% of total sulfur is then assigned to thiol. Assuming core specific gravity4.8 and30Å diameter gives~130caps,22Å²/cap and2827Å² spherical surface area. Keep separate fromp2 20%.','QDOH author geometrical model','author_calculation'),
(4,'Surface coverage comparison','Same calculation applied to prior unfunctionalized(ref7) and pyridyl-functionalized(ref6) elemental analyses gives25 and22Å²/cap respectively. These are cited comparative systems, not newQDOH measurements.','prior papers only','citation_only'),
(4,'NMR discussion','QDOH broadened signals, no non-solvent signals upfield of5ppm; sharp water singlet possibly chemisorbed. Aromatic6.0–7.3 andOH8.6–9.1 integrate4:1; D2O removes the latter. Broad structure interpreted as multiple environments.','QDOH','reported_with_author_interpretation'),
(4,'IR discussion','RingC=C1488,1,4-disubstituted-ring overtone1870/1734 andout-of-plane819cm−1;OH3301 andphenylOH deformation assigned1013cm−1. Absence ofca2580cm−1S–H stretch interpreted as sulfur-bound thiolate.','QDOH','reported_with_author_interpretation'),
(4,'IR comparison','Unfunctionalized thiophenol-capped CdS comparator has686/734cm−1 monosubstituted-ring features and weak four-band overtone1730–1950cm−1, distinct fromQDOH.','prior unfunctionalized comparator','citation_context'),
([4,5],'NMR interpretation','Ester spectra retain broad aromatic signal with structure; residualOH in some samples indicates incomplete conversion.3a–e imidazole assignments in discussion~7.0(C4),7.7(C5),8.4(C2) differ fromTable1C4/C5 labels.','2a–e and3a–e','author_interpretation'),
(5,'Control interpretation','No acylimidazole reaction in unfunctionalized control is interpreted by authors as excluding simple chemisorption onto theCdS core; not direct atomically resolved proof.','unfunctionalized control','author_interpretation'),
(5,'IR ester discussion','Esters develop carbonyl near1750cm−1 and decreased but not always absentOH near3300cm−1, consistent with95–100%conversion. Weak-to-medium sharp~1015 is assignedS-coupled ring mode; broad1200–1270 phenyl–O antisymmetric stretch.','2a–e','reported_with_author_interpretation'),
(5,'IR ester discussion','2c1720 and2d1736cm−1 carbonyl frequencies lie below aliphatic counterparts; authors attribute this to aromatic resonance coupling.','2c and2d','author_interpretation'),
([5,6],'Optical analysis','Authors assignQDOH band-to-band onset~390nm,bandgap3.19eV,bulkCdS2.53eV andconfinementshift0.66eV, obtaining24Å diameter from cited tight-binding theory. Values are source-reported calculations, not a new model fit.','QDOH','author_calculation'),
(6,'Optical comparison','Authors describe ester optical diameters as identical to startingQDOH except masked2c and infer preserved cluster integrity/no fusion; Table3 actually lists19–27Å versus24ÅQDOH. Retain wording as qualitative interpretation, not exact equality.','2a,b,d,e compared with1','author_interpretation'),
(6,'Optical interference','Intense pyrene pi–pi* transitions maskCdS absorption for2c;Table3 gives356–420nm and no optical size. Do not relabel this asCdS bandgap or derive a diameter.','2c','reported'),
(6,'TEM discussion; ref15','Clusters and esters agglomerate into larger spheroids amid individual clusters. Histogram discussion givesQDOH~30.4±7Å; reference15 saysprecision limited by microscope resolution. Distribution/uncertainty type and particle count are not specified.','1 and2a–e general;numericQDOH','reported'),
(6,'TEM discussion; Figure6','Body saysFigure6 contains a large1100Åaggregate with individual clusters. Caption givesQDOH driedCHCl3suspension,290000×;printedbar6nm appears incompatible with a1100Å feature within this field. Preserve text andimage separately; do not silently correct.','Figure6QDOH','reported_conflict'),
([3,6],'Solubility','QDOH insoluble inwater,ether,hexane; transparent suspensions inDMSO/DMF,also methanol/ethanol. It is reported insoluble inCHCl3, although TEMuses sonicated suspension.','QDOH','reported_qualitative'),
(6,'Solubility','All esters2a–e soluble inCHCl3 but not lower alcohols.2b/2e soluble inacetone;2e soluble inether;2a/2d insoluble inboth.2e losesDMSOsolubility. Other ester/solvent combinations are not individually resolved.','2a–e','reported_qualitative'),
(3,'Reference10 definition','Soluble means clear transparent nonsettling suspensions, nonopalescent inambientlight and not separable byconventionalcentrifugation, yet laserTyndall-positive. Do not equate with molecular dissolution.','source-wide terminology','author_definition'),
([1,6],'Application outlook','Surface-functionalized dots proposed for covalent molecular coupling and device/composite applications; no functioning electronic device or measured deviceperformance is reported here.','prospective use','author_outlook')]
for i,(p,loc,text,scope,claim) in enumerate(obs,1): add(f'observation-{i:02d}','observations_and_author_interpretations',p,loc,text,scope,claim)

figures=[
('figure-1',4,'Figure1a/b','400MHz1H NMR ofQDOH inDMSO-d6 before andafteroneD2Odrop. A/B arechemical probe states,not independent synthesis batches.','QDOH;D2O exchange pair','experimental_spectra'),
('figure-2',4,'Figure2','400MHz1H NMR ofN-decanoylimidazole3e inDMSO-d6;asteriskDMSOresidual.','3e','experimental_spectrum'),
('figure-3',4,'Figure3','400MHz1H NMR ofdecanoylQDOHester2e inCDCl3;asteriskCHCl3residual,double-daggerwater,daggerTMS.','2e','experimental_spectrum'),
('figure-4',5,'Figure4','FTIR of2e inKBr. Axis ispercenttransmittance versuswavenumber;captioncallsabsorption. Retainoriginalaxis ratherthaninvertingorlabelingabsorbance.','2e','experimental_spectrum'),
('figure-5',5,'Figure5','UVvis of10^-4M QDOH inmethanol,1cm path;absorbancevswavelength. No rawcurve digitization performed.','QDOH opticalspecimen','experimental_spectrum'),
('figure-6',6,'Figure6','TEM ofdriedQDOH suspension(CHCl3) oncarbon-coatedCu;290000×;6nmbar;sourcebodyaggregate1100Åflagged.','QDOH TEMspecimen','experimental_image'),
('scheme-1',3,'Scheme1','Generalimidazole+RCOClintoluene→N-acylimidazole3+imidazoliumchloride;3+QDOH→ester2+imidazole. The commoncartoon doesnotreplace explicit anhydride routesfor3a/3b.','reaction families3a–e→2a–e','author_reaction_scheme'),
('structure-illustration',2,'Unnumbered structures1 and2','SchematicphenolicCdSdot1 andesterifieddot2withfivebranches;substituentsaacetyl,bbutanoyl,cpyrenecarboxoyl,dbenzoyl,edecanoyl. Branchcount andcircle areillustrative,notmeasuredligandcoverage or atomicstructure. Ligand sulfur linkage isdiscussedintext butnotatomicallyresolvedbycartoon.','1 and2a–e','author_schematic')]
for id,p,loc,text,scope,claim in figures:add(id,'figures_and_schemes',p,loc,text,scope,claim)
for n,desc in [(1,'Reaction solvents/times,precursoryields orphenolicsiteconversions,andall400MHz1HNMRdata'),(2,'AllFTIRfeaturesandassignmentsfor1/2a–easKBrpellets'),(3,'UVvisfeatures,authorcalculateddiameters,andTEMdiameters;2c opticalsizemissing')]:add(f'table-{n}','table_inventory',3,f'Table{n}',desc,'table rows itemized separately')
add('equation-inventory','equations',3,'Table3 heading','Heading refers toCalculated(Eq1), but no numberedEq1 or explicit sizingformula appears on any ofthe sixsuppliedmainpages. Do not reconstruct an equation fromcitedliterature withoutseparateverification.','source completeness','unresolved')

conflicts=[
([1,2],'Cd precursor quantity','Cadmiumacetate5.05g/29mmol implies~174g/mol, incompatiblewithcadmiumacetate formula evenbeforeunspecifiedhydration. Preservebothreportedvalues; nophysicalcharge repair.','QDOH'),
([2,3],'Sulfur accounting','20mol%thiol-derivedsulfur(p2) versus34mol%(p3discussion), bothassumingquantitativesulfideyield. Distinctsource-labelledauthorcalculations.','QDOH'),
([2,3,5],'UVvis feature identity','Experimental295nmedge/305nmshoulder versusTable3/p5~390nmband-to-bandonset. No samefeatureassignment orsilentmerge.','QDOH'),
([2,3],'3b reaction time','Anhydrideprose30min versusTable1 3b15min. Not selectable provenalternatives.','3b'),
(3,'3d NMR','Benzoylimidazole3d table contains2.6ppm(s,3H,CH3) althoughbenzoylstructurehasnomethyl; preserve asanomaly.','3d'),
([3,5],'Imidazole NMR assignments','Table1labels~7.7ImC4 and~7.0–7.2ImC5;bodylabels~7.0C4 and~7.7C5. Do not silentlyswap.','3a–e'),
([2,3,4],'QDOH IR differences','ExperimentalOH3302 vsTable2/discussion3301;ring1734prose vs1730Table2. These closelyspacedsourcevalues remainlabelled,notaveraged.','QDOH'),
([3,4,5],'~1010cm−1 IR assignment','QDOHTable21009phenyl–S;bodyp4calls1013phenolicOHdeformation;estersnear1013 anddiscussion~1015S-coupled mode. Retainsourceandmaterialscope.','1/2a–e'),
([3,6],'Optical size interpretation','Authorclaimidenticaldiameters versusTable3numeric19–27Å andQDOH24Å; qualitativeinterpretation isnotexactnumericidentity.','1/2a,b,d,e'),
(6,'Aggregate scale','Body1100Åaggregate versusFig6visible6nmbar/field;preserverawtextandimage andflagincompatibilityratherthaninventingcorrectedsize.','QDOH Fig6'),
(6,'TEM uncertainty typography','30.4±7 followedbysuperscript15referencesnote15;not±715. Note15isresolution-limitedprecision,notdeclaredSD/SEM.','QDOH'),
(3,'Missing equation','Table3headingreferencesEq1,noneprovidedintheinspectedmain.','sizing model'),
([2,6],'Suspension versus dissolution','QDOHreportedCHCl3insolublebutTEMexplicitlyusesCHCl3suspension; do notclassifythisasprovensolubilityorinventsolventsubstitution.','QDOH'),
(2,'50% stock basis','Acylchloride50%solutionintoluene hasunreportedmass/volume basis; do not convertto molarity.','3c–e'),
([1,2],'Missing receiver volume','150mL applies toS/ligand feedonly;Cdcounter-solution volumeunknown,sototalvolumeandone-thirdconcentratedvolumeareunresolved.','QDOH'),
([2,3],'General versus representative charges','300mgQDOH/170mg3a andtwo5mLDMSOquantitiesonlyexplicitfor2a;do nottransfer170mg or molarityto2b–e.','ester branches'),
([2,3,5],'Yield semantics','2a–epercentsareOHesterificationconversionsfromNMR;3a–epercentsareprecursoryields;1hasblankTable1percentand2.23gisligand-bearingisolatedsolid.','all'),
([2,3],'Scheme versus actual preparation','Scheme1generalacidchloride route doesnotassert3a/3bwereprepared thatway; explicitprose/tableuseanhydrides. n-Butanoylchlorideislistedbutnotanindependentlyquantifiedrun.','3a/3b'),
([1,2,3,4,5,6],'Measurement absence','NoXRD,SAED,Raman,quantitativePLspectrum/QY,atomisticstructure,phase-specificlatticeassignmentorcrystalCIFreported. Fluorescentpyreneintermediateisanobservation,notQDPLmeasurement.','inspected supplied main')]
for i,(p,loc,text,scope) in enumerate(conflicts,1):add(f'conflict-{i:02d}','conflicts_and_semantic_hazards',p,loc,text,scope,'unresolved_or_semantic_guardrail')

refs=[
(1,1,'AlivisatosJPhysChem1996,100,13266;WellerAngew1993,32,41;SchmidChemRev1992,92,1709;Steigerwald/BrusAccChemRes1990,23,183;HengleinChemRev1989,89,1861.','Backgroundreviews; not inspected original sources.'),
(2,1,'Merkt/SikorskiSemiconductSciTechnol1990,5,182;FultonNature1988,346,408 asprinted;Zorman/Ramakrishna/FriesnerJPhysChem1995,99,7649.','Proposeddevicecontext; printedbibliography not independently corrected.'),
(3,1,'Torimoto/Maeda/Maenaka/YoneyamaJPhysChem1994,98,13658.','Earlierfunctionalizednanocrystals; citationonly.'),
(4,1,'Nosaka/Ohta/Fukuyama/FujiiJColloidInterfaceSci1993,155,23.','Earlierfunctionalizednanocrystals; citationonly.'),
(5,1,'Torimoto/Uchida/Sakata/Mori/YoneyamaJACS1993,115,1874.','Earlierfunctionalization andNMRcomparison4-hydroxythiophenol-cappedPbS; separate material context.'),
(6,1,'Noglik/PietroChemMater1994,6,1593.','EarlierpyridylCdS,modifiedkinetictrapping andstability/surfacecoveragecomparison. Upstreampreparationnotfullyinspected.'),
(7,1,'Herron/Wang/EckertJACS1990,112,1322.','Kinetictrappingandunfunctionalizedthiophenol-cappedCdS; citationonly,also repeated14b.'),
(8,1,'Peng/Wilson/Alivisatos/SchultzAngew1997,36,145;Noglik/PietroChemMater1995,7,1333;Lawless/Kapoor/MeiselJPhysChem1995,99,10392;Brust/Bethell/Schiffrin/KielyAdvMater1995,7,795;Majetich/Carter/McCulough/Seth/BelotZPhysD1993,26,210.','Aggregation/couplingcontext.8b ispart2ofthisseries, notcurrentpaperSI.'),
(9,3,'Kronman/Holmes/RobbinsJBiolChem1971,246,1909;Hirayama/Matsuda/Takeda/Maenaka/TakatsukaBiochemBiophysActa1975,384,127.','N-acylimidazoletyrosinetagging rationale; do not importbiologicalexperimentalconditions.'),
(10,3,'Explanatorynote defining soluble suspensions.','Scientificdefinitionfullycapturedobservation19;notanexternalpaper.'),
(11,4,'Sachleben/Wooten/Emsley/Pines/Colvin/AlivisatosChemPhysLett1992,198,431.','BroadenedNMRin20Åthiophenol-cappedCdS; citedcomparisononly.'),
(12,4,'Majetich/Carter/Belot/McCulloughJPhysChem1994,98,13705.','BroadenedNMRinn-butanethiolate-cappedCdSe; citedcomparisononly.'),
(13,6,'Wang/HerronPhysRevB1990,42,7253;Wang/HerronJPhysChem1991,95,525;Vossmeyer/Katsikas/Giersig/Popovic/Diesner/Chemsddine/Eychmüller/WellerJPhysChem1994,98,7665.','Tight-bindingopticalsizebasis; originalsnotread; noEq1reconstructed.'),
(14,6,'Colvin/Goldstein/AlivisatosJACS1992,114,5221;Herron/Wang/EckertJACS1990,112,1322;Ogata/Hosokawa/Tatsuhiko/Wada/Sakata/Mori/YanagidaChemLett1992,1665 asprinted.','Priorlow-boilingsolventsolubleCdScontext; citedonly.'),
(15,6,'Explanatorynote:reportedprecisionlimitedbymicroscoperesolution.','QualifiesQDOH30.4±7Å; notastatisticaldefinition.')]
for n,p,bib,context in refs:add(f'reference-{n:02d}','reference_contexts',p,f'Reference{n}',context,'cited source or explanatory note','citation_only' if n not in[10,15] else 'author_note',bibliography_as_source=bib)

intuition=[
([1,2,3],'Mild functionalization','TheauthorschooseN-acylimidazolesbecauseacidic/basic/oxidizing/thermalconditionscanbreakCd–thiolateclustersandacylchloridesfailed. MildphenolicacylationtargetsOHwhileretainingthetrappingcap.','author_interpretation'),
([3,4],'Two equivalents imidazole','SecondimidazoleequivalentacceptsHClandprecipitatesasimidazoliumchloride;2.05equivalentsexperimentalversus2equivalentsdiscussionisnotastatedoptimizationstudy.','author_interpretation'),
([3,6],'Surface-controlled dispersibility','HydrogenbondingisproposedtoexplainQDOHalcoholsolubility;esterificationremovesOHcharacterandlongeraliphaticchainsalterorganic-solventcompatibility. Qualitativecomparisonsarenotasolvationmodel.','author_interpretation'),
([4,5,6],'Converging evidence','NMRexchange/integration,IRcarbonyl/OHfeatures,TEMandopticalchangesjointlysupportsurfacefunctionalizationwithoutmajorclusterfusionunderbriefconditions;noneprovidesatomiccoordinatesorcompleteinterfacialcoverage.','author_interpretation'),
(5,'Limited reaction window','Moretimedoesnotguaranteemoreconversion:>12hcausesdecompositionandO,S-diesterformation. Do notturnthatthresholdintoanoptimizedendpointorassumethesamefailureforeachester.','author_interpretation'),
([1,6],'Future scope','Authorsproposechromophores,luminophores,wiresanddevices;currentpaperdemonstrateschemicalhandlesandchangesindispersibility,notelectronic-deviceoperation.','author_outlook')]
for i,(p,loc,text,claim) in enumerate(intuition,1):add(f'intuition-{i:02d}','source_specific_intuition',p,loc,text,'source-wide chemical rationale',claim)

ids=[u['id'] for u in units]
assert len(ids)==len(set(ids))
assert all(u['evidence'] and all(1<=e['pdf_page']<=6 for e in u['evidence']) for u in units)
categories={k:sum(u['category']==k for u in units) for k in sorted({u['category'] for u in units})}
out=dict(schema_version='1.0',source_id='veinot1997',doi='10.1021/cm970189m',title='Surface Functionalization of Cadmium Sulfide Quantum-Confined Nanoclusters. 3. Formation and Derivatives of a Surface Phenolic Quantum Dot',authors=['Jonathan G. C. Veinot','Madlen Ginzburg','William J. Pietro'],journal='Chemistry of Materials',year=1997,volume=9,pages='2117–2122',dates=dict(received='1997-04-02',revised='1997-07-25',advance_abstract='1997-09-01'),source_basename=SOURCE.name,source_sha256=sha(SOURCE),review_scope='supplied_main_only_si_unverified',status='independent_supplied_main_text_and_visual_review_complete',supporting_information=dict(status='not_located_or_verified_by_this_audit',note='Local SI matching delegated separately by root; this audit inspected only the supplied six-page main.'),page_review=[dict(pdf_page=n,printed_page=2116+n,text_read=True,visual_read=True,text_sha256=sha(B/f'plain-page-{n}.txt'),image_sha256=sha(B/f'main-{n:02d}.png')) for n in range(1,7)],unit_count=len(units),category_counts=categories,units=units,scope_limits=['No cited original reference was opened in this bounded audit. Bibliographic identity and legacy typo corrections were not externally verified.','All spectra, table cells, cartoons and source-reported numbers are inventoried; original curve data were not digitized and image pixel dimensions were not converted into repaired sizes.','No canonical record, training status, Site, publication, queue or SI status is promoted by this source audit.','No exact crystal phase, lattice/interface coordinates, XRD, SAED, Raman or quantitative QD photoluminescence data are established in the supplied main.'])
(B/'source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
md=['# Veinot 1997: independent source audit','',f"All six supplied main pages were read in text and visually inspected. **{len(units)} source units** have stable IDs, page locators, claim types and sample scope. Main-only review; SI remains unverified by this audit.",'',f"Source SHA-256: `{out['source_sha256']}`",'', '## Experimental scope','', '- QDOH kinetic trapping, precursor conditioning, workup and dispersion; five ester derivatives 2a–e.', '- Pyrene acid chloride and five N-acylimidazole preparations 3a–e, including separate anhydride and acyl-chloride pathways.', '- Representative acetyl charges are kept distinct from incompletely quantified other esters; control/no-reaction and prolonged-decomposition observations are separate.', '- Six figures, three complete tables, Scheme 1, unnumbered structures 1/2, all 15 reference entries/notes and the absent Eq 1 reference are inventoried.','', '## Important unresolved source details','']
md += ['- **'+u['id']+'** '+u['text'] for u in units if u['category']=='conflicts_and_semantic_hazards']
md += ['', '## Inventory counts','']+[f'- {k}: {v}' for k,v in categories.items()]+['','## Review limitations','']+['- '+x for x in out['scope_limits']]+['','The detailed source-audit.json retains all NMR/IR table signals, complete Table3 numeric rows, figure/sample joins, preparation details and exact source locators. Reproducible private generator: build_source_audit.py.']
(B/'source-audit.md').write_text('\n'.join(md)+'\n',encoding='utf8')
print(json.dumps(dict(source_sha256=out['source_sha256'],unit_count=len(units),categories=categories),indent=2))
