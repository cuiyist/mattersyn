"""Private, metadata-only canonical promotion and task-view author proposal.

Read current Site validators only. Never modifies the Site, canonical originals,
source files, live ledger, prior audits, reader or visual packages.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

B = Path(__file__).resolve().parent
SITE = B.parents[4] / 'recipe-atlas'
sys.path.insert(0, str(SITE / 'scripts'))
from dataset_lib import validate_record, eligibility, training_view, build_groups

CONFIG = {
 'la036034c': {
  'source_id': 'nagasaki2004', 'count': 16, 'main_pages': 5, 'si_pages': 3,
  'scope': 'All five supplied main pages and all three content-matched SI pages completely read and visually inspected; independent source, canonical, reader, apparatus, component and product-context audits passed. Four source ambiguities, the incomplete biotin variant and all missing quantities remain explicit. The abstract size summary and optical-model size do not establish a TEM/XRD/biotin recipe-to-specimen join. No measured atomic coordinates are supplied. This metadata promotion and its explicitly requested task views remain a private proposal pending independent promotion and integration review.',
  'audits': ['source-scientific-audit.json', 'canonical-records-audit.json', 'reader-source-audit.json', 'apparatus-source-audit.json', 'component-source-audit.json', 'product-source-audit.json'],
  'tasks': {
   'nagasaki-2004-cho-cds': ['precursor_selection', 'partial_protocol'],
   'nagasaki-2004-biotin-cds': ['precursor_selection', 'partial_protocol'],
   'nagasaki-2004-polymer-preparation': ['partial_protocol'],
   'nagasaki-2004-aldehyde-polymer': ['partial_protocol'],
   'nagasaki-2004-biotin-polymer': ['partial_protocol'],
  },
  'reasons': {
   'nagasaki-2004-cho-cds': 'The representative aqueous coprecipitation identifies cadmium chloride and sodium sulfide and supplies five preparation/workup operations. Retain unknown temperature, stock basis and dialysis details; no structure, size or optical outcome target.',
   'nagasaki-2004-biotin-cds': 'The source explicitly names the biotin-stabilized substitution and the same Cd/S precursor identities. Export only its single qualitative similar-manner operation with all unreported numerical fields preserved; it is not a second independently quantified run. Requested surface denotes the named stabilizer, not measured grafting or geometry.',
   'nagasaki-2004-polymer-preparation': 'The present article supplies seven polymer preparation/workup operations and quantitative EO/AMA/PDP framework. The protonating reagent and cited upstream details remain unknown; exclude the separate NMR acquisition operation. This is a partial precursor-preparation protocol, not an additional CdS synthesis.',
   'nagasaki-2004-aldehyde-polymer': 'Three reported hydrolysis, neutralization and dialysis operations form a distinct polymer conversion. Preserve unknown scale, neutralization endpoint and dialysis parameters.',
   'nagasaki-2004-biotin-polymer': 'Three source-scoped hydrazide coupling, reduction and workup-context operations preserve the pre-dialysis branch. Do not replace its starting mixture with the separately dialyzed aldehyde polymer or invent purification conditions.',
  },
  'excluded_reasons': {
   'nagasaki-2004-concentration-series': 'Grouped formulation comparison with unresolved physical batch identities, not independent protocol instances.',
   'nagasaki-2004-stabilizer-controls': 'Grouped failed/partial stabilization controls retained as evidence, not calibrated success labels or independent precursor/protocol examples.',
  },
  'expected_precursors': {'cadmium chloride', 'sodium sulfide'},
 },
 'jp0473669': {
  'source_id': 'ribeiro2004', 'count': 11, 'main_pages': 6, 'si_pages': None,
  'scope': 'All six supplied main pages completely read and visually inspected; independent source, canonical, reader and private visual audits passed. No matched supporting information was located or verified; SI existence remains unverified and no absence is inferred. Preserve the unspecified basis of the approximately 500:1 water/Sn ratio, acid-set treatment pH versus unreported final TBAOH measurement pH, and radius/diameter/model distinctions. XRD is mentioned but the inspected article supplies no trace, SAED or atomic coordinates. This metadata promotion and its explicitly requested task views remain a private proposal pending independent promotion and integration review.',
  'audits': ['source-scientific-audit.json', 'canonical-records-audit.json', 'reader-source-audit.json', 'visual-source-audit.json'],
  'tasks': {'ribeiro-2004-hydrolysis': ['precursor_selection', 'partial_protocol']},
  'reasons': {'ribeiro-2004-hydrolysis': 'Tin(II) chloride dihydrate is the explicitly identified tin precursor. Three dissolution, hydrolysis and dialysis operations are supplied, with a concentration range rather than invented separate batches. The approximately 500:1 water/Sn basis, absolute scale, reaction time and dialysis schedule remain unresolved. No optical-model size is an output label.'},
  'excluded_reasons': {'ribeiro-2004-ph-treatment': 'Treatment/aging/redispersion belongs to source characterization contexts. The current canonical stage is characterization, so do not relabel it or emit an empty protocol after acquisition-stage filtering.'},
  'expected_precursors': {'Tin(II) chloride dihydrate'},
 },
 'ja048427j': {
  'source_id': 'norberg2004', 'count': 19, 'main_pages': 12, 'si_pages': 4,
  'scope': 'All twelve supplied main pages and all four content-matched SI pages completely read and visually inspected; independent source, canonical, reader and private visual audits passed. Absolute recipe scale and multiple workup conditions remain unreported. Keep the 0.02% feed EPR series, 0.20 +/- 0.01% measured colloids, 1.1% TOPO/MCD specimen and optical/model contexts separate. Preserve SI statistical-notation and Figure S3/Table S4 D/F conflicts. Films A-C preparation does not supply missing D-F coat counts or annealing conditions. An external undoped ZnO cell is a reference, not measured Mn:ZnO coordinates. This metadata promotion and its explicitly requested task views remain a private proposal pending independent promotion and integration review.',
  'audits': ['source-scientific-audit.json', 'canonical-records-audit.json', 'reader-source-audit.json', 'reader-link-audit.json', 'reader-original-pixel-audit.json', 'reader-render-delta-audit.json', 'visual-source-audit.json'],
  'tasks': {
   'norberg-2004-hydrolysis': ['precursor_selection', 'partial_protocol'],
   'norberg-2004-amine-cleaning': ['partial_protocol'],
   'norberg-2004-films-a-c': ['partial_protocol'],
   'norberg-2004-surface-control': ['partial_protocol'],
  },
  'reasons': {
   'norberg-2004-hydrolysis': 'Seven common preparation/workup operations identify zinc acetate dihydrate and manganese(II) acetate tetrahydrate as synthesis-stage host/dopant precursors. Preserve those exact roles. No absolute scale, arbitrary feed assignment, generic growth duration or initial capping conditions are filled from the later cleaning treatment.',
   'norberg-2004-amine-cleaning': 'Four source-described surface treatment/workup operations retain the 180 degC, approximately 30 min nitrogen treatment and cooling below 80 degC. This is a separate post-treatment of preformed colloids, not their original synthesis or an asserted product-size label.',
   'norberg-2004-films-a-c': 'Three spin-coat/anneal/repeat operations describe the A-C film preparation family. Preserve the 40 versus 20 coat alternatives and all unknown spin settings; do not duplicate rows per film or transfer conditions to D-F. Film magnetization is not a training target.',
   'norberg-2004-surface-control': 'Four reported operations define a deliberately prepared surface-bound Mn control from the common undoped ZnO preparation. Preserve the approximately 2% Mn and 0.002 equivalent LiOH with unresolved equivalent basis. No success, occupancy, size or exact surface-geometry label is admitted.',
  },
  'excluded_reasons': {
   'norberg-2004-growth-series': 'Grouped EPR aliquot progression combines continuation of original bulk and a separate cleaning context, not a second independent recipe. Keep specimen boundaries and operations in the reader without another protocol row.',
   'norberg-2004-topo': 'The alternative treatment points to uninspected reference 32 and does not restate temperature, time or amount. Conservatively retain it as literature context, without borrowing the amine treatment or admitting a protocol row.',
   'norberg-2004-oxidation-controls': 'Grouped solution-stability/control conditions are not a target synthesis protocol or calibrated success dataset.',
   'norberg-2004-structure': 'The retained workup is preparation for structural characterization, not an independently requested synthesis protocol.',
   'norberg-2004-films-d-f': 'Incomplete film outcomes with unresolved preparation and Figure S3/Table S4 D/F conflict; no inferred recipe or outcome task.',
  },
  'expected_precursors': {'Zinc acetate dihydrate', 'Manganese(II) acetate tetrahydrate'},
 },
}
cfg = CONFIG[B.name]
# Record metadata states the scientific review scope; proposal lifecycle belongs
# in the private manifest and must not become a stale public reader sentence.
cfg['scope'] = cfg['scope'].removesuffix(' This metadata promotion and its explicitly requested task views remain a private proposal pending independent promotion and integration review.')
O = B / 'promotion-proposal'
ALLOWED = {'/collection', '/quality/review_status', '/quality/review_scope', '/quality/requested_tasks', '/sources/0/main_status'}
FORBIDDEN = {'exact_structure_recipe', 'size_conditioned_recipe', 'optical_outcome', 'success_prediction'}
checks, bound, gate_statuses = [], {}, []

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def check(name, condition, detail=''):
    checks.append({'check': name, 'passed': bool(condition), 'detail': detail})
    if not condition: raise AssertionError((name, detail))
def bind(p, expected=None):
    p = Path(p).resolve(); value = sha(p); bound[str(p)] = value
    if expected is not None: check('hash: ' + str(p), value == expected)
    return value
def diffs(a, b, pointer=''):
    if type(a) is not type(b): return [pointer]
    if isinstance(a, dict):
        return [d for k in sorted(set(a) | set(b)) for d in ([pointer + '/' + k] if k not in a or k not in b else diffs(a[k], b[k], pointer + '/' + k))]
    if isinstance(a, list):
        if len(a) != len(b): return [pointer]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diffs(x, y, pointer + '/' + str(i))]
    return [] if a == b else [pointer]

bind(__file__)
for name in ['dataset_lib.py', 'schema_definition.py']: bind(SITE / 'scripts' / name)
snapshot_path = B.parent / 'integration-resume-20260920T0116.json'
bind(snapshot_path)
snapshot = read(snapshot_path)
fingerprint = next(x for x in snapshot['source_fingerprints'] if x['group_id'] == '10.1021_' + B.name)
check('Current frozen source generation is 2', fingerprint['generation'] == 2)
for filename, expected in fingerprint['files'].items():
    origin = B.parents[5] / 'data_Tanjin/papers/50k_all_papers' if filename.startswith('legacy::') else B.parents[4] / 'downloaded_papers'
    bind(origin / filename.replace('legacy::', ''), expected)
for name in cfg['audits']:
    path = B / name; a = read(path); bind(path)
    check(name + ': independent gate passed', str(a['status']).startswith('passed'))
    for key in ['open_findings', 'unresolved_findings', 'corrections_required', 'required_author_corrections']:
        check(name + ': no open ' + key, not a.get(key))
    gate_statuses.append({'path': str(path), 'sha256': sha(path), 'status': a['status'], 'scope': a.get('scope'), 'auditor': a.get('auditor', a.get('reviewer'))})
canonical_audit = read(B / 'canonical-records-audit.json')
for name in ['canonical-record-manifest.json', 'canonical-source-coverage.json', 'source-facts.json', 'source-inventory.json']:
    path = B / name
    expected = canonical_audit['bound_files'].get(str(path))
    check(name + ': bound by canonical audit', expected is not None)
    bind(path, expected)

drafts = sorted((B / 'canonical-drafts').glob('*.json'))
check('Complete frozen record set', len(drafts) == cfg['count'] and {p.stem for p in drafts} == set(canonical_audit['record_hashes']))
records, originals, rows, exports = [], [], [], []
for path in drafts:
    original = read(path); rid = original['record_id']; originals.append(original)
    bind(path, canonical_audit['record_hashes'][rid])
    check(rid + ': own source only', original['lineage']['source_group'] == cfg['source_id'] and original['sources'][0]['id'] == cfg['source_id'])
    proposal = deepcopy(original)
    proposal['collection'] = 'reviewed_literature'
    proposal['quality']['review_status'] = 'source_reviewed'
    proposal['quality']['review_scope'] = cfg['scope']
    proposal['quality']['requested_tasks'] = cfg['tasks'].get(rid, [])
    proposal['sources'][0]['main_status'] = f"All {cfg['main_pages']} supplied main pages text-read and visually inspected; independent source and canonical scientific audits passed. Preserved source conflicts and missing fields remain explicit."
    delta = diffs(original, proposal)
    check(rid + ': allowed metadata-only delta', all(any(p == a or p.startswith(a + '/') for a in ALLOWED) for p in delta), str(delta))
    restored = deepcopy(proposal)
    if 'collection' in original: restored['collection'] = original['collection']
    else: restored.pop('collection')
    for key in ['review_status', 'review_scope', 'requested_tasks']: restored['quality'][key] = original['quality'][key]
    restored['sources'][0]['main_status'] = original['sources'][0]['main_status']
    check(rid + ': exact scientific equality after five-field restore', restored == original)
    check(rid + ': SI status exactly unchanged', proposal['sources'][0]['si_status'] == original['sources'][0]['si_status'])
    errors = validate_record(proposal)
    check(rid + ': current schema and semantic checks', not errors, str(errors))
    permitted = eligibility(proposal)
    selected = [t for t, value in permitted.items() if value['eligible']]
    check(rid + ': exact requested task eligibility', set(selected) == set(cfg['tasks'].get(rid, [])))
    check(rid + ': no outcome or exact-structure task', not any(permitted[t]['eligible'] for t in FORBIDDEN))
    for task in selected:
        export = training_view(proposal, task)
        check(rid + '/' + task + ': inputs allowlist', set(export['input']) <= {'composition', 'method', 'requested_surface', 'requested_host'})
        check(rid + '/' + task + ': no experimental labels in export', not ({'products', 'measurements', 'structure_assets', 'intended_target'} & set(export['output'])))
        if task == 'precursor_selection':
            check(rid + ': exact source precursor identities', {m['name'] for m in export['output']['precursors']} == cfg['expected_precursors'])
            check(rid + ': full precursor count', len(export['output']['precursors']) == len(cfg['expected_precursors']))
        else:
            ops = export['output']['operations']; ids = {op['id'] for op in ops}
            check(rid + ': nonempty preparative protocol', bool(ops))
            check(rid + ': no characterization operations', all(op['stage'] != 'characterization' for op in ops))
            check(rid + ': retained dependency closure', all(set(op['depends_on']) <= ids for op in ops))
            check(rid + ': original operations retained exactly', ops == [op for op in original['operations'] if op['stage'] != 'characterization'])
            check(rid + ': typed protocol gaps retained', bool(export['output']['missing_fields']) and export['output']['missing_fields'] == original['quality']['missing_fields'])
        exports.append(export)
    records.append(proposal)
    reason = cfg['reasons'].get(rid, cfg['excluded_reasons'].get(rid, 'Characterization, instrument, interpretation or source-context evidence remains reviewed literature without requested training tasks. No operation-count-based automatic admission.'))
    rows.append({'record_id': rid, 'source_sha256': sha(path), 'proposal_path': 'records/' + path.name, 'eligible_tasks': selected, 'changed_leaf_paths': delta, 'scientific_fields_unchanged': restored == original, 'task_selection_rationale': reason, 'schema_errors': errors, 'task_gate_results': permitted})
groups = build_groups(records)
check('One unchanged source split group', groups == build_groups(originals) and len(set(groups.values())) == 1)
check('All selected records resolved', set(cfg['tasks']) <= {r['record_id'] for r in records})
check('No unexpected proposal records already present', not (O / 'records').exists() or {p.stem for p in (O / 'records').glob('*.json')} <= {r['record_id'] for r in records})
counts = Counter(x['task'] for x in exports)
protocol_counts = {x['record_id']: len(x['output']['operations']) for x in exports if x['task'] == 'partial_protocol'}
for record, row in zip(records, rows):
    destination = O / row['proposal_path']; save(destination, record); row['proposal_sha256'] = sha(destination)
preview = {'status': 'private_proposal_only', 'published': False, 'source_id': cfg['source_id'], 'source_generation': 2, 'exports': exports, 'source_split_groups': groups}
save(O / 'training-export-preview.json', preview)
gate_note = 'Current dataset_lib synthesis_precursors includes host_precursor and dopant_precursor only when stage is synthesis. Root made this targeted allowlist change; this author changed no Site code or canonical roles. Explicit requested_tasks remain mandatory. Norberg common-route output preserves Zn host/Mn dopant identity and complete precursor pair.'
validation = {'schema': 'mattersyn.private-promotion-author-validation/1', 'author': '/root/backlog_eta', 'status': 'passed_author_checks_pending_independent_audit', 'source_id': cfg['source_id'], 'checks': checks, 'counts': {'checks': len(checks), 'records': len(records), 'exports': len(exports), 'tasks': dict(counts)}, 'source_split_groups': groups, 'partial_protocol_operation_counts': protocol_counts, 'records': rows, 'independent_audit': False, 'site_modified': False, 'scientific_fields_changed': False}
save(O / 'author-validation.json', validation)
manifest = {
 'schema': 'mattersyn.private-promotion-proposal/2', 'author': '/root/backlog_eta', 'source_id': cfg['source_id'],
 'status': 'private_proposal_valid_pending_independent_promotion_audit_and_integration', 'created_at': datetime.now(timezone.utc).isoformat(),
 'source_generation': 2, 'source_fingerprint': fingerprint, 'source_canonical_audit_sha256': sha(B / 'canonical-records-audit.json'),
 'allowed_promotion_fields': sorted(ALLOWED), 'scientific_fields_unchanged': True, 'source_si_status_exactly_unchanged': True,
 'records': rows, 'record_count': len(records), 'one_source_split_group': True, 'source_split_group_assignments': groups,
 'proposed_precursor_selection_rows': counts.get('precursor_selection', 0), 'proposed_partial_protocol_rows': counts.get('partial_protocol', 0),
 'proposed_exact_structure_pairs': 0, 'proposed_size_conditioned_rows': 0, 'proposed_optical_rows': 0, 'proposed_success_labels': 0,
 'partial_protocol_operation_counts': protocol_counts, 'training_export_preview_sha256': sha(O / 'training-export-preview.json'),
 'author_validation_sha256': sha(O / 'author-validation.json'), 'passed_prior_gate_evidence': gate_statuses, 'bound_inputs': bound,
 'current_task_gate_change': gate_note, 'promotion_independent_audit': 'pending', 'site_modified': False, 'ledger_modified': False,
 'canonical_originals_modified': False, 'reader_visual_files_modified': False, 'publication_approved': False,
 'limits': ['Partial protocol means source-limited literature supervision, not a complete executable SOP or new independent experiment.', 'All records from one paper remain in one source split group, including variants and controls.', 'No exact structure, size, optical-outcome or success-prediction rows.', 'Prior private reader/visual audits do not substitute for root integration and browser validation.', 'Scientific notes, conflicts, references, quantities, sample identifiers, materials and roles remain exactly as independently audited.'],
}
save(O / 'promotion-manifest.json', manifest)
readme = [f'# {cfg["source_id"]}: private promotion proposal', '', f'{len(records)} metadata-only record proposals; {counts.get("precursor_selection", 0)} precursor-selection rows and {counts.get("partial_protocol", 0)} partial-protocol rows. {len(checks)} author checks passed. Independent promotion review is pending.', '',
 'Only collection, quality review status/scope/requested tasks and primary-source main-reading status change. Restoring exactly those five fields yields complete equality with every frozen original. SI status is unchanged.', '', cfg['scope'], '', 'Task decisions:', '']
readme += [f'- `{x["record_id"]}` — {", ".join(x["eligible_tasks"]) or "no training task"}. {x["task_selection_rationale"]}' for x in rows]
readme += ['', gate_note, '', 'Exact before/after record hashes, changed JSON pointers, source generation, prior gate hashes and validator hashes are retained in promotion-manifest.json. The training preview is generated with the current dataset_lib, with one unchanged source split group. No Site/shared-ledger/source/reader/visual edits or publication actions occurred.']
(O / 'README.md').write_text('\n'.join(readme) + '\n', encoding='utf-8')
print(json.dumps({'paper': B.name, 'records': len(records), 'task_counts': dict(counts), 'protocol_operations': protocol_counts, 'author_checks': len(checks), 'manifest_sha256': sha(O / 'promotion-manifest.json'), 'preview_sha256': sha(O / 'training-export-preview.json')}, indent=2))
