"""Activate completed screening only for the immutable collection.

The priority gate already rejects unranked new claims. Keep every later-arrival
scope unranked, while preserving the active batch and all scientific statuses.
Rebuild the partition against the current ledger before each activation.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import monitor


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_policy(ledger, report, partition, report_path):
    if report.get('scientific_review_performed') is not False:
        raise ValueError('Expected an automated candidate screen, not a scientific completion claim.')
    counts = report['counts']
    if counts['per_file_dispositions'] != counts['snapshot_present_files']:
        raise ValueError('Screening is incomplete: every snapshot file needs a disposition.')
    if counts['actual_source_hashes_computed'] != counts['snapshot_present_files']:
        raise ValueError('Missing actual source hashes; resolve source failures before activation.')
    if partition['unmapped_cutoff_files'] or partition['missing_current_cutoff_scope_ids']:
        raise ValueError('Cutoff membership still has unmapped or missing scope IDs.')
    included = set(partition['included_canonical_group_ids'])
    later = set(partition['later_arrival_group_ids'])
    if included & later:
        raise ValueError('Cutoff and later-arrival scopes overlap.')
    present = {k for k, g in ledger['groups'].items() if not g.get('alias_of')
               and any(ledger['files'][f]['exists'] for f in g['files'])}
    screened = {s['group_id'] for s in report['scopes']}
    if included & present - screened:
        raise ValueError('Some included present scopes have no screening disposition.')
    rankings, held = [], []
    for row in report['rankings']:
        key = row['group_id']
        if key not in included:
            continue
        group = ledger['groups'].get(key)
        if not group or group.get('alias_of') or group['generation'] != row['source_generation']:
            held.append(key)
            continue
        rankings.append({k: row[k] for k in ('group_id', 'score', 'source_generation')})
    return ({'mode': 'evidence_richness', 'require_screened': True,
             'source_report': str(report_path.resolve()), 'source_report_sha256': digest(report_path),
             'screened_at': report['screened_at'], 'rankings': rankings}, held)


def activate(ledger_path, report_path, partition_path, output):
    if output.exists():
        raise ValueError('Preserve activation history; choose a new output directory.')
    raw = ledger_path.read_bytes()
    ledger = json.loads(raw)
    report = json.loads(report_path.read_bytes())
    partition = json.loads(partition_path.read_bytes())
    if partition['partition_ledger_sha256'] != hashlib.sha256(raw).hexdigest():
        raise ValueError('Partition is stale; regenerate it from the current ledger.')
    progress = json.loads(report_path.with_name('progress.json').read_bytes())
    if progress.get('state') != 'complete' or progress.get('report_sha256') != digest(report_path):
        raise ValueError('Screening completion/report hash is unverified.')
    source_snapshot = Path(report['source_snapshot'])
    if digest(source_snapshot) != report['source_snapshot_sha256']:
        raise ValueError('Screened snapshot changed.')
    manifest = Path(partition['cutoff_manifest_path'])
    if digest(manifest) != partition['cutoff_manifest_sha256']:
        raise ValueError('Cutoff manifest changed.')
    for path, expected in json.loads(manifest.read_bytes())['bound_files'].items():
        if digest(path) != expected:
            raise ValueError('Immutable cutoff dependency changed: ' + path)
    policy, held = build_policy(ledger, report, partition, report_path)
    output.mkdir(parents=True)
    (output / 'ledger-before-activation.json').write_bytes(raw)
    (output / 'priority-policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf8')
    # Only root calls this mutation. It uses the monitor's atomic ledger lock.
    result = monitor.set_priority(ledger_path, policy)
    after = monitor.read_ledger(ledger_path)
    for field in ('groups', 'files', 'current_batch', 'current_paper'):
        if after.get(field) != ledger.get(field):
            raise AssertionError('Unexpected scientific/claim mutation: ' + field)
    ranked = {r['group_id'] for r in after['selection_policy']['rankings']}
    if ranked & set(partition['later_arrival_group_ids']):
        raise AssertionError('Later arrivals leaked into selection.')
    proof = {'schema': 'mattersyn-screened-cutoff-activation/1',
             'activated_at': datetime.now(timezone.utc).isoformat(),
             'report_path': str(report_path.resolve()), 'report_sha256': digest(report_path),
             'partition_path': str(partition_path.resolve()), 'partition_sha256': digest(partition_path),
             'cutoff_at': partition['cutoff_at'], 'cutoff_counts': partition['counts'],
             'screen_counts': report['counts'], 'eligible_ranked_cutoff_scopes': len(ranked),
             'stale_rankings_held': held, 'later_scopes_without_selection_rank': len(partition['later_arrival_group_ids']),
             'current_batch_preserved': result['current_batch_preserved'],
             'scientific_statuses_changed': False, 'screening_exclusions_assigned': 0,
             'selection_enforced_by': 'require_screened=true, with rankings restricted to immutable cutoff membership',
             'original_arrival_order_and_source_names_preserved': True,
             'held_nested_candidates': partition['nested_cutoff_candidates_held_for_scope_review'],
             'note': 'Automated screening only. No full reading/audit or no-recipe exclusion is implied.'}
    (output / 'activation-proof.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf8')
    return proof


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('ledger', 'report', 'partition', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    proof = activate(a.ledger, a.report, a.partition, a.output)
    print(json.dumps({k: proof[k] for k in ('eligible_ranked_cutoff_scopes', 'later_scopes_without_selection_rank', 'stale_rankings_held', 'current_batch_preserved')}))
