from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json,hashlib
B=Path(__file__).resolve().parent
S=Path(r'[local path redacted]')
L=Path(r'[local path redacted]')
SID='braun2001';DOI='10.1021/jp010002l'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,d):(B/name).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
U=[]
def add(id,page,locator,kind,claim,disposition='retain_source_linked_evidence'):
 U.append({'id':SID+'-'+id,'source_unit_id':SID+'-'+id,'source_role':'main','pdf_page':page,'printed_page':5547+page,'locator':locator,'kind':kind,'claim':claim,'disposition':disposition})
for id,claim in [
 ('title','Variation of the Thickness and Number of Wells in the CdS/HgS/CdS Quantum Dot Quantum Well System.'),
 ('authors','Markus Braun, Clemens Burda, Mostafa A. El-Sayed; School of Chemistry and Biochemistry, Georgia Institute of Technology, Atlanta, GA30332-0400.'),
 ('journal','Journal of Physical Chemistry A2001,105(23),5548–5551; DOI10.1021/jp010002l. JPC A, not JPC B.'),
 ('dates','Received January3,2001; final form May1,2001; published on web May22,2001.'),
 ('administrative','Edward W. Schlag Festschrift special issue; corresponding author El-Sayed; ACS copyright2001. Download watermark July1,2026 at07:51:49UTC via University of Chicago is not an experimental/publication date.')]:add('identity-'+id,1,'Title/byline/dates/footer','source_metadata',claim,'retain_bibliographic_metadata')
for id,claim in [
 ('architecture','The article claims the first chemically prepared multilayer quantum-well structure in a semiconductor dot: two HgS wells separated by a CdS double layer with CdS core/cap. This is the authors’ historical claim, not independently established priority.'),
 ('evidence','Absorption/emission and relaxation dynamics compare single-monolayer well, contiguous double-layer well and two separated monolayer wells. Structural assignment is based on synthesis sequence and optical comparison, not current atomically resolved imaging.'),
 ('outlook','Barrier/well thickness variation is proposed to investigate carrier interaction; the current separated-well specimen uses a two-CdS-monolayer barrier, not a measured broad barrier sweep.')]:add('abstract-'+id,1,'Abstract','study_summary',claim)
for id,claim in [
 ('prior-work','References1–7 discuss physically/chemically prepared wells;8–10 solid-state devices;1–2 earlier CdS-dot QDQW;11–16 experimental and17–19 theoretical literature.'),
 ('tetrahedral','Pioneering prior work describes tetrahedral CdS cores with111 facets. Figure1 caption repeats actual small-crystallite tetrahedral shape. This is cited structural context, not new TEM, phase refinement or measured coordinates for these three samples.'),
 ('exchange','Adding Hg²⁺ exchanges the outermost CdS layer for less soluble HgS; subsequently CdS caps it. Layer sequence and core/well/clad thickness can be varied.'),
 ('motivation','Wet-chemical nanoparticle units are proposed as a lower-cost alternative to clean-room/UHV physical multilayers, with handling/deposition from solution at ambient conditions. This is a motivation, not a fabricated device or cost measurement.'),
 ('prior-theory','Chang/Xia reference19 treated a two-layer QDQW theoretically; authors say a multiple-layer chemical realization remained lacking. Earlier theory is distinct from this source’s experimental measurements.')]:add('context-'+id,1,'Introduction','cited_context',claim,'retain_cited_context_not_current_recipe')

