"""Source-review staging, not a canonical training record or public publication."""
from pathlib import Path
import hashlib
import json

OUT = Path(__file__).resolve().parent
SOURCE = Path(r'[local path redacted]')

def ev(page, section):
    return {'document': 'main', 'pdf_page': page, 'printed_page': 1223 + page, 'section_or_item': section}

def q(value, unit, page, section, *, meaning=None, qualifier='reported', raw=None):
    return {'value': value, 'unit': unit, 'qualifier': qualifier, 'meaning': meaning,
            'raw': raw, 'evidence': [ev(page, section)]}

def item(identifier, text, page, section, **extra):
    return {'id': identifier, 'summary': text, 'evidence': [ev(page, section)], **extra}

chemicals = [
    item('disilane', 'Disilane, Si2H6: silicon precursor supplied as 0.1% in He (Matheson); further diluted to reported 3–30 ppm.', 2, 'Experimental A', role='precursor', formula='Si2H6', charged_mass=None),
    item('helium', 'He: purified carrier gas (Air Products research grade); Oxisorb used to remove possible water and oxygen. Also dilution gas (zero grade mixture).', 2, 'Experimental A', role='carrier_and_dilution_gas', formula='He'),
    item('oxygen', 'O2 in the 1:6 O2:He dilution/oxidation stream (zero grade, Air Products).', 2, 'Experimental A', role='oxidant', formula='O2'),
    item('ethylene-glycol', 'Ethylene glycol, HOCH2CH2OH: 9 cm3 in each of the prebubbler and frit collector. Also HPLC mobile phase.', 2, 'Experimental A–B', role='collection_liquid_and_mobile_phase', formula='C2H6O2'),
    item('dichlorosilane', 'Frit is silanized with a toluene solution of printed SiH2Cl2; amount, concentration and treatment conditions are not stated.', 2, 'Experimental A, collection', role='apparatus_pretreatment', formula='SiH2Cl2', identity_note='Formula visually read from paper; not the synthesis gas precursor.'),
    item('toluene', 'Solvent for frit silanization reagent; charge is unreported.', 2, 'Experimental A, collection', role='apparatus_pretreatment_solvent', formula='C7H8'),
    item('methanol', 'Methanol: component of reported 60:40 methanol–ethylene glycol HPLC mixture; percentage basis not expressly defined.', 2, 'Experimental B', role='analysis_mobile_phase', formula='CH4O'),
    item('sodium-methoxide', 'Sodium methylate (sodium methoxide), 1.5 × 10^-3 M in HPLC mobile phase.', 2, 'Experimental B', role='analysis_additive', formula='CH3NaO'),
    item('tetrabutylammonium-bromide', 'Tetrabutylammonium bromide, 0.1 M in HPLC mobile phase.', 2, 'Experimental B', role='analysis_additive', formula='C16H36BrN'),
    item('polystyrene-sulfonate-sodium', 'Polystyrene sulfonate sodium-salt polymers of several molecular weights (Polymer Laboratories): HPLC calibration standards. Molecular weights not listed.', 2, 'Experimental B', role='calibration_standard', formula=None),
    item('ethylene-dichloride', 'Ethylene dichloride used for powder washing. TEM fraction preparation says ethylene chloride; preserve original naming distinction instead of silently assigning a separate recipe.', 2, 'Experimental B', role='washing_solvent', formula='C2H4Cl2', identity_note='1,2-dichloroethane conventional identity; TEM paragraph short name should be retained.'),
    item('acetone', 'Acetone used with ethylene dichloride for repeated washing after colloid evaporation.', 2, 'Experimental B', role='washing_solvent', formula='C3H6O'),
    item('potassium-bromide', 'KBr used to press IR pellets.', 2, 'Experimental B', role='characterization_matrix', formula='KBr'),
    item('aot', 'AOT soap: small amount used as alternative powder-XRD binder. Paper does not expand its identity or give a dose.', 3, 'Experimental B continuation', role='characterization_binder', formula=None),
    item('mylar', 'Mylar: alternative XRD powder enclosure, not a synthesis input.', 3, 'Experimental B continuation', role='characterization_support', formula=None),
    item('argon', 'Ar atmosphere for acidic reflux activation; purity/flow/pressure are not reported.', 5, 'Results B', role='post_treatment_atmosphere', formula='Ar'),
    item('sulfuric-acid', 'H2SO4 acidifies added water to pH 1; acid concentration/charge is not reported.', 5, 'Results B', role='post_treatment_acid', formula='H2SO4'),
    item('water', '5% added acidic water, pH 1, for activation of ethylene glycol colloid. Percentage denominator and volume/mass basis are unspecified.', 5, 'Results B', role='post_treatment_addition', formula='H2O'),
    item('rhodamine-6g', 'R6G in ethanol, reference quantum yield 0.9, used for approximate absolute luminescence-yield comparison; dye concentration not supplied.', 6, 'Results B', role='calibration_standard', formula=None),
    item('ethanol', 'Solvent for the R6G luminescence reference.', 6, 'Results B', role='calibration_solvent', formula='C2H6O'),
]

