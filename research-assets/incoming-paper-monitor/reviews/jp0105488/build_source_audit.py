"""Independent complete main-article inventory; no Site/queue mutation."""
import json, hashlib, datetime
from pathlib import Path
B=Path(__file__).parent
S=Path(r'[local path redacted]')
L=Path(r'[local path redacted]')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
U=[]
def add(key,page,loc,kind,claim,disposition='retain_source_linked_evidence',**extra):
    uid='gerion2001-'+key
    U.append(dict(id=uid,source_unit_id=uid,source_role='main',pdf_page=page,printed_page=8860+page,locator=loc,kind=kind,claim=claim,disposition=disposition,**extra))
def block(prefix,page,loc,kind,rows,disposition='retain_source_linked_evidence'):
    for key,text in rows:add(prefix+'-'+key,page,loc,kind,text,disposition)

block('identity',1,'Title/byline/banner/footer','identity',[
('title','Synthesis and Properties of Biocompatible Water-Soluble Silica-Coated CdSe/ZnS Semiconductor Quantum Dots. DOI 10.1021/jp0105488 is printed in the page footer.'),
('authors','Daniele Gerion, Fabien Pinaud, Shara C. Williams, Wolfgang J. Parak, Daniela Zanchet, Shimon Weiss, A. Paul Alivisatos. Affiliations: UC Berkeley Chemistry and Lawrence Berkeley Laboratory Materials Science Division.'),
('journal','J. Phys. Chem. B 2001, 105, 8861–8871, issue 37. Eleven consecutive main-article pages, including References and Notes.'),
('dates','Received February 12, 2001; final form April 17, 2001; published on Web June 5, 2001. July 6, 2026 institutional download watermark is not publication/experiment date.'),
('administrative','Part of Royce W. Murray Festschrift; corresponding author Gerion and Alivisatos email supplied. Correspondence, affiliation marks, copyright and download-sharing notice are administrative, not synthesis parameters.')], 'retain_identity_or_administrative_context')
block('abstract',1,'Abstract','study_summary',[
('architecture','Hydrophobic CdSe/ZnS core/shell nanocrystals with CdSe core sizes 2–5 nm are embedded in a siloxane shell with thiol and/or amine functionality. This is a multicomponent coated particle, not a homogeneous CdSe crystal.'),
('size','AFM-based siloxane shell thickness 1–5 nm and overall sizes 6–17 nm are study-wide results with interpretation limits discussed later.'),
('optics','Emission widths 32–35 nm fwhm, blue-to-red tunability and quantum yields up to 18% are reported; quantum yield depends mainly on starting core/shell particles.'),
('stability','Enhanced photochemical stability over organic fluorophores and buffer stability at physiological salt concentrations >150 mM NaCl are study summaries, not universal guarantees.'),
('bioconjugation','Surface functional groups are intended to permit biological conjugation; a biological-conjugation synthesis or efficacy assay is not supplied by this abstract.')])
block('context',1,'Introduction','cited_context',[
('size-control','Prior wet chemistry yields luminescent semiconductor nanocrystals about 1.5–8 nm, with size/shape control cited to references 1–4; assemblies/material applications cite 5–8.'),
('confinement','Size-dependent confinement shifts absorption onset/emission to higher energy with decreasing size; continuum absorption and narrow symmetric excitation-independent emission motivate multiplexing; references 2,9,10.'),
('passivation','Higher-band-gap shell passivation can raise prior nanocrystal quantum yields to 50–70% and improve photostability; references 11–13. These are not QYs measured for current silanized specimens.'),
('dye-limits','Organic dye narrow absorption, overlapping emission, environmental dependence and photobleaching are contextual limitations; refs14–16. Dye lifetime <5 ns is contextual.'),
('lifetime','Semiconductor emission decay of roughly30–100 ns at room temperature, refs17/18, motivates time-gated detection; no current time-resolved decay measurement is supplied.'),
('aqueous-alternatives','Earlier aqueous syntheses yield broad trapped-state emission; thiolated carboxyl-bearing primers can solubilize hydrophobic particles but dynamic ligand exchange/dissolution motivates robust encapsulation; refs14,15,19–22.')], 'retain_context_without_new_recipe')
block('context',2,'Introduction continuation','study_scope',[
('prior-silica','Authors previously reported polymerized silica encapsulation (ref14); present method is given in detail and compared with MPA coating.'),
('shell-range','Introduction describes shell about2–5nm, distinct from abstract/discussion1–5nm summary. Stable buffers up to200mM and stronger stability than MPA are contextual study summaries; preserve each scope.')])

block('chemical',2,'Experimental A: Chemicals and Materials','chemical_inventory',[
('topo','Trioctylphosphine oxide (TOPO), Sigma-Aldrich #346187; original particle ligand/storage mixture component. Do not infer a pure-solvent volume from a butanol/TOPO mixture.'),
('mps','Mercaptopropyltris(methyloxy)silane (MPS), Sigma-Aldrich #175617; later called trimethoxysilane. Purchased methoxy precursor differs from hydrolyzed silanol form drawn in Figure1.'),
('aps','Aminopropyltris(methyloxy)silane (APS), Sigma-Aldrich #281778; successful optional addition after priming is distinct from unsuccessful APS-only priming. No APS amount specified.'),
('tmah-solution','Tetramethylammonium hydroxide in methanol (TMAH), Sigma-Aldrich #334901. Solution concentration is not reported. Discussion says minute water amount <5%; do not import catalog concentration.'),
('tmah-hydrate','Tetramethylammonium hydroxide pentahydrate, Sigma-Aldrich #223212; solid ~3g belongs to chlorotrimethylsilane quenching mixture, separate from methanolic base additions.'),
('phosphonate','(Trihydroxysilyl)propyl methylphosphonate in water, 42% wt/wt, Sigma-Aldrich #435716. Figure1 depicts propyl–P(=O)(O−)–CH3, whereas the name says methylphosphonate. Preserve the named reagent and drawn connectivity as source-specific representations; do not silently impose P–O–CH3, a counterion, a unique stock formula or computed geometry.'),
('chlorotrimethylsilane','Chlorotrimethylsilane, Sigma-Aldrich #386529; quenching reagent. Do not portray it as a cooling solvent or chemically identical to hydrolyzed MPS.'),
('mpa','Mercaptopropionic acid (MPA), Sigma-Aldrich #M5801; procedure specifies3-mercaptopropionic acid. Surface thiol binding and outward carboxyl functionality are distinct roles.'),
('dmap','4-(Dimethylamino)pyridine (DMAP), Sigma-Aldrich #D5640; materials spelling prints pridine, procedure gives pyridine. Used as a DMF solution; no reagent purity reported.'),
('dtnb','5,5′-Dithiobis(2-nitrobenzoic acid), DTNB, Sigma-Aldrich; Ellman assay reagent, not a synthesis additive.'),
('methanol','Anhydrous methanol used for initial precipitation and silanization dilution; subsequent methanol additions/dialysis specified without supplier or purity. Precipitating methanol volume absent.'),
('butanol','Butanol/TOPO starting-particle storage mixture with approximate volume ratio1/2; butanol isomer is unreported.'),
('dmf','N,N-Dimethylformamide, DMF, used for MPA exchange and DMAP stock; supplier/purity not reported.'),
('water','18MΩ Millipore water, as source reports resistance without an explicit cm basis; used in coating, redispersion, chromatography/dialysis and analysis.'),
('nitrogen','Nitrogen atmosphere/flow explicitly applies to silanization stages and specified drying steps. Gas purity/flow and pressure are unreported.'),
('optical-solvents','Toluene is the optical core/shell comparison solvent; toluene, chloroform or water are TEM-deposition alternatives. No new colloidal synthesis from these solvents is supplied.'),
('rhodamine','Rhodamine6G in water is the QY/photobleaching reference with cited QY95%; no source-specific supplier/concentration in molarity supplied.'),
('glycerin','30%wt/wt glycerin in buffer is a gel-loading additive;20µL particle sample mixed with4µL of this stock. Agarose and glycerin are analytical materials, not shell precursors.'),
('buffers','PB is K2HPO4/KH2PO4 mixture (#P8709/#P8584); MES is2-(N-morpholino)ethanesulfonic acid(#M5287);0.5×TBE is Tris–Borate–EDTA(#T3913), all Sigma-Aldrich. Salt ionic strength adjusted with calibrated NaCl; exact component recipes absent.')])
block('hardware',2,'Experimental A/B','equipment_or_support',[
('dialysis','MWCO10000 tubing #D9652, Sigma-Aldrich; Slide-A-Lyzer cassettes #66810 Pierce. MWCO is membrane cutoff, not actual nanoparticle molecular mass.'),
('sephadex','SephadexG25 medium #G2580 Sigma-Aldrich and NAP columns #17-0852-01 Amersham Pharmacia. Homemade exchange column dimensions are given separately.'),
('filters','Pall Gelman Acrodisc nylon #PN4428T: materials list prints0.45mm, while method specifies0.45µm. Preserve contradictory source units rather than silently converting.'),
('ultrafiltration','YM-100 Centrip(l)us/Centricon100, Millipore, MWCO100000; device names vary in source. This concentration/removal step is not the same as the final20000×g pelleting of unwanted material.'),
('evaporators','Buchi Re111 rotary evaporator; optional Eppendorf vacufuge #5301 at60°C. Discussion also permits a Schlenk line for solvent evaporation without its detailed conditions.')])

