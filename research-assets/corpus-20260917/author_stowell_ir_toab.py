"""One source-reviewed Ir recipe. Site helpers are imported read-only."""
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path('[local path redacted]')
OUT = ROOT / 'research-assets/corpus-20260917'
sys.path.insert(0, str(ROOT / 'recipe-atlas/scripts'))
from record_helpers import ev, fact, qty, source, record, material, state, operation, product, measurement

sid = 'stowell2005'
rid = 'stowell-2005-ir-toab-270c'
doi = '10.1021/nl050648f'
title = 'Iridium Nanocrystal Synthesis and Surface Coating-Dependent Catalytic Activity'
chem_e = ev(sid, 'Supporting Information PDF p. 1, Chemicals')
method_e = ev(sid, 'Supporting Information PDF p. 3, Tetraoctylammonium Bromide or Tetraoctylphosphonium Bromide Capped Iridium; TOAB branch only')
main_e = ev(sid, 'Main PDF p. 3, printed p. 1205, paragraph describing TOP-, TOAB- and TOPB-coated Ir syntheses')
tem_e = ev(sid, 'Main PDF p. 3, printed p. 1205, Figure 3A caption and TOAB size/crystallinity discussion')
cat_e = ev(sid, 'Main PDF p. 3, printed p. 1205, TOAB 1-decene conversion and turnover-frequency discussion, Eq. 2')
fig2_e = ev(sid, 'Main PDF p. 2, printed p. 1204, Figure 2 caption, TOAB-coated Ir series')
cat_method_e = ev(sid, 'Supporting Information PDF pp. 3–4, Catalysis and Gas Chromatography/Mass Spectroscopy; main printed p. 1204, batch hydrogenation conditions')

src = source(sid, doi, title, 'Cynthia A. Stowell and Brian A. Korgel', 2005,
             si='Matching 4-page SI: same title/authors, detailed recipes corresponding to the main article; SI pp. 1 and 3–4 visually verified')
src['main_status'] = 'Complete 5-page main text read; relevant complete printed pp. 1204–1205 visually verified'
r = record(rid, 'Stowell and Korgel (2005) · TOAB-capped iridium nanocrystals', 'Ir',
           'Noble-metal nanocrystals', 'Single-flask thermal reduction with 1,2-hexadecanediol',
           src, method_e[0]['locator'], kind='protocol_variant')
r['material'].update(elements=['Ir'], components=['Ir'], architecture='single_material')
r['collection'] = 'reviewed_literature'
r['lineage']['recipe_family'] = 'stowell2005-ir-toab'
r['intended_target']['composition']['note'] = 'Ir is the inorganic material; TOAB is the surface ligand, not an inorganic shell or alloy component.'
r['intended_target']['size']['basis'] = 'No prospective numerical size target is stated for this preparation.'
r['intended_target']['phase']['note'] = 'No prospective phase target; FCC characterization of a different ligand formulation is not inherited.'

def q(value=None, unit='', **kw):
    return qty(value, unit, evidence=method_e, **kw)

def purity(value):
    return qty(value, '%', evidence=chem_e, basis='Supplier purity reported by the authors; not an independent assay')

r['materials'] = [
    material('ir-mecp-cod', '(Methylcyclopentadienyl)(1,5-cyclooctadiene)iridium', 'C14H19Ir',
             'metal_precursor', 'synthesis', method_e + chem_e,
             {'mass': q(0.2, 'g', basis='Direct reactor charge'), 'purity': purity(99)},
             ['Supplier: Strem. Source condensed formula: (C6H7)(C8H12)Ir.',
              'Used without further purification, as specified in the Chemicals section.']),
    material('hexadecanediol', '1,2-Hexadecanediol', 'C16H34O2', 'reducing_agent', 'synthesis', method_e + chem_e,
             {'mass': q(0.2, 'g', basis='Direct reactor charge'), 'purity': purity(90)},
             ['Supplier: Aldrich; used without further purification.']),
    material('dioctyl-ether', 'Dioctyl ether', 'C16H34O', 'solvent', 'synthesis', method_e + chem_e,
             {'volume': q(7, 'mL', basis='Direct reactor charge'), 'purity': purity(97)},
             ['Supplier: Fluka (the specifically named chemical entry); used without further purification.',
              'Source condensed formula: [CH3(CH2)7]2O.']),
    material('toab', 'Tetraoctylammonium bromide (TOAB)', 'C32H68BrN', 'ligand', 'synthesis', method_e + chem_e,
             {'mass': q(0.76, 'g', basis='TOAB choice in the shared TOAB-or-TOPB method'), 'purity': purity(98)},
             ['Supplier: Aldrich; used without further purification.',
              'This record selects TOAB only. The equally weighted TOPB alternative is a different ligand formulation and is not mixed into this recipe.']),
    material('nitrogen', 'Nitrogen', 'N2', 'process_gas', 'synthesis', main_e,
             {'flow_rate': qty(None, 'mL/min', evidence=main_e, basis='The main text specifies nitrogen; flow rate is not reported for this formulation.')},
             ['Nitrogen environment at 270 °C is stated in the main article.']),
    material('ethanol', 'Ethanol', 'C2H6O', 'antisolvent', 'workup', method_e + chem_e,
             {'rinse_volume': q(None, 'mL', basis='One ethanol rinse is specified, without its volume.')},
             ['Solvents are stated to be analytical grade and purchased from Aldrich.',
              'The method deliberately limits ethanol exposure because repeated rinsing removes capping ligands.'])
]

