"""Aggregate frozen bounded source screens without changing scientific admissions."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = ROOT / 'research-assets'
ATOMIC = ASSETS / 'pair-priority-screen-20260922/atomic-shortlist-review'

def read(p):
    return json.loads(p.read_text(encoding='utf8'))

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def verify_freeze(directory):
    f = read(directory/'author-freeze.json')
    bound = f.get('bound_files', f.get('files'))
    pairs = bound.items() if isinstance(bound, dict) else [(x['path'], x['sha256']) for x in bound]
    checked = 0
    for name, expected in pairs:
        p = Path(name)
        if not p.is_absolute():
            p = directory/p
        assert digest(p) == expected, 'Frozen artifact changed: '+str(p)
        checked += 1
    return checked

scopes, batches = [], []
for number in range(1, 5):
    directory = ATOMIC/f'batch-{number:02d}'
    summary_path = directory/('batch-summary.json' if number <= 2 else 'summary.json')
    s = read(summary_path)
    verified = verify_freeze(directory)
    if number <= 2:
        rows = s['scope_receipts']
        for row in rows:
            scopes.append({'group_id':row['group_id'], 'rank':row['rank'], 'batch':str(directory.relative_to(ROOT)), 'receipt_sha256':row['sha256'], 'outcome':'synthesis_present', 'new_this_checkpoint':False})
    else:
        for row in s['rows']:
            receipt = read(directory/row['receipt'])
            scopes.append({'group_id':receipt['group_id'], 'rank':row['rank'], 'batch':str(directory.relative_to(ROOT)), 'receipt_sha256':row['receipt_sha256'], 'outcome':row['outcome'], 'new_this_checkpoint':True})
    batches.append({'batch':str(directory.relative_to(ROOT)), 'summary_sha256':digest(summary_path), 'freeze_sha256':digest(directory/'author-freeze.json'), 'scope_count':s['scope_count'], 'integrity_checks':verified, 'elapsed_seconds':s.get('elapsed_seconds'), 'full_review':False})

for number in (1, 2):
    directory = HERE/f'phase-batch-{number:02d}'
    s = read(directory/'summary.json')
    verified = verify_freeze(directory)
    for row in s['scope_results']:
        p = directory/f"scope-rank{row['rank']:03d}.json"
        scopes.append({'group_id':row['group_id'], 'rank':row['rank'], 'batch':str(directory.relative_to(ROOT)), 'receipt_sha256':digest(p), 'outcome':'synthesis_present', 'new_this_checkpoint':True})
    batches.append({'batch':str(directory.relative_to(ROOT)), 'summary_sha256':digest(directory/'summary.json'), 'freeze_sha256':digest(directory/'author-freeze.json'), 'scope_count':s['scopes'], 'integrity_checks':verified, 'elapsed_seconds':s['elapsed_seconds'], 'full_review':False})

for number in (1, 2):
    directory = HERE/f'mixed-batch-{number:02d}'
    s = read(directory/'batch-summary.json')
    verified = verify_freeze(directory)
    for row in s['receipts']:
        scopes.append({'group_id':row['group_id'], 'rank':row['rank'], 'batch':str(directory.relative_to(ROOT)), 'receipt_sha256':digest(directory/'batch-summary.json'), 'outcome':row['outcome'], 'new_this_checkpoint':row['outcome'] != 'reuse_existing_terminal_screen'})
    batches.append({'batch':str(directory.relative_to(ROOT)), 'summary_sha256':digest(directory/'batch-summary.json'), 'freeze_sha256':digest(directory/'author-freeze.json'), 'scope_count':s['selected_scopes'], 'integrity_checks':verified, 'elapsed_seconds':s['elapsed_seconds_including_coordination_and_receipt_writing'], 'full_review':False})

assert len({s['group_id'] for s in scopes}) == len(scopes), 'Duplicate provisional scope'
at = datetime.now(timezone.utc).isoformat()
audits = [
    ATOMIC/'batch-01-independent-audit/independent-audit.json',
    ATOMIC/'batch-02-independent-audit/independent-audit.json',
    HERE/'mixed-batch-01-independent-check/independent-check.json',
    HERE/'mixed-batch-02-independent-check/independent-check.json',
    HERE/'phase-batch-01-independent-check/independent-check.json',
    HERE/'phase-batch-02-coordinate-check/independent-check.json',
]
for p in audits:
    assert p.is_file(), 'Independent receipt pending: '+p.name
new = [s for s in scopes if s['new_this_checkpoint']]
report = {
    'at':at, 'scope':'Bounded Methods/relevant-SI screens, not full scientific curation',
    'provisional_scopes_with_receipts':len(scopes),
    'newly_screened_scopes_this_checkpoint':len(new),
    'prior_scope_receipts':20,
    'reused_preexisting_terminal_scopes':1,
    'new_positive_scopes':sum(s['outcome'] in ('synthesis_present','present') for s in new),
    'new_deferred_or_source_hold_scopes':sum(s['outcome'] not in ('synthesis_present','present') for s in new),
    'batches':batches,
    'independent_checks':[{'path':str(p.relative_to(ROOT)), 'sha256':digest(p)} for p in audits],
    'independent_check_limits':'Atomic batches01/02 and mixed batches01/02 have separate bounded checks; phase batch01 only ranks53/55/58 and phase batch02 only rank66. Atomic batches03/04 remain author-screened. None are full scientific approvals.',
    'source_role_hold':{'group_id':'legacy::10.1038_s43246-021-00198-z', 'reason':'Main-labelled file is a Peer Review File; SI has partial preparation details. True main article remains unverified.'},
    'count_limits':['Provisional scopes include exact-copy aliases and parallel editions; do not call this a unique-paper count.','Positive screening includes partial preparation and surface modification; it does not certify complete recipes.','Automated corpus nominations, initial screening, full review, publication and training admission remain separate.'],
    'new_scientific_records':0, 'new_approved_structure_recipe_pairs':0,
    'full_source_reviews_completed_here':0, 'scientific_source_closures':0,
    'fixed_collection_unfinished_scopes':9500,
    'schedule':'daily_preserved', 'paid_processing_started':False,
    'capacity_limits':['Small purposive readable-source batches; no representative corpus throughput or yield estimate.','Author screen timing includes reading and record preparation, excludes later full extraction and publication.','Independent audit timings are separate; overlapping worker time must not be summed as elapsed wall time.','GPU capacity is not established as the bottleneck; no hardware or paid API commitment.'],
}
save(HERE/'screening-checkpoint.json', report)
save(HERE/'screened-scopes.json', {'at':at,'purpose':'Avoid repeating unchanged source screens; use original generation/hash bindings before reuse. This index neither closes sources nor admits training data.','scopes':scopes})
print(json.dumps({k:v for k,v in report.items() if k not in ('batches','independent_checks','capacity_limits')}, indent=2))