block('upstream',2,'Experimental B: initial CdSe/ZnS particles','upstream_scope',[
('preparation','CdSe/ZnS core/shell particles were prepared in TOPO by references1,11–13. The present paper does not reproduce CdSe core or ZnS shell precursor amounts, injection conditions or growth programs; retain a cited upstream dependency.'),
('storage','Store at room temperature in butanol/TOPO ~1/2 by volume, typical5–10mg CdSe cores per mL of solution; stable for months, no special oxidation precautions. Mass basis is CdSe cores, not total capped CdSe/ZnS particle mass.'),
('aged','Discussion p8869 states aged starting CdSe/ZnS samples were used throughout, without storage precautions; improved QY with fresh/double-shell particles is an outlook, not a tested optimized route here.')])

block('silica-step',2,'Experimental B: Silica-Coated Nanocrystals','operation_or_condition',[
('scope','Typical quantities are scalable and said to apply to CdSe/ZnS particles ~2–8nm. This procedural applicability range is distinct from actual Table2 CdSe-core and core/shell sizes.'),
('precipitate','Start1mL nanocrystals in butanol/TOPO, OD~2; precipitate with anhydrous methanol. Keep wet precipitate; methanol amount and separation settings absent.'),
('mps-exchange','Dissolve wet precipitate in50µL pure MPS; vortex; then add5µL TMAH in methanol. Solution becomes optically clear. No vortex duration or TMAH stock concentration.'),
('dilute','Dilute with120mL anhydrous methanol basified to pH~10 using750µL methanolic TMAH; put underN2 in500mL three-neck flask. Flask capacity differs from solvent amount.'),
('stir-primary','Mildly stir1h. Stirring speed and numeric room temperature are not given.'),
('heat-primary','Gently heat to~60°C for30min, then cool to room temperature. Heating/cooling rates and bath hardware not specified.'),
('outer-add','Add90mL methanol,10mL18MΩ water,600µL42%wt/wt aqueous (trihydroxysilyl)propyl methylphosphonate and20µL MPS. Keep separate solute/solvent stock composition; no invented molar concentration or isolated shell stoichiometry.'),
('outer-stir','Stir~2h after outer-shell additions.'),
('outer-heat','Heat to~60°C for less than5min and cool to~30°C. Preserve strict upper time bound; do not assign exactly5min.'),
('quench-mixture','Quench remaining silanol groups with mixture20mL methanol+2mL chlorotrimethylsilane basified with~3g solid TMAH pentahydrate. No final pH supplied for this quench mixture.'),
('quench-stir','After quench addition stir again~2h.'),
('quench-heat','Heat to~60°C for~30min, then leave at room temperature2–4days while stirring inN2. Do not replace the extended equilibration by a short generic cooling step.'),
('rotavap','Condense by factor2–5 in Re111 rotary evaporator, then leave24h. Discussion later specifies factor<4 and underN2; retain source conflict rather than intersecting into a new prescribed range.'),
('methanol-dialysis','Dialyze in10000MWCO tubing against methanol for1day, then pass through0.45µm nylon syringe filter.'),
('centrifugal-concentrator','Remove excess free silane using YM-100 Centrip(l)us/Centricon100 devices, MWCO100000; reduce volume to~2mL. Speed/time for these devices absent; do not transfer final20000×g/30min to this step.'),
('wait-before-exchange','Leave methanolic concentrated silanized solution at least12h before solvent-exchange column. Discussion places a~12h rest between rotary and centrifugal concentration; retain differing stage assignments.'),
('column','Exchange solvent with either commercial NAP or homemade20cm-long,0.7cm-diameter column filled with~5g SephadexG25 medium, equilibrated with10mMPB pH~7.'),
('collect','Monitor elution by fluorescence and collect only fluorescent fraction, ~3mL; leave a few hours, then filter through0.22µm acetate filter. Do not portray all eluate or discarded complexes as product.'),
('optional-water-dialysis','Optional further dialysis against18MΩ water1–4days in10000MWCO membrane; source then prints0.22mm filter, in conflict with preceding0.22µm; concentrate to desired concentration in vacufuge at60°C. No desired scalar concentration given.'),
('final-centrifuge','As last step centrifuge20000×g for30min; discard precipitate and retain supernatant. Relative centrifugal force is not rpm.'),
('final-storage','Store supernatant in air, typicalOD~0.3–1 at absorption feature, corresponding to3–10µM using assumed extinction coefficient10^5M−1cm−1. Path-length assumption for this concentration conversion is not supplied; keep source conversion and basis.'),
('missing','No isolated yield, direct shell composition/phase, quantitative pressure, stirring rpm, thermal ramps, base molarity, APS quantity, original wet-pellet separation settings, ultrafiltration speed/time, wash-cycle count or biological-conjugation procedure is given.')])
block('mpa-step',2,'Experimental B: MPA-Coated Nanocrystals; continuation p8863','operation_or_condition',[
('scope','MPA coating follows refs21/22 but a local ligand-exchange procedure is provided; it is an alternative coating route using starting CdSe/ZnS, not a later mandatory stage of silica coating.'),
('precipitate','1mL CdSe/ZnS in butanol/TOPO,OD~2, precipitated using anhydrous methanol; retain wet precipitate, methanol quantity/separation conditions absent.'),
('resuspend','Resuspend wet precipitate in1mL DMF+0.1mL3-mercaptopropionic acid.'),
('mix','Vortex and sonicate~10–30min until transparent; sonication power/frequency and vortex settings absent.'),
('age','Store solution1–4days at room temperature.'),
('dmap-stock','Add~3–7mL DMAP solution in DMF, prepared at~20mg DMAP in1mL DMF. The stock concentration does not describe final exchange-mixture concentration.'),
('separate','Cloudy mixture centrifuged1h at3000×g. Discard supernatant and retain precipitate.'),
('dry-redissolve','Dry retained precipitate under nitrogen; dissolve in0.1–1mL18MΩ water. No drying time/temperature specified.'),
('clarify','Centrifuge30min at20000×g and use only supernatant for experiments.'),
('optional-purify','When necessary remove excessMPA using NAP column pre-equilibrated with18MΩ water. No obligatory dialysis or repeated column count.'),
('buffer-exchange','For buffer experiments, change water to desired buffer using NAP column,10000MWCO dialysis, or direct concentrated-buffer addition. These are alternatives, not three successive steps.')])