# No separate stock solution is reported: all four nongaseous synthesis inputs are charged to one flask.
r['stocks'] = []
r['material_states'] = [
    state('ir-reaction-charge', 'Ir precursor/reductant/TOAB in dioctyl ether', ['ir-mecp-cod', 'hexadecanediol', 'dioctyl-ether', 'toab']),
    state('deoxygenated-ir-charge', 'Charge after three freeze–pump–thaw cycles', ['ir-reaction-charge']),
    state('ir-reaction-dispersion', 'Black reaction dispersion after heating', ['deoxygenated-ir-charge'], 'reaction_batch'),
    state('isolated-toab-ir', 'Ir particles isolated with one ethanol rinse', ['ir-reaction-dispersion', 'ethanol'], 'product')
]
r['operations'] = [
    operation('charge-one-flask', 'load', 'Charge the single three-neck round-bottom flask', method_e,
              ['ir-mecp-cod', 'hexadecanediol', 'dioctyl-ether', 'toab'], ['ir-reaction-charge'],
              parameters={'flask_capacity': q(25, 'mL'), 'flask_neck_count': q(3, 'count'),
                          'ir_precursor_mass': q(0.2, 'g'), 'reductant_mass': q(0.2, 'g'),
                          'dioctyl_ether_volume': q(7, 'mL'), 'toab_mass': q(0.76, 'g')},
              description='All four materials are measured into one flask. The source does not prescribe a separate injection feed, stock preparation, or detailed addition order.'),
    operation('deoxygenate-charge', 'freeze_pump_thaw', 'Deoxygenate with three freeze–pump–thaw cycles', method_e,
              ['ir-reaction-charge'], ['deoxygenated-ir-charge'], depends=['charge-one-flask'],
              parameters={'cycles': q(3, 'count'), 'vacuum_pressure': q(None, 'Pa'), 'freeze_temperature': q(None, '°C'), 'cycle_duration': q(None, 'min')},
              stage='precursor_preparation', description='The cycle count is specified; vacuum level, freeze/thaw temperatures, durations and backfill details are not.'),
    operation('heat-and-reduce', 'heat', 'Heat the TOAB formulation to form Ir nanocrystals', method_e + main_e,
              ['deoxygenated-ir-charge', 'nitrogen'], ['ir-reaction-dispersion'], depends=['deoxygenate-charge'],
              parameters={'temperature': q(270, '°C'), 'duration': q(30, 'min', qualifier='Reported heating duration; ramp/hold split not separately specified', raw_text='heated up to 270 °C for 30 minutes'),
                          'heating_rate': q(None, '°C/min'), 'stirring_rate': q(None, 'rpm'), 'pressure': q(None, 'Pa')},
              environment=fact('Nitrogen', main_e), endpoint=fact('Black liquid product', method_e),
              description='The main article identifies hexadecanediol reduction under nitrogen; the SI supplies the selected charge and 30 min heating condition.'),
    operation('single-ethanol-isolation', 'rinse_and_isolate', 'Isolate the particles with one ethanol rinse', method_e,
              ['ir-reaction-dispersion', 'ethanol'], ['isolated-toab-ir'], depends=['heat-and-reduce'],
              parameters={'rinse_count': q(1, 'count'), 'ethanol_volume': q(None, 'mL'), 'workup_temperature': q(None, '°C')},
              stage='workup', retained_fraction='isolated-toab-ir',
              description='The product particles are retained. The source does not identify a specific pellet/supernatant separation, centrifugation settings, cooling protocol or final redispersion volume. Repeated ethanol rinsing is not part of this selected protocol.')
]