# Source-named materials deliberately do not imply counterions or stock recipes.
for id,claim in [
 ('cadmium','Aqueous Cd²⁺ ions: source does not identify salt/counterion, purity, stock preparation or pH-adjusting reagent. The A charge is100mL at2×10^-4M.'),
 ('mercury','Aqueous Hg²⁺:12mL at10^-3M, described atpH7.0 in B. Salt/counterion and stock preparation are unreported.'),
 ('h2s-gas','StepA injects0.6mL H2S gas. Gas purity, temperature, pressure and flow/delivery rate are unreported; no moles should be inferred from volume alone.'),
 ('h2s-water','StepC uses H2S/water solution; its volume, concentration, preparation and sulfide speciation are not given. This is distinct from the0.6mL gas charge in A.'),
 ('hexametaphosphate','Hexametaphosphate stabilizer is named; counterion, exact chain/ring form, amount/concentration, purity and surface coverage are not reported. Do not silently assign sodium hexametaphosphate.'),
 ('argon','Argon is the A atmosphere and the stated post-A/post-C purging gas. Pressure and flow are unreported.'),
 ('water','Aqueous reaction medium and water optical reference are stated. No water purity, deoxygenation protocol or ionic-strength recipe is specified.'),
 ('materials-scope','CdS and HgS identify layers in a composite particle, not an overall fixed formula. Sapphire is a white-light-generation optical component, not a nanocrystal precursor.')]:add('chemical-'+id,1 if id in ['cadmium','h2s-gas','hexametaphosphate','water','materials-scope'] else 2,'Experimental and sample preparation','chemical_identity_or_missingness',claim)

for id,page,claim in [
 ('scope',1,'Preparation is summarized as A CdS core growth, B surface CdS-to-HgS exchange, C one-CdS-monolayer growth. Full detail is cited to references2 and13; reference13 is listed only as submitted.'),
 ('vessel',1,'StepA uses a250mL flask containing100mL of2×10^-4M aqueous Cd²⁺ with hexametaphosphate, stirred under argon. Flask capacity is not reaction volume.'),
 ('initial-ph',1,'Initial stepA pH7.9. The source does not give the reagent or operation used to set pH.'),
 ('gas-injection',1,'Inject0.6mL H2S gas into the stirred A mixture under argon; injection duration/rate and gasT/P are not specified.'),
 ('nucleation',1,'Authors explain high pH as promoting fast H2S ionization and nucleation of many small CdS crystallites. The printed sulfur-ion notation is S− alongside H+; retain source wording without treating it as a fully balanced speciation model.'),
 ('acidification',1,'Source says CdS precipitation promotes H2S dissociation and H+ release, moving pH into an acidic range after about30s. This is an acidification timescale, not total growth time or an instructed30s quench.'),
 ('growth',2,'Slow CdS growth is said to continue until3.5nm, with finalpH4.6. Time to growth completion and size-measurement protocol for this statement are not supplied.'),
 ('purge',2,'After A, purge colloid with argon for20min to remove excess H2S. Flow and gas pressure are unknown.'),
 ('size-conflict',2,'A prose growth endpoint3.5nm conflicts with later all-system/Figure1 CdS core3.2nm. Preserve both locators; do not average, silently replace or invent separate measured batches.')]:add('step-a-'+id,page,'Sample Preparation, stepA'+(' continuation' if page==2 else ''),'protocol_or_author_interpretation',claim)
for id,claim in [
 ('feed','B adds12mL aqueous10^-3M Hg²⁺ solution, described atpH7.0, to the colloidal particles. The sentence attaches pH to the aqueous feed; no separately quantified colloid-adjustment operation is given.'),
 ('exchange','The outermost CdS monolayer exchanges Cd²⁺ for Hg²⁺ and becomes one HgS monolayer. This is cation exchange of an existing sulfide layer, not deposition of a new sulfide layer from an unreported sulfur dose.'),
 ('thermodynamics','The paper says HgS solubility product is26 orders of magnitude smaller than CdS, motivating exchange. This is a source thermodynamic rationale; no measured Ksp value or temperature series supplied.'),
 ('released-cadmium','Exchanged Cd²⁺ remains in the same solution; authors state it suffices for one CdS monolayer when sulfide is supplied. Do not remove the supernatant or reset the dissolved Cd inventory.'),
 ('unknowns','B addition time/rate, equilibration interval, temperature specific to B and post-B workup/purge are not supplied. No wash or solid isolation occurs in the reported summarized step.'),
 ('repeat','B is invoked twice in II and III. Repeated invocations are sequential layer transformations in the same described route, not independent syntheses.12mL/10^-3M is the common B description, with no separately optimized later-B amount.')]:add('step-b-'+id,2,'Sample Preparation, stepB','protocol_or_author_interpretation',claim)