operations = [
    item('feed', 'Purify He and combine with supplied 0.1% disilane/He stream. The three sample labels specify different stock-gas flow rates, not pure-disilane flows.', 2, 'Experimental A',
         inputs=['helium', 'disilane'], apparatus='MKS mass-flow controllers; Matheson Oxisorb purifier',
         conditions={'total_pyrolysis_feed': q(300, 'sccm', 2, 'Experimental A', meaning='standard gas-volume flow, standard-reference temperature/pressure not stated'),
                     'disilane_concentration_range': q([3,30], 'ppm', 2, 'Experimental A'),
                     'reactor_pressure': q(1.4, 'atm', 2, 'Experimental A', meaning='absolute versus gauge not specified'),
                     'quartz_inner_diameter': q(7, 'mm', 2, 'Experimental A')}),
    item('pyrolysis', 'Thermally decompose dilute disilane in the first externally heated quartz zone, forming silicon aerosol and some wall deposit. Internal thermocouples are removed before disilane introduction.', 2, 'Experimental A',
         inputs=['feed'], outputs=['silicon-aerosol', 'silicon-wall-deposit'], apparatus='Quartz tube with external oven',
         conditions={'zone_length':q(1,'cm',2,'Experimental A'), 'text_temperature':q(860,'degC',2,'Experimental A'),
                     'figure_temperature':q(865,'degC',1,'Figure 1',meaning='conflicting source illustration label'),
                     'linear_velocity':q(18,'cm/s',2,'Experimental A',qualifier='approximate'),
                     'residence_time':q(60,'ms',2,'Experimental A',qualifier='approximate')},
         observations=['Paper describes 2–8 nm crystalline particles by the zone exit.', 'Substantially faster flow or temperature below 700 °C gives amorphous particles; no exact alternative flow stated.', 'No apparent operational change reported over 850–1050 °C; this is not an assigned sample-specific temperature sweep.']),
    item('dilution', 'Pass hot aerosol through first aperture and dilute immediately with O2/He to suppress further growth/aggregation by dilution and cooling.', 2, 'Experimental A',
         inputs=['silicon-aerosol', 'oxygen', 'helium'], outputs=['diluted-aerosol'],
         conditions={'aperture':q(0.6,'mm',2,'Experimental A'), 'dilution_ratio':q('1:23',None,2,'Experimental A',meaning='reported ratio; retain stream basis'),
                     'oxygen_to_helium':q('1:6',None,2,'Experimental A'), 'cooled_temperature':q([200,300],'degC',2,'Experimental A'),
                     'oxygen_flow':q(1000,'sccm',1,'Figure 1'), 'dilution_helium_flow':q(6000,'sccm',1,'Figure 1')},
         notes=['Gas flows in Figure 1 imply an approximate dilution; do not silently replace the reported 1:23 by an exact derived value.']),
    item('oxidation', 'Pass diluted aerosol through a second aperture and external oven to form surface oxide.', 2, 'Experimental A',
         inputs=['diluted-aerosol'], outputs=['surface-oxidized-aerosol'], apparatus='Second external oven on quartz tube',
         conditions={'aperture':q([1,2],'mm',2,'Experimental A'), 'temperature':q(700,'degC',2,'Experimental A'),
                     'linear_velocity':q(430,'cm/s',2,'Experimental A',qualifier='approximate'), 'residence_time':q(20,'ms',2,'Experimental A',qualifier='approximate')},
         notes=['Protocol-level estimated oxide thickness is 1–2 nm; sample-specific measurements remain separate.', 'Dilution consumes approximately one 1A tank of compressed He per 24 h; tank capacity is not specified and this is not a reported individual run duration.']),
    item('collection', 'Cool aerosol, pass first through EG prebubbler, then through silanized coarse-glass frit into the EG collection bubbler. Collect both dispersions without conflating them into a single measured batch.', 2, 'Experimental A',
         inputs=['surface-oxidized-aerosol','ethylene-glycol'], outputs=['prebubbler-colloid','collector-colloid'],
         conditions={'prebubbler_EG':q(9,'cm3',2,'Experimental A'), 'collector_EG':q(9,'cm3',2,'Experimental A'),
                     'collection_temperature':None,'collection_duration':None},
         notes=['Prebubbler is before frit, although paragraph initially introduces the frit first.', '2–3 cm3 EG loss in prebubbler per 24 h is an operational observation, not synthesis duration.', 'About two-thirds of collected crystallites appear in second bubbler; one-third Si capture is a separate source-derived mass-efficiency estimate.']),
]

