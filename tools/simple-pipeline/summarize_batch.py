#!/usr/bin/env python3
"""Read private checked pairs and emit metadata only; never infer publication or accuracy.

Uses the current converter, canonical schema and ordinary material-route predicate.
Five-field completeness is reported separately and does not change admission rules.
The input folder and all quotes remain private. Output contains no source fact values,
captions, excerpts, titles, author strings, private file paths or exception messages.
"""
from __future__ import annotations
import argparse
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

import to_site

CHECK = 'two passes agree, quotes found'
FIELDS = ('composition', 'precursor_with_amount', 'reaction_temperature', 'reaction_time', 'product_statement')


def normalized_doi(value):
    value = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', str(value or '').strip(), flags=re.I)
    value = re.sub(r'^doi:\s*', '', value, flags=re.I)
    pattern = (r'10\.\d{4,9}/[^\s"<>]+'
               r'(?:<[^<>\s",;]+::(?i:AID)-[^<>\s",;]+>\d+\.\d+\.(?i:CO);2-[A-Za-z0-9])?')
    return value.casefold() if re.fullmatch(pattern, value) else ''


def finite_number(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def five_fields(pair):
    recipe, structure = pair.get('recipe') or {}, pair.get('structure') or {}
    numeric_fact = lambda key: finite_number((recipe.get(key) or {}).get('value')) and bool((recipe.get(key) or {}).get('unit'))
    return {
        'composition': bool(str((structure.get('composition') or {}).get('value') or '').strip()),
        'precursor_with_amount': any(str(c.get('role') or '').lower() in ('metal source', 'anion source')
                                     and finite_number(c.get('amount')) and bool(c.get('unit'))
                                     for c in recipe.get('chemicals') or []),
        'reaction_temperature': numeric_fact('reaction_temperature'),
        'reaction_time': numeric_fact('reaction_time'),
        'product_statement': bool(str(pair.get('product') or '').strip()),
    }


class ProjectChecks:
    def __init__(self, repo):
        import jsonschema
        scripts = Path(repo) / 'recipe-atlas/scripts'
        sys.path.insert(0, str(scripts))
        from schema_definition import SCHEMA
        from build_atlas import synthesis_route, material_elements, slug
        self.validator = jsonschema.Draft202012Validator(SCHEMA)
        self.is_route, self.elements, self.material_id = synthesis_route, material_elements, slug

    def errors(self, record):
        if any(self.validator.iter_errors(record)):
            return ['schema_invalid']
        if not self.is_route(record):
            return ['no_synthesis_operation']
        if (record.get('material') or {}).get('elements') == []:
            return ['technical_unresolved_composition_for_navigation']
        try:
            self.elements(record)
        except (ValueError, KeyError, TypeError):
            return ['material_elements_invalid']
        return []


def baseline(site, checks):
    """Read the supplied site checkout as a baseline, not as anonymous deployment proof."""
    site = Path(site)
    dois, sources, counts = set(), {}, Counter()
    with (site / 'data/records.jsonl').open(encoding='utf-8-sig') as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            sid = (record.get('lineage') or {}).get('source_group')
            primary = next((s for s in record.get('sources') or [] if s.get('id') == sid), {})
            doi = normalized_doi(primary.get('doi'))
            if doi:
                dois.add(doi)
            if sid:
                sources[sid] = {'doi': doi, 'status': (record.get('quality') or {}).get('review_status')}
            if checks.is_route(record):
                counts[(record.get('material') or {}).get('formula') or ''] += 1
    index_path = site / 'data/materials-index.json'
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding='utf-8-sig'))
        for material in index.get('materials', []) if isinstance(index, dict) else index:
            # Earlier indexes call all ordinary routes reviewed_records; this is a
            # storage compatibility key, not a review claim about extracted rows.
            counts[material['formula']] = int(material.get('route_records', material.get('reviewed_records', 0)))
    return dois, sources, counts