for id,claim in [
 ('cadmium-rule','C requires enough Cd²⁺ for one monolayer. If immediately preceded by B, released Cd²⁺ is stated sufficient. Otherwise inject the appropriate amount of Cd²⁺ through a septum; exact amount, concentration and salt are not specified.'),
 ('growth','Slowly inject H2S/water solution dropwise over25min atpH7.0 to grow one CdS monolayer. This is sulfide-driven growth, distinct from B exchange.'),
 ('purge','After each C, purge with argon for at least20min to remove excess H2S. This is a lower bound, not an exact20min duration or a20min upper limit.'),
 ('missing','C aqueous-H2S concentration/volume and supplemental-Cd dose are absent. No constant drop size, pump rate or sulfide-to-Cd ratio can be derived.'),
 ('medium','Repeated B/C steps act on the colloidal dispersion without a reported intervening wash, centrifugation, drying or powder isolation.')]:add('step-c-'+id,2,'Sample Preparation, stepC','protocol',claim)

for system,sequence,architecture in [
 ('i','A–B–C','CdS/(HgS)1/(CdS)1: one HgS monolayer well plus one CdS cap.'),
 ('ii','A–B–C–B–C','CdS/(HgS)2/(CdS)1: contiguous double-layer HgS well plus one CdS cap.'),
 ('iii','A–B–C–C–C–B–C','CdS/(HgS)1/(CdS)2/(HgS)1/(CdS)1: two separated monolayer HgS wells, two CdS barrier layers, final one-layer CdS cap.')]:
 add('route-'+system+'-sequence',2,'Sample Preparation, System'+system.upper(),'recipe_sequence',sequence+'. '+architecture)
 add('route-'+system+'-scope',2,'Sample Preparation, System'+system.upper(),'sample_lineage', 'System'+system.upper()+' is a route/cohort label. Intermediate stages are sequential states. The source does not report unique batch identifiers, replicates or independent optimization runs.')
add('route-i-transforms',2,'SystemI','sample_lineage','A grows the core; B turns its outermost CdS layer into HgS; C restores a CdS outer cap using Cd²⁺ released by B.')
add('route-ii-transforms',2,'SystemII','sample_lineage','The initial A–B–C gives systemI. The second B replaces that CdS cap with HgS adjoining the first HgS layer; the final C caps the now-double-thickness well. Do not depict two separated wells in II.')
add('route-iii-transforms',2,'SystemIII','sample_lineage','Starting from A–B–C, two additional C invocations make three CdS layers outside the first HgS well. B exchanges only the outermost third CdS layer to HgS, leaving two CdS barrier layers. Final C caps the second well.')
add('route-iii-topups',2,'StepC rule and SystemIII sequence','source_logical_consequence','The two consecutive additional C steps in III require unspecified supplemental Cd²⁺ because they do not immediately follow B. C immediately after B uses released Cd²⁺. This follows the stated rule and sequence; no numeric top-up is fabricated.')
add('route-temperature',1,'Experimental Section, final optical-method sentence','scope_limit','The source says all experiments were performed with samples at room temperature. This statement immediately follows optical methods; retain scope explicitly rather than importing a numeric synthesis temperature.')
add('route-final-state',2,'Complete supplied sample preparation','missingness','Final products remain aqueous colloids as used in optical experiments. No isolated mass, reaction yield, powder workup, storage condition, final dispersion concentration, stabilizer removal or long-term stability test is specified.')

for id,claim in [
 ('core','Figure1 and dimensions paragraph assign a3.2nm CdS core to all three systems, conflicting with3.5nm in A growth prose.'),
 ('cap','All systems are described with one0.4nm CdS capping layer.'),
 ('i','I has one0.4nm HgS quantum well between CdS core and cap.'),
 ('ii','II has one0.8nm HgS well, described as two contiguous monolayers.'),
 ('iii','III has two0.4nm HgS wells separated by a0.8nm CdS barrier. These are stated nominal architecture dimensions, not source-resolved radial composition profiles.'),
 ('coordinates','No atomic coordinates, unit cell, space group, CIF, phase-refined XRD, SAED or current TEM image is supplied. Tetrahedral111-facet context is cited earlier work; do not promote schematic circles into measured spherical particles.')]:add('structure-'+id,2,'System dimensions paragraph/Figure1','reported_architecture_or_limit',claim)

