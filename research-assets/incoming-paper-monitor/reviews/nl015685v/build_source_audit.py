"""Independent complete supplied-main inventory. Source images/text read before authoring."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
L=Path(r'[local path redacted]')
SID='besson2002';DOI='10.1021/nl015685v';U=[];F=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(B/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def add(i,p,loc,kind,claim,disposition='retain_source_linked_evidence'):
 U.append({'id':SID+'-'+i,'source_unit_id':SID+'-'+i,'source_role':'main','pdf_page':p,'printed_page':408+p,'locator':loc,'kind':kind,'claim':claim,'disposition':disposition})
def many(prefix,p,loc,kind,rows,disposition='retain_source_linked_evidence'):
 for i,c in rows:add(prefix+i,p,loc,kind,c,disposition)
def fact(i,unitid,scope,prop,value=None,unit=None,minimum=None,maximum=None,approximate=False,status='reported',qualifier=''):
 F.append({'id':SID+'-fact-'+i,'source_unit_id':SID+'-'+unitid,'sample_scope':scope,'property':prop,'value':value,'minimum':minimum,'maximum':maximum,'unit':unit,'approximate':approximate,'status':status,'qualifier':qualifier,'eligible_training':False})
many('identity-',1,'Title, byline, dates and footer','source_metadata',[
 ('title','3D Quantum Dot Lattice Inside Mesoporous Silica Films.'),
 ('authors','Sophie Besson, Thierry Gacoin, Christian Ricolleau, Catherine Jacquiod and Jean-Pierre Boilot. Corresponding author Jean-Pierre Boilot; author affiliations are Ecole Polytechnique, CNRS/Saint-Gobain Surface du Verre et Interfaces, and Laboratoire de Minéralogie Cristallographie de Paris.'),
 ('journal','Nano Letters 2002, volume 2, issue 4, pages 409–414; DOI 10.1021/nl015685v.'),
 ('dates','Received November 29, 2001; revised manuscript January 23, 2002; published on web February 7, 2002.'),
 ('administrative','ACS copyright 2002 and article code NL015685V. July 1, 2026 download timestamp and malformed PDF creation metadata are not publication or experimental dates; PDF Title is No Job Name, not the scientific title.')],'retain_bibliographic_metadata')
many('abstract-',1,'Abstract','study_summary',[
 ('claim','The paper reports CdS quantum dots inside 3D hexagonal mesoporous silica films, with a proposed generalization to other II–VI semiconductors.'),
 ('evidence','Authors state XRD and electron microscopy demonstrate template control of CdS size and organization, giving a 3D quantum-dot lattice over a large scale; this is an author claim bounded by the supplied images and measurements.')])
many('context-',1,'Introduction','cited_context',[
 ('size-effects','Prior work motivates nanocrystals below 10 nm through metal local-field effects, semiconductor confinement and magnetic superparamagnetism; these are general literature claims, not new metal/magnet synthesis results.'),
 ('control','Particle size, shape, surface state and arrangement influence properties; periodic three-dimensional arrays are a stated synthesis objective.'),
 ('template','General mesoporous synthesis polymerizes inorganic species around surfactant micelles or copolymers; thermal removal leaves pores. This background does not specify a new executed copolymer recipe.'),
 ('pore-range','The introduction cites mesostructures with pores from 2 to 30 nm, varying shape and periodicity. This is literature scope, not the present film pore-size distribution.'),
 ('applications','Templates can control size/shape, support periodic 2D/3D arrays and optimize solid-matrix filling; collective effects are a motivation, not measured here.'),
 ('powders','Prior nanoparticle-filled powders often had random distributions or poorly controlled size; earlier periodic arrays had small domains except cited carbon/Pt replicas. No current carbon/Pt recipe should be created.'),
 ('nanowires','Earlier cylindrical-pore templates yielded nanowires; this remains cited context, not a nanowire variant of the present CdS route.'),
 ('films','Prior film studies used SiGe MBE, silicon-cluster CVD or silver nanoparticles with incomplete penetration/size/organization control; those are cited comparisons, not primary current recipes.')],'retain_cited_context_not_current_recipe')
many('chemical-',2,'Matrix preparation and impregnation protocol','chemical_identity_or_missingness',[
 ('teos','TEOS is explicitly Si(OC2H5)4, the silica sol precursor. Supplier, purity and batch amount are absent.'),
 ('acid-water','Water adjusted to pH 1.25 is mixed into the sol. Acid identity, acid concentration and adjustment method are absent; do not assume HCl.'),
 ('ethanol','Ethanol is both sol cosolvent and later dilution solvent. Initial molar ratio is specified; the later 1:1 dilution basis is not stated.'),
 ('ctab','CTAB is the surfactant for the detailed mesoporous-film route; CTAB/TEOS molar ratio 0.1. No grade, water content or supplier supplied.'),
 ('cd-nitrate','Cadmium nitrate aqueous solution is initially 0.1 M. Hydrate, purity, stock-making mass, total volume and final concentration after ligands/base addition are unreported.'),
 ('ammonia','Ammonia is added initially at one equivalent and additionally to pH 9.5. Stock concentration/form and final total dose are not supplied; it serves complexation and basicity roles.'),
 ('citrate','Sodium citrate is added at one equivalent from a 1 M aqueous stock. Salt stoichiometry/protonation, hydration, purity and stock preparation are not stated; do not silently assign a particular hydrate or an exact coordinated Cd complex.'),
 ('h2s','Gaseous H2S is the sulfide source after evacuation. Purity, injection flow, exposure time and gas dose are absent; its reported target pressure is atmospheric.'),
 ('rinse-water','Deionized water is explicitly the post-impregnation rinse; rinse volume, number, duration and drying procedure are absent.'),
 ('substrates','Pyrex slides support the detailed spin-coated films; silicon wafer supports the separate PL/excitation specimen to avoid Pyrex luminescence. These are distinct substrate contexts, not two serial deposition steps.'),
 ('copolymer','A second film uses an unspecified triblock copolymer, with larger spherical pores and an ordered 3D periodic structure. No polymer identity, block composition, molecular mass, ratio, matrix preparation or pore diameter supplied.'),
 ('matrix-product','CdS nanoparticles reside within a silica matrix; CdS and SiO2 are components of a composite, not a fixed whole-film stoichiometric formula or a core–shell ligand structure.')])
many('matrix-',2,'Detailed mesoporous matrix preparation, continuing between columns','protocol',[
 ('dependency','Matrix synthesis follows reference 29; references 29 and 30 support highly ordered/textured open films. These cited articles are not independently inspected upstream recipes in this task.'),
 ('sol-ratio','Mix TEOS, water of pH 1.25 and ethanol in a TEOS:water:ethanol molar ratio 1:5:3.8 under acidic conditions. No absolute scale or addition order/rate is reported.'),
 ('age','Age the polymeric silica sol for 1 h at 60 °C. Vessel, atmosphere, agitation, heating ramp and reflux conditions are absent.'),
 ('ctab-add','Dissolve CTAB in the aged sol with CTAB/TEOS molar ratio 0.1. Dissolution time and temperature are unreported.'),
 ('dilute','Dilute the obtained solution with ethanol at 1:1. The source does not explicitly say volume:volume, mass:mass or molar basis; do not silently normalize the ratio.'),
 ('coat','Deposit on Pyrex slides by spin-coating at 3000 rpm. Spin time, acceleration, dispense amount, substrate dimensions/cleaning and coating number are absent.'),
 ('calcine','Calcine films in air at 450 °C to remove surfactant. Heating/cooling ramp, hold time and gas flow are not supplied.'),
 ('film','Resulting highly ordered films are about 300 nm thick and have 3D hexagonal structure throughout, with c-axis perpendicular to substrate.'),
 ('open-porosity','Films have open porosity allowing solution impregnation through the thickness. This structural accessibility is necessary for the repeated filling process, not a quantified transport coefficient.')])
many('stock-',2,'Cadmium loading solution preparation','stock_protocol',[
 ('cd-start','Start from 0.1 M cadmium nitrate in water. This is the starting stock concentration, not a demonstrated final bath concentration after additions.'),
 ('ammonia-first','Add one equivalent ammonia to the cadmium nitrate solution. The source writes equivalents without an explicit calculation basis; relative-to-Cd interpretation must remain qualified and no mmol inferred.'),
 ('citrate','Add one equivalent sodium citrate, with its aqueous stock concentration stated as 1 M. No total stock volume, exact salt or final bath volume supplied.'),
 ('ph','Complete the solution with additional ammonia until pH 9.5. The initial one-equivalent charge is not the full ammonia dose.'),
 ('complex','Citrate and ammonia maintain soluble cadmium species in the required basic range; exact equilibrium speciation or coordination number is not measured.'),
 ('ph-window','The general strategy recommends cadmium adsorption at pH 9–10; adsorption is optimal above pH 9 whereas silica partially dissolves above pH 10. Actual specified loading bath is pH 9.5.'),
 ('hydroxides','Complexing agents are generally required to avoid hydroxide precipitation. No discrete Cd(OH)2 precipitate product or Cd ammine molecular structure is measured here.')])
many('loading-',2,'Impregnation, washing and H2S precipitation','protocol',[
 ('impregnate','Impregnate the calcined porous film with the basic cadmium-nitrate/citrate/ammonia solution. Soak time, bath volume, film area, loading temperature and vessel are unreported.'),
 ('rinse','Wash the film in deionized water to eliminate excess cations and obtain a clean surface. Source stresses preventing cation accumulation at the film–air interface.'),
 ('retention','Authors state strong cadmium interactions with Si–O− groups cause no significant leaching during rinsing. This is a qualitative claim without a leached-fraction assay table.'),
 ('evacuate','Place the impregnated/rinsed film under vacuum before introducing H2S. Vacuum level, duration, apparatus and drying extent are not specified.'),
 ('gas','Inject gaseous H2S slowly until P_H2S equals P_atm. This is a stated atmospheric-pressure endpoint, not a known numerical pressure, flow or reaction duration.'),
 ('repeat','Repeat impregnation and precipitation until film saturation. The rinse and vacuum steps belong to the common cycle; this is repeated growth within a film, not multiple independent syntheses.'),
 ('gas-rationale','Authors argue gaseous H2S diffuses rapidly through the film and precipitates CdS simultaneously in the pores, avoiding isolated domains sealed by nanoparticles. This is a mechanistic explanation, not a measured diffusion time.'),
 ('silanol-regeneration','CdS precipitation is said to regenerate pore-surface silanols, enabling new cadmium adsorption and further cycles.'),
 ('missing','No final isolated yield/mass, exact CdS loading per cycle, storage condition, post-H2S purge or wash, or detached-powder recovery is stated.')])
many('ctab-',2,'CdS filling of the CTAB-templated film','sample_and_measurement',[
 ('colors','Cd2+-impregnated film is colorless; after first H2S treatment it is light yellow, with stronger color during later impregnation cycles.'),
 ('saturation','CTAB film reaches optical saturation after nine impregnation–precipitation cycles.'),
 ('size-first','Gap–size correlation curves from reference 35 give an average CdS diameter of 2.2 nm after one impregnation/precipitation cycle.'),
 ('size-final','The same correlation gives average diameter 3.6 nm at saturation, Figure 1b. This is author-derived optical size, not a measured TEM histogram mean.'),
 ('exciton','Visible excitonic transitions are interpreted as evidence of a narrow size distribution. No numerical dispersion, population count or fit uncertainty supplied.'),
 ('size-control','Agreement between final particle size and pore dimensions suggests confinement by the template, supported by the copolymer comparison. Exact particle shape is not established by absorption alone.')])
many('copolymer-',2,'Preliminary larger-pore matrix comparison, Figure 1c–d','partial_variant_and_measurement',[
 ('scope','A separately templated film using an unidentified triblock copolymer has larger spherical pores and highly ordered 3D periodic structure; reference 37 is only to be published.'),
 ('recipe-gap','The paper does not report this copolymer film preparation or independently restate every loading parameter. Do not treat the CTAB/TEOS ratio or 3D-hexagonal assignment as established for this unidentified matrix.'),
 ('redshift','Absorption edge is shifted toward longer wavelength versus CTAB-derived material; authors infer larger CdS particles.'),
 ('size-first','Average CdS diameter grows from 3.3 nm after the first impregnation/precipitation.'),
 ('size-final','Average diameter reaches 5.8 nm at stated saturation; Figure 1d final plotted endpoint is six impregnations, while prose gives no explicit numeric saturation cycle count for this matrix.'),
 ('exciton-loss','Excitonic transitions are no longer present after the second impregnation; authors attribute this to weak confinement for sizes above 5 nm, citing reference 35. Preserve source wording about after the second step, without inventing an exact detection threshold.'),
 ('generalization','Appropriate template pore size is proposed to tune nanocrystal size; no additional polymer or semiconductor formulations are experimentally specified.')])
many('uv-',2,'UV-visible absorption and Figure 1','analytical_method',[
 ('acquisition','Absorption spectrum is followed after each impregnation–precipitation cycle. Absorption instrument, optical geometry, substrate correction, acquisition temperature and raw numeric spectrum are not supplied.'),
 ('size-model','Optical gap–size correlation from reference 35 underlies reported average particle sizes; explicit fitting equation, numerical gap values and fit uncertainties are not given here.')])
many('sims-',2,'SIMS paragraph','analytical_method_and_result',[
 ('method','Secondary-ion mass spectrometry analyses are reported, with no model, primary-ion conditions, sputtering calibration or plotted depth profile.'),
 ('result','Cadmium is described as homogeneous with depth in both the Cd2+-impregnated film and CdS-saturated film. These are distinct stages; SIMS uniformity is not an elemental atomic-percentage table.')])
many('xrd-',2,'XRD method and Figure 2 discussion','analytical_method_and_result',[
 ('instrument','XRD uses Cu Kα radiation on an X’Pert Philips diffractometer in Bragg–Brentano geometry; no scan speed, step size or exposure given.'),
 ('texture','Only the 0002 mesostructural peak and its harmonic appear in this geometry due to c-axis texture perpendicular to the film plane. They are mesolattice reflections, not atomic CdS Bragg peaks.'),
 ('initial-change','Cadmium adsorption reduces the 0002 intensity to about one-half of the calcined film and shifts the peak to larger 2θ. This prose intensity comparison is separate from the plot’s display-rescaling factors.')])
many('xrd-',3,'XRD discussion and Figure 2','measurement_or_author_interpretation',[
 ('initial-c','The c parameter decreases from 6.9 nm in the initial calcined film to 6.8 nm after cadmium adsorption.'),
 ('condensation','Authors attribute this small contraction possibly to silica-wall condensation caused by high-pH impregnation; it is an interpretation rather than an independently measured condensation reaction.'),
 ('h2s-first','First H2S exposure drastically lowers the 0002 intensity; subsequent cycles increase it progressively until saturation.'),
 ('contrast-adsorb','Adsorbed cadmium increases pore electron density and reduces silica–pore scattering contrast.'),
 ('contrast-cds','Growing CdS increases pore scattering above that of silica walls, producing contrast inversion: near-disappearance then recovery of the 0002 peak. This qualitative model must not be read as loss and reappearance of crystal ordering.'),
 ('width','No significant 0002-width change accompanies intensity changes; authors infer constant ordered-domain size and preserved order. No FWHM, Scherrer size or correlation-length value supplied.'),
 ('final-c','Peak shifts back to lower 2θ during filling; c increases from 6.8 nm before the first H2S treatment to 7.2 nm at saturation.'),
 ('deformation','Authors interpret the increase as deformation on full pore filling; prior InP-in-mesoporous-powder work is cited as an analogy, not a current InP recipe.'),
 ('combined','UV-visible and XRD are interpreted together as showing CdS growth inside pores without loss of the original organization, supporting periodic particle distribution.')])
many('filling-',3,'Absorbance-reference and porosity comparison','author_derived_quantity',[
 ('comparator','Optical calibration compares the absorbance maximum with a CdS colloid of average size 3.5 nm. Reference 38 says it was made by reverse micelles following reference 42; no complete comparator synthesis is supplied.'),
 ('cds-fraction','Authors derive a 13% CdS volume fraction in the saturated film from the absorbance reference. Extinction coefficient, film optical path calculation and error estimate are not supplied.'),
 ('pore-fraction','A 15% mesoporous volume fraction is deduced from crystallographic data using two mesopores per hexagonal unit cell. This is a template volume fraction, not a CdS chemical stoichiometry.'),
 ('occupancy','Authors report about 85% pore-space filling in the saturated film from those estimates. Preserve the reported rounded value; do not replace it by an artificially exact 13/15 result.'),
 ('diameter-scope','The optical size at saturation is 3.6 nm, whereas the calibration colloid is described as the same average size of 3.5 nm and note 36 estimates a 3.5 nm pore. Preserve these distinct model/comparator dimensions without averaging.')])
many('tem-',3,'TEM method before Figure 3','analytical_method',[
 ('instrument','Saturated film is examined in cross section on a Topcon 002B TEM at 200 kV, with reported point-to-point resolution 0.18 nm.'),
 ('focus','HRTEM images are slightly underfocused to enhance particle contrast; exact defocus, sample preparation, cross-sectional thickness and exposure are not supplied.')])
many('tem-',4,'Figure 3 and accompanying discussion','measurement_or_author_interpretation',[
 ('filled','Figure 3a is the CdS-saturated film; CdS dots appear dark on a bright background.'),
 ('empty','Figure 3b is a separate calcined mesoporous film before impregnation, with pores bright on a dark background. It is a matrix-control specimen, not the CdS-loaded product.'),
 ('contrast','Authors compare contrast inversion with XRD. They note sensitivity to zone axis, thickness, defocus and voltage, and assume thickness/conditions and identical underfocus to attribute inversion to CdS/SiO2 versus air/SiO2 scattering.'),
 ('residual-pores','The text calls the film totally filled but explicitly notes a few white empty pores near the film–substrate interface. This qualitative observation must not overwrite the separate ~85% volume-filling estimate.'),
 ('enlargement','Figure 3c enlarges the filled cross section and shows periodic particle organization; no segmented particle-size histogram or occupancy count is supplied.'),
 ('cds-lattice','Some clusters show 111 fringes assigned to blende-type CdS, which the authors relate to known behavior at these sizes (reference 39). This supports a source phase assignment for imaged clusters, not a refined atomic unit cell or uniform phase-fraction determination.'),
 ('orientations','The darkest particles are interpreted as lying near a zone axis/strong Bragg condition; others have different orientations. No common atomic orientation of every CdS particle is established.'),
 ('projection','Figure 3c is a projected 3D superlattice slightly misaligned from the [1 1 −2 0] direction as printed; superposition is used to explain gray contrast between particles. Exact orientation angle is absent.'),
 ('power-spectrum','Figure 3d is the image power spectrum, defined as |Fourier transform|², of the filled-film cross section. It is not a separately acquired selected-area electron-diffraction pattern.'),
 ('mesosymmetry','Pattern is compared to reference 30 and assigned to the 3D hexagonal mesostructure with space group P63/mmc. This symmetry belongs to the pore/particle-center lattice, not the atomic CdS lattice.'),
 ('mesoparameters','Power-spectrum discussion gives approximate mesolattice a=6.0 nm, c=6.8 nm and c/a=1.13, said consistent with empty film.'),
 ('c-conflict','The HRTEM discussion of saturated film gives c≈6.8 nm, whereas XRD discussion reports c=7.2 nm at saturation. Different methods/scopes and approximations must be retained; no single corrected lattice parameter is justified.'),
 ('conclusion','Authors interpret HRTEM as demonstrating homogeneous filling and control of particle size/organization by the porous structure. Preserve this interpretation alongside residual empty pores and absence of quantitative particle statistics.')])
many('pl-',4,'PL/excitation method continuing on p. 413','analytical_method',[
 ('instrument','Photoluminescence and excitation spectra use a Hitachi F-4500 fluorescence spectrophotometer. Excitation/collection wavelengths, slits, scan parameters and intensity normalization are not tabulated.')])
many('pl-',5,'Optical results and Figure 4','sample_measurement_or_interpretation',[
 ('substrate','The PL specimen is a mesoporous film deposited on silicon wafer to avoid Pyrex-slide luminescence. It is a separate substrate branch; source does not restate the complete coating recipe or a distinct final film thickness.'),
 ('temperature','Figure 4 spectra are taken at room temperature; no numerical value specified. Do not silently transfer this condition to impregnation or gas reaction.'),
 ('first-h2s','Body text says after first H2S treatment only weak broad emission around 640 nm is observed, assigned to surface defects.'),
 ('next-cd','Body text says following impregnation in the cadmium solution enhances the 640 nm surface band, attributed to sulfur vacancies at nanoparticle surfaces.'),
 ('bound-exciton','Body text describes a sharp band at 450 nm after that following cadmium impregnation, assigned to direct recombination of a bound exciton.'),
 ('passivation','Authors suggest ammonia or hydroxyl surface complexation may passivate CdS and allow the sharp exciton emission, citing prior studies. No measured molecular surface structure or unique ligand coverage is established.'),
 ('later-cycles','After the second H2S treatment and later impregnations the emission decreases and bound-exciton luminescence disappears. No quantitative rate, quantum yield, detection limit or cycle-by-cycle peak table is supplied.'),
 ('wall-rationale','Growth may reduce surface accessibility and increase interactions with silica walls, suppressing direct exciton recombination; the mechanism is conjectural and supported by cited reference 42.'),
 ('caption-conflict','Figure 4 caption labels upper curves as after first H2S and lower curves as after following cadmium impregnation. This conflicts with body text’s weak-first/enhanced-after-Cd narrative and visible stronger upper curves with a sharp feature. Preserve both source assignments without silently relabeling.'),
 ('excitation-limits','Dashed excitation spectra are shown, but excitation-monitor wavelengths and numerical excitation peak assignments are not specified. Do not turn the emission peaks into excitation settings.')])
many('figure-',3,'Original figures and captions','original_figure_or_axis_metadata',[
 ('1','Figure 1 has CTAB absorption(a)/optical particle diameter(b) and copolymer absorption(c)/diameter(d) versus impregnation count. Absorption axes are 300–600 nm, displayed absorbance 0–0.5; original curves may extend beyond the top plot limit. Panel b vertical range reaches 4 nm, panel d 6 nm. No raw arrays provided.'),
 ('1-ctab-series','CTAB panel a labels calcined film and cycles 1,2,3,4,5,7,9. Panel b includes the final nine-cycle diameter; plotted lines connect observations and are not a fitted kinetic law.'),
 ('1-copolymer-series','Copolymer panel c labels calcined film and cycles 1,2,3,4,6; panel d ends at six impregnations. Figure endpoint supports a six-cycle observation but should remain distinct from an explicitly stated general saturation-cycle count.'),
 ('2','Figure 2 is the low-angle XRD series: intensity (a.u.) versus 2θ in degrees, displayed about 2.2–2.9°. It includes calcined film, cadmium-impregnated film and cycle-labelled CdS states.'),
 ('2-rescaling','Figure 2 explicitly scales calcined film by ×0.5 and first-cycle trace by ×5. Peak heights cannot be directly compared as unscaled quantitative intensity or loading values.'),
 ('2-series','Figure 2 labels cycles 1,2,3,4,5,7,9, alongside the Cd2+-impregnated precursor film. The low-angle reflection concerns mesoscopic ordering.')])
many('figure-',4,'Original Figure 3 and caption','original_figure_or_axis_metadata',[
 ('3','Four panels: a filled film cross section; b calcined empty-film cross section; c enlargement of a; d Fourier power spectrum of a. Preserve their distinct roles and contrast assumptions.'),
 ('3-scales','Panels a and b have 30 nm scale bars; panel c has 20 nm scale bar. These are scale lengths, not particle diameters or template lattice parameters.'),
 ('3-indices','Power spectrum d labels (0 0 0 2), (0 1 −1 1) and (0 1 −1 0) mesolattice spots as printed. Preserve the third-index overbar from the original image rather than silently mapping these labels to atomic CdS diffraction.')])
add('figure-4',5,'Figure 4 and caption','original_figure_or_axis_metadata','Excitation curves are dashed; luminescence curves solid. Axes: wavelength about 300–700 nm, intensity in arbitrary units without numeric calibrated vertical values. Upper/lower curve assignments have the explicit caption/body conflict; no digitization or absolute intensity reconstructed.')
many('conclusion-',5,'Concluding paragraphs','author_interpretation_and_outlook',[
 ('control','Authors report filling a 300 nm film with CdS while template controls size and 3D organization; large-scale extension over glass is contrasted with small colloidal self-assembled ordered regions.'),
 ('connectivity','Repeated loading without structural deterioration is interpreted as demonstrating pores open to the exterior and interconnected. No pore-neck diameter or connectivity tomography supplied.'),
 ('repeat-necessity','Several impregnation–precipitation cycles are argued necessary for saturation compared with literature single-cycle approaches.'),
 ('extension','Method could be generalized to other sulfides or selenides provided their cations anchor to silica. This is future scope; no additional semiconductor recipe or measured property is supplied.')])
add('acknowledgment',5,'Acknowledgment','source_metadata','Supported by Saint Gobain Recherche; T. Cretin thanked for SIMS analyses. Funding/operator acknowledgment is not a synthesis condition.','retain_bibliographic_metadata')
add('note-36',5,'Reference 36','author_derived_model','Assuming spherical pores and using hexagonal unit-cell volume determined by XRD, porosity measurements imply average pore diameter 3.5 nm. It is a model-based average, not a direct pore image measurement or a supplied atomic CIF.','retain_source_linked_evidence')
add('note-38',6,'Reference 38','comparator_recipe_limit','The 3.5 nm CdS calibration colloid was prepared by a reverse-micelle technique following reference 42. No quantities, surfactant identity, stock recipes or full protocol are supplied; do not create a fully reproducible comparator recipe.','retain_cited_context_not_current_recipe')
add('source-missing',6,'Complete supplied main article','missingness','No Supporting Information declaration is seen in the six supplied pages. No local SI is independently matched. Raw spectra, SIMS profile, lifetime/QY, SAED acquisition, full size distributions, refined atomic coordinates, reagent hydration, several bath/timing details and complete copolymer matrix recipe are absent.','retain_coverage_limitation')

refs=[
('Flytzanis, C.; Hache, F.; Klein, M. C.; Ricard, D.; Roussignol, P. Progress in Optics; Wolf, E., Ed.; North-Holland: Amsterdam, 1991; Vol. 24, p 321.','Metal optical local-field background.'),
('Alivisatos, A. P. J. Phys. Chem. 1996, 100, 13226.','Semiconductor nanocrystal background.'),
('Bean, C. B.; Livingston, J. D. J. Appl. Phys. 1959, 30, 120.','Superparamagnetism context; names as printed.'),
('Shipway, A. N.; Katz, E.; Willner, I. ChemPhysChem 2000, 1, 18.','Nanoparticle organization/applications context.'),
('Beck, J. S.; Vartuli, J. C.; Roth, W. J.; Leonowicz, M. E.; Kresge, C. T.; Schmitt, K. D.; Chu, C. T.-W.; Olson, K. H.; Sheppard, E. W.; McCullen, S. B.; Higgins, J. B.; Schlenk, J. L. J. Am. Chem. Soc. 1992, 114(27), 10834.','MCM-41 history.'),
('Huo, Q.; Margolese, D. I.; Stucky, G. D. Chem. Mater. 1996, 8, 1147.','Mesopore structures.'),
('Zhao, D.; Huo, Q.; Feng, J.; Chmelka, B. F.; Stucky, G. D. J. Am. Chem. Soc. 1998, 120, 6024.','Mesopore structures.'),
('Takagahara, T. Surf. Sci. 1992, 267, 310.','Collective effects motivation.'),
('Murray, C. B.; Kagan, C. R.; Bawendi, M. G. Annu. Rev. Mater. Sci. 2000, 30, 545.','Colloidal assemblies and size of ordered domains.'),
('Agger, J. R.; Anderson, M. W.; Pemble, M. E.; Terasaki, O.; Nozue, Y. J. Phys. Chem. B 1998, 102, 3345.','Prior mesoporous nanoparticles/InP deformation comparison.'),
('Srdanov, V. I.; Alxneit, I.; Stucky, G. D.; Reaves, C. M.; DenBaars, S. M. J. Phys. Chem. B 1998, 102, 3341.','Mesoporous powder nanocrystal context.'),
('Winkler, H.; Birkner, A.; Hagen, V.; Wolf, I.; Schmechel, R.; von Seggern, H.; Fisher, R. A. Adv. Mater. 1999, 11(17), 1444.','Mesoporous powder context; Fisher as printed.'),
('Parala, H.; Winkler, H.; Kolbe, M.; Wohlfart, A.; Fischer, R. A.; Schmechel, R.; von Seggern, H. Adv. Mater. 2000, 12(14), 1050.','Mesoporous powder context.'),
('Zhang, W.-H.; Shi, J.-L.; Chen, H.-R.; Hua, Z.-L.; Yan, D.-S. Chem. Mater. 2001, 13, 648.','Mesoporous powder context.'),
('Zheng, S.; Gao, L.; Zhang, Q.-H.; Guo, J.-K. J. Mater. Chem. 2000, 10, 723.','Mesoporous powder context.'),
('Fröba, M.; Köhn, R.; Bouffaud, G. Chem. Mater. 1999, 11, 2858.','Mesoporous powder context.'),
('Jung, J. S.; Chae, W. S.; McIntyre, R. A.; Seip, C. T.; Wiley, J. B.; O’Connor, C. J. Mater. Res. Bull. 1999, 34(9), 1353.','Mesoporous powder context; source punctuation retained conceptually.'),
('Wang, L.-Z.; Shi, J.-L.; Zhang, W.-H.; Ruan, M.-L.; Yu, J.; Yan, D.-S. Chem. Mater. 1999, 11, 3015.','Prior periodic nanoparticle arrays.'),
('Kang, H.; Jun, Y.-W.; Park, J.-L.; Lee, K.-B.; Cheon, J. Chem. Mater. 2000, 12, 3530.','Prior arrays/nanowires.'),
('Ryoo, R.; Joo, S. H.; Jun, S. J. Phy. Chem. B 1999, 103(37), 7743.','Carbon replica context; journal abbreviation as printed.'),
('Jun, S.; Joo, S. H.; Ryoo, R.; Kruk, M.; Jaroniec, M.; Liu, Z.; Ohsuna, T.; Terasaki, O. J. Am. Chem. Soc. 2000, 122, 10712.','Carbon replica context.'),
('Shin, H. J.; Ko, C. H.; Ryoo, R. J. Mater. Chem. 2001, 11, 260.','Platinum replica context.'),
('Shin, H. J.; Ryoo, R.; Liu, Z.; Terasaki, O. J. Am. Chem. Soc. 2001, 123, 1246.','Platinum replica context.'),
('Leon, R.; Margolese, D.; Stucky, G. D.; Petroff, P. M. Phys. Rev. B 1995, 52(4), 2285.','Nanowire context.'),
('Han, Y.-J.; Kim, J. M.; Stucky, G. D. Chem. Mater. 2000, 12, 2068.','Nanowire context.'),
('Tang, Y. S.; Cai, S. J.; Jin, G. L.; Wang, K. L.; Soyer, H. M.; Dunn, B. S. Thin Solid Films 1998, 321, 76.','SiGe MBE film comparison.'),
('Dag, Ö.; Ozin, G. A.; Yang, H.; Reber, C.; Bussière, G. Adv. Mater. 1999, 11(6), 474.','Silicon CVD film comparison.'),
('Plyuto, Y.; Berquier, J.-M.; Jacquiod, C.; Ricolleau, C. Chem. Commun. 1999, 1653.','Silver-loaded film comparison.'),
('Besson, S.; Gacoin, T.; Jacquiod, C.; Ricolleau, C.; Babonneau, D.; Boilot, J.-P. J. Mater. Chem. 2000, 10, 1331.','Detailed matrix preparation dependency.'),
('Besson, S.; Ricolleau, C.; Gacoin, T.; Jacquiod, C.; Boilot, J.-P. J. Phys. Chem. B 2000, 104(51), 12095.','Prior hexagonal film morphology/Fourier structure comparison.'),
('Iler, R. K. The Chemistry of Silica; Wiley-Interscience: New York, 1979; pp 667–676.','Silica adsorption/dissolution pH rationale.'),
('Hirai, T.; Okubo, H.; Komasawa, I. J. Phys. Chem. B 1999, 103, 4228.','Prior single-impregnation CdS powder route.'),
('Wellmann, H.; Rathousky, J.; Wark, M.; Zukal, A.; Schulz-Ekloff, G. Microporous Mesoporous Mater. 2001, 44–45, 419.','Prior single-impregnation context.'),
('Zhang, Z.; Dai, S.; Fan, X.; Blom, D. A.; Pennycook, S. J.; Wei, Y. J. Phys. Chem. B 2001, 105(29), 6755.','Prior single-impregnation context.'),
('Wang, Y.; Herron, N. Phys. Rev. B 1990, 42, 7253.','Optical gap–size correlation and confinement comparison.'),
('Source note: assuming spherical pores and XRD hexagonal unit-cell volume, porosity measurements imply average pore diameter 3.5 nm.','Model-based pore estimate, separately inventoried note 36.'),
('Besson, S.; Gacoin, T.; Ricolleau, C.; Jacquiod, C.; Boilot, J.-P., to be published.','Unidentified future copolymer-matrix dependency; no title/DOI/year inferred.'),
('Source note: the reference CdS colloid was made using the reverse-micelle technique; see reference 42.','Incomplete comparator preparation, separately inventoried note 38.'),
('Ricolleau, C.; Audinet, L.; Gandais, M.; Gacoin, T. Eur. Phys. J. D 1999, 9, 565.','Prior blende CdS size-range context.'),
('Wang, Y.; Suna, A.; McHugh, J.; Hilinski, E. F.; Lucas, P. A.; Johnson, R. D. J. Chem. Phys. 1990, 92(11), 6927.','Surface vacancy/passivation optical interpretation.'),
('Spahnel, L.; Hasse, M.; Weller, H.; Heinglein, A. J. Am. Chem. Soc. 1987, 109(19), 5649.','Names retained as printed; cited CdS passivation context, not independently corrected bibliography.'),
('Gacoin, T.; Malier, L.; Counio, G.; Esnouf, S.; Boilot, J.-P.; Audinet, L.; Ricolleau, C.; Gandais, M. MRS Proceedings (Better Ceramics through Chemistry VII) 1996, 435, 643.','Comparator reverse-micelle method and silica-interaction optical context.'),
('Murray, C. B.; Kagan, C. R.; Bawendi, M. G. Science 1995, 270, 1335.','Colloidal self-assembly comparison.')]
for n,(cite,scope) in enumerate(refs,1):add(f'reference-{n:02}',5 if n<=37 else 6,f'References, entry {n}','cited_reference',cite+' '+scope,'retain_reference_not_new_experiment')

# Numeric/categorical source facts retain context and model status; this is an audit inventory, not extra training outcomes.
for args in [
 ('matrix-water-ph','matrix-sol-ratio','Acidified input water','pH',1.25,'pH'),
 ('matrix-teos-ratio','matrix-sol-ratio','Initial sol ratio','TEOS molar parts',1,'molar_parts'),
 ('matrix-water-ratio','matrix-sol-ratio','Initial sol ratio','Water molar parts',5,'molar_parts'),
 ('matrix-ethanol-ratio','matrix-sol-ratio','Initial sol ratio','Ethanol molar parts',3.8,'molar_parts'),
 ('matrix-age-time','matrix-age','Sol aging','duration',1,'h'),
 ('matrix-age-temperature','matrix-age','Sol aging','temperature',60,'degC'),
 ('matrix-ctab-ratio','matrix-ctab-add','CTAB film sol','CTAB/TEOS molar ratio',.1,'mol/mol'),
 ('matrix-dilution','matrix-dilute','Sol dilution','ethanol dilution ratio','1:1',None),
 ('matrix-spin','matrix-coat','Pyrex coating','spin speed',3000,'rpm'),
 ('matrix-calcination','matrix-calcine','Matrix calcination','temperature',450,'degC'),
 ('matrix-calcination-atmosphere','matrix-calcine','Matrix calcination','atmosphere','Air',None),
 ('cd-start','stock-cd-start','Starting cadmium nitrate stock','concentration',.1,'M'),
 ('nh3-first','stock-ammonia-first','Initial ammonia addition','amount ratio',1,'equivalent'),
 ('citrate-equivalent','stock-citrate','Citrate addition','amount ratio',1,'equivalent'),
 ('citrate-stock','stock-citrate','Sodium citrate input stock','concentration',1,'M'),
 ('loading-ph','stock-ph','Final loading bath','pH',9.5,'pH'),
 ('gas-pressure','loading-gas','H2S precipitation','pressure endpoint','P_H2S = P_atm',None),
 ('ctab-cycle','ctab-saturation','CTAB CdS-loaded film','saturation cycle count',9,'cycles'),
 ('xrd-c-initial','xrd-initial-c','Calcined empty CTAB film','mesolattice c',6.9,'nm'),
 ('xrd-c-cd','xrd-initial-c','Cadmium-impregnated CTAB film before first H2S','mesolattice c',6.8,'nm'),
 ('xrd-c-final','xrd-final-c','CdS-saturated CTAB film','mesolattice c',7.2,'nm'),
 ('filling-cds','filling-cds-fraction','Saturated film optical-reference estimate','CdS volume fraction',13,'%'),
 ('filling-pore','filling-pore-fraction','Template crystallographic estimate','Pore volume fraction',15,'%'),
 ('filling-multiplicity','filling-pore-fraction','Hexagonal mesolattice model','Mesopores per cell',2,'count'),
 ('comparator-size','filling-comparator','Separate reverse-micelle CdS comparator','average diameter',3.5,'nm'),
 ('tem-voltage','tem-instrument','Topcon 002B HRTEM','accelerating voltage',200,'kV'),
 ('tem-resolution','tem-instrument','Topcon 002B HRTEM','point resolution',.18,'nm'),
 ('mesospacegroup','tem-mesosymmetry','Pore/particle-center superlattice','space group','P63/mmc',None),
 ('meso-ratio','tem-mesoparameters','HRTEM power-spectrum mesolattice','c/a',1.13,'ratio'),
 ('pl-bound-exciton','pl-bound-exciton','Following Cd impregnation, per body text','bound-exciton emission wavelength',450,'nm'),
 ('pl-temperature','pl-temperature','Figure 4 optical measurements','temperature description','Room temperature',None),
 ('figure2-initial-scale','figure-2-rescaling','Calcined trace display','scale factor',.5,'ratio'),
 ('figure2-first-scale','figure-2-rescaling','First-cycle trace display','scale factor',5,'ratio'),
 ('figure3a-scale','figure-3-scales','Figure 3a','scale bar',30,'nm'),
 ('figure3b-scale','figure-3-scales','Figure 3b','scale bar',30,'nm'),
 ('figure3c-scale','figure-3-scales','Figure 3c','scale bar',20,'nm')]:fact(*args)
for args in [
 ('film-thickness','matrix-film','Detailed CTAB mesoporous film','thickness',300,'nm'),
 ('meso-a','tem-mesoparameters','HRTEM power-spectrum mesolattice','a',6.0,'nm'),
 ('meso-c','tem-mesoparameters','HRTEM power-spectrum mesolattice','c',6.8,'nm'),
 ('pl-defect-first','pl-first-h2s','First H2S state, body text','surface-defect emission wavelength',640,'nm'),
 ('pl-defect-next','pl-next-cd','Following Cd impregnation, body text','surface-defect emission wavelength',640,'nm')]:fact(*args,approximate=True)
for i,u,s,p,v in [
 ('ctab-size-first','ctab-size-first','CTAB first cycle','optical correlation average diameter',2.2),
 ('ctab-size-final','ctab-size-final','CTAB saturation','optical correlation average diameter',3.6),
 ('copolymer-size-first','copolymer-size-first','Copolymer first cycle','optical correlation average diameter',3.3),
 ('copolymer-size-final','copolymer-size-final','Copolymer saturation','optical correlation average diameter',5.8),
 ('pore-size-model','note-36','Spherical-pore assumption and porosity/XRD','average pore diameter',3.5)]:fact(i,u,s,p,v,'nm',status='author_derived')
fact('pore-occupancy','filling-occupancy','Saturated-film volume estimate','pore filling',85,'%',approximate=True,status='author_derived')
fact('copolymer-cycle','copolymer-size-final','Figure 1d terminal plotted state','impregnation count',6,'cycles',status='figure_read',qualifier='Terminal labelled plot position; prose saturation paragraph does not state a numeric cycle count.')
fact('recommended-ph','stock-ph-window','General adsorption strategy','pH window',unit='pH',minimum=9,maximum=10)
for i,u,s,p,unit in [
 ('calcination-time','matrix-calcine','Air calcination','hold duration','h'),
 ('spin-time','matrix-coat','Spin coating','duration','s'),
 ('impregnation-time','loading-impregnate','Cadmium adsorption','duration','min'),
 ('h2s-dwell','loading-gas','H2S treatment','exposure duration','min'),
 ('vacuum-pressure','loading-evacuate','Pre-H2S evacuation','pressure','Pa'),
 ('loading-temperature','loading-impregnate','Adsorption/H2S synthesis','temperature','degC'),
 ('nh3-total','stock-ph','Complete loading bath','total ammonia amount','mol'),
 ('bath-cd-final','stock-cd-start','Complete loading bath','final cadmium concentration','M')]:fact(i,u,s,p,unit=unit,status='not_reported')

for f in F:
 if f['id'] in [SID+'-fact-filling-cds',SID+'-fact-filling-pore']:f['status']='author_derived'
assert len({u['id'] for u in U})==len(U)
assert all(f['source_unit_id'] in {u['id'] for u in U} for f in F)
import pypdf
docs=[]
for path in (S,L):
 rr=pypdf.PdfReader(str(path));txt='\n'.join(p.extract_text() or '' for p in rr.pages)
 docs.append({'path':str(path),'sha256':sha(path),'page_count':len(rr.pages),'metadata':{str(k):str(v) for k,v in dict(rr.metadata or {}).items()},'content_checks':{'doi_in_extracted_content':DOI in txt,'title_phrase_present':'Mesoporous' in txt and 'Quantum' in txt,'authors_present':all(n in txt for n in ['Besson','Gacoin','Ricolleau','Jacquiod','Boilot'])},'role':'main','identity_method':'Visible full six-page main inspected; byte identity plus extracted metadata/content independently checked.'})
identity={'source_id':SID,'doi':DOI,'title':'3D Quantum Dot Lattice Inside Mesoporous Silica Films','authors':['Sophie Besson','Thierry Gacoin','Christian Ricolleau','Catherine Jacquiod','Jean-Pierre Boilot'],'journal':'Nano Letters','year':2002,'volume':2,'issue':4,'pages':'409–414','received':'2001-11-29','revised':'2002-01-23','published_online':'2002-02-07','primary_article':True,'source_path':str(S),'source_sha256':sha(S),'main_pages':6,'local_candidates':docs,'copies_byte_identical':sha(S)==sha(L),'si_status':'not_located_or_matched_locally_no_declaration_in_supplied_main','si_expected_content':None,'si_search_scope':'Bounded case-insensitive rg filename search in both local collections for nl015685, Besson, 3D/quantum title patterns, lattice/silica and mesoporous/silica found these two main PDFs only. Candidate PDF content, page count and metadata inspected; supplied six-page article has no SI declaration. This is not an exhaustive content search of all differently named documents and does not prove SI absence. Root owns source-bundle refingerprinting; this audit does not mutate the monitor.','external_downloads':False}
pages=[{'pdf_page':n,'printed_page':408+n,'text_file':f'main-{n:02}.txt','text_sha256':sha(B/f'main-{n:02}.txt'),'text_read':True,'render_file':f'main-{n}.png','render_sha256':sha(B/f'main-{n}.png'),'visually_reviewed':True,'scope':'Whole supplied page including both columns, figures, captions, references and source metadata.'} for n in range(1,7)]
conflicts=[
 {'id':'figure4-assignment','source_units':['pl-first-h2s','pl-next-cd','pl-bound-exciton','pl-caption-conflict'],'issue':'Body weak-first/enhanced-next-Cd assignment conflicts with upper/lower caption and plotted features; no silent relabeling.'},
 {'id':'saturated-c-parameter','source_units':['xrd-final-c','tem-mesoparameters','tem-c-conflict'],'issue':'XRD saturated c7.2 nm versus HRTEM approximate c6.8 nm; keep method-scoped values.'},
 {'id':'total-versus-partial-filling','source_units':['tem-residual-pores','filling-occupancy'],'issue':'Qualitative totally filled statement includes residual empty pores; ~85% is a separate derived volume estimate.'},
 {'id':'diameter-comparison','source_units':['ctab-size-final','filling-comparator','note-36'],'issue':'3.6 nm optical saturation size versus 3.5 nm comparator/model pore, retained as source-specific approximate/model comparison.'},
 {'id':'ratio-basis','source_units':['matrix-dilute','stock-ammonia-first','stock-citrate'],'issue':'1:1 dilution basis and equivalent calculation basis incompletely stated; do not invent absolute charges.'},
 {'id':'mesolattice-not-atomic','source_units':['tem-mesosymmetry','tem-power-spectrum','tem-cds-lattice'],'issue':'Hexagonal mesostructure and power spectrum are distinct from atomic blende CdS fringes and SAED.'}]
for c in conflicts:c['source_units']=[SID+'-'+i for i in c['source_units']]
limits=['Main-only source: six pages, four figures, no tables or numbered equations; one inline power-spectrum definition; 43 numbered references/notes.','Copolymer film is an incomplete variant; reference37 is unpublished and unidentified.','Unknown acid, salt hydration/protonation, stock volume, reaction dwell, vacuum level, calcination time and final bath concentration remain explicit.','XRD and Fourier mesostructure parameters cannot become CdS atomic-unit-cell targets. Figure3d is not SAED.','Silicon PL film is separate from Pyrex-supported film; no shared unique physical batch identity supplied.','No raw curve arrays, quantitative SIMS depth profile, lifetime or absolute quantum yield supplied.']
audit={'source_id':SID,'doi':DOI,'status':'complete_supplied_main_text_and_visual_inventory_no_matched_SI','reviewer':'independent_source_audit_agent','reviewed_at':datetime.now(timezone.utc).isoformat(),'source_path':str(S),'source_sha256':sha(S),'coverage':{'main_pages':6,'text_pages_read':6,'visual_pages_reviewed':6,'si_pages_verified':0,'si_status':identity['si_status'],'original_figures':4,'original_tables':0,'numbered_equations':0,'inline_mathematical_definitions':1,'references_and_notes':43,'scope':'Complete supplied main and both matching local main candidates. No cited external articles downloaded/read; no curve digitization or matched SI.'},'pages':pages,'unit_count':len(U),'units':U,'typed_fact_count':len(F),'typed_fact_inventory':'source-facts.json','conflicts':conflicts,'critical_limits':limits,'independent_source_inventory':True,'external_downloads':False,'site_mutated':False,'monitor_mutated':False}
write('source-identity.json',identity);write('independent-page-coverage.json',{'source_id':SID,'pages':pages,'main_text_pages_read':6,'main_visual_pages_reviewed':6,'si_pages_reviewed':0});write('source-facts.json',{'source_id':SID,'source_sha256':sha(S),'scope':'Audit quantities/categorical anchors; not an independent training export. Source unit IDs connect all facts to locators and interpretation limits.','facts':F});write('source-audit.json',audit)
(B/'source-identity.md').write_text('# Besson 2002 source identity\n\n3D Quantum Dot Lattice Inside Mesoporous Silica Films. Nano Letters 2002, 2(4), 409–414. DOI '+DOI+'. Received November 29, 2001; revised January 23, 2002; online February 7, 2002.\n\nBoth local candidates are byte-identical six-page main articles. PDF content, page count and metadata independently checked; visible paper identity takes precedence over the generic metadata title. SHA256: '+sha(S)+'.\n\nNo SI declaration found in the supplied main. No candidate matched the bounded local filename search. This does not establish that SI cannot exist under another filename. No download, Site or monitor mutation.\n',encoding='utf8')
(B/'source-audit.md').write_text('# Besson 2002 independent source inventory\n\nAll six main pages read and visually inspected; '+str(len(U))+' stable units and '+str(len(F))+' scoped typed facts. Four figures, no tables/numbered equations; one inline Fourier-power definition; all 43 references/notes.\n\n'+'\n'.join('- '+l for l in limits)+'\n\n'+'\n\n'.join('**'+u['id']+'** — p. '+str(u['printed_page'])+', '+u['locator']+'. '+u['claim']+' ['+u['disposition']+']' for u in U)+'\n',encoding='utf8')
print(json.dumps({'units':len(U),'facts':len(F),'source_sha256':sha(S),'legacy_identical':sha(S)==sha(L),'source_audit_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'kinds':dict(Counter(u['kind'] for u in U))},ensure_ascii=False,indent=2))
