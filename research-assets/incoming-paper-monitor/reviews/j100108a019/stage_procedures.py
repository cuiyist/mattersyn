"""Private supporting-procedure staging for Littau 1993; never edits the Site.

These are procedure and observation contexts, not nine new synthesis recipes.
Canonical independent review, source-item coverage and reader integration remain open.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
SITE = Path(r'[local path redacted]')
sys.path.insert(0, str(SITE / 'scripts'))
from record_helpers import ev, fact, qty, source, record, material, operation, product, state, measurement
from dataset_lib import validate_record, eligibility

SID = 'littau1993'
D = json.loads((HERE / 'source-extraction.json').read_text(encoding='utf-8'))
OUT = HERE / 'procedure-drafts'
OUT.mkdir(exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protected = [HERE / 'stage_canonical.py', *sorted((HERE / 'canonical-drafts').glob('*.json'))]
before = {str(p): sha(p) for p in protected}


def E(page, section):
    return ev(SID, f'Main PDF p. {page}, printed p. {1223 + page}, {section}')


METHOD = E(2, 'Experimental B')
SRC = source(SID, D['source']['doi'], D['source']['title'], '; '.join(D['source']['authors']), 1993,
             si='Not located or verified in either local collection; no main-plus-SI completion claim.')
SRC['main_status'] = ('All seven supplied main pages read and visually checked; independent main-text/source-extraction audit exists. '
                      'These supporting-procedure canonical joins await independent review.')
LINK_NOTE = ('Source labels identify formulation families, not individually documented physical batches. '
             'Collector fraction, exact synthesis run and specimen identity across techniques are unresolved. '
             'No cross-record physical-specimen identity is asserted.')
CONFLICT_PL = ('Figure 9 caption reports 355 nm excitation; Results B on p. 1229 describes Figures 9–11 as 350 nm. '
               'Both are retained without selecting or averaging a setting.')
RECORDS = []
PROCEDURE_IDS = {}


def base(key, suffix, title, method, page, section, missing=(), conflicts=()):
    rid = 'littau-1993-si-' + suffix
    r = record(rid, 'Littau et al. (1993) · ' + title, 'Si/SiOx', 'Surface-oxidized silicon colloids',
               method, deepcopy(SRC), f'Main PDF p. {page}, {section}', kind='procedure')
    r['collection'] = 'reviewed_literature'
    r['material'].update(elements=['Si', 'O'], components=['Si', 'SiOx'], architecture='unresolved')
    r['lineage']['recipe_family'] = 'littau1993-si-aerosol'
    r['quality'].update(review_status='imported_unreviewed', requested_tasks=[], experimental_outcome='not_established',
                        review_scope=('Private supporting-procedure draft from fully read main source; independent canonical review, '
                                      'item-coverage reconciliation and reader integration pending. This is not a standalone synthesis or complete SOP. ' + LINK_NOTE),
                        missing_fields=['Matching SI not located or verified.', LINK_NOTE, *missing], conflicts=list(conflicts))
    # A characterization/workup context has no new prospective crystal-design target.
    for key2 in ['composition', 'phase', 'morphology']:
        r['intended_target'][key2] = fact(evidence=E(page, section), status='not_applicable',
                                         note='Supporting procedure; no prospective crystal-design target specified.')
    r['intended_target']['size'] = qty(unit='nm', evidence=E(page, section), status='not_applicable',
                                      basis='Supporting procedure; measured sizes are not prospective targets.')
    r['context_links'] = [{'label': 'Shared aerosol formulation contexts (6.0, 2.0, 1.0)',
                          'url': 'https://doi.org/10.1021/j100108a019',
                          'relation': 'Same source and formulation families; exact specimen/batch joins unresolved.'}]
    RECORDS.append(r)
    PROCEDURE_IDS[key] = rid
    return r


def mat(r, id, name, formula, role, e, stage='characterization', qs=None, notes=None):
    r['materials'].append(material(id, name, formula, role, stage, e, quantities=qs, notes=notes))


def st(r, id, name, parents=None, kind='mixture'):
    r['material_states'].append(state(id, name, parents, kind))
    return id


def prod(r, id, label, e, state_id=None, parent=None, notes=None, formula='Si/SiOx'):
    p = product(id, formula, e, link='general_context', state=state_id,
                notes=[LINK_NOTE, *(notes or [])])
    p['source_sample_label'] = label
    p['parent_sample_id'] = parent
    r['products'].append(p)
    return id


def op(r, id, action, label, e, inputs, outputs, *, params=None, depends=None, stage='characterization',
       branch='main', desc='', env=None, endpoint=None, retained=None, optional=False):
    r['operations'].append(operation(id, action, label, e, inputs, outputs, depends=depends,
                                     parameters=params, stage=stage, branch=branch, optional=optional,
                                     description=desc, environment=env, endpoint=endpoint, retained_fraction=retained))


def meas(r, id, sample, prop, q, technique, e, conditions):
    r['measurements'].append(measurement(id, sample, prop, q, technique, e, conditions))


# 1. Acid activation: three alternative formulation contexts, not one physical three-product batch.
ea = E(5, 'Results B, acidic reflux and pH dependence')
ep = E(6, 'Results B, activated luminescence and quantum-yield estimate')
r = base('acid-activation', 'acid-activation', 'Acid activation of silicon colloids',
         'Postsynthetic acidic reflux', 5, 'Results B',
         missing=['Basis and denominator of the 5% acidic-water addition; colloid starting volume; sulfuric-acid concentration/charge.',
                  'Argon flow, reflux pressure, addition sequence and any post-reflux purification are not reported.',
                  'Final mixture pH is not reported; pH 1 refers to the added acidic water.',
                  'Absolute QY is approximate; no per-run QY, uncertainties or raw calibration data.'], conflicts=[CONFLICT_PL])
mat(r, 'water', 'Water', 'H2O', 'acid_solution_solvent', ea, stage='workup')
mat(r, 'sulfuric-acid', 'Sulfuric acid', 'H2SO4', 'acid', ea, stage='workup',
    qs={'charge': qty(evidence=ea, basis='Acid charge/concentration not reported')})
mat(r, 'argon', 'Argon', 'Ar', 'atmosphere', ea, stage='workup')
mat(r, 'ethylene-glycol', 'Ethylene glycol', 'C2H6O2', 'colloid_medium', ea, stage='workup')
mat(r, 'r6g', 'R6G reference dye (counterion not specified)', None, 'quantum_yield_reference', ep,
    qs={'reference_quantum_yield': qty(0.9, 'fraction', ep, basis='Source-assumed R6G reference value, not a measured silicon-colloid yield')})
mat(r, 'ethanol', 'Ethanol', 'C2H6O', 'reference_dye_solvent', ep)
r['stocks'].append({'id': 'acidic-water', 'name': 'Added sulfuric-acid water at pH 1',
    'components': [{'material_id': x, 'quantities': {}} for x in ['water', 'sulfuric-acid']],
    'concentrations': {'pH': qty(1, 'pH', ea, basis='Added acidic water; not final colloid pH')},
    'preparation_operation_ids': [], 'scope': 'Preparation quantities and order are not supplied.', 'evidence': ea})
for label, peak in [('6.0', 970), ('2.0', 770), ('1.0', 660)]:
    slug = label.replace('.', 'p')
    feed = st(r, 'as-made-' + slug, f'As-made {label} colloid in ethylene glycol', ['ethylene-glycol'])
    activated = st(r, 'activated-' + slug, f'Acid-activated {label} colloid', [feed, 'acidic-water'], 'product')
    op(r, 'activate-' + slug, 'acid_reflux_activation', f'Acid-reflux the {label} formulation context', ea,
       [feed, 'acidic-water', 'argon'], [activated], stage='workup', branch='formulation-' + slug,
       params={'temperature': qty(200, 'degC', ea, approximate=True, qualifier='near'),
               'duration': qty(1, 'h', ea, approximate=True),
               'added_acidic_water_fraction': qty(5, '%', ea, basis='Fraction basis and denominator not stated'),
               'argon_flow': qty(evidence=ea, basis='Not reported'),
               'pressure': qty(evidence=ea, basis='Not reported; no reactor pressure transfer')},
       env=fact('Argon', ea), desc=('Alternative formulation template; not simultaneous treatment of all three formulations. '
       'Acidic reflux enhances luminescence. HPLC, TEM, UV and XRD showed no significant change; this does not prove unchanged atomic surface chemistry. '
       'Oxidation of residual traps and Fermi-level changes are proposed explanations, not measured mechanisms.'))
    p0 = prod(r, 'as-made-sample-' + slug, label, ea, feed, notes=['As-made input-state context; no activated PL assigned.'])
    p1 = prod(r, 'activated-sample-' + slug, label, ea + ep, activated, parent=p0,
              notes=['Activated state; exact physical run/fraction unresolved.',
                     'The 1.0 formulation has no directly established crystal-core structure.' if label == '1.0' else 'Phase not independently remeasured here.'])
    efig = E(5 if label == '6.0' else 6, 'Figure ' + {'6.0':'9','2.0':'10','1.0':'11'}[label])
    meas(r, 'activated-pl-peak-' + slug, p1, 'PL_emission_peak', qty(peak, 'nm', ep,
         qualifier='broad_peak_with_run_variation', basis='Reported peak after acidic activation; not an exact invariant'),
         'Steady-state photoluminescence', METHOD + ep + efig,
         'Room temperature; acid-activated formulation. ' + CONFLICT_PL + ' Which PL instrument recorded this curve is not fully specified.')
cohort = prod(r, 'activated-qy-cohort', 'Activated 6.0, 2.0 and 1.0 formulation cohort', ep,
              notes=['One shared estimate, not three independent measured QYs and not a pooled physical specimen.'])
meas(r, 'activated-qy-shared-estimate', cohort, 'PL_quantum_yield',
     qty(5, '%', ep, status='author_derived', approximate=True, qualifier='slightly_above_reference_value',
         raw_text='slightly above 5%', basis='5 is the quoted comparison threshold, not an exact measured point; upper bound/error unknown'),
     'Relative photoluminescence quantum-yield estimate', METHOD + ep,
     'All three activated colloids: initial-absorbance correction and integrated emission compared with dilute R6G in ethanol (reference QY 0.9). '
     'No physical batch or fraction joins resolved. pH above about 5 quenches room-temperature emission; second acidic reflux can partly restore it, '
     'while prolonged strong-base exposure can prevent recovery. Base identity, exposure duration and titration protocol not reported.')

# 2. Concentration is separate from powder drying.
ec = E(4, 'Results A, colloid concentration')
r = base('concentrate', 'colloid-concentration', 'Concentration of silicon colloids',
         'Vacuum concentration', 4, 'Results A', missing=['Vacuum level, duration, initial/final volumes and exact formulation/sample assignment.'])
st(r, 'colloid-feed', 'Colloid before concentration')
st(r, 'concentrated-colloid', 'Concentrated colloid', ['colloid-feed'], 'product')
op(r, 'concentrate', 'vacuum_concentration', 'Concentrate the colloid under vacuum', ec,
   ['colloid-feed'], ['concentrated-colloid'], stage='workup',
   params={'temperature': qty(80, 'degC', ec), 'concentration_factor': qty(unit='fold', minimum=5, maximum=10, evidence=ec),
           'duration': qty(unit='h', evidence=ec), 'vacuum_pressure': qty(evidence=ec)},
   env=fact('Vacuum; numerical pressure not reported', ec),
   desc='Mild concentration of the colloid; this 80 °C value is not a reported temperature for the distinct dry-powder procedure.')
prod(r, 'concentrated-colloid-context', None, ec, 'concentrated-colloid')

# 3. Dry-powder preparation. Repeated washing is not silently turned into a centrifuge recipe.
ed = METHOD
r = base('dry-powder', 'powder-preparation', 'Preparation of dry silicon-colloid powder',
         'Evaporation and repeated washing', 2, 'Experimental B',
         missing=['Numeric drying temperature, vacuum level and duration.',
                  'Wash order, number, volumes, separation device and final-drying details.',
                  'The typical mass is not a run-resolved synthesis yield.'])
mat(r, 'acetone', 'Acetone', 'C3H6O', 'wash_solvent', ed, stage='workup')
mat(r, 'ethylene-dichloride', 'Ethylene dichloride', 'C2H4Cl2', 'wash_solvent', ed, stage='workup')
st(r, 'colloid-feed', 'Unassigned colloid for dry-powder preparation')
st(r, 'paste', 'Paste after mild heated vacuum evaporation', ['colloid-feed'])
st(r, 'washed-powder', 'Deep-brown washed powder', ['paste'], 'product')
op(r, 'evaporate', 'vacuum_evaporation', 'Evaporate to a paste', ed, ['colloid-feed'], ['paste'], stage='workup',
   params={k: qty(evidence=ed, basis='Not numerically reported for this powder-preparation stage') for k in ['temperature','pressure','duration']},
   env=fact('Mild heating under vacuum', ed), endpoint=fact('Paste', ed),
   desc='Do not transfer the separate 80 °C colloid-concentration condition to this step.')
op(r, 'wash-paste', 'repeated_washing', 'Wash the paste repeatedly', ed,
   ['paste','acetone','ethylene-dichloride'], ['washed-powder'], depends=['evaporate'], stage='workup',
   params={k:qty(evidence=ed) for k in ['wash_count','acetone_volume','ethylene_dichloride_volume','separation_conditions']},
   endpoint=fact('Deep-brown powder', ed), retained='washed-powder',
   desc='Both solvents are named, but their sequence, mixing and separation procedure are not specified. No centrifugation speed or fabricated supernatant branch.')
p = prod(r, 'washed-powder-context', None, ed + E(7,'Reference 41'), 'washed-powder',
         notes=['Used subsequently for IR and powder XRD. It is not established which single batch supplies every later measurement.',
                'Note 41: powder before washing can show extra sharp XRD peaks and larger foreign crystallites; proposed small-molecule oxidation products were not identified.'])
meas(r, 'typical-small-crystallite-powder-mass', p, 'recovered_powder_mass_context',
     qty(10, 'mg', ed, qualifier='typically_at_most', basis='Typical powder amount for smaller crystallite sizes; not fixed batch output or chemical yield',
         raw_text='typically 10 mg or less for the smaller crystallite sizes'),
     'Reported preparation amount', ed, 'Generic smaller-size preparations; exact formulation and physical run not assigned.')

# 4. HPLC: analytical fractionation, calibration and explicit activated-fraction branch.
eh = METHOD
eh2 = E(6, 'Results B, HPLC fractions and reactivation')
r = base('HPLC', 'hplc-fractionation', 'Chromatographic characterization and fractionation',
         'Size-exclusion HPLC', 2, 'Experimental B',
         missing=['60:40 solvent ratio basis, injection volume/concentration, column dimensions and fraction collection schedule.',
                  'Polymer calibration molecular weights and exact equivalent-diameter calculation not reproduced.',
                  'Reactivation charge, duration, temperature and pressure are not separately specified for collected HPLC fractions.'])
for args in [('methanol','Methanol','CH4O','mobile_phase_solvent'),
             ('ethylene-glycol','Ethylene glycol','C2H6O2','mobile_phase_solvent'),
             ('sodium-methylate','Sodium methylate (sodium methoxide)','CH3ONa','mobile_phase_base'),
             ('tbab','Tetrabutylammonium bromide','C16H36BrN','mobile_phase_electrolyte'),
             ('polymer-calibrants','Polystyrene sulfonate sodium-salt polymers',None,'calibration_standard')]:
    mat(r, *args, eh)
mat(r,'reactivation-acid','Acid for fraction reactivation (identity not restated)',None,'reactivation_acid',eh2,
    stage='workup',notes=['Acidic reflux is stated; fraction-specific identity/charge are not separately supplied. Generic sulfuric-acid activation remains contextual.'])
r['stocks'].append({'id':'mobile-phase','name':'60:40 methanol:ethylene glycol mobile phase',
    'components':[{'material_id':x,'quantities':{}} for x in ['methanol','ethylene-glycol','sodium-methylate','tbab']],
    'concentrations':{'sodium_methylate':qty(1.5e-3,'mol/L',eh), 'tetrabutylammonium_bromide':qty(0.1,'mol/L',eh)},
    'preparation_operation_ids':[], 'scope':'Reported solvent ratio 60:40; mass/volume/mole basis and mixing order unstated.', 'evidence':eh})
st(r, 'colloid-feed', 'Unassigned colloid for HPLC')
st(r, 'separated-fractions', 'HPLC liquid fractions', ['colloid-feed','mobile-phase'], 'fraction')
op(r, 'calibrate', 'size_exclusion_calibration', 'Calibrate equivalent hard-sphere diameter', eh,
   ['polymer-calibrants','mobile-phase'], [],
   params={'flow':qty(0.75,'cm3/min',eh), 'temperature':qty(50,'degC',eh),
           'diameter_decrease_factor_for_one_minute':qty(1.72,'fold',eh,status='author_derived',basis='A one-minute elution-time increase corresponds to 1.72-fold smaller equivalent diameter; logarithmic mapping, not a linear rate'),
           'instrumental_fwhm':qty(0.4,'min',eh,status='author_derived',basis='Narrow-fraction reinjection'),
           'instrumental_diameter_factor':qty(1.24,'fold',eh,status='author_derived'),
           'total_exclusion_time':qty(8.0,'min',eh), 'total_exclusion_diameter':qty(20,'nm',eh,approximate=True,status='author_derived'),
           'molecular_size_elution_time':qty(14.8,'min',eh)},
   desc='Polymer Laboratories standards of different molecular weight; equivalent hard-sphere calibration under the same conditions as colloids. '
        'These are calibration descriptors, not nanoparticle synthesis outcomes.')
op(r, 'fractionate', 'size_exclusion_hplc', 'Analyze and collect time-resolved fractions', eh,
   ['colloid-feed','mobile-phase'], ['separated-fractions'], depends=['calibrate'], stage='fractionation',
   params={'flow':qty(0.75,'cm3/min',eh),'temperature':qty(50,'degC',eh),
           'injection_volume':qty(evidence=eh),'injection_concentration':qty(evidence=eh)},
   desc='HP 1090 with diode-array UV–vis detection; sequential ZORBAX 60-S and 300-S columns. '
        'Equivalent chromatographic dimensions can include permanent aggregates and are not crystalline-core sizes. '
        'Base is proposed to prevent adsorption by ionizing surface OH groups; electrolyte screening helps pore access. '
        'The analytical elution times are not synthesis residence times.')
prod(r, 'hplc-fraction-context', None, eh, 'separated-fractions',
     notes=['Table I formulation-specific metrics remain in the three aerosol drafts; no duplicates are generated here.'])
st(r, 'activated-feed', 'Activated colloid before basic HPLC; formulation unassigned')
st(r, 'quenched-particle-fraction', 'Nonluminescent particle-containing eluate at 8.5–12.5 min', ['activated-feed','mobile-phase'], 'fraction')
st(r, 'reactivated-fraction', 'Acid-reactivated particle fraction', ['quenched-particle-fraction','reactivation-acid'], 'product')
op(r, 'fractionate-activated', 'size_exclusion_hplc', 'Collect activated-colloid particle eluate', eh + eh2,
   ['activated-feed','mobile-phase'], ['quenched-particle-fraction'], depends=['calibrate'], stage='fractionation',
   branch='activated-colloid-control', params={'flow':qty(0.75,'cm3/min',eh),'temperature':qty(50,'degC',eh),
      'particle_fraction_elution_window':qty(unit='min',minimum=8.5,maximum=12.5,evidence=eh2)},
   desc='Alternative activated-input branch. Collected particles do not luminesce in the basic mobile phase; later-eluting molecular species are distinct.')
op(r, 'reactivate-fraction', 'acid_reflux_reactivation', 'Reactivate the particle-containing fraction', eh2,
   ['quenched-particle-fraction','reactivation-acid'], ['reactivated-fraction'], depends=['fractionate-activated'], stage='workup',
   branch='activated-colloid-control', params={k:qty(evidence=eh2,basis='Not separately specified for this HPLC-fraction reactivation')
           for k in ['temperature','duration','acid_charge','water_fraction','pressure']},
   desc='Acid reflux restores particle-fraction luminescence. The generic activation recipe provides context, but its numeric settings are not asserted here as fraction-specific measurements.')
p0=prod(r,'quenched-hplc-particle-fraction',None,eh2,'quenched-particle-fraction',notes=['Qualitative quenching; no numeric zero PL intensity is asserted.'])
prod(r,'reactivated-hplc-particle-fraction',None,eh2,'reactivated-fraction',parent=p0,notes=['Qualitative reactivation; no PL peak or QY assigned to this unresolved fraction.'])

# 5. TEM: preparation alternatives remain unassigned to individual observed specimens.
et = METHOD
et4 = E(4,'Results A, 6.0 TEM core and shell observations')
et5 = E(5,'Results A, 2.0 and 1.0 TEM limitations')
r=base('TEM','tem-characterization','Transmission electron microscopy','TEM specimen preparation and imaging',2,'Experimental B',
       missing=['Preparation route and HPLC fraction are not linked to each reported micrograph or quantitative specimen.',
                'Grid exposure/evaporation conditions, wash volume/count and exact identity of printed ethylene chloride.',
                'No original SAED pattern is displayed; diffraction rings are discussed only in prose.'])
mat(r,'holey-carbon','Holey-carbon film','C','TEM_support',et)
mat(r,'ethylene-chloride','Ethylene chloride (source wording; identity unresolved)',None,'fraction_wash_solvent',et,
    notes=['Do not silently equate with the separately printed ethylene dichloride powder-wash solvent.'])
for feed,name in [('aerosol-feed','Aerosol before grid collection'),('colloid-feed','Colloid for grid evaporation'),('hplc-feed','HPLC fraction for grid evaporation')]:
    st(r,feed,name)
st(r,'aerosol-grid','Aerosol collected directly on holey carbon',['aerosol-feed','holey-carbon'],'product')
st(r,'colloid-grid','Evaporated colloid on holey carbon',['colloid-feed','holey-carbon'],'product')
st(r,'fraction-grid','Evaporated HPLC fraction on holey carbon',['hplc-feed','holey-carbon'])
st(r,'washed-fraction-grid','HPLC-fraction grid after salt-removal wash',['fraction-grid'],'product')
op(r,'collect-aerosol','grid_deposition','Collect aerosol directly on the support',et,['aerosol-feed','holey-carbon'],['aerosol-grid'],branch='direct-aerosol',desc='Reported alternative; no source image is assigned to this branch by inference.')
op(r,'evaporate-colloid','grid_evaporation','Evaporate colloid on the support',et,['colloid-feed','holey-carbon'],['colloid-grid'],branch='colloid-evaporation')
op(r,'evaporate-fraction','grid_evaporation','Evaporate an HPLC fraction on the support',et,['hplc-feed','holey-carbon'],['fraction-grid'],branch='HPLC-fraction')
op(r,'wash-fraction-grid','grid_washing','Remove organic salt from the evaporated fraction',et,['fraction-grid','ethylene-chloride'],['washed-fraction-grid'],depends=['evaporate-fraction'],branch='HPLC-fraction',params={'wash_volume':qty(evidence=et),'wash_count':qty(evidence=et)},desc='Printed solvent identity is retained without an invented chemical structure.')
op(r,'tem-acquisition','electron_microscopy','Acquire TEM images',et,[],[],params={'electron_energy':qty(200,'keV',et)},
   desc='JEOL 2000-FX; the source permits alternative preparation routes but does not map each observed sample to a route. Inputs intentionally unresolved rather than pooled.')
p6=prod(r,'tem-6p0-context','6.0',et+et4,notes=['TEM observation context; route, fraction and exact physical specimen unresolved.'])
p2=prod(r,'tem-2p0-context','2.0',et+et5,notes=['Occasional resolved lattices are a biased subset and do not define the full core-size distribution.'])
meas(r,'tem-6p0-total-diameter-standard-deviation',p6,'total_particle_diameter_standard_deviation',qty(2.5,'nm',et4,status='author_derived'),
     'TEM',et+et4,'6.0 formulation; standard deviation about total-particle diameter, not FWHM or uncertainty of the mean.')
meas(r,'tem-6p0-oxide-shell-thickness',p6,'oxide_shell_thickness',qty(1.2,'nm',et4,status='author_derived',basis='Reported average oxide-shell thickness'),
     'Bright/dark-field TEM comparison',et+et4,'6.0 formulation; shell thickness, not total diameter; no crystalline SiO2 shell phase established.')
meas(r,'tem-6p0-core-total-diameter-ratio',p6,'core_to_total_diameter_ratio',
     qty(2/3,'ratio',et4,status='author_derived',raw_text='2/3',basis='Mean Si-core diameter divided by total particle diameter; not a volume fraction'),
     'Bright/dark-field TEM comparison',et+et4,'6.0 formulation; no systematic variation reported across 5–8 nm overall particle diameters.')
meas(r,'tem-2p0-occasional-lattice-core-size',p2,'lattice_resolved_core_diameter',
     qty(unit='nm',minimum=3,maximum=4,evidence=et5,qualifier='occasional_resolved_particles'),
     'Lattice-resolved TEM',et+et5,'2.0 formulation; occasional resolved Si lattice planes, not population-average size. Table I bright/dark-field ranges remain separate.')

# 6. IR powder state, not colloid or an invented Raman result.
ei=METHOD + E(4,'Figure 7 and Results A') + E(5,'Results A, IR continuation')
r=base('IR','ir-characterization','Infrared characterization of dry powder','KBr-pellet infrared spectroscopy',2,'Experimental B',
       missing=['KBr/sample loading, grinding/pressing conditions, instrument, spectral resolution and acquisition settings.'],
       conflicts=['Results A calls the X-ray plot Figure 5 when discussing the same 6.0 powder; actual XRD plot is Figure 6.'])
mat(r,'kbr','Potassium bromide','KBr','IR_matrix',METHOD,qs={'amount':qty(evidence=METHOD)})
st(r,'washed-powder','Washed dry colloid powder; upstream powder procedure is separate')
st(r,'kbr-pellet','Ground and pressed powder/KBr pellet',['washed-powder','kbr'],'product')
op(r,'press-pellet','grind_and_press','Grind sample and press a KBr pellet',METHOD,['washed-powder','kbr'],['kbr-pellet'],
   params={k:qty(evidence=METHOD) for k in ['KBr_amount','powder_amount','press_pressure','press_duration']},
   desc='Washed powder input; drying temperature is not inferred from colloid concentration.')
op(r,'record-ir','infrared_spectroscopy','Record the infrared spectrum',ei,['kbr-pellet'],[],depends=['press-pellet'],
   params={'resolution':qty(unit='cm^-1',evidence=ei)},desc='Figure 7 is 6.0 powder. Source reports near absence of the 2100 cm^-1 SiH feature; this is not quantitative zero hydrogen.')
p=prod(r,'ir-6p0-powder','6.0',ei,'kbr-pellet',notes=['Source identifies the same 6.0 powder as used for XRD, but physical run and XRD mounting alternative remain unresolved.',
    'Near-absent 2100 cm^-1 SiH band is retained qualitatively; no detection limit or numeric zero intensity.', 'No Raman data are reported.'])
for wn,assignment,page in [(1100,'strong band assigned by authors to SiO2',4),(800,'weak band assigned by authors to SiO2',4),
                           (3300,'OH stretch assignment',4),(1350,'wash-dependent; presumed residual organic species',5),(1700,'wash-dependent; presumed residual organic species',5)]:
    e=E(page,'Results A, IR interpretation and Figure 7')
    meas(r,f'ir-6p0-band-{wn}',p,'IR_band_position',qty(wn,'cm^-1',e,approximate=True,basis=assignment),
         'KBr-pellet infrared spectroscopy',METHOD+e,'6.0 washed dry powder; author-assigned band identity, not independently resolved molecular composition. Wash history for this specimen is not fully quantified.')

# 7. Powder XRD alternatives. Lattice comparison is not an exact experimental lattice parameter.
ex=E(3,'Experimental B continuation, powder XRD apparatus')
exr=E(5,'Results A, simultaneous least-squares lattice fit')
r=base('powder-XRD','xrd-characterization','Powder X-ray diffraction','Powder XRD with alternative mounts',3,'Experimental B continuation',
       missing=['AOT composition/charge, Mylar specification, mount assignment, scan range/step/time and detailed fit uncertainty.',
                'No experimental atomic coordinates or measured CIF; bulk reference lattice is not a measured nanocrystal structure.'])
mat(r,'aot','AOT soap (identity not expanded)',None,'powder_binder',ex,qs={'amount':qty(evidence=ex,basis='A small amount; numerical amount absent')})
mat(r,'mylar','Mylar film',None,'powder_encasement',ex)
mat(r,'optical-fiber','Optical fiber',None,'mechanical_mount',ex)
st(r,'powder-input','Washed dry colloid powder; upstream powder preparation separate')
st(r,'aot-bound-powder','Powder bound with AOT',['powder-input','aot'])
st(r,'mylar-powder','Powder encased in Mylar',['powder-input','mylar'])
st(r,'aot-fiber-mount','AOT-bound powder on optical-fiber tip',['aot-bound-powder','optical-fiber'],'product')
st(r,'mylar-fiber-mount','Mylar-encased powder on optical-fiber tip',['mylar-powder','optical-fiber'],'product')
op(r,'bind-aot','powder_mount_preparation','Bind powder with a little AOT',ex,['powder-input','aot'],['aot-bound-powder'],branch='AOT-mount')
op(r,'encase-mylar','powder_mount_preparation','Encase powder in Mylar',ex,['powder-input','mylar'],['mylar-powder'],branch='Mylar-mount')
op(r,'mount-aot','mechanical_mounting','Mount bound powder on optical-fiber tip',ex,['aot-bound-powder','optical-fiber'],['aot-fiber-mount'],depends=['bind-aot'],branch='AOT-mount')
op(r,'mount-mylar','mechanical_mounting','Mount encased powder on optical-fiber tip',ex,['mylar-powder','optical-fiber'],['mylar-fiber-mount'],depends=['encase-mylar'],branch='Mylar-mount')
op(r,'acquire-xrd','powder_diffraction','Acquire powder diffraction',ex,[],[],
   params={'rotating_anode_source_nominal_power':qty(12,'kW',ex,basis='Source described as a 12-kW rotating anode; actual operating power not separately supplied'),
           'operating_power':qty(unit='kW',evidence=ex)},
   desc='Triple-crystal spectrometer; Mo Kα radiation from Rigaku rotating-anode source; pyrolytic graphite monochromator and analyzer. '
        'Either mount may be used; the source does not assign each formulation to one mount. No combined two-mount specimen is asserted.')
for label in ['6.0','2.0']:
    slug=label.replace('.','p')
    p=prod(r,'xrd-'+slug+'-powder',label,ex+exr,notes=['Dry-powder context; exact mount unspecified.',
        'Figure 6 low-angle broad scattering contains binder and possible oxide contributions; an arbitrary Gaussian is a fit component, not a newly identified phase.'])
    meas(r,'xrd-'+slug+'-bulk-lattice-agreement',p,'lattice_parameter_relative_agreement_with_bulk',
         qty(0.25,'%',exr,status='author_derived',qualifier='within',basis='Agreement bound relative to bulk Si a0 = 5.43 Å; no exact nanocrystal lattice parameter reported'),
         'Simultaneous least-squares fit of powder-XRD line positions',METHOD+ex+exr,
         f'{label} dry powder; mounting alternative unresolved. This agreement is not size error or lattice strain measured as exactly 0.25%.')
p=prod(r,'bulk-si-lattice-reference','Bulk Si lattice reference',exr,formula='Si',notes=['Comparison constant cited by source, not a produced or independently measured sample.'])
meas(r,'bulk-si-reference-a0',p,'reference_lattice_parameter',qty(5.43,'angstrom',exr,basis='Source comparison value a0 for bulk Si; not measured nanocrystal lattice constant'),
     'Source-stated bulk reference',exr,'Reference only; no experimental CIF or atomic coordinates supplied.')

# 8. Optical acquisition and controls; activated peaks belong to the acid-activation record.
eo=METHOD
eo5=E(5,'Results B and Figure 9, as-prepared emission')
eo6=E(6,'Results B, bulk silicon comparison')
r=base('optical-acquisition','optical-characterization','Optical absorption and steady-state luminescence',
       'UV–vis and steady-state PL',2,'Experimental B',
       missing=['Per-curve PL instrument assignment, sample concentration, path length, slit settings and numeric room temperature.',
                'Exact liquid-helium temperature and bulk-Si control specimen identity.'], conflicts=[CONFLICT_PL])
st(r,'colloid-input','Colloid for steady-state optical acquisition; activation state must follow each observation')
op(r,'uv-vis','uv_vis_spectroscopy','Record UV–vis spectra',eo,['colloid-input'],[],
   desc='HP 8452A diode-array spectrometer. The weak tail and UV spectral-shape observations remain source-linked qualitative context; no unobserved indirect gap is converted into a measured bandgap.')
op(r,'pl-spex','steady_state_PL','Acquire spectra with SPEX Fluorolog 2',eo,['colloid-input'],[],branch='SPEX',
   params={'extended_red_response':qty(900,'nm',eo,approximate=True,basis='Approximate instrumental red response, not a sample emission cutoff')},
   desc='Instrument alternative. Both PL systems calibrated with tungsten lamp of known irradiance.')
op(r,'pl-long-wavelength','steady_state_PL','Acquire selected long-wavelength spectra',eo,['colloid-input'],[],branch='Jobin-Yvon',
   params={'reported_excitation':qty(355,'nm',eo)},
   desc='Jobin-Yvon HR640 with Ge photodiode detection; used for some spectra only. Do not assign this configuration to every curve. Both PL systems calibrated with tungsten lamp of known irradiance.')
# The source discrepancy is not a set of selectable experimental alternatives.
# Both source-labelled values remain in conflicts, observation notes and conditions.
p=prod(r,'as-made-6p0-optical','6.0',eo5 + E(6,'Results B, excitation for Figures 9–11'),
       notes=['As-prepared state. Does not inherit activated 970 nm peak or activated QY.',CONFLICT_PL])
meas(r,'as-made-6p0-weak-pl',p,'PL_emission_peak_region',qty(unit='nm',minimum=900,maximum=950,evidence=eo5,approximate=True,qualifier='broad_weak_peak_region'),
     'Steady-state photoluminescence',eo+eo5+E(6,'Results B, excitation for Figures 9–11'),
     'Room temperature; Figure 9 lower trace, as prepared. '+CONFLICT_PL)
p=prod(r,'bulk-si-optical-control','High-quality bulk crystalline Si',eo6,formula='Si',notes=['External comparison sample; not this synthesis product.',
    'No detectable room-temperature emission in the authors’ apparatus is qualitative; no zero intensity or detection threshold assigned.'])
meas(r,'bulk-si-low-temperature-emission',p,'PL_emission_peak',qty(1060,'nm',eo6,qualifier='sharp_line'),
     'Steady-state photoluminescence',eo6,'Bulk silicon reference at liquid-helium temperature; exact temperature unreported. Not room-temperature nanocrystal PL.')

# 9. Time-resolved PL: fitted multiexponential components, not a radiative lifetime label.
el=E(6,'Figure 12 and Results B, time-resolved luminescence')
r=base('time-resolved-PL','time-resolved-pl','Time-resolved luminescence of the 1.0 colloid',
       'Pulsed time-resolved PL',6,'Figure 12 and Results B',
       missing=['Exact pulse width within the picosecond regime, pulse energy/repetition rate and detection wavelength.',
                'Fit amplitudes, complete fit function, residuals, uncertainties and matched physical activation batch.',
                'Crystallinity of the 1.0 formulation is not structurally established.'])
st(r,'activated-1p0','Activated 1.0 colloid; earlier acidic reflux is contextual, not a new synthesis batch',kind='product')
op(r,'acquire-decay','time_resolved_PL','Acquire the luminescence decay',el,['activated-1p0'],[],
   params={'excitation_wavelength':qty(355,'nm',el), 'instrument_time_resolution':qty(10,'ns',el),
           'pulse_duration':qty(unit='ps',evidence=el,basis='Picosecond pulse stated; numerical pulse width not supplied')},
   env=fact('Room temperature; numerical value not supplied',el),
   desc='Photomultiplier plus digital storage oscilloscope; preliminary decay of the 1.0 colloid in activated-luminescence context. '
        'No crystal phase is inferred from decay. The source does not establish that these are purely radiative lifetimes.')
p=prod(r,'activated-1p0-decay','1.0',el+ea,'activated-1p0',notes=['Activated state is supported by the surrounding optical discussion; run/fraction identity remains unresolved.'])
for t in [17,76]:
    meas(r,f'activated-1p0-decay-component-{t}',p,'PL_decay_fit_component',
         qty(t,'us',el,status='author_derived',qualifier='major_multiexponential_component',basis='One of two stated major components of an adequate multiexponential fit'),
         'Time-resolved photoluminescence',el,'Room temperature; picosecond 355 nm excitation; 10 ns detection-system resolution. Same reported decay, not separate lifetime experiments; amplitude and uncertainty absent.')


def validate_semantics(records):
    by={r['record_id']:r for r in records}
    assert len(records)==9 and len(PROCEDURE_IDS)==9
    assert {p['id'] for p in D['supporting_procedures']}==set(PROCEDURE_IDS)
    for r in records:
        assert r['record_type']=='procedure' and r['quality']['review_status']=='imported_unreviewed'
        assert r['quality']['requested_tasks']==[] and not any(v['eligible'] for v in eligibility(r).values())
        assert all(p['batch_id'] is None and p['recipe_link']=='general_context' for p in r['products'])
        assert not r['structure_assets']
        assert 'AKS41' not in json.dumps(r) and 'ASK41' not in json.dumps(r)
        assert r['intended_target']['phase']['value'] is None
        assert not any(o['stage']=='synthesis' for o in r['operations'])
    drying=by[PROCEDURE_IDS['dry-powder']]
    assert drying['operations'][0]['parameters']['temperature']['value'] is None
    assert by[PROCEDURE_IDS['concentrate']]['operations'][0]['parameters']['temperature']['value']==80
    acid=by[PROCEDURE_IDS['acid-activation']]
    assert len([m for m in acid['measurements'] if m['property']=='PL_quantum_yield'])==1
    assert all(m['sample_id'].startswith('activated') for m in acid['measurements'])
    assert all(p['phase']['value'] is None for r in records for p in r['products'])
    time=by[PROCEDURE_IDS['time-resolved-PL']]
    assert {m['value']['value'] for m in time['measurements']}=={17,76}
    assert all(m['value']['status']=='author_derived' for m in time['measurements'])
    hplc=by[PROCEDURE_IDS['HPLC']]
    reactivation=next(o for o in hplc['operations'] if o['id']=='reactivate-fraction')
    assert all(q['value'] is None for q in reactivation['parameters'].values())


validate_semantics(RECORDS)
reports=[]
errors=[]
for r in RECORDS:
    issues=validate_record(r)
    errors.extend(issues)
    path=OUT/(r['record_id']+'.json')
    path.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    reports.append({'record_id':r['record_id'],'path':str(path),'sha256':sha(path),'schema_graph_errors':issues,
                    'operations':len(r['operations']),'products':len(r['products']),'measurements':len(r['measurements']),
                    'measurement_ids':[m['id'] for m in r['measurements']],'eligible_training_tasks':[]})
after={str(p):sha(p) for p in protected}
assert before==after, 'Protected root-owned artifacts changed during procedure staging.'
report={'status':'passed' if not errors else 'failed',
        'scope':'Schema/graph checks, targeted procedure-state invariants and disabled training gates. Independent scientific canonical audit pending.',
        'source_extraction_sha256':sha(HERE/'source-extraction.json'),'script_sha256':sha(Path(__file__)),
        'records':reports,'total_procedures':len(RECORDS),'total_measurements':sum(len(r['measurements']) for r in RECORDS),
        'protected_artifact_hashes':after,'protected_artifacts_unchanged':before==after,
        'publication':'None; private drafts only. No Site files were written.'}
(HERE/'procedure-drafts-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

lines=['# Littau 1993 supporting-procedure drafts','',
       'Nine private procedure records are staged. They are supporting workup/analysis contexts, **not nine new synthesis recipes**. '
       'All remain `imported_unreviewed`, request no training tasks, assert no physical batch identity and have no measured structure assets. '
       'The three root-owned aerosol drafts and their builder were not edited.','',
       f"Validation: **{report['status']}** for schema, graph and targeted state-separation checks. Independent scientific review is pending.",
       f"Measurement entries: **{report['total_measurements']}** (including explicitly marked reference/cohort observations).",'',
       '| Source procedure | Private record ID | Operations | Measurement entries |','|---|---|---:|---:|']
for key,rid in PROCEDURE_IDS.items():
    row=next(x for x in reports if x['record_id']==rid)
    lines.append(f"| {key} | `{rid}` | {row['operations']} | {row['measurements']} |")
lines.extend(['','## Scientific boundaries','',
    '- Acid-activation branches identify formulation contexts. PL peaks belong to activated products. The approximate QY statement is one shared cohort estimate, not three independent measurements.',
    '- The 5% addition has an unknown basis/denominator. pH 1 describes added water, not final colloid. Both 350/355 nm excitation statements remain.',
    '- The separate 80 °C concentration condition is not transferred into dry-powder preparation. Typical powder mass is not synthesis yield.',
    '- HPLC calibration and fractionation have their own parameters. Basic eluate and acid-reactivated fractions are separate states; fraction reactivation numeric settings remain unreported.',
    '- TEM preparation alternatives and XRD mounting alternatives are not silently assigned to individual observed specimens. Figure 3 / AKS41 is wholly outside this task and remains parent-owned.',
    '- IR uses washed dry powder/KBr. Near-absent SiH is qualitative, not zero hydrogen. No SAED image, Raman data or measured CIF is invented.',
    '- Lattice agreement is a bound relative to bulk reference; 5.43 Å is not an exact measured nanocrystal constant. The 1.0 phase remains unresolved.',
    '- The 17/76 microsecond values are author-derived components of one multiexponential decay, not independent or purely radiative lifetimes.',
    '', '## Exact remaining work', '',
    '1. Independently audit these generated records against all cited main pages and the earlier source extraction; close findings against regenerated hashes.',
    '2. Reconcile source item coverage with the parent-owned AKS41 record and all original figure/Table I assets. These drafts do not constitute full-paper canonical completion.',
    '3. General spectral-shape observations, model-based Mie concentration calibration, stability/aggregation prose, mechanistic hypotheses and follow-up limitations remain in source extraction/parent coverage review where not explicitly encoded here. Do not imply their omission from numeric fields means absent source information.',
    '4. Cross-record procedure-to-synthesis family context may be reused, but precise batch/fraction/physical-specimen joins remain unresolved. Viewer integration must not turn these shared templates into extra synthesis methods or count them as experimental batches.',
    '5. Resolve or preserve unclear chemical identities, render appropriate stage-specific scenes, integrate original figures with source/sample context, and review the complete reader page at CdSe quality. No Site or publication work occurred in this task.',
    '6. Keep training disabled until the root performs scoped review and explicit task-specific eligibility decisions. No SI has been located/verified; do not claim main-plus-SI completion.',
    '', '## Evidence and reproducibility', '',
    f"- Source extraction SHA-256: `{report['source_extraction_sha256']}`.",
    '- `stage_procedures.py` reproduces only this separate private `procedure-drafts` directory and its summary/validation artifacts.',
    '- `procedure-drafts-validation.json` records all output hashes, measurement IDs and protected root-owned artifact hashes.',
    '- No next paper was read, downloaded or processed.'])
(HERE/'procedure-drafts-summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'records':len(RECORDS),'measurements':report['total_measurements'],'errors':errors},indent=2))
assert not errors