block('figure1',3,'Figure1 drawing and caption','mechanism_schematic',[
('scope','Silanization drawing is a conceptual chemical mechanism, not atomic coordinates or measured shell geometry. MPS deliberately drawn hydrolyzed for convenience even though starting reagent is trimethoxy.'),
('exchange','TOPO-capped CdSe/ZnS dissolved in pureMPS; basification promotes surface replacement ofTOPO. Si–OCH3 groups hydrolyze to Si–OH, forming primary polymerization layer.'),
('condensation','Heating strengthens silanol bridges into siloxane bonds and releases water. Figure depicts successive shell growth, not different experimental temperatures.'),
('functionalization','Fresh silane precursors add functionality F=–SH,–NH2,–PO(O−)CH3. Functionalization may be varied; APS is optional and not quantified in standard recipe.'),
('termination','Final step not drawn converts remaining hydroxyl functionality to methyl-bearing groups and blocks further silica growth. Preserve explanatory source wording without treating it as measured surface coverage.')])
block('optical-method',3,'Experimental C: Photophysical Characterization','measurement_method',[
('absorption','UV–vis absorption with HP8453 diode-array spectrometer. Core/shell,silanized andMPA solutions in2mm-path quartz cuvette.'),
('emission','Fluorescence using Spex1681,0.22m/0.34m spectrometer. Slit widths, detector response correction and spectral integration bounds absent.'),
('qy','Room-temperature QY: integrated emission of silica particles in10mMPB compared to rhodamine6G inwater,QY95%(ref24), identicalOD0.15 at480nm excitation. No new absolute photon-counting assay asserted.'),
('storage-stability','1mL diluted silica particles in10mMPB,OD0.01 at exciton peak, excitation340nm; four subsequent measurements of integrated fluorescence, mean peak area normalized to day1.'),
('cw-sample','For continuous-laser test: thin quartz cuvette,1µL silica-particle or dye solution, identicalOD0.065 at488nm. This analytical sample is not the synthesis batch volume.'),
('cw-excitation','Zeiss AxiovertS100TV epifluorescence microscope;488nm CWAr+laser,0.5mW,focused spot700µm. Spot definition/shape absent; do not convert to irradiance.'),
('cw-acquisition','Integrated fluorescence of~10µm×10µm region recorded over4h at5s intervals and normalized to initial value. Figure4 shows only0–4000s plotted range; preserve separately.')])
block('size-method',3,'Experimental D: Size Characterization','measurement_method',[
('tem','HRTEM either TopconEM002B at200keV orJEM-3010ARP at300keV. Preserve source energy notation; no unreported magnification/lattice parameters.'),
('tem-specimen','Spread~5–10µL nanocrystals in toluene,chloroform orwater,OD~0.3,on ultrathin carbon-coated grid and dryinair.'),
('tem-analysis','GatanMSC794CCD or later digitized images; particle diameter via standard image-processing software, unspecified packages. No exact per-TEM-sample count supplied.'),
('eels','EELS TEM-CM200FEG;~10µL silanized sample on400mesh carbon-coated grid,dryovernight. Spectra atSi edge110eV andSe edge67eV; edge energies not measured particle dimensions.'),
('afm-deposit','~10µL water-soluble particles on freshly cleaved mica,incubate10min,gently rinse3dropswater,dryunderN2flow. AFM samples are deposited/dried, not measured in liquid.'),
('afm-acquire','Tapping-mode AFM inair using MultiMode andTESPcantilevers(DigitalInstrument). Particle height measured; all features counted in initial histograms,morethan500dots per sample.'),
('afm-selection','Published Figure5 histograms selectively omit small features per caption/Note27. Initial all-features-counted statement does not establish published histograms are unfiltered raw counts.')])
block('hplc-method',4,'Experimental D continuation','measurement_method',[
('column','30cm size-exclusion column G4000-SWxl,TSK-gel,Supelco; silica-phase7µm beads with45nm pores. Bead/pore dimensions are hardware, not product dimensions.'),
('load','20µL silanized aliquot in10mMPB,OD~0.1,eluted0.5mL/min in10mMPB+50mMNaCl,pH~7.'),
('detect','Eluate monitored by210nm absorption versus time. UV peak area is not directly particle count or mass fraction; no fluorescence detector simultaneous with the trace is claimed.')])
block('surface-method',4,'Experimental E: Surface Characterization and Solubility','measurement_method',[
('ellman-add','AddDTNB to particles in50mMPB,pH7.3,finalDTNB1–10mM; incubate2h atroomtemperature.'),
('ellman-control','Compare absorbance ofDTNB-treated solution to similar particle solution withoutDTNB. Particle concentration from exciton absorbance using assumed100000M−1cm−1 extinction coefficient.'),
('ellman-thiols','Free-thiol concentration derived from412nm absorbance difference using13600M−1cm−1 coefficient attributed in source toDTNB. This is an assay calculation, not a directly measured ligand count.'),
('gel-system','BioRadSub-CellGTagarose electrophoresis;1–3%agarose inPBpH~7,MESpH~5.5,or0.5×TBEpH~8.6.'),
('gel-load','Mix20µL nanoparticle sample+4µL30%wt/wt glycerin inbuffer;brieflyvortexandloadwells.'),
('gel-run','Typical50–100V,3.3–6.7V/cm,30–120min. These general ranges differ from specific Figure7 panels; do not overwrite panel-specific conditions.'),
('gel-detect','Illuminate with2020EUV/White transilluminator(Stratagene); recordCCDfluorescence withEagleEyeIIsoftware. No calibrated band charge or absolute mobility supplied.'),
('salt-series','NaCl in30mMPB:1000,500,200,100,50,20,10,5,1,0mM listed;incubate5h then run1%agarose in30mMPBwithoutNaCl. Figure7also includes2mM lane absent from this list.'),
('band-selection','Electrophoresis selects narrow size-to-charge bands using ref26step-by-step method; band narrowing inTBE. Filter-paper extraction details are cited rather than reproduced.')])

