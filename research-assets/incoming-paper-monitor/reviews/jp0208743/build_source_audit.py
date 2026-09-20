"""Independent supplied-main inventory, after reading and viewing all five pages."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
from pypdf import PdfReader
B=Path(__file__).resolve().parent;SID='dantas2002';DOI='10.1021/jp0208743'
S=Path(r'[local path redacted]')
L=Path(r'[local path redacted]')
U=[];F=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def add(i,p,loc,kind,claim,disposition='retain_source_linked_evidence'):
 U.append({'id':SID+'-'+i,'source_unit_id':SID+'-'+i,'source_role':'main','pdf_page':p,'printed_page':7452+p,'locator':loc,'kind':kind,'claim':claim,'disposition':disposition})
def many(prefix,p,loc,kind,rows,disposition='retain_source_linked_evidence'):
 for i,c in rows:add(prefix+i,p,loc,kind,c,disposition)
def fact(i,uid,scope,prop,value=None,unit=None,minimum=None,maximum=None,approximate=False,status='reported',qualifier=''):
 F.append({'id':SID+'-fact-'+i,'source_unit_id':SID+'-'+uid,'sample_scope':scope,'property':prop,'value':value,'minimum':minimum,'maximum':maximum,'unit':unit,'approximate':approximate,'status':status,'qualifier':qualifier,'eligible_training':False})
many('identity-',1,'Title/byline/footer','source_metadata',[
 ('title','Anti-Stokes Photoluminescence in Nanocrystal Quantum Dots.'),
 ('authors','Noelio Oliveira Dantas, Fanyao Qu, R. S. Silva and Paulo César Morais. Fanyao Qu is corresponding author. Affiliations: Universidade Federal de Uberlândia, Faculdade de Física, Laboratório de Novos Materiais Isolantes e Semicondutores; Universidade de Brasília, Instituto de Física, Núcleo de Física Aplicada.'),
 ('journal','J. Phys. Chem. B 2002, 106, 7453–7457; running headers identify issue 30. DOI 10.1021/jp0208743.'),
 ('dates','Received April 3, 2002; published on web July 9, 2002. No revised date printed.'),
 ('administrative','ACS copyright2002, download watermark July5,2026 and metadata Title No Job Name/creation date are administrative provenance, not synthesis dates. Contact details are bibliographic, not scientific conditions.')],'retain_bibliographic_metadata')
many('abstract-',1,'Abstract','study_summary',[
 ('material','Fusion synthesis of PbS nanocrystal quantum dots embedded in sulfur-doped oxide glass, with absorption, AFM and PL on different samples.'),
 ('size-control','Annealing time is said to control QD size; numerical optical-transition calculations are compared with experimental data.'),
 ('aspl','Study-wide narrative reports strong room-temperature anti-Stokes PL from green2.409 eV to violet2.978 eV in all samples. Detailed optical figures concern SG1–SG4; AFM1/2 are distinct microscopy specimens, so do not assign each the same measured emission range.'),
 ('mechanism','A sequential two-step two-photon process through a surface state is proposed; it is a microscopic interpretation, not a directly resolved intermediate or measured transition rate.')])
many('context-',1,'Introduction','cited_context',[
 ('applications','Semiconductor lasers are motivated by telecommunications, storage, medical diagnostics and therapeutics; these are applications, not devices tested here.'),
 ('qw','Quantum-well confinement is described as increasing electron–hole overlap, oscillator strength and edge density of states, reducing threshold, improving thermal stability and narrowing laser lines, citing references1–3.'),
 ('qd','Prior QD arrays are described as improving gain, threshold, noise, linewidth and thermal dependence, citing4–6. No gain or lasing-threshold measurement is supplied for the present glass.'),
 ('bohr','PbS exciton Bohr radius200 Å is cited to motivate strong confinement; it is not a measured present-particle radius.'),
 ('gap','Prior PbS optical gap tuning from bulk0.41 eV to about5.2 eV in small QDs is cited, not a current sample series.'),
 ('telecom','Prior PbS absorption at1–2 µm, equivalently the source’s rounded0.6–1.3 eV range, motivates telecom applications.'),
 ('aspl-definition','Anti-Stokes emission has photon energy above the excitation source; absorption is contrasted with this optical probe.'),
 ('prior-aspl','Prior bulk, one-dimensional heterostructure and quantum-well ASPL references9–13 are context, not additional materials synthesized here.'),
 ('three-models','Three candidate ASPL mechanisms are introduced: sequential two-step two-photon absorption via impurity states, Auger energy transfer, and LO-phonon absorption through Fröhlich interaction.'),
 ('ts-tpa','Prior TS-TPA uses two sequential absorptions via deep/shallow impurity states; no simultaneous two-photon coefficient is measured here.'),
 ('auger','Prior Auger-like recombination transfers energy from a decaying electron–hole pair to another carrier.'),
 ('phonon','LO-phonon absorption is a candidate thermal process in cited work; no phonon frequency or Raman mode assignment supplied here.'),
 ('prior-dots','InAs/GaAs, InP/GaInP and colloidal InP/CdSe examples support different intermediate-state hypotheses; these cited systems are not current synthesis records.'),
 ('priority','Authors state PbS-QD ASPL had not previously been reported. Retain as historical author claim, not independently verified current priority.'),
 ('study-scope','Current PbS oxide-glass samples are compared using absorption, PL/ASPL, AFM and four-band envelope-function theory; theory must remain distinguishable from observations.')],'retain_cited_or_author_context_not_new_recipe')
many('chemical-',1,'Sample Preparation and Experimental Details','chemical_identity_or_missingness',[
 ('glass-list','Printed sulfur-doped oxide glass mixture is SiO2–Na2CO3–ZnO–Al2O3–PbO2–B2O3. This is a precursor/host formulation list, not the final exact multicomponent glass stoichiometry.'),
 ('silica','SiO2 powder is explicitly the glass former. Crystal phase, particle size, source and amount absent.'),
 ('sodium-carbonate','Na2CO3 is explicitly used to lower the melting point. Hydration state, amount and exact final-glass species are absent; carbonate precursor must not be silently changed to Na2O in the inventory.'),
 ('zinc-oxide','ZnO is explicitly an intermediate oxide. Quantity, grade details and crystal polymorph not supplied.'),
 ('alumina','Al2O3 is in the glass precursor list. Its specific role and proportion are not separately stated; distinguish powder from the printed aluminum crucible.'),
 ('lead-dioxide','PbO2 is printed consistently in abstract, preparation and conclusion. Do not silently substitute PbO or infer lead-oxide decomposition products. Subsequent Pb2+ diffusion wording is a separate source statement, not proof the original precursor was PbO.'),
 ('boron-oxide','B2O3 occurs in the glass precursor list; specific amount, grade and separate role are not stated.'),
 ('sulfur','Sulfur-doped matrix and S2− diffusion are stated, but sulfur precursor identity, allotrope, feed form, dose and addition procedure are not supplied. Do not assume elemental S8, sulfide salt or gas.'),
 ('purity','Powders are described collectively as high purity without supplier, percentage, catalog identifier or impurity assay.'),
 ('missing-formulation','No reagent proportions, molar/mass percentages, absolute batch size or sulfur/lead loading supplied; no stock solvent or solution concentrations are described.'),
 ('crucible','The text literally says aluminum crucible at1400 °C. Retain as unresolved apparatus/material inconsistency; do not silently normalize to alumina or depict a verified stable aluminum vessel at that temperature.'),
 ('product','Product is PbS nanocrystals embedded in multicomponent oxide glass. No freestanding PbS powder, isolated yield, surface ligand or exact final-glass composition established.')])
many('preparation-',1,'Preparation paragraph, continuing on p2','protocol',[
 ('mix','High-purity powder mixture is used; mixing order, grinding method, weighing and sulfur addition details are absent.'),
 ('melt','Mixture is melted at1400 °C for2 h in the literally named aluminum crucible. Heating ramp, furnace, gas atmosphere, pressure, cover and melt mass are unreported.')])
many('preparation-',2,'Preparation continuation','protocol',[
 ('cool','Fast cool the melt to room temperature. Cooling rate, quench medium, casting geometry and numerical room temperature are unspecified.'),
 ('stress-relief','First anneal the glass at350 °C for3 h to release thermal stress. Ramp, cooling between stages and atmosphere absent.'),
 ('growth','Second thermal treatment at600 °C is said to enhance Pb2+ and S2− diffusion and form PbS QDs. Diffusion coefficients, oxidation/reduction balance, pressure and atmosphere are not measured or specified.'),
 ('sets','Two sample sets are explicitly distinct: optical SG1–SG4 and microscopy AFM1/AFM2; no physical batch identifiers or proof of common split parent given.'),
 ('sg1','SG1 corresponds to1 h of the600 °C second anneal.'),('sg2','SG2 corresponds to3 h of the600 °C second anneal.'),('sg3','SG3 corresponds to6 h of the600 °C second anneal.'),('sg4','SG4 corresponds to12 h of the600 °C second anneal.'),
 ('afm1','AFM1 corresponds to5 h of the second anneal, distinct from SG3 at6 h even though sizes are compared.'),('afm2','AFM2 corresponds to30 h of the second anneal, not SG4 at12 h.'),
 ('color','The SG set changes from brown to black depending on annealing duration; no per-sample color coordinates or exact color/time assignments supplied.'),
 ('optical-finish','SG1–SG4 are cut and polished for optical measurements. Thickness, cutting orientation, abrasive, cleaning, mounting and final geometry are absent.'),
 ('afm-prep','AFM1/AFM2 are prepared for AFM images, but cleavage, polishing, etching, deposition and surface preparation are not described.'),
 ('missing','No isolated-QD workup, purification, yield, storage, particle recovery or anneal cooldown schedule is supplied. Six times define variants, not a measured continuous growth law.')])
many('optical-method-',2,'Experimental Details and figure captions','analytical_method',[
 ('spectrometer','Optical measurements use SPEX-750M monochromator with detector printed Joban-Yvon CCD2000×800-3. Preserve manufacturer spelling/model as source; no unverified detector resolution interpretation.'),
 ('excitation','Samples are optically excited with514.5 nm argon-ion laser line. This is optical excitation, not an argon synthesis atmosphere. Absorption illumination/instrument configuration is not independently detailed; do not claim monochromatic514.5 nm absorption spectrum across0.5–3 eV.'),
 ('temperature','Figures1,2 and5 specify room-temperature absorption/PL. No numerical temperature or separate AFM temperature given.'),
 ('missing','No laser spot size, beam profile, exposure time, integration time, slits, polarization, thickness normalization, fluorescence lifetime, absolute PL quantum yield or raw-spectrum array supplied.')])
many('absorption-',2,'Results, Figure1 and Figure2','measurement_or_author_interpretation',[
 ('sg1-peaks','SG1 feature energies S,1,2,3 are1.391,2.486,2.691,2.894 eV, respectively.'),
 ('sg2-peaks','SG2 feature energies S,1,2,3 are1.420,2.200,2.490,2.863 eV, respectively. Text gives SG1 values first and SG2 in parentheses although Figure1 main panel is SG2.'),
 ('features','Both SG1 and SG2 have four well-resolved features S,1,2,3; S is broader than the other three.'),
 ('assignment','S is attributed to surface states;1,2,3 to intrinsic QD transitions. Surface-state attribution is an interpretation, not a measured atomistic defect structure.'),
 ('broadening','Authors explain broad S through scattering from phonons localized in surface defects; no linewidth, phonon spectrum or scattering-rate fit supplied.'),
 ('time-shift','Intrinsic features red-shift with increasing annealing time, interpreted as increasing QD size. No complete numeric SG3/SG4 transition table is printed.'),
 ('surface-shift','S shows no significant shift while intensity and width increase. Literal1.391 versus1.420 eV must remain, rather than forcing identical S energy.'),
 ('merging','Authors argue larger QDs reduce ground-state energy and level spacing so intrinsic and surface features merge, broadening S; this is mechanistic interpretation.'),
 ('dependence','Absorption depends on QD concentration, glass properties and annealing procedure; no isolated control sweep of these factors supplied.')])
many('theory-',2,'Numerical calculation paragraphs','author_model',[
 ('simple','Single-particle Schrödinger calculation assumes an infinite potential well and parabolic energy bands. No full numbered Hamiltonian, boundary condition implementation or code supplied.'),
 ('masses','Effective electron and hole masses each0.25m0; m0 is free electron mass. Model inputs, not measured effective masses of the samples.'),
 ('four-band','More elaborate calculation uses four-band envelope functions and bulk(4×4) k·p Hamiltonian. Band anisotropy is neglected because parameters are described as nearly isotropic; refs19,20 support the model.'),
 ('quantum-labels','k·p eigenvalues are labeled by angular momentum j and parity π; l denotes orbital angular momentum. Figure3 labels are retained as plotted, not reconstructed numerical transitions.'),
 ('agreement','Authors find ground and first excited transition energies of the two models close. No error metric, fit residual or independent parameter table supplied.'),
 ('strong-regime','Text says strong confinement for QD size≤80 Å and rapidly decreasing transitions with increasing QD radius. Size/radius terminology is inconsistent; do not convert these thresholds to certain diameters.'),
 ('large-regime','Text says size>100 Å gives weaker size dependence, level spacings smaller than room-temperature thermal energy and breakdown of phonon bottleneck, with temperature-dependent lasing implications. This is theory, not measured lasing here.'),
 ('sg1-calibration','Calculated first transition2.44 eV for a24 Å dot is compared with SG1 feature1 rounded2.48 eV, whereas the earlier peak table gives2.486 eV. Preserve both levels of source rounding.'),
 ('sg1-size','SG1 average QD size is estimated about24 Å by model–absorption comparison.'),('sg2-size','SG2 average QD size estimated about27 Å by model–absorption comparison.'),('sg3-size','SG3 average QD size estimated about40 Å by model–absorption comparison. SG4 size is not numerically estimated.'),
 ('size-ambiguity','Figure3 horizontal axes and caption explicitly say dot radius; prose estimates are called QD size. Record source-native size with radius/diameter ambiguity, not silently double or halve.'),
 ('no-structure','Neither optical model supplies an experimentally refined atomic structure, lattice constant, phase fraction, CIF or measured wavefunction; no theory curve should be promoted as a new experimental specimen.')],'retain_author_model_not_direct_measurement')
add('theory-prior-agreement',3,'Top left following Figure3','cited_comparison','Authors state size analysis agrees with Thielsch et al., reference8; that cited full text is not independently inspected here.','retain_cited_context')
many('afm-',3,'AFM discussion and Figure4 on p4','analytical_method_and_measurement',[
 ('purpose','AFM is used to support QD formation, average size and size distribution; no instrument model, probe, scan mode, tip radius, scan speed or deconvolution method supplied.'),
 ('afm1-scan','Figure4a upper image is AFM1 after5 h, scanned over5×5 µm². Lower image magnifies its marked region; magnified-region physical dimensions not given.'),
 ('afm1-size','AFM1 is described as relatively narrow in size distribution, average QD size about40 Å.'),
 ('afm1-comparison','AFM1 at5 h is compared with SG3 optical/model size at6 h as consistent. They are different labeled samples and annealing durations; no exact same-batch measurement join.'),
 ('afm2-size','AFM2 after30 h has a wider distribution and average QD size about291 Å, larger than AFM1. No numeric distribution width or particle count supplied.'),
 ('metric-ambiguity','Figure4 plots histograms versus Depth(Å) and labels grain height, whereas discussion calls average QD size. Height is not automatically an isotropic diameter, model radius or independently measured lateral size.'),
 ('image-limit','Grayscale AFM images and histograms are not atomic structure or diffraction. No TEM, XRD, SAED, chemical map, refined phase, morphology reconstruction or verified lattice coordinates supplied.')])
many('aspl-',3,'Luminescence and mechanism discussion','measurement_or_author_interpretation',[
 ('glass-limit','Authors discuss broad size distributions, low loading and poor surface passivation causing trapping/nonradiative loss, making stimulated emission difficult in glass QDs. The paper does not give a gain threshold, linewidth narrowing or coherent emission measurement proving lasing in these specimens.'),
 ('growth-control','Authors state adequate growth/annealing control allows stimulated emission in glass QDs; retain as statement/context rather than turning the PL traces into a lasing dataset.'),
 ('sg-series','Figure5 shows luminescence of SG1–SG4 and prose repeats ASPL from2.409 to2.978 eV in all samples. This broad narrative range is not a separately quantified endpoint pair for each trace.'),
 ('time-trend','Longer annealing broadens ASPL, shifts it to lower energy and enhances a low-energy tail. No per-sample peak table, FWHM or calibrated intensity given.'),
 ('phonon-bottleneck','Authors argue phonon-mediated relaxation is suppressed by confined level spacing and energy/momentum restrictions, requiring weak multiphonon processes in strong confinement.'),
 ('phonon-exclusion','Thermal phonon absorption is argued not dominant for present ASPL. This is theoretical interpretation, not a measured phonon population or temperature sweep.'),
 ('auger-competition','Small QDs may enhance effective carrier density but discrete states restrict final states and energy-conserving Auger recombination; authors weigh competing effects qualitatively.'),
 ('low-excitation','Experiments are described as low optical excitation intensities, with low excited-carrier density; no absolute carrier density given. Figure6 uses kW/cm² rather than W or incident total power.'),
 ('power-law','SG1 Figure6 shows sublinear integrated ASPL I∝I_exc^0.86, solid log–log regression slope about0.86. No slope uncertainty, integration limits or time-dependent carrier model supplied.'),
 ('auger-exclusion','Sublinear rather than superlinear power dependence is used to argue negligible/excluded Auger contribution. Preserve as author conclusion, not uniquely proven mechanism.'),
 ('two-step','Preferred model is sequential two-photon absorption with a surface-defect intermediate. It is not established by measuring two simultaneous photons or a two-photon cross section.'),
 ('first-step','Initial optical excitation creates electron–hole pairs in QD; electrons relax/trap at surface defects near QD–glass interface while holes remain trapped in the valence-band state.'),
 ('second-step','A second photon excites trapped electron from surface state to QD conduction band, followed by radiative recombination across effective gap.'),
 ('momentum','Strong surface localization is argued to broaden momentum uncertainty and relax momentum-conservation restrictions in the second absorption; no measured localization length supplied.')])
many('aspl-',4,'Mechanism continuation below Figure4','author_model',[
 ('photon-source','Second-step photon can come directly from excitation source or from photon recycling, citing21. Recycling fraction and photon path are not measured.'),
 ('sublinear-model','Small density of surface-defect states and first-step capture faster than second-step photoionization are proposed to explain exponent0.86; rates and state density are not quantified.'),
 ('support','Authors cite sublinear excitation dependence and slightly sample-dependent ASPL transition energies as supporting observations for the model; these do not resolve a unique defect identity.')],'retain_author_interpretation')
many('raman-',5,'Figure7 and discussion across columns','measurement_or_author_interpretation',[
 ('sg1-main','SG1 principal ASPL feature is about2.978 eV, referring to Figure5.'),
 ('sg1-secondary','A second narrow upconverted emission line in SG1 is around2.476 eV.'),
 ('alignment','Figure7 compares SG1 absorption symbols and PL solid curve on separate vertical scales; authors say the2.476 eV emission aligns with first intrinsic absorption feature. Earlier SG1 peak1 is2.486 eV, so retain near alignment/rounding rather than exact equality.'),
 ('assignment','Secondary emission close to excitation energy is tentatively assigned to a resonant Raman process. No Raman shift, phonon mode, polarization selection rule or dedicated Raman spectrum is measured; do not invent a vibrational assignment.')])
many('figure-',2,'Figures1–2 including captions/axes','original_figure',[
 ('1','Main plot SG2 absorption at3 h with inset SG1 at1 h, both room temperature. Arrows label S,1,2,3. Main energy axis0.5–3.0 eV; inset labeled0.5–3.5 eV, conflicting with prose description of both spectra as0.5–3.0 eV. Absorption arbitrary units: main vertical ticks0–0.15, inset0–2.5. Original curves and source-display discrepancy preserved without dense digitization.'),
 ('2','Room-temperature absorption SG1–SG4 (600 °C,1/3/6/12 h). Energy axis shows labels1–3.5 eV, absorption0–0.30 a.u.; traces labeled1,3,6,12 hours. Dash-dotted E^(1/2) curve is identified as bulk PbS absorption, not a separate synthesized bulk control with given recipe.')])
many('figure3-',3,'Figure3 panels, labels and caption','model_figure',[
 ('panels','Figure3a effective-mass/parabolic model and3b four-band(4×4) k·p calculation. Both x axes explicitly Dot radius(Å); panel a ticks10–90 Å and energies−8 to6 eV; b ticks10–50 Å and energies−3 to3 eV. These are plotted theory domains, not measured particle distributions.'),
 ('states-a','Panel a labels electron1Se,1Pe,2Se,2Pe and hole1Sh,1Ph,2Sh,2Ph branches; legend solid E2,1, dashed E2,0, dotted E1,1, dash-dot E1,0. Do not treat positive/negative branches as all independent optical transition measurements.'),
 ('states-b','Panel b labels angular momentum/parity states including j=1/2,3/2,5/2 and π=±1. Caption defines l as orbital angular momentum; exact original state labels remain in crop.'),
 ('spaces','Figure3b legend: filled markers Space I: j=l+1/2, π=(-1)^(l+1); open markers Space II: j=(l+1)-1/2, π=(-1)^l. Preserve as printed; no extra Hamiltonian matrix or derived selection-rule table supplied.')],'retain_theory_plot_not_experimental_training_label')
many('figure4-',4,'Figure4 AFM panels/histograms/caption','original_figure',[
 ('panels','Figure4a includes AFM1 overview5×5 µm², marked square region and its magnification, correlation plot and height/depth histogram. Figure4b has AFM2 magnification with correlation plot and histogram. No lateral scale bar on magnifications, no contour-height calibration/color bar supplied.'),
 ('afm1-labels','AFM1 histogram source labels Substrate depth:1.57 Å and Grain height:40.19 Å. Histogram ordinate Hist.% with labels0–0.75; abscissa Depth(Å) labeled0 and90. Upper Correlation plot labels0,0.50,1.00, with no independently printed horizontal scale.'),
 ('afm2-labels','AFM2 histogram labels Substrate depth:0 Å and Grain height:291.24 Å. Hist.% ordinate0–1.00 and Depth(Å) axis0–670. Correlation plot has ordinate0–1.00; no numeric fit width supplied.'),
 ('precision','Exact printed grain-height annotations40.19/291.24 Å are separate from rounded prose QD-size≈40/≈291 Å. Histograms are not transcribed as invented raw bins or converted to model radii.')])
many('figure-',5,'Figures5–7 including captions and insets','original_figure',[
 ('5','Room-temperature SG1–SG4 PL traces labeled1/3/6/12 hours at600 °C. Energy ticks2.90,2.95,3.00 eV; visible window narrower than broad2.409–2.978 eV narrative. Intensity arbitrary units0–8, no statement of absolute calibration or separate offset corrections. No full green-to-violet spectral array reconstructed.'),
 ('6','SG1 at600 °C/1 h, excitation514.5 nm. Log–log integrated ASPL(a.u.) versus Excitation intensity(kW/cm²), labeled intensity decades0.1 and1 on both axes; about0.86 regression. Dots are measurements and solid line fit, inset a proposed energy-level mechanism, not measured band structure or current atomistic geometry.'),
 ('6-inset','Inset labels Surface state, hν0 and hν and depicts sequential excitation/relaxation with dot/interface energy levels. No numerical surface-state depth, lifetime, state count or exact band offset given.'),
 ('7','SG1 absorption symbols use left0–1 a.u. scale and PL line right0–7 a.u.; energy2.3–2.9 eV. Arrows identify distinct axes. The narrow secondary line around2.476 eV is not the higher-energy main2.978 eV ASPL feature. No raw-data table supplied.')])
many('conclusion-',5,'Conclusions and acknowledgment','study_conclusion',[
 ('six-samples','Six distinct annealed sulfur-doped glass samples are reported; annealing promotes PbS growth and size increase. Optical and AFM comparisons support this at separate sample scopes.'),
 ('model-agreement','Authors claim agreement between theory, absorption and AFM. This does not remove size/radius/height ambiguity or join5 h AFM1 to6 h SG3 as one specimen.'),
 ('aspl','Authors conclude room-temperature anti-Stokes emission and favor surface-state TS-TPA; they tentatively assign nearby secondary upconversion to resonant Raman. Mechanistic uncertainty remains.'),
 ('funding','FAPEMIG and CNPq supported the work. Funding is administrative provenance, not a synthesis parameter.')])
add('source-missing',5,'Complete supplied main','missingness','No SI declaration is visible in the five main pages, and no local matching SI found by the bounded filename/content-identity search. No formulation proportions, sulfur identity, atmosphere, refined structure, raw spectra, acquisition error bars, kinetics or complete numerical theory code supplied.','retain_explicit_missingness')
refs=[
 'Qu, Fanyao; Cardoso, A. J. C.; Morais, P. C. Phys. Rev. B 1999, 60, 4501. Quantum-well optical/laser context.',
 'Qu, Fanyao; Dantas, N. O.; Morais, P. C. Phys. E 2001, 9, 709. Quantum-well context.',
 'Qu, Fanyao; Dantas, N. O.; Morais, P. C. Europhys. Lett. 2001, 53, 790. Quantum-well context.',
 'Qu, Fanyao; Morais, P. C. J. Phys. Chem. 2000, 104, 5232. QD optical context; journal abbreviation as printed.',
 'Klimov, V. I.; Mikhailovsky, A. A.; McBranch, D. W.; Leatherdale, C. A.; Bawendi, M. C. Science 2000, 287, 101. Carrier relaxation/phonon context; author initials retained as printed.',
 'Klimov, V. I.; Mikhailovsky, A. A.; Xu, Su; Malko, A.; Hollingsworth, J. A.; Leatherdale, C. A.; Eisler, H.-J.; Bawendi, M. C. Science 2000, 290, 314. QD gain and Auger/context claims.',
 'Tsuyoshi, O.; Andrey, A. L.; Tomoyasu, O.; Isamu, A.; Yasuaki, M. J. Lumin. 2000, 87–89, 491. PbS confinement/telecom context; name order as printed.',
 'Thielsch, R.; Böhme, T.; Reiche, R.; Schläfer, D.; Bauer, H. D.; Böttcher, H. Nanostruct. Mater. 1998, 10, 13. Prior PbS size/gap comparison.',
 'Iino, T.; Weber, J. Mater. Sci. Forum 1995, 196–201, 993. Bulk ASPL context.',
 'Su, Z. P.; Teo, K. L.; Yu, P. Y.; Uchida, K. Solid State Commun. 1996, 99, 933. Sequential-absorption/heterostructure context.',
 'Seidel, W.; Tikov, A.; André, J. K.; Voisin, P.; Voos, M. Phys. Rev. Lett. 1994, 73, 2356. Heterostructure ASPL context; names as printed.',
 'Vagos, P.; Boucaud, P.; Julien, F. H.; Lourtioz, J. M. Phys. Rev. Lett. 1993, 70, 1018. Quantum-well ASPL context.',
 'Hellmann, R.; Euteneuer, A.; Hense, S. G.; Feldmann, J.; Thomas, P.; Göbel, E. O. Phys. Rev. B 1995, 51, 18053. Quantum-well ASPL context.',
 'Junnarkar, M. R.; Yamaguchi, E. Solid-State Electron. 1996, 40, 665. Two-step capture/photoionization model context.',
 'Cheong, H. M.; Fkuegel, B.; Hanna, M. C.; Mascarenhas, A. Phys. Rev. B 1998, 58, R4254. Auger mechanism context; Fkuegel as printed.',
 'Paskov, P. P.; Holtz, P. O.; Monemar, B.; Garcia, J. M.; Schoenfeld, W. V.; Petroff, P. M. Appl. Phys. Lett. 2000, 77, 812. InAs/GaAs QD ASPL context.',
 'Ignatiev, I. V.; Kozin, I. E.; Ren, H. W.; Sugou, S.; Masumoto, Y. Phys. Rev. B 1999, 60, R14001. InP/GaInP context.',
 'Poles, E.; Selmarten, D. C.; Micic, O. I.; Nozik, A. J. Appl. Phys. Lett. 1999, 75, 971. Colloidal InP/CdSe surface-state context.',
 'Tudury, G. E.; Marquezini, M. V.; Ferreira, L. G.; Barbosa, L. C.; César, C. L. Phys. Rev. B 2000, 62, 7357. Four-band PbS model dependency.',
 'Andreev, A. D.; Lipovskii, A. A. Phys. Rev. B 1999, 59, 15402. Envelope-function/band-isotropy context.',
 'Sales, F. V.; Da Silva, S. W.; Monte, A. F. G.; Soler, M. A. G.; Cruz, J. M. R.; Da Silva, M. J.; Quivy, A. A.; Leite, J. R.; Morais, P. C. Phys. Status Solidi A 2001, 187, 45. Photon recycling context.'
]
for n,t in enumerate(refs,1):add(f'reference-{n:02}',5,f'Reference {n}','bibliography',t,'retain_reference_not_independently_read')
for i,uid,scope,prop,v,u,ap,st in [
 ('melt-t','preparation-melt','Common glass preparation','melt temperature',1400,'°C',False,'reported'),('melt-time','preparation-melt','Common glass preparation','melt duration',2,'h',False,'reported'),
 ('stress-t','preparation-stress-relief','Common glass preparation','stress-relief temperature',350,'°C',False,'reported'),('stress-time','preparation-stress-relief','Common glass preparation','stress-relief duration',3,'h',False,'reported'),('growth-t','preparation-growth','All six annealed variants','growth anneal temperature',600,'°C',False,'reported'),
 ('laser','optical-method-excitation','SG optical excitation','argon-ion wavelength',514.5,'nm',False,'reported'),('electron-mass','theory-masses','Effective-mass model','electron mass/m0',.25,'ratio',False,'model_input'),('hole-mass','theory-masses','Effective-mass model','hole mass/m0',.25,'ratio',False,'model_input'),
 ('model-energy','theory-sg1-calibration','24 Å model dot','first transition energy',2.44,'eV',False,'model_output'),('rounded-sg1-transition','theory-sg1-calibration','SG1 comparison','rounded intrinsic feature1',2.48,'eV',False,'reported'),
 ('sg1-size','theory-sg1-size','SG1 at1 h','source-native size; radius/diameter unresolved',24,'Å',True,'author_derived'),('sg2-size','theory-sg2-size','SG2 at3 h','source-native size; radius/diameter unresolved',27,'Å',True,'author_derived'),('sg3-size','theory-sg3-size','SG3 at6 h','source-native size; radius/diameter unresolved',40,'Å',True,'author_derived'),
 ('afm1-size','afm-afm1-size','AFM1 at5 h','rounded source-native QD size',40,'Å',True,'reported'),('afm2-size','afm-afm2-size','AFM2 at30 h','rounded source-native QD size',291,'Å',True,'reported'),
 ('afm1-height','figure4-afm1-labels','AFM1 Figure4','grain height',40.19,'Å',False,'figure_read'),('afm1-substrate','figure4-afm1-labels','AFM1 Figure4','substrate depth annotation',1.57,'Å',False,'figure_read'),('afm2-height','figure4-afm2-labels','AFM2 Figure4','grain height',291.24,'Å',False,'figure_read'),('afm2-substrate','figure4-afm2-labels','AFM2 Figure4','substrate depth annotation',0,'Å',False,'figure_read'),
 ('afm1-scan-x','afm-afm1-scan','AFM1 overview','scan width',5,'µm',False,'reported'),('afm1-scan-y','afm-afm1-scan','AFM1 overview','scan height',5,'µm',False,'reported'),
 ('power-exponent','aspl-power-law','SG1 Figure6 only','integrated ASPL excitation power-law exponent',.86,'dimensionless',True,'author_derived'),('sg1-aspl','raman-sg1-main','SG1','main ASPL feature energy',2.978,'eV',True,'reported'),('sg1-secondary','raman-sg1-secondary','SG1','secondary narrow upconversion energy',2.476,'eV',True,'reported'),
 ('bohr','context-bohr','Cited PbS context','exciton Bohr radius',200,'Å',False,'cited_context'),('bulk-gap','context-gap','Cited bulk PbS','optical gap',.41,'eV',False,'cited_context'),('small-gap','context-gap','Cited small PbS QDs','optical gap',5.2,'eV',True,'cited_context')]:fact(i,uid,scope,prop,v,u,approximate=ap,status=st)
for s,t in [('sg1',1),('sg2',3),('sg3',6),('sg4',12),('afm1',5),('afm2',30)]:fact(s+'-anneal','preparation-'+s,s.upper(),'growth anneal duration',t,'h')
for s,vals in [('sg1',[1.391,2.486,2.691,2.894]),('sg2',[1.420,2.200,2.490,2.863])]:
 for label,v in zip(['S','1','2','3'],vals):fact(s+'-feature-'+label.lower(),'absorption-'+s+'-peaks',s.upper(),'absorption feature '+label,v,'eV')
fact('aspl-narrative-range','abstract-aspl','Study-wide narrative; not each physical sample','reported ASPL span',unit='eV',minimum=2.409,maximum=2.978,qualifier='Figure5 covers a narrower plotted window; AFM samples have no individual PL trace.')
fact('strong-regime','theory-strong-regime','Model discussion','source size upper strong-confinement boundary',unit='Å',maximum=80,status='author_model',qualifier='≤80 Å; prose size versus plotted radius ambiguity.')
fact('weak-regime','theory-large-regime','Model discussion','source size threshold',unit='Å',minimum=100,status='author_model',qualifier='Strictly >100 Å, source size/radius terminology unresolved.')
fact('telecom-wavelength','context-telecom','Cited context','absorption wavelength range',unit='µm',minimum=1,maximum=2,status='cited_context')
fact('telecom-energy','context-telecom','Cited context','rounded absorption energy range',unit='eV',minimum=.6,maximum=1.3,status='cited_context')
fact('abs-fig1-range','figure-1','Figure1 SG2 main and prose description of both spectra','main displayed/prose energy extent',unit='eV',minimum=.5,maximum=3,status='reported',qualifier='The SG1 inset actually labels through3.5 eV; retain the source discrepancy.')
fact('abs-fig1-inset-range','figure-1','SG1 inset Figure1','displayed energy-axis labels',unit='eV',minimum=.5,maximum=3.5,status='figure_read',qualifier='Source prose instead describes both spectra as0.5–3.0 eV.')
fact('afm1-hist-range','figure4-afm1-labels','AFM1 height histogram','displayed depth labels',unit='Å',minimum=0,maximum=90,status='figure_read')
fact('afm2-hist-range','figure4-afm2-labels','AFM2 height histogram','displayed depth labels',unit='Å',minimum=0,maximum=670,status='figure_read')
fact('power-axis-unit','figure-6','SG1 power dependence','source x-axis unit','kW/cm²',status='figure_read',qualifier='Irradiance rather than total laser power; no unreported W/cm² or spot-size assumption.')
fact('room-temperature','optical-method-temperature','Absorption/PL','measurement temperature','Room temperature',qualifier='No numerical temperature supplied; not synthesis atmosphere/temperature.')
fact('crucible-literal','chemical-crucible','Common melt','reported crucible material','aluminum',qualifier='Source-internal apparatus concern at1400 °C; alumina correction is not established.')
fact('lead-precursor','chemical-lead-dioxide','Glass charge','printed lead precursor','PbO2',qualifier='Later Pb2+ diffusion statement does not change input identity to PbO.')
ids=[x['id'] for x in U];assert len(ids)==len(set(ids));assert all(f['source_unit_id'] in ids for f in F)
identity_candidates=[]
for path in (S,L):
 pdf=PdfReader(str(path));text='\n'.join(p.extract_text() or '' for p in pdf.pages);identity_candidates.append({'path':str(path),'sha256':sha(path),'page_count':len(pdf.pages),'metadata':dict(pdf.metadata or {}),'content_checks':{'doi':DOI in text,'title':'Anti-Stokes Photoluminescence' in text,'authors':'Dantas' in text and 'Morais' in text,'journal':'7453' in text and '7457' in text},'role':'main','identical_alias':path==L})
identity={'status':'passed_local_main_identity_no_matched_SI','source_id':SID,'doi':DOI,'title':'Anti-Stokes Photoluminescence in Nanocrystal Quantum Dots','source_sha256':sha(S),'page_count':5,'authors':['Noelio Oliveira Dantas','Fanyao Qu','R. S. Silva','Paulo César Morais'],'journal':'Journal of Physical Chemistry B','year':2002,'volume':106,'issue':30,'pages':'7453–7457','received':'2002-04-03','published_online':'2002-07-09','candidates':identity_candidates,'supporting_information':{'status':'not_located_or_matched','matched_count':0,'declaration_in_supplied_main':False,'search_scope':'Both local collections searched with rg --files filtered by jp020874, Dantas and anti.?stokes.*nanocrystal. Both resulting PDFs independently checked by hash, page count, metadata and DOI/title/byline content.','search_limit':'Bounded filename and candidate-content review; not exhaustive content search of every unrelated PDF and not proof that no SI exists.'},'independent_visual_identity':True}
pages=[{'role':'main','pdf_page':p,'printed_page':7452+p,'text_path':str(B/f'main-{p:02}.txt'),'text_sha256':sha(B/f'main-{p:02}.txt'),'image_path':str(B/f'main-{p}.png'),'image_sha256':sha(B/f'main-{p}.png'),'text_read':True,'actually_visually_inspected':True,'unit_count':sum(u['pdf_page']==p for u in U)} for p in range(1,6)]
report={'status':'complete_supplied_main_text_and_visual_inventory_no_matched_SI','source_id':SID,'doi':DOI,'source_sha256':sha(S),'audited_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent full five-page text and visual review, including every source paragraph, seven figures, captions, inset diagrams, unnumbered mathematical relations and all21references.','units':U,'unit_count':len(U),'unit_kind_counts':dict(Counter(u['kind'] for u in U)),'typed_anchor_count':len(F),'page_coverage':pages,'figure_count':7,'table_count':0,'numbered_equation_count':0,'references_and_notes_count':21,'source_conflicts_and_limits':['Literal aluminum crucible at1400 °C is unresolved; no silent alumina substitution.','PbO2 precursor identity and later Pb2+ diffusion statement retained separately without reaction/redox reconstruction.','Prose size versus model radius versus AFM grain height/depth must not be collapsed into one particle diameter.','SG3(6 h) and AFM1(5 h) are compared, not a verified same specimen; no optical measurements assigned to AFM1/2.','Broad2.409–2.978 eV narrative range exceeds Figure5 visible window; do not fabricate full-range spectrum or per-sample endpoints.','SG1 absorption2.486 eV, rounded comparison2.48 eV and secondary emission2.476 eV remain distinct; resonant Raman is tentative.','Theory/model curves, phenomenological exponent and microscope histograms remain separate evidence classes.','No local matched SI or quantitative glass formulation/sulfur identity; full reproducible synthesis cannot be reconstructed.'],'site_mutated':False,'downloaded_sources':False}
write('source-audit.json',report);write('source-facts.json',{'source_id':SID,'source_sha256':sha(S),'scope':'Source-native quantitative/categorical audit anchors; not independent training examples.','facts':F});write('source-identity.json',identity);write('independent-page-coverage.json',{'source_id':SID,'source_sha256':sha(S),'pages':pages,'source_detail_images_actually_viewed':['source-detail-figure3.png','source-detail-figure4-labels.png']})
(B/'source-audit.md').write_text('# Dantas 2002 independent source audit\n\nAll five supplied main pages were fully read and visually inspected. '+str(len(U))+' granular source units and '+str(len(F))+' typed anchors cover seven figures, unnumbered theory/power-law relations and all 21 references.\n\n'+'\n'.join('- '+x for x in report['source_conflicts_and_limits'])+'\n\nSix600 °C anneals are distinct: SG1/2/3/4 at1/3/6/12 h; AFM1/2 at5/30 h. Shared fusion and stress-relief steps remain source-scoped. No Site or monitor edits/downloads.\n',encoding='utf8')
(B/'source-identity.md').write_text('# Dantas 2002 source identity\n\nVerified DOI '+DOI+', title, byline, journal, 2002 dates and five-page extent against both identical local main copies. SHA256 `'+sha(S)+'`.\n\nNo SI declaration was found in the five pages, and the bounded local filename/content search found no matching supplement. This does not establish that SI cannot exist. PDF metadata/download timestamps are not scientific publication dates.\n',encoding='utf8')
print(json.dumps({'source_units':len(U),'typed_anchors':len(F),'source_audit_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json')},ensure_ascii=False))