samples=[]
for label,flow,pressure in [('6.0',6.0,20),('2.0',2.0,7),('1.0',1.0,3.5)]:
    samples.append(item('colloid-'+label, 'Aerosol-derived colloid, label is the 0.1%-disilane/He stock-gas flow.',3,'Results A',
        parent_protocol='continuous-aerosol', stock_gas_flow=q(flow,'sccm',3,'Results A'),
        disilane_partial_pressure=q(pressure,'mTorr',3,'Results A'),
        paired_states=[label+'-as-made',label+'-acid-activated',label+'-dried-powder'],
        sample_link='source formulation label; repeated physical runs not enumerated',
        structural_status=('diamond-Si cores with oxide-shell evidence' if label!='1.0' else 'direct core crystal structure not established; do not force diamond-Si training target')))
samples.append(item('AKS41','Earlier apparatus formulation; 13 nm nominal crystallites, not one of the three quantified flow recipes.',3,'Results A',parent_protocol=None,quantified_recipe_available=False,
                    notes=['Separate TEM reports individual crystallite average 14 nm, SD 3 nm; a shown particle has 13 nm core and 1.5 nm amorphous shell. These are distinct dimensional scopes.']))

procedures = [
    item('acid-activation','Reflux EG colloid under Ar near 200 °C for about 1 h with 5% added acidic water (pH 1, H2SO4).',5,'Results B',
         inputs=['as-made-colloid','water','sulfuric-acid','argon'], outputs=['acid-activated-colloid'],
         conditions={'temperature':q(200,'degC',5,'Results B',qualifier='near'), 'time':q(1,'h',5,'Results B',qualifier='approximate'),
                     'added_water_fraction':q(5,'%',5,'Results B',meaning='basis/denominator unreported'),'added_water_pH':q(1,None,5,'Results B'), 'argon_flow':None, 'pressure':None},
         notes=['Luminescence enhancement belongs to activated state. HPLC/TEM/UV/XRD show no significant reported change on reflux; do not interpret this as atomically proven unchanged surface chemistry.']),
    item('concentrate','Concentrate colloid 5–10 times by mild 80 °C heating under vacuum.',4,'Results A',conditions={'temperature':q(80,'degC',4,'Results A'),'vacuum_pressure':None,'time':None,'concentration_factor':q([5,10],None,4,'Results A')}),
    item('dry-powder','Evaporate colloid under mild heating and vacuum to paste; wash repeatedly with acetone and ethylene dichloride to yield deep-brown powder, typically 10 mg or less for small crystallites.',2,'Experimental B',
         inputs=['colloid','acetone','ethylene-dichloride'], outputs=['dried-powder'], conditions={'temperature':None,'pressure':None,'time':None,'wash_counts':None,'wash_volumes':None},
         notes=['Do not inherit 80 °C from separate concentration sentence as the explicitly reported powder-preparation setting. Powder amount is not a whole-reactor Si yield.']),
    item('HPLC','Analyze/fractionate by sequential ZORBAX 60-S and 300-S columns on HP 1090 with diode-array UV–vis detection.',2,'Experimental B',
         inputs=['colloid','methanol','ethylene-glycol','sodium-methoxide','tetrabutylammonium-bromide'],
         conditions={'mobile_phase':q('60:40 methanol:ethylene glycol',None,2,'Experimental B',meaning='mixture basis not explicit'),
                     'mobile_phase_flow':q(0.75,'cm3/min',2,'Experimental B'),'temperature':q(50,'degC',2,'Experimental B'),
                     'sodium_methylate':q(0.0015,'mol/L',2,'Experimental B'), 'TBAB':q(0.1,'mol/L',2,'Experimental B')},
         calibration={'standard':'polystyrene-sulfonate-sodium','mapping':'equivalent hard-sphere diameter; logarithmic with elution time',
                      'diameter_decrease_per_minute':1.72,'instrumental_fwhm_min':0.4,'instrumental_diameter_factor':1.24,
                      'exclusion_time_min':8.0,'exclusion_size_nm':'about 20','molecular_front_min':14.8},
         notes=['Equivalent chromatographic diameters include permanent aggregates; not core diameters.', 'The basic mobile phase quenches activated luminescence. Particle-containing fractions at 8.5–12.5 min can be acid-reactivated; reactivation does not create a new independent synthesis.']),
    item('TEM','JEOL 2000-FX at 200 keV. Collect aerosol directly or evaporate colloid on holey-carbon film. Wash evaporated HPLC fractions with reported ethylene chloride to remove organic salt.',2,'Experimental B',conditions={'electron_energy':q(200,'keV',2,'Experimental B')},notes=['TEM sample-preparation branches are not identically linked to every figure.']),
    item('IR','Grind dried sample and press into KBr pellets.',2,'Experimental B',conditions={'KBr_amount':None}),
    item('powder-XRD','Bind powder with a little AOT soap OR enclose in Mylar; mount on optical-fiber tip. Triple-crystal spectrometer, Mo K-alpha, Rigaku 12-kW rotating anode, pyrolytic-graphite monochromator and analyzer.',3,'Experimental B continuation',notes=['Alternatives remain separate; soap causes low-angle scattering and is not a product phase.']),
    item('optical-acquisition','HP 8452A UV–vis; SPEX Fluorolog 2 red response to about 900 nm; some long-wavelength spectra on Jobin-Yvon HR640 with Ge photodiode and 355-nm excitation. Both PL systems calibrated against tungsten-lamp known irradiance.',2,'Experimental B',notes=['p6 says 350-nm excitation for Figs9–11; Fig9 caption says355nm. Keep discrepancy, not a silently averaged value.']),
    item('time-resolved-PL','1.0-colloid decay after picosecond355-nm pulse, photomultiplier/digital-storage oscilloscope with10-ns resolution.',6,'Figure12',notes=['Decay fits17 and76microseconds are major multiexponential components, not a single radiative lifetime.']),
]

