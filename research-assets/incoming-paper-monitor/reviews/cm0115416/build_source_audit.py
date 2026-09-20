"""Independent complete supplied-main inventory after actual text and image inspection."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
from pypdf import PdfReader
B=Path(__file__).resolve().parent;SID='yi2002';DOI='10.1021/cm0115416'
S=Path('[local path redacted]');L=Path('[local path redacted]')
U=[];F=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def add(i,p,loc,kind,claim,disposition='retain_source_linked_evidence'):
 U.append({'id':SID+'-'+i,'source_unit_id':SID+'-'+i,'source_role':'main','pdf_page':p,'printed_page':2909+p,'locator':loc,'kind':kind,'claim':claim,'disposition':disposition})
def many(prefix,p,loc,kind,rows,disposition='retain_source_linked_evidence'):
 for i,c in rows:add(prefix+i,p,loc,kind,c,disposition)
def fact(i,uid,scope,prop,value=None,unit=None,minimum=None,maximum=None,approximate=False,status='reported',qualifier=''):
 F.append({'id':SID+'-fact-'+i,'source_unit_id':SID+'-'+uid,'sample_scope':scope,'property':prop,'value':value,'minimum':minimum,'maximum':maximum,'unit':unit,'approximate':approximate,'status':status,'qualifier':qualifier,'eligible_training':False})
many('identity-',1,'Title, byline and footer','source_metadata',[
 ('title','Synthesis and Characterization of High-Efficiency Nanocrystal Up-Conversion Phosphors: Ytterbium and Erbium Codoped Lanthanum Molybdate.'),
 ('authors','Guangshun Yi, Baoquan Sun, Fengzhen Yang, Depu Chen, Yuxiang Zhou and Jing Cheng. Depu Chen is corresponding author. Affiliations include Tsinghua University Chemistry and Biological Sciences/Biotechnology, Beijing National Biochip Research & Engineering Center and Zibo University.'),
 ('journal','Chemistry of Materials 2002, volume14, issue7, pages2910–2914; DOI10.1021/cm0115416.'),
 ('dates','Received October25,2001; revised manuscript received March29,2002; published on web June19,2002.'),
 ('administrative','ACS copyright2002, contact details, manuscript code CM0115416 and July7,2026 download watermark are administrative metadata; download/creation timestamps are not preparation or publication dates.')],'retain_bibliographic_metadata')
many('abstract-',1,'Abstract','study_summary',[
 ('material','Hydrothermal synthesis of Yb/Er-codoped La2(MoO4)3 nanocrystals, nominal average diameter50 nm; reported here for potential bioassays/biochips, without an actual bioconjugation or bioassay experiment.'),
 ('anneal','After800 °C/5 h annealing, strong980 nm-excited emission is reported. Higher intensity than bulk is qualitative, not an absolute quantum-efficiency measurement.'),
 ('scope','Down-conversion, up-conversion, annealing and Er concentration effects and size-dependent behavior are examined. Two-photon excitation and surface-effect mechanisms are proposed interpretations.'),
 ('priority','Authors claim first synthesis/particle-size-dependent UCP observation for this system. Preserve as attributed2002 historical claims, not independently verified priority.')])
many('context-',1,'Introduction','cited_context',[
 ('nanocrystals','References1–4 motivate doped-nanocrystal size-dependent optical properties. These external materials and experiments are not additional present synthesis records.'),
 ('downconversion','Down-conversion emits lower-energy photons under higher-energy excitation; ZnS:Mn and Y2O3:Eu are cited examples, refs5–8.'),
 ('upconversion','UCP emits higher-energy photons under lower-energy excitation; at least two absorbed low-energy photons are described as needed. This introductory principle does not measure a two-photon cross section.'),
 ('lasers','Red, green and blue room-temperature IR-pumped lasers are cited, especially motivation for blue solid-state lasers; no present-sample laser threshold, gain or coherent device is demonstrated.'),
 ('led','A cited GaAs IR diode coated with UCP motivates different-color LEDs. No GaAs substrate or LED fabrication is part of the current synthesis.'),
 ('bio-labels','Cited UCP labels are described as low-background and resistant to photobleaching relative to Cy-3/Cy-5/Cy-7 dyes; simultaneous multi-analyte detection by common IR pumping is context, not measured photostability or assay performance here.'),
 ('bio-size','DNA/RNA/protein labeling motivates small, narrowly distributed, efficient UCPs; prior reported UCPs were considered too large. No specific conjugating ligand or biological surface chemistry is supplied.')],'retain_cited_or_author_context_not_new_recipe')
many('context-',2,'Introduction continuation','cited_context',[
 ('sensitizer','Ytterbium is described as absorber and erbium as emitter in the lattice:980 nm excitation is absorbed and energy transferred to visible-emitting Er. No transfer efficiency or measured dopant-site structure is supplied.'),
 ('bulk-history','Prior bulk lanthanum molybdate Yb/Er phosphors are usually made by1200 °C solid-state reaction, citing reference15. A separate current bulk comparator preparation is subsequently reported.'),
 ('study','Authors report approximately50 nm nanocrystals with narrow distribution, stronger emission and a different spectral shape than bulk. These comparisons do not establish equal optical normalization or absolute luminescent efficiency.')],'retain_cited_or_author_context_not_new_recipe')
many('precursor-',2,'Experimental2.1, solution A and B','chemical_identity_and_amount',[
 ('la-oxide','La2O3:1.1760 g,3.607 mmol,99.99%; oxide obtained from Aldrich.'),
 ('yb-oxide','Yb2O3:0.3692 g,0.937 mmol,99.99%; oxide obtained from Aldrich.'),
 ('er-oxide','Er2O3:0.05370 g,0.140 mmol,99.99%; oxide obtained from Aldrich.'),
 ('nitric-acid','Diluted nitric acid dissolves the three oxides. Concentration, dilution solvent ratio, volume, excess, supplier and acid-addition order are not supplied.'),
 ('residue','Warm the solution to dryness to drive off unreacted nitric acid. Temperature, time, atmosphere and residual acidity are not given; no weighed isolated nitrate hydrate or verified residue structure is reported.'),
 ('water-a','Redissolve the residue in30 mL deionized water to prepare solution A. This is added water volume, not a measured final solution volume or named solution molarity.'),
 ('ammonium-molybdate','Solution B uses printed (NH4)2MoO4,1.961 g and9.37 mmol, supplied by Beijing Chemical Corp. Purity and hydration are unreported. Do not replace it with ammonium heptamolybdate or an inferred hydrate.'),
 ('water-b','Dissolve the ammonium molybdate in30 mL deionized water. Exact final stock volume/pH and molarity are not directly reported.'),
 ('mass-amount-conflict','Printed1.961 g/9.37 mmol implies approximately209.3 g/mol, whereas the literal anhydrous (NH4)2MoO4 formula is approximately196.0 g/mol. Keep both reported mass and amount; no silent numeric/identity repair or replacement concentration.'),
 ('feed-stoichiometry','Reported rare-earth oxide amounts correspond to9.368 mmol total rare-earth atoms, close to77:20:3 La:Yb:Er; reported9.37 mmol Mo gives approximately1:1 Mo:rare-earth rather than the nominal host3:2. This arithmetic consistency issue is a curator check, not an author-established off-stoichiometric phase or corrected recipe.'),
 ('dopant-composition','Nominal La:Yb:Er77:20:3 is explicitly stated for the bulk comparator and approximately consistent with nanocrystal oxide feed amounts. Neither chemically measured incorporation nor exact crystallographic occupancy is supplied.'),
 ('bulk-moo3','Bulk comparator uses MoO3 powder rather than aqueous (NH4)2MoO4. Supplier, purity, charge and Mo:rare-earth ratio are not stated for this comparator.')])
many('protocol-',2,'Experimental2.1, hydrothermal route','protocol',[
 ('stock-a-stir','After redissolution in30 mL water, solution A is stirred1 h at room temperature. Numerical temperature, stirring speed and vessel are unspecified.'),
 ('stock-b-stir','Solution B is stirred1 h at room temperature after dissolution in30 mL water. Numerical temperature and stirring speed unreported.'),
 ('addition','Add solution B drop by drop to solution A at20–30 drops/min with vigorous stirring. Drop volume, actual volumetric flow, total addition time, mixed pH and stirring speed are absent.'),
 ('suspension','A suspension forms and is continuously stirred20 min. No precipitate composition/phase or exact mixture temperature is independently measured.'),
 ('transfer','Transfer suspension to a100 mL Teflon vessel, cap it and place it closely in an RD-100 autoclave supplied by Institute of Beijing Petrochemical Industry. Nominal solvent amounts do not establish exact fill fraction after acid drying/redissolution and solute addition.'),
 ('hydrothermal','Heat the sealed assembly to180 °C for1 h. Heating ramp, autoclave pressure, prepurge gas, thermal equilibration criterion, mixing during hold and cooling/depressurization sequence are absent.'),
 ('centrifuge','Centrifuge suspension at6000 rpm for10 min. Retain the precipitates. Rotor radius and relative centrifugal force are not given; do not silently convert rpm to g.'),
 ('wash','Wash precipitates twice with deionized water. Water volumes, redispersion details and separate wash-centrifugation settings are not specified.'),
 ('dry','Dry in air to obtain white powders. Drying temperature/time and residual-water endpoint are unreported.'),
 ('anneal-ramp','Heat nanocrystals to800 °C at20 °C/min. The exact ramp belongs to this standard preparation; the temperature-series paragraph does not independently restate a ramp for every variant.'),
 ('anneal-hold','Hold800 °C for5 h. Atmosphere and furnace/vessel are unspecified for this nanocrystal anneal; air is explicitly stated for drying and bulk firing but must not be transferred without evidence.'),
 ('anneal-cool','Naturally cool to room temperature after the800 °C hold. No numerical cooldown rate, duration or ambient temperature is supplied. Final product is white powder.'),
 ('route-limits','No isolated yield, quantitative phase purity, storage condition, surface ligand, bioconjugation, batch repetitions, batch identifier or raw reagent-analysis data are provided. All staged material outputs must distinguish acid residue, wet precipitate, dried powder and annealed product.')])
many('bulk-',2,'Experimental2.1, comparison material','comparator_protocol',[
 ('mix','For comparison, solid-state mix La2O3,MoO3,Yb2O3,Er2O3 powders. Actual masses, mixing duration/apparatus, grinding medium and binder are unreported.'),
 ('composition','La:Yb:Er molar ratio77:20:3 is reported. The amount of MoO3 relative to total rare-earth cations is not specified.'),
 ('pellet','Press mixture into a pellet; dimensions, pressure, dwell, die and binder are unreported.'),
 ('fire','Fire the pellet in air at1200 °C for5 h, citing reference15. Heating/cooling ramps, furnace, vessel and product size distribution are unreported.'),
 ('identity','The bulk material is a current synthesized comparison specimen, not merely a prior-literature value. No physical batch link or identical chemical/optical normalization to the nano specimen is established.')])
many('method-',2,'Experimental2.2','characterization_protocol',[
 ('tem','TEM images collected with a Hitachi transmission electron microscope, Tokyo. Model, accelerating voltage, grid/coating/preparation, camera length and size-counting statistics absent.'),
 ('fluorescence','Fluorescence spectra recorded with Perkin-Elmer LS-50B fluorescence spectrophotometer using front-surface accessory. Instrument manufacturer address printed Forster City,CA; preserve source metadata without externally correcting.'),
 ('nir','Near-IR absorption measured with Perkin-Elmer PE SYSTEM2000 FTIR spectrophotometer using a quartz beamsplitter. Sample mass/path length, resolution, scans, background and preparation absent.'),
 ('xrd','XRD acquired with Bruker D8 advance diffractometer. Radiation wavelength, scan step/rate, instrumental standard, zero correction and sample geometry absent.'),
 ('particle-size','Particle-size analysis uses BI-90Plus,Brookhaven. The paper does not explicitly specify scattering method, solvent, concentration, hydrodynamic basis or algorithm; do not force histogram to TEM counts or assume a particular size-weighting model.'),
 ('upconversion','Up-conversion uses the LS-50B with external980 nm laser (50 mW,Beijing Hi-Tech Optoelectronic Co.,China), replacing the xenon source, and an optic-fiber accessory.50 mW is stated source power, not a documented sample irradiance or each Figure8 sweep point.'),
 ('missing','No present fluorescence acquisition temperature, beam spot, wavelength/power calibration, exposure, slit, detector corrections, absolute quantum yield, fluorescence lifetime or uncertainty reported. Introduction room-temperature laser literature is not proof present spectra were measured at a numeric or symbolic room temperature.')])
many('xrd-',2,'Results, Figure1 and Scherrer paragraph','structure_evidence',[
 ('sample','Figure1 is the nanocrystal material after800 °C/5 h annealing.'),
 ('phase','Authors assign crystalline tetragonal La2(MoO4)3 with a little second phase and agreement with bulk. Retain the reported symmetry and unidentified minor phase; no phase-pure assertion, refined space group, dopant site or phase fraction supplied.'),
 ('reference','Pattern compared to ICDD No.45-0407 and reference16. This identifier is a source citation, not a supplied or independently verified CIF/atomic model.'),
 ('peak','Peak of maximum intensity is stated at2θ=28.053 (degree angle context). No full indexed reflection table supplied.'),
 ('fwhm','Measured FWHM B1=0.186° and instrumental B0=0.104° are reported. Keep instrumental broadening separate from observed peak width; no correction formula or Scherrer shape factor/radiation is explicitly specified.'),
 ('size','Authors calculate crystallite size52.5 nm using Scherrer equation. It is author-derived coherent-domain size, not independently measured TEM diameter or supplied full crystallographic refinement.'),
 ('single-crystal','Agreement with microscopy/particle-size values is used to infer individual particles are single crystals rather than agglomerates of much smaller crystallites. This is author interpretation, not SAED, lattice-resolved TEM or proof every particle is monocrystalline.')])
many('size-',2,'Results, Figures2–3','morphology_and_size',[
 ('tem-panels','Figure2a is before annealing; Figure2b is after800 °C/5 h. Source states nearly spherical and well-separated particles, but original images also show close contacts; do not invent numerical aggregation fractions.'),
 ('tem-range','Most TEM particle diameters are described as40–60 nm; not a precise minimum/maximum bound for all particles.'),
 ('distribution','Figure3 particle-size histogram is described as mostly45–65 nm with average about53 nm, in agreement with TEM. Sample post-treatment is source-general; no explicit before/after split or raw bin/count table supplied.'),
 ('rounding','Abstract/introduction/conclusion use approximately50 nm average diameter, distinct from about53 nm histogram and52.5 nm Scherrer values. Do not replace all with one size measurement.'),
 ('narrow','Authors call the size distribution narrow. No numerical FWHM, dispersity, standard deviation, particle count or analysis repeat given.')])
many('optical-',3,'Results, Figures4–5','optical_measurement',[
 ('down-excitation','Down-conversion emission in Figure4a is excited at374 nm. The plot also includes a dotted excitation spectrum; its emission-monitoring wavelength and excitation-scan settings are not specified.'),
 ('down-peaks','Down-conversion bands centered at525 and549 nm are assigned to Er3+ ²H11/2→⁴I15/2 and⁴S3/2→⁴I15/2, respectively, citing17. They are distinct from up-conversion519/541 nm values.'),
 ('up-peaks','Under980 nm excitation, three up-conversion peaks at519,541,653 nm are assigned to²H11/2→⁴I15/2,⁴S3/2→⁴I15/2,⁴F9/2→⁴I15/2, respectively, citing17–18.'),
 ('abs-range','Near-IR spectrum acquired in9000–11000 cm−1 range to estimate excitation range. No spectrometer resolution or dense absorption array given.'),
 ('abs-center','Absorption centered approximately10238 cm−1, printed equivalent976 nm. Preserve both reported rounded quantities rather than replacing one by recalculation.'),
 ('abs-transitions','Near-IR absorption assigned to Er3+⁴I15/2→⁴I11/2 and Yb3+²F7/2→²F5/2, citing19; separate quantitative contributions/energy-transfer efficiencies are not resolved.'),
 ('abs-window','Source gives whole absorption range10625–9875 cm−1, with printed941–1013 nm equivalents. This is the inferred excitation window, not a separate measured excitation-efficiency sweep.'),
 ('preanneal','Wet-prepared nanocrystals have very low fluorescence before annealing, attributed to extremely poor crystallinity. No numeric pre-anneal intensity, crystallinity fraction or diffraction comparison supplied.')])
many('anneal-',3,'Temperature study, Figure6','synthesis_variant_and_outcome',[
 ('series','Nanocrystals annealed5 h at temperatures600–1000 °C. Figure6 explicitly labels600,700,800,900,1000 °C, all5 h. These are temperature endpoints, not sequential heating of one demonstrated specimen.'),
 ('trend','Intensity rises strongly from600 to800 °C, increases more slowly800–900 °C, then decreases sharply at1000 °C. No calibrated integrated intensity table or uncertainty supplied.'),
 ('800-size','Authors state particle size remains unchanged during800 °C annealing, referencing before/after TEM Figure2. No paired numeric size-distribution statistics supplied.'),
 ('900-growth','At900 °C particle-size increase and aggregation occur according to the authors. No900 °C TEM panel, mean diameter or aggregate fraction is supplied.'),
 ('1000-bulk','After1000 °C/5 h, authors describe UCP becoming bulk material;541 nm peak becomes stronger than519 nm. This annealed-nano outcome is distinct from the separately prepared1200 °C solid-state comparator.'),
 ('selection','800 °C chosen as optimized condition for subsequent experiments. It is not the maximum measured fluorescence temperature, because900 °C is described/depicted as more intense; morphology/aggregation considerations remain part of selection.'),
 ('mechanism','Intensity decrease at1000 °C attributed to grain growth/reduced surface area, with analogous Eu3+:Y2O3 behavior cited from20. Surface-area change is not measured by BET or a numeric area assay.')])
many('doping-',3,'Er concentration study, Figure7','comparison_series',[
 ('scope','Emission intensity of annealed nanocrystals examined over1–7% Er3+ mole fraction. Er molar-fraction denominator, exact revised oxide charges, La compensation, Yb concentration for each point and batching scheme are not independently specified.'),
 ('trend','Prose says all three transitions grow from1 to3% Er, then decrease sharply with further4–7%. Figure7 plots only one unlabeled intensity series, so do not synthesize three independently digitized wavelength series.'),
 ('optimum','3% Er mole fraction chosen as optimum. This is nominal preparation/comparison context, not an ICP/EDS-determined dopant composition.'),
 ('quenching','Decrease at high Er concentration is attributed to concentration quenching. No quenching rate, lifetime, dopant clustering measurement or critical transfer distance is supplied.'),
 ('figure-conflict','Figure7 visibly has points1,2,3,4,5,7%; no point at6%. The4% point remains close to3%, differing from prose that emphasizes sharp decrease over4–7%; preserve both without invented intermediate values or adjusted curve.')])
many('power-',3,'Power dependence, Figure8','power_law_and_interpretation',[
 ('law','Unnumbered relationship I_up ∝ (I_exc)^n; I_up is visible up-conversion intensity, I_exc near-IR excitation intensity and n the number of photons inferred per emitted up-conversion photon, citing21–22.'),
 ('measurement','Figure8 measures519,541,653 nm peak intensities against980 nm excitation intensity. Exact power values, spot size, raw tabulation and log normalization units are absent; do not infer watts or irradiance from ln-axis numbers.'),
 ('rounded-slopes','Prose gives slopes2.20,1.89,2.09 for519,541,653 nm, respectively.'),
 ('two-photon','Near-quadratic exponents are interpreted as two IR photons producing one up-conversion photon. It is not a direct measurement of a two-photon cross section or unique mechanism proof.')])
many('mechanism-',4,'Figure9 and explanatory paragraphs','author_model',[
 ('levels','Figure9 is an electronic energy-level schematic for Yb3+ and Er3+, not an atomistic lattice, measured wavefunction or direct level-lifetime experiment.'),
 ('excitation','Authors describe Er excitation from⁴I15/2 to⁴I11/2, then⁴F7/2 under980 nm pumping. Figure9 additionally depicts Yb²F7/2→²F5/2 excitation and energy transfer to Er⁴I11/2.'),
 ('relaxation','Excited Er electrons decay mainly nonradiatively to²H11/2,⁴S3/2 and⁴F9/2, then emit519,541,653 nm to⁴I15/2. Radiative/nonradiative rates and transfer yields unreported.'),
 ('comparison','Figure10 compares strong green519/541 and weak red653 nm nanocrystal emission with bulk where653 nm exceeds the green peaks, citing15. No absolute quantum yield or equal absorbed-power/sample-mass normalization is given.'),
 ('population','Authors infer greater⁴F9/2 population/relaxation probability in bulk from red intensity, citing25. No time-resolved populations or decay rates measured.')])
many('comparison-',5,'Figure10 and size-dependent interpretation','comparison_or_author_interpretation',[
 ('ranking','Nanocrystals:519 nm intensity>541 nm>653 nm. Bulk is described as opposite,653>541>519. Qualitative source ordering, not digitized amplitude ratios.'),
 ('efficiency','Authors say lower-temperature800 °C nanocrystals have stronger luminescence efficiency than bulk and potential biolabel utility. Measurements are arbitrary-intensity spectra; absolute efficiency or biological performance is not quantified.'),
 ('same-structure','Authors state nano and bulk have the same composition/crystal structure and attribute spectral differences to size. No quantitative chemical-composition assay, separate refined bulk pattern or independent control for every confounder supplied.'),
 ('prior-materials','Y2O3:Eu,Y2O3:Tb,ZnS:Mn cited as analogous down-conversion size enhancement; proposed quantum confinement or greater surface area cited1–3,7,20. These do not become present synthesis outcomes.'),
 ('surface-centers','As size decreases, authors propose more luminescent ions exposed at surface. Surface ions remain lattice-associated but interact more weakly through pendent bonds. No measured surface density, ligand identity, site coordination or dangling-bond spectroscopy supplied.'),
 ('lifetime','Citing Blasse25, weaker environment coupling is proposed to prolong Er⁴I11/2 lifetime and improve up-conversion. No lifetime value or time-resolved dataset supplied here.'),
 ('surface-emission','Authors mainly attribute519 nm emission to surface ions and653 nm to interior ions to explain spectral-shape changes. These are hypotheses, not spatially resolved emission or chemically identified sites.'),
 ('grinding','Authors state their experiment confirmed grinding bulk material into very fine powder does not improve optical properties. No grinding method, duration, size, before/after spectrum or quantitative intensity is provided; retain as incomplete comparator procedure/observation.'),
 ('grinding-model','Reduced intensity on grinding is attributed to changed intrinsic point-defect concentration, citing26. Analogous europium-doped CaS and rare-earth oxysulfides cite26–27; no current defect-concentration assay supplied.')])
many('figure-',2,'Original figures and captions','figure_metadata',[
 ('1','XRD Figure1 after800 °C/5 h. Abscissa2-Theta-Scale with labeled10–70 and ordinateLin/Counts0–500. No assigned hkl indices, exact phase fractions or plotted bulk curve; retain original trace.'),
 ('2','TEM Figure2a before annealing has300 nm scale bar; Figure2b after800 °C/5 h has100 nm scale bar. Full images/panel letters/caption must remain; unlike scale bars do not imply measured diameter differences.')])
many('figure-',3,'Original figures and captions','figure_metadata',[
 ('3','Size histogram Figure3 abscissaParticle size/nm with labels20–60 and bars extending beyond these tick centers; ordinateIntensity0–100, not specified particle counts or percentage. Low-size bars outside the most45–65 nm prose range remain visible; no raw bins reconstructed.'),
 ('4a','Figure4a overlays solid emission and dotted excitation spectra; wavelength labels300–600 nm, intensity a.u.40–200.374 nm excitation applies to the reported down-conversion emission; emission-monitor wavelength for excitation trace unreported.'),
 ('4b','Figure4b up-conversion under980 nm laser, wavelength labels300–800 nm and intensity a.u.0–500. Peaks519/541/653 correspond to nano specimen, no absolute intensity normalization or error bars.')])
many('figure-',4,'Original figures and captions','figure_metadata',[
 ('5','Figure5 near-IR absorption: frequency/wavenumber axis11000 descending to9000 cm−1; Absorbance ordinate0.0 at top to1.0 at bottom. Preserve original reversed ordinate and label; do not silently relabel transmittance or flip/redraw the trace.'),
 ('6','Figure6 five curves labeled(a)600,(b)700,(c)800,(d)900,(e)1000 °C, each5 h, under980 nm laser diode. Abscissa450–700 nm and ordinateIntensity/a.u.4–10. Source spectral offsets/scaling are not raw absolute efficiency; no unreported numeric peak matrix digitized.'),
 ('7','Figure7 Er doping plot, xDoped concentration(%) labeled1–7; yIntensity/a.u. labeled200–450. Actual markers1,2,3,4,5,7%; wavelength channel not identified. The high4% point remains; no6% data invented.'),
 ('8','Figure8 plots ln(I_up) versus ln(I_exc), xlabels2.0–4.0,y2–8, with squares519 nm slope2.2024,circles541 nm slope1.8853,triangles653 nm slope2.0907. Caption instead lists520,541,653 nm; body uses519 and rounded slopes. Keep exact graph/prose/caption distinctions.'),
 ('9','Figure9 level diagram: Yb²F7/2 and²F5/2; Er⁴I15/2,⁴I13/2,⁴I11/2,⁴I9/2,⁴F9/2,⁴S3/2,²H11/2,⁴F7/2.980 nm excitation, sensitizer-transfer arrow, upward steps/dashed relaxations and downward519/541/653 nm emission arrows retained as author model. No numerical level energies or lifetimes assigned.')])
add('figure-10',5,'Original Figure10 and caption','figure_metadata','Figure10 dotted bulk versus solid nanoparticle spectra under980 nm excitation. Wavelength axis400–750 nm, intensity a.u.0–900; whole spectra, legend and caption retained. No independently measured efficiency ratio, equal normalization or bulk crystallite-size distribution inferred.')
many('conclusion-',5,'Conclusions and acknowledgments','conclusion_or_administrative',[
 ('synthesis','Hydrothermal preparation of nearly spherical La2(MoO4)3:Yb,Er nanocrystal UCP with approximately50 nm mean diameter reiterated.'),
 ('optics','Annealing-temperature/Er-concentration effects, stronger nano than bulk fluorescent intensity, two-photon excitation and surface-effect interpretation reiterated with the same evidence limits.'),
 ('funding','National Science Foundation of China grants39989001,39825108 and National Key Basic Research Development ProgramG19990116 acknowledged. Funding is not a synthesis parameter.')])
add('source-missing',5,'End of article, supplied-main completeness','source_missingness','No SI declaration is visible in the five main pages; bounded local filename/content candidate search matched only two identical main copies. No CIF, raw spectra, diffraction refinement, absolute quantum yield, lifetime, elemental assay or complete concentration-series recipe supplied. No assertion that SI cannot exist.','retain_missingness_not_invented_data')
refs=[
'Bhargava, R. N. J. Lumin. 1997, 72–74, 46. Doped-nanocrystal optical and size-effect context.',
'Bhargava, R. N. J. Lumin. 1996, 70, 85. Quantum-confinement interpretation context.',
'Sharma, P. K.; Jilavi, M. H.; Nass, R.; Schmidt, H. J. Lumin. 1999, 82, 187. Surface/size effect context.',
'Sharma, P. K.; Jilavi, M. H.; Schmidt, H.; Varadan, V. K. Int. J. Inorg. Mater. 2000, 2, 407. Doped-nanocrystal context.',
'Chen, W.; Sammynaiken, R.; Huang, Y. N. J. Appl. Phys. 2000, 88, 5188. Down-conversion context.',
'Xie, P. B.; Zhang, W. P.; Yin, M.; Chen, H. T.; Zhang, W. W.; Lou, L. R.; Xia, S. D. J. Colloid. Interface Sci. 2000, 229, 534. Down-conversion context; abbreviation as printed.',
'Sharma, P. K.; Nass, R.; Schmidt, H. Opt. Mater. 1998, 10, 161. Down-conversion and surface effect.',
'Konrad, A.; Fries, T.; Gahn, A.; Kummer, F.; Herr. U.; Tidecks, R.; Samwer, K. J. Appl. Phys. 1999, 86, 3129. Down-conversion context; punctuation retained.',
'Tropper, A. C.; Carter, J. N.; Lader, R. D. T. J. Opt. Soc. Am. 1994, B11, 886. Up-conversion context; volume spelling retained.',
'Sandrock, T.; Scheife, H.; Heuman, E.; Huber, G. Opt. Lett. 1997, 22, 808. IR-pumped visible laser context.',
'Rijke, F. V. D.; Zijlmans, H.; Li, S.; Vail, T.; Raap, A. K.; Niedbala, R. S.; Tanke, H. J. Nat. Biotechnol. 2001, 19, 273. Bio-label context.',
'Hampl, J.; Hall, M.; Mufti, N. A.; Yao, Y. M.; Macquee, D. B.; Wright, W. H.; Cooper, D. E. Anal. Biochem. 2001, 288, 176. Bio-label context.',
'Zijlmans, H. J. M. A. A.; Bonnet, J.; Burton, J.; Kardos, K.; Tail, T.; Niedbala, R. S.; Tanke, H. J. Anal. Biochem. 1999, 267, 30. Multiplex detection context; Tail as printed.',
'Chan, W. C. W.; Nie, S. M. Science 1998, 281, 2013. Nanocrystal biological-label motivation.',
'Yu, X. Practical luminescent materials and mechanism of photoluminescence (in Chinese); Light Industrial Publishing Company of China: Beijing, 1997. Bulk preparation and emission comparator reference.',
'Huang, Q.; Xu, J. Z.; Li, W. Solid-State Ionics 1989, 32, 244. Host crystallographic/second-phase context.',
'Ribeiro, C. T. M.; Zanatta, A. R.; Nunes, L. A. O. J. Appl. Phys. 1998, 83, 4. Er transition assignment; printed locator retained.',
'Capobianco, J. A.; vetrone, F.; Alesio, T. D.; Tessari, G.; Speghini, A. Phys. Chem. Chem. Phys. 2002, 2, 3203. Up-conversion assignment; year/volume/names retained as printed without external correction.',
'Zhao, S. L.; Hou, Y. B.; Sun, L. J. Northern Jiaotong Univ. 2000, 24, 2. Near-IR transition assignment.',
'Sharma, P. K.; Jilavi, M. H.; Varadan, V. K.; Schmidt, H. J. Phys. Chem. Solids 2002, 63, 171. Annealing and surface-effect analogy.',
'Wu, X.; Denis, J. P. Appl. Phys. B: Laser Opt. 1993, 56, 269. Excitation power law.',
'Chamarro, M. A.; Cases, R. J. Lumin. 1990, 46, 59. Excitation power law.',
'Mosses, R. W.; Wells, J. P. R.; Gallagher, H. G.; Han, T. P. J.; Yamaga, M.; Kodama, N.; Yosida, T. Chem. Phys. Lett. 1998, 286, 291. Er energy-level mechanism; names retained as printed.',
'Silver, J.; Martinez-Rubio, M. I.; Ireland, T. G.; Fern, G. R.; Withnall, R. J. Phys. Chem. B 2001, 105, 948. Er energy-level mechanism.',
'Blasse, G.; Grabmaier, B. C. Luminescent Materials; Springer: Berlin, 1994. Environment coupling/lifetime interpretation.',
'Caurant, D.; Gourier, D.; Demoncy, N.; Ronot, I. J. Appl. Phys. 1995, 78, 876. Grinding/point-defect and CaS analogy.',
'Tamatani, N.; Tsuda, N.; Nomoto, K.; Nishimura, T.; Yokota, K. J. Lumin. 1976, 12–13, 935. Rare-earth oxysulfide grinding analogy.'
]
for n,t in enumerate(refs,1):add(f'reference-{n:02}',1 if n<=14 else 2 if n<=16 else 5,f'Reference {n}','bibliography',t,'retain_reference_not_independently_read')
for id,mass,amount in [('la',1.1760,3.607),('yb',.3692,.937),('er',.05370,.140)]:
 for suffix,v,u in [('mass',mass,'g'),('amount',amount,'mmol'),('purity',99.99,'%')]:fact(id+'-'+suffix,'precursor-'+id+'-oxide','Solution A','oxide '+suffix,v,u)
for i,uid,scope,prop,v,u,ap,st in [
 ('water-a','precursor-water-a','Solution A','added deionized water',30,'mL',False,'reported'),('water-b','precursor-water-b','Solution B','added deionized water',30,'mL',False,'reported'),('molybdate-mass','precursor-ammonium-molybdate','Solution B','printed ammonium molybdate mass',1.961,'g',False,'reported'),('molybdate-amount','precursor-ammonium-molybdate','Solution B','printed ammonium molybdate amount',9.37,'mmol',False,'reported'),
 ('stir-a','protocol-stock-a-stir','Solution A','stirring duration',1,'h',False,'reported'),('stir-b','protocol-stock-b-stir','Solution B','stirring duration',1,'h',False,'reported'),('postmix','protocol-suspension','Mixed suspension','stirring duration',20,'min',False,'reported'),('vessel','protocol-transfer','Hydrothermal setup','Teflon vessel nominal capacity',100,'mL',False,'reported'),('hydrothermal-temperature','protocol-hydrothermal','Hydrothermal','temperature',180,'°C',False,'reported'),('hydrothermal-duration','protocol-hydrothermal','Hydrothermal','hold duration',1,'h',False,'reported'),('centrifuge-speed','protocol-centrifuge','Recovery','centrifuge rotation',6000,'rpm',False,'reported'),('centrifuge-duration','protocol-centrifuge','Recovery','centrifugation duration',10,'min',False,'reported'),('wash-count','protocol-wash','Recovery','water washes',2,'count',False,'reported'),('nano-ramp','protocol-anneal-ramp','Standard800 °C nanocrystals','heating ramp',20,'°C/min',False,'reported'),('nano-temperature','protocol-anneal-hold','Standard nanocrystals','annealing temperature',800,'°C',False,'reported'),('nano-duration','protocol-anneal-hold','Standard nanocrystals','annealing duration',5,'h',False,'reported'),
 ('bulk-t','bulk-fire','Solid-state bulk comparator','firing temperature',1200,'°C',False,'reported'),('bulk-time','bulk-fire','Solid-state bulk comparator','firing duration',5,'h',False,'reported'),('laser-wavelength','method-upconversion','Up-conversion acquisition','external laser wavelength',980,'nm',False,'reported'),('laser-power','method-upconversion','Up-conversion laser source','stated source power',50,'mW',False,'reported'),
 ('xrd-peak','xrd-peak','800 °C/5 h nano','maximum-intensity peak2theta',28.053,'degree',False,'reported'),('xrd-b1','xrd-fwhm','800 °C/5 h nano','observed FWHM B1',.186,'degree',False,'reported'),('xrd-b0','xrd-fwhm','Diffractometer','instrumental width B0',.104,'degree',False,'reported'),('xrd-size','xrd-size','800 °C/5 h nano','Scherrer crystallite size',52.5,'nm',False,'author_derived'),('histogram-mean','size-distribution','Particle size analyzer; post-treatment not explicitly resolved','mean particle diameter',53,'nm',True,'reported'),('rounded-mean','size-rounding','Source study summary','rounded mean diameter',50,'nm',True,'reported'),
 ('down-excitation','optical-down-excitation','Down-conversion','excitation wavelength',374,'nm',False,'reported'),('abs-center','optical-abs-center','Nano near-IR absorption','peak wavenumber',10238,'cm−1',True,'reported'),('abs-wavelength','optical-abs-center','Nano near-IR absorption','printed peak wavelength equivalent',976,'nm',False,'reported'),('er-optimum','doping-optimum','Nominal Er sweep','selected Er mole fraction',3,'%',False,'reported'),
 ('fig2-before-scale','figure-2','TEM before anneal','scale bar',300,'nm',False,'figure_read'),('fig2-after-scale','figure-2','TEM after800 °C5 h','scale bar',100,'nm',False,'figure_read')]:fact(i,uid,scope,prop,v,u,approximate=ap,status=st)
fact('feed-rate','protocol-addition','B added into A','addition rate',unit='drops/min',minimum=20,maximum=30,qualifier='Drop volume unspecified; no mL/min conversion.')
for k,v in [('La',77),('Yb',20),('Er',3)]:fact('bulk-ratio-'+k.lower(),'bulk-composition','Bulk precursor feed',k+' relative cation molar proportion',v,'relative mol',qualifier='77:20:3; not directly measured product composition.')
fact('tem-most-range','size-tem-range','TEM source description','majority particle diameter range',unit='nm',minimum=40,maximum=60,qualifier='Most particles, not hard limits.')
fact('analyzer-most-range','size-distribution','Particle-size source description','majority diameter range',unit='nm',minimum=45,maximum=65,qualifier='Most particles, not hard limits; intensity histogram basis unresolved.')
for i,v in enumerate([525,549],1):fact('down-peak-'+str(i),'optical-down-peaks','Down-conversion at374 nm','emission peak'+str(i),v,'nm')
for i,v in enumerate([519,541,653],1):fact('up-peak-'+str(i),'optical-up-peaks','Up-conversion at980 nm','emission peak'+str(i),v,'nm')
fact('nir-scan','optical-abs-range','FTIR','reported scan interval',unit='cm−1',minimum=9000,maximum=11000)
fact('nir-window','optical-abs-window','Nano absorption','source excitation-window wavenumbers',unit='cm−1',minimum=9875,maximum=10625,qualifier='Original order10625–9875 cm−1 retained in source unit.')
fact('nir-window-nm','optical-abs-window','Nano absorption','printed window wavelength equivalent',unit='nm',minimum=941,maximum=1013)
for v in [600,700,800,900,1000]:
 fact('anneal-'+str(v)+'-temperature','anneal-series',str(v)+' °C variant','annealing temperature',v,'°C');fact('anneal-'+str(v)+'-duration','anneal-series',str(v)+' °C variant','annealing duration',5,'h')
fact('er-range','doping-scope','Nominal Er concentration comparison','reported Er range',unit='%',minimum=1,maximum=7,qualifier='Denominator/feed adjustments unresolved; no claim every integer point was prepared/measured.')
for v in [1,2,3,4,5,7]:fact('er-marker-'+str(v),'figure-7','Figure7 markers','plotted nominal Er concentration',v,'%',status='figure_read',qualifier='Figure-only x coordinate; no recreated reagent charges or digitized intensity.')
for wl,rounded,exact in [(519,2.20,2.2024),(541,1.89,1.8853),(653,2.09,2.0907)]:
 fact('slope-'+str(wl)+'-body','power-rounded-slopes',str(wl)+' nm channel','power exponent rounded in prose',rounded,'dimensionless',status='author_derived');fact('slope-'+str(wl)+'-plot','figure-8',str(wl)+' nm channel','power exponent printed in plot',exact,'dimensionless',status='author_derived',qualifier='Figure8 caption lists520 nm for first channel, unlike legend/body519 nm.')
fact('caption-channel','figure-8','Figure8 caption only','first channel wavelength',520,'nm',qualifier='Conflict with519 nm graph/body, not extra emission peak.')
fact('two-photon','power-two-photon','Author model','inferred absorbed IR photons per emitted photon',2,'count',status='author_interpretation')
fact('bulk-atmosphere','bulk-fire','Bulk firing','atmosphere','Air');fact('dry-atmosphere','protocol-dry','Preanneal powder drying','atmosphere','Air');fact('stock-temperature','protocol-stock-a-stir','A and B stirring','temperature','Room temperature',qualifier='No numerical temperature; does not assign optical acquisition temperature.')
fact('nano-symmetry','xrd-phase','800 °C/5 h nano','reported crystal system','Tetragonal',qualifier='A little unidentified second phase also stated; no space-group/refinement data.')
fact('xrd-reference','xrd-reference','Reference comparison','ICDD pattern identifier','45-0407',status='cited_context')
fact('molybdate-implied-mass','precursor-mass-amount-conflict','Curator arithmetic consistency check','mass/amount implied molar mass',1.961/.00937,'g/mol',status='curator_derived',qualifier='This is a check on printed values, not a replacement formula or source quantity.')
fact('reported-mo-ln','precursor-feed-stoichiometry','Curator arithmetic consistency check','printed Mo/total rare-earth atom mole ratio',9.37/(2*(3.607+.937+.140)),'ratio',status='curator_derived',qualifier='Nominal host expects3:2; do not repair the recipe or assert a measured composition from this check.')
ids=[x['id'] for x in U];assert len(ids)==len(set(ids));assert all(f['source_unit_id'] in ids for f in F)
candidates=[]
for path in [S,L]:
 pdf=PdfReader(str(path));text='\n'.join(p.extract_text() or '' for p in pdf.pages)
 candidates.append({'path':str(path),'sha256':sha(path),'page_count':len(pdf.pages),'metadata':dict(pdf.metadata or {}),'content_checks':{'doi':DOI in text,'title':'Up-Conversion' in text and 'Lanthanum Molybdate' in text,'authors':'Guangshun Yi' in text and 'Depu Chen' in text,'journal':'2910' in text and '2914' in text},'role':'main','identical_alias':path==L})
assert all(x['sha256']=='6438ee53b3fffb86f5e36508f265041d9235b8ee9f3e20dd99d46aae91c68a57' and x['page_count']==5 and all(x['content_checks'].values()) for x in candidates)
identity={'status':'passed_local_main_identity_no_matched_SI','source_id':SID,'doi':DOI,'title':'Synthesis and Characterization of High-Efficiency Nanocrystal Up-Conversion Phosphors: Ytterbium and Erbium Codoped Lanthanum Molybdate','source_sha256':sha(S),'page_count':5,'authors':['Guangshun Yi','Baoquan Sun','Fengzhen Yang','Depu Chen','Yuxiang Zhou','Jing Cheng'],'journal':'Chemistry of Materials','year':2002,'volume':14,'issue':7,'pages':'2910–2914','received':'2001-10-25','revised':'2002-03-29','published_online':'2002-06-19','candidates':candidates,'supporting_information':{'status':'not_located_or_matched','matched_count':0,'declaration_in_supplied_main':False,'search_scope':'Both local collections searched with rg --files filtered by cm0115416, yi.*up.?conversion and lanthanum.molybdate. Both resulting PDFs independently checked by hash, page count, metadata and DOI/title/byline content.','search_limit':'Bounded filenames and candidate-content identity; not exhaustive full-content search of every unrelated PDF and not proof SI cannot exist.'},'independent_visual_identity':True}
pages=[{'role':'main','pdf_page':p,'printed_page':2909+p,'text_path':str(B/f'main-{p:02}.txt'),'text_sha256':sha(B/f'main-{p:02}.txt'),'image_path':str(B/f'main-{p}.png'),'image_sha256':sha(B/f'main-{p}.png'),'text_read':True,'actually_visually_inspected':True,'unit_count':sum(u['pdf_page']==p for u in U)} for p in range(1,6)]
conflicts=['Printed ammonium molybdate1.961 g/9.37 mmol conflicts with the literal formula molar mass; reported Mo/rare-earth feed ratio also differs from nominal host stoichiometry. Both original quantities preserved; no identity or charge repair.','XRD reported tetragonal host has a little unidentified second phase. ICDD identifier is a citation, not an actual source CIF or dopant-site refinement.','TEM majority40–60 nm, histogram majority45–65 nm/about53 nm, Scherrer52.5 nm and rounded50 nm remain separate measurement bases.','800 °C optimum is selected despite stronger900 °C intensity; aggregation/size constraints matter.1000 °C annealed-nano outcome is distinct from1200 °C solid-state bulk comparator.','Figure7 has1,2,3,4,5,7% points and high4% intensity, unlike an implied uniform4–7% sharp decline. No6% point or three independent emission-channel series fabricated.','Figure8 caption520 nm conflicts with519 nm legend/body; exact plot slopes2.2024/1.8853/2.0907 and rounded prose2.20/1.89/2.09 coexist.','Figure5 inverse absorbance ordinate retained; Figure3 ordinateIntensity is not assigned particle-count or percentage weighting.','50 mW source power is not sample irradiance or exact sweep power. Actual fluorescence acquisition temperature and normalization remain unspecified.','Mechanistic energy-transfer, two-photon, surface-center, lifetime and defect explanations are interpretations; no measured transfer efficiency, lifetime, absolute quantum yield or bioassay demonstrated.','No matched local SI, complete dopant-series feed recipe, atomic coordinates or raw arrays supplied.']
report={'status':'complete_supplied_main_text_and_visual_inventory_no_matched_SI','source_id':SID,'doi':DOI,'source_sha256':sha(S),'audited_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent full five-page text and actual original-page visual review, every scientific paragraph, all ten figures/captions, unnumbered power law, named Scherrer method, references1–27 and acknowledgments.','units':U,'unit_count':len(U),'unit_kind_counts':dict(Counter(x['kind'] for x in U)),'typed_anchor_count':len(F),'page_coverage':pages,'figure_count':10,'table_count':0,'numbered_equation_count':0,'references_and_notes_count':27,'source_conflicts_and_limits':conflicts,'site_mutated':False,'downloaded_sources':False}
write('source-audit.json',report);write('source-facts.json',{'source_id':SID,'source_sha256':sha(S),'scope':'Source-native quantitative/categorical anchors plus explicitly separated curator arithmetic checks. None is automatically a training example.','facts':F});write('source-identity.json',identity);write('independent-page-coverage.json',{'source_id':SID,'source_sha256':sha(S),'pages':pages,'source_detail_images_actually_viewed':['source-detail-figure2.png','source-detail-figure8.png','source-detail-figure9.png']})
(B/'source-audit.md').write_text('# Yi 2002 independent source audit\n\nAll five supplied main pages were fully read and visually inspected. '+str(len(U))+' granular units and '+str(len(F))+' typed anchors cover ten figures, unnumbered mathematical relationships and all27references.\n\n'+'\n'.join('- '+x for x in conflicts)+'\n\nMain hydrothermal sequence and real solid-state bulk comparator remain distinct. No Site/monitor edits or downloads.\n',encoding='utf8')
(B/'source-identity.md').write_text('# Yi 2002 source identity\n\nVerified DOI '+DOI+', title, six-author byline, journal and date metadata against both identical local five-page main copies. SHA256 `'+sha(S)+'`.\n\nNo SI declaration was identified and no matching local SI found by the bounded filename/content-identity search. This does not prove no SI exists.\n',encoding='utf8')
print(json.dumps({'source_units':len(U),'typed_anchors':len(F),'source_audit_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json')},ensure_ascii=False))