block('table1',4,'Table1 and footnote','tabulated_observation',[
('blue','Blue: emission504nm; absorption peak not distinct, hence absorption/QY/relativeQY not determined. Missing values are not zeros.'),
('green','Green: absorption522nm,emission544nm,QY18%,QYrelative toCdSe/ZnS81%.'),
('yellow','Yellow: absorption560nm,emission576nm,QY12%,relativeQY66%.'),
('orange','Orange: absorption576nm,emission595nm,QY9%,relativeQY60%.'),
('red','Red: absorption620nm,emission644nm,QY5%,relativeQY71%.'),
('scope','Optical color cohorts are reported for silica-coated particles; starting-particle relativeQY is a comparison. Table1 alone does not join its specimens to Table2 structural cohorts or define one independently reproduced synthesis batch per row.')])
block('optical-result',4,'Results A and Figure2','measurement_or_interpretation',[
('spectrum-invariance','Silica shell changes absorption little from450–720nm; emission remains symmetric without dye-like redtail. Source gives~32nmfwhm and~20nm globalStokes shifts.'),
('redshift','Silanized aqueous emission redshifts1–2nm comparedwithsame original samples intoluene. This matched comparison differs from unjustified joins between different characterization tables.'),
('body-peaks-conflict','Body givesgreen542nm,yellow572nm,orange595nm,red644nm withQYs18,12,9,5%; Table1 gives544/576forgreen/yellow. Retain both locators; do not silently replace or average.'),
('qy-variation','ExactQY varies slightly across silanization syntheses fromsameCdSe/ZnS; typicalretention~60–80% ofstartingQY. Tablegreen81% is independently preserved.'),
('month-stability','ReportedQY decrease~1–5% inone month in10mMPB; threecolors tested. Figure3reports normalizedfluorescence rather than a newabsoluteQYassay perday.'),
('ph-stability','No noticeableQY variation for6<pH<8 over1day. Preserve strictpHlimits; this is not proof of stability at everypH/saltcombination.')])
block('figure2',4,'Figure2 upper/lower panels, inset and caption','original_figure',[
('axes','Upperrelativeabsorption andlowernormalizedintensity versuswavelength; labeledx480–720nm,uppery0–1.6arb.units,lowery0–1.0arb.units. Normalization is for display; traces not digitized.'),
('colors','Right-to-left red,orange,yellow,green,blue emission;blueabsorption omitted because nofeaturesabove450nm. Captioncalls10mMPBS pH~7 whilebody/methods usePB; do not infer unreported salinecomposition.'),
('inset','Insetcompares samegreenCdSe/ZnS beforecoatingintoluene(dashed)andaftercoatingin10mMPB(solid),absorption+emission. Shapeillustratespairedopticalcomparison,notatomicstructure.')])
block('figure3',5,'Figure3 and caption','original_figure',[
('axes','Threepanelsgreen544nm,orange595nm,red644nm;day0–30 versusrelativefluorescenceintensity,withpoints/errorbarsandlines. Errorbartype notspecified; no newexactday-by-dayvalues extracted.'),
('scope','Caption says particles in10mMPB excitedeachday; fluorescence stableovermonth. Methodfourconsecutivemeasurements perobservation andday1normalization retained; these are longitudinal observations, not30synthesisreplicates.')])
block('figure4',5,'Figure4 and Results A continuation','original_figure',[
('axes','Normalizedintensityy0–2.0 versustimex0–4000s. Coloreddottraces,blackrhodamine6G; colorcorrespondstoemission but plottedtraceidentities are notfullykeyed by exactwavelength.'),
('conditions','Caption0.5mW,700µmspot,~1µL,OD0.065at488nm,CWAr+;particlesstableatleast~4h,dyephotobleachesafter~10min. Plotends4000s, not14400s; reportedexperimentdurationanddisplayedextent remain distinct.'),
('brightening','Textemission initiallyrises andlevels at120–200% initialintensity. Not a uniformmonotoniccurve or exactfactorassignedtoeverycolor.')])
block('size-result',5,'Results B','measurement_or_interpretation',[
('paired-design','SystematicTEM/AFM comparesstartingcore/shelland silica/MPAcoatings preparedfromsame starting sample; Figure5 explicit yellowpair. Does not establishalloptical/stability assays use identicalbatches.'),
('tem-green','Greencore/shell diameter4.2(0.5)nm; sourceparenthesiswidth parameter notexplicitlydefined asSEM/SD here, do not invent errorstatistic.'),
('tem-yellow','Yellowcore/shell4.4(0.4)nm; narrow TEMdistribution illustratedFigure5.'),
('tem-red','Redcore/shell5.6(0.4)nm.'),
('tem-darkred','Darkredcore/shell6.4(0.4)nm; source statesroughlyconstantdistributionwidth acrosscolors.'),
('silica-hrtem','Amorphousshell difficulttoimageagainstultrathincarbon; smallcore/shell<7nm andproposedthinporoussilica. A particleonlaceycarbonedge shows~3nmamorphouscoating, but imageis referredtoSI notpresentinmain.'),
('eels','EELSnotshown; preliminarySe-richcenterandSi-richsurroundingzone, but size/shape/homogeneitynotunambiguouslyidentified. No fabricatedEELSimage,elementmaporquantitativecomposition.'),
('silica-peaks','Silica AFM shows a first peak ~4 nm independent of starting size; second peak ~6,9,14,17 nm for green,yellow,red,dark red. The small peak chemical identity is interpretive.'),
('height-increase','Secondpeakheightincreases~2,4,8,10nm overcorrespondingcore/shell. PeakbroaderthanTEM;heights>20nmrare. These arecohortheights,notpreciseisolatedsingleparticlesizes.'),
('mpa-peaks','MPAAFMsinglebroadpeak~5,5,9,12nm forgreen,yellow,red,darkred;abovebarecore/shellandbelowsilicasecondpeak.'),
('aggregation-limit','AFM alonecannotestablishsolutionaggregation; driedmicaspecimens andpossiblemultiplecores must remain explicit.')])
block('figure5',6,'Figure5 and caption','original_figure',[
('axes','Yellowcohort:topplainTEM, middlesilanizedAFM,bottomMPAAFM; xdiameter[nm]0–20 for all, yFrequency(topto30,middle60,bottom70). AFMmeasurement isheightdespiteaxislabeldiameter.'),
('sample-links','SilicaandMPApreparedfromsameyellowCdSe/ZnSsample;TEMbaselineandheightdistributions canbespecificallycomparedwithinthiscohort.'),
('selection-conflict','CaptionclaimsAFMfeaturesbelowcorrespondingcore/shelldiameteromitted;Note27saysprominent0.5–2nmpeakomitted. YetvisibleAFM~3–4nmfeaturesliebelowyellow4.4nmTEMdiameter; preserveimageandreportedrulewithoutassertinguniformcutoff.')])
block('table2',6,'Table2 and footnote','tabulated_observation',[
('green','Green:CdSecoreTEM2.7nm;CdSe/ZnSTEM4.2nm;silicaAFM6nm;MPAAFM5nm.'),
('yellow','Yellow:CdSecore3.1nm;core/shell4.4nm;silicaAFM9nm;MPAAFM5nm.'),
('red','Red:CdSecore4.1nm;core/shell5.6nm;silicaAFM14nm;MPAAFM9nm.'),
('darkred','Darkred:CdSecore4.8nm;core/shell6.4nm;silicaAFM17nm;MPAAFM12nm.'),
('footnote','ShellthicknessdefinedashalfthedifferencebetweenCdSe/ZnSdiameterandsilica-coatedparticleapparentdiameter/height. Modelinterpretationrequiresaggregation/AFMlimitations; notdirectatomicresolvedshellmeasurement.')])
block('figure6',6,'Figure6, caption and Results B','original_figure_or_observation',[
('axes','Absorption210nmchromatogramversustimewithx0–25minlabeled;verticalamplitudeunit/scale notgiven. Blue/redrefer to two preparations, bothstartinggreennanocrystals, notblue/redemission.'),
('standard-void','Standardbluecurvevoidpeak~13min,~8%totalelutionarea,objects largerthan45nmpores; thisarea isnotprovenparticlecountfraction.'),
('standard-dots','Standardbluefeature~15min,~49%area,greenfluorescenceunderUV indicatesnanocrystals. Fractionscollectedseparatelyandexaminedinepifluorescencemicroscope.'),
('standard-complexes','Standardbluefeature~21min,~43%area,nonfluorescent;authorassignstosilicacomplexes tentatively.'),
('purified','Redcurve:distinctsilanizationsynthesisusingsamestartinggreencohort,purifiedbyMWCO100000dialysisandrepeatedNAP10size-exclusionpasses;onepeak,reducedsilicaandnocolloidsinvoid. Do not silentlyreplacestandardMWCO10000dialysis orinventcyclecount.'),
('inset','R/Bsampleshavealmostsame1%agarosemigrationpattern:10mMPB,pH7.2,40min,50V,dashedloadingline,5mmscalebar. ElectrophoresisdoesnotdistinguishimpurityprofilesseeninHPLC.')])
block('surface-result',6,'Results C','measurement_or_interpretation',[
('thiol-count','Ellmantestreproduciblyyieldseveralhundredactivethiolsperparticle;upperestimatebecausefreesilicacomplexesalsoreactandparticleconcentrationapproximate. Noexactintegerorligandcoverageperarea supplied.'),
('thiol-time','Apparentactivethiolnumberdoesnotvaryover1month. Noindividualtime-seriesvaluesgiven.'),
('charge','Negativephosphonategroupsconsistentwithmigrationtowardpositiveelectrode;charge inferredqualitatively,notmeasuredzetapotential or absolutecharge.')])
block('figure7',7,'Figure7 panels/caption and Results C','original_figure_or_measurement',[
('a-conditions','Panelsa1/a2:green,yellow,red;pairedMPA/silicalanes;1%agarose,1h,75V;10mMMESpH5.4versus10mMPBpH7.2,bothnoNaCl. Redlanes digitallycontrast-enhanced;scale1cm.'),
('a-observation','Differentemissioncolorshavesimilarbroadmigrationpositions;MPAretardedversussilicaatbothpHs. AtpH5.4silicamigratesabouthalfneutraldistance,MPAbarelymigrates;surfacechargeproposedmajorfactoroveroverallsize.'),
('b-conditions','PanelbgreenMPAandsilica;5hincubationin30mMPBpH7.3withNaCl0–1000mM;1%agarose30min100V. SaltincubationbufferdiffersfromNaCl-freegelrunningbuffer.'),
('b-lanes','Figure7blabels0,1,2,5,10,20,50,100,200,500,1000mMNaCl.2mM isextraagainstmethodslist;retainbothsourcegrids.'),
('b-observation','Silicamigrationconstantthrough200mMNaClandretardedhigher;MPAreducedabove20mM. Otherbatchesremainedunretardedeven1MNaClfor1week;notuniversalupperstabilitythresholdorassigntothe5hpanel.'),
('c-conditions','Panelcgreen,silica,cNaCl0,pH8.5printedimage;caption1%agarosein50mMTBE,pH~8.6,1h. Voltageforthisselectionnotindividuallyspecified.'),
('c-selection','Extractsmallbandfractionbyfilterpapermethodref26;rerunselectedandoriginalparticlesatsameconcentrationin1%gel. Figureuntreated/narrowedcomparison,notnewgrowthreaction.'),
('c-yield','Narrowedfractionyield up to30%;basisnotexplicitlydefined,notsilanizationisolatedyield. Selectionchangescharge-to-sizerange,doesnotproveuniquelysingle-coreparticles.')])

