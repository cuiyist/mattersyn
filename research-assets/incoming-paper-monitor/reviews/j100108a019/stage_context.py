"""Private contextual observation draft; does not invent an AKS41 synthesis."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r'[local path redacted]')
from record_helpers import ev, fact, qty, source, record, product, state, measurement

D = json.loads((HERE / 'source-extraction.json').read_text(encoding='utf-8'))
SID = 'littau1993'

def evidence(page, section):
    return ev(SID, f'Main PDF p. {page}, printed p. {1223 + page}, {section}')

src = source(SID, D['source']['doi'], D['source']['title'], '; '.join(D['source']['authors']), 1993,
             si='Not located or verified in either local collection; main-only scope.')
src['main_status'] = 'All seven supplied main pages reviewed; private contextual canonical draft awaits independent audit.'
r = record('littau-1993-aks41-context', 'Littau et al. (1993) · AKS41 contextual characterization',
           'Si/SiOx', 'Surface-oxidized silicon colloids',
           'Characterization of AKS41 from an earlier aerosol apparatus; synthesis not reconstructed',
           src, 'Main pp. 1226–1227, Results A and Figures 3–4', kind='observation')
r['collection'] = 'reviewed_literature'
r['material'].update(elements=['Si', 'O'], components=['Si', 'SiOx'], architecture='core_shell')
r['lineage']['recipe_family'] = 'littau1993-aks41-context'
r['intended_target'] = {
    'composition': fact(status='not_applicable', note='Contextual characterization; no prospective synthesis target reconstructed.'),
    'phase': fact(status='not_applicable', note='Observed phase is stored with the sample, not as a synthesis target.'),
    'size': qty(unit='nm', status='not_applicable', basis='Not a reconstructed synthesis.'),
    'morphology': fact(status='not_applicable', note='Not a reconstructed synthesis.')}
r['quality'].update(review_status='imported_unreviewed', requested_tasks=[], experimental_outcome='not_established',
    review_scope='Private contextual observation draft. No complete AKS41 synthesis, current-apparatus stock-flow assignment, training eligibility, reader integration or publication.',
    conflicts=['Figure 4 caption prints ASK41; surrounding prose and Figure 3 identify AKS41. This is not a second sample.',
               'The aggregate discussion on printed p. 1227 cross-references Figure 1, which is the apparatus; Figure 3 contains the aggregate TEM.'],
    missing_fields=['Earlier-apparatus AKS41 synthesis parameters and run history are not supplied as a reconstructable method.',
                    'Exact physical batch, collector fraction and figure-to-specimen identity beyond author AKS41 label remain unresolved.',
                    'No displayed electron-diffraction/SAED image or experimental atomic-coordinate model is supplied.',
                    'Matching SI is not located or verified.'])
r['material_states'] = [
    state('aks41-colloid', 'AKS41 colloid; earlier-apparatus context', [], kind='mixture'),
    state('aks41-imaged-particle', 'One lattice-resolved particle within the Figure 3 aggregate', ['aks41-colloid'], kind='aliquot'),
    state('aks41-excluded-fraction', 'AKS41 HPLC excluded aggregate fraction', ['aks41-colloid'], kind='fraction'),
    state('aks41-middle-fraction', 'AKS41 middle HPLC peak fraction', ['aks41-colloid'], kind='fraction'),
    state('aks41-monomer-fraction', 'AKS41 late monomer HPLC peak fraction', ['aks41-colloid'], kind='fraction')]

def add_sample(sample_id, state_id, label, note):
    e = evidence(4, 'Results A, AKS41 TEM and HPLC discussion')
    p = product(sample_id, 'Si/SiOx', e, link='general_context', state=state_id,
                phase='Diamond-lattice Si core',
                surface='Amorphous surface-oxide shell; atomic structure and exact oxide stoichiometry not established.',
                notes=[note, 'Contextual sample only; no verified synthesis recipe-to-outcome link.'])
    p['source_sample_label'] = label
    p['phase']['note'] = 'Author characterization of AKS41 crystallites; not proof for the separate 1.0 formulation.'
    p['surface']['note'] = 'The 1.5 nm shell measurement belongs to one depicted particle, not every AKS41 particle.'
    r['products'].append(p)

add_sample('aks41-population', 'aks41-colloid', 'AKS41', 'TEM population average and individual-particle measurements have separate sample IDs.')
add_sample('aks41-fig3-particle', 'aks41-imaged-particle', 'AKS41 (Figure 3 particle)', 'One fortuitously lattice-resolved particle in an aggregate; not the population mean. Schema state kind aliquot denotes a subset here, not a reported aliquoting operation.')
r['products'][-1]['parent_sample_id'] = 'aks41-population'
for suffix, label, description in [
    ('excluded', 'AKS41 excluded HPLC peak', 'Excluded peak contains aggregates tens of nanometers across.'),
    ('middle', 'AKS41 middle HPLC peak', 'Mostly dimers and trimers according to TEM of the fraction.'),
    ('monomer', 'AKS41 late HPLC peak', 'Mostly individual crystallites according to TEM of the fraction.')]:
    add_sample('aks41-'+suffix+'-sample', 'aks41-'+suffix+'-fraction', label, description)
    r['products'][-1]['parent_sample_id'] = 'aks41-population'
    for field in ['phase', 'surface']:
        r['products'][-1][field]['status'] = 'inherited'
        r['products'][-1][field]['note'] = ('Inherited parent-AKS41 characterization context; no independent fraction-specific '
            + field + ' determination is reported. The one depicted particle does not establish every fraction particle shell thickness.')

def add_value(mid, sample, prop, value, unit, technique, *, approximate=False, qualifier='', status='reported', basis='', conditions=''):
    e = evidence(4, 'Results A, AKS41 TEM and HPLC discussion')
    q = qty(value, unit, e, status=status, approximate=approximate, qualifier=qualifier, basis=basis)
    r['measurements'].append(measurement(mid, sample, prop, q, technique, e, conditions=conditions))

tem_conditions = ('Source preparation allows direct aerosol collection or colloid evaporation on holey carbon, '
                  'with JEOL 2000-FX at 200 keV; the exact branch for Figure 3 is not assigned.')
hplc_conditions = ('Sequential ZORBAX 60-S and 300-S, 50 °C, 0.75 cm3/min; reported 60:40 methanol/ethylene glycol '
                   'with 0.0015 M sodium methylate and 0.1 M tetrabutylammonium bromide. Equivalent hard-sphere '
                   'diameters use polymer calibration, not direct Si-core measurement. Solvent-ratio basis is unstated.')
add_value('population-tem-mean', 'aks41-population', 'mean_individual_particle_size', 14, 'nm', 'TEM',
          basis='Source wording: individual crystallite average size. This sentence does not explicitly distinguish outer diameter from core extent; do not reinterpret as a crystalline-core mean or the single Figure 3 particle.', conditions=tem_conditions)
add_value('population-tem-sd', 'aks41-population', 'particle_diameter_standard_deviation', 3, 'nm', 'TEM',
          basis='Population standard deviation, not measurement uncertainty on each particle.', conditions=tem_conditions)
add_value('fig3-core', 'aks41-fig3-particle', 'crystalline_core_diameter', 13, 'nm', 'Lattice-resolved TEM',
          basis='One lattice-resolved core in Figure 3.', conditions=tem_conditions)
add_value('fig3-shell', 'aks41-fig3-particle', 'amorphous_shell_thickness', 1.5, 'nm', 'TEM',
          basis='Shell width of the same single depicted particle, not a population-wide thickness.', conditions=tem_conditions)
add_value('fig3-fringes', 'aks41-fig3-particle', '111_lattice_plane_spacing', 3.1, 'angstrom', 'Lattice-resolved TEM',
          basis='Author-reported (111) spacing in the depicted crystalline-Si core.', conditions=tem_conditions)
for mid, sample, value, qualifier, approximate in [
    ('excluded-size', 'aks41-excluded-sample', 20, 'greater_than', False),
    ('middle-size', 'aks41-middle-sample', 16, '', True),
    ('monomer-size', 'aks41-monomer-sample', 11, '', True)]:
    add_value(mid, sample, 'equivalent_HPLC_diameter', value, 'nm', 'Size-exclusion HPLC',
              status='author_derived', approximate=approximate, qualifier=qualifier,
              basis=('Polymer-calibrated equivalent hard-sphere size; late fraction contains mostly individual crystallites.'
                     if sample == 'aks41-monomer-sample' else
                     'Polymer-calibrated equivalent hard-sphere size; aggregate-containing fraction.'), conditions=hplc_conditions)
add_value('exclusion-elution', 'aks41-excluded-sample', 'exclusion_elution_time', 8.0, 'min', 'Size-exclusion HPLC',
          basis='Total exclusion from the column pores.', conditions=hplc_conditions)

for m in r['measurements']:
    m['evidence'] += evidence(2, 'Experimental B, TEM and HPLC preparation/acquisition')
    if m['sample_id'] == 'aks41-fig3-particle':
        m['evidence'] += evidence(3, 'Figure 3')
    if m['technique'] == 'Size-exclusion HPLC':
        m['evidence'] += evidence(3, 'Figure 4')
r['products'][0]['notes'] += [
    'Prose reports intense narrow diamond-lattice electron-diffraction lines; there is no displayed SAED pattern to reproduce.',
    'HPLC reinjection retains each fraction elution time, supporting permanent aggregation rather than a simple core-size distribution.']
r['context_links'] = [{'label': 'Original paper', 'url': 'https://doi.org/10.1021/j100108a019', 'relation': 'source'}]
out = HERE / 'context-drafts'
out.mkdir(exist_ok=True)
path = out / (r['record_id']+'.json')
path.write_text(json.dumps(r, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'record': r['record_id'], 'measurements': len(r['measurements']),
                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'status': 'private_unaudited_context_draft', 'published': False}))