table_rows = [
 {'sample':'6.0','TEM_bright_field_nm':7.5,'TEM_dark_field_core_nm':5,'XRD_coherence_nm':4.8,'HPLC_monomer_time_min':10.7,'HPLC_monomer_equivalent_size_nm':6.5,'HPLC_distribution_fwhm_nm':[5,13],'activated_PL_peak_nm':970},
 {'sample':'2.0','TEM_bright_field_nm':{'range':[3,6],'approximate':True},'TEM_dark_field_core_nm':{'range':[2,4],'approximate':True},'XRD_coherence_nm':2,'HPLC_monomer_time_min':11.5,'HPLC_monomer_equivalent_size_nm':4.2,'HPLC_distribution_fwhm_nm':[3.1,10],'activated_PL_peak_nm':770},
 {'sample':'1.0','TEM_bright_field_nm':{'less_than':5},'TEM_dark_field_core_nm':{'value':None,'status':'not_observed'},'XRD_coherence_nm':{'value':None,'status':'not_observed'},'HPLC_monomer_time_min':12.1,'HPLC_monomer_equivalent_size_nm':3.2,'HPLC_distribution_fwhm_nm':[2.5,9],'activated_PL_peak_nm':660},
]
observations = [
 item('6.0-TEM-distribution','Mean overall TEM diameter7.5nm, standard deviation2.5nm; dark-field core about5nm, average oxide shell1.2nm.',4,'Results A',sample='6.0',values={'overall_diameter_nm':7.5,'standard_deviation_nm':2.5,'core_diameter_nm':5,'shell_thickness_nm':1.2}),
 item('6.0-HPLC-conflict','Table I reports5–13nm FWHM; Results prose says5.5–13nm. Monomer peak about6.5nm. Retain both.',4,'Results A',sample='6.0'),
 item('2.0-HPLC-conflict','Table I gives4.2nm monomer size; prose describes a barely resolved shoulder about4.5nm.',5,'Results A',sample='2.0'),
 item('1.0-structure-limit','No direct structural information on smallest colloid. Powder XRD only diffuse background; any crystalline Si, if present, must be smaller than2nm according to authors. This is not measured2nm crystallinity.',5,'Results A',sample='1.0'),
 item('lattice','Joint powder-line-position fit: lattice parameter within0.25% of bulk5.43Angstrom for6.0 and2.0. No measured atom coordinates or experimental CIF supplied.',5,'Results A',samples=['6.0','2.0'],values={'bulk_reference_a_angstrom':5.43,'reported_relative_tolerance_percent':0.25}),
 item('AKS41-TEM','Shown particle has13nm core,1.5nm amorphous shell and3.1Angstrom(111) fringes. Overall individual-particle mean14nm, SD3nm. Text describes intense narrow diamond-Si diffraction rings but displays no diffraction pattern.',4,'Results A',sample='AKS41'),
 item('aggregation','HPLC fractions preserve elution times on reinjection. AKS41 large/excluded fraction contains aggregates, middle16nm peak mostly dimers/trimers and11nm peak mostly individual crystallites. HPLC is not a direct crystalline-core-size distribution.',4,'Results A',sample='AKS41'),
 item('IR-peaks','6.0 powder: strong SiO2-related1100cm^-1, weaker800cm^-1, OH about3300cm^-1; washing-sensitive1350/1700cm^-1 peaks interpreted as residual organic species; little2100cm^-1 SiH signal.',4,'Results A, Figure7',sample='6.0',continuation_evidence=[ev(5,'Results A')]),
 item('absorption','6.0 and AKS41 similar bulk-like UV absorption: weak visible tail from370nm, stronger370–240nm.2.0/1.0 lose inflections without clear blue shift/discrete structure. Actual indirect gap not directly observed in dilute colloid.',5,'Results B',context_only=True),
 item('activation-state','6.0 as-made luminescence weak and broad near900–950nm, enhanced by acid activation. Activated peaks970/770/660nm vary somewhat between runs.',5,'Results B',continuation_evidence=[ev(6,'Results B')]),
 item('PL-yield','All three activated colloids have estimated quantum yields slightly above5%, by comparison with R6G/ethanol reference quantum yield0.9 after absorbance correction and spectral integration.',6,'Results B',samples=['6.0-acid-activated','2.0-acid-activated','1.0-acid-activated'],values={'yield_percent':5,'qualifier':'slightly_above_estimated','reference_QY':0.9},notes=['Abstract rounds to5%; not exact5.000%, not as-made yield.']),
 item('PL-decay','1.0 activated-colloid decay is multiexponential on microsecond scale; adequate fit major components17 and76microseconds.',6,'Results B and Figure12',sample='1.0-acid-activated',values={'major_decay_components_us':[17,76]},notes=['Amplitudes, full fit model and uncertainty absent; not a uniquely fitted single lifetime.']),
 item('pH-quenching','pH above about5 quenches activated emission at room temperature. A second acidic reflux partly restores it. Prolonged strong-base storage degrades particles so reflux no longer restores emission.',5,'Results B',continuation_evidence=[ev(6,'Results B')],notes=['Base identity and exact dose/time are missing. Do not invent a base-titration recipe.']),
 item('mass-accounting','6.0 apparatus input21mg Si/day; optical-density comparison with Mie model gives aboutone-third of Si collected as colloidal crystallites, with day-to-day variation;2.0/1.0 similar yields. Abouttwo-thirds of collected crystallites reach second bubbler.',3,'Results A',continuation_evidence=[ev(4,'Results A')],values={'Si_feed_mg_per_day':21,'estimated_capture_fraction':1/3,'second_bubbler_fraction':2/3},notes=['Input rate, model-derived capture, bubbler partition, capped powder mass, and duration are separate.']),
 item('concentration-calibration','Mie calculation:1mg/cm3 crystallineSi -> optical density1.85 at295nm for1mm path, approximately size-independent below50nm absent quantum/scattering effects.',3,'Results A',model_derived=True),
 item('stability','Collected dispersions resist flocculation for months under air and during reflux, centrifuging and concentration; this does not establish months-long activated PL stability.',2,'Experimental A'),
    item('unwashed-powder','Reference note41: unwashed powder can have extra sharp XRD lines and unidentified crystallites tensofnanometers large, possibly oxidized molecular pyrolysis products.',7,'Reference41',notes=['Unknown byproduct composition remains unknown.']),
 item('current-colloid-electron-diffraction','6.0 gives intense crystalline Si electron diffraction. The paragraph discussing smaller2.0/1.0 colloids describes weak broadened rings; the authors later explicitly state no direct structural information for1.0. Preserve that limitation and do not assign an unambiguous1.0 phase.',4,'Results A',continuation_evidence=[ev(5,'Results A')],notes=['Prose observations only; no actual electron-diffraction/SAED image supplied.']),
 item('2.0-TEM-size-bias','Occasional2.0 particles show3–4nm lattice-resolvedSi; dark-field cores2–4nm are near method limit. Authors consider TEM-resolved crystallites the larger end relative to XRD2nm coherence.',5,'Results A',sample='2.0'),
 item('1.0-excitation-spectrum','Luminescence excitation spectrum of activated1.0 colloid essentially tracks the UV absorption spectrum; reported in prose without an additional plotted excitation spectrum.',6,'Results B',sample='1.0-acid-activated'),
 item('bulk-silicon-optical-control','High-quality strongly absorbing bulkSi gives no detectable room-temperature emission in the authors apparatus; liquid-helium-temperature bulkSi shows a sharp1060nm line.',6,'Results B',context_only=True,notes=['Control is not a nanoparticle outcome or a new synthesis recipe.']),
]

