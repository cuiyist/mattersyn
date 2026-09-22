"""Root-only, audited nomination-order activation; no scientific state promotion."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
MONITOR = HERE.parent / 'incoming-paper-monitor'
sys.path.insert(0, str(MONITOR))
import monitor


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_audits(summary, summary_sha, integrity, benchmark):
    for name, report in [('independent ranker', integrity), ('source benchmark', benchmark)]:
        require(report.get('passed') is True, name + ' audit has not passed')
        require(report.get('summary_sha256') == summary_sha, name + ' audit covers another run')
        require(report.get('ranker_script_sha256') == summary['script_sha256'], name + ' audit covers another ranker')


def build_rows(ledger, partition, rows, audited_generation_holds=()):
    included = set(partition['included_canonical_group_ids'])
    later = set(partition['later_arrival_group_ids'])
    require(not included & later, 'Cutoff membership overlaps later arrivals')
    require(not partition['unmapped_cutoff_files'] and not partition['missing_current_cutoff_scope_ids'], 'Unresolved cutoff membership')
    require(len(rows) == len(included) == 9532 and {r['group_id'] for r in rows} == included,
            'Every cutoff scope must have exactly one nomination row')
    require([r['candidate_inspection_rank'] for r in rows] == list(range(1, len(rows)+1)), 'Nomination order is incomplete')
    generation_holds = {g['group_id'] for g in partition['included_groups'] if g['requires_generation_reopen_consistency_check']} | set(audited_generation_holds)
    require(generation_holds <= included, 'Generation hold outside the cutoff collection')
    rankings, held = [], []
    for row in rows:
        key = row['group_id']
        require(all(row.get(k) is False for k in ('verified_pair', 'task_ready', 'automatic_exclusion')), 'Unexpected automatic scientific approval')
        require(row.get('main_si_pairing') == 'unverified_candidate_group_only', 'Unexpected automatic source pairing')
        group = ledger['groups'].get(key)
        reasons = []
        if row['source_hold']:
            reasons.append('known_source_identity_or_role_exception')
        if key in generation_holds:
            reasons.append('generation_or_membership_reconciliation_required')
        if not group or group.get('alias_of') or group.get('generation') != row['source_generation_in_partition']:
            reasons.append('current_generation_or_canonical_identity_changed')
        if reasons:
            held.append({'group_id': key, 'reasons': reasons})
        else:
            rankings.append({'group_id': key, 'score': len(rows)+1-row['candidate_inspection_rank'],
                             'source_generation': group['generation']})
    require(not {r['group_id'] for r in rankings} & later, 'Later arrivals entered nominations')
    return rankings, held


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('run', 'audit', 'benchmark', 'partition', 'output'):
        p.add_argument('--'+key, required=True, type=Path)
    p.add_argument('--activate', action='store_true', help='Without this, prepare a proposal only; shared state is not changed.')
    a = p.parse_args()
    output = a.output.resolve()
    require(output.is_relative_to(HERE) and output != HERE and not output.exists(), 'Use a new output directory within the pair-screen workspace')
    run = a.run.resolve()
    require(run.is_relative_to(HERE/'ranker-proposal'), 'Unexpected candidate-run location')
    summary_path = run/'summary.json'
    summary = read(summary_path)
    summary_sha = digest(summary_path)
    audit = read(a.audit)
    check_audits(summary, summary_sha, audit, read(a.benchmark))
    holds_path = Path(audit['generation_dispatch_holds_path'])
    require(digest(holds_path) == audit['generation_dispatch_holds_sha256'], 'Audit-bound generation holds changed')
    audited_generation_holds = {g['group_id'] for g in read(holds_path)['groups']}
    require(read(run/'progress.json').get('status') == 'completed_dry_run_not_activated', 'Full nomination run is incomplete')
    require(summary['fixed_cutoff_file_dispositions'] == 13831 and summary['nested_held_files_preserved'] == 3,
            'Incomplete file dispositions')
    for binding in summary['input_bindings'].values():
        require(digest(binding['path']) == binding['sha256'], 'A frozen screening input changed')
    for rel, binding in summary['output_bindings'].items():
        path = (run/rel).resolve()
        require(path.is_relative_to(run), 'Output binding escapes run directory')
        require(digest(path) == binding['sha256'], 'A frozen screening output changed')
    require(digest(run.parent/'rank_pairs.py') == summary['script_sha256'], 'Ranker code changed after audit')
    ledger_path = MONITOR/'ledger.json'
    before_raw = ledger_path.read_bytes()
    ledger = json.loads(before_raw)
    partition = read(a.partition)
    require(partition['partition_ledger_sha256'] == hashlib.sha256(before_raw).hexdigest(), 'Refresh partition against current ledger before activation')
    require(digest(partition['cutoff_manifest_path']) == partition['cutoff_manifest_sha256'], 'Cutoff manifest changed')
    for path, expected in read(partition['cutoff_manifest_path'])['bound_files'].items():
        require(digest(path) == expected, 'Immutable cutoff dependency changed')
    rows = [json.loads(line) for line in (run/'ranked-scopes.jsonl').open(encoding='utf8')]
    rankings, held = build_rows(ledger, partition, rows, audited_generation_holds)
    output.mkdir(parents=True)
    (output/'ledger-before-activation.json').write_bytes(before_raw)
    report = {'schema': 'mattersyn-audited-pair-nomination-policy/1',
              'created_at': datetime.now(timezone.utc).isoformat(),
              'scientific_review_performed_by_ranker': False,
              'summary_path': str(summary_path), 'summary_sha256': summary_sha,
              'ranker_script_sha256': summary['script_sha256'],
              'independent_ranker_audit': {'path': str(a.audit.resolve()), 'sha256': digest(a.audit)},
              'source_benchmark_audit': {'path': str(a.benchmark.resolve()), 'sha256': digest(a.benchmark)},
              'audited_generation_holds': {'path': str(holds_path), 'sha256': digest(holds_path)},
              'current_partition': {'path': str(a.partition.resolve()), 'sha256': digest(a.partition)},
              'cutoff_scopes_nominated': len(rows), 'rankings': rankings, 'held_scopes': held,
              'meaning': 'Inspection order only. Every recipe, structure origin, sample link and source identity requires its own review. No new verified pairs, exclusions, task approvals or publications.',
              'unreadable_and_low_signal_scopes': 'Retained in the full report; not scientifically excluded.'}
    report_path = output/'pair-nomination-policy-report.json'
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    policy = {'mode': 'evidence_richness', 'require_screened': True,
              'source_report': str(report_path), 'source_report_sha256': digest(report_path),
              'screened_at': report['created_at'], 'rankings': rankings}
    (output/'priority-policy.json').write_text(json.dumps(policy, indent=2)+'\n', encoding='utf8')
    if a.activate:
        require(ledger_path.read_bytes() == before_raw, 'Ledger changed while preparing activation')
        monitor.set_priority(ledger_path, policy, expected_ledger_sha256=hashlib.sha256(before_raw).hexdigest())
        after = monitor.read_ledger(ledger_path)
        for field in ('groups', 'files', 'current_batch', 'current_paper'):
            require(after.get(field) == ledger.get(field), 'Unexpected scientific or claim mutation: '+field)
    proof = {'at': datetime.now(timezone.utc).isoformat(), 'activated': a.activate,
             'ranked_scopes': len(rankings), 'held_scopes': len(held),
             'candidate_run_summary_sha256': summary_sha,
             'policy_report_sha256': digest(report_path),
             'scientific_statuses_changed': False, 'claims_preserved': True,
             'new_pairs_approved': 0, 'papers_excluded': 0,
             'later_scopes_unranked': len(partition['later_arrival_group_ids'])}
    (output/'activation-proof.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf8')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
