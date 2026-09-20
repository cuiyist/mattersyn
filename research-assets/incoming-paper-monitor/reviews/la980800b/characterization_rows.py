"""Map the independently extracted Stiger rows without inventing physical specimens."""
from pathlib import Path
import json

B = Path(__file__).resolve().parent

def build_characterization(base, P, Q, F, E, measurement):
    draft = json.loads((B / 'characterization-draft.json').read_text(encoding='utf-8'))
    record = base('characterization', 'Structure, electrochemical response and source models',
                  'observation', 'Source-scoped characterization')
    def evidence(row):
        return [e for x in row['evidence'] for e in E(x['pdf_page'], x['locator'])]
    def sample_id(row):
        original = row['sample_id']
        return 'shared-' + '-and-'.join(original) if isinstance(original, list) else original
    groups = {}
    for row in draft['measurement_rows']:
        groups.setdefault(sample_id(row), []).append(row)
    for sid, rows in groups.items():
        ev = list({json.dumps(e, sort_keys=True): e for row in rows for e in evidence(row)}.values())
        physical_ag = sid.startswith(('figure5-', 'figure7-')) and sid != 'figure7-body-context' or sid == 'tem-saed-context'
        substrate = sid in {'etched-si-reference', 'npp-si-substrate', 'n-si-substrate'}
        composition = 'Ag nanocrystals on Si(100)' if physical_ag else 'Si(100) substrate' if substrate else None
        if sid == 'tem-saed-context':
            composition = 'Ag nanocrystals mechanically transferred from Si(100) to a carbon-supported gold TEM grid'
        nonphysical = any(row['scope_type'] in {'model_context', 'method_context', 'cited_context'} for row in rows)
        note = ('Source model, method or cited-reference context. This identifier is not an independently synthesized material, '
                'physical specimen, measured atomic structure or transferable particle-size target.') if nonphysical else (
                'Source figure, substrate, control or aggregate-series context only. This curator identifier is not an author batch ID; '
                'no same-particle or cross-instrument identity is inferred.')
        p = P(record, sid, sid.replace('-', ' '), composition=composition, e=ev,
              notes=[note, 'Original source scope: ' + '; '.join(dict.fromkeys(str(row['sample_id']) for row in rows))])
        p['source_sample_label'] = sid.replace('-', ' ')
        if sid == 'tem-saed-context':
            p['phase'] = F('FCC metallic silver', E(7, 'Figure 6 and Table 1'), status='author_derived',
                           note='SAED assignment for the transferred cohort only; pulse duration and exact AFM specimen identity are unreported.')
    derived = {'fitted', 'author_calculated', 'author_calculated_model', 'author_calculated_upper_bound',
               'author_assignment', 'author_interpretation', 'author_model_inference', 'author_model',
               'author_model_comparison', 'model_fit', 'author_derived', 'author_estimate', 'method_interpretation'}
    for row in draft['measurement_rows']:
        ev = evidence(row)
        basis = row['basis']
        status = 'author_derived' if basis in derived else 'reported'
        note = '; '.join(x for x in [row.get('source_condition'), row.get('caveat'),
                          'Evidence basis: ' + basis, 'Scope: ' + row['scope_type']] if x)
        if 'quantity' in row:
            q = row['quantity']
            qualifiers = []
            bound_notes = {
                'char-transient-fast-rise':'Less than 30 ms; upper bound, not equality.',
                'char-aqueous-instability':'Particles smaller than 5 nm; strict upper bound in the cited aqueous context.',
                'char-coverage-study-range':'Strict source range: 0.005 < equivalent monolayer coverage < 0.20; endpoints excluded.',
                'char-blank-transient-decay':'Within 3 ms; time bound for the stated decay, not an exact pulse duration.',
                'char-density-time-limit':'Pulse durations greater than 30 ms were not measured; study coverage limit, not a kinetic endpoint.'
            }
            if row['id'] in bound_notes:
                qualifiers.append(bound_notes[row['id']])
            if q.get('unit') is None:
                qualifiers.append('Unit not reported; no unit assigned.')
            if 'upper_bound' in row['property'] or 'lower_bound' in row['property']:
                qualifiers.append('Source bound, not equality; preserve the direction stated in the property and source note.')
            if row['id'].startswith('char-f5-') and row['id'].endswith('-charge') or row['id'] == 'char-coverage-calibration':
                qualifiers.append('mC/cm² as printed; unresolved conflict with µC/cm² in Figures 7 and 9.')
            value = Q(q.get('value'), q.get('unit') or '', e=ev,
                      minimum=q.get('lower_bound'), maximum=q.get('upper_bound'),
                      approximate=q.get('approximate', False), status=status,
                      raw_text=q.get('raw_text', ''), basis=basis, qualifier=' '.join(qualifiers))
        else:
            value = F(row['fact'], ev, status=status, note='Evidence basis: ' + basis)
        record['measurements'].append(measurement(row['id'], sample_id(row), row['property'], value,
                    row.get('method') or row['scope_type'].replace('_', ' ').capitalize(), ev, note))
    record['quality']['conflicts'] = [x['text'] for x in draft['conflicts_and_limitations']]
    record['quality']['missing_fields'] += draft['not_reported']
    record['quality']['requested_tasks'] = []
    record['quality']['experimental_outcome'] = 'not_established'
    for key, label in [('electrodeposition', 'Pulsed electrodeposition'), ('cyclic-voltammetry', 'Cyclic voltammetry'),
                       ('current-transients', 'Current-transient analysis'), ('afm', 'AFM analysis'),
                       ('tem-saed', 'TEM and SAED'), ('open-circuit-control', 'Open-circuit control'),
                       ('silver-free-pulse-control', 'Silver-free pulse control')]:
        record['context_links'].append({'label': label, 'url': '../records/stiger-1999-' + key + '.html',
                    'relation': 'Source-cohort or supporting-method association; physical specimen equality is not established.'})
    assert len(record['measurements']) == len(draft['measurement_rows']) == 143
    return record