block('intuition',7,'Discussion A opening','cited_context',[
('stober','PriorStöber-stylealkalineTEOShydrolysis/polycondensationinethanol(ref31),andcoatingsAu,Ag,CdS,CdTe,CdSe,CdSe/CdS(refs19,20,23,32,33),arebackground;notadditionalcurrentrecipes/materialpages.'),
('previous-shells','Priorwaterroutesyield~40–80nmshellsandbroadtrapped-stateemission;TOPOCdSe/ZnSflocculatesinwater. Presentmethodadaptsthoseapproachesintogrowth/functionalization/quenchandpurification/transferparts.')], 'retain_context_without_new_recipe')
block('intuition',8,'Discussion A: silica growth and solvent exchange','interpretation_or_method_qualification',[
('solvent','MethanolchosendespiteTOPO-particlepoorsolubility. Toluenesupportsgrowthbutfasterharder-controlshellformationandnosatisfactoryreproduciblefinalsolventexchange;noquantifiedalternativeprotocol.'),
('base-role','InitiallycloudyMPSmixtureclearsuponcontrolledbasepH9or10(measuredwithpHpaper);thioldeprotonationproposedtoenabledisplacementofTOPO. Stablehours,butexcessbasecausesimmediatecross-linking/flocculation.'),
('water-role','TransferMPS-primedparticletoalmostwater-freealkalinemethanolpH~10;TMAOHcontains<5%water,basisnotstated. AbovepH~8.5waterpartiallyhydrolyzestrimethoxysilanetosilanol,enablinghydrogenbondingbeforeheating.'),
('heat-role','~60°CstrengthensSiOH···HOSibridgesintoSi–O–Siwithwaterrelease;authorsalsocallbridgesvanderWaals. Thisisaqualitativemechanism,notmeasuredconversionorfittedkinetics.'),
('overheat-control','T>70°C or heating≫1hcausesflocculationattributedtoacceleratedpolymerization/interparticlelinking. Preserve≫,notinventstrictnumericalthreshold>1h.'),
('incomplete-shell','Afterfirstgrowth,removingunreactedMPSbydialysisagainstbasifiedmethanolcausesflocculationafter~2days;dialysisagainstwatercausesalmostinstantaggregation. Partialcross-linkinganddynamicMPSexchangeareinferences.'),
('second-growth','FreshMPSinmethanoland~10%watergrowsoutershell;source~10%describesaddedmixture,notnecessarilyfinaltotalreactionwaterfraction. AfteradditionpHdrops~9andpolymerization slows;briefheatingbecauseexcessreagent/water.'),
('quench','Chlorotrimethylsilaneexcessstopscontinuedgrowth/cross-linking. Unquenchedsolutionsflocculateafterafewdaysinmethanol;quenchingaddswater-disfavoringmethylgroups.'),
('phosphonate','Negativelychargedphosphonatesaddedbeforequenchcounterreducedsolubility;authorsconsiderchargeessential. Attemptsremovingphosphonateresultedprecipitationafterafewdays;notfullyspecifiedcontrolrecipe.'),
('concentration-conflict','DiscussionevaporationviarotavaporSchlenkline,condensationfactor<4,left≥24hunderN2;experimentalprocedure2–5×then24h. Higherconcentrationcausescloudiness/precipitation;donotsilentlyreconcile.'),
('ultrafiltration','DiscussionMWCO100000membranepermeabletosolvent/smallcomplexes,retainsnanocrystals;final~2–3mL,silicaamountestimatedreduced50fold. Distinguishestimatefrommeasuredmassbalance.'),
('column-water-option','DiscussionSephadexG25equilibratedwitheither10mMPBpH~7or18MΩwater;~2mLload,top5mmperturbedbymethanol,butlongcolumnallowsproperexchange;typical~3mLfluorescenteluate.'),
('cloudiness','Initialaqueouseluateslightcloudinessascribedincompletesolvation;0.22µmacetatefilterremovesit;final~20000×gprecipitatediscarded. Solvent-equilibrationinterpretationnotdirectmeasurement.'),
('storage','Finalsilicaaqueoussolutionstoredinairandlight,stablemonths. Exacttemperature,concentrationperstabilityobservationandcontainerareunknown.'),
('wait-controls','≥2daypostquenchrestempirical;shorteningcausespartialprecipitationduringconcentration. Discussion~12hbetweenrotaryevaporationandcentrifugalconcentrationdiffersfrommethod≥12haftercentrifugalconcentrationbeforecolumn. Reasonunknown;slowsolvationhypothesis.')])
block('intuition',9,'Discussion A/B/C','interpretation_or_control',[
('residual-complexes','Optionaldialysisremovessmallbyproducts,butauthorscannotexcludesilicaspheresofsimilarsizetocoatednanocrystals. Surfaceexpectedthiols,phosphonates,methylgroupsandunquenchedsilanols;notameasuredquantitativecomposition.'),
('aps-failure','TOPOparticlescaninitiallydissolveinAPS,butfirstheatingraises~10foldscatteringsuggestingpartialagglomeration. Weakerprimaryamine–Znthanthiol–Znbondproposed;noAPSdoseorcompletefailurevariantgiven.'),
('aps-addition','APS canbeaddedafterMPSpriming,withphosphonatereagent,tointroduceaminesandslightlyraiseemission. Amountstockcompositionandquantitativeopticaloutcomeabsent;partialoptionalvariantonly.'),
('prior-optical-comparison','Previoussilica-onCdSe/CdSwork(ref20)lostfluorescence20foldwithtrapemissionbroadening. Current5–18%QYisaseparateCdSe/ZnSsystem;nottransferablecontroldata.'),
('photooxidation','Photobrighteningup2foldalsooccursinCdSe/ZnSintoluene,notinvacuum;authorssuggestaeratedphotooxidationandporoussilica. Thisisnotaprovenmechanism,oxygenflowprotocolorcontrolledoxygenkinetics.'),
('qy-outlook','FresherCdSe/ZnSordouble-shellCdSe/CdS/ZnSproposedforhigherQY;notacurrentmeasuredbatchoradditionalroute.'),
('afm-text-error','DiscussionopenswithAFMdataofFigure4andone/twofeaturesforsilica/MPA,respectively;actualFigure5andnextsentencesdescribeTWOforSILICAandONEforMPA. Preserveerrorwithcross-reference.'),
('small-peak','SmallAFMpeakroughlyindependentofcoresizeassignedtentativelytosilicacomplexes,includingsilica-coatedZnSmoieties(ref28). Ultrathin-silicaparticlealternativeconsideredunlikelybecauseprimedparticlesarewater-unstable;noidentityproof.'),
('large-peak','SecondAFMpeaklikelysilicaCdSe/ZnSbecauseheightincreaseswithcoresize;themethoddoesnotdirectlydistinguishpureSiO2fromQD-containingobjects.'),
('mpa-monolayer','Green/yellowMPAadds<1nmtoapparentdiameter,plausiblemonolayer;larger-heighttailascribeddimers/trimers. Largerred/darkredMPAapparentheightandwidthsuggestsmallaggregates;solutionversusmica-depositionoriginunknown.'),
('afm-limits','AFMcannotreliablydistinguishmonomers/dimersoroptical/chemicalidentity. SlightlyelongatedCdSecoresandnonhomogeneousZnS/silicashellscomplicateinterpretation;donotcreateexactstructuraltraininglabels.'),
('shell-estimates','Heightincrease<11nm,sourcecallsupperthicknessbelow5nmanddarkredtotal17nm;simplehalf-differencemodelgives~1,2,4,5nmgreen/yellow/red/darkred. Preserveapproximationandliteralbelow5vs~5boundaryratherthanfabricatingrefinement.'),
('aggregation-estimate','Authorsreportatleasttwoparticlespeciesandfew>20nmAFMaggregates. HPLC suggests90–100%below~40–45nm;thresholdfromporeexclusionandUVsignal,notexactparticlenumberfraction.'),
('hplc-limits','40nmsizecouldcorrespondto~sevengreennanocrystalsclusteredorsharingoneshell;interpretativeexample,notobservedaggregationnumber. Meanparticle sizecannotbequantifiedwithoutanunavailableelutionmodel.')])
block('discussion',10,'Discussion C/D and Conclusion','interpretation_or_outlook',[
('hplc-outlook','Modelingelutionneededforsize/distribution;simultaneousfluorescenceandabsorptionproposedtodistinguishQDspeciesfromsilica,notacquisitionalreadyperformed.'),
('monomer-uncertainty','AFM/HPLCcannotprovesamplescontainonlymonomers;dimers/trimers,twin/triplecoresinonebeadmayremain. Smallmulticoreentitiescouldstillworkforfluorescencetracking;applicationjudgmentnotvalidatedcellassay.'),
('homogeneity','Authorsarguepartiallycoatedparticleswoulddestabilizeandberemovedbyworkup,thereforefinalcoverageunlikelyimperfect. Thisselectionargumentisnotdirectproofuniformcontinuoussilicashell.'),
('charge-distribution','Broadgelbandsattributedmainlytowidechargedistributionratherthanmass;isoelectricbehaviorvarieswithsurfacecomposition. MPAcarboxylgroupsalmostunchargedpH5.4;silicaparticlesnegativepH5.4–8.6qualitatively.'),
('roles','Phosphonatestabilizationandthiolconjugationrolesseparatedinsilica;MPAcarboxylsserveboth. AttachingneutralbiomoleculestoMPAcouldlowerstabilitybyconsumingcharge;reasonedoutlook,notreactionmeasuredhere.'),
('group-count','Several hundred thiols per particle is consistent with the upper-estimate assay; number of negative phosphonates unknown. Do not assign charged-group density or zeta potential.'),
('dna-outlook','PrecisenumberofsingleDNAstrandattachmentsdesired;priorgoldcountingref36andband-selectionref26arecited. ThispaperdoesnotgiveDNAbindingstoichiometryorconjugationrecipe.'),
('conclusion','Conclusionblue-to-darkred~32nmfwhm,months-stabilityandhoursillumination summarizesreportedscopes;phraseQYfewtensofpercentshouldnotreplaceTable15–18%results. EasierMPApreparationversusbetterphysiological-bufferrobustnessforsilica.'),
('recent-work','Recentoligonucleotidecouplingandprogrammableassembliesareforwardcontextwithoutnewquantifiedrecipe. Do not inferclinicalbiocompatibilityorprovensuppressionofcadmiumreleasefromtitle.')])
add('acknowledgment',10,'Acknowledgment','administrative','NamedTEM/EELS/AFMhelpersandfacilities,FNS,LLNL/NPSC,DFG,FAPESP,NIH/DOE/DARPAfundingretainedasadministrativecontext;notexperimentalparameters.','administrative_context')
add('si-declaration',10,'Supporting Information Available','source_gap','MainexplicitlydeclaresHRTEMandAFMfiguresofsilanizednanocrystalsasSI. Page8865refersto~3nmamorphousshellimageandothersupportingimages. NoSIinthefingerprintedbundleorDOI-filenamematchesinbothlocalcollections;SI notlocated/verified. Do notclaimmain+SIcoverage ordisplayinventedmicroscopy.','unresolved_missing_local_supporting_information')