for id,claim in [
 ('pump','Transient absorption excites at400nm with100fs fwhm pulses of100µJ. Pulse energy is not average power, and pump repetition rate/spot area are not stated here.'),
 ('probe','White-light continuum probe spans450–1050nm; generated by focusing a small portion of800nm fundamental output into a sapphire plate.'),
 ('delay','Pump and probe are overlapped on the colloid; differential absorption is measured versus delay. Optical delay-line resolution3µm corresponds to21fs as reported; do not relabel this as100fs pulse duration or temporal decay lifetime.'),
 ('cell','Colloid is placed in a2mm thick glass cell, rotated to prevent photodegeneration. No rotation speed, optical density or path correction is supplied.'),
 ('upstream','The transient setup is described in detail in reference13, listed as submitted. No article identity or omitted apparatus settings can be supplied from that citation alone.'),
 ('temperature','All experiments use samples at room temperature; numerical temperature is not specified.')]:add('ta-method-'+id,1,'Experimental Section, transient absorption','analytical_method',claim)
for id,claim in [
 ('excitation','PL uses440nm excitation from an optical parametric oscillator pumped by the third harmonic of a Q-switched Nd:YAG laser. The parent source reports5ns pulse duration at10Hz; do not assign this repetition rate to the fs transient setup.'),
 ('collection','PL spectra are acquired in a90° setup through a cutoff filter, monochromator and CCD. Exact component models, bandwidths and calibrations are unreported.'),
 ('correction','A water reference spectrum is subtracted to correct Raman bands and background. This does not provide a material Raman spectrum or a separate Raman-property data point.')]:add('pl-method-'+id,1,'Experimental Section, photoluminescence','analytical_method',claim)
add('abs-method-missing',2,'Results, Absorption Spectra','analytical_method','Steady-state absorption spectra are reported at room temperature after synthetic stages. Source gives no separate steady-state absorption instrument, cell path, dilution or baseline protocol; do not assume the transient2mm cell necessarily applies.')

for system,claim in [
 ('i','Figure2I labels a=CdS core, b=CdS/(HgS)1 after B, c=CdS/(HgS)1/(CdS)1 after C.'),
 ('ii','Figure2II labels a,b,c identical stage descriptions to I; d=CdS/(HgS)2 after second B, e=CdS/(HgS)2/(CdS)1 after final C. Caption writes d as CdS/(HgS)1/(HgS)1, equivalent contiguous layers.'),
 ('iii','Figure2III labels a,b,c as I; d=CdS/(HgS)1/(CdS)3 after both additional C steps, e=CdS/(HgS)1/(CdS)2/(HgS)1 after B, f=the final capped two-well particle. There is no separately labeled spectrum after the first of the two extra C steps.')]:add('abs-stages-'+system,2,'Absorption Spectra and Figure2 caption','stage_specific_measurement_scope',claim)
for id,page,claim in [
 ('core',3,'Figure2 caption assigns starting CdS-core absorption at470nm; this is a source spectral feature, not enough to resolve3.2 versus3.5nm core size.'),
 ('progression',2,'Absorption edges shift continuously to red through the shown synthetic stages, attributed to increased HgS-well or nanoparticle size. No digitized full spectra/arrays supplied.'),
 ('i',2,'Second-derivative absorption minimum at625nm gives lowest optically allowed transition for systemI.'),
 ('ii',2,'Second-derivative absorption minimum at700nm gives lowest optically allowed transition for systemII.'),
 ('iii',2,'Second-derivative absorption minimum at670nm gives lowest optically allowed transition for systemIII.'),
 ('energy-order',2,'III’s lowest allowed transition lies energetically between I and II. Preserve wavelength/energy distinction:700nm is lower energy than670nm or625nm.'),
 ('oscillator-ratio',2,'Source reports III lowest-exciton oscillator strength about twice that of I or II; Figure2 caption says I and II have the same strength. No absolute oscillator strength, integrated-area method, error bars or independent concentration normalization protocol supplied.'),
 ('atom-context',2,'Authors state a III nanoparticle has about twice the atom count of I and equal HgS amount to II. These are architectural comparison statements, not measured atom counts or total-batch mercury balances.'),
 ('state-mixing',2,'Authors propose mixing between the two HgS-well states creates newly allowed transitions near670nm. This is a mechanistic interpretation, not measured wavefunction or a new quantitative model.')]:add('abs-result-'+id,page,'Absorption Spectra/Figure2','measurement_or_interpretation',claim)

