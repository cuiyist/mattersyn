"""Count distinct primary papers represented in regular material pages."""
from html import escape


def source_coverage(records):
    """Count each primary paper once; supporting citations and variants do not add papers."""
    primary_ids, primary_dois = set(), set()
    for record in records:
        if record.get('collection') not in ('reviewed_literature','published_benchmark'):
            raise ValueError('Machine-extracted or unknown collections cannot contribute to audited paper counts')
        primary = next(s for s in record['sources'] if s['id'] == record['lineage']['source_group'])
        primary_ids.add((primary.get('doi') or primary.get('url') or primary['id']).lower())
        if primary.get('doi'): primary_dois.add(primary['doi'].lower())
    return {
        'total_contributing_papers': len(primary_ids),
        'reviewed_contributing_papers': len(primary_ids),
        'audited_contributing_papers': len(primary_ids),
        'machine_extracted_contributing_papers': 0,
        'audited_primary_dois': sorted(primary_dois),
        'count_definition': (
            'Distinct primary source identifiers among papers represented in regular material pages. '
            'Each paper counts once regardless of recipe variants; supporting citations do not add papers.'
        ),
    }


def coverage_note_html(coverage):
    return ('<p class="coverage-note">Each contributing primary paper counts once, '
            'irrespective of its number of recipes. Individual source scopes and '
            'missing information are retained with the published records. '
            'Audited counts cover the published source scopes, including core or partial reviews; '
            'they do not imply an independently audited complete paper. Machine-extracted counts '
            'require all five core fields unmasked and exclude papers already in the audited count.</p>')


def collection_metrics_html(collection, css_class='library-summary inventory-metrics'):
    """Shared index/dataset/inventory cards for the regular published collection."""
    coverage = collection['source_coverage']
    metrics = [(collection['material_families'], 'Material families'),
               (collection['synthesis_structure_pairs'], 'Recipe–structure pairs')]
    cards = '<div class="' + escape(css_class, quote=True) + '">'
    import json
    cards += ('<div><strong data-audited-papers="' + str(coverage['reviewed_contributing_papers'])
              + '" data-audited-primary-dois="' + escape(json.dumps(coverage['audited_primary_dois']), quote=True) + '">'
              + f"{coverage['reviewed_contributing_papers']:,} + "
              + '<b data-machine-papers>0</b></strong><span>Audited + machine-extracted papers</span></div>')
    cards += ''.join(f'<div><strong>{value:,}</strong><span>{label}</span></div>' for value, label in metrics)
    return cards + '</div>' + coverage_note_html(coverage)


def source_metrics_html(collection):
    """Library overview; the searchable reviewed list remains a separate collection."""
    coverage = collection['source_coverage']
    cards = '<div class="library-summary"><div><strong>' + str(coverage['reviewed_contributing_papers']) + '</strong><span>Contributing papers</span></div></div>'
    return cards + coverage_note_html(coverage)
