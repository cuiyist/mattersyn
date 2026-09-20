"""Independent supplied-main audit, every page text and visual; no Site mutation."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
B=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
I=read(B/'source-identity.json');units=[];counts=Counter()
def add(category,text,page,locator,scope='Study-wide source context; physical specimen identities unresolved',claim='reported',**kw):
 counts[category]+=1
 x={'id':f'{category}-{counts[category]:02d}','category':category,'text':text,'sample_scope':scope,'claim_type':claim,'evidence':[{'source_id':'yao1998','pdf_page':page,'printed_page':594+page,'locator':locator}],**kw};units.append(x);return x
add('identity','Yao, Takada and Kitamura; clean article title is Electrolyte Effects on CdS Nanocrystal Formation in Chelate Polymer Particles: Optical and Distribution Properties. Langmuir1998,14(3),595–601; terminal article codeLA970480G.',1,'Title, byline, journal header/footer; closing code p7')
add('identity','Received May8,1997; final form November14,1997; published on Web February3,1998.1997 article-code year and received dates do not replace1998 publication.',1,'Title/date/footer')
add('identity','Seven supplied main pages; two local byte-identical mains, one content. SI not located or verified by targeted local filename/catalog/hash/log checks.',7,'Supplied document scope and local source-identity.json','Main/SI availability','curation_scope')
chem=[
('Chelex100,200–400mesh, Analytical Grade, Bio-Rad; styrene–divinylbenzene copolymer with iminodiacetate ligands –CH2N(CH2COO−)2. Host polymer, not measured atomic CdS structure.','Materials; reagent and polymer identity'),
('Ion-exchange fixed-charge capacity2.0mequiv/g dry or0.4mequiv/mL wet, from manufacturer instruction manual ref18; polymer charge-density property is not product yield.','Materials; ref18'),
('Distilled water used for resin soaking/washing, Cd and sulfide aqueous stocks, no-salt pretreatment, final workup, and wet optical dispersion. Water quality beyond distilled not reported.','Materials; preparation; measurements'),
('Methanol wash follows water soaking in host conditioning. Amount and wash duration unspecified.','Materials'),
('Aqueous HCl2M follows methanol in resin conditioning; stock volume and exposure duration unspecified.','Materials'),
('Aqueous NaOH2M follows acid wash, then thorough distilled-water washing. Eluent pH approximately10; not a measured synthesis pH.','Materials'),
('Ethanol treats washed host before vacuum drying/storage and is used after water in final product workup. Amount, wash count and duration not supplied.','Materials and product workup'),
('Cadmium acetate dihydrate Cd(CH3COO)2·2H2O, GR grade, Kanto Chemical, as received; aqueous Cd loading stock8.4×10−3M,5.0mL.','Materials and Cd loading'),
('Sodium sulfide nonahydrate Na2S·9H2O, GR grade, Wako Pure Chemicals, as received; freshly prepared aqueous Na2S3.8×10−4M,100mL addition.','Materials and sample a'),
('NaCl, GR grade, Kanto Chemical, as received. Sample b pretreatment10mL of0.5M solution,10min; post-addition mixture concentration is ambiguous.','Materials and sample b'),
('LiCl, KCl and tetramethylammonium chloride are alternative1:1electrolytes at nominal0.5M in direct footnote25 comparisons; grades, amounts and complete recipes absent.','Reference note25'),
('Aqueous Na2S species are described as Na+,HS− andOH− under the present conditions. HS− is the reactive diffusant, not a separate charged sodium hydrosulfide feed.','Reference note15'),
('DowexA-1 is a cited resin comparison for Na+ diffusion; Nafion, ethylene–methacrylic-acid polymer, zeolite, porous glass, clay and PbS are introductory prior systems, not synthesized materials in this paper.','Introduction and refs8–14; sample b rationale')]
for i,(t,l) in enumerate(chem):add('chemical_inventory',t,4 if i==10 else 1 if i in [11,12] else 2,l)
procedures=[
('Condition the host: soak Chelex in distilled water; wash successively methanol→aqueous2M HCl→aqueous2M NaOH→thorough distilled water; eluent pH~10. Authors state careful cleaning is necessary for reproducibility.','Materials','Host polymer preprocessing'),
('Treat cleaned host with ethanol, dry under vacuum, then store. Drying temperature/time/pressure and storage temperature/time/atmosphere/container unreported.','Materials','Dry cleaned Chelex host'),
('Load0.107g dry polymer in5.0mL8.4×10−3M aqueous cadmium acetate. Sonicate10min, then store2days at room temperature; sonication power and temperature not specified.','Cd loading','Shared Cd-loaded host preparation'),
('All Cd2+ judged incorporated because supernatant did not form CdS upon HS− challenge. This qualitative test has no detection limit and is not a calibrated100% uptake measurement.','Cd loading','Cd loading supernatant assay'),
('Adsorbed Cd2+/total resin adsorption capacity is reported about0.4. Wash Cd-loaded particles with distilled water several times; count, amount and separation apparatus unspecified.','Cd loading','Shared Cd-loaded host'),
('Sample a: disperse Cd-loaded particles in10mL distilled water for10min. The paper does not separately repeat the polymer mass in this step.','Sample a','Sample a; no added NaCl'),
('Sample a: add freshly prepared100mL3.8×10−4M aqueous Na2S under vigorous stirring; pale-yellow color develops slowly. Addition rate and reaction temperature not reported.','Sample a','Sample a; no added NaCl'),
('Stir sample a2h, then allow to stand2days at room temperature. Room temperature explicitly attaches to standing; exact stirring speed, vessel, atmosphere, light and pressure absent.','Sample a','Sample a bulk procedure'),
('Time-course branch: remove several-milliliter aliquots at various elapsed times after mixing. Exact times/volumes and whether sequential aliquots deplete a single batch are not specified.','Sample a; time-profile sampling','Time-course aliquots a/b; same-batch relation unresolved'),
('Remove supernatant; wash retained particles thoroughly with water and ethanol; dry under vacuum. Method of supernatant removal is unspecified—do not assume centrifugation or filtration.','Sample a workup','Dried CdS/polymer sample or aliquot'),
('Sample b uses the analogous general sample-a procedure, but pretreats Cd-loaded particles10min in10mL0.5M aqueous NaCl before Na2S addition. Do not transfer10mL water as an additional charge.','Sample b','Sample b; NaCl pretreatment'),
('Cd2+ did not elute into solution during NaCl pretreatment, as reported qualitatively; no assay detection limit or numeric released fraction.','Sample b','NaCl-treated Cd-loaded host'),
('Sample b pale-yellow development is faster than a. Stir2h, stand2days at room temperature; analogous washing and vacuum drying. General-method inheritance is bounded by the explicit analogous-procedure statement.','Sample b','Sample b bulk procedure'),
('Direct note25 reports LiCl/KCl/tetramethylammonium chloride nominal0.5M comparisons with similar visible absorption and layer width to NaCl. Preserve incomplete comparison records without invented full feed quantities or proven same-batch links.','Reference note25','Alternative electrolyte comparison cohort'),
('Concentrated aqueous Na2S~10−2M gives homogeneous CdS throughout polymer, cited to ref14; this is prior-work evidence, not a fully described extra experiment in this paper.','Dispersion discussion; ref14','Earlier Yao–Kitamura1996 system'),
('TEM requires thin cross-sectional slices of swelling polymer; source says elaborate effort was necessary but gives no embedding medium, microtome, slice thickness, grid or drying/sectioning details.','Dispersion textures','TEM cross-section preparation')]
for i,(t,l,s) in enumerate(procedures):add('procedure',t,4 if i in [13,14] else 3 if i==15 else 2,l,s,'citation_only' if i==14 else 'reported')
measure=[
('Single-bead absorption microspectroscopy: Nikon Optiphoto2 microscope; Oriel Multispec257 polychromator; Princeton Instruments ICCD-576E/G multichannel detector. Details refer to refs20,21.','Measurements','Wet individual CdS/polymer bead'),
('150W Xe lamp Hamamatsu L2273 is the source specification; no calibrated sample irradiance/exposure dose.','Measurements','Absorption apparatus'),
('Dry beads scatter probe light; disperse in water to reduce scattering. Host swells;100–110µm diameter determined for wet solution samples,~100µm used for Fig1.','Measurements and Fig1','Wet host-bead size, not CdS diameter'),
('Optical images: Sony DXC-930 CCD video camera attached to microscope, Mitsubishi CP-11 video printer. Ring-boundary image is not TEM or XRD.','Measurements','Optical microscopy of host particles'),
('XRD: Rigaku RINT2000,2θ20–60°,CuKα radiation wavelength0.154nm. Operating voltage/current, step size, scan rate, calibration and specimen preparation absent.','Measurements','Cohort-level XRD; exact aliquot unresolved'),
('Low-magnification TEM uses Hitachi H-300; high-magnification TEM JEOL JEM2010. Neither accelerating voltage nor counted-particle number nor statistical resampling protocol stated.','Measurements','TEM at source-defined depth regions'),
('Absorption reproducibility at a given host diameter and reaction time is within±5%; preserve as reported repeatability without assigning point-specific error bars or independent replicate count.','Results preceding Fig1','Absorption repeatability statement'),
('450nm absorbance is used for kinetic profiles and layer-width calibration; it is near an excitonic shoulder only in the qualified time/size regime (note27).','Results; Fig2,8,9; note27','Absorption kinetics/calibration','author_interpretation')]
for item in measure:add('characterization_method',item[0],2 if item!=measure[-1] else 3,item[1],item[2],item[3] if len(item)>3 else 'reported')
obs=[
('At30min, sample b has much higher absorbance below500nm than a; authors interpret more CdS generated early with added NaCl.','Fig1a and discussion',2,'Samples a/b at30min'),
('At48h, sample b absorption is blue-shifted relative to a; authors interpret smaller CdS size, consistent with source XRD estimates. No numeric onset wavelength is explicitly tabulated.','Fig1b and discussion',3,'Samples a/b at labelled48h'),
('Both samples show fast450nm absorbance increase within first2h. With NaCl, CdS formation is said to finish within2h; without NaCl, gradual formation continues up to48h. This is an absorbance-based interpretation, not measured completion/yield fraction.','Fig2 discussion',3,'Time-series a/b'),
('Broad intense XRD reflection2θ26.5° with weak~44° and~52° peaks is consistent with cubic zinc-blende CdS:111,220,311 respectively. Source gives no actual XRD figure.','XRD discussion',3,'Samples a/b source-general crystalline phase'),
('Gaussian fitting of26.5° reflection and Debye–Scherrer calculation gives mean diameters3.8nm(a) and3.1nm(b). These are author-derived diffraction estimates, not direct microscopy particle means.','XRD discussion; refs22,23',3,'XRD formulations a/b; exact batch/time unresolved'),
('Sample a low-TEM panels span surface,4–5µm inward and8–9µm inward. CdS formation terminates ca8–10µm inward; no crystals observed at center. Depth is radial from host surface.','Fig3 and discussion',3,'Sample a depth-resolved cross-section'),
('Sample a near-surface CdS shows no flocculation. At4–5µm depth,~4–7nm crystallites flocculate into larger objects several tens of nanometers across. Do not conflate primary crystal and aggregate sizes.','Fig4 discussion',3,'Sample a near-surface/interior TEM'),
('TEM size histogram near surface is fitted log-normal, mean2.7nm and reported standard deviation0.4 without unit or mathematical definition.','Fig5a caption',5,'Sample a near-surface CdS; fit output'),
('At~4µm depth, sample a histogram fitted normal, mean4.6nm and standard deviation1.8nm.','Fig5b caption',5,'Sample a interior CdS; fit output'),
('Optical sample a has a ring about8µm inward. Combined with TEM, authors identify ring as edge of CdS dispersion layer; L is distance from bead surface to ring.','Fig6 and discussion',3,'Sample a optical ring and interpreted CdS layer'),
('Ring visibility attributed to inhomogeneous CdS dispersion and refractive-index contrast; flocculation changes scattering inside/outside ring. Ref24 gives underlying context.','Fig6 discussion; ref24',3,'Optical ring interpretation'),
('Sample b has a wider CdS layer. At surface no flocculation;9–10µm inward slight flocculation but homogeneous dispersion;15–16µm inward clear flocculation plus single small crystals.','Fig7 and discussion',3,'Sample b depth-resolved TEM'),
('Authors contrast b with a: clear flocculation at a8–9µm versus b15–16µm; salt suppresses flocculation in polymer, contrasting prior homogeneous-electrolyte behavior.','Fig7 discussion',3,'a/b depth comparison; no paired same-bead claim'),
('Discussion summarizes many~3nm crystals near surface and fewer~5nm crystals inside. These rounded trend values are not new independent samples and are distinct from detailed Fig5 fits.','Dispersion discussion',4,'Qualitative a/b spatial interpretation'),
('Note25 directly reports visible absorption and L for0.5M LiCl, KCl and tetramethylammonium chloride are quite similar to0.5M NaCl. No numeric peaks, L values or replicate counts.','Note25',4,'Alternative salt formulation comparison'),
('Initial time-domain discussion distinguishes t<30min (large difference) and detailed t<10min measurements. At a given t, spectral band shapes of a and b nearly same, interpreted as similar sizes as time proceeds.','Electrolyte distribution discussion',5,'Early-time a/b absorbance'),
('Linear absorbance450nm versus√t fits give slopes4.6×10−3s−1/2(a) and8.9×10−3s−1/2(b). These are fit slopes of absorbance versus square-root time, not concentration production rates.','Fig8 and text',5,'Early-time a/b fits'),
('L varies with reaction time. Direct L is not precise below4µm because ring boundary hard to establish; this is a measurement limitation, not absence of a smaller layer.','Layer calibration discussion',5,'Optically observed layer width'),
('Absorbance450nm and L fall on a common line for a/b. Authors infer the same CdS density at given absorbance and use absorbance to estimate L. No numerical regression coefficient explicitly reported.','Fig9 discussion',5,'a/b empirical calibration'),
('Using L=(2Dt)1/2 and absorbance calibration, HS− diffusion coefficients are calculated2.5×10−10cm²/s(a) and1.1×10−9cm²/s(b). They are effective author-model estimates, not directly tracked diffusion measurements.','Diffusion analysis',6,'a/b fitted diffusion model'),
('Qualitative NaCl pretreatment rationale uses cited Na+ diffusion~1.2×10−7cm²/s for Chelex/Dowex context;10min deemed adequate for~100µm particles. This is not measured HS−D.','Sample b; ref19',2,'Cited sodium diffusion context'),
('Note27 warns450nm is not an exciton-absorption measure when very small crystals form initially; authors restrict quantitative interpretation to their analyzed t and L ranges. Exact earliest cutoff unreported.','Note27',6,'Kinetic interpretation limits')]
for t,l,p,s in obs:add('observation',t,p,l,s,'author_derived' if any(q in t for q in ['Gaussian fitting','fitted log-normal','fitted normal','fits give slopes','diffusion coefficients are calculated']) else 'reported_with_author_interpretation')
models=[
('Authors reject inherent host-structure or Cd-loading inhomogeneity as sole reason for radial size gradients, citing prior uniform growth with~10−2M sulfide.','Dispersion discussion; ref14',4),
('Higher near-surface HS− creates higher supersaturation and more nuclei, giving smaller crystals; depleted inner HS− yields fewer nuclei and growth-dominated larger crystals.','Dispersion discussion; ref26',4),
('Restricted near-surface growth is hypothesized to involve chelating ligands and lack of available Cd2+, not measured binding constants or in-situ concentrations.','Dispersion discussion',5),
('Faster HS− diffusion with salt hypothesized to create more nuclei and faster reactant depletion near them, suppressing later growth even with longer exposure.','Diffusion analysis',6),
('Electrolyte reduces osmotic-pressure difference and swelling; smaller pores would slow diffusion. Authors therefore reject swelling alone as the explanation of measured acceleration. No actual salt-dependent pore size or swelling ratio measured.','Swelling discussion; ref28',6),
('Donnan equilibrium model imported from charged-membrane work refs29–32 explains charge screening and HS− influx qualitatively. It is not a DFT calculation or measured electrochemical potential.','Donnan model introduction',6),
('Without added NaCl, Na+ redistributes toward water and polymer surface becomes more negative; HS− penetration slows. With NaCl, Na+/Cl− partition lowers magnitude of Donnan potential and permits faster/deeper HS− influx.','Donnan interpretation',7),
('Cited resin selectivity Cd2+ versusNa+ approximately10^7 greater (ref18), used to argue Na+ does not readily displace Cd2+. Not a newly measured binding ratio.','Donnan interpretation; ref18',7),
('Model uses wet-polymerX0.4equiv/L and reports potentials−390mV for no added NaCl,−10mV fornominal0.5MNaCl. Model temperature and zero-added-salt effective C not specified.','Donnan calculations',7),
('Assuming swelling reduced toone-third, reported potential becomes−26meV. Swelling change is hypothetical and potential unit conflicts with mV; preserve as printed.','Donnan sensitivity example',7),
('Note33 discusses rough anion diffusion predictions involving noncharged-polymerD0,Q0,t0; exact values not estimable because Q0 and t0 cannot be evaluated precisely. Its positively charged polymer phrase differs from the negative/cation-exchange discussion.','Note33',7),
('Conclusion proposes tuning embedded-CdS optical/distribution properties using electrolyte, sulfide injection method and host size; last two are cited earlier ref14 results, not newly parameterized routes here. Device applicability is prospective.','Conclusion; ref14',7)]
for t,l,p in models:add('author_model',t,p,l,'Source theoretical/interpretive or cited context, not experimental training labels','author_interpretation')
figs=[
('Figure1','Two absorption panels ofa/b:30min(a),48h(b),~100µm host. Wavelength400–600nm; absorption axes0–0.60 and0–0.80 respectively. NominalNaCl0/0.5M. Original curves, no digitized points.',2,['a30min','b30min','a48h','b48h']),
('Figure2','450nm absorbance versus reaction time0–50h for a/b; filled circles markNaCl0.5M, open circles0M here. Curves are guide/kinetic presentation, not complete tabulated data.',3,['a-time-series','b-time-series']),
('Figure3','Sample a low-TEM cross-sections:surface(a),4–5µm(b),8–9µm(c); each250nm scale bar. Lower image side corresponds to polymer interior.',4,['a-surface','a-depth4-5um','a-depth8-9um']),
('Figure4','Sample a high-TEM near surface(a) and4–5µm inside(b); both50nm scale bars. Exact exposure time and physical batch relation toXRD/optical are not supplied.',4,['a-surface','a-depth4-5um']),
('Figure5','Sample a observed crystal-count histograms versus nanocrystal diameter0–10nm. Surface log-normal fit2.7nm/std0.4(a);interior~4µm normalfit4.6nm/std1.8nm(b). Counts perbin shown graphically, not digitized.',5,['a-surface-size-histogram','a-inner-size-histogram']),
('Figure6','Sample a optical micrograph(a),25µm scale bar, and author-drawn schematic(b) defining L from polymer exterior to inner CdS formation edge. Panelb is explanatory, not microscopy.',5,['a-optical-bead','a-author-layer-schematic']),
('Figure7','Sample b low-TEM surface(a),9–10µm(b),15–16µm(c),each250nmbar. Third image retains small dispersed crystals among aggregates.',6,['b-surface','b-depth9-10um','b-depth15-16um']),
('Figure8','Early450nm absorbance vs√time, x0–25s^1/2,y0–0.20. Filledcircles=a0M andopencircles=b0.5M, opposite assignments toFig2. Slopes inbody; no interpolated raw kinetics.',6,['a-early-time-fit','b-early-time-fit']),
('Figure9','450nm absorbance versus observed CdS-layer widthL0–12µm with common fit; filledcircles=a0M andopencircles=b0.5M. yto0.20. No exact regression coefficient printed.',6,['a-b-layer-calibration'])]
for label,t,p,ss in figs:add('figure',t,p,label,'; '.join(ss),'original_experiment_and_author_fit' if label!='Figure6' else 'original_experiment_and_author_schematic',label=label,formulation_scope=ss)
eqs=[
('Unnumbered diffusion relation','Δ=(2Dt)^(1/2); later L=(2Dt)^(1/2), assumingquasi-linear diffusion;D andΔ are diffusivity and penetrationlength. L is empiricalring-widthproxy.',5,'Diffusion paragraph; repeated p6'),
('Equation1','Δφ=φi−φo=−(RT/F)ln(Bi/Bo)=−(RT/F)ln(Ao/Ai). B=cation/counterion,A=anion/coion;i=polymer,o=water. R gasconstant,T modeltemperature,F Faradayconstant.',7,'Eq1 and symbol definitions'),
('Equation2','Bi=Ai+X; Bo=Ao≡C. Charge neutrality and equal aqueouscation/anion concentrations. X isfixednegativecharge density magnitude underthecation-exchange model.',7,'Eq2'),
('Equation3','Δφ=−(RT/F)ln[X/(2C)+sqrt(1+(X/(2C))²)]. Do not evaluateC=0literally as the printedfinite no-added-NaCl example requires unresolved backgroundconcentration handling.',7,'Eq3')]
for label,t,p,l in eqs:add('equation',t,p,l,'Author model; symbols are not new experimental settings','author_model',label=label)
conf=[
('Sample b salt concentration:10mL0.5Mpretreatment then100mLNa2S addition, but discussion/figures callreaction0.5M. Stock→mixture handling oradditionalNaCl undocumented. Conditional volume-additivity wouldgive0.04545M, not an observed correction.','Sample b; Fig1,2,8,9; model',2),
('Bulk procedure2hstir+2daysstand is not identical to Fig1b48h aftermixing. Keep clocks separately without summing48hinto50h measurements or replacing procedure.','Preparation and Fig1b',2),
('Roomtemperature explicitly applies to2day storage/standing; temperature duringCdloading sonication,10minpretreatment and2hstir not explicitlygiven. Noimplied25°C.','Preparation',2),
('Dry/wet polymer mass andcapacity differ;0.107gdryhost notCdSproductmass.100–110µmwetbead diameter not3nmCdS crystaldiameter.','Materials and measurements',2),
('Absorbance∝√t is plotted and fitted; abstractformationrate∝√t isloosewording. Do notlabel slopesasamount/timeorfitderivativewithoutnewcalculation.','Abstract and Fig8',1),
('Fig5alog-normal standarddeviation0.4 lacksunit/definition. Preserve rawstd0.4 anddistributiontype; no automaticnmorlogspace assignment.','Fig5caption',5),
('XRDcohorts3.8/3.1nm and TEMdepthcohorts2.7/4.6nm are different measurement scopes; noidenticalbatch/timeorwhole-beadTEMmean established.','XRDtext; Figs3–7',3),
('TEMdepth4–5µmcaption versus~4µmFig5 are region descriptions, not precision-matched sectionthickness. L8–10µm vsdepth8–9µm vsoptical~8µm similarly retainlocators.','Figs3–6',3),
('Donnan−26meV printedpotential usesenergyunit unlike−390/−10mV; never silently normalize.','Donnan sensitivity example',7),
('No-addedNaCl is not ion-freeC=0 becauseNa2Sstock suppliesions; Eq3undefinedatC=0 while finite−390mVreported. EffectivebackgroundC/modelT notgiven.','Eq3 and no-saltmodel',7),
('Note33 says positivelychargedpolymer, whilebodydescribesnegative surface/cationexchange; retain as sourceterminology inconsistency and do notbuild contrarychargeillustration.','Donnan body and note33',7),
('Fig2 usesfilled=b/open=a; Fig8–9usefilled=a/open=b. Legend-specific mapping necessary; OCR bullets/parentheses easilymisread.','Figs2,8,9',6),
('CuKαextractsCuKR; ±5%extracts(5%; square-root equation glyphs and negativeHS−lines canbreak. Visualsource resolvesglyphs, no chemicalidentity change.','Measurements; Eq1–3',2),
('Na+diffusivity1.2×10−7 cited forresincontext is distinctfromauthor-derivedHS−D2.5×10−10/1.1×10−9. Slopes4.6/8.9×10−3areabsorptance-vs√time quantities.','Sample b; diffusionanalysis',6),
('Unknown aliquotidentities, exact sampling schedule,TEM preparation andreactiontime,XRDspecimenhistory mean figures cannot be declaredsame physicalexperiment. Source supportsnominalformulation/depthjoins.','Measurements/results overall',3),
('NoXRDpattern supplied despite narrativeXRDresults. NoTEMdiffraction,SAED,Raman,PL/QY,thermalstability curve,atomiccoordinates,CIForcomputedinterface in suppliedmain.','Entire supplied main',7),
('Reference14concentratedNa2S,hostsizeandinjectionvariants arecitation-only; note25alternativeelectrolytes aredirectreportedcomparisons despitebeingfootnote.','Ref14; note25; conclusion',4),
('Colloidal waterdispersion isofswollenCdS-containinghostbeads;TEMrequirescross-sections. Do not portray freestanding uncappedCdSnanocrystals orcastuniformCdSshell at exactatomicinterface.','Preparation, measurements,Figs3–7',3)]
for t,l,p in conf:add('conflict',t,p,l,'Source ambiguity or data semantics; unresolved unless visual glyph correction explicitly stated','curation_assessment')
refs=[
('Wang,Y. Acc.Chem.Res.1991,24,133.','Nonlinear optical background; no local recipe extraction.'),
('Takagahara,T. Phys.Rev.1987,B36,9293.','Quantum/nonlinear optical background.'),
('Kamat,P.V. Chem.Rev.1993,93,267.','Photocatalytic context; not measured here.'),
('Alivisatos,A.P. Science1996,271,933.','Semiconductor nanocrystal background.'),
('Steigerwald,M.L.;Brus,L.E. Acc.Chem.Res.1990,23,183.','Nanocrystal background.'),
('Vossmeyer etal. J.Phys.Chem.1994,98,7665.','Size-controlled synthesis and cubicCdSreference; not independently read.'),
('Murray,C.B.;Norris,D.J.;Bawendi,M.G. JACS1993,115,8706.','Prior nanocrystal preparation; no hot-injection steps inherited here.'),
('Herron etal. JACS1989,111,530.','Zeolite host prior.'),
('Kuczynksi,J.;Thomas,J.K. J.Phys.Chem.1985,89,2720.','Porous glass prior; author spelling retained as source.'),
('Dékány etal. Langmuir1995,11,2285.','Organo-clay prior.'),
('Kuczynski etal. J.Phys.Chem.1984,88,980.','Nafion/ionic-polymer prior.'),
('Wang etal. J.Chem.Phys.1990,92,6927.','Ionic-polymer nanocrystal prior.'),
('Wang,Y.;Suna,A.;Mahler,W.;Kasowski,R. J.Chem.Phys.1987,87,7315.','Ethylene–methacrylic-acid polymer prior.'),
('Yao,H.;Kitamura,N. Bull.Chem.Soc.Jpn.1996,69,1227.','PriorCdS/Chelexhostsize/injection and~10−2MNa2Suniformgrowth; citedonly.'),
('Direct note15.','CurrentaqueousNa2SspeciesNa+,HS−,OH−; directsourcechemistrycontext.'),
('Cotton,F.A.;Wilkinson,G.;Gaus,P.L. BasicInorganicChemistry,Wiley,1987.','Speciationtextbook.'),
('Israelachvili,J.N. IntermolecularandSurfaceForces,AcademicPress,London,1985.','Homogeneousdouble-layerscreening/flocculationcontext.'),
('Chelex100chelatingionexchangeresinInstructionManual.','Manufacturerfixedchargecapacity and~10^7Cd/Na selectivity; citednotnewmeasurement.'),
('Marinsky,J.A. IonExchange,MarcelDekker,NewYork,1966,Vol1.','Na+resindiffusion1.2×10−7cm²/s citedcomparativevalue.'),
('Yao,H.;Inoue,Y.;Ikeda,H.;Nakatani,K.;Kim,H.-B.;Kitamura,N. J.Phys.Chem.1996,100,1494.','Microspectroscopyconfigurationprior.'),
('Kitamura,N.;Nakatani,K.;Kim,H.-B. PureAppl.Chem.1995,67,79.','Microspectroscopyprior.'),
('Langford,J.I.;Louer,D. PowderDiffr.1986,1,211.','GaussianXRDfitmethod.'),
('Bawendi,M.G.;Kortan,A.R.;Steigerwald,M.L.;Brus,L.E. J.Chem.Phys.1989,91,7282.','Debye–Scherrersizeestimationcontext; not another current source.'),
('Debye,P.;Bueche,A.H. J.Appl.Phys.1949,20,518.','Scattering/refractive-indexinhomogeneitycontext.'),
('Direct note25.','LiCl,KCl,tetramethylammoniumchloride0.5M absorption/Lsimilarity; directexperimentalscope, recipeincomplete.'),
('Ramsden,J.J. Surf.Sci.1985,156,1027.','Supersaturation/nucleationgrowthinterpretation.'),
('Direct note27.','Earliestvery-smallCdS450nmabsorbancenotexcitonmeasure; boundedkineticinterpretation.'),
('Inczédy,J. AnalyticalApplicationofIonExchangers,Pergamon,Oxford,1966.','Electrolyte/swellingcontext.'),
('Teorell,T. Prog.Biophys.Biophys.Chem.1953,3,305.','Charged-membraneDonnanmodel.'),
('Meyer,K.H.;Siever,J.F. Helv.Chim.Acta1936,19,649.','Donnanmodel;body spellsSieverswhilebibliographySiever.'),
('Meyer,K.H.;Siever,J.F. Helv.Chim.Acta1936,19,665.','Chargedmembraneaniondiffusioncomparison.'),
('Toyoshima,Y.;Kobatake,Y.;Fujita,H. Trans.FaradaySoc.1967,63,2814.','Donnanpotentialclosedform.'),
('Direct note33.','ModelD0,Q0,t0assumptions; exactvaluesnotavailable; chargedpolymerterminologyconflict.')]
for n,(bib,scope) in enumerate(refs,1):
 p=1 if n<=17 else 2 if n<=21 else 3 if n<=24 else 4 if n==25 else 5 if n==26 else 6 if n<=29 else 7
 add('reference',bib+' '+scope,p,f'Reference/note{n}',scope,'direct_source_note' if n in [15,25,27,33] else 'citation_only',reference_number=n,bibliographic_text=bib,independently_opened=False)
intuition=[
('Use immobilized iminodiacetate sites to captureCd2+ and limit free-crystalflocculation; scaffoldchemistry and transport matter alongsideprecursorstoichiometry.',1,'Introduction and laterdispersion discussion'),
('Electrolyte screening can promote smaller,deeperdistributedCdS inachelatehost even when saltwouldpromoteflocculation inhomogeneousdispersion; effectisboundedtohostsystem.',3,'NaClresults and ref17comparison'),
('Precursortransport andconsumption setlocal supersaturation; near-surface many nuclei and interiorgrowth canproducespatiallydifferentcrystalswithinonebead.',5,'Supersaturationinterpretation'),
('Opticalabsorption,depth-resolvedTEM, andXRDprobe differentaverages;combinewithscopequalifiersratherthanforcingsingleparticlelabel.',3,'Figs1–7 andXRD'),
('Futureclarifyingexperimentscouldseparatelymeasurefinalsaltconcentration,wet swelling,localionsandpotential; thesearecurationoutlook,notauthorperformedexperiments.',7,'Donnanmodelambiguities'),
('Datasetneedsresinchargecapacity/dry-wetstate,pretreatment,hostversuscrystalsize,radialdepth,aliquotclock,measurementproxyandmodelparameters; a singletemperature-to-size recipewouldlosekeyinformation.',7,'Whole source; model andmeasurementlimits')]
for t,p,l in intuition:add('intuition',t,p,l,'Interpretation/outlook; no experimental training labels','curator_synthesis_of_source' if p!=7 else 'curator_outlook')
out={'schema':'mattersyn-independent-source-audit-1','source_id':'yao1998','doi':I['doi'],'title':I['title'],'authors':I['authors'],'journal':I['journal'],'year':1998,'volume':14,'pages':'595–601','dates':I['dates'],'source_basename':'10.1021_la970480g.pdf','source_sha256':I['main_sha256'],'review_scope':'supplied_main_only_si_unverified','status':'independent_supplied_main_text_and_visual_review_complete','checked_utc':datetime.now(timezone.utc).isoformat(),'supporting_information':I['si'],'page_review':[{'pdf_page':i,'printed_page':594+i,'text_read':True,'visual_read':True,'text_sha256':sha(B/f'page-{i}.txt'),'image_sha256':sha(B/f'page-{i}.png')} for i in range(1,8)],'unit_count':len(units),'category_counts':dict(counts),'units':units,'inventory_totals':{'main_pages':7,'main_figures':9,'figure_panels':17,'numbered_equations':3,'unnumbered_diffusion_relation':1,'tables':0,'references_and_notes':33,'primary_full_procedure_variants':2,'direct_incomplete_alternative_electrolytes':3},'scope_limits':['All supplied main pages text+visual reviewed; no independent access to citedpapers/manuals/books.','SI not located orverified; no absence claim.','No rawcurve/histogrambin digitization or pixel-derivedquantities. Graphical values remain originalfigures plus explicitlyprintednumericresults.','Figureslinkedonlyto statedformulations/depths/times; nobatchidentityinvention.','Fullsourceaudit is notcanonicalvalidation,originalassetreview,readerintegration,browserQA,trainingpromotionorpublication.','No Site/source/monitor mutations.']}
(B/'source-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
lines=['# Independent supplied-main audit: Yao et al.1998','',I['title'],'',f'All seven supplied pages read as text and images. {len(units)} auditable source units; nine figures (17 panels), three numbered equations plus one diffusion relation, no tables,33 references/notes. SI remains not located or verified.','','Two full synthesis variants are source a (no addedNaCl) and b (NaClpretreatment). Direct note25 adds three incomplete electrolytecomparisons. Cited concentratedsulfide/priorhostvariants remain citationcontext.','','## Critical preserved limitations','']
lines+=['- '+u['text'] for u in units if u['category']=='conflict']
lines+=['','## Unit inventory','']+['- '+k+': '+str(v) for k,v in counts.items()]+['','Exact locators, formulation/state scopes, claim types and page/source hashes are in source-audit.json. No record, reader or publication completion is implied.']
(B/'source-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'source_id':'yao1998','units':len(units),'counts':dict(counts),'audit_sha256':sha(B/'source-audit.json')},indent=2))