for id,claim in [
 ('qy','All systems have weak PL, estimated quantum yield below1%. This is an approximate strict upper estimate, not zero and not an independently tabulated exact yield for each specimen.'),
 ('broad','Broad emission is attributed mainly to trap states, initially considered at CdS/HgS interface or particle surface.'),
 ('onset','PL onsets follow absorption energy ordering:III onset lies between I and II. No precise PL-onset wavelengths are tabulated here.'),
 ('i','PL maximum for systemI is820nm.'),
 ('ii','PL maximum for systemII is950nm.'),
 ('iii','PL maximum for systemIII is820nm, same as I despite III’s intermediate absorption edge.'),
 ('trap-assignment','Shared I/III PL peak with monolayer HgS wells, versus redderII double-layer peak, motivates trap states governed by well thickness and located at CdS/HgS interfaces, not exterior surface. This is an author inference, supported by cited prior TEM/ODMR/ESR studies3,15, not a new site-resolved measurement.')]:add('pl-result-'+id,3,'Emission Spectra/Figure3','measurement_or_interpretation',claim)

for id,page,claim in [
 ('short',3,'Upon400nm excitation, all three systems show a roughly5ps short-lived negative transient component in the higher-energy absorption region. This is bleach-recovery timescale, not PL lifetime at every wavelength.'),
 ('long',3,'At lower energies, a distribution of longer decay times increases with increasing wavelength. No single scalar long lifetime or complete fitted-parameter table supplied.'),
 ('i-transition',3,'First appearance of long-lived component is at600nm forI.'),
 ('ii-transition',3,'First appearance of long-lived component is at700nm forII.'),
 ('iii-transition',3,'First appearance of long-lived component is at650nm forIII.'),
 ('transition-scope',3,'Crossover wavelengths correlate with PL onset qualitatively; they differ from625/700/670nm absorption-minimum values and must remain separate properties.'),
 ('negative-signal',3,'Negative transient signal can represent bleaching or stimulated emission; bleaching is limited to a spectral interval in which the sample absorbs.'),
 ('stimulated-emission',4,'The source assigns long-lived low-energy signal in PL spectral regions to stimulated emission from carrier recombination within an inhomogeneous trap-state distribution.'),
 ('bleach',4,'Higher-energy short-lived component is assigned to recovery of the lowest optically allowed excitonic-state bleach.'),
 ('theory',4,'Reference18 predictions forI/II are said consistent with cited hole-burning, line-narrowing and transient spectroscopy3,11–14. Authors explicitly say no lowest-excitonic-state energy calculation is available forIII with two HgS wells separated by two CdS layers.')]:add('ta-result-'+id,page,'Energy Dependence of Relaxation Dynamics and continuation','measurement_or_interpretation',claim)

