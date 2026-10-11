"""Count distinct primary papers represented in regular material pages."""
from html import escape


def source_coverage(records):
    """Count each primary paper once; supporting citations and variants do not add papers."""
    audited_ids, extracted_ids, audited_dois, extracted_dois = set(), set(), set(), set()
    for record in records:
        if record.get('collection') not in ('reviewed_literature','published_benchmark'):
            raise ValueError('Machine-extracted or unknown collections cannot contribute to audited paper counts')
        primary = next(s for s in record['sources'] if s['id'] == record['lineage']['source_group'])
        key = (primary.get('doi') or primary.get('url') or primary['id']).lower()
        extracted = record.get('quality', {}).get('review_status') == 'source_extracted'
        if extracted:
            from build_atlas import synthesis_route
            if not synthesis_route(record): continue
            extracted_ids.add(key)
            if primary.get('doi'): extracted_dois.add(primary['doi'].lower())
        else:
            audited_ids.add(key)
            if primary.get('doi'): audited_dois.add(primary['doi'].lower())
    extracted_ids -= audited_ids
    extracted_dois -= audited_dois
    return {
        'total_contributing_papers': len(audited_ids | extracted_ids),
        'reviewed_contributing_papers': len(audited_ids),
        'audited_contributing_papers': len(audited_ids),
        'machine_extracted_contributing_papers': len(extracted_ids),
        'audited_primary_dois': sorted(audited_dois),
        'source_extracted_primary_dois': sorted(extracted_dois),
        'count_definition': (
            'Distinct primary sources represented in regular material pages, separated by review status. '
            'Each paper counts once regardless of variants; supporting citations do not add papers. '
            'Source-extracted contributions are not independently audited or training eligible.'
        ),
    }


def coverage_note_html(coverage):
    return ('<p class="coverage-note">Each contributing primary paper counts once, '
            'irrespective of its number of recipes. Source locators, individual source '
            'scopes and missing information remain with the published records.</p>')


def collection_metrics_html(collection, css_class='library-summary inventory-metrics'):
    """Shared visitor counts; internal curation metadata remains separate."""
    coverage = collection['source_coverage']
    metrics = [(collection['material_families'], 'Material families'),
               (collection['synthesis_structure_pairs'], 'Recipe–structure pairs')]
    import json
    cards = '<div class="' + escape(css_class, quote=True) + '">'
    cards += ('<div><strong data-paper-total data-audited-papers="'
              + str(coverage['reviewed_contributing_papers'])
              + '" data-audited-primary-dois="' + escape(json.dumps(coverage['audited_primary_dois']), quote=True)
              + '" data-source-extracted-papers="' + str(coverage['machine_extracted_contributing_papers'])
              + '" data-source-extracted-dois="' + escape(json.dumps(coverage.get('source_extracted_primary_dois', [])), quote=True)
              + '">' + f"{coverage['total_contributing_papers']:,}" + '</strong><span>Papers</span></div>')
    cards += ''.join(f'<div><strong>{value:,}</strong><span>{label}</span></div>' for value, label in metrics)
    return cards + '</div>' + coverage_note_html(coverage)


def source_metrics_html(collection):
    coverage = collection['source_coverage']
    cards = '<div class="library-summary"><div><strong>' + str(coverage['total_contributing_papers']) + '</strong><span>Papers</span></div></div>'
    return cards + coverage_note_html(coverage)
