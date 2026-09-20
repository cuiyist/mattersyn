"""Create a PRIVATE, source-scoped canonical promotion proposal. Never writes the Site.

Run with Python -B. Audited input bytes are checked before any proposal is prepared.
The resulting source_reviewed metadata is a proposal, not publication authorization.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent
SITE = REVIEW.parents[3] / 'recipe-atlas'
sys.path.insert(0, str(SITE / 'scripts'))
from dataset_lib import build_groups, eligibility, training_view, validate_record
from build_atlas import synthesis_route

RANGE_KEY = 'study_wide_disilane_concentration_range'
SOURCE_ID = 'littau1993'
SOURCE_DOI = '10.1021/j100108a019'
PREFIX = 'littau-1993-si-'
VARIANTS = [PREFIX + 'aerosol-' + n for n in ('1p0', '2p0', '6p0')]
TASKS = ['precursor_selection', 'partial_protocol']
SOURCE_SCOPE = 'supplied_main_only_si_unverified'
REVIEW_LINK = '../paper-review.html?id=littau1993'
FULL_AUDIT = 'independent-audit.json'
AUDITS = {
    'canonical-drafts': 'canonical-drafts-audit.json',
    'procedure-drafts': 'procedure-drafts-independent-audit.json',
    'context-drafts': 'context-draft-audit.json',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    assert path.resolve().is_relative_to(OUT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def differences(a, b, pointer=''):
    """Every actual JSON change, with JSON-pointer paths and exact old/new values."""
    if type(a) is not type(b):
        return [{'path': pointer, 'operation': 'replace', 'old': a, 'new': b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            p = pointer + '/' + str(key).replace('~', '~0').replace('/', '~1')
            if key not in a:
                result.append({'path': p, 'operation': 'add', 'new': b[key]})
            elif key not in b:
                result.append({'path': p, 'operation': 'remove', 'old': a[key]})
            else:
                result.extend(differences(a[key], b[key], p))
        return result
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'path': pointer, 'operation': 'replace', 'old': a, 'new': b}]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, pointer + '/' + str(i))]
    return [] if a == b else [{'path': pointer, 'operation': 'replace', 'old': a, 'new': b}]


def expected_audited_hashes(audits):
    result = {}
    for item in audits['canonical-drafts']['reviewed_records']:
        result[item['file'][:-5]] = item['sha256']
    for item in audits['procedure-drafts']['records']:
        result[item['record_id']] = item['sha256']
    result['littau-1993-aks41-context'] = audits['context-drafts']['record_sha256']
    return result


def scoped_review_text(kind):
    common = (
        'Supplied main only: all seven main pages were read and visually inspected, '
        'with independent source review and a bounded canonical source-join audit. '
        'Matching SI has not been located or verified; no main-plus-SI review is claimed. '
        'Final item-coverage reconciliation, canonical-to-reader audit and publication remain separate pending gates. '
    )
    if kind == 'canonical-drafts':
        return common + (
            'This formulation family and its six structural/HPLC entries passed the corrected variant audit. '
            'Precursor selection and partial literature-protocol supervision are proposed only; '
            'this is not a complete SOP or a validated outcome/size/atomic-structure prediction label. '
            'IDs denote formulation families, not individually documented physical batches. '
            'Study-wide feed concentration is retained separately as source context, not a variant setting.'
        )
    if kind == 'procedure-drafts':
        return common + (
            'Supporting-procedure operations and their measurement/reference/cohort entries passed the bounded procedure audit. '
            'No training task is requested; this is not a standalone synthesis or complete SOP. '
            'Source labels identify formulation families, not individually documented physical batches. '
            'Collector fraction, exact synthesis run and specimen identity across techniques are unresolved. '
            'No cross-record physical-specimen identity is asserted.'
        )
    return common + (
        'The AKS41 contextual observation and nine separate population, particle and HPLC entries passed the corrected bounded context audit. '
        'No complete AKS41 synthesis, current-apparatus stock-flow assignment or training eligibility is asserted. '
        'The earlier-apparatus observation is not a parent recipe for the three current-apparatus formulations.'
    )


def link(target, label, relation):
    return {'label': label, 'url': '../records/' + target + '.html', 'relation': relation}


def additional_links(record, all_records):
    links = [{
        'label': 'Source review · seven supplied main pages; SI unverified',
        'url': REVIEW_LINK,
        'relation': 'source_review; bounded main-only evidence and unresolved source gaps',
    }]
    rid = record['record_id']
    if rid in VARIANTS:
        links.append({
            'label': 'Study-wide feed-concentration context · not a formulation setting',
            'url': REVIEW_LINK,
            'relation': 'source_context; 3–30 ppm is a study-wide range, excluded from this variant training view',
        })
        for key in sorted(all_records):
            if all_records[key]['record_type'] == 'procedure':
                links.append(link(key, all_records[key]['title'],
                    'Supporting procedure from the same source; formulation-level context only. '
                    'Exact run, collector fraction and physical-specimen identity are unresolved.'))
    elif record['record_type'] == 'procedure':
        for key in VARIANTS:
            links.append(link(key, all_records[key]['title'],
                'Related formulation family, not an identified parent batch or an asserted same-specimen measurement.'))
        related = {
            'acid-activation': ['optical-characterization', 'time-resolved-pl', 'hplc-fractionation'],
            'colloid-concentration': [],
            'hplc-fractionation': ['acid-activation', 'tem-characterization'],
            'ir-characterization': ['powder-preparation', 'xrd-characterization'],
            'optical-characterization': ['acid-activation', 'time-resolved-pl'],
            'powder-preparation': ['xrd-characterization', 'ir-characterization'],
            'tem-characterization': ['hplc-fractionation'],
            'time-resolved-pl': ['acid-activation', 'optical-characterization'],
            'xrd-characterization': ['powder-preparation', 'ir-characterization'],
        }
        for suffix in related[rid.removeprefix(PREFIX)]:
            key = PREFIX + suffix
            links.append(link(key, all_records[key]['title'],
                'Related supporting-procedure context in this source; not an exact physical-batch join. '
                'Consult each record for acquisition branches and unresolved specimen assignment.'))
    else:
        for suffix in ['tem-characterization', 'hplc-fractionation']:
            key = PREFIX + suffix
            links.append(link(key, all_records[key]['title'],
                'Reported acquisition-method context for AKS41 characterization; '
                'does not reconstruct its earlier-apparatus synthesis or assign a current formulation.'))
    return links


def justification(change, kind):
    path = change['path']
    if path in ['/quality/review_status', '/quality/review_scope'] or path.startswith('/sources/'):
        return {
            'reason': 'Replace stale pending-source-join status with the bounded review supported by the audited input bytes; explicitly preserve main-only/SI-unverified and pending reader/publication scope.',
            'evidence': [FULL_AUDIT, AUDITS[kind]],
        }
    if path == '/quality/requested_tasks':
        return {
            'reason': 'Only the three reviewed synthesis variants have identified Si2H6 synthesis precursor and reviewed partial operations. No measured outcome, size, quantum-yield or exact-structure task is enabled.',
            'evidence': [AUDITS[kind], 'Main PDF p. 2, printed p. 1225, Experimental A', 'Main PDF p. 3, printed p. 1226, Results A', 'recipe-atlas/scripts/dataset_lib.py:eligibility,training_view'],
        }
    if path.startswith('/operations/') or path.startswith('/materials/'):
        return {
            'reason': 'Move the study-wide 3–30 ppm range out of the per-formulation operation and material note because both are exported by partial_protocol. Preserve the exact original quantity and note in source-context.json, with raw source excerpt and evidence.',
            'evidence': ['canonical-drafts-audit.json:concentration-scope/future_training_gate_requirement', 'Main PDF p. 2, printed p. 1225, Experimental A', 'source-context.json'],
        }
    if path == '/context_links':
        return {
            'reason': 'Add reader navigation to the main-only source review and related procedures/formulation families. All relationships are contextual; no physical parent, batch or specimen linkage is invented.',
            'evidence': [AUDITS[kind], 'Main PDF pp. 2–6, Experimental A–B and Results A–B', 'reader-integration-spec.json'],
        }
    raise AssertionError('Unexpected unaudited change: ' + path)


def validate_proposals(originals, proposals, source_context):
    errors = []
    checks = []
    def check(label, passed):
        checks.append({'check': label, 'passed': bool(passed)})
        if not passed:
            errors.append(label)
    check('Exactly 13 stable record IDs', set(originals) == set(proposals) and len(proposals) == 13)
    check('All 48 measurement entries retained', sum(len(r['measurements']) for r in proposals.values()) == 48)
    views = []
    detail = []
    for rid, proposal in sorted(proposals.items()):
        original = originals[rid]
        issues = validate_record(proposal)
        errors.extend(issues)
        check(rid + ': strict schema and evidence/material/sample graph', not issues)
        # Scientific identity and specimen boundaries must be byte-equivalent as JSON values.
        for key in original.keys() - {'quality', 'sources', 'context_links', 'operations', 'materials'}:
            check(rid + ': preserve ' + key, original[key] == proposal[key])
        for key in ['missing_fields', 'conflicts', 'experimental_outcome']:
            check(rid + ': preserve quality.' + key, original['quality'][key] == proposal['quality'][key])
        for before, after in zip(original['sources'], proposal['sources']):
            check(rid + ': preserve source identity and SI status',
                {k:v for k,v in before.items() if k != 'main_status'} == {k:v for k,v in after.items() if k != 'main_status'})
        expected_ops = copy.deepcopy(original['operations'])
        expected_materials = copy.deepcopy(original['materials'])
        if rid in VARIANTS:
            next(o for o in expected_ops if o['id'] == 'feed')['parameters'].pop(RANGE_KEY)
            next(m for m in expected_materials if m['id'] == 'disilane')['notes'][0] = (
                'Disilane, Si2H6: silicon precursor supplied as 0.1% in He (Matheson). '
                'The study-wide dilution range is stored separately as source context, not a formulation setting.'
            )
        check(rid + ': operations unchanged except removed study-wide range', proposal['operations'] == expected_ops)
        check(rid + ': chemicals unchanged except scoped source-context note', proposal['materials'] == expected_materials)
        expected_tasks = TASKS if rid in VARIANTS else []
        gates = eligibility(proposal)
        check(rid + ': requested tasks exactly scoped', proposal['quality']['requested_tasks'] == expected_tasks)
        check(rid + ': actual eligible tasks exactly scoped', {t for t,g in gates.items() if g['eligible']} == set(expected_tasks))
        check(rid + ': actual hub-route gate', synthesis_route(proposal) == (rid in VARIANTS))
        for task, gate in gates.items():
            if gate['eligible']:
                view = training_view(proposal, task)
                serialized = json.dumps(view, ensure_ascii=False)
                check(rid + '/' + task + ': no study-wide concentration leakage',
                    RANGE_KEY not in serialized and not re.search(r'3\s*[-–]\s*30\s*ppm', serialized))
                check(rid + '/' + task + ': no measured target inputs',
                    set(view['input']) == {'composition', 'method'})
                if task == 'partial_protocol':
                    check(rid + ': no observation/structure label fields exported',
                        not ({'products','measurements','structure_assets','context_links'} & view['output'].keys()))
                if task == 'precursor_selection':
                    check(rid + ': only actual Si2H6 precursor label', view['output']['precursors'] == [
                        {'name':'Disilane','formula':'Si2H6','role':'nonmetal_precursor'}])
                views.append(view)
            else:
                try:
                    training_view(proposal, task)
                except ValueError:
                    blocked = True
                else:
                    blocked = False
                check(rid + '/' + task + ': disabled export rejects', blocked)
        for item in proposal['context_links']:
            if item['url'].startswith('../records/'):
                target = item['url'].removeprefix('../records/').removesuffix('.html')
                check(rid + ': proposed record-link target exists: ' + target, target in proposals)
        detail.append({'record_id':rid, 'record_type':proposal['record_type'], 'measurements':len(proposal['measurements']), 'eligible_tasks':expected_tasks, 'hub_synthesis_route':synthesis_route(proposal)})
    groups = build_groups(list(proposals.values()))
    check('All 13 records remain one evaluation group', len(set(groups.values())) == 1)
    check('Exactly six task views, not six unique recipes', len(views) == 6)
    check('Three source-context quantities retained', len(source_context['removed_variant_fields']) == 3)
    for item in source_context['removed_variant_fields']:
        rid = item['record_id']
        original = originals[rid]
        feed = next(o for o in original['operations'] if o['id'] == 'feed')
        note = next(m for m in original['materials'] if m['id'] == 'disilane')['notes'][0]
        check(rid + ': exact removed quantity retained', item['original_quantity'] == feed['parameters'][RANGE_KEY])
        check(rid + ': exact removed material note retained', item['original_material_note'] == note)
    return {
        'status':'passed' if not errors else 'failed', 'scope':'Private proposal schema/graph, exact scientific preservation, task gating and actual training-view audit; no reader/publication claim.',
        'record_count':len(proposals), 'measurement_count':48, 'synthesis_variant_count':3,
        'supporting_procedure_count':9, 'context_observation_count':1,
        'eligible_task_view_counts':dict(Counter(v['task'] for v in views)),
        'evaluation_groups':groups, 'records':detail, 'checks':checks, 'errors':errors,
        'si_reviewed':False, 'final_reader_audit_complete':False, 'published':False,
    }, views


def main():
    audits = {kind:read(REVIEW / name) for kind,name in AUDITS.items()}
    expected = expected_audited_hashes(audits)
    full = read(REVIEW / FULL_AUDIT)
    assert full['scope']['full_main_text'] and full['scope']['full_main_visual']
    assert full['scope']['main_pages'] == 7 and not full['scope']['matched_si_read']
    assert audits['canonical-drafts']['outstanding_in_scope_must_fix_count'] == 0
    assert not audits['procedure-drafts']['outstanding_in_scope_must_fix']
    assert audits['context-drafts']['must_fix_remaining'] == 0
    extracted_sha = sha(REVIEW / 'source-extraction.json')
    for kind in ['canonical-drafts', 'procedure-drafts']:
        assert audits[kind]['source_extraction_sha256'] == extracted_sha
    current = read(REVIEW / 'private-records-validation.json')
    assert current['status'] == 'passed' and current['record_count'] == 13 and current['measurement_count'] == 48
    originals, paths, kinds = {}, {}, {}
    for kind in AUDITS:
        for path in sorted((REVIEW / kind).glob('*.json')):
            record = read(path)
            rid = record['record_id']
            assert rid not in originals
            assert sha(path) == expected[rid], 'Draft changed since independent audit: ' + str(path)
            originals[rid], paths[rid], kinds[rid] = record, path, kind
    assert set(originals) == set(expected) and len(originals) == 13
    raw_excerpt = 'Matheson), further diluted to 3-30 ppm in He (Air Products,'
    assert raw_excerpt in (REVIEW / 'main-text.txt').read_text(encoding='utf-8')
    source_context = {
        'schema':'mattersyn-private-source-context-proposal-1', 'source_id':SOURCE_ID, 'doi':SOURCE_DOI,
        'review_scope':SOURCE_SCOPE, 'published':False,
        'context_id':'study-wide-disilane-dilution-range',
        'scope':'Study-wide apparatus/feed context; not independently assigned to any fixed stock-flow formulation.',
        'source_raw_range':'3-30 ppm', 'source_text_excerpt':raw_excerpt,
        'source_text_file':'../main-text.txt',
        'evidence':[{'source_id':SOURCE_ID,'locator':'Main PDF p. 2, printed p. 1225, Experimental A'}],
        'removed_variant_fields':[],
        'training_rule':'Exclude from variant material notes, operation quantities, condition options and all task-specific training views. Preserve this context on the source review page.',
        'integration_requirement':'Merge this sourced study-wide context into the Littau source-review ledger/reader. Do not import this companion file as a canonical recipe. Record links intentionally target the source-review page without inventing an anchor.',
    }
    proposals, changes = {}, []
    for rid, original in sorted(originals.items()):
        proposal = copy.deepcopy(original)
        kind = kinds[rid]
        proposal['quality']['review_status'] = 'source_reviewed'
        proposal['quality']['review_scope'] = scoped_review_text(kind)
        proposal['quality']['requested_tasks'] = TASKS.copy() if rid in VARIANTS else []
        for source in proposal['sources']:
            source['main_status'] = (
                'All seven supplied main pages read and visually inspected; independent source review and '
                'bounded canonical source-join audit passed. Final item-coverage reconciliation, '
                'canonical-to-reader audit and publication are separate pending gates.'
            )
        if rid in VARIANTS:
            feed = next(o for o in proposal['operations'] if o['id'] == 'feed')
            chemical = next(m for m in proposal['materials'] if m['id'] == 'disilane')
            source_context['removed_variant_fields'].append({
                'record_id':rid, 'operation_id':'feed', 'quantity_path':'/operations/0/parameters/' + RANGE_KEY,
                'original_quantity':feed['parameters'].pop(RANGE_KEY),
                'material_id':'disilane', 'material_note_path':'/materials/0/notes/0',
                'original_material_note':chemical['notes'][0],
            })
            chemical['notes'][0] = (
                'Disilane, Si2H6: silicon precursor supplied as 0.1% in He (Matheson). '
                'The study-wide dilution range is stored separately as source context, not a formulation setting.'
            )
        proposal['context_links'].extend(additional_links(proposal, originals))
        deltas = differences(original, proposal)
        for change in deltas:
            change.update(justification(change, kind))
        changes.append({
            'record_id':rid, 'draft_path':str(paths[rid].relative_to(REVIEW)),
            'audited_draft_sha256':sha(paths[rid]), 'audit_path':AUDITS[kind],
            'changes':deltas,
        })
        proposals[rid] = proposal
    validation, views = validate_proposals(originals, proposals, source_context)
    assert not validation['errors'], '\n'.join(validation['errors'])
    for rid, record in proposals.items():
        path = OUT / 'records' / (rid + '.json')
        write(path, record)
        next(item for item in changes if item['record_id'] == rid)['proposal_sha256'] = sha(path)
    write(OUT / 'source-context.json', source_context)
    write(OUT / 'changes.json', {
        'status':'private_proposal_not_imported', 'created_utc':datetime.now(timezone.utc).isoformat(),
        'scope':SOURCE_SCOPE, 'draft_count':13, 'stable_revision_policy':'Keep revision 1: this is an unpublished initial-record proposal. Stable IDs and lineage are unchanged.',
        'source_extraction_sha256':extracted_sha,
        'audit_inputs':{name:sha(REVIEW/name) for name in [FULL_AUDIT,*AUDITS.values(),'private-records-validation.json']},
        'site_dependencies':{str(p.relative_to(SITE)):sha(p) for p in [SITE/'scripts/dataset_lib.py',SITE/'scripts/schema_definition.py',SITE/'scripts/build_atlas.py']},
        'records':changes,
    })
    write(OUT / 'validation.json', validation)
    (OUT / 'training-view-proposals.jsonl').write_text(
        ''.join(json.dumps(view,ensure_ascii=False) + '\n' for view in views), encoding='utf-8')
    print(json.dumps({k:validation[k] for k in ['status','record_count','measurement_count','synthesis_variant_count','supporting_procedure_count','context_observation_count','eligible_task_view_counts']}))
    print('Checks:', len(validation['checks']), '; output:', OUT)


if __name__ == '__main__':
    main()