for id,page,claim in [
 ('figure1',2,'Figure1 contains three colored architecture sketches with HgS red, CdS green, nominal dimensions in nm, radial potential/wavefunction sketches to the right with radius ticks0,1,2,3nm. Caption cites wavefunctions calculated in Figure4 of reference18. These are schematic/source-attributed functions, not measured morphology or newly computed structures.'),
 ('figure1-theory-scope',2,'Figure1 sketches a two-well wavefunction forIII, but p5551 explicitly reports no quantitative lowest-exciton-energy theory for thatIII geometry. Preserve schematic versus quantitative-calculation scope; do not fabricate numericalIII wavefunctions.'),
 ('figure2',3,'Figure2 absorption(OD) versus Energy(eV), lower labeled range approximately1.2–3.0eV; dual upper wavelength scale labeled1000,800,600nm. PanelsI/II/III contain3/5/6 stage curves. Different vertical plotting scales are not automatic concentration-normalized oscillator-strength integrals.'),
 ('figure3',3,'Figure3 PL intensity(a.u.) versus Energy(eV), lower labels about1.2–3.0eV and upper wavelength scale1000,800,600nm. Three panels correspondI/II/III; intensity scaling/background-subtracted curves are not absolute quantum yields.'),
 ('figure4',4,'Figure4 plots decay time(ps) versus energy(eV), with upper wavelength(nm) axis and I/II/III panels. Insets show bleach intensity(a.u.) versus delay time(ps), with delay ticks0–100ps. Original measured points/curves remain source assets; no raw point values reconstructed.'),
 ('figure4-i-inset',4,'Figure4I inset original labels: bleach at650nm and bleach at500nm. Long650nm trace and short500nm trace are distinct illustrative kinetics.'),
 ('figure4-ii-inset',4,'Figure4II inset original labels: bleach at900nm and bleach at500nm.'),
 ('figure4-iii-inset',4,'Figure4III inset original labels: bleach at750nm and bleach at600nm.'),
 ('figure4-label-conflict',4,'All inset traces are labeled bleach, although surrounding main text/caption interpret the longer-wavelength component as stimulated emission. Preserve original labels and explanatory interpretation, not a silent figure relabeling.'),
 ('figure4-fits',4,'Lines are least-squares fits but caption says intended mainly as a visual aid. Intersections identify600/700/650nm crossover; do not treat these lines as a validated mechanistic law or derive unjustified exact lifetimes.')]:add(id,page,'Original figure and caption','original_figure_or_scope',claim)
add('conclusion-coupling',4,'Conclusion','author_interpretation','Adding second HgS layer red-shifts lowest exciton; separating it by CdS reduces that red shift. Observed red shift is interpreted as interaction between wells rather than fully independent wells. Earlier preparation wording calls two wells independent; this means spatially separate and must not override later coupling inference.')
add('conclusion-outlook',4,'Conclusion','outlook','Future work will vary CdS-barrier and HgS-well thickness to investigate strength/nature of carrier interactions. No additional barrier-series recipes or properties are reported.')
add('acknowledgment',4,'Acknowledgment','source_metadata','Supported by Office of Naval Research contractN00014-95-1-0306; Braun supported by Alexander von Humboldt Foundation Feodor Lynen Fellowship. Funding is not experimental sample evidence.','retain_bibliographic_metadata')
add('si-search',4,'Complete supplied article and local file search','source_coverage','No supporting-information declaration appears in the supplied four-page article. Bounded local DOI/author/title filename search and current grouped fingerprint locate only two byte-identical main copies. SI not located/matched; not a claim that no SI could exist.','retain_coverage_limitation')
add('unreported-techniques',4,'Complete supplied main article','missingness','No current-source TEM/SAED/XRD/Raman material spectrum, lattice/CIF, direct shell-composition map, DLS, isolated yield, toxicity, device test, raw spectral array or raw lifetime-fit table is supplied. References to prior structural/theory work remain context.','retain_coverage_limitation')

