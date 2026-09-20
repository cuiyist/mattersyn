"""Independent complete main+SI inventory after actual text and page-image review."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
from pypdf import PdfReader
B=Path(__file__).resolve().parent;SID='banerjee2003';DOI='10.1021/ja035980c'
ROOT=Path('[local path redacted]');S=ROOT/'data_Tanjin/papers/50k_all_papers/10.1021_ja035980c.pdf';SI=S.with_name('10.1021_ja035980c_si_1.pdf');L=ROOT/'mattersyn/downloaded_papers'/S.name;LS=L.with_name(SI.name)
U=[];F=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):(B/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def add(i,p,loc,kind,claim,disposition='retain_source_linked_evidence',role='main'):
 U.append({'id':SID+'-'+i,'source_unit_id':SID+'-'+i,'source_role':role,'pdf_page':p,'printed_page':10341+p if role=='main'else None,'locator':loc,'kind':kind,'claim':claim,'disposition':disposition})
def many(prefix,p,loc,kind,rows,disposition='retain_source_linked_evidence',role='main'):
 for i,c in rows:add(prefix+i,p,loc,kind,c,disposition,role)
def fact(i,uid,scope,prop,value=None,unit=None,minimum=None,maximum=None,approximate=False,status='reported',qualifier=''):
 F.append({'id':SID+'-fact-'+i,'source_unit_id':SID+'-'+uid,'sample_scope':scope,'property':prop,'value':value,'minimum':minimum,'maximum':maximum,'unit':unit,'approximate':approximate,'status':status,'qualifier':qualifier,'eligible_training':False})
many('identity-',1,'Title/byline/footer','source_metadata',[
 ('title','In Situ Quantum Dot Growth on Multiwalled Carbon Nanotubes.'),
 ('authors','Sarbajit Banerjee and Stanislaus S. Wong; Wong corresponding author. SUNY Stony Brook Department of Chemistry and Brookhaven National Laboratory Materials and Chemical Sciences Department.'),
 ('journal','Journal of the American Chemical Society2003,125,issue34,pages10342–10350,DOI10.1021/ja035980c.'),
 ('dates','Received May6,2003; published online July31,2003. Download watermark July1,2026 is administrative, not experiment/publication date.'),
 ('administrative','ACS copyright, contact addresses/emails and manuscript code JA035980C are provenance metadata, not synthesis instructions.')],'retain_bibliographic_metadata')
many('abstract-',1,'Abstract','study_summary',[
 ('product','Current study mineralizes crystalline CdTe quantum dots in situ on oxidized multiwalled carbon nanotubes, forming tube–nanocrystal heterojunctions. This is a composite rather than an isolated pristine CdTe-only product.'),
 ('approach','Authors propose direct metal-precursor coordination to oxygenated nanotube sites before growth as a controlled chemical route to networks and junctions.'),
 ('methods','Characterization includes SEM,TEM,HRTEM,EDS,XPS,Raman,UV-visible and XRD; infrared data/method appear in main and matched SI. No current charge-transport/device measurement is claimed.')])
many('context-',1,'Introduction','cited_context',[
 ('cnt-properties','CNT structural,electronic,mechanical and optical properties motivate controlled device assembly; reference1 is background, not a new measured property here.'),
 ('assembly','Biological recognition,lithography,supramolecular assembly and prepatterned-substrate nanotube networks/CVD cite refs2–9; no such additional synthesis is demonstrated here.'),
 ('applications','Computing,data storage,photovoltaics,textiles,sensors and drug-delivery applications cite refs10–12. They are prospective context, not performance data for this composite.'),
 ('functionalization','Prior CNT chemistry targets endcaps,defects,sidewalls and hollow interiors: covalent conjugated-bond reactions,noncovalent pi-stacking,end/defect chemistry and macromolecular wrapping cite refs13–23.')],'retain_cited_context_not_current_recipe')
many('context-',2,'Introduction continuation','cited_context',[
 ('heterostructures','BN coaxial growth,carbide solid-state reactions and Si-nanowire growth at CNT ends cite refs24–27,not present routes.'),
 ('previous-cdse-tio2','Prior authors’ oxidized-CNT/CdSe-thiol and TiO2/11-aminoundecanoic-acid heterostructures use amide-forming EDC chemistry,ref28. EDC is1-ethyl-3-(3-dimethylaminopropyl)carbodiimide hydrochloride. These precursor identities belong to previous work,not current CdTe growth.'),
 ('previous-limitation','Prior amide-linked ball-and-stick heterostructures are described as isolated/disordered; refs29–31 analogous systems. No quantitative current versus old assembly-yield comparison.'),
 ('coordination','Prior SWNT bulky inorganic complexes,solubility/catalysis and recoverable metal supports cite32–33; ruthenium-derived T/Y-junction MWNTs cite34. Do not create current Ru or SWNT synthesis records.'),
 ('ligand-role','MWNTs are proposed as bulky pi-conjugated ligands and growth terminators; dots bridging gaps can form junctions. Geometry control is an author interpretation,not refined atomic interface coordinates.'),
 ('transport-outlook','Carrier mobility,trapping/delocalization,charge separation and photovoltaic optimization motivate work; no measured mobility,efficiency or carrier dynamics.'),
 ('generalization','Generalization to other binary/complex nanocrystals and oriented-attachment insight is prospective. Do not assign unreported material syntheses.')],'retain_cited_or_author_context_not_current_recipe')
many('precursor-',2,'Experimental, nanotube processing and heterostructure synthesis','chemical_identity',[
 ('mwnt','Commercial multiwalled carbon nanotubes obtained from MER Corporation. Feed mass,diameter,length,wall count,purity grade and initial catalyst amount unspecified.'),
 ('oxidant','Vigorous KMnO4/H2SO4 treatment,ref35. Permanganate and sulfuric-acid amounts/concentrations,ratio,addition order,temperature,time and quench are not given.'),
 ('hcl','Successive treatment with35%HCl after oxidation; percent basis,dilution recipe,volume,duration and temperature unknown.'),
 ('hf','Subsequent10%HF treatment; percent basis,volume,duration,temperature and exact wash sequence between acids unspecified.'),
 ('wash-water','Extensive distilled-water washing after treatment. Water volume,number of washes,endpoint pH and recovery method unknown.'),
 ('oxidized-mwnt','Processed oxygenated MWNTs used as ligands/templates. Carboxylic acid,alcohol and ketone groups expected; individual concentrations and atomistic arrangement not measured.'),
 ('cdo','CdO is the cadmium precursor in a modified Peng one-pot procedure,refs36–37. Mass,amount,purity,supplier and Cd:MWNT loading unreported.'),
 ('tdpa','Tetradecylphosphonic acid(TDPA) is used substoichiometrically so some Cd may coordinate to nanotube oxygen groups. Exact TDPA amount,Cd:TDPA ratio and percentage vacancy unknown; no guessed numerical ratio.'),
 ('topo','Trioctylphosphine oxide(TOPO) is the high-temperature reaction medium. Charge,purity,grade,supplier and final concentration unspecified.'),
 ('te-top','A Te solution in trioctylphosphine(TOP) is injected. Exact Te allotrope,stock preparation,stoichiometric TOPTe molecular assignment,mass,concentration,volume and injection speed unspecified.'),
 ('argon','Argon is explicitly used while MWNT/CdO/TDPA are heated in TOPO; flow,pressure,purity and purge protocol unreported. Later phases are not independently restated as separate atmosphere measurements.'),
 ('toluene','5mL toluene added after cooling to50°C; further copious toluene washes remove free CdTe. Only first dilution volume quantified.'),
 ('methanol','Methanol induces nanocrystal precipitation. Volume,ratio,addition rate,temperature and number of precipitation cycles unspecified.'),
 ('filter','0.2µm PTFE membrane filters the precipitated solid mixture; membrane pore size is not nanocrystal size and PTFE is processing equipment,not product precursor.'),
 ('analysis-media','Ethanol is used for TEM/HRTEM sample droplets; free CdTe/toluene and sonicated heterostructure/DMF are distinct UV-visible preparations. These solvents are not invented synthesis feeds.')])
many('protocol-',2,'Experimental, nanotube processing and heterostructure synthesis','operation',[
 ('oxidation','Treat MWNTs vigorously with KMnO4/H2SO4 according to cited ref35,then successively with35%HCl and10%HF. Named method is incomplete without external reference details; no undocumented timed recipe is added.'),
 ('wash-dry','Extensively wash with distilled water,then heat at150°C in a drying oven. Drying duration,atmosphere and endpoint unknown.'),
 ('purification-result','Authors say treatment removes almost all metal impurities(such as Fe) and substantial amorphous carbon; residual metal below XPS/EDS detection. Detection limit and removal percentage are unreported,so do not record zero metal.'),
 ('mix-heat','Mix processed MWNTs,CdO and TDPA in TOPO; heat to320°C under argon with vigorous stirring. Reagent charges,hold time,ramp,stirring rate and equipment geometry unreported.'),
 ('substoich-rationale','Substoichiometric TDPA intentionally permits some Cd coordination to oxygenated MWNT groups,especially carboxylic acid/alcohol. No verified solution complex or exact vacant-site fraction.'),
 ('injection','Inject Te/TOP solution at300°C. Transition from320°C,temperature stabilization,injection duration/volume and atmosphere restatement absent.'),
 ('growth','Allow nanocrystals to grow at250°C for20min. This is the stated growth interval,not320°C or300°C hold duration.'),
 ('heat-off','Remove heating source after20min growth; cool to50°C. Cooling rate and duration unreported.'),
 ('dilution','At50°C add5mL toluene to reaction mixture. This volume is not the total reaction volume or subsequent washing volume.'),
 ('precipitate','Add methanol to initiate precipitation. Solid residue includes functionalized tubes and unbound CdTe nanocrystals; not a pure composite at this step.'),
 ('filter','Filter the solid residue over0.2µm PTFE membrane; initially retains composite plus free crystal-containing residue.'),
 ('toluene-wash','Use copious toluene to wash unbound CdTe off the membrane. Retained material is described as functionalized heterostructures; washed fraction is a separate CdTe-rich characterization context.'),
 ('final-dry','Dry retained heterostructures and characterize. Temperature,time,atmosphere,isolated yield,storage and residual-ligand/solvent amounts unreported.')])
many('method-',3,'Experimental, electron microscopy','acquisition_method',[
 ('tem-preparation','Dry sample droplets from an ethanolic solution on a300-mesh Cu grid with lacey carbon film; source calls it solution without proving molecular dissolution. Droplet volume/concentration/drying conditions unknown.'),
 ('tem','Low-resolution PhilipsCM12 TEM with EDAX at120kV.'),
 ('hrtem','JEOL2010F HRTEM with OxfordINCA EDS at200kV. No measured lattice-spacing table,zone-axis indexing or SAED pattern supplied.'),
 ('sem-preparation','Drop dry samples on Cu grids held over a Be plate in a homemade sample holder. Copper/beryllium are substrate/equipment context,not target elements.'),
 ('sem','Leo1550 field-emission SEM,accelerating voltage2–10kV,working distance2mm.')])
many('method-',3,'Experimental, XPS/XRD/optics','acquisition_method',[
 ('xps-preparation','Attach samples to stainless-steel holders with conductive double-sided tape; place in KratosDS800 XPS vacuum chamber,base pressure approximately5×10−9torr. This pressure is analytical,not synthesis pressure.'),
 ('xps-survey','Hemispherical electron-energy analyzer; MgKα excitation; initial XPS at80eV pass energy and0.75eV steps. Source photon energy is not numerically stated.'),
 ('xps-high-resolution','High-resolution XPS uses10eV pass energy and0.1eV steps. These are instrument parameters distinct from chemical binding energies.'),
 ('xrd','Scintag powder diffractometer in Bragg configuration with CuKα radiation,λ1.54Å. Scan step/rate,peak fitting,phase fractions and lattice constants not reported.'),
 ('uvvis-instrument','High-resolution UV-visible spectra on ThermospectronicsUV1 with10mm-path quartz cells. Scan settings,concentration and absolute extinction calibration absent.')])
many('method-',4,'Experimental optical methods continuation','acquisition_method',[
 ('uvvis-preparation','CdTe nanocrystals dissolved in toluene; heterostructure dispersed by sonication in DMF. Sonication duration/power,concentration and sedimentation time absent; solvent difference limits direct absolute intensity comparison.'),
 ('ftir','ThermoNicoletNexus670 with ZnSe single-reflectance ATR accessory. SI gives oxidized MWNT trace only,not a spectrum demonstrating all hybrid interfacial species.'),
 ('raman','JascoVentuno micro-Raman,200µm confocal aperture,785nm diode-laser excitation,10mW power. Aperture is not beam waist/spot area; no W/cm2 conversion or acquisition temperature stated.')])
many('morphology-',4,'Results microscopy; Figure1','observation',[
 ('oxidation','Pristine walls have a crystalline graphite lattice; aggressively processed MWNTs have opened caps,partially removed outer layers and serrated sidewalls. Chemical oxygen identities are supported elsewhere/inferred,not visible individual functional groups in these TEM images.'),
 ('sites','Open ends and etched defect sites are interpreted as oxygenated-ligand nucleation sites. Images establish morphology,not a quantitative functional-group map.')])
many('morphology-',5,'Results microscopy continuation','observation',[
 ('purity','No extraneous catalyst particles in processed tubes according to XPS/EDS; retain detection-limit qualification and no quantitative elemental purity claim.'),
 ('tip-density','Figures2a/d show greater particle density near tips. Curvature-enhanced reactivity and functional-group abundance are proposed using refs38–39,not directly measured site densities.'),
 ('etched-layers','Prior acid-etching literature suggests outer layers near tips are destroyed after opening. Distinguish cited rationale from exact measured wall counts here.')])
many('morphology-',6,'Results microscopy continuation','observation',[
 ('sidewall','Figure2 shows substantial sidewall attachment in addition to ends; authors contrast aggressive oxidation with prior end-limited amidation.'),
 ('junctions','Figures2b/e and4a show nanocrystal-mediated junctions between MWNTs/bundles. No electrical continuity or carrier transport measured.'),
 ('eds-elements','Authors report Cd,Te and P confirmed by EDS; P is attributed to secondary TDPA ligand. Original Figure4 inset visibly labels C,O,Cu,Cd,Te; no individually labeled P peak or quantitative stoichiometry is supplied.'),
 ('lattice','Figure3 HRTEM displays lattice fringes and interfaces of CdTe on MWNT. Authors assign predominantly wurtzite with some cubic zinc-blende-like crystals; no refined single polymorph or full atomic interface structure.'),
 ('elongated-tip','Figure3b shows an irregular elongated crystal at an opened tip,with carbon support film present.'),
 ('defect','Figure3c illustrates attachment at an apparent etched sidewall discontinuity; arrows frame a defect,not counted oxygen atoms.'),
 ('edge','Figure3d and3a inset show nanocrystals at exposed outer edges; site-preference interpretation is qualitative.')])
many('growth-',7,'Results growth interpretation','author_interpretation',[
 ('diffusion','Elongation is explained by diffusion-limited growth: bulky MWNT obstructs one crystal face while monomer adds to a free end,ref40. No measured diffusion constant,flux or growth-rate law.'),
 ('steric','Bulky nanotube ligand can control directional monomer access,analogous to coordination complexes refs32–33. This is explanatory,not a reconstructed atomistic growth simulation.'),
 ('free-size','Text describes free washed-away crystals as relatively monodisperse,quasi-spherical,5nm,from conventional cadmium-phosphonic-acid growth. Laterp9 says washings are less monodisperse than no-tube~5nm crystals; preserve both scoped descriptions rather than one exact uniform population.')])
many('growth-',8,'Results morphology and controls','observation',[
 ('bound-size','Bound in-situ crystals have long-axis lengths1–9nm and aspect ratios1–5. These are source ranges,not a mean diameter,complete size distribution or all crystallite sizes.'),
 ('heterogeneity','Authors attribute bound-crystal variability to local functional-group density,site geometry/monomer access and spacing between groups/tubes. No quantified dependence or individually matched recipe per morphology.'),
 ('spacing','Intertube spacing is proposed to explain crystal-mediated junctions; actual distance distribution and oriented-growth trajectories are unreported.'),
 ('controls','Successive growth controls used pristine/raw and mildly oxidized tubes; those terms do not establish separate complete recipes for all named controls. Few if any nanocrystals coordinated to pristine unoxidized tubes.'),
 ('oxygen-high','Reported study results correspond to highly oxidized MWNTs with approximately5–6atomic%oxygen by XPS; this is precursor surface composition,not bulk composite oxygen or functional-group counts.'),
 ('oxygen-low','Mildly oxidized MWNTs with approximately1–2atomic%oxygen show sparse coordinated nanocrystal coverage. Their oxidation recipe,masses and quantified coverage are absent.'),
 ('coverage-correlation','Greater oxidation correlates with greater coverage at ends/sidewalls; no quantitative dose-response curve or universal oxygen threshold established.')])
many('xrd-',8,'Additional structural characterization; Figure5ii','observation',[
 ('phase','XRD indicates predominant wurtzite CdTe with possible zinc-blende stacking faults and some zinc-blende particles. Overlapping reflections prevent treating it as quantitatively phase-pure.'),
 ('broadening','Peaks are broader than analogous bulk because of finite particle size according to authors; no Scherrer numerical size or explicit broadening fit reported.'),
 ('indexing','Figure5ii black labels: combined100,002,101;110;103;200 for wurtziteCdTe. Red MWNT labels002,101,004. Near~44° the red101 and black103 overlap in the printed label. Do not assign all peaks to CdTe.')])
many('xps-',8,'Additional structural characterization; Figure5i','observation',[
 ('carbon','C1s high-binding-energy asymmetry is interpreted as carboxylic-acid/carboxylate-like surface structures. No deconvolved species-area percentages or exact C1s chemical shifts given.'),
 ('cadmium','Cd3d5/2 high-resolution peak is assigned to CdTe with Cd binding energy405.22eV. Do not confuse with pass energy or claim a quantitative Cd:Te ratio.'),
 ('tellurium','Source literally assigns Te3d5/2 features to TeO3 species from inadequate surface passivation. Preserve this author chemical assignment without silently changing to TeO2 or supplying a charge/state not printed.'),
 ('passivation','Authors propose bulky nanotubes limit surface coordination and permit ambient/prolonged-air decomposition,accelerated by higher temperature. Exposure duration,oxidized fraction,kinetics and stability lifetime not measured.'),
 ('thermal-carboxyl','Heating can remove MWNT carboxyl groups,not completely until approximately350°C; intrinsic nanotube/nanocrystal structures are expected to remain intact to such temperatures. This is interpretation/thermal context,not a reported annealing experiment or operational stability guarantee.')])
many('raman-',8,'Raman discussion; Figure6','observation',[
 ('cdte','Hybrid Raman at785nm shows LO-type band166cm−1 absent from precursor-MWNT spectrum. It is assigned to confined CdTe clusters.'),
 ('bulk-reference','Downshift/broadening relative to bulk170cm−1 is discussed with ref41. The bulk value is a literature comparator,not an independently synthesized/measured bulk CdTe control.'),
 ('g-band','Both precursor and hybrid show nanotube G modes near1590cm−1,ref42; no exact fitted shifts,intensity ratio or defect-density calibration.')])
many('raman-',9,'Raman continuation','observation',[
 ('d-band','A weaker disorder D-mode band appears1290–1320cm−1. Range is not separate exact peak positions for each sample and no ID/IG ratio is provided.')])
many('optical-',9,'Electronic-spectrum discussion; Figure7','observation',[
 ('hybrid','Hybrid electronic spectrum is featureless with no resolvable CdTe exciton. Do not assign a nonexistent exciton energy,band gap,emission maximum or quantum yield.'),
 ('background','Large MWNT background absorbance and broad crystal size/shape distribution are proposed causes of featureless spectrum; no fitted component decomposition.'),
 ('washings','Toluene washings show lower monodispersity than quasi-spherical~5nm crystals grown without nanotube ligands. This is distinct from the broad bound1–9nm cohort; no complete no-tube preparation or raw distribution provided.'),
 ('detachment','Authors postulate washed-away crystals may detach from MWNTs at different growth stages,causing greater heterogeneity. Detachment events and time-resolved growth are not directly observed.'),
 ('anisotropy','Spatial constraint favoring one-dimensional/anisotropic growth is an interpretation tied to ref40,not proof all free crystals retain tube-derived surfaces.')])
many('conclusion-',9,'Conclusions and acknowledgment','author_interpretation',[
 ('scope','Coordination-mediated in-situ CdTe mineralization on MWNTs demonstrated. Authors say crystals appear quantum-confined; no measured full electronic structure or refined atomic interface follows.'),
 ('swnt-limit','Generating enough oxidized functional groups on SWNTs without compromising structural/electronic integrity is described as harder; improved oxidationref43 is future direction,not another present complete SWNT recipe.'),
 ('outlook','Future charge transport through junctions,aligned-tube junction growth and composite thin films are proposed. No current electrical/photovoltaic device metrics.'),
 ('support','SUNYStonyBrook/Brookhaven startup funds,ACS PetroleumResearchFund and3M faculty award acknowledged; microscopy,Raman andXPS contributors named. Administrative provenance only.')])
add('si-declaration',9,'Supporting Information Available','source_identity','Main explicitly declares a PDF infrared spectrum of oxidized multiwalled nanotubes; exactly matches supplied one-page SI content.','retain_identity_evidence')
many('figure-',3,'Figure1 image/caption','original_figure',[
 ('1a','Pristine unprocessed MWNT HRTEM,scale20nm; original support/particle appearance retained.'),
 ('1b','Processed clean MWNT low-resolution TEM,scale125nm.'),
 ('1c','Opened oxidized MWNT tip HRTEM,scale7nm.'),
 ('1d','Etched serrated outer wall HRTEM,scale8nm; arrows indicate removed-wall edges,not atom-resolved oxygen groups.')])
many('figure-',4,'Figure2 image/caption','original_figure',[
 ('2a','SEM particle near tip,scale100nm; arrowCdTe assignment supported by EDS.'),
 ('2b','SEM nanocrystal-mediated junction with CNT bundles,scale200nm.'),
 ('2c','TEM sidewall coverage on MWNT bundle,scale180nm.'),
 ('2d','TEM sidewall/tip-edge CdTe,scale75nm.'),
 ('2e','TEM nanocrystal-mediated nanotube junctions(arrows),scale112nm.')])
many('figure-',5,'Figure3 image/caption','original_figure',[
 ('3a','HRTEM CdTe on MWNT; main and inset are different composite images,each scale5nm.'),
 ('3b','HRTEM elongated CdTe at opened MWNT tip; attachment arrow;scale20nm.'),
 ('3c','HRTEM CdTe at etched-defect site; arrows circumscribe defect;scale5nm.'),
 ('3d','HRTEM dots at serrated sidewall edges;scale10nm; nucleation positions are author interpretations.')])
many('figure-',6,'Figure4 image/caption','original_figure',[
 ('4a','Junction HRTEM crystal between two nanotube bundles,irregular crystals outlined by colored arrows;scale20nm.'),
 ('4b','HRTEM extensive sidewall coverage,scale10nm.'),
 ('4c','HRTEM sidewall coverage,scale10nm.'),
 ('4-eds','Inset EDS has C,O,Cu,Cd,Te labels and horizontal ticks2,4,6,8,10 without in-plot units. Caption explicitly calls energy eV; scale suggests a possible eV/keV inconsistency. Preserve original caption/axis,no unverified numeric conversion or digitized elemental amount.')])
many('figure-',7,'Figures5 and6','original_figure',[
 ('5i-carbon','C1s original red data/black fit trace; binding-energy ticks295,290,285eV(descending); arbitrary intensity without numerical y ticks. No distinct component-fit table.'),
 ('5i-oxygen','O1s original trace with descending ticks534,532,530,528eV. No numerical peak center or oxygen-species composition inferred by digitization.'),
 ('5i-cadmium','Cd3d5/2 original trace,descending ticks408,406,404,402eV;405.22eV is separately stated in prose.'),
 ('5i-tellurium','Te3d5/2 two-feature trace,descending ticks580,578,576,574,572,570eV. No extra exact fitted energies or chemical-state area ratios inferred.'),
 ('5ii','XRD plot spans labeled2θ20–70; arbitrary-intensity y without numeric scale. Original blackCdTe/redMWNT indexing and overlap retained; no new peak positions/rawintensities/CIF.'),
 ('6','Original Raman topblue oxidized precursor,bottomredCdTe–MWNT hybrid. X wavenumber labeled1000,2000,3000,4000cm−1; y arbitrary without numerical labels. Entire high-frequency and low-frequency trace retained; no assignment of every unlabeled mode.')])
many('figure-',8,'Figures7 and8','original_figure',[
 ('7','Original electronic spectra: lowerredCdTe washings,uppergreenhybrid; x ticks300–1000nm,arbitrary y without numericlabels. Hybrid trace ends earlier thanwashings; do not extend or impose identical plotted ranges.'),
 ('8','Conceptual oxidation→CdTe-growth/junction schematic: KMnO4/H2SO4,oxygen groups at ends/defects,coordination/injection mechanism. TDPA omitted for clarity. Drawn atoms/junction shapes are proposed illustrations,not experimentally measured coordinates or exact site counts.')])
many('si-',1,'SI heading and single original infrared trace','original_figure',[
 ('identity','Heading only says Supplementary Information: Infrared spectrum of oxidized multiwalled nanotubes; no full article title,author list or printed DOI. PDF metadata titleMicrosoft Word-ja035980csi20030625_041651.doc and mainSIdeclaration establish matched identity jointly with filename and content.'),
 ('infrared','Red infrared spectrum of oxidized MWNT precursor,not CdTe hybrid. X in wavenumberscm−1,descending labeled2000,1800,1600,1400,1200,1000,800; y intensityarbitrary units without numerical labels. No fitted peak list,chemical functional-group assignments or calibration provided.'),
 ('limits','SI contains one figure only,no additional recipes,tables,equations,isolated compound structures or references. Original peak/dip shape retained; do not relabel absorbance/transmittance or invent exact peak positions from pixels.')],role='si')
add('source-completeness',9,'Entire main and one-page SI','curation_limit','All9main+1SIpages,8numbered main figures(including conceptualFigure8),one unnumberedSIIRfigure and43numberedreferences fully read/viewed. No table,numbered equation,SAED,CIF,raw arrays,recipe reagentcharges or standalone quantified control protocols supplied.','retain_explicit_missingness')
refs=[
'Dresselhaus, M. S.; Dresselhaus, G.; Avouris, P. Carbon Nanotubes: Synthesis, Structure, Properties, and Applications; Springer-Verlag: New York, 2001.',
'Mitchell, G. P.; Mirkin, C. A.; Letsinger, R. L. J. Am. Chem. Soc. 1999, 121, 8122.',
'Yang, Y.; Huang, S.; He, H.; Mau, A. W. H.; Dai, L. J. Am. Chem. Soc. 1999, 121, 10832.',
'Sano, M.; Kamino, A.; Okamura, J.; Shinkai, S. Nano Lett. 2002, 2, 531.',
'Cassell, A. M.; McCool, G. C.; Ng, H. T.; Koehne, J. E.; Chen, B.; Li, J.; Han, J.; Meyyappan, M. Appl. Phys. Lett. 2003, 82, 817.',
'Zhang, Z.; Wei, B.; Ajayan, P. M. Chem. Commun. 2002, 9, 962.',
'Choi, K. H.; Bourgoin, J. P.; Auvray, S.; Esteve, D.; Duesberg, G. S.; Roth, S.; Burghard, M. Surf. Sci. 2000, 462, 195.',
'Lewenstein, J. C.; Burgin, T. P.; Ribayroi, A.; Nagahara, L. A.; Tsui, R. K. Nano Lett. 2002, 2, 443.',
'Wei, B. Q.; Vajtai, R.; Jung, Y.; Ward, J.; Zhang, R.; Ramanath, G.; Ajayan, P. M. Nature 2002, 416, 495.',
'Avouris, P. Acc. Chem. Res. 2002, 35, 1026.',
'Huynh, W. U.; Dittmer, J. J.; Alivisatos, A. P. Science 2002, 295, 2425.',
'Kong, J.; Franklin, N. R.; Zhou, C.; Chapline, M. G.; Peng, S.; Cho, K.; Dai, H. Science 2000, 287, 622.',
'Hirsch, A. Angew. Chem., Int. Ed. 2002, 41, 1853. Banerjee, S.; Kahn, M. G. C.; Wong, S. S. Chem. Eur. J. 2003, 9, 1898. Two distinct cited works within numbered reference13.',
'Sinnott, S. B. J. Nanosci. Nanotechnol. 2002, 2, 113.',
'Bahr, J.; Tour, J. M. J. Mater. Chem. 2002, 12, 195.',
'Bahr, J. L.; Yang, J.; Kosynkin, D. V.; Broniskowski, M. J.; Smalley, R. E.; Tour, J. M. J. Am. Chem. Soc. 2001, 123, 6536.',
'Georgakilas, V.; Kordatos, K.; Prato, M.; Guldi, D. M.; Holzinger, M.; Hirsch, A. J. Am. Chem. Soc. 2002, 124, 760.',
'Mickelson, E. T.; Huffman, C. B.; Rinzler, A. G.; Smalley, R. E.; Hauge, R. H.; Margrave, J. L. Chem. Phys. Lett. 1998, 296, 188.',
'Chen, R. J.; Zhang, Y.; Wang, D.; Dai, H. J. Am. Chem. Soc. 2001, 123, 3838.',
'Chen, J.; Hamon, M. A.; Hu, H.; Chen, Y.; Rao, A. M.; Eklund, P. C.; Haddon, R. C. Science 1998, 282, 95.',
'O’Connell, M.; Boul, P.; Ericson, L. M.; Huffman, C.; Wang, Y.; Haroz, E.; Kuper, C.; Tour, J.; Ausman, K. D.; Smalley, R. E. Chem. Phys. Lett. 2001, 342, 265.',
'Riggs, J. E.; Guo, Z.; Carroll, D. L.; Sun, Y.-P. J. Am. Chem. Soc. 2000, 122, 5879.',
'Star, A.; Stoddart, J. F.; Steurman, D.; Diehl, M.; Boukai, A.; Wong, E. W.; Yang, X.; Chung, S.-W.; Choi, H.; Heath, J. R. Angew. Chem., Int. Ed. 2001, 40, 1721.',
'Zhang, Y.; Suenaga, K.; Colliex, C.; Iijima, S. Science 1998, 281, 973.',
'Suenaga, K.; Colliex, C.; Demoncy, N.; Loiseau, A.; Pascard, H.; Willaime, F. Science 1997, 278, 653.',
'Zhang, Y.; Ichihashi, T.; Landree, E.; Nihey, F.; Iijima, S. Science 1999, 285, 1719.',
'Hu, J.; Ouyang, M.; Yang, P.; Lieber, C. M. Nature 1999, 399, 48.',
'Banerjee, S.; Wong, S. S. Nano Lett. 2002, 2, 195.',
'Ravindran, S.; Chaudhary, S.; Colburn, B.; Ozkan, M.; Ozkan, C. S. Nano Lett. 2003, 3, 447.',
'Haremza, J. M.; Hahn, M. A.; Krauss, T. D.; Chen, S.; Calcines, J. Nano Lett. 2002, 2, 1253.',
'Azamian, R.; Coleman, K.; Davis, J.; Hanson, N.; Green, M. Chem. Commun. 2002, 366.',
'Banerjee, S.; Wong, S. S. Nano Lett. 2002, 2, 49.',
'Banerjee, S.; Wong, S. S. J. Am. Chem. Soc. 2002, 124, 8940.',
'Frehill, F.; Vos, J. G.; Benrezzak, S.; Koos, A. A.; Konya, Z.; Ruther, M. G.; Blau, W. J.; Fonseca, A.; Nagy, J. B.; Biro, L. P.; Minett, A. I.; in Het Panhuis, M. J. Am. Chem. Soc. 2002, 124, 13694.',
'Hiura, H.; Ebbesen, T. W.; Tanigaki, K. Adv. Mater. (Weinheim, Ger.) 1995, 7, 275. Cited oxidation/purification dependency.',
'Peng, Z. A.; Peng, X. J. Am. Chem. Soc. 2001, 123, 183. Cited one-pot CdO nanocrystal preparation dependency.',
'Peng, Z. A.; Peng, X. J. Am. Chem. Soc. 2002, 124, 3343. Cited modified one-pot CdTe growth and free-crystal context.',
'Ajayan, P. M.; Ebbesen, T. W.; Ichihashi, T.; Iijima, S.; Tanigaki, K.; Hiura, H. Nature 1993, 361, 333.',
'Yao, N.; Lordi, V.; Ma, S. X. C.; Dujardin, E.; Krishnan, A.; Treacy, M. M. J.; Ebbesen, T. W. J. Mater. Res. 1998, 13, 2432.',
'Peng, Z. A.; Peng, X. J. Am. Chem. Soc. 2001, 123, 1389. Cited anisotropic/diffusion-limited growth model.',
'Rolo, A. G.; Vasilevskiy, M. I.; Gaponik, N. P.; Rogach, A. L.; Gomes, M. J. M. Phys. Status Solidi B 2002, 229, 433.',
'Rao, A. M.; Richter, E.; Bandow, S.; Chase, B.; Eklund, P. C.; Williams, K. A.; Fang, S.; Subbaswamy, K. R.; Menon, M.; Thess, A.; Smalley, R. E.; Dresselhaus, G.; Dresselhaus, M. S. Science 1997, 275, 187.',
'Banerjee, S.; Wong, S. S. J. Phys. Chem. B 2002, 106, 12144. Cited improved oxidation/SWNT context.'
]
for n,t in enumerate(refs,1):add(f'reference-{n:02}',1 if n<=22 else 2 if n<=37 else 6 if n<=39 else 7 if n==40 else 8 if n==41 else 9,f'Reference{n}','bibliography',t,'retain_reference_not_independently_read')
for i,uid,scope,prop,v,u in [
 ('hcl-percent','precursor-hcl','MWNT cleaning','stated HCl concentration',35,'%'),('hf-percent','precursor-hf','MWNT cleaning','stated HF concentration',10,'%'),('tube-dry','protocol-wash-dry','Processed MWNT','oven temperature',150,'°C'),('mix-heat','protocol-mix-heat','MWNT/CdO/TDPA/TOPO','preinjection heating temperature',320,'°C'),('inject-t','protocol-injection','Te/TOP injection','temperature',300,'°C'),('growth-t','protocol-growth','Composite growth','temperature',250,'°C'),('growth-time','protocol-growth','Composite growth','duration',20,'min'),('cool-t','protocol-heat-off','Reaction before toluene','cooling target',50,'°C'),('toluene-volume','protocol-dilution','Initial dilution only','toluene added',5,'mL'),('membrane','protocol-filter','Workup membrane','nominal pore size',.2,'µm'),
 ('tem-grid','method-tem-preparation','TEM sample support','Cu grid mesh',300,'mesh'),('tem-voltage','method-tem','PhilipsCM12','accelerating voltage',120,'kV'),('hrtem-voltage','method-hrtem','JEOL2010F','accelerating voltage',200,'kV'),('sem-distance','method-sem','Leo1550','working distance',2,'mm'),('xps-survey-pass','method-xps-survey','XPS survey','pass energy',80,'eV'),('xps-survey-step','method-xps-survey','XPS survey','step',.75,'eV'),('xps-high-pass','method-xps-high-resolution','High-resolution XPS','pass energy',10,'eV'),('xps-high-step','method-xps-high-resolution','High-resolution XPS','step',.1,'eV'),('xrd-wavelength','method-xrd','CuKalpha powderXRD','wavelength',1.54,'Å'),('uvvis-path','method-uvvis-instrument','Quartz cell','path length',10,'mm'),('raman-aperture','method-raman','JascoVentuno','confocal aperture',200,'µm'),('raman-excitation','method-raman','Raman acquisition','diode excitation wavelength',785,'nm'),('raman-power','method-raman','Raman acquisition','laser power',10,'mW'),('cd-binding','xps-cadmium','CompositeCd3d5/2','reported binding energy',405.22,'eV'),('cdte-raman','raman-cdte','Hybrid','LO-type peak',166,'cm−1')]:fact(i,uid,scope,prop,v,u,qualifier='Percent basis unknown.'if i in['hcl-percent','hf-percent']else'')
fact('xps-pressure','method-xps-preparation','XPS chamber','base pressure',5e-9,'torr',approximate=True)
fact('sem-voltage','method-sem','SEM','accelerating voltage range',unit='kV',minimum=2,maximum=10)
fact('high-oxygen','growth-oxygen-high','Highly oxidized precursor MWNT','surface oxygen byXPS',unit='atomic%',minimum=5,maximum=6,approximate=True)
fact('low-oxygen','growth-oxygen-low','Mildly oxidized precursor MWNT','surface oxygen byXPS',unit='atomic%',minimum=1,maximum=2,approximate=True)
fact('bound-length','growth-bound-size','Attached CdTe population','long-axis length',unit='nm',minimum=1,maximum=9)
fact('bound-aspect','growth-bound-size','Attached CdTe population','aspect ratio',unit='ratio',minimum=1,maximum=5)
fact('free-rounded-size','growth-free-size','P7free-washings description','quasi-spherical characteristic size',5,'nm',qualifier='Retain p9 relative heterogeneity discussion; not a measured monodisperse raw distribution.')
fact('no-tube-size','optical-washings','No-nanotube comparator context','quasi-spherical size',5,'nm',approximate=True,qualifier='No complete comparator preparation supplied.')
fact('carboxyl-removal','xps-thermal-carboxyl','Author thermal interpretation','approximate complete-removal temperature',350,'°C',approximate=True,status='author_interpretation',qualifier='Not a separate reported anneal or stability-validation experiment.')
fact('bulk-raman','raman-bulk-reference','Cited bulkCdTe','LO peak reference',170,'cm−1',status='cited_context')
fact('g-band','raman-g-band','Precursor andhybrid','G-mode vicinity',1590,'cm−1',approximate=True)
fact('d-band','raman-d-band','Precursor andhybrid','disorder-mode range',unit='cm−1',minimum=1290,maximum=1320)
fact('argon','precursor-argon','320°C initial heating','atmosphere','Argon')
fact('tdpa','precursor-tdpa','Growth precursor','TDPA ratio descriptor','Substoichiometric',qualifier='No numeric ratio or exact coordination occupancy supplied.')
fact('phase','xrd-phase','CdTe in MWNTcomposite','author phase assignment','Predominantly wurtzite; possible zinc blende and stacking faults',status='author_interpretation')
fact('oxide-label','xps-tellurium','Te3d5/2 assignment','printed surface species','TeO3',status='author_interpretation',qualifier='Literal author attribution; no silent TeO2 substitution.')
for f,values in [(1,[('a',20),('b',125),('c',7),('d',8)]),(2,[('a',100),('b',200),('c',180),('d',75),('e',112)]),(3,[('a',5),('b',20),('c',5),('d',10)]),(4,[('a',20),('b',10),('c',10)])]:
 for panel,nm in values:fact(f'figure{f}{panel}-scale',f'figure-{f}{panel}',f'Figure{f}{panel}','scale bar',nm,'nm')
fact('figure3a-inset-scale','figure-3a','Figure3a different-specimen inset','scale bar',5,'nm')
for i,uid,lo,hi,u in [('xrd-axis','figure-5ii',20,70,'degree2theta'),('uv-axis','figure-7',300,1000,'nm'),('si-axis','si-infrared',800,2000,'cm−1')]:fact(i,uid,'Original plot display','outer labeled ticks',unit=u,minimum=lo,maximum=hi,status='figure_read',qualifier='Labeled tick scope,not necessarily full acquisition span or measured parameter.')
for i,uid,values in [('xps-c','figure-5i-carbon',[295,290,285]),('xps-o','figure-5i-oxygen',[534,532,530,528]),('xps-cd','figure-5i-cadmium',[408,406,404,402]),('xps-te','figure-5i-tellurium',[580,578,576,574,572,570])]:fact(i,uid,'Original XPS plot display','descending labeled binding-energy ticks',values,'eV',status='figure_read')
fact('raman-axis','figure-6','Original Raman display','labeled ticks',[1000,2000,3000,4000],'cm−1',status='figure_read')
fact('eds-axis','figure-4-eds','Original EDS inset','labeled energy ticks',[2,4,6,8,10],'caption eV; unresolved',status='figure_read',qualifier='Do not repair to keV or use these as calibrated peak energies.')
ids=[x['id']for x in U];assert len(ids)==len(set(ids));assert len(refs)==43;assert all(f['source_unit_id']in ids for f in F)
candidates=[]
for path in [S,SI,L,LS]:
 role='si'if'_si_'in path.name else'main';pdf=PdfReader(str(path));tx='\n'.join(p.extract_text()or''for p in pdf.pages);meta=dict(pdf.metadata or{})
 checks={'doi':DOI in tx,'title':'In Situ Quantum Dot Growth' in tx,'byline':'Sarbajit Banerjee'in tx and'Stanislaus S. Wong'in tx,'journal_pages':'10342'in tx and'10350'in tx}if role=='main'else{'spectrum_identity':'Infrared spectrum of oxidized multiwalled nanotubes'in tx,'supplementary_heading':'Supplementary Information'in tx,'metadata_doi_stem':'ja035980c'in str(meta)}
 candidates.append({'path':str(path),'sha256':sha(path),'page_count':len(pdf.pages),'metadata':meta,'content_checks':checks,'role':role,'identical_alias':path in[L,LS]})
assert all(all(x['content_checks'].values())for x in candidates)
assert sha(S)==sha(L)=='24faaec54cea1293bc7951b7d363587e2ec80edaa68d6e90049b5525bc312837';assert sha(SI)==sha(LS)=='0746611853616b5531750d1cd4c610d605c551eec0b3317805c0fcc98fce301e'
pages=[]
for role,n in [('main',9),('si',1)]:
 for p in range(1,n+1):pages.append({'role':role,'pdf_page':p,'printed_page':10341+p if role=='main'else None,'text_path':str(B/f'{role}-{p:02}.txt'),'text_sha256':sha(B/f'{role}-{p:02}.txt'),'image_path':str(B/f'{role}-{p}.png'),'image_sha256':sha(B/f'{role}-{p}.png'),'text_read':True,'actually_visually_inspected':True,'unit_count':sum(u['pdf_page']==p and u['source_role']==role for u in U)})
identity={'status':'passed_local_main_and_SI_identity','source_id':SID,'doi':DOI,'title':'In Situ Quantum Dot Growth on Multiwalled Carbon Nanotubes','authors':['Sarbajit Banerjee','Stanislaus S. Wong'],'journal':'Journal of the American Chemical Society','year':2003,'volume':125,'issue':34,'pages':'10342–10350','received':'2003-05-06','published_online':'2003-07-31','source_sha256':sha(S),'si_sha256':sha(SI),'page_count':9,'si_page_count':1,'candidates':candidates,'supporting_information':{'status':'matched_and_fully_reviewed','matched_unique_count':1,'matched_local_copy_count':2,'main_declaration':'Infrared spectrum of oxidized multiwalled nanotubes (PDF).','evidence':['Exact mainSI declaration matches standalone SI heading and precursor spectrum.','SI PDF metadata Title embeds ja035980csi20030625_041651.doc.','Incoming and legacy SI filenames shareDOI; bothcopyhashes are identical.'],'limitations':['SI has no full article title/byline/printedDOI; matching rests on combined declaration/content/metadata/filename,not filename alone.','Bounded rg filename search in both collections using ja035980c|quantum.dot.growth|banerjee.*wong,then full candidate metadata/content/hash checks. Not exhaustive unrelatedPDFcontent search.']},'independent_visual_identity':True}
conflicts=['All reagent masses,Te/TOPstock concentration/injectionvolume and numericCd:TDPA:MWNT ratios are absent. Referenced purification/growth papers were not downloaded or silently merged.','35%HCl and10%HF have no stated percent basis. Heating320°C,injection300°C,growth250°C20min,cooling50°C and150°C precursor drying are distinct stages.','Argon is explicit for initial320°C heating. Later atmosphere is contextual/inherited,not a separately measured condition; XPSvacuum is analytical only.','Free washed-away crystals described p7 as relatively monodisperse/quasi-spherical5nm,whilep9 describes less monodispersity than no-tube~5nm reference. Preserve comparison/scopes and no invented distribution.','AttachedCdTe longaxis1–9nm/aspect1–5 must not become mean diameter or size of freewashing controls.','TeO3 is the literal authorXPS surface-oxide assignment; identity is not silently repaired toTeO2.','Figure4EDS caption calls energy eV although numeric0–10scale implies possibleunitproblem; no in-plotunit. Preserve source and mark unresolved,do not convert or reconstructpeakpositions.','Authors reportEDSP; original inset labelsC,O,Cu,Cd,Te but noPpeaklabel. Cu grid/support is not proofCu incorporation; no quantitativeEDSstoichiometry.','Wurtzite predominant with possiblezincblende/stackingfaults and overlappingXRDpeaks; no phasefractions,uniquepolymorphCIF or refinedinterface coordinates.','XPS5–6at%O high-oxidized and1–2at%O mild precursor cohorts are incompletely specified controls,not completealternate recipes.','Raman166cm−1 iscurrenthybrid;170cm−1 ispriorbulkreference. No exactCdTe exciton resolved in hybridUV-visible.','SI IR belongs to oxidizedMWNTprecursor only; no exact unlabelled peak positions/functionalgroupassignments invented.','Figure8 is a conceptualchemical-growtharchitecture with TDPA omitted,not measuredlatticeor atomisticinterface.','NoSAED,rawarrays,tables,numberedequations,currentelectricaltransport,photovoltaicmetrics,PLquantumyield or opticalemission spectra supplied.']
report={'status':'complete_supplied_main_and_SI_text_and_visual_inventory','source_id':SID,'doi':DOI,'source_sha256':sha(S),'si_sha256':sha(SI),'audited_utc':datetime.now(timezone.utc).isoformat(),'scope':'Independent full nine-main-plus-one-SI text and actual original-page visual review,allmethods,results,eightnumberedmainfigures,SIIR,all43numberedreferences(includingtwo works inref13),acknowledgments and sourceidentity.','units':U,'unit_count':len(U),'unit_kind_counts':dict(Counter(x['kind']for x in U)),'typed_anchor_count':len(F),'page_coverage':pages,'figure_count':8,'si_figure_count':1,'table_count':0,'numbered_equation_count':0,'references_and_notes_count':43,'source_conflicts_and_limits':conflicts,'site_mutated':False,'downloaded_sources':False}
write('source-audit.json',report);write('source-facts.json',{'source_id':SID,'source_sha256':sha(S),'si_sha256':sha(SI),'scope':'Source-native quantities,categorical values and explicitly figure-read labels; not automatic trainingexamples.','facts':F});write('source-identity.json',identity);write('independent-page-coverage.json',{'source_id':SID,'source_sha256':sha(S),'si_sha256':sha(SI),'pages':pages,'source_detail_images_actually_viewed':['source-detail-eds.png','source-detail-xps-xrd.png']})
(B/'source-audit.md').write_text('# Banerjee and Wong2003 independent source audit\n\nAll9main+1SIpages fully read and visually inspected. '+str(len(U))+' granular units and '+str(len(F))+' typedanchors cover8numberedfigures,oneSIIRfigure and43numberedreferences.\n\n'+'\n'.join('- '+x for x in conflicts)+'\n\nNoSite/monitor edits or downloads.\n',encoding='utf8')
(B/'source-identity.md').write_text('# Banerjee and Wong2003 source identity\n\nVerified main DOI,title,authors,journal,dates and9pages; exact main hash`'+sha(S)+'`. SI hash`'+sha(SI)+'`,onepage.\n\nMainSI declaration and exactSIheading/content match. SI metadata embedsja035980c despite absence of fullarticleidentity on standalonepage. Eachhasoneidenticallegacyalias. Boundedlocalfilename/candidate-contentsearch only,no downloads.\n',encoding='utf8')
print(json.dumps({'source_units':len(U),'typed_anchors':len(F),'source_audit_sha256':sha(B/'source-audit.json'),'source_identity_sha256':sha(B/'source-identity.json')},ensure_ascii=False))

