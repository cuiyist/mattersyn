"""Deduplicated public source coverage; never changes reviewed or training counts."""
from html import escape
from preliminary_contract import SCHEMA, validate_catalog


def source_coverage(records, preliminary=None):
    """Use only each canonical record's primary source, plus admitted preliminary DOIs."""
    catalog = preliminary if preliminary is not None else {'schema': SCHEMA, 'entries': []}
    errors = validate_catalog(catalog)
    if errors:
        raise ValueError('Invalid preliminary catalogue: ' + '; '.join(errors))
    reviewed = set()
    for record in records:
        primary = next(s for s in record['sources'] if s['id'] == record['lineage']['source_group'])
        # Match the existing contributing_papers identity rule exactly.
        reviewed.add((primary.get('doi') or primary.get('url') or primary['id']).lower())
    preliminary_ids = {e['doi'].lower() for e in catalog['entries']}
    return {
        'total_contributing_papers': len(reviewed | preliminary_ids),
        'reviewed_contributing_papers': len(reviewed),
        'preliminary_contributing_papers': len(preliminary_ids),
        'additional_preliminary_papers': len(preliminary_ids - reviewed),
        'overlapping_preliminary_papers': len(preliminary_ids & reviewed),
        'count_definition': 'Distinct primary source identifiers across the reviewed collection and the validated preliminary collection. A source present in both tiers counts once in the total. Supporting citations and multiple recipes do not add papers.',
        'tier_note': 'Reviewed collection retains its recorded source scopes, including selected recipes and published experimental series. Preliminary contributions are author-source-checked, independently unaudited, accuracy unmeasured and excluded from training. Preliminary entries do not add reviewed material families or recipe–structure pairs.'}


def coverage_note_html(coverage):
    reviewed = coverage['reviewed_contributing_papers']
    extra = coverage['additional_preliminary_papers']
    overlap = coverage['overlapping_preliminary_papers']
    note = (f'<p class="coverage-note"><strong>{reviewed:,} reviewed-collection papers</strong>'
            f' + <strong>{extra:,} additional preliminary papers</strong>. '
            '<a href="preliminary-synthesis.html">Explore preliminary synthesis contributions →</a>. '
            'Sources appearing in both tiers count once. ')
    if overlap:
        note += f'{overlap:,} preliminary source(s) also appear in the reviewed collection. '
    return note + ('Preliminary contributions await independent audit, have unmeasured accuracy and are excluded from training. '
                   'Material-family and recipe–structure-pair counts below refer only to the reviewed collection.</p>')


def collection_metrics_html(collection, css_class='library-summary inventory-metrics'):
    """Shared index/dataset/inventory cards with a separately qualified tier breakdown."""
    coverage = collection['source_coverage']
    metrics = [(coverage['total_contributing_papers'], 'Papers across all tiers'),
               (collection['material_families'], 'Reviewed material families'),
               (collection['synthesis_structure_pairs'], 'Reviewed recipe–structure pairs')]
    cards = '<div class="' + escape(css_class, quote=True) + '">'
    cards += ''.join(f'<div><strong>{value:,}</strong><span>{label}</span></div>' for value, label in metrics)
    return cards + '</div>' + coverage_note_html(coverage)


def source_metrics_html(collection):
    """Library overview; the searchable reviewed list remains a separate collection."""
    coverage = collection['source_coverage']
    metrics = [('total_contributing_papers', 'Papers across all tiers'),
               ('reviewed_contributing_papers', 'Reviewed-collection papers'),
               ('additional_preliminary_papers', 'Additional preliminary papers')]
    cards = '<div class="library-summary">'
    cards += ''.join(f'<div><strong>{coverage[key]:,}</strong><span>{label}</span></div>' for key, label in metrics)
    return cards + '</div>' + coverage_note_html(coverage)
