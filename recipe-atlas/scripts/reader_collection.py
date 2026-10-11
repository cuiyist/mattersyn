"""Reader-facing inventory; documentation coverage never grants training eligibility."""
import re
from copy import deepcopy
from charge_coverage import quantified_inputs
from source_coverage import source_coverage


def known(value):
    return (isinstance(value, dict) and value.get('status') in {'reported', 'calculated', 'inherited', 'author_derived'}
            and any(value.get(k) is not None for k in ('value', 'minimum', 'maximum')) and bool(value.get('evidence')))


def pair_documentation(row, record, references):
    """A reproducible description of supplied fields, not a laboratory-completeness audit."""
    fields = {f['kind'] for f in row['product_structure_fields'] if known(f.get('value'))}
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


def source_extracted_record_pairs(records, structural_policy=None):
    """One display row per record, including supporting/assembly records.

    This does not create an audited metric, structural assertion or training pair.
    Missing fields stay empty; values and their reported/inferred statuses are copied.
    """
    policy = structural_policy or {}
    allowed = set(policy.get('measurement_properties', []))
    mapping = policy.get('measurement_fields', {})
    rows = []
    for record in records:
        if record.get('quality', {}).get('review_status') != 'source_extracted':
            continue
        rid = record['record_id']
        product = next(iter(record.get('products', [])), {})
        sample_id = product.get('sample_id', '')
        source = next(s for s in record['sources'] if s['id'] == record['lineage']['source_group'])
        fields = [{'kind': kind, 'value': deepcopy(product[kind])} for kind in ('phase', 'morphology')
                  if isinstance(product.get(kind), dict) and product[kind].get('value') is not None]
        measures = [{'measurement_id': m['id'], 'property': m['property'],
                     'descriptor_field': mapping.get(m['property'], ''),
                     'value': deepcopy(m['value']), 'technique': m.get('technique', ''),
                     'conditions': m.get('conditions', ''), 'evidence': deepcopy(m.get('evidence', []))}
                    for m in record.get('measurements', []) if sample_id and m.get('sample_id') == sample_id
                    and m.get('property') in allowed and isinstance(m.get('value'), dict)
                    and any(m['value'].get(k) is not None for k in ('value', 'minimum', 'maximum'))]
        rows.append({'pair_row_id': rid + '::display', 'record_id': rid,
                     'record_page_path': 'records/' + rid + '.html',
                     'source_group': record['lineage']['source_group'], 'title': record['title'],
                     'doi': source.get('doi'), 'year': source.get('year'),
                     'method': record.get('method', ''), 'recipe_label': record['title'],
                     'sample_id': sample_id, 'source_sample_label': product.get('source_sample_label', ''),
                     'composition': deepcopy(product.get('composition', {})),
                     'recipe_link': product.get('recipe_link', ''),
                     'recipe_link_evidence': deepcopy(product.get('link_evidence', [])),
                     'product_structure_fields': fields, 'structural_measurements': measures,
                     'review_status': 'source_extracted', 'display_pair_basis': 'one_record',
                     'cross_record_sample_deduplication': 'not_assessed'})
    return rows


def collection_summary(records, pair_rows, references, structural_policy=None):
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
    display_rows = list(pair_rows) + source_extracted_record_pairs(records, structural_policy)
    for pair in display_rows:
        row = deepcopy(pair)
        row['documentation'] = pair_documentation(pair, by_id[pair['record_id']], references)
        rows.append(row)
    complete = sum(r['documentation']['category'] == 'more_comprehensive' for r in rows)
    return {'schema_version': 'mattersyn.reader-collection/1',
            'material_families': len(systems), 'material_family_definition': 'Distinct directly synthesized material systems; component-only cross-links excluded.',
            'material_systems': systems, 'contributing_papers': len(primary),
            'source_coverage': source_coverage(records),
            'synthesis_structure_pairs': len(rows),
            'audited_synthesis_structure_pairs': len(pair_rows),
            'source_extracted_record_pairs': len(display_rows) - len(pair_rows),
            'more_comprehensive_pairs': complete,
            'partial_pairs': len(rows) - complete,
            'count_definition': 'Audited recipe/sample rows retain their existing definition and identifiers. The display also includes one row per additional source-linked record, including supporting and assembly records. Missing product or structural details remain blank. Multiple measurements do not add rows. This display count does not grant training eligibility or establish independent physical batches.',
            'documentation_rubric': 'More comprehensive means at least two source-backed quantified synthesis inputs, two source-located operations, reported temperature and duration, sample-linked phase, morphology and dimensions, and an available reference unit cell. Partial pairs lack one or more of these categories. Neither category implies a complete laboratory SOP or training readiness.',
            'all_records': len(records),
            'experimental_series_rows': sum(r.get('collection') == 'published_benchmark' for r in records),
            'pairs': rows}
