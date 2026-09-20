"""Read-only bounded metadata audit; writes only separate private audit reports."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

L = Path(__file__).resolve().parents[1]
P = L / 'site-integration-proposal'
A = Path(__file__).resolve().parent
S = Path('[local path redacted]')
checks = []
bound = {}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    path = Path(path)
    bound[str(path)] = sha(path)
    return json.loads(path.read_text(encoding='utf-8'))

def check(name, value):
    checks.append({'check': name, 'passed': bool(value)})
    if not value:
        raise AssertionError(name)

def differences(a, b, pointer=''):
    if type(a) is not type(b):
        return [{'pointer': pointer, 'before': a, 'after': b}]
    if isinstance(a, dict):
        out = []
        for key in sorted(a.keys() | b.keys()):
            p = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key not in a:
                out.append({'pointer': p, 'operation': 'add', 'after': b[key]})
            elif key not in b:
                out.append({'pointer': p, 'operation': 'remove', 'before': a[key]})
            else:
                out.extend(differences(a[key], b[key], p))
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'pointer': pointer, 'before': a, 'after': b}]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, pointer + '/' + str(i))]
    return [] if a == b else [{'pointer': pointer, 'before': a, 'after': b}]

delta = read(P / 'reader-final-status-delta.json')
before = read(delta['before_file'])
after = read(delta['after_file'])
check('before raw SHA', sha(delta['before_file']) == delta['before_sha256'])
check('after raw SHA', sha(delta['after_file']) == delta['after_sha256'])
check('actual Site remains baseline at audit', sha(S / 'data/paper-reviews/lian2021.json') == delta['before_sha256'])
allowed_top = {'presentation_gates', 'route_evidence_scope_notes', 'remaining_gaps', 'audit_details'}
check('exact declared top-level allowlist', set(delta['allowed_top_level_changes']) == allowed_top)
check('deep equality outside four metadata fields', {k: v for k, v in before.items() if k not in allowed_top} == {k: v for k, v in after.items() if k not in allowed_top})
diff = differences(before, after)
expected = {
    '/audit_details/browser_validation_sha256',
    '/audit_details/integration_audit_sha256',
    '/audit_details/qualified_bulk_model_audit_sha256',
    '/presentation_gates/browser_render',
    '/presentation_gates/qualified_partial_bulk_display',
    '/remaining_gaps/10',
    '/route_evidence_scope_notes/bulk_structure',
}
check('exact seven leaf differences', {d['pointer'] for d in diff} == expected and len(diff) == 7)
check('only four top-level fields differ', {d['pointer'].split('/')[1] for d in diff} == allowed_top)
check('publication remains false', before['presentation_gates']['publication'] is False and after['presentation_gates']['publication'] is False and delta['publication_claim'] is False)
check('exact atomic binding remains false', after['presentation_gates']['exact_product_atomic_structure_binding'] is False)
check('qualified partial display only', after['presentation_gates']['qualified_partial_bulk_display'] is True)
check('browser approved flag supported separately', before['presentation_gates']['browser_render'] is False and after['presentation_gates']['browser_render'] is True)
check('publication status unchanged', after['publication_status'] == before['publication_status'])
check('no training promotion', after['audit_details']['training_promotions'] == 0)
receipts = {
    'browser_validation_sha256': P / 'browser-validation.json',
    'integration_audit_sha256': A / 'integration-transport-audit.json',
    'qualified_bulk_model_audit_sha256': L / 'visuals/bulk-structure-independent-audit/independent-audit.json',
}
loaded = {}
for key, path in receipts.items():
    receipt = read(path)
    loaded[key] = receipt
    check(key + ' exact hash', sha(path) == after['audit_details'][key])
    check(key + ' passed', receipt['status'] == 'passed')
    check(key + ' no open findings', not receipt.get('open_findings'))
browser = loaded['browser_validation_sha256']
check('browser 21 stages', browser['total_actual_stage_controls'] == 21 and sum(x['operation_count'] for x in browser['stage_controls']) == 21)
check('browser 122 source rows', browser['adjacent_condition_rows'] == 122)
check('browser console clean', browser['checks']['console_errors'] == [])
for filename, digest in browser['changed_code_sha256'].items():
    path = S / 'dist' / filename
    bound[str(path)] = sha(path)
    check('browser code hash ' + filename, sha(path) == digest)
bulk = loaded['qualified_bulk_model_audit_sha256']
check('bulk author and auditor distinct', bulk['author'] == '/root/peng1998_reader_assets' and bulk['auditor'] == '/root')
for key in ['physical_batch_join_verified', 'full_model_eligible', 'nanocrystal_or_film_model', 'dft_ready', 'exact_structure_recipe_eligible']:
    check('bulk restriction ' + key, bulk[key] is False)
check('bulk model exact qualified role', bulk['model_role'] == 'qualified_partial_non_hydrogen_bulk_table_reconstruction')
for key, name in [('math_audit_sha256', 'coordinate-math-audit.json'), ('binding_audit_sha256', 'binding-audit.json')]:
    path = L / 'visuals/bulk-structure-independent-audit' / name
    proof = read(path)
    check(key + ' exact subordinate proof', sha(path) == bulk[key] and proof['status'] == 'passed')
check('bulk links same browser proof', bulk['browser_validation_sha256'] == after['audit_details']['browser_validation_sha256'])
check('bulk links same root-only transport proof', bulk['root_presentation_delta_audit_sha256'] == after['audit_details']['integration_audit_sha256'])
for relative, digest in after['audit_details']['audit_sha256'].items():
    path = L / relative
    receipt = read(path)
    check('unchanged prerequisite ' + relative, sha(path) == digest and receipt['status'] == 'passed')
check('all reader sections unchanged', before['reader_sections'] == after['reader_sections'])
check('all source documents unchanged', before['documents'] == after['documents'])

timestamp = datetime.now(timezone.utc).isoformat()
report = {
    'schema': 'mattersyn.independent_reader_status_delta_audit/1',
    'source_id': 'lian2021', 'auditor': '/root/peng1998_reader_assets',
    'implementation_author': '/root', 'created_at': timestamp, 'status': 'passed',
    'scope': 'Exact root reader metadata delta and receipt verification only; no repeated source extraction, model self-audit or deployment verification.',
    'proposal_delta_sha256': sha(P / 'reader-final-status-delta.json'),
    'before_sha256': delta['before_sha256'], 'after_sha256': delta['after_sha256'],
    'scientific_deep_equality': True, 'exact_leaf_changes': diff,
    'manual_review': [
        'Read both revised sentences completely. The bulk note restricts four explicit contexts to partial non-H table reconstructions and retains absent hydrogen/occupancy/ZIP and unresolved physical aliquot joins.',
        'The remaining-gap sentence removes only superseded gate status; it explicitly excludes complete atomic models and exact structure-recipe training pairs.',
        'Read the root model and browser reports. Root independently audited this auditor-authored model; the current audit only checks that distinct proof and the narrow status wording.',
        'Local browser proof is not deployment proof. Publication remains false and its status string is unchanged.'
    ],
    'checks': checks, 'check_count': len(checks), 'open_findings': [],
    'bound_files': bound, 'site_modified': False, 'publication_verified': False,
    'new_model_science_approval': False, 'training_approved': False,
}
audit_path = A / 'reader-final-status-audit.json'
audit_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(A / 'reader-final-status-audit.md').write_text(
    '# Lian reader final-status delta audit\n\nPassed. Exactly seven leaf changes occur within the four declared metadata fields. All reader scientific content, typed values, source documents, figures, sample links and training boundaries are deeply equal.\n\n'
    'The model, integration and local browser receipts match their exact hashes; the five browser code hashes match current Site files. The bulk model remains a separately audited partial non-hydrogen reconstruction, with no complete model or exact structure–recipe eligibility. Publication remains false.\n\n'
    f'{len(checks)} bounded checks passed, with no findings. This review did not re-audit its own model science, perform a new browser run, mutate Site, or verify public deployment.\n\n'
    f'JSON SHA256: `{sha(audit_path)}`\n', encoding='utf-8')

publication_text = 'Published on GitHub Pages after independent source, data, illustration, integration and browser checks; anonymous deployment verified.'
conditional_after = copy.deepcopy(after)
conditional_after['presentation_gates']['publication'] = True
conditional_after['publication_status'] = publication_text
publication_diff = differences(after, conditional_after)
assert {x['pointer'] for x in publication_diff} == {'/presentation_gates/publication', '/publication_status'}
rule = {
    'schema': 'mattersyn.conditional_publication_metadata_rule_audit/1',
    'source_id': 'lian2021', 'auditor': '/root/peng1998_reader_assets',
    'created_at': timestamp, 'status': 'passed_conditionally',
    'scope': 'Approval of one exact future metadata-only transition; not a claim that deployment prerequisites have occurred.',
    'baseline_reader_sha256': delta['after_sha256'],
    'reader_status_audit_sha256': sha(audit_path),
    'exact_allowed_changes': publication_diff,
    'prerequisites': [
        'First apply only the exact reader proposal approved above. Save its exact pre-publication bytes and verify the baseline hash.',
        'Retain an immutable passed anonymous deployment verification receipt for the actual Lian scientific release on GitHub Pages, with release/site identity and checked public endpoints/assets bound to the deployed build. Local preview and a push response alone do not satisfy this condition.',
        'Verify no failed or unresolved required deployment checks, and verify the public reader/record/assets correspond to the independently audited scientific release (apart from these exact publication labels).',
        'Record the anonymous receipt path and SHA256 in a separate publication delta/proof, keeping this rule unchanged.',
        'Immediately before applying, compare the saved baseline. Immediately after, verify exactly the two listed leaf changes and deep equality at every other field. If any other reader leaf differs, this conditional approval does not apply.',
        'Keep exact_product_atomic_structure_binding false, all training tasks/gates unchanged, and partial-model scope unchanged. Do not infer a complete structure or exact training pair from publication.',
    ],
    'simulation': {'exactly_two_leaf_changes': True, 'all_other_data_deep_equal': True, 'no_transition_applied': True},
    'publication_verified': False, 'deployment_receipt': None,
    'open_findings': [], 'bound_files': {str(audit_path): sha(audit_path), str(P / 'reader-final-status-proposal.json'): delta['after_sha256']},
}
rule_path = A / 'conditional-publication-rule-audit.json'
rule_path.write_text(json.dumps(rule, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(A / 'conditional-publication-rule-audit.md').write_text(
    '# Conditional publication metadata rule\n\nThe exact two-leaf transition is approved only after an immutable passed anonymous deployment receipt verifies the actual audited Lian release. No deployment verification is asserted by this report.\n\n'
    '- Set `presentation_gates.publication` from false to true.\n'
    '- Set `publication_status` to: ' + publication_text + '\n\n'
    'Every other reader field must remain deeply equal to the exact approved baseline. Save the receipt hash and before/after proof separately. No Site change was made.\n\n'
    f'JSON SHA256: `{sha(rule_path)}`\n', encoding='utf-8')
print(json.dumps({'status': 'passed', 'checks': len(checks), 'audit': str(audit_path), 'audit_sha256': sha(audit_path), 'conditional_rule': str(rule_path), 'conditional_rule_sha256': sha(rule_path)}))
