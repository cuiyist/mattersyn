"""Save accepted nomination results while keeping unresolved screening explicit."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MONITOR = HERE.parent/'incoming-paper-monitor'
RUN = HERE/'ranker-proposal/final-run-v2'
def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
summary = read(RUN/'summary.json')
audit_path = HERE/'ranker-audit/independent-audit.json'
bench_path = HERE/'rubric-audit/ranker-benchmark-check/independent-benchmark-audit.json'
for path in (audit_path, bench_path):
    audit = read(path)
    assert audit['passed'] is True and audit['summary_sha256'] == sha(RUN/'summary.json')
    assert audit['ranker_script_sha256'] == summary['script_sha256']
rows = [json.loads(line) for line in (RUN/'ranked-scopes.jsonl').open(encoding='utf8')]
assert len(rows) == 9532 and sum(summary['priority_bands'].values()) == 9532
assert all(not r['verified_pair'] and not r['task_ready'] and not r['automatic_exclusion'] for r in rows)
partition = read(MONITOR/'deadline-20260920/pair-screen-20260922/current-partition.json')
manual = read(HERE/'manual-text-screen-holds.json')
at = datetime.now(timezone.utc).isoformat()
public = {
    'schema': 'mattersyn-public-screening-milestone/1', 'at': at,
    'status': 'audited_automated_nomination_pass_complete_manual_screening_remains',
    'document_copies_accounted_for': 13831, 'provisional_groups': 9532,
    'nested_identity_cases_retained': 3,
    'nomination_counts': summary['priority_bands'],
    'atomic_nominations_with_recipe_cues': sum(r['priority_band'].startswith('B_') and r['recipe_candidate_windows'] > 0 for r in rows),
    'source_held_nominations_by_band': dict(Counter(r['priority_band'] for r in rows if r['source_hold'])),
    'unresolved_format_or_text_copies': 238, 'unresolved_format_or_text_unique_hashes': manual['source_hashes'],
    'unresolved_formats': manual['formats'], 'known_source_identity_or_role_group_holds': 32,
    'generation_reconciliation_holds': 4,
    'method_checks': {'integrity': 26125, 'semantic_cases': 17, 'known_source_benchmark_checks': 183},
    'new_scientific_pairs_certified_by_screen': 0, 'papers_excluded_by_screen': 0,
    'screen_summary_sha256': sha(RUN/'summary.json'), 'ranker_script_sha256': summary['script_sha256'],
    'audit_sha256': sha(audit_path), 'benchmark_audit_sha256': sha(bench_path),
    'limits': [
        'Counts are paper-group nominations, not verified recipes, physical samples or training pairs.',
        'Atomic-evidence nominations can refer to a product, bulk comparator, molecular precursor or unavailable deposit; source-specific review is required.',
        'All supplied files are accounted for, but 238 format/text cases still need recovery or manual inspection. This is not complete reading of every paper.',
        'Original cached text lacks historical content hashes; current source verification remains necessary.',
        'Lower-signal, unlinked and unresolved papers remain in the collection. No no-recipe exclusions were assigned.',
    ],
    'next_actions': ['Recover and screen unresolved legacy formats.', 'Inspect the first ten previously unreviewed atomic-evidence nominations against original sources.', 'Re-estimate priority curation after source validation.'],
}
save(HERE/'screening-result-public.json', public)

control = read(MONITOR/'review-control.json')
control.update(recorded_at=at, workflow_phase='manual_format_recovery_and_priority_verification',
    new_paper_admission_allowed=False,
    admission_hold_reason='Accepted automated nomination screen; recover/screen remaining format cases and verify priority pairs before further full website builds. Existing packages remain intact.',
    accepted_pair_screen_summary_sha256=public['screen_summary_sha256'],
    remaining_time_estimate='October 22 target retained. Re-estimate after original-source checks of atomic nominations and unresolved format recovery; nomination counts are not verified workload.')
save(MONITOR/'review-control.json', control)

editorial = read(MONITOR/'public-progress-editorial.json')
editorial['current_work'] = [w for w in editorial['current_work'] if w['short_label'] != 'Collection screening']
editorial['current_work'].insert(0, {
    'short_label': 'Collection screening',
    'title': 'Synthesis–structure evidence and source verification',
    'stage': 'Automated pass audited; source checks and format recovery underway',
    'summary': 'The fixed collection has 9,532 provisional groups and 13,831 top-level document copies. The screen nominated 52 atomic-evidence, 655 phase-link and 433 morphology-link groups. These categories guide review; they do not certify synthesis–structure pairs.',
    'stages': [
        {'label': 'Cached-text nomination pass', 'status': 'complete', 'detail': 'Every fixed-cutoff copy has a disposition; three nested identity cases remain separately held.'},
        {'label': 'Independent method checks', 'status': 'complete', 'detail': 'Coverage, source exceptions, sample-label counterexamples and previously checked coordinate-table benchmarks passed.'},
        {'label': 'Unresolved formats', 'status': 'in_progress', 'detail': '238 copies remain unresolved: 187 legacy Word, 4 spreadsheet, 22 archive, 24 PDF and 1 unidentified file. These are mostly supplements.'},
        {'label': 'Priority source verification', 'status': 'in_progress', 'detail': 'Inspect the first ten previously unreviewed atomic-evidence nominations; separate product, precursor, bulk-comparison and reference structures.'},
        {'label': 'Further website contributions', 'status': 'pending', 'detail': 'Resume from verified priorities after screening gaps are addressed; each contribution still requires its own audit.'},
    ],
})
for work in editorial['current_work']:
    if work['short_label'] == 'Chen et al. (2018)':
        work['summary'] = 'The 8-page main article and 10-page matched supplement have a complete extraction and a passed independent source audit. Composite variants, scale-up, comparison synthesis and device preparation are preserved. Host refinements and fixed minority-phase coordinates retain separate qualifications.'
    elif work['short_label'] == 'Saini et al. (2023)':
        work['summary'] = 'Complete 12-page main article and 107-page supplement coverage is recorded, and extraction is frozen. The separate scientific audit remains pending; this contribution is not yet published.'
editorial['workflow'].update(
    summary='The corrected automated pair-nomination pass is complete and independently checked. Recover unresolved source formats and inspect priority evidence before further website builds.',
    screening_scope='All 13,831 top-level cutoff copies are accounted for, plus three nested identity cases. The 238 unresolved format/text cases remain explicit; this is not full manual screening or complete reading of every paper.',
    capacity='Parallel work now covers legacy-format recovery and original-source checks of atomic-evidence nominations. Existing source extractions remain preserved.',
    screened_at=at, scope_counts_updated_at=partition['generated_at'],
    later_arrival_groups_current=partition['counts']['later_arrival_group_candidates'],
    later_arrival_file_candidates_current=partition['counts']['later_arrival_file_candidates'])
editorial['estimate']['status'] = 'recalibrating_after_original_source_priority_checks'
editorial['estimate']['summary'] = 'October 22 remains the requested target. The automated screen has narrowed the first atomic-evidence inspection list to 52 provisional groups, but their usable recipe links and structural roles still need verification. We will estimate priority curation after those checks and the remaining format recovery; this is not a promise to fully curate all 9,500 unfinished scopes by that date.'
editorial['estimate']['current_batch'] = 'Chen’s complete source extraction has passed its separate audit. Saini’s complete extraction is frozen with audit pending. Both are preserved while collection screening is completed.'
editorial['estimate']['notes'] = public['limits'] + ['No paid API processing has been authorized or started.']
editorial['recent_milestones'].insert(0, {'at':at, 'text':'Corrected automated screen audited: 9,532 provisional groups, 13,831 copies and three nested identity holds. Nominations: 52 atomic-evidence, 655 phase-link and 433 morphology-link groups. All 238 manual format/text cases are retained for further screening. No scientific records or training pairs were added.'})
save(MONITOR/'public-progress-editorial.json', editorial)

memory = ROOT/'MEMORY.md'
heading = '## 2026-09-22 — Accepted automated pair nominations; manual screening continues'
assert heading not in memory.read_text(encoding='utf8'), 'Milestone already saved; preserve history'
entry = f'''{heading}

Corrected ranker 4815804844292ab1378a0be9dd5b264014fd63c4a34dc4c9ca2e12473f2c85a2 completed the cached-text pass: all 13,831 fixed top-level copies, 9,532 provisional groups and three nested identity cases are accounted for. Nomination counts: A 0, B 52 atomic evidence, C 655 phase links, D 433 morphology links, E 45 contextual structures, R 4,041 recipe/unresolved-structure groups and U 4,306 insufficient/manual cases. These are automated candidates, not source-verified category assignments, no-recipe exclusions or task approvals. In particular, no automatic A does not invalidate the separately audited Chen host-coordinate evidence. Run summary SHA256: {public['screen_summary_sha256']}.

Independent ranker audit passed 26,125 integrity checks and 17 bounded semantic cases. Separate source-benchmark audit passed 183 checks across 12 cases/seven papers, closing all five actual-source table/CIF sensitivity misses. Audit hashes: {public['audit_sha256']} and {public['benchmark_audit_sha256']}. Raw cue output is about 337 MB and stays private. Historical rejected/partial runs remain diagnostic. Current source identity, physical-batch linkage, component roles and task admission still require their own evidence.

Remaining screen gaps: 238 copies / 211 distinct hashes (187 legacy DOC, 2 legacy XLS, 2 XLSX, 22 ZIP, 24 PDF and 1 unknown); 221 are SI candidates. Continue safe read-only format recovery plus bounded original-source inspection of the first ten previously unreviewed atomic nominations. Do not call all-paper content screening or full reading complete while these gaps remain. Keep 32 source-identity/role holds and four independently bound generation holds. Further full website admissions remain held; Chen/Saini source packages are preserved. October 22 remains a target, and no paid processing or downloads were started.

Status and public-safe result: research-assets/pair-priority-screen-20260922/screening-result-public.json. Original PDFs/SI, complete text/pages and raw excerpt corpus remain local. Publication of this progress checkpoint is tracked separately from new scientific contributions.

'''
memory.write_text(entry + memory.read_text(encoding='utf8'), encoding='utf8')
print(json.dumps({'accepted_machine_nomination_pass': True, 'manual_copies_unresolved': 238,
                  'atomic_nominations_with_recipe_cues': public['atomic_nominations_with_recipe_cues'], 'website_science_added': 0}))
