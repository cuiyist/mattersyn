"""Coordinate inventory, documentary linkage and audited task readiness are distinct.

No scientific requirements are inferred from operation names, material names or
missing-field prose. A trusted, independently reviewed task profile is mandatory
for admission. Empty/missing policy means no exact_structure_recipe exports.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote

TASK = 'exact_structure_recipe'
REPRESENTATIONS = {'molecular_structure', 'experimental_periodic_structure', 'finite_sample_structure'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def pointer(value, path):
    if not isinstance(path, str) or not path.startswith('/'):
        raise ValueError('Expected a non-root JSON pointer')
    for key in path[1:].split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def typed_fields(value, path=''):
    if isinstance(value, dict):
        if 'status' in value and 'value' in value:
            yield path, value
        else:
            for key, item in value.items():
                yield from typed_fields(item, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from typed_fields(item, path + '/' + str(index))


def known(value):
    """Reported zero/bounds are known; missing, inferred or conflicting values are not."""
    if not isinstance(value, dict) or value.get('status') not in {'reported', 'calculated', 'inherited'}:
        return False
    present = value.get('value') is not None or value.get('minimum') is not None or value.get('maximum') is not None
    return present and bool(value.get('evidence'))


def profile_shape_valid(profile):
    strings = ['id', 'task', 'record_id', 'record_sha256', 'sample_id', 'scope']
    if any(not isinstance(profile.get(k), str) or not profile[k] for k in strings):
        return False
    if any(not isinstance(profile.get(k), dict) for k in ['review', 'selection', 'coordinate_validation']):
        return False
    lists = [profile.get('structure_asset_ids')] + [profile['selection'].get(k) for k in ['materials', 'stocks', 'material_states', 'operations', 'condition_options']]
    if any(not isinstance(v, list) or any(not isinstance(x, str) for x in v) for v in lists):
        return False
    for key in ['field_decisions', 'missing_fields_decisions', 'conflicts_decisions']:
        if not isinstance(profile.get(key), list) or any(not isinstance(x, dict) for x in profile[key]):
            return False
    if any(not isinstance(x.get('pointer'), str) for x in profile['field_decisions']):
        return False
    for key in ['missing_fields_decisions', 'conflicts_decisions']:
        if any(not isinstance(x.get('index'), int) or isinstance(x.get('index'), bool) or not isinstance(x.get('text'), str) for x in profile[key]):
            return False
    return isinstance(profile['coordinate_validation'].get('asset_sha256'), dict)


def load_structure_policy(root):
    path = Path(root) / 'data/structure-task-policy.json'
    if not path.exists():
        return {'schema_version': '1.0', 'asset_qualifications': {}, 'task_profiles': {}}
    policy = json.loads(path.read_text(encoding='utf-8'))
    if policy.get('schema_version') != '1.0' or not isinstance(policy.get('task_profiles'), dict) or not isinstance(policy.get('asset_qualifications'), dict):
        raise ValueError('Invalid structure-task policy; exact export cannot continue')
    policy['_asset_root'] = str(Path(root) / 'dist')
    return policy


def coordinate_inventory(record, policy=None, asset_root=None):
    """Read canonical sample-coordinate links; references/illustrations never enter.

    available=None means reachability was not tested (e.g. no filesystem root or
    external URL). Presence of a URL alone is not a successful download/geometry check.
    """
    policy = policy or {}
    asset_root = asset_root if asset_root is not None else policy.get('_asset_root')
    samples = {p['sample_id']: p for p in record['products']}
    rows = []
    for asset in record['structure_assets']:
        if asset['role'] != 'measured_sample':
            continue
        sample = samples.get(asset['sample_id'])
        row = {'asset_id': asset['id'], 'url': asset['url'], 'sample_id': asset['sample_id'],
               'source_group': record['lineage']['source_group'], 'sample_resolved': sample is not None,
               'available': None, 'asset_sha256': None, 'representation': 'unclassified',
               'label': asset['id'], 'eligible_as_measured_label': asset['eligible_as_measured_label'],
               'source_verified_explicit_link': False}
        parsed = urlsplit(asset['url'])
        if asset_root is not None and not parsed.scheme and not parsed.netloc:
            root = Path(asset_root).resolve()
            candidate = (root / unquote(parsed.path).lstrip('/')).resolve()
            row['available'] = candidate.is_relative_to(root) and candidate.is_file() and candidate.stat().st_size > 0
            if row['available']:
                row['asset_sha256'] = hashlib.sha256(candidate.read_bytes()).hexdigest()
        key = record['lineage']['source_group'] + '::' + asset['id']
        qualification = policy.get('asset_qualifications', {}).get(key, {})
        if (row['asset_sha256'] and qualification.get('asset_sha256') == row['asset_sha256']
                and qualification.get('url') == asset['url'] and qualification.get('representation') in REPRESENTATIONS):
            row['representation'] = qualification['representation']
            row['label'] = qualification.get('label') or asset['id']
        sources = {s['id'] for s in record['sources']}
        row['source_verified_explicit_link'] = bool(sample and record['quality']['review_status'] == 'source_reviewed'
            and sample['recipe_link'] == 'explicit' and sample['link_evidence']
            and all(e.get('source_id') in sources and e.get('locator') for e in sample['link_evidence']))
        rows.append(row)
    return rows


def assess_structure_recipe(record, policy=None):
    """Fail closed; readiness is an audited task-profile decision, not global null scanning."""
    policy = policy or {}
    reasons = []
    def reject(code, message, path=None):
        row = {'code': code, 'message': message}
        if path is not None:
            row['pointer'] = path
        if row not in reasons:
            reasons.append(row)
    quality = record['quality']
    if quality['review_status'] != 'source_reviewed':
        reject('source_review_required', 'This record has not completed source review.')
    if record['lineage']['duplicate_of'] is not None:
        reject('duplicate_record', 'This record is marked as a duplicate, not a separate training example.')
    if TASK not in quality['requested_tasks']:
        reject('task_not_requested', 'Exact structure–recipe training has not been requested for this record.')
    sample_assets = coordinate_inventory(record, policy)
    if not sample_assets:
        reject('no_sample_coordinate_asset', 'No canonical measured-sample coordinate asset is recorded; phase/size observations and reference viewers are separate.')
    if sample_assets and not any(a['source_verified_explicit_link'] for a in sample_assets):
        reject('explicit_sample_recipe_link_missing', 'The coordinate-bearing sample has no source-reviewed explicit recipe link.')
    if sample_assets and not any(a['eligible_as_measured_label'] for a in sample_assets):
        reject('measured_label_not_approved', 'The available sample coordinates have not been approved as a measured training label.')
    profile = policy.get('task_profiles', {}).get(record['record_id'])
    selected_assets = []
    if not isinstance(profile, dict):
        reject('audited_task_profile_missing', 'No independently audited completeness profile defines this task’s required recipe fields. Completeness is unassessed, not established.')
    elif not profile_shape_valid(profile):
        reject('invalid_task_profile', 'The task profile is malformed or lacks explicit IDs, selection, field decisions, gap dispositions or coordinate validation.')
    else:
        review = profile.get('review', {})
        if (profile.get('task') != TASK or profile.get('record_id') != record['record_id']
                or profile.get('record_sha256') != digest(record)):
            reject('stale_or_wrong_task_profile', 'The task profile does not bind this exact record revision and task.')
        if not (review.get('status') == 'independently_approved' and review.get('author') and review.get('reviewer')
                and review['author'] != review['reviewer'] and review.get('audit_reference')
                and re.fullmatch('[a-f0-9]{64}', str(review.get('audit_sha256', '')))):
            reject('independent_profile_audit_missing', 'The completeness profile requires a distinct reviewer and an immutable audit reference/hash.')
        if profile.get('required_field_inventory_complete') is not True or not profile.get('scope'):
            reject('required_field_inventory_unassessed', 'An auditor must explicitly attest the task-specific required-field inventory and recipe scope.')
        sample_id = profile.get('sample_id')
        samples = {p['sample_id']: p for p in record['products']}
        sample = samples.get(sample_id)
        linked = {a['asset_id']: a for a in sample_assets if a['sample_id'] == sample_id and a['source_verified_explicit_link']}
        ids = profile.get('structure_asset_ids', [])
        if not ids or len(ids) != len(set(ids)) or any(i not in linked or not linked[i]['eligible_as_measured_label'] for i in ids):
            reject('profile_coordinate_link_not_approved', 'The selected measured coordinate assets must resolve to this same explicitly linked, label-approved sample.')
        else:
            selected_assets = ids
        coordinate = profile.get('coordinate_validation', {})
        if (coordinate.get('status') != 'passed_for_task' or coordinate.get('representation') not in REPRESENTATIONS
                or set(coordinate.get('asset_sha256', {})) != set(ids)
                or any(not re.fullmatch('[a-f0-9]{64}', str(h)) for h in coordinate.get('asset_sha256', {}).values())):
            reject('coordinate_task_validation_missing', 'The profile must identify and hash the experimentally supported representation validated for this task; a viewer model alone is insufficient.')
        for asset_id in selected_assets:
            row = linked[asset_id]
            if (row['available'] is not True or row['asset_sha256'] != coordinate.get('asset_sha256', {}).get(asset_id)
                    or row['representation'] != coordinate.get('representation')):
                reject('coordinate_bytes_or_representation_unverified', 'The local coordinate bytes and explicit representation qualification must match the audited task profile.')
        if not sample or not known(sample['composition']):
            reject('sample_target_identity_missing', 'The selected sample’s reported composition is required; the paper’s broad material label cannot substitute for molecular/sample identity.')
        selection = profile.get('selection', {})
        chosen = {}
        typed = {}
        for field in ['materials', 'stocks', 'material_states', 'operations', 'condition_options']:
            wanted = selection.get(field)
            if not isinstance(wanted, list) or len(wanted) != len(set(wanted)):
                reject('invalid_recipe_selection', 'Every recipe inventory category requires an explicit, duplicate-free ID list.', '/' + field)
                wanted = []
            by_id = {x['id']: (i, x) for i, x in enumerate(record[field])}
            if not set(wanted) <= set(by_id):
                reject('unresolved_recipe_selection', 'Task-selected IDs must resolve to the frozen canonical record.', '/' + field)
            chosen[field] = [x for x in record[field] if x['id'] in wanted]
            for wanted_id in wanted:
                if wanted_id in by_id:
                    index, value = by_id[wanted_id]
                    typed.update(typed_fields(value, '/' + field + '/' + str(index)))
        if not chosen['operations'] or any(o['stage'] == 'characterization' for o in chosen['operations']):
            reject('recipe_operation_scope_invalid', 'Select actual recipe operations; standalone characterization is excluded from recipe supervision.')
        # Explicit selected outputs must retain their material-flow dependencies.
        known_ids = {x['id'] for f in ['materials', 'stocks', 'material_states'] for x in chosen[f]}
        op_ids = {o['id'] for o in chosen['operations']}
        graph_ok = all(set(o['inputs'] + o.get('optional_inputs', []) + o['outputs']) <= known_ids
                       and (not o['retained_fraction'] or o['retained_fraction'] in known_ids)
                       and set(o['depends_on']) <= op_ids for o in chosen['operations'])
        graph_ok &= all(set(s['parent_ids']) <= known_ids for s in chosen['material_states'])
        graph_ok &= all({c['material_id'] for c in s['components']} <= known_ids and set(s['preparation_operation_ids']) <= op_ids for s in chosen['stocks'])
        if not graph_ok:
            reject('incomplete_selected_recipe_graph', 'The selected recipe omits a declared material, stock, state or operation dependency.')
        sample_state = sample.get('material_state_id') if sample else None
        if (not sample_state or sample_state not in {s['id'] for s in chosen['material_states']}
                or not any(sample_state in o['outputs'] for o in chosen['operations'])):
            reject('selected_sample_output_unresolved', 'The selected recipe must explicitly produce the canonical material state of this coordinate-bearing sample.')
        decisions = profile.get('field_decisions', [])
        mapped = {d.get('pointer'): d for d in decisions if isinstance(d, dict)}
        if len(mapped) != len(decisions) or not set(typed) <= set(mapped):
            reject('unclassified_task_fields', 'Each typed field in the selected recipe must be explicitly classified as required or not required for this task.')
        if not any(d.get('disposition') == 'required' for d in decisions):
            reject('empty_required_field_inventory', 'A task profile cannot admit a recipe with an empty required-field inventory.')
        for path, decision in mapped.items():
            if not decision.get('reason') or decision.get('disposition') not in {'required', 'not_required'}:
                reject('invalid_field_decision', 'Each task field needs a required/not-required decision with a scientific rationale.', path)
                continue
            try:
                value = pointer(record, path)
            except (KeyError, IndexError, ValueError, TypeError):
                reject('required_field_absent' if decision['disposition'] == 'required' else 'invalid_field_pointer', 'The task profile points to an absent canonical field.', path)
                continue
            if path not in typed:
                reject('field_outside_selected_recipe', 'Task field decisions must address the selected recipe’s typed fields.', path)
            if decision['disposition'] == 'required' and not known(value):
                reject('required_field_unresolved', 'A field required by this audited task profile is missing, inferred, conflicting, or lacks source evidence.', path)
        for key in ['missing_fields', 'conflicts']:
            dispositions = profile.get(key + '_decisions', [])
            expected = list(enumerate(quality[key]))
            observed = [(d.get('index'), d.get('text')) for d in dispositions if isinstance(d, dict)]
            if len(observed) != len(set(i for i, _ in observed)) or sorted(observed) != expected:
                reject('unassessed_' + key, 'Every recorded ' + key.replace('_', ' ') + ' item needs a task-specific disposition; global lists are not silently ignored.')
            for d in dispositions:
                if not d.get('reason') or d.get('disposition') not in {'outside_task_scope', 'not_required', 'required_unresolved'}:
                    reject('invalid_' + key + '_decision', 'Task gap/conflict disposition lacks a valid decision and rationale.')
                elif d['disposition'] == 'required_unresolved':
                    reject('task_relevant_' + key, d['text'])
    return {'eligible': not reasons, 'reason': ' '.join(x['message'] for x in reasons) if reasons else 'This exact record, selected coordinate representation and task-specific recipe scope passed an independent completeness profile.',
            'reason_codes': list(dict.fromkeys(x['code'] for x in reasons)), 'reasons': reasons,
            'profile_id': profile.get('id') if isinstance(profile, dict) else None,
            'selected_asset_ids': selected_assets}


def exact_recipe_selection(record, policy):
    profile = policy['task_profiles'][record['record_id']]
    return {field: [row for row in record[field] if row['id'] in profile['selection'][field]]
            for field in ['materials', 'stocks', 'material_states', 'operations', 'condition_options']}


def structure_recipe_coverage(records, policy=None, asset_root=None):
    """Counts distinct assets, record/sample links and ready records; never physical batches."""
    asset_root = asset_root if asset_root is not None else (policy or {}).get('_asset_root')
    rows = []
    assets, links, ready = {}, set(), []
    reason_counts = Counter()
    for record in records:
        inventory = coordinate_inventory(record, policy, asset_root)
        assessment = assess_structure_recipe(record, policy)
        for row in inventory:
            if row['available'] is True and row['sample_resolved']:
                key = (row['source_group'], row['url'])
                assets[key] = row
                if row['source_verified_explicit_link']:
                    links.add((record['record_id'], row['sample_id'], row['url'], row['representation']))
        if assessment['eligible']:
            ready.append(record['record_id'])
        reason_counts.update(assessment['reason_codes'])
        rows.append({'record_id': record['record_id'], 'source_group': record['lineage']['source_group'],
                     'coordinate_assets': inventory, 'exact_structure_recipe': assessment})
    return {'schema_version': '1.0', 'scope': 'Canonical measured-sample coordinate links only. Reachability is a local file check, not a new structural validation. External reference/illustrative viewers and unregistered source structures are outside this inventory. Assets, documentary links and task-ready records are different units; none counts independent experimental batches.',
            'availability_assessed': asset_root is not None,
            'counts': {'sample_coordinate_assets': len(assets) if asset_root is not None else None,
                       'records_with_sample_coordinates': sum(any(a['available'] is True and a['sample_resolved'] for a in row['coordinate_assets']) for row in rows) if asset_root is not None else None,
                       'source_verified_explicit_links': len(links) if asset_root is not None else None,
                       'exact_task_ready_records': len(ready)},
            'asset_representation_counts': dict(Counter(a['representation'] for a in assets.values())),
            'explicit_link_representation_counts': dict(Counter(x[3] for x in links)),
            'ready_record_ids': ready, 'exclusion_reason_record_counts': dict(sorted(reason_counts.items())), 'records': rows}