refs=[
('Eychmüller, A.; Mews, A.; Weller, H. Chem. Phys. Lett.1993,208,59.','Prior chemical QDQW.'),
('Mews, A.; Eychmüller, A.; Giersig, M.; Schooss, D.; Weller, H. J. Phys. Chem.1994,98,934.','Cited full synthesis details; not independently re-read in this task.'),
('Mews, A.; Kadavanich, A. V.; Banin, U.; Alivisatos, A. P. Phys. Rev. B1996,53,R13242.','Prior TEM/optical structural context.'),
('Mews, A.; Eychmüller, A. Ber. Bunsen-Ges. Phys. Chem.1998,102,1343.','QDQW context.'),
('Dumas, Ph.; Derycke, V.; Makarenko, I. V.; Houdre, R.; Guaino, P.; Downes, A.; Salvan, F. Appl. Phys. Lett.2000,77,3992.','Quantum-well context.'),
('Ahn, Y. H.; Yahng, J. S.; Sohn, J. Y.; Yee, K. J.; Hohng, S. C.; Woo, J. C.; Kim, D. S.; Meier, T.; Koch, S. W.; Lim, Y. S.; Kim, E. K. Phys. Rev. Lett.1999,82,3879.','Quantum-well context.'),
('Kim, D. S.; Ko, H. S.; Kim, Y. M.; Rhee, S. J.; Hohng, S. C.; Yee, Y. H.; Kim, W. S.; Woo, J. C.; Choi, H. J.; Ihm, J.; Woo, D. H.; Kang, K. N. Phys. Rev. B1996,54,14580.','Quantum-well context.'),
('Abeeluck, A. K.; Garmire, E.; Canoglu, E. J. Appl. Phys.2000,88,5859.','Solid-state device motivation.'),
('Shen, A.; Liu, H. C.; Gao, M.; Dupont, E.; Buchanan, M.; Ehret, J.; Brown, G. J.; Szmulowicz, F. Appl. Phys. Lett.2000,77,2400.','Solid-state device motivation.'),
('Kawakami, Y.; Narukawa, Y.; Omae, K.; Fujita, S.; Nakamura, S. Appl. Phys. Lett.2000,77,2151.','Solid-state device motivation.'),
('Kamalov, V. F.; Little, R.; Logunov, S. L.; El-Sayed, M. A. J. Phys. Chem.1996,100,6381.','Prior single-layer-well spectroscopy.'),
('Little, R. B.; Burda, C.; Link, S.; Logunov, S.; El-Sayed, M. A. J. Phys. Chem. A1998,102,6581.','Prior single-layer-well spectroscopy.'),
('Braun, M.; Burda, C.; El-Sayed, M. A., submitted.','Incomplete submitted-work citation for synthesis/transient details and double-layer prior work. No inferred title, DOI, year or publication coordinates.'),
('Yeh, A. T.; Cerullo, G.; Banin, U.; Mews, A.; Alivisatos, A. P.; Shank, C. V. Phys. Rev. B1999,59,4973.','Cited spectroscopy and theory comparison.'),
('Lifshitz, E.; Porteanu, H.; Glozman, A.; Weller, H.; Pflughoefft, M.; Eychmüller, A. J. Phys. Chem. B1999,103,6870.','Cited ODMR/ESR trap study; not a current assay.'),
('Koberling, F.; Mews, A.; Basché, T. Phys. Rev. B1999,60,1921.','Prior QDQW spectroscopy.'),
('Bryant, G. Phys. Rev. B1995,52,R16997.','Earlier theory.'),
('Jaskólski, W.; Bryant, G. Phys. Rev. B1998,57,R4237.','Figure1 wavefunction attribution and theoretical comparison for I/II; not current measured coordinates.'),
('Chang, K.; Xia, J.-B. Phys. Rev. B1998,57,9780.','Prior multiple-layer theory mentioned in introduction.')]
for n,(cite,scope) in enumerate(refs,1):add(f'reference-{n:02}',4,f'References and Notes,{n}','cited_reference',cite+' '+scope,'retain_reference_not_new_experiment')