nominal = product('toab-ir-method-product', 'Ir', method_e, link='explicit', state='isolated-toab-ir', surface='TOAB-capped',
                  notes=['Explicit link supports this named ligand formulation and product composition; no author batch ID or exact recipe-to-figure sample mapping is supplied.',
                         'The article reports crystalline TOAB-capped Ir. Its specific polymorph is not assigned from the OA/oleylamine XRD figure.'])
nominal['source_sample_label'] = 'TOAB-capped Iridium (SI method branch)'
nominal['phase'] = fact(evidence=tem_e, note='TOAB particles are described as crystalline; an explicit TOAB-specific FCC phase assignment is not supplied.')
tem = product('toab-ir-fig3a-context', 'Ir', tem_e, link='general_context', surface='TOAB-capped',
              notes=['TEM sample from the same ligand formulation; exact physical batch and purification lineage relative to the SI recipe are not stated.',
                     'Reported 1.5–3 nm is a diameter range, not a mean with an error bar or a size target.'])
tem['source_sample_label'] = 'Figure 3A (TOAB)'
cat = product('toab-ir-fig2-context', 'Ir', cat_e + fig2_e, link='general_context', surface='TOAB-capped',
              notes=['Catalysis sample described as approximately 1.5 nm; it is not asserted to be the identical Figure 3A sample or a uniquely identified batch of the SI preparation.',
                     'Measurements describe catalytic testing, not synthesis operating conditions.',
                     'The text and Figure 2 caption disagree on the turnover frequency; both source statements are retained separately, without averaging.'])
cat['source_sample_label'] = 'Figure 2 TOAB-coated Ir series (~1.5 nm)'
r['products'] = [nominal, tem, cat]
catalysis_conditions = ('1-Decene hydrogenation to decane at 75 °C and 3 psig H2; 1000:1 decene/Ir mass ratio. '
                        'SI reports a transient 70 °C temperature after injection followed by recovery to 75 °C after 1 min. '
                        'These are contextual assay conditions, not nanocrystal synthesis steps.')
r['measurements'] = [
    measurement('fig3a-diameter-range', tem['sample_id'], 'diameter',
                qty(unit='nm', minimum=1.5, maximum=3, evidence=tem_e, qualifier='Reported range; not mean ± spread', basis='TOAB-capped particles in Figure 3A'),
                'TEM', tem_e, conditions='Figure 3A and associated descriptive text; physical batch unspecified.'),
    measurement('fig2-catalyst-diameter', cat['sample_id'], 'diameter',
                qty(1.5, 'nm', evidence=cat_e + fig2_e, approximate=True, basis='Approximate diameter identifying the TOAB catalysis sample'),
                'TEM', cat_e + fig2_e, conditions='The body uses approximately 1.5 nm; Figure 2 labels 1.5 nm. General-context sample only.'),
    measurement('fig2-decene-conversion-230min', cat['sample_id'], '1_decene_conversion',
                qty(42, '%', evidence=cat_e, basis='Fraction of 1-decene converted after 230 min; stated in the body text'),
                'GC/MS', cat_e + cat_method_e, conditions=catalysis_conditions + ' Endpoint reported at 230 min.'),
    measurement('body-toab-turnover-frequency', cat['sample_id'], 'turnover_frequency',
                qty(4, 's^-1', evidence=cat_e, status='author_derived', qualifier='Body-text value conflicts with Figure 2 caption',
                    basis='Eq. 2 estimate assumes every surface Ir atom is an active site; actual active-site population is not measured'),
                'Author calculation from GC/MS and TEM size', cat_e, conditions=catalysis_conditions),
    measurement('fig2-caption-toab-turnover-frequency', cat['sample_id'], 'turnover_frequency',
                qty(5, 's^-1', evidence=fig2_e, status='author_derived', qualifier='Figure 2 caption value conflicts with body text',
                    basis='Published caption value, using the paper’s total-surface-atom convention; no reconciliation supplied'),
                'Author calculation from GC/MS and TEM size', fig2_e + cat_e, conditions=catalysis_conditions)
]
r['structure_assets'] = []
r['quality'].update(
    review_scope='One TOAB branch of a shared TOAB-or-TOPB literature method. Complete main and matching SI text read; main printed pp. 1204–1205 and SI pp. 1, 3–4 visually checked. Figure 3A and Figure 2 remain contextual samples. The record is not a reproduced experiment, an exact sample-CIF pair, or a complete SOP.',
    experimental_outcome='reported_product',
    missing_fields=[
        'Author batch IDs and exact physical pairing of the SI preparation with Figure 3A and the Figure 2 catalytic specimen.',
        'Reagent lot IDs, nitrogen purity/flow rate, vacuum level and freeze–pump–thaw temperatures/times/backfill details.',
        'Heating rate, ramp/hold split, stirring rate, pressure and cooling protocol before isolation.',
        'Ethanol rinse volume, exact physical separation method/settings, final redispersion solvent/volume, storage and isolated yield.',
        'A measured TOAB-specific atomic structure/CIF, explicit TOAB-specific phase assignment, and a resolved active-site population for TOF.'
    ],
    conflicts=[
        'TOAB turnover frequency is 4 s^-1 in the main p. 1205 body text but 5 s^-1 in Figure 2 caption on p. 1204. These are separate contextual source statements, not an uncertainty interval or duplicate independent trials.'
    ]
)
r['context_links'] = [{'label': 'Stowell and Korgel (2005), primary article and SI', 'url': 'https://doi.org/' + doi, 'relation': 'primary_source'}]