figures = [
 (1,1,'Quartz pyrolysis, dilution and oxidation apparatus','protocol','865°C diagram versus860°C main text'),
 (2,3,'Optical absorbance spectra:6.0 upper,2.0 lower','6.0;2.0','Measured spectra, not digitized raw curves'),
 (3,3,'Bright-field TEM of oxidizedSi aggregate','AKS41','Earlier apparatus; must not be relabeled6.0'),
 (4,3,'HPLC of older colloid','AKS41','Caption prints ASK41 versus bodyAKS41; same contextual label likely, retained discrepancy'),
 (5,4,'HPLC','6.0','Chromatographic size includes aggregates'),
 (6,4,'PowderXRD:6.0 upper,2.0 lower with fitted lines','6.0;2.0','Measured pattern and fitted diamondSi/reference broad component distinct'),
 (7,4,'Powder infrared spectrum','6.0','Main text incorrectly references XRD Figure5 rather than6'),
 (8,5,'HPLC','1.0','No direct proof of crystalline core'),
 (9,5,'Room-temperaturePL before/after acid activation','6.0','Caption355nm excitation versus Results350nm'),
 (10,6,'Luminescence','2.0-acid-activated','PL state established by surrounding Results'),
 (11,6,'Luminescence','1.0-acid-activated','Do not assign proven diamond lattice to smallest sample'),
 (12,6,'Time-resolved luminescence','1.0-acid-activated','Picosecond355nm pulse,10ns detector resolution'),
]

