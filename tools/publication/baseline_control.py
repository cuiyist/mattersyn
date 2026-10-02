"""Derive the dataset baseline from reviewed, staged canonical record bytes.

Existing digest and task-eligibility approvals remain anchored to the previous
committed baseline. Only new membership and mechanical metadata are generated.
The final independent builder recomputes every row and checks this baseline.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import json
from pathlib import Path
import sys


BASELINE = 'recipe-atlas/data/release-baseline-manifest.json'
RECORD_PREFIX = 'recipe-atlas/data/records/'


def canonical_records(raw):
    paths = sorted(name for name in raw if name.startswith(RECORD_PREFIX) and name.endswith('.json'))
    records = []
    for name in paths:
        record = json.loads(raw[name])
        rid = name[len(RECORD_PREFIX):-5]
        if record.get('record_id') != rid:
            raise ValueError('Canonical record path/ID mismatch: ' + name)
        records.append(record)
    if len({record['record_id'] for record in records}) != len(records):
        raise ValueError('Duplicate canonical record ID')
    return records


def dataset_manifest(root, raw):
    """Project staged records with the same metadata functions as build_dataset."""
    scripts = Path(root) / 'recipe-atlas/scripts'
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from dataset_lib import build_groups, chemical_signature, digest, eligibility, validate_record
    from structure_recipe_metrics import recipe_structure_outcome_coverage

    records = canonical_records(raw)
    for record in records:
        errors = validate_record(record)
        if errors:
            raise ValueError('Canonical record validation failed: ' + '; '.join(errors[:5]))
    root_data = 'recipe-atlas/data/'
    task_policy = json.loads(raw[root_data + 'structure-task-policy.json'])
    # As in the isolated build, public assets resolve inside the static copy.
    task_policy['_asset_root'] = str(Path(root) / 'recipe-atlas/static')
    outcome_policy = json.loads(raw[root_data + 'structure-outcome-policy.json'])
    outcome_rows = recipe_structure_outcome_coverage(records, outcome_policy)['rows']
    pair_ids = defaultdict(list)
    for row in outcome_rows:
        pair_ids[row['record_id']].append(row['pair_row_id'])
    groups = build_groups(records)
    unique_groups = sorted(set(groups.values()))
    assign = {group: ('development' if len(unique_groups) < 10 else
                      'test' if int(digest(group)[:8], 16) % 10 == 0 else
                      'validation' if int(digest(group)[:8], 16) % 10 == 1 else 'train')
              for group in unique_groups}
    rows = []
    for record in records:
        rid = record['record_id']
        row = {
            'record_id': rid, 'title': record['title'],
            'formula': record['material']['formula'], 'family': record['material']['family'],
            'method': record['method'], 'record_type': record['record_type'],
            'source_year': record['sources'][0]['year'],
            'source_doi': record['sources'][0]['doi'],
            'revision': record['revision'], 'record_sha256': digest(record),
            'recipe_signature': chemical_signature(record),
            'group_id': groups[rid], 'split': assign[groups[rid]],
            'eligibility': eligibility(record, task_policy),
            'record_url': 'data/records/' + rid + '.json',
            'page_url': 'records/' + rid + '.html',
            'missing_field_count': len(record['quality']['missing_fields']),
            'collection': record.get('collection', 'reviewed_literature'),
            'components': record['material'].get('components', [record['material']['formula']]),
            'pair_ids': pair_ids[rid],
        }
        rows.append(row)
    families = sorted({record['material']['family'] for record in records
                       if record['record_type'] != 'procedure'})
    return {
        'schema_version': '1.0.0', 'dataset_version': '0.41.2',
        'record_count': len(records), 'group_count': len(unique_groups),
        'families': families,
        'split_policy': ('Connected source/recipe/parent/batch/duplicate components. '
                         'Development-only below ten groups. Split thresholds are deterministic '
                         'group hash 80/10/10, not a claim of balanced class coverage.'),
        'records': rows,
    }


def generate(root, raw, old_baseline, approved_digests, reviewed_changes,
             previous_approved_digests=None):
    """Retain all prior approvals; produce one current membership/count snapshot."""
    if not isinstance(old_baseline.get('records'), list):
        raise ValueError('Previous dataset baseline is invalid')
    old_rows = {row['record_id']: row for row in old_baseline['records']}
    if len(old_rows) != len(old_baseline['records']):
        raise ValueError('Duplicate previous dataset-baseline record')
    if old_baseline.get('record_count') != len(old_rows):
        raise ValueError('Previous dataset-baseline count is stale')
    if not isinstance(approved_digests, dict) or not isinstance(previous_approved_digests or {}, dict):
        raise ValueError('Approved record digests must be a mapping')
    previous_approved_digests = previous_approved_digests or {}
    projected = (dataset_manifest(root, raw) if canonical_records(raw) else copy.deepcopy(old_baseline))
    new_rows = {row['record_id']: row for row in projected['records']}
    if (len(new_rows) != len(projected['records']) or projected.get('record_count') != len(new_rows)
            or set(new_rows) != {record['record_id'] for record in canonical_records(raw)}):
        raise ValueError('Generated baseline count or canonical membership differs')
    for rid, old in old_rows.items():
        new = new_rows.get(rid)
        path = RECORD_PREFIX + rid + '.json'
        if new is None:
            if reviewed_changes.get(path, {}).get('decision') != 'delete':
                raise ValueError('Prior canonical record removed without exact deletion review: ' + rid)
            continue
        if old.get('eligibility') != new['eligibility']:
            raise ValueError('Prior record task eligibility changed: ' + rid)
        if old.get('record_sha256') != new['record_sha256']:
            newly_reviewed = reviewed_changes.get(path, {}).get('decision') == 'allow'
            previously_approved = previous_approved_digests.get(rid) == new['record_sha256']
            if approved_digests.get(rid) != new['record_sha256'] or not (newly_reviewed or previously_approved):
                raise ValueError('Prior record digest changed without exact approval: ' + rid)
            # Keep the original digest in the baseline; the final builder must
            # independently compare the approved override with built bytes.
        new['record_sha256'] = old['record_sha256']
        new['eligibility'] = copy.deepcopy(old['eligibility'])
    if set(approved_digests) - set(new_rows):
        raise ValueError('Approved digest names a noncanonical record')
    # Keep established row order stable. Canonical membership and content are
    # checked above; re-sorting thousands of unchanged rows needlessly rewrites
    # the approved baseline and obscures the substantive release diff.
    old_order = [row['record_id'] for row in old_baseline['records']
                 if row['record_id'] in new_rows]
    new_order = sorted(set(new_rows) - set(old_order))
    projected['records'] = [new_rows[rid] for rid in old_order + new_order]
    return projected