def summary(documents, checks, known_dois=(), known_sources=None, existing_routes=None):
    known_dois = {normalized_doi(d) for d in known_dois if normalized_doi(d)}
    known_sources, existing_routes = known_sources or {}, existing_routes or {}
    seen, papers, totals = {}, [], Counter()
    for path, doc in documents:
        row = {'paper_id': to_site.slug(path.name.removesuffix('.pairs.json'), 120), 'doi': '', 'status': '',
               'generated_records': 0, 'eligible_records': 0, 'five_field_complete_records': 0,
               'figures_listed': 0, 'figure_files_found': 0, 'missing_figure_files': 0, 'records': []}
        papers.append(row)
        totals['papers_seen'] += 1
        if not isinstance(doc, dict):
            row['status'] = 'invalid_pair_json'; continue
        row['doi'] = normalized_doi(doc.get('doi'))
        figures = doc.get('figures') or []
        if not isinstance(figures, list):
            figures = []
        row['figures_listed'] = len(figures)
        for figure in figures:
            value = figure.get('file') if isinstance(figure, dict) else None
            try:
                found = isinstance(value, str) and bool(value) and (Path(value).is_file() or (path.parent / value).is_file() or (path.parent / 'figures' / value).is_file())
            except (OSError, ValueError):
                found = False
            row['figure_files_found' if found else 'missing_figure_files'] += 1
        if doc.get('check') != CHECK:
            row['status'] = 'not_two_pass_checked'; continue
        if not row['doi']:
            row['status'] = 'missing_or_invalid_doi'; continue
        if row['doi'] in seen:
            row['status'] = 'duplicate_doi_in_batch'; row['duplicate_of_paper_id'] = seen[row['doi']]; continue
        seen[row['doi']] = row['paper_id']
        if row['doi'] in known_dois:
            row['status'] = 'doi_already_in_site_baseline'; continue
        try:
            builder, records = to_site.records_of(doc)
            row['source_id'] = builder.source_id
            protected = known_sources.get(builder.source_id)
            if protected and (protected.get('status') != 'source_extracted' or protected.get('doi') != row['doi']):
                row['status'] = 'protected_source_identity'; continue
            row['generated_records'] = len(records)
            usable_pairs = [p for p in doc.get('pairs') or [] if ((p.get('recipe') or {}).get('steps') or (p.get('recipe') or {}).get('chemicals')) and to_site._composition_from(p) is not None]
            for record, pair in zip(records, usable_pairs):
                errors = checks.errors(record)
                formula = record['material']['formula']
                fields = five_fields(pair)
                previous = int(existing_routes.get(formula, 0))
                item = {'record_id': record['record_id'], 'eligible': not errors, 'hold_reasons': errors,
                        'material_id': checks.material_id(formula), 'existing_routes': previous,
                        'rare_material': previous < 3, 'five_fields_present': fields,
                        'five_field_complete': all(fields.values())}
                row['records'].append(item)
                row['eligible_records'] += not errors
                row['five_field_complete_records'] += not errors and all(fields.values())
            row['status'] = ('ready_for_conversion' if row['eligible_records'] else
                             'no_route_eligible_record' if records else 'no_usable_pairs')
        except (ValueError, KeyError, TypeError, IndexError, AttributeError):
            # Never echo a private fact, quote or raw exception to a public report.
            row['status'] = 'conversion_or_metadata_error'
            row['eligible_records'] = row['five_field_complete_records'] = 0
            for item in row['records']:
                item['eligible'] = False
                item['hold_reasons'] = ['conversion_or_metadata_error']
    for row in papers:
        totals['status:' + row['status']] += 1
        for key in ('generated_records', 'eligible_records', 'five_field_complete_records',
                    'figures_listed', 'figure_files_found', 'missing_figure_files'):
            totals[key] += row[key]
        totals['eligible_papers'] += row['eligible_records'] > 0
        totals['five_field_complete_papers'] += row['five_field_complete_records'] > 0
        totals['rare_material_records'] += sum(r['eligible'] and r['rare_material'] for r in row['records'])
        for field in FIELDS:
            totals['eligible_records_with:' + field] += sum(r['eligible'] and r['five_fields_present'][field] for r in row['records'])
    return {'schema_version': 'simple-batch-metadata-v1', 'scope': 'post-check candidates; no publication or scientific acceptance claim',
            'five_field_completeness_is_admission_gate': False, 'totals': dict(totals), 'papers': papers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pairs'); parser.add_argument('--repo', required=True); parser.add_argument('--site', required=True)
    parser.add_argument('--out', help='metadata-only JSON report; private input path is not stored')
    args = parser.parse_args()
    checks = ProjectChecks(args.repo)
    dois, sources, routes = baseline(args.site, checks)
    documents = []
    for path in sorted(Path(args.pairs).glob('*.pairs.json')):
        try:
            doc = json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError):
            doc = None
        documents.append((path, doc))
    result = summary(documents, checks, dois, sources, routes)
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps(result['totals'], indent=2))


if __name__ == '__main__':
    main()