refs=[
('Murray,C.B.;Norris,D.J.;Bawendi,M.G. JACS1993,115,8706.','UpstreamCdSenanocrystals.'),
('Murray,C.B.;Kagan,C.R.;Bawendi,M.G. Annu.Rev.Mater.Sci.2000,30,545.','Review/background.'),
('Peng,X.;Manna,L.;Yang,W.;Wickham,J.;Scher,E.;Kadavanich,A.;Alivisatos,A.P. Nature2000,404,59.','Shapecontrolbackground.'),
('Manna,L.;Scher,E.C.;Alivisatos,A.P. JACS2000,122,12700.','Shapecontrolbackground.'),
('Welser,J.J.;Tiwari,S.;Rishton,S.;Lee,K.Y.;Lee,Y. IEEE ElectronDeviceLett.1997,18,278.','Applicationbackground.'),
('Murray,C.B.;Kagan,C.R.;Bawendi,M.G. Science1995,270,1335.','Assemblybackground.'),
('Huyhn,W.;Peng,X.;Alivisatos,A.P. Adv.Mater.1999,11,923.','Applicationbackground;authorasprinted.'),
('Vlasov,Y.A.;Yao,N.;Norris,D.J. Adv.Mater.1999,11,165.','Applicationbackground.'),
('Efros,Al.L.;Rosen,M. Annu.Rev.Mater.Sci.2000,30,475.','Confinementtheorybackground.'),
('Nirmal,M.;Brus,L. Acc.Chem.Res.1999,32,407.','Opticalbackground.'),
('Dabbousi,B.O.;Rodriguez-Viejo,J.;Mikulec,F.V.;Heine,J.R.;Mattoussi,H.;Ober,R.;Jensen,K.F.;Bawendi,M.G. J.Phys.Chem.B1997,101,9463.','Citedupstreamcore/shellprocedure.'),
('Hines,M.A.;Guyot-Sionnest,Ph. J.Phys.Chem.1996,100,468.','Citedupstreamcore/shellprocedure.'),
('Peng,X.;Schlamp,M.C.;Kadavanich,A.V.;Alivisatos,A.P. JACS1997,119,7019.','Citedupstreamshellprocedure;notindependentproofspecificcurrentZnSrecipe.'),
('Bruchez,M.J.;Moronne,M.;Gin,P.;Weiss,S.;Alivisatos,A.P. Science1998,281,2013.','Prioraqueoussilica/biologicalcontext.'),
('Chan,W.C.W.;Nie,S. Science1998,281,2016.','Priorbiologicallabeling/solubilization.'),
('Tsurui,H.;Nishimura,H.;Hattori,S.;Hirose,S.;Okamura,K.;Shirai,T. J.Histochem.Cytochem.2000,48,653.','Multiplexdyecontext.'),
('Nirmal,N.;Norris,D.J.;Kuno,M.;Bawendi,M.G.;Efros,Al.L.;Rosen,M. Phys.Rev.Lett.1995,75,3728.','Priorfluorescencelifetimes;sourceinitialNretained.'),
('Dahan,M.;Laurence,T.;Pinaud,F.;Chemla,D.S.;Alivisatos,A.P.;Sauer,M.;Weiss,S. Opt.Lett.,submittedforpublication.','Unpublished-at-sourcecitation;noinventedyear/DOI.'),
('Correa-Duarte,M.A.;Giersig,M.;Liz-Marzan,L.M. Chem.Phys.Lett.1998,286,497.','Priorsilicacoating.'),
('Rogach,A.L.;Dattatri,N.;Ostrander,J.W.;Giersig,M.;Kotov,N.A. Chem.Mater.2000,9,2676.','Priorsilicacoatingandopticalcomparison;retainprintedbibliographywithoutsilentvolumeamendment.'),
('Mitchell,G.P.;Mirkin,C.A.;Letsinger,R.L. JACS1999,121,8122.','MPAprotocoldependency.'),
('Chen,C.C.;Yet,C.P.;Wang,H.N.;Chao,C.Y. Langmuir1999,15,6845.','MPAprotocoldependency.'),
('Mulvaney,P.;Liz-Marzan,L.M.;Giesig,M.;Ung,T. J.Mater.Chem.2000,10,1259.','Coatingcontext;spellingasprinted.'),
('Kubin,R.F.;Fletcher,A.N. J.Lumin.1982,27,455.','Rhodamine6G95%QYreference.'),
('Hermanson,G.T. BioconjugationTechniques,AcademicPress,1996.','Ellmanassayandbioconjugationmethodscontext.'),
('Loweth,C.J.;Caldwell,W.B.;Peng,X.;Alivisatos,A.P.;Schultz,P.G. Angew.Chem.Int.Ed.Engl.1999,38,1808.','Citedfilter-paperbandextractionprocedure.'),
('Note27: AFMsmallfeaturesanddisplayselection.','Fullscientificnoteextractedseparatelybelow.'),
('Note28: evidenceforresidualZnSnanoparticles.','Fullscientificnoteextractedseparatelybelow.'),
('Fisher,Ch.H.;Weller,H.;Katsikas,L.;Henglein,A. Langmuir1989,5,429.','HPLCmethodcontext.'),
('Wilcoxon,J.P.;Martin,J.E.;Provencio,P. Langmuir2000,16,9912.','HPLCmethodcontext.'),
('Ströber,W.;Fink,A.;Bohn,E. J.ColloidInterfaceSci.1968,26,62.','Silicapolymerizationbackground;sourceprintsStröber.'),
('Liz-Marzan,L.M.;Giersig,M.;Mulvaney,P. Langmuir1996,12,4329.','Priorsilicacoating.'),
('Ung,T.;Liz-Marzan,L.M.;Mulvaney,P. Langmuir1998,14,3740.','Priorsilicacoating.'),
('Note34: fluorometerscatteringmethod.','Fullscientificnoteextractedseparatelybelow.'),
('Plueddemann,E.P. SilaneCouplingAgents,2nded.,PlenumPress,NewYork,1991.','Silanolcondensationmechanismcontext.'),
('Zanchet,D.;Micheel,C.;Parak,W.J.;Gerion,D.;Alivisatos,A.P. NanoLett.2001,1,32.','PriorAu–DNAcountingcontext;noexecutedcurrentDNAsynthesis.')]
for i,(bib,scope) in enumerate(refs,1):
    add(f'reference-{i:02}',10 if i<=4 else 11,f'References and Notes ({i})','reference',bib+' '+scope+' Cited document not independently inspected in this current main-only audit.','retain_cited_dependency_without_claimed_external_review')