metadata = {
    'material_system': 'Ir', 'elements': ['Ir'], 'contains_materials': ['Ir'], 'architecture': 'single_material',
    'primaryrecordid': rid, 'source': {'source_id': sid, 'doi': doi, 'url': 'https://doi.org/' + doi,
                                     'title': title, 'authors': 'Cynthia A. Stowell and Brian A. Korgel', 'year': 2005},
    'surface_ligands': ['tetraoctylammonium bromide'],
    'scope': 'One explicitly selected TOAB synthesis condition; TOPB, TOP and oleic-acid/oleylamine variants are excluded.',
    'sample_linkage': 'Named protocol and composition are explicit. Figure 3A and Figure 2 product properties are contextual because no physical batch mapping is supplied.',
    'phase_note': 'Do not transfer Figure 1 FCC XRD or SAXS sizes from oleic-acid/oleylamine-coated particles to this TOAB record.',
    'public_source_url': 'https://doi.org/' + doi
}
audit = {
    'record_id': rid, 'main_si_match': {
        'verified': True, 'main_pages': 5, 'si_pages': 4,
        'basis': 'Matching exact title and authors; SI recipe headings, ligand formulations and characterization match main article. SI supplies the synthetic details explicitly referenced by the main.'},
    'selected_condition': {'ligand': 'TOAB', 'temperature_C': 270, 'reported_heating_duration_min': 30,
                           'scope': 'One single-flask formulation; no independently observed batch ID.'},
    'visually_verified_complete_pages': {'main_printed': [1204, 1205], 'si_pdf': [1, 3, 4]},
    'figure_audit': [
        {'source': 'Main Figure 1', 'disposition': 'Excluded from TOAB product labels', 'reason': 'Oleic-acid/oleylamine-coated particles: FCC XRD, size-selected TEM and SAXS fractions; wrong ligand formulation.'},
        {'source': 'Main Figure 2, TOAB series', 'disposition': 'Separate general-context catalytic sample', 'reason': 'Approximate 1.5 nm catalyst, 42% conversion at 230 min in body; TOF conflict 4 versus 5 s^-1 retained. No exact SI-run batch link.'},
        {'source': 'Main Figure 3A', 'disposition': 'Separate general-context TEM sample', 'reason': 'Explicit TOAB label and 1.5–3 nm range; no quantitative mean or exact batch mapping.'},
        {'source': 'Main Figures 3B–C and 5', 'disposition': 'Excluded', 'reason': 'Different ligand formulations (TOPB or TOP).'},
        {'source': 'Main Figure 4', 'disposition': 'Excluded from this initial product record', 'reason': 'TOAB catalyst recycling changes surface coverage, size and aggregation; successive cycles are not independent synthesis recipes.'}
    ],
    'not_invented': ['A separate injection or stock solution', 'A centrifuge speed or explicit pellet selection',
                     'An isolated yield or final storage condition', 'A size target', 'A measured CIF',
                     'A ligand shell classified as an inorganic core/shell architecture'],
    'source_specific_caveats': [
        'The OA/oleylamine recipe on SI p. 1 prints 0.08 and 0.085 microliters. That unselected formulation is not silently corrected or used here.',
        'SAXS radius/diameter wording and solvent differences in the unselected OA/oleylamine characterization are outside the selected record.',
        'TOF assumes all surface atoms are active despite ligand blocking; the authors acknowledge that approximation.'
    ]
}

(OUT / 'canonical').mkdir(parents=True, exist_ok=True)
for path, value in [(OUT / 'canonical' / (rid + '.json'), r),
                    (OUT / (rid + '-contribution.json'), metadata),
                    (OUT / (rid + '-source-audit.json'), audit)]:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(path)