assert len({u['id'] for u in U})==len(U)
identity={'source_id':SID,'doi':DOI,'title':'Variation of the Thickness and Number of Wells in the CdS/HgS/CdS Quantum Dot Quantum Well System','authors':['Markus Braun','Clemens Burda','Mostafa A. El-Sayed'],'journal':'Journal of Physical Chemistry A','year':2001,'volume':105,'issue':23,'pages':'5548–5551','received':'2001-01-03','final_form':'2001-05-01','published_online':'2001-05-22','primary_article':True,'source_path':str(S),'source_sha256':sha(S),'legacy_copy_path':str(L),'legacy_copy_sha256':sha(L),'copies_byte_identical':sha(S)==sha(L),'main_pages':4,'verified_by':'Visible title, byline, DOI footer, consecutive printed page headers and complete four-page article contents; PDF metadata No Job Name is not used as title evidence.','si_status':'not_located_or_matched_locally_no_declaration_in_supplied_main','si_expected_content':None,'si_search_scope':'Current fingerprint generation2 contains two identical main files. Case-insensitive rg filename search across both source folders for jp010002, Braun, Burda, or quantum-dot-quantum-well title pattern found only these two main copies. This does not prove absence in every differently named file.','external_research':False}
pages=[{'pdf_page':n,'printed_page':5547+n,'text_file':f'main-{n:02}.txt','text_sha256':sha(B/f'main-{n:02}.txt'),'text_read':True,'render_file':f'main-{n}.png','render_sha256':sha(B/f'main-{n}.png'),'visually_reviewed':True,'review_scope':'Complete supplied page: both columns, figures/captions, reference list and headers/footers.'} for n in range(1,5)]
conflicts=[{'id':'core-size','source_units':['step-a-growth','step-a-size-conflict','structure-core'],'issue':'3.5nm growth prose versus3.2nm all-system/Figure1 core.'},{'id':'sulfide-notation','source_units':['step-a-nucleation'],'issue':'PrintedS−/H+ description is not silently changed into a balanced equilibrium/speciation model.'},{'id':'figure4-signal-label','source_units':['figure4-label-conflict','ta-result-stimulated-emission'],'issue':'Inset labels bleach versus long-wavelength stimulated-emission interpretation.'},{'id':'figure1-theory-scope','source_units':['figure1-theory-scope','ta-result-theory'],'issue':'Wavefunction sketches do not establish a new quantitativeIII excitonic theory.'},{'id':'independent-wells','source_units':['route-iii-transforms','conclusion-coupling'],'issue':'Spatially separate wells still show inferred interaction; avoid interpreting preparation independent as uncoupled.'}]
for c in conflicts:c['source_units']=[SID+'-'+u for u in c['source_units']]
audit={'source_id':SID,'doi':DOI,'status':'complete_supplied_main_text_and_visual_inventory_no_matched_SI','reviewer':'independent_source_audit_agent','reviewed_at':datetime.now(timezone.utc).isoformat(),'source_path':str(S),'source_sha256':sha(S),'coverage':{'main_pages':4,'text_pages_read':4,'visual_pages_reviewed':4,'si_pages_verified':0,'si_status':identity['si_status'],'original_figures':4,'original_tables':0,'numbered_equations':0,'references_and_notes':19,'scope':'Complete supplied main. No external citations independently read, no curve digitization, no located/matched SI.'},'pages':pages,'unit_count':len(U),'units':U,'conflicts':conflicts,'critical_limits':['StepA3.5nm versus3.2nm nominal core conflict preserved.','Unknown Cd/Hg salts, stabilizer form/dose, H2S aqueous stock quantities and supplemental Cd²⁺ doses.','Exchange leaves dissolved Cd²⁺ available; repeat-C top-ups distinct from C immediately following B.','Architecture and prior theoretical wavefunctions are not measured atomic structure.','Raman correction does not create a material Raman spectrum.','Room-temperature statement has optical-method context and is not a specified numeric synthesis temperature.','Main-only reading; no SI, cited upstream full synthesis or submitted reference13 was independently inspected.'],'independent_source_inventory':True,'external_downloads':False,'site_mutated':False}
write('source-identity.json',identity);write('independent-page-coverage.json',{'source_id':SID,'pages':pages,'main_text_pages_read':4,'main_visual_pages_reviewed':4,'si_pages_reviewed':0});write('source-audit.json',audit)
(B/'source-identity.md').write_text('# Braun 2001 source identity\n\n'+identity['title']+'\n\nBraun, Burda and El-Sayed. Journal of Physical Chemistry A 2001, 105(23), 5548–5551. DOI '+DOI+'. Received January 3; final form May 1; online May 22, 2001.\n\nBoth local files are byte-identical four-page main articles. SHA-256: '+sha(S)+'.\n\nNo SI declaration was found in the complete supplied main. No SI was located or matched in the bounded local grouped/filename search; this is not proof that none exists elsewhere. No download or external research was performed.\n',encoding='utf8')
(B/'source-audit.md').write_text('# Braun 2001 independent source inventory\n\nAll four main pages were completely read as text and visually inspected. '+str(len(U))+' stable source units retain methods, architecture, spectroscopy, figures, interpretation, missingness and all 19 references. Four figures; no tables or numbered equations.\n\n'+ '\n'.join('- '+x for x in audit['critical_limits'])+'\n\n'+ '\n\n'.join('**'+u['id']+'** — p. '+str(u['printed_page'])+', '+u['locator']+'. '+u['claim']+' ['+u['disposition']+']' for u in U)+'\n',encoding='utf8')
print(json.dumps({'units':len(U),'source_audit_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json'),'kinds':dict(Counter(u['kind'] for u in U))},indent=2))
