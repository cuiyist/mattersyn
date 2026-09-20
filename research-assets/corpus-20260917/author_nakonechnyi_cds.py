"""Author one source-reviewed core/shell record; reads Site helpers but writes outside Site."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path('[local path redacted]')
sys.path.insert(0, str(ROOT / 'recipe-atlas/scripts'))
from record_helpers import ev, fact, qty, source, record, material, state, operation, product, measurement

OUT = ROOT / 'research-assets/corpus-20260917'
(OUT / 'canonical').mkdir(parents=True, exist_ok=True)
sid = 'nakonechnyi2017'
rid = 'nakonechnyi-2017-zb-cdse-cds-seeded-growth'
doi = '10.1021/acs.chemmater.7b00354'
method_e = ev(sid, 'Main PDF p. 2, printed p. 4720, Experimental Section: zb-CdSe/CdS by Seeded Growth')
core_e = ev(sid, 'Main PDF p. 2, printed p. 4720, Experimental Section: Zinc Blende CdSe Core QDs')
fig_e = ev(sid, 'Main PDF pp. 3–4, printed pp. 4721–4722, Figure 1b caption and corresponding TEM discussion')
table_e = ev(sid, 'Main PDF p. 4, printed p. 4722, Table 1, zb-CdSe/CdS row and footnote')
phase_e = ev(sid, 'Supporting Information PDF p. 3, printed p. S3, section S2 and Figure S2b')
src = source(sid, doi, 'Mechanistic Insights in Seeded Growth Synthesis of Colloidal Core/Shell Quantum Dots',
             'Igor Nakonechnyi, Michael Sluydts, Yolanda Justo, Jacek Jasieniak, Zeger Hens', 2017,
             si='Matching main (9 pages) and SI (7 pages) reviewed; main pp. 4720–4722 and SI S3 visually verified for this extraction')
r = record(rid, 'Nakonechnyi et al. (2017) · Zinc-blende CdSe/CdS seeded growth',
           'CdSe/CdS', 'II–VI core/shell chalcogenides', 'Seeded growth by rapid core/sulfur coinjection', src,
           method_e[0]['locator'])
r['collection'] = 'reviewed_literature'
r['lineage'].update(recipe_family='nakonechnyi2017-cdse', parent_record_id='nakonechnyi-2017-zb-cdse-core')
r['intended_target']['composition']['note'] = 'Architecture label: CdSe core with CdS shell; slash notation is not a single stoichiometric compound.'
r['intended_target']['phase']['note'] = 'Observed zinc-blende phase is stored separately; no independent prospective phase specification is supplied.'
r['intended_target']['size']['basis'] = 'No numeric prospective size target for this named protocol.'

def q(v=None, u='', **kw):
    return qty(v, u, evidence=method_e, **kw)

r['materials'] = [
    material('cd-oxide', 'Cadmium oxide', 'CdO', 'metal_precursor', 'synthesis', method_e,
             {'amount': q(0.25, 'mmol', basis='Charge to three-neck reaction flask')}),
    material('oleic-acid', 'Oleic acid (OA)', 'C18H34O2', 'ligand', 'synthesis', method_e,
             {'amount': q(5.6, 'mmol', basis='Charge to three-neck reaction flask')},
             ['Used to form cadmium oleate in situ; free/bound acid speciation is not quantified.']),
    material('ode', '1-Octadecene (ODE)', 'C18H36', 'solvent', 'synthesis', method_e,
             {'reactor_volume': q(3.8, 'mL', basis='Initial reactor charge'),
              'feed_volume': q(1.12, 'mL', basis='Additional solvent for core/sulfur injection feed')}),
    material('cdse-seeds', 'Oleate-capped zinc-blende CdSe core quantum dots', 'CdSe', 'seed', 'synthesis', method_e + core_e,
             {'nanocrystal_amount': q(50, 'nmol', basis='Amount of CdSe core nanocrystals, not CdSe formula units'),
              'dispersion_volume': q(None, 'mL', basis='Volume/carrier solvent of the core dispersion entering the feed is not given')},
             ['Preparation context is the separately curated nakonechnyi-2017-zb-cdse-core record.',
              'The parent-record link represents preparation dependency, not verified identity of a physical core batch.',
              'No exact starting-core size is assigned to this feed from a separate TEM/Table 1 context.']),
    material('top-s', 'Trioctylphosphine sulfur (TOP-S) precursor', None, 'chalcogen_precursor', 'synthesis', method_e,
             notes=['Supplied as a 2 M solution; synthesis of this stock and its quantitatively specified solvent composition are not given in the selected method.']),
    material('nitrogen', 'Nitrogen', 'N2', 'process_gas', 'synthesis', method_e,
             {'flow_rate': q(None, 'mL/min', basis='Nitrogen flow during the 120 °C pretreatment; rate not specified')}),
    material('cadmium-oleate', 'Cadmium oleate formed in situ', None, 'intermediate', 'precursor_preparation', method_e,
             notes=['Formed by heating the CdO/OA/ODE charge; not a separately weighed, isolated stock.',
                    'Molecular speciation, conversion yield and concentration are not reported.']),
    material('toluene', 'Toluene', 'C7H8', 'dilution_solvent', 'characterization', method_e,
             {'volume_per_yield_aliquot': q(1, 'mL', basis='Each aliquot for chemical-yield study is put in this volume')}),
    material('ethanol', 'Ethanol', 'C2H6O', 'antisolvent', 'workup', method_e,
             {'initial_precipitation_volume': q(None, 'mL', basis='Initial ethanol precipitation of TEM samples'),
              'volume_per_purification': q(1, 'mL', basis='Each of the three TEM-sample purification cycles')}),
    material('hexane', 'Hexane', 'C6H14', 'solvent', 'workup', method_e,
             {'volume_per_purification': q(1, 'mL', basis='Each of the three TEM-sample purification cycles')})
]

r['stocks'] = [
    {'id': 'top-s-stock', 'name': '2 M TOP-S precursor solution',
     'components': [{'material_id': 'top-s', 'quantities': {}}],
     'concentrations': {'top_s_concentration': q(2, 'mol/L', basis='Reported concentration of supplied TOP-S solution', raw_text='2 M')},
     'preparation_operation_ids': [],
     'scope': 'Supplied stock; its preparation and quantitative solvent composition are not reported here. Only a 0.38 mL aliquot is used.',
     'evidence': method_e},
    {'id': 'core-sulfur-feed-stock', 'name': 'CdSe core/TOP-S injection feed in ODE',
     'components': [
         {'material_id': 'cdse-seeds', 'quantities': {'nanocrystal_amount': q(50, 'nmol', basis='Nanocrystal cores, not CdSe formula units')}},
         {'material_id': 'top-s', 'quantities': {'stock_aliquot_volume': q(0.38, 'mL', basis='Volume of the separately identified 2 M TOP-S solution')}},
         {'material_id': 'ode', 'quantities': {'volume': q(1.12, 'mL', basis='ODE added to make this injection feed')}}],
     'concentrations': {}, 'preparation_operation_ids': ['prepare-core-sulfur-feed'],
     'scope': 'Prepared while the reactor is conditioned; entire described feed is rapidly injected. Total measured feed volume is not specified.',
     'evidence': method_e}
]
r['material_states'] = [
    state('reactor-charge', 'CdO/OA/ODE charge in three-neck flask', ['cd-oxide', 'oleic-acid', 'ode']),
    state('conditioned-charge', 'Charge after nitrogen-flow pretreatment', ['reactor-charge']),
    state('hot-cadmium-oleate', 'Hot in situ cadmium-oleate reaction medium', ['conditioned-charge']),
    state('prepared-core-sulfur-feed', 'Prepared core/sulfur feed in ODE', ['core-sulfur-feed-stock'], 'stock'),
    state('seeded-growth-batch', 'CdSe/CdS seeded-growth reaction after injection', ['hot-cadmium-oleate', 'prepared-core-sulfur-feed'], 'reaction_batch'),
    state('tem-selected-sample', 'TEM sample, sampling time not specified in the generic method', ['seeded-growth-batch'], 'aliquot'),
    state('tem-precipitated-sample', 'Ethanol-precipitated TEM sample', ['tem-selected-sample', 'ethanol'], 'fraction'),
    state('tem-purified-sample', 'TEM sample after three solvent/nonsolvent purifications', ['tem-precipitated-sample', 'hexane', 'ethanol'], 'product')
]
sample_times = [(10, '10 s'), (30, '30 s'), (60, '1 min'), (90, '1 min 30 s'), (120, '2 min'), (180, '3 min'), (240, '4 min'), (300, '5 min'), (360, '6 min')]
for seconds, label in sample_times:
    r['material_states'].append(state(f'yield-aliquot-{seconds}s', f'{label} aliquot diluted in toluene', ['seeded-growth-batch', 'toluene'], 'aliquot'))

r['operations'] = [
    operation('charge-reactor', 'load', 'Charge a three-neck reaction flask', method_e,
              ['cd-oxide', 'oleic-acid', 'ode'], ['reactor-charge'],
              parameters={'cdo_amount': q(0.25, 'mmol'), 'oa_amount': q(5.6, 'mmol'), 'ode_volume': q(3.8, 'mL'), 'flask_capacity': q(None, 'mL')},
              description='Use the reactor amounts; the additional 1.12 mL ODE belongs to the separate injection feed.'),
    operation('condition-reactor', 'heat_under_gas_flow', 'Condition the charge under nitrogen flow', method_e,
              ['reactor-charge', 'nitrogen'], ['conditioned-charge'], depends=['charge-reactor'],
              parameters={'temperature': q(120, '°C'), 'duration': q(1, 'h'), 'pressure': q(None, 'Pa'), 'gas_flow_rate': q(None, 'mL/min')},
              environment=fact('Nitrogen flow', method_e)),
    operation('form-cadmium-oleate', 'heat_until_dissolved', 'Form cadmium oleate in situ', method_e,
              ['conditioned-charge'], ['hot-cadmium-oleate'], depends=['condition-reactor'],
              parameters={'temperature': q(260, '°C'), 'duration': q(None, 'min'), 'heating_rate': q(None, '°C/min')},
              endpoint=fact('Complete dissolution of CdO', method_e),
              description='The next injection is triggered by complete CdO dissolution. Gas conditions during this phase are not separately restated.'),
    operation('prepare-core-sulfur-feed', 'prepare_dispersion', 'Prepare the parallel CdSe core/TOP-S feed', method_e,
              ['cdse-seeds', 'top-s-stock', 'ode'], ['prepared-core-sulfur-feed'],
              parameters={'seed_amount': q(50, 'nmol', basis='Nanocrystal cores'), 'top_s_stock_volume': q(0.38, 'mL'), 'top_s_stock_concentration': q(2, 'mol/L'), 'ode_volume': q(1.12, 'mL'), 'temperature': q(None, '°C')},
              stage='precursor_preparation', branch='parallel-feed',
              description='The paper prepares this feed meanwhile; it is not required to wait for completion of reactor heating. No new CdSe core synthesis is implied.'),
    operation('inject-core-sulfur-feed', 'rapid_injection', 'Coinject CdSe cores and sulfur precursor', method_e,
              ['hot-cadmium-oleate', 'prepared-core-sulfur-feed'], ['seeded-growth-batch'], depends=['form-cadmium-oleate', 'prepare-core-sulfur-feed'],
              parameters={'reactor_temperature_at_injection': q(260, '°C'), 'injection_duration': q(None, 's', qualifier='Described qualitatively as rapid'), 'post_injection_temperature': q(None, '°C'), 'bulk_reaction_endpoint_time': q(None, 'min')},
              description='Injection starts the sampling clock. The method reports sampling through 6 min, but does not specify that 6 min is the final bulk reaction hold or quench time.'),
    operation('sample-yield-time-series', 'sample_and_dilute', 'Collect the chemical-yield aliquot time series', method_e,
              ['seeded-growth-batch', 'toluene'], [f'yield-aliquot-{t}s' for t, _ in sample_times], depends=['inject-core-sulfur-feed'],
              parameters={**{f'elapsed_time_{i+1}': q(t, 's', basis='Time after core/sulfur injection', raw_text=label) for i, (t, label) in enumerate(sample_times)},
                          'toluene_volume_per_aliquot': q(1, 'mL'), 'aliquot_volume': q(None, 'mL'), 'aliquot_mass': q(None, 'g')},
              stage='characterization', branch='yield-aliquots', optional=True,
              description='Nine related aliquots from a time series, not nine independent synthesis trials. Toluene dilution is reported; a quantitative bulk quench protocol is not.'),
    operation('select-tem-sample', 'take_sample', 'Select a sample for TEM workup', method_e,
              ['seeded-growth-batch'], ['tem-selected-sample'], depends=['inject-core-sulfur-feed'],
              parameters={'elapsed_time': q(None, 's', basis='Generic method does not name the selected TEM-sample time'), 'sample_volume': q(None, 'mL')},
              stage='characterization', branch='tem-workup', optional=True,
              description='Figure 1b separately names a 2 min high-OA specimen. That contextual specimen is not silently assigned to this generic workup branch.'),
    operation('precipitate-tem-sample', 'precipitate', 'Precipitate the TEM sample with ethanol', method_e,
              ['tem-selected-sample', 'ethanol'], ['tem-precipitated-sample'], depends=['select-tem-sample'],
              parameters={'ethanol_volume': q(None, 'mL')}, stage='workup', branch='tem-workup', optional=True),
    operation('purify-tem-sample', 'repeat_solvent_nonsolvent_purification', 'Purify the TEM sample three times', method_e + core_e,
              ['tem-precipitated-sample', 'hexane', 'ethanol'], ['tem-purified-sample'], depends=['precipitate-tem-sample'],
              parameters={'cycles': q(3, 'count'), 'hexane_volume_per_cycle': q(1, 'mL'), 'ethanol_volume_per_cycle': q(1, 'mL'),
                          'centrifugation_relative_force': qty(3000, 'g', evidence=core_e, status='inherited', basis='Relative centrifugal force; global Experimental Section statement applies here and afterward, not mass'),
                          'centrifugation_duration': q(None, 'min')},
              stage='workup', branch='tem-workup', optional=True,
              description='The shell paragraph specifies three hexane/ethanol purification cycles. The 3000 g setting is inherited from the earlier global centrifugation statement; individual cycle duration and detailed fraction transfers are not supplied.')
]

nominal = product('nominal-zb-cdse-cds-product', 'CdSe/CdS', method_e, link='explicit', state='seeded-growth-batch',
                  notes=['Explicit linkage applies to the named core/shell composition and protocol, not to an identified physical batch or exact numerical size.',
                         'This state is the reacting product dispersion; a final bulk isolated product/end time is not documented.',
                         'CdSe is the pre-existing core and CdS is the deposited shell.'])
nominal['source_sample_label'] = 'zb-CdSe/CdS by Seeded Growth (method heading)'
nominal['phase'] = fact(evidence=method_e, note='SAED phase is reported for the separately labeled SI Figure S2b context sample.')
fig = product('fig1b-zb-cdse-cds-context', 'CdSe/CdS', fig_e, link='general_context',
              notes=['Figure 1b is the high-OA, nominal OA/Cd 20:1 product after 2 min; exact physical batch link to the charged-quantity paragraph is not established.',
                     'The 2 min label describes this TEM specimen, not a prescribed endpoint for every run of the method.',
                     'Table 1 uses a conflicting shell-thickness heading for the same 8.6 ± 1.5 nm value; this measurement follows the body text, which calls it overall nanocrystal diameter.'])
fig['source_sample_label'] = 'Figure 1b (OA/Cd 20:1, 2 min)'
tab = product('table1-zb-cdse-cds-context', 'CdSe/CdS', table_e, link='general_context',
              notes=['Table row represents the reported material system, not an author-provided batch identifier.',
                     'Its physical sample identity relative to Figure 1b and SI Figure S2b is not explicitly established.'])
tab['source_sample_label'] = 'zb-CdSe/CdS (Table 1)'
saed = product('si-figs2b-zb-cdse-cds-context', 'CdSe/CdS', phase_e, link='general_context', phase='zinc blende',
               notes=['Overall nanocrystal phase assignment from SAED; not a separate resolved core/shell coordinate model or measured CIF.',
                      'Physical sample identity relative to the generic method, Figure 1b and Table 1 is not explicitly established.'])
saed['source_sample_label'] = 'zb-CdSe/CdS (SI Figure S2b)'
r['products'] = [nominal, fig, tab, saed]
r['measurements'] = [
    measurement('fig1b-overall-diameter', fig['sample_id'], 'diameter', qty(8.6, 'nm', evidence=fig_e, basis='Mean overall nanocrystal diameter; follows body text rather than conflicting Table 1 footnote'), 'TEM', fig_e,
                conditions='Figure 1b specimen after 2 min; OA/Cd described as 20:1; batch unspecified.'),
    measurement('fig1b-diameter-spread', fig['sample_id'], 'diameter_spread', qty(1.5, 'nm', evidence=fig_e, qualifier='Reported ± spread; spread type unknown', basis='Spread associated with the mean 8.6 nm overall diameter', raw_text='8.6 nm ± 1.5 nm'), 'TEM', fig_e,
                conditions='Co-reported with the mean diameter; not derived from that mean. Do not interpret as a standard error or confidence interval.'),
    measurement('table1-plqy', tab['sample_id'], 'photoluminescence_quantum_yield', qty(35, '%', evidence=table_e, basis='Table 1 zb-CdSe/CdS row'), 'Photoluminescence quantum-yield measurement', table_e,
                conditions='Table-level material-system context; body gives a typical approximate range of 30–35%; exact sampled time/batch is not specified here.')
]
r['quality']['experimental_outcome'] = 'reported_product'
r['quality']['review_scope'] = ('One named seeded-growth literature protocol, not a new independent experiment. Main and matching SI read; main printed pp. 4720–4722 and SI S3 visually checked. '
    'Parent record links CdSe-core preparation context, not a verified shared physical batch. Figure 1b, Table 1 and SI Figure S2b remain separate contextual sample records. '
    'Low-OA comparison reactions, blank controls, other core/shell compositions and simulation inputs are excluded.')
r['quality']['missing_fields'] = [
    'Author-assigned batch identity and exact pairing of the generic charged-quantity protocol with Figure 1b, Table 1 and SI Figure S2b.',
    'Preparation, quantitative carrier-solvent composition and purity of the supplied 2 M TOP-S stock.',
    'Exact physical parent CdSe-core batch, seed dispersion volume/carrier and core storage conditions.',
    'Reagent suppliers, purities/lots, flask capacity, stirring, heating rate, gas-flow rate and pressure.',
    'Duration to CdO dissolution, numeric injection duration, post-injection temperature trajectory, final bulk hold endpoint and quench.',
    'Aliquot masses/volumes; the generic TEM workup sampling time; initial ethanol precipitation amount.',
    'Individual centrifugation durations, detailed fraction transfers, final bulk isolation/redispersion and storage.',
    'An independently linked numerical shell thickness, statistical meaning of ±1.5 nm and exact-sample atomic coordinates/CIF.'
]
r['quality']['conflicts'] = [
    'The method charges 5.6 mmol OA and 0.25 mmol CdO (nominal charged OA/Cd = 22.4), whereas Figure 1/high-OA results use 20:1. Free-versus-total acid basis or rounding may differ; the source does not resolve the basis. Original charge values are preserved and characterization is not assumed to be exactly paired.',
    'The body identifies 8.6 ± 1.5 nm as mean overall nanocrystal diameter; Table 1 labels this value d_shell and its footnote says shell thickness. Only a contextual overall-diameter measurement following the body is retained; no measured shell thickness is asserted.'
]
r['context_links'] = [{'label': 'Nakonechnyi et al. (2017), original paper and supporting information', 'url': 'https://doi.org/' + doi, 'relation': 'primary_source'}]

metadata = {
    'material_system': 'CdSe/CdS', 'elements': ['Cd', 'Se', 'S'], 'contains_materials': ['CdSe', 'CdS'],
    'architecture': 'core_shell', 'primaryrecordid': rid,
    'source': {'source_id': sid, 'doi': doi, 'url': 'https://doi.org/' + doi, 'locator': method_e[0]['locator']},
    'components': [{'role': 'core', 'material': 'CdSe'}, {'role': 'shell', 'material': 'CdS'}],
    'parent_record_id': 'nakonechnyi-2017-zb-cdse-core',
    'parent_link_meaning': 'Preparation dependency only; physical seed batch is unknown.',
    'scope': 'One literature protocol contribution; not a new measured batch. Figure/table/SI sample contexts are separate and do not constitute additional independent recipes.',
    'recommended_schema_extensions': [
        'Add a controlled architecture field and ordered component roles outside the single formula label.',
        'Represent seed-parent preparation linkage separately from verified physical batch lineage.',
        'Add field-level condition/sample linkage so a source-family phase assignment cannot imply an exact recipe-to-size pairing.'
    ]
}

record_path = OUT / 'canonical' / (rid + '.json')
record_path.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / (rid + '-contribution.json')).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(record_path)