block('note27',11,'Reference/Note27, columns1–2','method_qualification',[
('small-peak','Everywater-solublesample,silicaandMPA,hasprominent0.5–2nmAFMpeak;ascribedmainlytosmallsilicacomplexesandresidualZnSfromshellgrowth,ref28. Itisomittedfromdisplaybecausenotshell-thicknessinformation.'),
('cutoff','Authorssaythey arbitrarilyomitallheightsbelowcorrespondingCdSe/ZnSdiameterinFigure5. Retainthisreportedselectionandvisiblelowerfeatures;norawfullhistogramcountsavailable.')])
block('note28',11,'Reference/Note28','control_or_interpretation',[
('stock-feature','CdSe/ZnScore/shellsolutionhasasharpUVexcitonfeature.'),
('seed-free-test','InjectZnS-shellprecursorsintohotpureTOPOwithoutCdSecorestoimitateshellgrowth;testsolutionhasthesameUVfeature. Noidentities,amounts,temperature,numericalpeakwavelengthorcompleteZnSrecipeprovided.'),
('aged-stock','SameUVpeakobservedinZnS-shellprecursorstockstoredroomtemperatureafewdays;authorsattributeothersmallparticlesinMPA/silicasolutionstoresidualZnS. Qualitativeattribution,notcompositionresolvedforeachAFMobject.')])
block('note34',11,'Reference/Note34','measurement_method_or_observation',[
('method','Qualitativescatteringwithfluorometersetup:sourcecallsitthesecondharmonicofexcitation,scatteredisotropically;detectlightat90°. Wavelengthnotgiven;donotreinterpretascalibratedDLSsize.'),
('comparison','TOPOCdSe/ZnSinmethanolscatteralmost100timesmorethanintoluene;authorsrejectrefractiveindexdifferenceasexplanation. MPS-primedCdSe/ZnSinmethanolexhibitsnoscatteringqualitatively. Noabsoluteparticlesizefromthisratio.')])
add('unreported-techniques',11,'Full supplied main article','missingness','No measured diffraction pattern/SAED/XRD, refined phase/unitcell/CIF, Raman, raw spectra tables, exactliganddensity, directcadmiumleaching/toxicityassayorDFTcalculationissupplied. HRTEM/AFMimagesareannouncedinmissingSI;mainFigure5containsdistributions,nottheoriginalmicroscopyimages.','retain_explicit_missingness')