data = {
 'extraction_schema':'mattersyn-source-review-staging-1',
 'status':'full_main_read; independent_full_main_audit_completed; canonical_integration_pending',
 'training_eligible':False, 'website_published':False,
 'source':{'title':'A Luminescent Silicon Nanocrystal Colloid via a High-Temperature Aerosol Reaction',
           'authors':['K. A. Littau','P. J. Szajowski','A. J. Muller','A. R. Kortan','L. E. Brus'],
           'journal':'The Journal of Physical Chemistry','year':1993,'volume':97,'pages':'1224–1230','doi':'10.1021/j100108a019',
           'doi_provenance':'local DOI-named file; printed title/authors/journal checked', 'main_file':str(SOURCE),
           'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'pdf_pages':7,
           'si_status':'not located or verified; not evidence that no SI exists', 'source_folder_unmodified':True},
 'review':{'reader':'root','text_pages':[1,2,3,4,5,6,7],'visually_inspected_pages':[1,2,3,4,5,6,7],
           'independent_audit':'independent-audit.md/json; targeted extraction additions addressed, canonical and browser audits remain pending','ordering':'oldest folder arrival; Windows creation timestamp',
           'next_stage':'Audit this staging extraction; implement continuous-gas-flow data fields and apparatus scenes; migrate to canonical records, source figures, inventory and reader views; validate then publish.'},
 'relevance':{'contains_synthesis':True,'contains_structure':True,'contains_properties':True,
              'method':'continuous aerosol pyrolysis with oxidative passivation and liquid collection',
              'systems':['Si/SiOx surface-oxidized nanocrystals'],
              'scope_note':'Do not claim stoichiometric crystallineSiO2 shell; surface oxide described asSiO2, no resolved atomic interface.1.0 crystallinity unresolved.'},
 'new_field_requirements':['gas_streams with stock and pure-species composition distinguished','standard_volumetric_flow and reference conditions','continuous production rate versus batch charge','linear_velocity','residence_time versus run duration','reactor geometry and apertures','stream dilution and sequential collection fractions','measured crystalline core versus overall particle versus equivalent hydrodynamic size','post_treatment-dependent property states','detector resolution and multicomponent decay fits','chromatography calibration and aggregation','reported source conflicts with separate locators'],
 'chemicals':chemicals,'stocks':[{'id':'disilane-in-He','components':['disilane','helium'],'concentration':q(0.1,'%',2,'Experimental A'),'basis':'not explicitly specified'},{'id':'acidic-water','components':['sulfuric-acid','water'],'pH':q(1,None,5,'Results B'),'acid_concentration':None}],
 'shared_continuous_protocol':operations,'synthesis_variants':samples,'supporting_procedures':procedures,
 'table_I':{'evidence':[ev(2,'Table I')],'rows':table_rows,'notes':['Properties are cross-method formulation comparisons, not proof of one physical specimen used for every measurement.','Luminescence values are activated-sample values according to Results, not as-made colloid.']},
 'observations':observations,
 'figures':[item('figure-'+str(n),title,p,'Figure'+str(n),sample_scope=scope,caveat=note,disposition='original_crop_in_private_crop_assets;retain_measured_vs_model_labels',raw_curve_digitized=False) for n,p,title,scope,note in figures],
 'other_items':{'tables':['Table I'],'unnumbered_schemes':[],'display_equations':[],'references':{'count':47,'page':7,'status':'bibliography_and_footnotes_read; cited works not independently reviewed here','particularly_relevant':[29,30,31,33,34,35,36,37,38,40,41,44]}},
 'chemical_intuition':[
   item('high-temperature','Authors choose gas-phase high temperature because strongly covalentSi is harder to anneal than partiallyionicII–VI nanocrystals in coordinating solvents.',1,'Introduction',claim_type='author_rationale'),
   item('carrier','He is chosen becauseH2 depresses homogeneous nucleation;1.4atm reported to improve thermal conductivity and reduce aggregation/wallloss/contaminants.',2,'Experimental A',claim_type='author_rationale'),
   item('quench','Dilution/cooling limits continuing growth and aggregation before controlled surface oxidation.',2,'Experimental A',claim_type='author_rationale'),
   item('collection','EG chosen for silica affinity and low vapor pressure; prebubbler saturates gas withEG and reduces collector-volume drift/fritloss.',2,'Experimental A',claim_type='author_rationale'),
   item('HPLC-surface-chemistry','Authors propose that basic mobile phase ionizes surface hydroxyls on colloid and packing, reducing adsorption; high ionic strength screens repulsion so particles enter smaller pores.',2,'Experimental B',claim_type='author_rationale'),
   item('HPLC-column-stability','Nonaqueous mobile phase and silanized packing appear to slow silica-column degradation; calibration performance reported stable for several months.',7,'Reference36',claim_type='author_observation_and_interpretation'),
   item('surface-activation','Trap passivation by further oxidation and alteredFermi level are proposed explanations for acidic activation, not established mechanisms.',5,'Results B',claim_type='author_hypotheses'),
   item('confinement','Authors consider confinedSi states andSi/oxide-interface participation; polymeric/noncrystalline emitters remain possible for smallest particles.',6,'Results C',claim_type='author_hypotheses_and_limits'),
   item('outlook','Better sample-linked structural characterization and narrower distributions would help separate core size, surface chemistry and aggregation effects.',6,'Results C',claim_type='author_outlook')],
 'gaps':['MatchingSI not located/verified.','Pressure absolute/gauge basis and sccm standard reference conditions omitted.','Continuous collection duration and per-sample collected volume not specified.','Acidicwater5% basis and acid concentration omitted.','Frit silanization conditions missing.','AKS41 quantified synthesis not supplied.','1.0 crystallinity not directly established.','Individual batch/aliquot identities across techniques not fully resolved.','No experimental atomic coordinates/CIF.','Plots not digitized into raw data.','Cited upstream papers not imported as inspected experimental evidence.'],
}
path=OUT/'source-extraction.json'
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert len(data['figures'])==12 and len(data['table_I']['rows'])==3
assert data['training_eligible'] is False and data['website_published'] is False
assert data['table_I']['rows'][2]['XRD_coherence_nm']['value'] is None
assert data['shared_continuous_protocol'][1]['conditions']['residence_time']['unit']=='ms'
print(json.dumps({'source_sha256':data['source']['sha256'],'chemicals':len(chemicals),'quantified_flow_variants':3,'contextual_formulations':1,'procedures':len(procedures),'figures':len(figures),'status':data['status']}))
