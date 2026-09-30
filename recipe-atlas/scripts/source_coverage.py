"""Count distinct primary papers represented in regular material pages."""
from html import escape


def source_coverage(records):
    """Count each primary paper once; supporting citations and variants do not add papers."""
    primary_ids = set()
    for record in records:
        primary = next(s for s in record['sources'] if s['id'] == record['lineage']['source_group'])
        primary_ids.add((primary.get('doi') or primary.get('url') or primary['id']).lower())
    return {
        'total_contributing_papers': len(primary_ids),
        'reviewed_contributing_papers': len(primary_ids),
        'count_definition': (
            'Distinct primary source identifiers among papers represented in regular material pages. '
            'Each paper counts once regardless of recipe variants; supporting citations do not add papers.'
        ),
    }


def coverage_note_html(coverage):
    return ('<p class="coverage-note">Each contributing primary paper counts once, '
            'irrespective of its number of recipes. Individual source scopes and '
            'missing information are retained with the published records.</p>')


def collection_metrics_html(collection, css_class='library-summary inventory-metrics'):
    """Shared index/dataset/inventory cards for the regular published collection."""
    coverage = collection['source_coverage']
    metrics = [(coverage['reviewed_contributing_papers'], 'Contributing papers'),
               (collection['material_families'], 'Material families'),
               (collection['synthesis_structure_pairs'], 'Recipe–structure pairs')]
    cards = '<div class="' + escape(css_class, quote=True) + '">'
    cards += ''.join(f'<div><strong>{value:,}</strong><span>{label}</span></div>' for value, label in metrics)
    return cards + '</div>' + coverage_note_html(coverage)


def source_metrics_html(collection):
    """Library overview; the searchable reviewed list remains a separate collection."""
    coverage = collection['source_coverage']
    cards = '<div class="library-summary"><div><strong>' + str(coverage['reviewed_contributing_papers']) + '</strong><span>Contributing papers</span></div></div>'
    return cards + coverage_note_html(coverage)