pages=[]
for i in range(1,12):
    p=B/f'main-{i:02}.png';t=B/f'main-{i:02}.txt'
    pages.append(dict(pdf_page=i,printed_page=8860+i,text_file=t.name,text_sha256=sha(t),text_read=True,render_file=p.name,render_sha256=sha(p),visually_reviewed=True,review_scope='Full supplied page: both columns, figures/tables/captions, headers/footers and notes.'))
conflicts=[u for u in U if any(k in u['source_unit_id'] for k in ['filters','optional-water-dialysis','wait-before-exchange','body-peaks-conflict','concentration-conflict','afm-text-error','selection-conflict','b-lanes','c-conditions','figure4-conditions','shell-estimates'])]
identity=dict(source_id='gerion2001',doi='10.1021/jp0105488',title='Synthesis and Properties of Biocompatible Water-Soluble Silica-Coated CdSe/ZnS Semiconductor Quantum Dots',authors=['Daniele Gerion','Fabien Pinaud','Shara C. Williams','Wolfgang J. Parak','Daniela Zanchet','Shimon Weiss','A. Paul Alivisatos'],journal='Journal of Physical Chemistry B',year=2001,volume=105,issue=37,pages='8861–8871',received='2001-02-12',final_form='2001-04-17',published_online='2001-06-05',primary_article=True,source_path=str(S),source_sha256=sha(S),legacy_copy_path=str(L),legacy_copy_sha256=sha(L),copies_byte_identical=sha(S)==sha(L),main_pages=11,verified_by='Title/byline, printed DOI footer, consecutive page headers and complete article contents; not PDF metadata title No Job Name.',si_status='explicitly_announced_but_not_located_or_verified_locally',si_expected_content='HRTEM and AFM figures of silanized nanocrystals',si_search_scope='Both fingerprint generation2 documents and DOI-name matches in incoming and legacy local directories; only identical main files located. This bounded search does not prove SI absent from every differently named local file.',external_research=False)
audit=dict(source_id='gerion2001',doi=identity['doi'],status='complete_supplied_main_text_and_visual_inventory_with_missing_SI',reviewer='independent_source_audit_agent',reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_path=str(S),source_sha256=sha(S),coverage=dict(main_pages=11,text_pages_read=11,visual_pages_reviewed=11,si_pages_verified=0,si_status=identity['si_status'],original_figures=7,original_tables=2,numbered_equations=0,references_and_notes=36,scope='All supplied main pages. No raw curve digitization or external citation review. Missing SI prevents full main+SI completion claim.'),pages=pages,unit_count=len(U),units=U,critical_limits=[u['source_unit_id'] for u in conflicts],sample_join_rules=['Silica versus MPA compare preparations from the same starting CdSe/ZnS cohort when explicitly stated; do not turn coating/assay states into independent starting-core syntheses.','Table1 optical colors and Table2 structural colors are not proven identical physical batches; no exact recipe-to-crystal-structure target.','HPLC blue/red traces are two silanization preparations of the same starting GREEN emission sample; curve color is not product emission.','Figure7 original/narrowed fractions belong to selection lineage; yield up to30% is selection recovery, not reaction yield.','No SI microscopy was read, shown or audited; EELS measurements are described but not plotted.','AFM measures heights of dried specimens; shell thickness is interpretation, some objects may be multicore or silica-only.','References1,11–13 are upstream core/shell dependencies, not reproduced precursor protocols.'],unresolved=['Missing explicitly announced SI.','Printedfilterunits and several prose/panelconditions conflict; preserved perlocator.','UnknownAPSamount,baseconcentration,phosphonatecounterion,butanolisomer,preformedcore/shellfullrecipe.','Uncertainmonomer/dimeridentity,shellhomogeneity,silicacomplexcontaminationandabsolutegroupcounts.'],local_only=True,site_mutated=False)
(B/'source-identity.json').write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'independent-page-coverage.json').write_text(json.dumps({'source_id':'gerion2001','source_sha256':sha(S),'pages':pages,'scope':audit['coverage']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Gerion2001 independent source audit','',f'All 11 supplied main pages were independently read and visually inspected. Inventory: {len(U)} source units, seven figures, two tables, 36 references/notes, no numbered equations.','',f'Source SHA256: `{sha(S)}`. The legacy main is byte-identical.','', '**SI gap:** The article explicitly announces HRTEM and AFM supporting images. No SI is present in the fingerprinted bundle or local DOI-filename matches. This is a complete supplied-main review, not a complete main+SI review.','', '**Scientific boundaries:** Two detailed alternative coating procedures use preformed CdSe/ZnS; upstream nanocrystal syntheses remain cited dependencies. APS after priming is an unquantified optional extension; failed APS priming and other qualitative controls are not complete preparative recipes. Particle-size measurements, optical tables, HPLC fractions and gel selections retain their own specimen scope. AFM-derived shell thickness is approximate and cannot prove single-core or uniform-shell structure.','', '**Retained source discrepancies:** mm versus µm filters; optical body versus Table1 peaks; Figure4 plotted4000s versus reported4h; Figure7 extra2mM lane and pH8.5/~8.6; condensation2–5× versus<4×; differing12h wait placement; reversed AFM peak count/wrong figure reference; histogram omission rules versus visible small features.','', '## Source units','']
for u in U:md.extend([f"- **{u['source_unit_id']}** — p.{u['printed_page']}, {u['locator']} ({u['kind']}; {u['disposition']}): {u['claim']}"])
(B/'source-audit.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
(B/'source-identity.md').write_text('# Verified source identity\n\n'+identity['title']+'\n\nGerion et al., J. Phys. Chem. B 2001,105(37),8861–8871. DOI10.1021/jp0105488. Received12February2001; finalform17April2001; online5June2001.\n\nBoth local main copies are byte-identical, SHA256`'+sha(S)+'`. All11pages read and visually inspected. SI is explicitly announced but not located or verified in the inspected local bundle. No downloads or external research.\n',encoding='utf-8')
assert len({u['source_unit_id'] for u in U})==len(U)
assert all(p['text_read'] and p['visually_reviewed'] for p in pages)
print(json.dumps({'units':len(U),'source_sha256':sha(S),'audit_sha256':sha(B/'source-audit.json'),'identity_sha256':sha(B/'source-identity.json'),'page_coverage':len(pages),'si_verified':0},indent=2))
