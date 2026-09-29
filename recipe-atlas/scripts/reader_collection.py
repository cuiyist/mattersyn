"""Reader-facing inventory; documentation coverage never grants training eligibility."""
import re
from charge_coverage import quantified_inputs
from source_coverage import source_coverage


def known(value):
    return (isinstance(value, dict) and value.get('status') in {'reported', 'calculated', 'inherited', 'author_derived'}
            and any(value.get(k) is not None for k in ('value', 'minimum', 'maximum')) and bool(value.get('evidence')))


def pair_documentation(row, record, references):
    """A reproducible description of supplied fields, not a laboratory-completeness audit."""
    fields = {f['kind'] for f in row['product_structure_fields']}
    measures = row['structural_measurements']
    size = any(m.get('descriptor_field', '').startswith('size.') or
               any(term in m.get('descriptor_field', '') for term in ('dimensions', 'size', 'thickness', 'diameter'))
               for m in measures)
    input_coverage = quantified_inputs(record)
    quantified = len(input_coverage['material_ids'])
    operations = [o for o in record['operations'] if o.get('evidence')]
    params = [(k, v) for o in operations if o.get('stage')=='synthesis' for k, v in o.get('parameters', {}).items() if known(v)]
    temperature = any(re.search('temperature', k, re.I) for k, _ in params)
    duration = any(re.search('duration|time|dwell', k, re.I) for k, _ in params)
    detailed = quantified >= 2 and len(operations) >= 2 and temperature and duration
    cells = [ref['id'] for ref in references if record['record_id'] in ref.get('record_ids', [])
             and (ref.get('displayPolicy') != 'sample_context_choice' or row['sample_id'] in (ref['sampleContextIdsByRecord'].get(record['record_id'], []) if 'sampleContextIdsByRecord' in ref else ref.get('sample_context_ids', [])))]
    checks = {'quantified_recipe_and_ordered_conditions': detailed,
              'reported_phase': 'phase' in fields or any(m.get('property') == 'phase' for m in measures),
              'reported_morphology': 'morphology' in fields,
              'reported_dimensions': size,
              'reference_unit_cell_available': bool(cells)}
    return {'category': 'more_comprehensive' if all(checks.values()) else 'partial',
            'checks': checks, 'missing_categories': [k for k, v in checks.items() if not v],
            'reference_ids': cells, 'quantified_input_evidence': input_coverage,
            'qualification': 'Documentation categories only. A reference cell is not a measured sample structure; missing details, source conflicts and task-specific eligibility remain in the source record.'}


def collection_summary(records, pair_rows, references, preliminary=None):
    by_id = {r['record_id']: r for r in records}
    primary = {}
    for r in records:
        source = next(s for s in r['sources'] if s['id'] == r['lineage']['source_group'])
        primary.setdefault((source.get('doi') or source.get('url') or source['id']).lower(), source)
    # Use the same direct target definition as the material atlas. Component cross-links
    # and verbose, source-specific family strings must not create extra families.
    from build_atlas import synthesis_route
    systems = sorted({r['material']['formula'] for r in records if synthesis_route(r)})
    rows = []
    for pair in pair_rows:
        row = dict(pair)
        row['documentation'] = pair_documentation(pair, by_id[pair['record_id']], references)
        rows.append(row)
    complete = sum(r['documentation']['category'] == 'more_comprehensive' for r in rows)
    return {'schema_version': 'mattersyn.reader-collection/1',
            'material_families': len(systems), 'material_family_definition': 'Distinct directly synthesized material systems; component-only cross-links excluded.',
            'material_systems': systems, 'contributing_papers': len(primary),
            'source_coverage': source_coverage(records, preliminary),
            'synthesis_structure_pairs': len(rows), 'more_comprehensive_pairs': complete,
            'partial_pairs': len(rows) - complete,
            'count_definition': 'One source-supported recipe/condition variant linked to one identified product with structural evidence. Different conditions producing separately characterized samples count separately. Multiple measurements of that same record/sample do not add pairs. Cross-paper physical-sample deduplication is not complete.',
            'documentation_rubric': 'More comprehensive means at least two source-backed quantified synthesis inputs, two source-located operations, reported temperature and duration, sample-linked phase, morphology and dimensions, and an available reference unit cell. Partial pairs lack one or more of these categories. Neither category implies a complete laboratory SOP or training readiness.',
            'all_records': len(records),
            'experimental_series_rows': sum(r.get('collection') == 'published_benchmark' for r in records),
            'pairs': rows}
